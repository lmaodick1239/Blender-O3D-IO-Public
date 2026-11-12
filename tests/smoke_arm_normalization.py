"""Standalone: blender --background --factory-startup --disable-autoexec
--python-exit-code 1 --python tests/smoke_arm_normalization.py -- --check plan
Public synthetic checks preserve caller state and never load private scenes.
"""
import argparse
from contextlib import contextmanager
import importlib
import math
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace

import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from smoke_support import load_addon


def close(actual, expected):
    assert len(actual) == len(expected), (actual, expected)
    assert all(abs(a - b) < 2e-5 for a, b in zip(actual, expected)), (actual, expected)


def matrix_close(actual, expected):
    assert all(abs(actual[row][col] - expected[row][col]) < 1e-7
               for row in range(4) for col in range(4)), (actual, expected)


def refuses(call, bone):
    try:
        call()
    except ValueError as error:
        assert bone in str(error), (bone, str(error))
    else:
        raise AssertionError('invalid arm input was accepted: ' + bone)


@contextmanager
def preserve_context():
    active = bpy.context.view_layer.objects.active
    selected = tuple(bpy.context.selected_objects)
    mode = active.mode if active else 'OBJECT'
    if active and mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    try:
        yield
    finally:
        current = bpy.context.view_layer.objects.active
        if current and current.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        for obj in selected:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = active
        if active and mode != 'OBJECT':
            bpy.ops.object.mode_set(mode=mode)


@contextmanager
def arm_fixture(addon, *, left_sign=-1, upper=35, forearm=35, y_offsets=(0, 0),
                patch=None, missing=None, world=None):
    rigmod = importlib.import_module(addon.__name__ + '.o3d_io.mmd_rig')
    points = {'Main': (0, 0, 1.15), 'Hip': (0, 0, .95), 'Head': (0, 0, 1.65),
              'OS_L': (-.1, 0, .95), 'OS_R': (.1, 0, .95),
              'US_L': (-.1, 0, .5), 'US_R': (.1, 0, .5)}
    for side, sign in (('L', left_sign), ('R', -left_sign)):
        # Independent literal lengths and known elevations, never planner output.
        shoulder = Vector((sign * .2, 0, 1.4))
        alpha, beta = math.radians(upper), math.radians(forearm)
        elbow = shoulder + Vector((sign * .30 * math.cos(alpha), y_offsets[0],
                                   -.30 * math.sin(alpha)))
        wrist = elbow + Vector((sign * .25 * math.cos(beta), y_offsets[1],
                                -.25 * math.sin(beta)))
        points.update({f'OA_{side}': shoulder, f'UA_{side}': elbow,
                       f'Hand_{side}': wrist})
    points = {name: Vector(point) for name, point in points.items()}
    if patch:
        points.update({name: Vector(point) for name, point in patch.items()})
    segments = {}
    for name, point in points.items():
        if name == missing:
            continue
        tail = point + Vector((0, 0, .08))
        if name.startswith('OA_'):
            tail = points['UA_' + name[3:]]
        elif name.startswith('UA_'):
            tail = points['Hand_' + name[3:]]
        segments[name] = (point, tail)
    rig = rigmod._create_armature('Arm normalization fixture', segments,
                                  bpy.context.scene.collection, matrix_world=world)
    try:
        yield rig, points
    finally:
        if rig.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        data = rig.data
        bpy.data.objects.remove(rig, do_unlink=True)
        bpy.data.armatures.remove(data)


def rig_state(rig):
    return (tuple(tuple(row) for row in rig.matrix_world), rig.data.pose_position,
            tuple((bone.name, tuple(bone.head_local), tuple(bone.tail_local),
                   tuple(tuple(row) for row in bone.matrix_local)) for bone in rig.data.bones),
            tuple((bone.name, tuple(tuple(row) for row in bone.matrix_basis))
                  for bone in rig.pose.bones), dict(rig.items()),
            tuple(bpy.context.selected_objects), bpy.context.view_layer.objects.active, rig.mode)


def assert_arm_transform_plan(addon):
    # Catches wrong rotation signs/pivots, coupled elevations, missing validation,
    # mutated source state, and landmark transforms applied to unrelated anatomy.
    with preserve_context():
        normalization = importlib.import_module(addon.__name__ + '.o3d_io.human_arm_normalization')
        rigmod = importlib.import_module(addon.__name__ + '.o3d_io.mmd_rig')
        identity = Matrix.Identity(4)
        for left_sign in (-1, 1):
            for upper, forearm, offsets in ((35, 35, (0, 0)), (0, 0, (0, 0)),
                                            (20, -10, (.015, -.012)),
                                            (-20, 40, (0, 0))):
                with arm_fixture(addon, left_sign=left_sign, upper=upper,
                                 forearm=forearm, y_offsets=offsets) as (rig, points):
                    rig['arm_test_marker'] = 'unchanged'
                    rig.pose.bones['OA_L'].rotation_mode = 'XYZ'
                    rig.pose.bones['OA_L'].rotation_euler.y = .4
                    bpy.context.view_layer.update()
                    before = rig_state(rig)
                    transforms = normalization.build_arm_transforms(rig)
                    assert rig_state(rig) == before
                    assert set(transforms) == set(rigmod.CANONICAL_NAMES)
                    for side, sign in (('L', left_sign), ('R', -left_sign)):
                        oa, ua, hand = (stem + '_' + side for stem in ('OA', 'UA', 'Hand'))
                        shoulder, elbow, wrist = (points[name] for name in (oa, ua, hand))
                        raised_elbow = Vector((sign * .50, offsets[0], 1.4))
                        raised_wrist = Vector((sign * .75, sum(offsets), 1.4))
                        close(transforms[oa] @ shoulder, shoulder)
                        close(transforms[oa] @ elbow, raised_elbow)
                        close(transforms[ua] @ elbow, raised_elbow)
                        close(transforms[ua] @ wrist, raised_wrist)
                        matrix_close(transforms[hand], transforms[ua])
                        assert abs((transforms[oa] @ elbow - transforms[oa] @ shoulder).length
                                   - (elbow - shoulder).length) < 2e-5
                        assert abs((transforms[ua] @ wrist - transforms[ua] @ elbow).length
                                   - (wrist - elbow).length) < 2e-5
                        for name in (oa, ua, hand):
                            if upper == forearm == 0:
                                matrix_close(transforms[name], identity)
                        finger = wrist + Vector((sign * .1 * math.cos(math.radians(forearm)),
                                                 0, -.1 * math.sin(math.radians(forearm))))
                        original = finger.copy()
                        close(normalization.transform_landmark(transforms, hand, finger),
                              (sign * .85, sum(offsets), 1.4))
                        close(finger, original)
                    for name in ('Main', 'Hip', 'Head', 'OS_L', 'OS_R', 'US_L', 'US_R'):
                        matrix_close(transforms[name], identity)
                        close(normalization.transform_landmark(transforms, name, points[name]),
                              points[name])
                    neck = Vector((0, .02, 1.55))
                    returned = normalization.transform_landmark(transforms, 'extra_neck', neck)
                    close(returned, neck)
                    assert returned is not neck
                    assert rig_state(rig) == before

        # World-space pivots must include a rig's positive uniform scale/translation.
        world = Matrix.Translation((.025, .07, .5)) @ Matrix.Scale(1.5, 4)
        with arm_fixture(addon, world=world) as (rig, points):
            transforms = normalization.build_arm_transforms(rig)
            for side, sign in (('L', -1), ('R', 1)):
                close(transforms['OA_' + side] @ (world @ points['OA_' + side]),
                      (sign * .30 + .025, .07, 2.6))
                close(transforms['UA_' + side] @ (world @ points['Hand_' + side]),
                      (sign * 1.125 + .025, .07, 2.6))

        # Each rejected anatomical case must identify the offending bone/side.
        for side, sign in (('L', -1), ('R', 1)):
            oa, ua, hand = (stem + '_' + side for stem in ('OA', 'UA', 'Hand'))
            shoulder = Vector((sign * .2, 0, 1.4))
            elbow = Vector((sign * .5, 0, 1.4))
            for delta in ((-sign * .3, 0, 0), (0, 0, -.3), (0, 0, 0),
                          (sign * 1e-8, 0, -.3), (sign * .3, .08, 0)):
                with arm_fixture(addon, upper=0, forearm=0,
                                 patch={ua: shoulder + Vector(delta)}) as (rig, _):
                    refuses(lambda: normalization.build_arm_transforms(rig), oa)
            for delta in ((-sign * .25, 0, 0), (0, 0, -.25), (0, 0, 0),
                          (sign * .25, .07, 0)):
                with arm_fixture(addon, upper=0, forearm=0,
                                 patch={hand: elbow + Vector(delta)}) as (rig, _):
                    refuses(lambda: normalization.build_arm_transforms(rig), ua)
            with arm_fixture(addon, missing=hand) as (rig, _):
                refuses(lambda: normalization.build_arm_transforms(rig), hand)
            for x in (0, -sign * .2):
                with arm_fixture(addon, patch={oa: (x, 0, 1.4)}) as (rig, _):
                    refuses(lambda: normalization.build_arm_transforms(rig), oa)
            for value in (float('nan'), float('inf')):
                with arm_fixture(addon) as (rig, _):
                    bpy.context.view_layer.objects.active = rig
                    bpy.ops.object.mode_set(mode='EDIT')
                    rig.data.edit_bones[hand].head.x = value
                    rig.data.edit_bones[hand].tail.x = value
                    bpy.ops.object.mode_set(mode='OBJECT')
                    assert hand in rig.data.bones, 'nonfinite fixture bone was discarded'
                    # Blender clamps an assigned infinity to FLT_MAX; finite scale
                    # overflows it in world space, exercising the public boundary.
                    rig.matrix_world = Matrix.Scale(2, 4)
                    assert not all(math.isfinite(v) for v in
                                   rig.matrix_world @ rig.data.bones[hand].head_local)
                    refuses(lambda: normalization.build_arm_transforms(rig), hand)
        with arm_fixture(addon, missing='Head') as (rig, _):
            refuses(lambda: normalization.build_arm_transforms(rig), 'Head')
        for value in (float('nan'), float('inf')):
            with arm_fixture(addon) as (rig, _):
                world = Matrix.Identity(4)
                world[0][3] = value
                rig.matrix_world = world
                refuses(lambda: normalization.build_arm_transforms(rig), 'OA_L')
        refuses(lambda: normalization.build_arm_transforms(None), 'armature')
        obj = bpy.data.objects.new('Not an armature', None)
        try:
            refuses(lambda: normalization.build_arm_transforms(obj), 'armature')
        finally:
            bpy.data.objects.remove(obj)


def yaw(point, degrees):
    # Scalar oracle: independent of planner matrices and production deformation.
    x, y, z = point
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return Vector((c * x + s * z, y, -s * x + c * z))


def expected_point(point, name, points):
    if name not in ('OA_L', 'UA_L', 'Hand_L', 'OA_R', 'UA_R', 'Hand_R'):
        return point.copy()
    side = name[-1]
    sign = -1 if side == 'L' else 1
    shoulder = points['OA_' + side]
    raised = shoulder + Vector((sign * .30, 0, 0))
    upper = shoulder + yaw(point - shoulder, -sign * 35)
    return upper if name.startswith('OA_') else raised + yaw(upper - raised, sign * 25)


@contextmanager
def skin_fixture(addon, *, custom=False):
    with arm_fixture(addon, upper=35, forearm=10) as (rig, points):
        bpy.context.view_layer.objects.active = rig
        bpy.ops.object.mode_set(mode='EDIT')
        extra = rig.data.edit_bones.new('Extra')
        extra.head, extra.tail = (0, 0, 1), (0, 0, 1.1)
        bpy.ops.object.mode_set(mode='OBJECT')
        world = (Matrix.Translation((.04, -.03, .2)) @ Matrix.Rotation(.23, 4, 'Z')
                 @ Matrix.Diagonal((1.7, .8, 1.2, 1)))
        # Non-unit sums catch omitted weight normalization. Helper mass must not
        # dilute the admitted weights; Extra is an admitted identity bone.
        bindings = [({'OA_L': .4},) * 3, ({'UA_L': .7},) * 3,
                    ({'Hand_L': .2},) * 3, ({'OA_R': .6},) * 3,
                    ({'UA_R': .3},) * 3, ({'Hand_R': .8},) * 3,
                    ({'Main': .2, 'OA_L': .6, 'helper': 1.},
                     {'Main': .4, 'OA_L': .4}, {'Main': .6, 'OA_L': .2}),
                    ({'OA_L': .2, 'UA_L': .3},) * 3,
                    ({'Main': .3},) * 3, ({'Extra': .5},) * 3,
                    ({'helper': .9, 'OA_L': 0.},) * 3]
        vertices, faces, weights = [], [], []
        for index, triangle in enumerate(bindings):
            side = 'R' if 3 <= index <= 5 else 'L'
            pivot = points[('UA_' if index in (0, 3, 6, 7) else 'Hand_') + side]
            start = len(vertices)
            for offset, entries in zip(((0, 0, 0), (.035, .012, .009), (.006, .027, .04)), triangle):
                vertices.append(world.inverted() @ (pivot + Vector(offset)))
                weights.append(entries)
            faces.append((start, start + 1, start + 2))
        # A shared vertex with different authored corner normals catches using
        # vertex normals or wrong loop-to-vertex associations.
        faces.append((0, 2, 3))
        data = bpy.data.meshes.new('Arm skin fixture')
        data.from_pydata(vertices, [], faces)
        data.update()
        obj = bpy.data.objects.new('Arm skin fixture', data)
        bpy.context.scene.collection.objects.link(obj)
        obj.matrix_world = world
        material = bpy.data.materials.new('Arm fixture material')
        data.materials.append(material)
        data.materials.append(None)
        for index, polygon in enumerate(data.polygons):
            polygon.material_index = index % 2
            polygon.use_smooth = custom
        for name in ('helper', 'Main', 'OA_L', 'UA_L', 'Hand_L', 'Extra', 'OA_R', 'UA_R', 'Hand_R'):
            group = obj.vertex_groups.new(name=name)
            for index, entries in enumerate(weights):
                if name in entries:
                    group.add([index], entries[name], 'REPLACE')
        for name in ('Editing', 'Render'):
            uv = data.uv_layers.new(name=name)
            for index, item in enumerate(uv.uv):
                item.vector = ((index % 5) / 7, (index % 7) / 9)
        data.uv_layers[1].active_render = True
        if custom:
            data.normals_split_custom_set([Vector((.2 + i % 3 * .1, .5, .7)).normalized()
                                           for i in range(len(data.loops))])
        modifier = obj.modifiers.new('Source pose must be ignored', 'ARMATURE')
        modifier.object = rig
        modifier.show_viewport, modifier.show_render = True, False
        rig.pose.bones['OA_L'].rotation_mode = 'XYZ'
        rig.pose.bones['OA_L'].rotation_euler.y = .31
        rig['arm_test_marker'] = 'keep'
        key = obj.shape_key_add(name='Basis')
        key = obj.shape_key_add(name='Unapplied shape')
        key.data[0].co.y += .02
        key.value = 0
        bpy.context.view_layer.update()
        try:
            yield rig, obj, points, weights
        finally:
            bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.meshes.remove(data)
            bpy.data.materials.remove(material)


def mesh_state(obj, mesh=None):
    mesh = obj.data if mesh is None else mesh
    return {'coordinates': tuple(tuple(v.co) for v in mesh.vertices),
            'normals': tuple(tuple(n.vector) for n in mesh.corner_normals),
            'custom': mesh.has_custom_normals,
            'memberships': tuple(tuple((g.group, g.weight) for g in v.groups) for v in mesh.vertices),
            'groups': tuple((g.index, g.name) for g in obj.vertex_groups),
            'polygons': tuple((tuple(p.vertices), p.material_index, p.use_smooth) for p in mesh.polygons),
            'loops': tuple(loop.vertex_index for loop in mesh.loops),
            'edges': tuple((tuple(edge.vertices), edge.use_edge_sharp) for edge in mesh.edges),
            'uvs': tuple((uv.name, uv.active_render, tuple(tuple(v.vector) for v in uv.uv))
                         for uv in mesh.uv_layers),
            'active_uv': mesh.uv_layers.active_index,
            'materials': tuple(material.original if material else None for material in mesh.materials),
            'world': tuple(tuple(row) for row in obj.matrix_world),
            'modifiers': tuple((m.name, m.type, m.show_viewport, m.show_render, m.object)
                               for m in obj.modifiers),
            'shape_keys': tuple((k.name, k.value, tuple(tuple(p.co) for p in k.data))
                                for k in obj.data.shape_keys.key_blocks),
            'selection': tuple(bpy.context.selected_objects),
            'active': bpy.context.view_layer.objects.active,
            'mode': bpy.context.object.mode if bpy.context.object else None}


def expected_skin(obj, points, weights):
    result = []
    for vertex, entries in zip(obj.data.vertices, weights):
        point = obj.matrix_world @ vertex.co
        admitted = [(name, weight) for name, weight in entries.items()
                    if name != 'helper' and math.isfinite(weight) and weight > 0]
        mass = sum(weight for _, weight in admitted)
        result.append(sum((weight / mass * expected_point(point, name, points)
                           for name, weight in admitted), Vector()) if mass else point)
    return result


def source_state(rig, obj):
    return rig_state(rig), mesh_state(obj)


def assert_callback_cleanup(exporter, obj, rig):
    # Forward to the real evaluated mesh lifecycle; only observe cleanup.
    cleared, received = [], []
    class Evaluated:
        def __init__(self, evaluated):
            self.evaluated = evaluated

        def to_mesh(self, **kwargs):
            return self.evaluated.to_mesh(**kwargs)

        def to_mesh_clear(self):
            cleared.append(True)
            self.evaluated.to_mesh_clear()

    class Source:
        def __getattr__(self, name):
            return getattr(obj, name)

        def __contains__(self, key):
            return key in obj

        def evaluated_get(self, depsgraph):
            return Evaluated(obj.evaluated_get(depsgraph))

    def fail(evaluated_object, mesh):
        received.append(mesh)
        mesh.vertices[0].co.x += 10
        raise RuntimeError('callback cleanup sentinel')

    before = source_state(rig, obj)
    try:
        with exporter.prepared_export_mesh(Source(), bpy.context, rest_deformer=fail):
            raise AssertionError('failing callback yielded a mesh')
    except RuntimeError as error:
        assert str(error) == 'callback cleanup sentinel'
    assert received and cleared == [True], 'temporary evaluated mesh was not cleared'
    assert source_state(rig, obj) == before
    with preserve_context(), tempfile.TemporaryDirectory(prefix='o3d-arm-failure-') as directory:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        before = source_state(rig, obj)
        destination = Path(directory) / 'not-published.o3d'
        try:
            exporter.do_export(str(destination), bpy.context, Matrix.Identity(4), False, 7,
                               objects=[Source()], rest_deformer=fail)
        except RuntimeError as error:
            assert str(error) == 'callback cleanup sentinel'
        else:
            raise AssertionError('callback failure did not propagate through do_export')
        assert cleared == [True, True], 'do_export leaked its temporary mesh'
        assert not destination.exists()
        assert source_state(rig, obj) == before


def assert_weight_boundaries(normalization, exporter, rig, obj, points):
    # Blender clamps authored weights; inject malformed entries only at this
    # boundary while keeping the actual temporary mesh and coordinate writes.
    indices = {group.name: group.index for group in obj.vertex_groups}
    callback = normalization.make_rest_deformer(rig, normalization.build_arm_transforms(rig))

    class Vertex:
        def __init__(self, vertex, entries):
            self.vertex = vertex
            self.groups = [SimpleNamespace(group=indices[name], weight=value)
                           for name, value in entries]

        @property
        def co(self):
            return self.vertex.co

        @co.setter
        def co(self, value):
            self.vertex.co = value

    class Mesh:
        def __init__(self, mesh):
            self.mesh = mesh
            self.vertices = list(mesh.vertices)
            self.vertices[0] = Vertex(mesh.vertices[0], [('OA_L', .2), ('Main', .6),
                ('helper', 100.), ('UA_L', float('nan')), ('Hand_L', float('inf')), ('Extra', -1.)])
            self.vertices[1] = Vertex(mesh.vertices[1], [('OA_L', 0.), ('Main', -1.),
                ('UA_L', float('nan')), ('Hand_L', float('inf')), ('helper', 1.)])

        def __getattr__(self, name):
            return getattr(self.mesh, name)

    def deform(evaluated, mesh):
        original = [v.co.copy() for v in mesh.vertices]
        callback(evaluated, Mesh(mesh))
        world = obj.matrix_world @ original[0]
        expected = .25 * expected_point(world, 'OA_L', points) + .75 * world
        close(mesh.vertices[0].co, obj.matrix_world.inverted() @ expected)
        assert tuple(mesh.vertices[1].co) == tuple(original[1])

    before = source_state(rig, obj)
    with exporter.prepared_export_mesh(obj, rest_deformer=deform):
        pass
    assert source_state(rig, obj) == before


def assert_arm_mesh_deformation(addon):
    # Catches omitted callback forwarding, wrong world/pivot/weight order, helper
    # dilution, changed UV/material/membership data and permanent source edits.
    normalization = importlib.import_module(addon.__name__ + '.o3d_io.human_arm_normalization')
    exporter = importlib.import_module(addon.__name__ + '.o3d_io.io_o3d_export')
    from o3d_export_support import read_export
    with preserve_context(), skin_fixture(addon, custom=True) as (rig, obj, points, weights):
        expected_world = expected_skin(obj, points, weights)
        before = source_state(rig, obj)
        callback = normalization.make_rest_deformer(rig, normalization.build_arm_transforms(rig))
        assert source_state(rig, obj) == before
        for global_matrix in (Matrix.Identity(4), Matrix.Scale(1.8, 4) @ Matrix.Rotation(math.pi, 4, 'Z')):
            before = source_state(rig, obj)
            with exporter.prepared_export_mesh(obj, bpy.context, global_matrix,
                                               rest_deformer=callback) as (evaluated, mesh, matrix):
                assert len(matrix) == 16
                for vertex, point in zip(mesh.vertices, expected_world):
                    close(vertex.co, global_matrix @ Vector((point.x, point.z, point.y)))
                actual = mesh_state(obj, mesh)
                for key in ('memberships', 'groups', 'polygons', 'loops', 'edges', 'uvs', 'active_uv', 'materials'):
                    assert actual[key] == before[1][key], key
            assert source_state(rig, obj) == before
        assert_callback_cleanup(exporter, obj, rig)
        assert_weight_boundaries(normalization, exporter, rig, obj, points)

        # Identity plans must preserve exact local coordinates AND authored data.
        identity = normalization.make_rest_deformer(rig, {})
        before = source_state(rig, obj)
        def unchanged(evaluated, mesh):
            local = mesh_state(obj, mesh)
            identity(evaluated, mesh)
            assert mesh_state(obj, mesh) == local

        with exporter.prepared_export_mesh(obj, rest_deformer=unchanged):
            pass
        assert source_state(rig, obj) == before
        original_world = obj.matrix_world.copy()
        try:
            # A true no-op must not demand an inverse even for a degenerate
            # object frame, which legacy export already supports.
            obj.matrix_world = Matrix.Diagonal((0., 1., 1., 1.))
            bpy.context.view_layer.update()
            with exporter.prepared_export_mesh(obj, rest_deformer=unchanged):
                pass
        finally:
            obj.matrix_world = original_world
            bpy.context.view_layer.update()

        with tempfile.TemporaryDirectory(prefix='o3d-arm-normalization-') as directory:
            default, explicit, normalized = (Path(directory) / (name + '.o3d')
                                             for name in ('default', 'none', 'normalized'))
            for path, kwargs in ((default, {}), (explicit, {'rest_deformer': None}),
                                 (normalized, {'rest_deformer': callback})):
                before = source_state(rig, obj)
                exporter.do_export(str(path), bpy.context, Matrix.Identity(4), False, 7,
                                   objects=[obj], **kwargs)
                assert source_state(rig, obj) == before
            assert default.read_bytes() == explicit.read_bytes(), 'callback-none changed serialized bytes'
            records = read_export(normalized.read_bytes())
            expected = [Vector((p.x, p.z, p.y)) for p in expected_world]
            assert all(any((Vector(v[:3]) - p).length < 2e-5 for v in records['vertices']) for p in expected)
            assert all(any((Vector(v[:3]) - p).length < 2e-5 for p in expected) for v in records['vertices'])
            names = {name for name, _ in records['bones']}
            assert 'Extra' in names and 'helper' not in names
            assert default.read_bytes() != normalized.read_bytes()


def assert_arm_normalization_normals(addon):
    # Catches forward-vector normal transforms, vertex-vs-loop mixups, stale
    # generated normals, identity churn and undefined blended Jacobians.
    normalization = importlib.import_module(addon.__name__ + '.o3d_io.human_arm_normalization')
    exporter = importlib.import_module(addon.__name__ + '.o3d_io.io_o3d_export')
    with preserve_context():
        for custom in (True, False):
            with skin_fixture(addon, custom=custom) as (rig, obj, points, weights):
                before = source_state(rig, obj)
                expected_world = expected_skin(obj, points, weights)
                callback = normalization.make_rest_deformer(rig, normalization.build_arm_transforms(rig))
                # Observe local identity/zero-mass data before export baking.
                def deform(evaluated, mesh):
                    local = mesh_state(obj, mesh)

                    class NormalMesh:
                        def __getattr__(self, name):
                            return getattr(mesh, name)

                        def normals_split_custom_set(self, normals):
                            # Original directions must reach the supported setter
                            # exactly, before Blender quantizes its short2 data.
                            for loop in mesh.loops:
                                if loop.vertex_index >= 24:
                                    assert tuple(normals[loop.index]) == local['normals'][loop.index]
                            mesh.normals_split_custom_set(normals)

                    callback(evaluated, NormalMesh() if custom else mesh)
                    after = mesh_state(obj, mesh)
                    for index in range(24, 33):
                        assert after['coordinates'][index] == local['coordinates'][index]
                    if custom:
                        for loop in mesh.loops:
                            if loop.vertex_index >= 24:
                                # The supported setter re-encodes short2 normals;
                                # unchanged directions incur native quantization.
                                assert (Vector(after['normals'][loop.index])
                                        - Vector(local['normals'][loop.index])).length < 3e-4

                with exporter.prepared_export_mesh(obj, rest_deformer=deform) as (_, mesh, _):
                    corners = mesh['_o3d_export_corners']
                    for loop in obj.data.loops:
                        index = loop.vertex_index
                        if custom:
                            normal = (obj.matrix_world.to_3x3().inverted().transposed()
                                      @ Vector(before[1]['normals'][loop.index]))
                            entries = [(name, weight) for name, weight in weights[index].items()
                                       if name != 'helper' and weight > 0]
                            mass = sum(weight for _, weight in entries)
                            c, s = (0., 0.) if mass else (1., 0.)
                            for name, weight in entries:
                                angle = (35 if name.startswith('OA_') else 10) if name in (
                                    'OA_L', 'UA_L', 'Hand_L', 'OA_R', 'UA_R', 'Hand_R') else 0
                                angle *= -1 if name.endswith('_R') else 1
                                c += weight / mass * math.cos(math.radians(angle))
                                s += weight / mass * math.sin(math.radians(angle))
                            # Analytic inverse transpose of weighted yaw, independent
                            # of production Jacobian inversion and transform outputs.
                            determinant = c * c + s * s
                            n = Vector(((c * normal.x + s * normal.z) / determinant,
                                        normal.y, (-s * normal.x + c * normal.z) / determinant)).normalized()
                            expected = Vector((n.x, n.z, n.y))
                            assert (Vector(corners['normals'][loop.index]) - expected).length < 3e-4
                    # Fresh geometric oracle uses independently expected points.
                    plain = bpy.data.meshes.new('Arm generated normal oracle')
                    try:
                        inverse = obj.matrix_world.inverted()
                        plain.from_pydata([inverse @ p for p in expected_world], [],
                                          [tuple(p.vertices) for p in obj.data.polygons])
                        for target, source in zip(plain.polygons, obj.data.polygons):
                            target.use_smooth = source.use_smooth
                        for target, source in zip(plain.edges, obj.data.edges):
                            target.use_edge_sharp = source.use_edge_sharp
                        plain.update()
                        for index, normal in enumerate(plain.corner_normals):
                            direction = (inverse.to_3x3().transposed() @ normal.vector).normalized()
                            expected = Vector((direction.x, direction.z, direction.y))
                            assert (Vector(corners['generated_normals'][index]) - expected).length < 3e-4
                            if not custom:
                                close(corners['normals'][index], corners['generated_normals'][index])
                    finally:
                        bpy.data.meshes.remove(plain)
                assert source_state(rig, obj) == before
                if custom:
                    for bad in (0., 1e-9, float('nan'), float('inf')):
                        transform = Matrix.Identity(4)
                        transform[0][0] = bad
                        callback = normalization.make_rest_deformer(rig, {'OA_L': transform})
                        before = source_state(rig, obj)
                        try:
                            with exporter.prepared_export_mesh(obj, rest_deformer=callback):
                                raise AssertionError('undefined Jacobian was accepted')
                        except ValueError as error:
                            assert 'Jacobian' in str(error), str(error)
                        assert source_state(rig, obj) == before


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', choices=('plan', 'mesh', 'normals', 'all'), default='all')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    checks = {'plan': assert_arm_transform_plan, 'mesh': assert_arm_mesh_deformation,
              'normals': assert_arm_normalization_normals}
    addon = load_addon()
    try:
        addon.register()
        for name, check in checks.items():
            if args.check in (name, 'all'):
                check(addon)
                print('ARM_NORMALIZATION_CHECK_OK', name, bpy.app.version_string)
    finally:
        addon.unregister()


if __name__ == '__main__':
    run()
