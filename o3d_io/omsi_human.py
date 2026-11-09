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
import unicodedata

from mathutils import Matrix, Vector

from .io_o3d_export import prepared_export_mesh
from .mmd_rig import CANONICAL_NAMES, _source_segment, read_source_rig


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
                  confirm_stale=False) -> dict:
    """Return errors/warnings, 22 links or None, height, and final XYZ landmarks.

    Bounds use primary bound meshes evaluated in rest space. Metadata is only
    consumed if current or explicitly confirmed; overrides always take priority.
    Errors block serialization, not generic conversion/export.
    """
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
        primary = _primary_meshes(armature, meshes, context, warnings)
        if not primary:
            raise ValueError('Human height requires nonempty primary character meshes, not physics/LODs')
        low = high = None
        for obj in primary:
            _validate_transform(obj)
            with prepared_export_mesh(obj, context, Matrix.Scale(scale, 4)) as (_, mesh, _):
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

        def final(point):
            return (armature.matrix_world @ _vector(point)) * scale

        def head(name):
            return final(armature.data.bones[name].head_local)

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
            raw['finger'] = (final(points['finger_L']), final(points['finger_R']))
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
