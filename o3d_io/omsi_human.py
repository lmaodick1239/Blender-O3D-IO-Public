"""Rest-space human geometry and in-memory OMSI HUM serialization.

HUM input is XYZ (Z up); the native parser stores XZY, just like exported
O3D vertices. See func-00624b40.c:317/329/342 and the shipped-file labels.
No handedness/sign change is performed. Numeric overrides are final, scaled
HUM-file coordinates: paired XYZ uses a positive symmetric X distance;
waist/neck accept YZ or XYZ (their X is diagnosed, not serialized).
"""
from hashlib import sha256
import json
from math import isfinite
from numbers import Real
import ntpath
import os
import shutil
import unicodedata
from io import BytesIO, StringIO

from mathutils import Matrix, Vector

from .human_arm_normalization import build_arm_transforms, make_rest_deformer, transform_landmark
from .io_o3d_export import prepared_export_mesh
from .mmd_rig import CANONICAL_NAMES, CANONICAL_SLOTS, _source_segment, read_source_rig


DEFAULT_SETTINGS = {'seat_height': .90, 'feetdist': .04,
                    'walk_params': (1.4, 80, 1.0, 1.0, 0.0),
                    'voice': 'M2', 'mass_kg': 70}
_METADATA = 'omsi_human_landmarks'
_PAIRS = {'hip': 'OS', 'knee': 'US', 'shoulder': 'OA', 'elbow': 'UA', 'hand': 'Hand'}
_ORDER = ('hip', 'knee', 'waist', 'shoulder', 'elbow', 'neck', 'hand', 'finger')


def _scalar(value):
    if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value):
        raise ValueError('Human values must be finite numbers')
    return float(value)


def _number(value):
    value = float(value)
    if not isfinite(value):
        raise ValueError('Human values must be finite')
    return format(value, '.9g')


def _vector(value, *, center=False):
    if isinstance(value, (str, bytes)):
        raise ValueError('Landmarks require numeric vectors')
    values = tuple(_scalar(item) for item in value)
    if center and len(values) == 2:
        values = (0.0, *values)
    if len(values) != 3:
        raise ValueError('Landmarks require XYZ (or YZ for waist/neck)')
    point = Vector(values)
    if not all(isfinite(item) for item in point):
        raise ValueError('Human landmarks exceed finite geometry range')
    return point


def _fingerprint(armature):
    # Local rest geometry only: object transforms and pose do not stale points.
    # Extras do not define human anatomy, so template-added extras are compatible.
    rest = [(name, list(bone.head_local), list(bone.tail_local),
             [value for row in bone.matrix_local for value in row])
            for name in sorted(CANONICAL_NAMES)
            if (bone := armature.data.bones.get(name)) is not None]
    return sha256(json.dumps(rest, separators=(',', ':'), allow_nan=False).encode('utf8')).hexdigest()


def capture_landmarks(source_armature, target_armature, *, template_armature=None) -> None:
    """Persist version-1 target-local neck/finger points, never a source pointer.

    ID properties contain version, rest_fingerprint, points (available XYZ
    arrays), and missing (explicit point names). TEMPLATE accepts only current,
    rest-compatible metadata; absent/stale/incompatible points stay missing.
    """
    points = {}
    if template_armature is not None:
        metadata = template_armature.get(_METADATA, {})
        if (hasattr(metadata, 'get') and metadata.get('version') == 1
                and metadata.get('rest_fingerprint') == _fingerprint(template_armature)
                and _fingerprint(template_armature) == _fingerprint(target_armature)):
            saved = metadata.get('points', {})
            for name, value in (saved.items() if hasattr(saved, 'items') else ()):
                if name in ('neck', 'finger_L', 'finger_R'):
                    try:
                        points[name] = list(_vector(value))
                    except (ValueError, TypeError, OverflowError):
                        pass  # Invalid optional metadata is an explicit missing point.
    elif source_armature is not None:
        segments = read_source_rig(source_armature)
        inverse = target_armature.matrix_world.inverted()
        # Exact anatomical names: helpers, shadow, twists and IK never win.
        for name, fragments, side in (
                ('neck', ('首', 'Neck', 'neck'), None),
                ('finger_L', ('中指１', '中指1', 'middle_finger1'), 'L'),
                ('finger_R', ('中指１', '中指1', 'middle_finger1'), 'R')):
            segment = _source_segment(segments, fragments, side)
            if segment is not None:
                points[name] = list(inverse @ segment[0])
    target_armature[_METADATA] = {
        'version': 1, 'rest_fingerprint': _fingerprint(target_armature),
        'points': points,
        'missing': [name for name in ('neck', 'finger_L', 'finger_R') if name not in points],
    }


def _validate_transform(obj):
    matrix = obj.matrix_world
    if not all(isfinite(value) for row in matrix for value in row):
        raise ValueError(f'{obj.name}: nonfinite transform; use finite human transforms')
    basis = matrix.to_3x3()
    columns = list(basis.col)
    lengths = [column.length for column in columns]
    if min(lengths) <= 1e-8:
        raise ValueError(f'{obj.name}: singular human transform; apply a positive uniform scale')
    if basis.determinant() <= 0:
        raise ValueError(f'{obj.name}: mirrored human transform; remove reflection')
    if max(lengths) - min(lengths) > max(lengths) * 1e-5:
        raise ValueError(f'{obj.name}: nonuniform human scale; apply uniform scale')
    if any(abs(columns[a].dot(columns[b])) > lengths[a] * lengths[b] * 1e-5
           for a, b in ((0, 1), (0, 2), (1, 2))):
        raise ValueError(f'{obj.name}: sheared human transform; remove shear')
    if any((column / length - Vector(axis)).length > 1e-5
           for column, length, axis in zip(columns, lengths, ((1, 0, 0), (0, 1, 0), (0, 0, 1)))):
        raise ValueError(f'{obj.name}: human frame must be upright and face model forward; align rest geometry')


def _primary_meshes(armature, objects, context, warnings):
    from .mesh_lod import _scene_paths
    candidates = []
    for obj in dict.fromkeys(objects):
        if getattr(obj, 'type', None) != 'MESH':
            continue
        if obj.rigid_body or obj.rigid_body_constraint:
            warnings.append(f'{obj.name}: excluded physics helper from human bounds')
            continue
        if obj.get('omsi_lod_level', 0) > 0:
            continue
        if not (obj.parent == armature or any(modifier.type == 'ARMATURE' and modifier.object == armature
                                              for modifier in obj.modifiers)):
            warnings.append(f'{obj.name}: excluded mesh not bound to the human armature')
            continue
        candidates.append(obj)
    # Imported/manual LOD families use ancestor LOD_* collections rather than IDs.
    paths = _scene_paths(context.scene)
    factors = {obj: set().union(*(paths.get(collection, set()) for collection in obj.users_collection))
               for obj in candidates}
    for obj, values in factors.items():
        if len(values) > 1:
            raise ValueError(f'{obj.name}: conflicting LOD collection factors; use one LOD bucket')
    highest = max((factor for values in factors.values() for factor in values), default=None)
    return [obj for obj in candidates if not factors[obj] or highest in factors[obj]]


def measure_human(armature, meshes, *, overrides=None, scale=1.0, context=None,
                  confirm_stale=False, turn_180=False, arm_transforms=None) -> dict:
    """Return errors/warnings, 22 links or None, height, and final XYZ landmarks.

    Bounds use primary bound meshes evaluated in rest space. Metadata is only
    consumed if current or explicitly confirmed; overrides always take priority.
    turn_180 rotates measured XYZ around Z; overrides remain final file vectors.
    A supplied arm plan normalizes world points before scale/yaw and uses the
    same temporary rest deformation for bounds. No plan is built here.
    Errors block serialization, not generic conversion/export.
    """
    return _measure_human(armature, meshes, overrides=overrides, scale=scale, context=context,
                          confirm_stale=confirm_stale, turn_180=turn_180,
                          arm_transforms=arm_transforms, rest_deformer=None)


def _measure_human(armature, meshes, *, overrides, scale, context, confirm_stale,
                   turn_180, arm_transforms, rest_deformer):
    # Bundle callers supply their one deformer for bounds, codec and publication.
    import bpy
    context = context or bpy.context
    result = {'errors': [], 'warnings': [], 'links': None, 'height': None, 'landmarks': {}}
    errors, warnings, landmarks = result['errors'], result['warnings'], result['landmarks']
    overrides = {} if overrides is None else overrides
    try:
        scale = _scalar(scale)
        if scale <= 0:
            raise ValueError('Human export scale must be positive')
        if armature is None or armature.type != 'ARMATURE':
            raise ValueError('Select one canonical human armature')
        _validate_transform(armature)
        missing = set(CANONICAL_NAMES) - set(armature.data.bones.keys())
        if missing:
            raise ValueError('Missing canonical rest bones: ' + ', '.join(sorted(missing)))
        if not hasattr(overrides, 'items') or set(overrides) - set((*_ORDER, 'height')):
            raise ValueError('Unknown human landmark override')
        if arm_transforms is not None:
            if rest_deformer is None:
                rest_deformer = make_rest_deformer(armature, arm_transforms)
            for name in ('elbow', 'hand', 'finger'):
                if name in overrides:
                    warnings.append(f'{name}: override is in final file coordinates and must match normalized geometry')
        primary = _primary_meshes(armature, meshes, context, warnings)
        if not primary:
            raise ValueError('Human height requires nonempty primary character meshes, not physics/LODs')
        low = high = None
        for obj in primary:
            _validate_transform(obj)
            with prepared_export_mesh(obj, context, Matrix.Scale(scale, 4),
                                      rest_deformer=rest_deformer) as (_, mesh, _):
                for vertex in mesh.vertices:
                    if not all(isfinite(value) for value in vertex.co):
                        raise ValueError(f'{obj.name}: nonfinite human geometry')
                    # Prepared geometry is O3D XZY: its Y coordinate is height.
                    z = vertex.co.y
                    low = z if low is None else min(low, z)
                    high = z if high is None else max(high, z)
        if low is None or high - low <= 0:
            raise ValueError('Human rest geometry must have positive height')
        result['height'] = _scalar(overrides.get('height', high - low))
        if result['height'] <= 0:
            raise ValueError('Human height must be positive')
        tolerance = max(.01, result['height'] * .01)
        if abs(low) > tolerance:
            warnings.append(f'Feet are not near the ground plane (minimum Z={_number(low)}); no translation applied')

        def final(point, bone_name=None):
            point = armature.matrix_world @ _vector(point)
            if arm_transforms is not None and bone_name is not None:
                point = transform_landmark(arm_transforms, bone_name, point)
            point *= scale
            return Vector((-point.x, -point.y, point.z)) if turn_180 else point

        def head(name):
            return final(armature.data.bones[name].head_local, name)

        raw = {name: (head(stem + '_L'), head(stem + '_R')) for name, stem in _PAIRS.items()}
        # Geometry, not object rotation alone, must demonstrate a human frame.
        hips = (raw['hip'][0] + raw['hip'][1]) * .5
        knees = (raw['knee'][0] + raw['knee'][1]) * .5
        shoulders = (raw['shoulder'][0] + raw['shoulder'][1]) * .5
        if not (shoulders.z > hips.z > knees.z):
            errors.append('Rest anatomy must be upright: shoulders above hips above knees')
        for name in ('hip', 'shoulder'):
            difference = raw[name][0] - raw[name][1]
            if abs(difference.x) <= 1e-8 or max(abs(difference.y), abs(difference.z)) > max(abs(difference.x) * .25, tolerance):
                errors.append(f'{name}: rest pair is not aligned with the human X axis; align model forward')
        center = (hips + shoulders) * .5
        if abs(center.x) > tolerance:
            errors.append('Human anatomical centerline must be on X=0; align the character before export')
        metadata = armature.get(_METADATA, {})
        points = {}
        if metadata.get('version') == 1:
            stale = metadata.get('rest_fingerprint') != _fingerprint(armature)
            needed = [name for name in ('neck', 'finger') if name not in overrides]
            if stale and needed:
                message = 'Captured source landmarks are stale after rest edits; confirm stale points or replace neck/finger overrides'
                (warnings if confirm_stale else errors).append(message)
            if not stale or confirm_stale:
                points = metadata.get('points', {})
        if 'finger' not in overrides and 'finger_L' in points and 'finger_R' in points:
            raw['finger'] = (final(points['finger_L'], 'Hand_L'), final(points['finger_R'], 'Hand_R'))
        for name in _ORDER:
            if name in overrides:
                point = _vector(overrides[name], center=name in ('waist', 'neck'))
                if name not in ('waist', 'neck') and point.x <= 0:
                    raise ValueError(f'{name}: paired override X must be a positive symmetric distance')
            elif name in raw:
                left, right = raw[name]
                if left.x * right.x >= 0:
                    errors.append(f'{name}: measured pair must lie on opposite sides of X=0')
                if (Vector((-left.x, left.y, left.z)) - right).length > tolerance:
                    warnings.append(f'{name}: asymmetric rest pair; export uses a symmetric approximation')
                point = Vector(((abs(left.x) + abs(right.x)) * .5,
                                (left.y + right.y) * .5, (left.z + right.z) * .5))
            elif name == 'waist':
                point = head('Main')
            elif name == 'neck' and 'neck' in points:
                point = final(points['neck'])
            else:
                errors.append(f'Missing {name} landmark; supply a numeric {name} override')
                continue
            if name in ('waist', 'neck') and abs(point.x) > tolerance:
                warnings.append(f'{name}: off-center X cannot be preserved by HUM; only Y/Z are serialized')
            landmarks[name] = list(point)
        if not errors:
            result['links'] = [float(value) for name in _ORDER
                               for value in (landmarks[name][1:] if name in ('waist', 'neck') else landmarks[name])]
    except (ValueError, TypeError, AttributeError, KeyError, OverflowError) as error:
        errors.append(str(error))
    return result


def _safe_text(value, name):
    if (not isinstance(value, str) or not value.strip() or value != value.strip()
            or any(unicodedata.category(char).startswith('C') or char in '[]' for char in value)):
        raise ValueError(f'{name} must be nonempty single-line text without controls or configuration blocks')
    try:
        value.encode('cp1252')
    except UnicodeEncodeError as error:
        raise ValueError(f'{name} must be CP1252 encodable') from error
    return value


def serialize_hum(cfg_name, measurements, settings=None) -> bytes:
    """Validate and return CP1252/CRLF HUM text; never create files."""
    cfg_name = _safe_text(cfg_name, 'Model CFG path').replace('/', '\\')
    if (ntpath.isabs(cfg_name) or ntpath.splitdrive(cfg_name)[0]
            or any(part in ('', '.', '..') for part in cfg_name.split('\\'))
            or any(char in cfg_name for char in ':*?"<>|')):
        raise ValueError('Model CFG path must be a safe relative OMSI path')
    if measurements.get('errors'):
        raise ValueError('Human measurements are unresolved: ' + '; '.join(measurements['errors']))
    height = _scalar(measurements.get('height'))
    if height <= 0:
        raise ValueError('Human height must be positive')
    links = measurements.get('links')
    if not isinstance(links, (tuple, list)) or len(links) != 22:
        raise ValueError('Human links require exactly 22 resolved numbers')
    links = [_scalar(value) for value in links]
    values = dict(DEFAULT_SETTINGS)
    if settings is not None:
        if not hasattr(settings, 'items') or set(settings) - set(values):
            raise ValueError('Unknown human settings')
        values.update(settings)
    for name in ('seat_height', 'feetdist', 'mass_kg'):
        values[name] = _scalar(values[name])
    if values['mass_kg'] <= 0 or values['seat_height'] < 0 or values['feetdist'] < 0:
        raise ValueError('Human mass must be positive; seat height and feet distance must be nonnegative')
    walk = values['walk_params']
    if isinstance(walk, (str, bytes)) or not hasattr(walk, '__len__') or len(walk) != 5:
        raise ValueError('Human walk_params requires five finite numbers')
    walk = [_scalar(value) for value in walk]
    voice = _safe_text(values['voice'], 'Voice')
    blocks = [('[model]', [cfg_name]), ('[seatheight]', [_number(values['seat_height'])]),
              ('[humangeom]', [_number(values['feetdist']), _number(height)]),
              ('[links]', [_number(value) for value in links]),
              ('[walk_param]', [_number(value) for value in walk]), ('[voice]', [voice]),
              ('[mass]', [_number(values['mass_kg'] / 1000)])]
    return ('\r\n\r\n'.join('\r\n'.join([tag, *lines]) for tag, lines in blocks) + '\r\n').encode('cp1252')


def _mesh_rigs(obj):
    rigs = {modifier.object for modifier in obj.modifiers
            if modifier.type == 'ARMATURE' and modifier.object is not None}
    parent = obj.parent
    while parent is not None:
        if parent.type == 'ARMATURE':
            rigs.add(parent)
        parent = parent.parent
    return rigs


def _human_candidates(context, armature, objects):
    scene_objects = set(context.scene.objects)
    if armature is None or armature.type != 'ARMATURE' or armature not in scene_objects:
        raise ValueError('Select one human rig in the current scene')
    meshes = []
    for obj in dict.fromkeys(objects):
        if obj not in scene_objects or 'skip_export' in obj or obj.rigid_body or obj.rigid_body_constraint:
            continue
        if obj.type == 'ARMATURE' and obj != armature:
            raise ValueError('Human export requires one rig, not multiple unrelated rigs')
        if obj.type != 'MESH':
            continue
        rigs = _mesh_rigs(obj)
        if rigs and rigs != {armature}:
            raise ValueError(f'{obj.name}: unrelated or multiple human rigs')
        if rigs == {armature}:
            meshes.append(obj)
    return meshes


def human_meshes(context, armature, *, selection_only=True) -> list:
    """Select bound scene meshes without changing selection, including hidden LODs.

    Explicit mesh selection retains its scope. Armature-only selection expands
    to that rig's bound scene meshes; physics/skip_export helpers never count.
    """
    if not selection_only:
        # Other rigs may coexist in a scene, but never enter this human's bundle.
        candidates = [obj for obj in context.scene.objects
                      if obj.type == 'MESH' and armature in _mesh_rigs(obj)]
        return _human_candidates(context, armature, candidates)
    selected = list(context.selected_objects)
    meshes = _human_candidates(context, armature, selected)
    explicit_meshes = any(obj.type == 'MESH' and 'skip_export' not in obj
                          and not obj.rigid_body and not obj.rigid_body_constraint for obj in selected)
    if explicit_meshes:
        return meshes
    if armature in selected:
        return human_meshes(context, armature, selection_only=False)
    return []


def _cfg_value(value, label, *, command=False):
    """Validate source values, not generated newlines/tags, before any file opens."""
    if isinstance(value, str):
        if any(unicodedata.category(char).startswith('C') or
               (char in '[]' and not command) for char in value):
            raise ValueError(f'{label}: controls or configuration injection are not allowed')
        try:
            value.encode('cp1252')
        except UnicodeEncodeError as error:
            raise ValueError(f'{label}: text must be CP1252 encodable') from error
    elif isinstance(value, Real):
        if not isfinite(value):
            raise ValueError(f'{label}: numbers must be finite')
    elif hasattr(value, 'items'):
        for key, item in value.items():
            _cfg_value(item, f'{label}.{key}')
    elif hasattr(value, '__iter__'):
        for item in value:
            _cfg_value(item, label)
    else:
        raise ValueError(f'{label}: unsupported CFG value')


def _human_cfg_props(owner, *, skip_skin=True):
    for block in owner.get('cfg_data', ()):
        if not block:
            raise ValueError('Empty preserved CFG command')
        command = str(block[0]).strip().lower()
        if skip_skin and command in ('[setbone]', '[smoothskin]'):
            continue  # The human renderer replaces these at mesh/material scope.
        _cfg_value(block[0], 'Preserved CFG command', command=True)
        if not (command.startswith('[') and command.endswith(']')
                and '[' not in command[1:] and ']' not in command[:-1]):
            raise ValueError('Invalid preserved CFG command')
        for value in block[1:]:
            _cfg_value(value, 'Preserved CFG parameter')


def _human_output_paths(filepath, meshes, overwrite, textures):
    from . import omsi_paths
    hum_path = os.path.abspath(os.fspath(filepath))
    root, basename = os.path.split(hum_path)
    _safe_text(basename, 'HUM filename')
    if ntpath.splitext(basename)[1].lower() != '.hum':
        raise ValueError('Human destination must have a .hum extension')
    cfg_name = 'model\\' + ntpath.splitext(basename)[0] + '.cfg'
    paths = [omsi_paths.safe_export_path(root, basename),
             omsi_paths.safe_export_path(root, cfg_name)]
    for obj in meshes:
        relative = _safe_text(str(obj.get('export_path', obj.name + '.o3d')), 'Mesh output path')
        normalized = relative.replace('/', '\\')
        if (ntpath.isabs(normalized) or ntpath.splitdrive(normalized)[0]
                or any(part in ('', '..') for part in normalized.split('\\'))
                or any(char in normalized for char in ':*?"<>|')):
            raise ValueError(f'Unsafe human mesh export path: {relative!r}')
        parts = [part for part in normalized.split('\\') if part != '.']
        if parts and parts[0].casefold() == 'model':
            parts.pop(0)
        if not parts:
            raise ValueError(f'Empty human mesh export path: {relative!r}')
        paths.append(omsi_paths.safe_export_path(root, 'model/' + '/'.join(parts)))
    paths.extend(omsi_paths.safe_export_path(root, relative) for _, relative in textures['files'])
    lexical, resolved, checked, existing_files = set(), set(), [], []
    source_keys = {source.casefold() for source in textures['sources']}
    def overlaps(key, previous):
        return any(key == other or key.startswith(other + os.sep)
                   or other.startswith(key + os.sep) for other in previous)
    for path in paths:
        lexical_key, resolved_key = os.path.abspath(path).casefold(), os.path.realpath(path).casefold()
        # Keep the longest case-insensitive existing prefix when the leaf (or
        # several trailing directories) is new. The generic importer resolver
        # deliberately returns the original path on any missing component.
        existing, missing = path, []
        while True:
            matched = omsi_paths.resolve_case_insensitive_path(existing)
            parent, leaf = os.path.split(existing)
            if os.path.lexists(matched) or parent == existing:
                existing = os.path.join(matched, *reversed(missing))
                break
            missing.append(leaf)
            existing = parent
        existing_key = os.path.realpath(existing).casefold()
        resolved_root = os.path.realpath(root)
        if os.path.commonpath((resolved_root, os.path.realpath(existing))) != resolved_root:
            raise ValueError(f'Human output path escapes selected root: {path!r}')
        if overlaps(lexical_key, lexical) or overlaps(resolved_key, resolved) or overlaps(existing_key, resolved):
            raise ValueError(f'Human bundle output paths collide at {path!r}')
        parent = os.path.dirname(existing)
        while parent != os.path.dirname(parent):
            if os.path.lexists(parent) and not os.path.isdir(parent):
                raise ValueError(f'Human output parent path is not a directory: {parent!r}')
            parent = os.path.dirname(parent)
        lexical.add(lexical_key)
        resolved.update((resolved_key, existing_key))
        if os.path.isdir(existing):
            raise ValueError(f'Human output path is an existing directory: {path!r}')
        if (resolved_key in source_keys or existing_key in source_keys
                or (os.path.exists(existing) and any(os.path.samefile(existing, source)
                    for source in textures['sources']))):
            raise ValueError(f'Human output would overwrite a source texture: {path!r}')
        if os.path.exists(existing):
            if any(os.path.samefile(existing, previous) for previous in existing_files):
                raise ValueError(f'Human bundle output paths collide at {path!r}')
            existing_files.append(existing)
        if not overwrite and (os.path.lexists(path) or os.path.lexists(existing)):
            raise ValueError(f'Human output already exists; explicit overwrite consent required: {path!r}')
        checked.append(existing)
    mesh_paths = {id(obj): os.path.relpath(path, os.path.dirname(checked[1])).replace(os.sep, '/')
                  for obj, path in zip(meshes, checked[2:2 + len(meshes)])}
    return checked, cfg_name, mesh_paths


def export_human(filepath, context, armature, meshes, *, settings=None, overrides=None,
                 scale=1.0, overwrite=False, confirm_stale=False, o3d_version=7,
                 export_custom_normals=True, preflight_only=False, turn_180=False,
                 max_texture_size=0, compress_textures=False, dds_converter='',
                 texture_format=None, normalize_arms=False, arm_rest_angle=0.0) -> dict:
    """Preflight a HUM/model/textures bundle and publish HUM last.

    All validation/overwrite refusal happens before destination files are opened.
    Later OS write failures may leave partial model files: this is not a
    multi-file transaction. Source IDs, selection, pose and flags stay untouched.
    Landmark overrides are already final scaled file vectors, not scaled twice.
    normalize_arms shares a temporary rest pose across all LODs, with arms at
    arm_rest_angle degrees (-89..+89): 0 is horizontal, positive below and negative
    above horizontal. Disabled normalization ignores the angle.
    Active/participating mesh or armature Edit mode is refused without flushing
    source edits: measurement and the shared exporter must see the same state.
    preflight_only runs the identical validation/serialization preparation, without
    opening output files. The panel uses a temporary destination for readiness;
    the actual chosen destination and overwrite consent are checked on export.
    """
    from .human_texture_export import staged_textures
    meshes = _human_candidates(context, armature, meshes)
    for obj in (context.view_layer.objects.active, armature, *meshes):
        if obj is not None and obj.type in {'MESH', 'ARMATURE'} and obj.mode == 'EDIT':
            raise ValueError(f'{obj.name}: switch to Object Mode before human export; pending edits are unsupported')
    with staged_textures(meshes, max_texture_size=max_texture_size,
                         compress_textures=compress_textures, dds_converter=dds_converter,
                         texture_format=texture_format) as textures:
        return _export_human_bundle(filepath, context, armature, meshes, textures,
            settings=settings, overrides=overrides, scale=scale, overwrite=overwrite,
            confirm_stale=confirm_stale, o3d_version=o3d_version,
            export_custom_normals=export_custom_normals, preflight_only=preflight_only,
            turn_180=turn_180, normalize_arms=normalize_arms, arm_rest_angle=arm_rest_angle)


def _export_human_bundle(filepath, context, armature, meshes, textures, *, settings, overrides,
                         scale, overwrite, confirm_stale, o3d_version, export_custom_normals,
                         preflight_only, turn_180, normalize_arms, arm_rest_angle=0.0):
    from . import io_o3d_export, o3d_cfg_parser, o3dconvert
    arm_transforms = None
    if normalize_arms:
        # Preserve the existing zero-target call as well as its exact arithmetic.
        arm_transforms = (build_arm_transforms(armature)
                          if type(arm_rest_angle) in (int, float) and arm_rest_angle == 0
                          else build_arm_transforms(armature, rest_angle_degrees=arm_rest_angle))
    # One closed rig admission for deformation, codec preflight and publication,
    # including accepted parent-only and fully disabled-modifier bindings.
    allowed_names = set(armature.data.bones.keys()) if normalize_arms else None
    rest_deformer = (make_rest_deformer(armature, arm_transforms, allowed_names=allowed_names)
                     if arm_transforms is not None else None)
    measurements = _measure_human(armature, meshes, overrides=overrides, scale=scale,
                                  context=context, confirm_stale=confirm_stale, turn_180=turn_180,
                                  arm_transforms=arm_transforms, rest_deformer=rest_deformer)
    paths, cfg_name, mesh_names = _human_output_paths(filepath, meshes, overwrite, textures)
    payload = serialize_hum(cfg_name, measurements, settings)
    hum_path, cfg_path = paths[:2]
    mesh_paths = paths[2:2 + len(meshes)]
    texture_paths = paths[2 + len(meshes):]
    texture_names = textures['names']
    measurements['warnings'].extend(textures['warnings'])
    global_matrix = Matrix.Scale(_scalar(scale), 4)
    if turn_180:
        # O3D vertices are XZY: Y is the vertical axis after preparation.
        global_matrix @= Matrix.Diagonal((-1, 1, -1, 1))
    bone_slots = dict(CANONICAL_SLOTS)
    if turn_180 or arm_transforms is not None:
        # Procedural human slots pivot at fixed signed-X sides, independent of names.
        for name in bone_slots:
            if name.endswith(('_L', '_R')):
                point = armature.matrix_world @ armature.data.bones[name].head_local
                if arm_transforms is not None:
                    point = transform_landmark(arm_transforms, name, point)
                x = -point.x if turn_180 else point.x
                if abs(x) <= 1e-8:
                    raise ValueError(f'{name}: cannot bind a paired human limb on X=0')
                bone_slots[name] = CANONICAL_SLOTS[name[:-1] + ('L' if x < 0 else 'R')]
    metadata = {}
    for obj, path in zip(meshes, mesh_paths):
        _validate_transform(obj)
        _human_cfg_props(obj.data)
        # Legacy discovery happens before rest evaluation hides modifiers.
        mesh_allowed_names = (io_o3d_export._armature_bone_names(obj)
                              if allowed_names is None else allowed_names)
        with prepared_export_mesh(obj, context, global_matrix,
                                  rest_deformer=rest_deformer) as (evaluated, mesh, matrix):
            _cfg_value(matrix, 'Serialized O3D transform')
            geometry = io_o3d_export.prepare_o3d_geometry(
                evaluated, mesh, export_custom_normals, allowed_names=mesh_allowed_names)
            long_indices = io_o3d_export.validate_o3d_geometry(geometry, o3d_version, character_runtime=True)
            if not all(isfinite(value) for vertex in geometry['verts'] for value in vertex):
                raise ValueError(f'{obj.name}: nonfinite serialized human geometry')
            for name, _ in geometry['bones']:
                _safe_text(name, 'Serialized bone name')
            materials = io_o3d_export._build_o3d_materials(path, evaluated.material_slots, cfg_path, texture_names)
            for material in materials:
                _cfg_value(material[-1], 'Material texture path')
            for slot in evaluated.material_slots:
                if slot.material is not None:
                    material = slot.material
                    _human_cfg_props(material)
                    for key in ('type', 'change_var', 'envmap_tex'):
                        if key in material:
                            _cfg_value(material[key], key, command=key == 'type')
                    wrapper = o3d_cfg_parser.o3d_node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=True)
                    for key in ('base_color_texture', 'alpha_texture', 'specular_texture', 'emission_color_texture'):
                        texture = getattr(wrapper, key, None)
                        if texture is not None and texture.image is not None:
                            _cfg_value(o3d_cfg_parser.texture_name(cfg_path, texture.image, texture_names), 'CFG texture path')
                    bump = io_o3d_export.blender_compat.find_bump_map(wrapper)
                    if bump is not None:
                        _cfg_value(o3d_cfg_parser.texture_name(cfg_path, bump[0], texture_names), 'CFG bump texture path')
                        _cfg_value(bump[1], 'CFG bump strength')
            # Exercise the real binary codec, including packing/range validation,
            # in memory. The subsequent shared exporter uses the same data path.
            try:
                o3dconvert.export_o3d(BytesIO(), geometry['verts'], geometry['tris'], materials,
                                      geometry['bones'], matrix, version=o3d_version,
                                      long_triangle_indices=long_indices, invert_triangle_winding=True)
            except (OverflowError, TypeError) as error:
                raise ValueError(f'{obj.name}: invalid serialized human geometry: {error}') from error
            metadata[id(obj)] = {'smoothskin': geometry['smoothskin'],
                                 'bones': {name: bone_slots[name] for name, _ in geometry['bones']
                                           if name in bone_slots}}
    scene = context.scene
    for key in ('groups', 'friendlyname', 'tree'):
        if key in scene:
            _cfg_value(scene[key], key)
    _human_cfg_props(scene, skip_skin=False)
    stream = StringIO()
    o3d_cfg_parser._write_cfg_stream(
        stream, cfg_path, context, False, objects_override=meshes, smoothskin_by_object=metadata,
        human_bindings_by_object={key: data['bones'] for key, data in metadata.items()},
        texture_names=texture_names, mesh_paths=mesh_names)
    try:
        stream.getvalue().encode('cp1252')
    except UnicodeEncodeError as error:
        raise ValueError('Model CFG must be CP1252 encodable') from error
    if preflight_only:
        return {'measurements': measurements, 'warnings': measurements['warnings'],
                'max_texture_size': textures['max_texture_size']}
    for (staged, _), destination in zip(textures['files'], texture_paths):
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        shutil.copyfile(staged, destination)
    os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
    io_o3d_export.do_export(cfg_path, context, global_matrix, False, o3d_version,
                           export_custom_normals, objects=meshes, human_bindings=True,
                           human_bone_slots=bone_slots, texture_names=texture_names, mesh_paths=mesh_names,
                           rest_deformer=rest_deformer, allowed_names=allowed_names)
    with open(hum_path, 'wb') as stream:
        stream.write(payload)
    return {'hum_path': hum_path, 'cfg_path': cfg_path, 'mesh_paths': mesh_paths,
            'texture_paths': texture_paths, 'max_texture_size': textures['max_texture_size'],
            'warnings': measurements['warnings']}


def physics_diagnostics(armature, objects) -> dict:
    """Read explicit native/MMD associations; never infer pivots or body mass."""
    objects = list(objects)
    associations = {}
    for obj in objects:
        if not obj.rigid_body:
            continue
        for constraint in obj.constraints:
            if (getattr(constraint, 'target', None) == armature
                    and getattr(constraint, 'subtarget', '') in armature.data.bones):
                associations[obj.name] = constraint.subtarget
                break
        if obj.name not in associations:
            mmd = getattr(obj, 'mmd_rigid', None)
            bone = getattr(mmd, 'bone', '') if mmd is not None else ''
            if not bone:
                native = obj.get('mmd_rigid', {})
                bone = native.get('bone', '') if hasattr(native, 'get') else ''
            if bone in armature.data.bones:
                associations[obj.name] = bone
    categories = {}
    for obj in objects:
        joint = obj.rigid_body_constraint
        if joint is None:
            continue
        names = ' '.join([obj.name, *(body.name + ' ' + associations.get(body.name, '')
                                     for body in (joint.object1, joint.object2) if body)]).lower()
        category = ('skirt' if any(token in names for token in ('skirt', 'スカート')) else
                    'hair' if any(token in names for token in ('hair', '髪', '发', '马尾', 'アホ毛')) else
                    'accessory' if any(token in names for token in ('accessory', 'acc_', '_acc', '飾')) else 'other')
        categories[category] = categories.get(category, 0) + 1
    return {'body_count': sum(obj.rigid_body is not None for obj in objects),
            'joint_count': sum(obj.rigid_body_constraint is not None for obj in objects),
            'bone_associations': associations, 'joint_categories': categories}
