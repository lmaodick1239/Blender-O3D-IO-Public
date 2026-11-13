"""Owned, static viewport diagnostics built from the human export stream.

Arm equations: native func-00626b98.c:531-625,1501-1802 and openOMSI
human_omsi.rs a19eac8:34-140,414-503,528-609. Column-vector matrices below
are the transpose of the D3DX row-vector graph in file (X right/Y up/Z forward)
coordinates. This isolates arms: torso/legs stay static, walk amplitude is 18,
stoop/reach/hold/running/smoothing are absent, and seated lowering is fixed 67.
It is neither a full game animation nor an automatic collision check. Reused
source material graphs give context, not proof of game shader parity.
"""
import math

import bpy
from bpy.app.handlers import persistent
from mathutils import Matrix, Vector

from . import human_arm_normalization as normalization
from . import io_o3d_export, mmd_rig, omsi_human

_session = None


def arm_pose_matrices(joints, pose, phase=0.0, *, beta=80.0):
    """Return the diagnostic graph in canonical file coordinates; REST is identity."""
    result = {name: Matrix.Identity(4) for name in mmd_rig.CANONICAL_NAMES}
    if pose == 'REST':
        return result
    if not math.isfinite(phase) or not math.isfinite(beta):
        raise ValueError('Arm preview phase and lowering must be finite')
    if pose == 'STANDING':
        lowering, twist = beta, -30
        swing, bend, hand = (-3, -3), (29, 29), (0, 0, 0)
    elif pose == 'WALKING':
        wave = math.sin(2 * math.pi * phase)
        lowering, twist = beta - 3, -30
        swing = ((wave - .2) * 18, (-wave - .2) * 18)
        bend, hand = (1.5 * (wave + 1) * 18, 1.2 * (1 - wave) * 18), (0, 0, 0)
    elif pose == 'SEATED':
        lowering, twist = 67, -58
        swing, bend, hand = (35, 35), (46, 46), (41, -26, 5)
    else:
        raise ValueError('Unknown arm preview pose: ' + str(pose))

    def rotate(degrees, axis):
        return Matrix.Rotation(degrees * .017453292, 4, axis)

    def pivot(point, matrix):
        return Matrix.Translation(point) @ matrix @ Matrix.Translation(-point)

    for side in ('L', 'R'):
        upper, forearm, palm = (stem + '_' + side for stem in ('OA', 'UA', 'Hand'))
        shoulder, elbow, wrist = (Vector(joints[name]) for name in (upper, forearm, palm))
        index, sign = (0, 1) if shoulder.x < 0 else (1, -1)
        result[upper] = pivot(shoulder, rotate(-3 * sign, 'Y') @ rotate(lowering * sign, 'Z')
                              @ rotate(swing[index] * sign, 'Y') @ rotate(twist * sign, elbow - shoulder))
        result[forearm] = result[upper] @ pivot(elbow, rotate(bend[index] * sign, 'Y'))
        hx, hz, hy = hand
        result[palm] = result[forearm] @ pivot(wrist, rotate(-hx, 'X')
                          @ rotate(hz * sign, 'Z') @ rotate(hy * sign, 'Y'))
    return result


def _runtime_joints(armature, measurements, transforms, turn_180):
    """HUM serializes symmetric final XYZ landmarks, not raw per-side heads."""
    joints = {}
    for side in ('L', 'R'):
        name = 'OA_' + side
        point = armature.matrix_world @ armature.data.bones[name].head_local
        if transforms is not None:
            point = normalization.transform_landmark(transforms, name, point)
        x = -point.x if turn_180 else point.x
        if abs(x) <= 1e-8:
            raise ValueError(f'{name}: cannot bind a paired human limb on X=0')
        sign = -1 if x < 0 else 1
        for stem, landmark in (('OA', 'shoulder'), ('UA', 'elbow'), ('Hand', 'hand')):
            x, y, z = measurements['landmarks'][landmark]
            joints[stem + '_' + side] = Vector((sign * x, z, y))
    return joints


def _display_geometry(geometry, matrices):
    """Apply only admitted serialized weights, retaining codec order for ties."""
    weights = [[] for _ in geometry['verts']]
    for name, entries in geometry['bones']:
        for index, weight in entries:
            if math.isfinite(weight) and weight > 0:
                weights[index].append((name, weight))
    identity = Matrix.Identity(4)
    points, normals = [], []
    for raw, entries in zip(geometry['verts'], weights):
        point, normal = Vector(raw[:3]), Vector(raw[3:6])
        if entries:
            if not geometry['smoothskin']:
                entries = [max(entries, key=lambda entry: entry[1])]
            mass = sum(weight for _, weight in entries)
            point = sum((weight / mass * (matrices.get(name, identity) @ point)
                         for name, weight in entries), Vector())
            normal = sum((weight / mass * (matrices.get(name, identity).to_3x3() @ normal)
                          for name, weight in entries), Vector()).normalized()
        points.append((point.x, point.z, point.y))
        normals.append((normal.x, normal.z, normal.y))
    return points, normals


def _live(item, collection):
    try:
        return collection.get(item.name) == item
    except (ReferenceError, AttributeError):
        return False


def _release(session):
    if session is None:
        return
    # Only these exact owned IDs are removed; material slots reference source IDs.
    for obj in session['objects']:
        if _live(obj, bpy.data.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in session['meshes']:
        if _live(mesh, bpy.data.meshes):
            bpy.data.meshes.remove(mesh, do_unlink=True)
    if _live(session['collection'], bpy.data.collections):
        bpy.data.collections.remove(session['collection'])


def clear_preview():
    """Idempotently discard only this module's session, even after source removal."""
    global _session
    previous, _session = _session, None
    _release(previous)


def is_preview_active(armature=None):
    if _session is None or not _live(_session['armature'], bpy.data.objects):
        return False
    return ((armature is None or _session['armature'] == armature)
            and any(_live(obj, bpy.data.objects) for obj in _session['objects']))


def refresh_preview(context, armature, meshes, *, normalize_arms=False, arm_rest_angle=0.0,
                    scale=1.0, turn_180=False, confirm_stale=False, overrides=None,
                    export_custom_normals=True, pose='REST', phase=.25, beta=80.0):
    """Stage a replacement from the exact prepared HUM export stream, then swap.

    Display C(x,y,z)=(x,z,y) reverses file handedness. The codec reverses each
    prepared triangle for file output; reversing it again for C gives the
    prepared order below. UV0 similarly undoes the exported V inversion.
    Local vertices are display coordinates; a shared object X translation puts
    the preview's minimum X .25 units beyond the original source's maximum X.
    Source selection, visibility, mode, pose and material graphs are untouched.
    """
    global _session
    meshes = omsi_human._human_candidates(context, armature, meshes)
    for obj in (context.view_layer.objects.active, armature, *meshes):
        if obj is not None and obj.type in {'MESH', 'ARMATURE'} and obj.mode == 'EDIT':
            raise ValueError(f'{obj.name}: switch to Object Mode before human export; pending edits are unsupported')
    transforms = None
    if normalize_arms:
        transforms = (normalization.build_arm_transforms(armature)
                      if type(arm_rest_angle) in (int, float) and arm_rest_angle == 0
                      else normalization.build_arm_transforms(armature, rest_angle_degrees=arm_rest_angle))
    allowed = set(armature.data.bones.keys()) if normalize_arms else None
    deformer = normalization.make_rest_deformer(armature, transforms, allowed_names=allowed) if normalize_arms else None
    # Same internal measurement entry as the bundle: share this captured admission
    # and deformer across bounds, landmarks and all displayed primary meshes.
    measurements = omsi_human._measure_human(armature, meshes, overrides=overrides, scale=scale,
        context=context, confirm_stale=confirm_stale, turn_180=turn_180,
        arm_transforms=transforms, rest_deformer=deformer)
    if measurements['errors']:
        raise ValueError('; '.join(measurements['errors']))
    primary = omsi_human._primary_meshes(armature, meshes, context, [])
    matrices = arm_pose_matrices(_runtime_joints(armature, measurements, transforms, turn_180), pose, phase, beta=beta)
    global_matrix = Matrix.Scale(omsi_human._scalar(scale), 4)
    if turn_180:
        global_matrix @= Matrix.Diagonal((-1, 1, -1, 1))
    staged = {'armature': armature, 'objects': [], 'meshes': [],
              'collection': bpy.data.collections.new('OMSI Arm Preview')}
    rest_min = None
    try:
        for source in primary:
            omsi_human._validate_transform(source)
            admitted = io_o3d_export._armature_bone_names(source) if allowed is None else allowed
            with io_o3d_export.prepared_export_mesh(source, context, global_matrix, rest_deformer=deformer) as (evaluated, mesh, _):
                geometry = io_o3d_export.prepare_o3d_geometry(evaluated, mesh, export_custom_normals, allowed_names=admitted)
                io_o3d_export.validate_o3d_geometry(geometry, character_runtime=True)
                if not all(math.isfinite(value) for vertex in geometry['verts'] for value in vertex):
                    raise ValueError(f'{source.name}: nonfinite serialized human geometry')
                materials = [slot.material.original if slot.material else None for slot in evaluated.material_slots]
            for raw in geometry['verts']:
                rest_min = raw[0] if rest_min is None else min(rest_min, raw[0])
            points, normals = _display_geometry(geometry, matrices)
            data = bpy.data.meshes.new('OMSI Arm Preview ' + source.name)
            staged['meshes'].append(data)
            data.from_pydata(points, [], [tri[:3] for tri in geometry['tris']])
            for material in materials:
                data.materials.append(material)
            uv = data.uv_layers.new(name='UVMap')
            for polygon, triangle in zip(data.polygons, geometry['tris']):
                polygon.material_index = triangle[3]
                polygon.use_smooth = True
            for loop in data.loops:
                raw = geometry['verts'][loop.vertex_index]
                uv.data[loop.index].uv = (raw[6], 1 - raw[7])
            data.normals_split_custom_set([normals[loop.vertex_index] for loop in data.loops])
            data.update()
            obj = bpy.data.objects.new('OMSI Arm Preview ' + source.name, data)
            staged['objects'].append(obj)
            obj['skip_export'] = True
            obj.hide_select = obj.hide_render = True
            staged['collection'].objects.link(obj)
        if rest_min is None:
            raise ValueError('Human preview requires nonempty serialized primary geometry')
        # Export preparation has restored modifier flags; evaluate the visible
        # source pose/shape now, including geometry generated on empty base meshes.
        depsgraph = context.evaluated_depsgraph_get()
        source_max = max((evaluated.matrix_world @ vertex.co).x
                         for evaluated in (source.evaluated_get(depsgraph) for source in primary)
                         for vertex in evaluated.data.vertices)
        offset = source_max - rest_min + .25
        for obj in staged['objects']:
            obj.location.x = offset
        context.scene.collection.children.link(staged['collection'])
    except Exception:
        _release(staged)
        raise
    previous, _session = _session, staged
    _release(previous)
    return {'objects': tuple(staged['objects']), 'measurements': measurements, 'offset': (offset, 0, 0)}


@persistent
def _clear_on_file_change(*_args):
    clear_preview()


def register():
    for handlers in (bpy.app.handlers.save_pre, bpy.app.handlers.load_pre):
        if _clear_on_file_change not in handlers:
            handlers.append(_clear_on_file_change)


def unregister():
    clear_preview()
    for handlers in (bpy.app.handlers.save_pre, bpy.app.handlers.load_pre):
        while _clear_on_file_change in handlers:
            handlers.remove(_clear_on_file_change)
