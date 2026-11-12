"""Standalone: blender --background --factory-startup --disable-autoexec
--python-exit-code 1 --python tests/smoke_arm_normalization.py -- --check plan
Public synthetic checks preserve caller state and never load private scenes.
"""
import argparse
from contextlib import contextmanager
import importlib
import hashlib
import math
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile
from types import SimpleNamespace

import bpy
import numpy as np
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
    shoulder = points['OA_' + side]
    sign = -1 if shoulder.x < 0 else 1
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

        def __setitem__(self, key, value):
            self.mesh[key] = value

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
            assert '_o3d_local_authored_normals' not in mesh

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


def export_normal_oracle(normals, world, global_matrix):
    # Match the established float64 export frame, without native normal storage.
    axis = np.array(((1., 0., 0.), (0., 0., 1.), (0., 1., 0.)))
    linear = np.asarray(global_matrix, dtype=np.float64)[:3, :3] @ axis @ np.asarray(world)[:3, :3]
    inverse_transpose = np.linalg.inv(linear).T
    directions = [inverse_transpose @ normal for normal in normals]
    return [tuple(direction / np.linalg.norm(direction)) for direction in directions]


def assert_arm_normalization_normals(addon):
    # Catches forward-vector normal transforms, vertex-vs-loop mixups, stale
    # generated normals, identity churn and undefined blended Jacobians.
    # Authored export/cached directions are exact; Blender's decoded temporary
    # short2 storage is tested separately and is never the export oracle.
    normalization = importlib.import_module(addon.__name__ + '.o3d_io.human_arm_normalization')
    exporter = importlib.import_module(addon.__name__ + '.o3d_io.io_o3d_export')
    from o3d_export_support import read_export
    global_matrix = Matrix.Scale(1.8, 4) @ Matrix.Rotation(.37, 4, 'Z')
    with preserve_context():
        for custom in (True, False):
            with skin_fixture(addon, custom=custom) as (rig, obj, points, weights):
                before = source_state(rig, obj)
                expected_world = expected_skin(obj, points, weights)
                callback = normalization.make_rest_deformer(rig, normalization.build_arm_transforms(rig))
                with exporter.prepared_export_mesh(obj, global_matrix=global_matrix) as (evaluated, mesh, baseline_matrix):
                    baseline_normals = [tuple(n) for n in mesh['_o3d_export_corners']['normals']]
                    baseline_geometry = exporter.prepare_o3d_geometry(evaluated, mesh)
                    with tempfile.TemporaryDirectory(prefix='o3d-arm-baseline-normals-') as directory:
                        destination = Path(directory) / 'baseline.o3d'
                        exporter.export_mesh(str(destination), bpy.context, evaluated, mesh,
                                             baseline_matrix,
                                             evaluated.material_slots, 7, True)
                        baseline_records = read_export(destination.read_bytes())
                computed_local = []
                # Observe local identity/zero-mass data before export baking.
                def deform(evaluated, mesh):
                    local = mesh_state(obj, mesh)

                    class NormalMesh:
                        def __getattr__(self, name):
                            return getattr(mesh, name)

                        def __setitem__(self, key, value):
                            mesh[key] = value

                        def normals_split_custom_set(self, normals):
                            computed_local[:] = [tuple(n) for n in normals]
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

                with exporter.prepared_export_mesh(obj, global_matrix=global_matrix,
                                                   rest_deformer=deform) as (evaluated, mesh, matrix):
                    corners = mesh['_o3d_export_corners']
                    if custom:
                        expected_export = export_normal_oracle(computed_local, obj.matrix_world, global_matrix)
                        for loop in mesh.loops:
                            actual = tuple(corners['normals'][loop.index])
                            if loop.vertex_index >= 24:
                                assert actual == baseline_normals[loop.index], ('identity export drift', loop.index)
                        assert [tuple(n) for n in corners['normals']] == expected_export, 'authored export drift'
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
                            expected = (global_matrix.to_3x3() @ Vector((n.x, n.z, n.y))).normalized()
                            # Independent analytic transport: no allowance for a
                            # second native custom-normal encoding round trip.
                            assert (Vector(corners['normals'][loop.index]) - expected).length < 2e-6
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
                            expected = (global_matrix.to_3x3()
                                        @ Vector((direction.x, direction.z, direction.y))).normalized()
                            assert (Vector(corners['generated_normals'][index]) - expected).length < 3e-4
                            if not custom:
                                close(corners['normals'][index], corners['generated_normals'][index])
                    finally:
                        bpy.data.meshes.remove(plain)
                    if custom:
                        geometry = exporter.prepare_o3d_geometry(evaluated, mesh)
                        with tempfile.TemporaryDirectory(prefix='o3d-arm-exact-normals-') as directory:
                            destination = Path(directory) / 'exact.o3d'
                            exporter.export_mesh(str(destination), bpy.context, evaluated, mesh, matrix,
                                                 evaluated.material_slots, 7, True)
                            records = read_export(destination.read_bytes())
                        # O3D stores float32: require exact float32 rounding of
                        # the authoritative snapshot, with no short2 detour.
                        emitted = [tuple(v[3:6]) for v in records['vertices']]
                        expected_emitted = [None] * len(geometry['verts'])
                        for triangle, indices in zip(corners['triangles'], geometry['tris']):
                            loops = triangle[:3][::-1] if corners['reverse_winding'] else triangle[:3]
                            for loop, index in zip(loops, indices[:3]):
                                expected_emitted[index] = tuple(float(v) for v in
                                                               np.asarray(expected_export[loop], dtype=np.float32))
                        assert emitted == expected_emitted, 'serialized authored normals drifted'
                        for source in range(24, 33):
                            baseline = {tuple(baseline_records['vertices'][i][3:6])
                                        for i in baseline_geometry['source_to_export'][source]}
                            actual = {emitted[i] for i in geometry['source_to_export'][source]}
                            assert actual == baseline, ('identity serialized normal drift', source)
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
        assert_local_authored_snapshot(addon)


def assert_local_authored_snapshot(addon):
    # Catches stale source metadata being trusted, lost loop association, silent
    # truncation and malformed/nonfinite callback payloads reaching serialization.
    exporter = importlib.import_module(addon.__name__ + '.o3d_io.io_o3d_export')
    key = '_o3d_local_authored_normals'
    with preserve_context(), skin_fixture(addon, custom=True) as (rig, obj, _, _):
        vertices = [loop.vertex_index for loop in obj.data.loops]
        normals = [(0.123456789123, .8, .3)] * len(vertices)
        payload = {'vertices': vertices, 'normals': normals}
        with tempfile.TemporaryDirectory(prefix='o3d-arm-snapshot-') as directory:
            baseline = Path(directory) / 'baseline.o3d'
            exporter.do_export(str(baseline), bpy.context, Matrix.Identity(4), False, 7, objects=[obj])
            expected = baseline.read_bytes()
            # Even malformed source-copied metadata must be invisible without a
            # fresh callback payload. Source IDs themselves are never modified.
            for stale in (payload, {'normals': [1., 2., 3.]}):
                obj.data[key] = stale
                stored = obj.data[key].to_dict()
                try:
                    def noop(evaluated, mesh):
                        assert key not in mesh, 'copied snapshot reached callback'

                    for label, kwargs in (('absent', {}), ('none', {'rest_deformer': None}),
                                          ('noop', {'rest_deformer': noop})):
                        path = Path(directory) / (label + '.o3d')
                        before = source_state(rig, obj)
                        exporter.do_export(str(path), bpy.context, Matrix.Identity(4), False, 7,
                                           objects=[obj], **kwargs)
                        assert path.read_bytes() == expected, ('stale snapshot consumed', label)
                        assert obj.data[key].to_dict() == stored
                        assert source_state(rig, obj) == before
                finally:
                    del obj.data[key]

        def snapshot(evaluated, mesh):
            mesh[key] = payload

        before = source_state(rig, obj)
        with exporter.prepared_export_mesh(obj, rest_deformer=snapshot) as (_, mesh, _):
            expected_normals = export_normal_oracle(normals, obj.matrix_world, Matrix.Identity(4))
            assert [tuple(n) for n in mesh['_o3d_export_corners']['normals']] == expected_normals
        assert source_state(rig, obj) == before
        wrong_vertices = vertices.copy()
        wrong_vertices[0] = vertices[1]
        malformed = [[], {}, {'vertices': wrong_vertices, 'normals': normals},
                     {'vertices': vertices[:-1], 'normals': normals},
                     {'vertices': vertices, 'normals': normals[:-1]},
                     {'vertices': vertices, 'normals': [(1., 2.)] * len(vertices)},
                     {'vertices': vertices, 'normals': 'bad'}]
        for bad in (float('nan'), float('inf')):
            malformed.append({'vertices': vertices, 'normals': [(bad, .2, .3)] * len(vertices)})
        for invalid in malformed:
            def snapshot(evaluated, mesh):
                mesh[key] = invalid

            before = source_state(rig, obj)
            try:
                with exporter.prepared_export_mesh(obj, rest_deformer=snapshot):
                    raise AssertionError('malformed authored normal snapshot was accepted')
            except ValueError as error:
                assert 'authored normal snapshot' in str(error), str(error)
            assert source_state(rig, obj) == before


@contextmanager
def bundle_fixture(addon, *, left_sign=-1):
    # Real separate object/mesh ownership: lower LODs also have distinct points.
    human = importlib.import_module(addon.__name__ + '.o3d_io.omsi_human')
    rigmod = importlib.import_module(addon.__name__ + '.o3d_io.mmd_rig')
    with arm_fixture(addon, left_sign=left_sign, upper=35, forearm=10,
                     y_offsets=(.015, -.012)) as (rig, points):
        source_points = {'首': Vector((0, .02, 1.55))}
        for side, sign in (('L', left_sign), ('R', -left_sign)):
            source_points['中指１.' + side] = points['Hand_' + side] + Vector((
                sign * .1 * math.cos(math.radians(10)), .025, -.1 * math.sin(math.radians(10))))
        source = rigmod._create_armature('Bundle source landmarks', {
            name: (point, point + Vector((0, 0, .03))) for name, point in source_points.items()
        }, bpy.context.scene.collection)
        human.capture_landmarks(source, rig)
        meshes, weights = [], []
        material = bpy.data.materials.new('Bundle arm material')
        try:
            for lod in range(3):
                vertices = [(0, 0, 0), (.1, 0, 1.8), (-.1, 0, 1.8)]
                faces = [(0, 1, 2)]
                entries = [{'Main': 1.}] * 3
                for side in ('L', 'R'):
                    for stem in ('OA', 'UA', 'Hand'):
                        name = stem + '_' + side
                        pivot = points[('UA' if stem == 'OA' else 'Hand') + '_' + side]
                        start = len(vertices)
                        for offset in ((0, 0, 0), (.01, .02 + lod * .003, .01), (0, .01, .03)):
                            vertices.append(pivot + Vector(offset))
                            entries.append({name: .7})
                        faces.append((start, start + 1, start + 2))
                start = len(vertices)
                # Blends exercise the same surface path as the standalone skin test.
                for offset, binding in zip(((0, 0, 0), (.02, .01, 0), (0, .02, .01)),
                                          ({'Main': .2, 'OA_L': .6, 'helper': .9},
                                           {'OA_L': .2, 'UA_L': .3}, {'Hand_L': .8})):
                    vertices.append(points['UA_L'] + Vector(offset))
                    entries.append(binding)
                faces.append((start, start + 1, start + 2))
                start = len(vertices)
                # This hand-owned tip changes the measured maximum Z. Lower LODs
                # are deliberately taller and must not contribute to HUM bounds.
                for offset in ((0, 0, 1 + lod), (.02, 0, 1 + lod), (0, .02, 1 + lod)):
                    vertices.append(points['Hand_L'] + Vector(offset))
                    entries.append({'Hand_L': .4})
                faces.append((start, start + 1, start + 2))
                data = bpy.data.meshes.new('Bundle arm LOD ' + str(lod))
                data.from_pydata(vertices, [], faces)
                data.update()
                obj = bpy.data.objects.new('Bundle arm LOD ' + str(lod), data)
                bpy.context.scene.collection.objects.link(obj)
                meshes.append(obj)
                weights.append(entries)
                obj['export_path'] = 'arm_lod_' + str(lod) + '.o3d'
                obj['omsi_lod_level'] = lod
                data.materials.append(material)
                uv = data.uv_layers.new(name='Bundle UV')
                for i, item in enumerate(uv.uv):
                    item.vector = ((i % 5) / 7, (i % 7) / 9)
                for name in ('Main', 'OA_L', 'UA_L', 'Hand_L', 'OA_R', 'UA_R', 'Hand_R', 'helper'):
                    group = obj.vertex_groups.new(name=name)
                    for index, binding in enumerate(entries):
                        if name in binding:
                            group.add([index], binding[name], 'REPLACE')
                modifier = obj.modifiers.new('Bundle source pose', 'ARMATURE')
                modifier.object = rig
                modifier.show_render = False
                obj.shape_key_add(name='Basis')
                key = obj.shape_key_add(name='Inactive authored shape')
                key.data[0].co.y += .04
                key.value = 0
            rig.pose.bones['OA_L'].rotation_mode = 'XYZ'
            rig.pose.bones['OA_L'].rotation_euler.y = .4
            bpy.context.view_layer.update()
            assert len({obj.data.as_pointer() for obj in meshes}) == 3
            yield rig, meshes, points, weights, source_points
        finally:
            for obj in meshes:
                data = obj.data
                bpy.data.objects.remove(obj, do_unlink=True)
                bpy.data.meshes.remove(data)
            data = source.data
            bpy.data.objects.remove(source, do_unlink=True)
            bpy.data.armatures.remove(data)
            bpy.data.materials.remove(material)


def hum_records(path):
    lines = path.read_text(encoding='cp1252').splitlines()
    start = lines.index('[links]') + 1
    return ([float(value) for value in lines[start:start + 22]],
            float(lines[lines.index('[humangeom]') + 2]))


def bundle_bytes(root):
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob('*') if path.is_file()}


def bundle_expected(points, source_points, *, normalized, turn_180, scale, world=None):
    # Independent scalar/fixture oracle; never call the planner or deformer.
    result = []
    for stem in ('OS', 'US', 'Main', 'OA', 'UA', 'neck', 'Hand', 'finger'):
        if stem in ('Main', 'neck'):
            point = points['Main'] if stem == 'Main' else source_points['首']
        else:
            names = (('中指１.L', '中指１.R') if stem == 'finger' else
                     (stem + '_L', stem + '_R'))
            pair = []
            for side, name in zip(('L', 'R'), names):
                point = source_points[name] if stem == 'finger' else points[name]
                if normalized:
                    point = expected_point(point, 'Hand_' + side if stem == 'finger' else name, points)
                pair.append(point)
            point = Vector(((abs(pair[0].x) + abs(pair[1].x)) / 2,
                            (pair[0].y + pair[1].y) / 2, (pair[0].z + pair[1].z) / 2))
        x, y, z = (world @ point if world is not None else point) * scale
        if turn_180:
            x, y = -x, -y
        result.extend((y, z) if stem in ('Main', 'neck') else (abs(x), y, z))
    return result


def assert_bundle_records(addon, result, meshes, points, weights, source_points,
                          *, normalized, turn_180, scale):
    from o3d_export_support import read_export
    cfg = Path(result['cfg_path']).read_text(encoding='cp1252')
    expected_links = bundle_expected(points, source_points, normalized=normalized,
                                     turn_180=turn_180, scale=scale)
    links, height = hum_records(Path(result['hum_path']))
    close(links, expected_links)
    lines = Path(result['hum_path']).read_text(encoding='cp1252').splitlines()
    walk = lines.index('[walk_param]') + 1
    close([float(value) for value in lines[walk:walk + 5]], (1.4, 80, 1, 1, 0))
    # Neck/legs unchanged; elbows, wrists AND captured fingers share shoulder Z.
    if normalized:
        close((links[13], links[18], links[21]), (1.4 * scale,) * 3)
    assert cfg.count('[mesh]') == 3
    assert cfg.count('[smoothskin]') == 3
    expected_height = None
    for obj, bindings, path in zip(meshes, weights, result['mesh_paths']):
        expected_world = (expected_skin(obj, points, bindings) if normalized else
                          [obj.matrix_world @ vertex.co for vertex in obj.data.vertices])
        if expected_height is None:
            expected_height = (max(p.z for p in expected_world) - min(p.z for p in expected_world)) * scale
        expected = [Vector(((-p.x if turn_180 else p.x) * scale, p.z * scale,
                            (-p.y if turn_180 else p.y) * scale)) for p in expected_world]
        records = read_export(Path(path).read_bytes())
        # Both parser paths read actual files, including weights and origin frame.
        parsed = addon.o3d_io.o3dconvert.import_o3d(Path(path).read_bytes())
        actual = [Vector(vertex[0]) for vertex in parsed[1]]
        assert all(any((vertex - point).length < 2e-5 for vertex in actual) for point in expected)
        assert all(any((vertex - point).length < 2e-5 for point in expected) for vertex in actual)
        sign = -1 if turn_180 else 1
        close([value for row in parsed[5] for value in row],
              (sign * scale, 0, 0, 0, 0, scale, 0, 0, 0, 0, sign * scale, 0, 0, 0, 0, 1))
        block = cfg.split('[mesh]\n' + Path(path).name + '\n', 1)[1].split('[mesh]', 1)[0]
        for name, emitted_weights in records['bones']:
            if name == 'Main':
                assert '[setbone]\nMain\n-11\n' in block
                continue
            # Fixed signed-X runtime slots; spelling need not indicate the side.
            x = points[name].x * sign
            side = ('L' if x < 0 else 'R') if normalized or turn_180 else name[-1]
            slots = {'OA_L': -6, 'OA_R': -7, 'UA_L': -8, 'UA_R': -9,
                     'Hand_L': -13, 'Hand_R': -14}
            assert f'[setbone]\n{name}\n{slots[name[:-1] + side]}\n' in block, block
            assert emitted_weights, name
        assert 'helper' not in {name for name, _ in records['bones']}
        # Match independent source corners to actual serialized indices, rather
        # than assuming normalization preserves normal/UV split vertex counts.
        emitted_weights = [{} for _ in records['vertices']]
        for name, entries in records['bones']:
            for index, weight in entries:
                emitted_weights[index][name] = weight
        samples = []
        for loop in obj.data.loops:
            point = expected[loop.vertex_index]
            u, v = obj.data.uv_layers.active.uv[loop.index].vector
            binding = {name: value for name, value in bindings[loop.vertex_index].items() if name != 'helper'}
            samples.append((point, (u, 1 - v), binding))
        def matches(index, sample):
            vertex = records['vertices'][index]
            point, uv, binding = sample
            actual_binding = emitted_weights[index]
            return ((Vector(vertex[:3]) - point).length < 2e-5
                    and all(abs(a - b) < 1e-6 for a, b in zip(vertex[6:], uv))
                    and actual_binding.keys() == binding.keys()
                    and all(abs(actual_binding[name] - value) < 1e-6 for name, value in binding.items()))
        assert all(any(matches(index, sample) for sample in samples) for index in range(len(records['vertices'])))
        assert all(any(matches(index, sample) for index in range(len(records['vertices']))) for sample in samples)
    assert abs(height - expected_height) < 2e-5, (height, expected_height)
    return links, height


# Captured on native Blender 5.0.1 at clean 669e70e, BEFORE adding the keyword.
# Other Blender versions still require exact default-vs-explicit-off bytes below;
# floating-point generated normals can differ between Blender builds.
_OFF_BASELINE_501 = {
    (False, 1): ('91bfa1731a7c91716ae1103b2cd7c9497d7e64d9ed905e4822b740f146797bad',
                 '62d7bafacbb4a2154bde14ad1dbf7df0d4b0199211ac3814065d49730c6fca07',
                 '578887e40111c4d8f60fd76de9658b895a3bbfaa44328d84ac002f2e9333b65b',
                 '80c2659a98a91da7e5c4eb88452b547ef7d7bae4f9a5bd04bc67e4195f6e16fe',
                 '263397cd910c543ef4ebb7e1c82deaf9188dee863b46978a11d80a9674cf0fc0'),
    (False, 2): ('a4a4370c6e6f9d516f4de883da26a7c53b821f8f0efa464517c69d5382b3edfd',
                 '62d7bafacbb4a2154bde14ad1dbf7df0d4b0199211ac3814065d49730c6fca07',
                 '8c76b57b21d3a562896648aa8e06b3b2888c046562b0bde4ea2e99472dcc25bb',
                 '87eff8a933ec281474bd84ad51fe85753c3f18536162f5c1a5ad777972f7b906',
                 '86b04d75b08b9508eb7b1cc4ce0fb62cd37707521353cd25540a0006dc7c9966'),
    (True, 1): ('5b98d3c4b6d08bb2076ba68f254b26934330e1e6212d985c5cdb050e5c84eb35',
                'dc7824612d8e9fd702238c6e22d9d5bcb8579fce43472b508e19105a2aa7b92c',
                '7dd58e47b3a9b9d427c542590e4928d2c112fbbbeb95c42da0958882f0b79498',
                'b2e9c8b1fd12b649e2637e5e7dd6c34ee197702ef67fc3623d46c505b764839c',
                '016fe32702912bf0ab10de3636f6a9c1196b38bc1c3b6b740036de32ef05d3aa'),
    (True, 2): ('6b5f5ca920703327c0632ba3d3eb46f05bdd3e2d1c76e1ff3452dc83bb20bcb2',
                'dc7824612d8e9fd702238c6e22d9d5bcb8579fce43472b508e19105a2aa7b92c',
                '6ca87061b56bf6847c2e7096acd670f2b9ad58ce42a014820a6697e69f0c5a74',
                '1bbb4d4fd0f1e860825be167f7fd18d0740e37beb15c6e6503e35485ad7e8d49',
                '4649f47a3db56a7ff13144f68a5f773cf7e385a01ebeb23d0a4af205d0b689e0'),
}


def assert_arm_normalization_bundle(addon):
    # Catches disconnected keywords, per-LOD plans, stale metadata trusted after
    # virtual edits, double-transformed overrides, wrong bounds/slots and writes
    # before complete normalized codec validation.
    from smoke_human import disk_snapshot, refuses as human_refuses, select_only, source_snapshot
    human = importlib.import_module(addon.__name__ + '.o3d_io.omsi_human')
    with preserve_context():
        for left_sign in (-1, 1):
            with bundle_fixture(addon, left_sign=left_sign) as (rig, meshes, points, weights, source_points):
                def state():
                    # Add rest data/pose_position; source_snapshot freezes ID props
                    # and context without comparing live IDPropertyGroup proxies.
                    return source_snapshot(), rig_state(rig)[:4], repr(tuple(mesh_state(obj) for obj in meshes))

                for turn_180 in (False, True):
                    for scale in (1, 2):
                        with tempfile.TemporaryDirectory(prefix='o3d-arm-bundle-') as directory:
                            root = Path(directory)
                            baseline_root = root / 'baseline'
                            human.export_human(str(baseline_root / 'character.hum'), bpy.context,
                                               rig, meshes, turn_180=turn_180, scale=scale)
                            baseline_bytes = bundle_bytes(baseline_root)
                            if left_sign == -1 and bpy.app.version == (5, 0, 1) and sys.platform == 'linux':
                                names = ['character.hum', 'model/character.cfg',
                                         *('model/arm_lod_' + str(i) + '.o3d' for i in range(3))]
                                actual = tuple(hashlib.sha256(baseline_bytes[name]).hexdigest() for name in names)
                                assert actual == _OFF_BASELINE_501[turn_180, scale], 'legacy baseline bytes changed'
                            for normalized in (True, False):
                                destination = root / ('on' if normalized else 'off') / 'character.hum'
                                before = state()
                                preview = human.export_human(str(destination), bpy.context, rig, meshes,
                                    normalize_arms=normalized, turn_180=turn_180, scale=scale, preflight_only=True)
                                assert not destination.parent.exists(), 'preflight created destination files'
                                assert state() == before
                                result = human.export_human(str(destination), bpy.context, rig, meshes,
                                    normalize_arms=normalized, turn_180=turn_180, scale=scale)
                                assert state() == before
                                links, height = assert_bundle_records(addon, result, meshes, points, weights,
                                    source_points, normalized=normalized, turn_180=turn_180, scale=scale)
                                close(preview['measurements']['links'], links)
                                assert abs(preview['measurements']['height'] - height) < 2e-5
                                assert preview['warnings'] == result['warnings']
                                if not normalized:
                                    assert bundle_bytes(destination.parent) == baseline_bytes, 'off bytes changed'

                # One planner and one callback instance for the complete bundle.
                planner, factory = human.build_arm_transforms, human.make_rest_deformer
                plans, callbacks, uses = [], [], []
                def plan_once(armature):
                    plan = planner(armature)
                    plans.append(plan)
                    return plan

                def deform_once(armature, plan):
                    assert plan is plans[0]
                    callback = factory(armature, plan)
                    callbacks.append(callback)
                    def observed(obj, mesh):
                        uses.append(obj.original)
                        callback(obj, mesh)
                    return observed

                human.build_arm_transforms, human.make_rest_deformer = plan_once, deform_once
                try:
                    with tempfile.TemporaryDirectory(prefix='o3d-arm-shared-') as directory:
                        before = state()
                        human.export_human(str(Path(directory) / 'shared.hum'), bpy.context,
                                           rig, meshes, normalize_arms=True)
                        assert state() == before
                    assert len(plans) == len(callbacks) == 1, (len(plans), len(callbacks))
                    assert uses.count(meshes[0]) == 3 and all(uses.count(obj) == 2 for obj in meshes[1:]), uses
                finally:
                    human.build_arm_transforms, human.make_rest_deformer = planner, factory

                # Public measurement consumes a supplied plan with normalized bounds.
                transforms = planner(rig)
                before = state()
                measured = human.measure_human(rig, meshes, arm_transforms=transforms, scale=2, turn_180=True)
                assert state() == before and not measured['errors'], measured
                close(measured['links'], bundle_expected(points, source_points, normalized=True,
                                                        turn_180=True, scale=2))
                expected_height = max(p.z for p in expected_skin(meshes[0], points, weights[0])) * 2
                assert abs(measured['height'] - expected_height) < 2e-5
                overrides = {'elbow': (.61, -.07, 1.91), 'hand': (.81, -.08, 1.92),
                             'finger': (.94, -.09, 1.93), 'neck': (-.03, 1.61)}
                with tempfile.TemporaryDirectory(prefix='o3d-arm-overrides-') as directory:
                    path = Path(directory) / 'overrides.hum'
                    before = state()
                    preview = human.export_human(str(path), bpy.context, rig, meshes, normalize_arms=True,
                        overrides=overrides, scale=2, turn_180=True, preflight_only=True,
                        settings={'walk_params': (1.3, 45, .9, 1.1, 0)})
                    assert not list(Path(directory).iterdir())
                    result = human.export_human(str(path), bpy.context, rig, meshes, normalize_arms=True,
                        overrides=overrides, scale=2, turn_180=True,
                        settings={'walk_params': (1.3, 45, .9, 1.1, 0)})
                    assert state() == before
                    links, _ = hum_records(path)
                    for start, name in ((11, 'elbow'), (16, 'hand'), (19, 'finger')):
                        close(links[start:start + 3], overrides[name])
                        assert any(name in warning and 'normalized' in warning.lower()
                                   for warning in result['warnings']), result['warnings']
                    close(links[14:16], overrides['neck'])
                    close(links, preview['measurements']['links'])
                    lines = path.read_text(encoding='cp1252').splitlines()
                    start = lines.index('[walk_param]') + 1
                    close([float(value) for value in lines[start:start + 5]], (1.3, 45, .9, 1.1, 0))

                # Pending edits remain pending and every refusal preserves sentinels.
                with tempfile.TemporaryDirectory(prefix='o3d-arm-refusal-') as directory:
                    root = Path(directory)
                    paths = ['character.hum', 'model/character.cfg',
                             *('model/' + obj['export_path'] for obj in meshes)]
                    for name in paths:
                        path = root / name
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_bytes(b'ARM NORMALIZATION SENTINEL ' + name.encode())
                    def refusal(word, **kwargs):
                        for preview in (True, False):
                            before, disk_before = state(), disk_snapshot(root)
                            human_refuses(lambda: human.export_human(str(root / 'character.hum'), bpy.context,
                                rig, meshes, normalize_arms=True, overwrite=True,
                                preflight_only=preview, **kwargs), word)
                            assert state() == before and disk_snapshot(root) == disk_before

                    before, disk_before = state(), disk_snapshot(root)
                    human_refuses(lambda: human.export_human(str(root / 'character.hum'), bpy.context,
                        rig, meshes, normalize_arms=True), 'overwrite')
                    assert state() == before and disk_snapshot(root) == disk_before
                    for editing in (rig, meshes[1]):
                        select_only(editing)
                        bpy.ops.object.mode_set(mode='EDIT')
                        if editing == rig:
                            pending = rig.data.edit_bones['Main']
                            old = pending.head.copy()
                            pending.head.z += .1
                            expected_pending = tuple(pending.head)
                        else:
                            import bmesh
                            edit = bmesh.from_edit_mesh(editing.data)
                            edit.verts.ensure_lookup_table()
                            pending = edit.verts[1]
                            old = pending.co.copy()
                            pending.co.z += .4
                            expected_pending = tuple(pending.co)
                        refusal('Object Mode')
                        assert editing.mode == 'EDIT'
                        assert tuple(pending.head if editing == rig else pending.co) == expected_pending
                        if editing == rig:
                            pending.head = old
                        else:
                            pending.co = old
                        bpy.ops.object.mode_set(mode='OBJECT')
                    # Finger freshness must be checked against ORIGINAL rest data,
                    # even though normalized virtual elbow/hand coordinates differ.
                    select_only(rig)
                    bpy.ops.object.mode_set(mode='EDIT')
                    rig.data.edit_bones['Main'].head.z += .03
                    bpy.ops.object.mode_set(mode='OBJECT')
                    refusal('stale')
                    accepted = human.measure_human(rig, meshes, arm_transforms=planner(rig), confirm_stale=True)
                    assert not accepted['errors'] and any('stale' in w for w in accepted['warnings']), accepted
                    close(accepted['landmarks']['finger'], (.85, .028, 1.4))
                    with tempfile.TemporaryDirectory(prefix='o3d-arm-stale-') as accepted_directory:
                        path = Path(accepted_directory) / 'confirmed.hum'
                        before = state()
                        preview = human.export_human(str(path), bpy.context, rig, meshes, normalize_arms=True,
                            confirm_stale=True, preflight_only=True)
                        assert not list(Path(accepted_directory).iterdir())
                        result = human.export_human(str(path), bpy.context, rig, meshes, normalize_arms=True,
                            confirm_stale=True)
                        assert state() == before
                        close(hum_records(path)[0], preview['measurements']['links'])
                        assert preview['warnings'] == result['warnings']
                    # Both metadata consumers overridden: stale data is unneeded.
                    fixed = human.measure_human(rig, meshes, arm_transforms=planner(rig), overrides=overrides)
                    assert not fixed['errors'] and not any('stale' in w for w in fixed['warnings']), fixed
                    # Bad late-LOD geometry must be rejected by the codec preflight,
                    # before the earlier LOD or HUM destination is truncated.
                    keys = meshes[-1].data.shape_keys.key_blocks
                    old = [key.data[0].co.copy() for key in keys]
                    for key in keys:
                        key.data[0].co.x = float('nan')
                    bpy.context.view_layer.update()
                    refusal('nonfinite', confirm_stale=True)
                    for key, point in zip(keys, old):
                        key.data[0].co = point
                    bpy.context.view_layer.update()
                    # Invalid coronal normalization has identical no-write refusal.
                    select_only(rig)
                    bpy.ops.object.mode_set(mode='EDIT')
                    rig.data.edit_bones['Hand_L'].head.y += .3
                    bpy.ops.object.mode_set(mode='OBJECT')
                    refusal('UA_L', confirm_stale=True)

        # Rig/object world transforms precede scale/yaw. Derive local expectations
        # before changing the frame, without using normalization matrices.
        with bundle_fixture(addon) as (rig, meshes, points, weights, source_points):
            local_expected = [expected_skin(obj, points, bindings) for obj, bindings in zip(meshes, weights)]
            world = Matrix.Translation((0, .07, .2)) @ Matrix.Scale(1.25, 4)
            for obj in (rig, *meshes):
                obj.matrix_world = world
            bpy.context.view_layer.update()
            before = source_snapshot(), rig_state(rig)[:4], repr(tuple(mesh_state(obj) for obj in meshes))
            with tempfile.TemporaryDirectory(prefix='o3d-arm-world-') as directory:
                path = Path(directory) / 'world.hum'
                preview = human.export_human(str(path), bpy.context, rig, meshes, normalize_arms=True,
                    scale=2, turn_180=True, preflight_only=True)
                assert not list(Path(directory).iterdir())
                result = human.export_human(str(path), bpy.context, rig, meshes, normalize_arms=True,
                    scale=2, turn_180=True)
                assert (source_snapshot(), rig_state(rig)[:4], repr(tuple(mesh_state(obj) for obj in meshes))) == before
                links, height = hum_records(path)
                close(links, bundle_expected(points, source_points, normalized=True, turn_180=True, scale=2,
                                            world=world))
                close(links[14:16], (-.19, 4.275))  # Original neck; no arm correction.
                close(links, preview['measurements']['links'])
                expected_height = (max(p.z for p in local_expected[0]) - min(p.z for p in local_expected[0])) * 2.5
                assert abs(height - expected_height) < 2e-5
                assert abs(preview['measurements']['height'] - height) < 2e-5
                for path, local in zip(result['mesh_paths'], local_expected):
                    parsed = addon.o3d_io.o3dconvert.import_o3d(Path(path).read_bytes())
                    expected = [world @ point * 2 for point in local]
                    expected = [Vector((-p.x, p.z, -p.y)) for p in expected]
                    actual = [Vector(vertex[0]) for vertex in parsed[1]]
                    assert all(any((v - p).length < 2e-5 for v in actual) for p in expected)
                    assert all(any((v - p).length < 2e-5 for p in expected) for v in actual)
                    close([value for row in parsed[5] for value in row],
                          (-2.5, 0, 0, 0, 0, 2.5, 0, 0, 0, 0, -2.5, 0, 0, .4, -.14, 1))


def _assert_arm_normalization_persistence(addon):
    # Only invoked in a factory-startup subprocess: never save/load the caller.
    with tempfile.TemporaryDirectory(prefix='o3d-arm-panel-settings-') as directory:
        path = str(Path(directory) / 'settings.blend')
        with preserve_context(), arm_fixture(addon) as (rig, _), arm_fixture(addon) as (other, _):
            first, second = rig.omsi_human_settings, other.omsi_human_settings
            assert not first.normalize_arms and not second.normalize_arms
            first.normalize_arms = True
            first.walk_params = (1.3, 45, .9, 1.1, .2)
            names = rig.name, other.name
            bpy.ops.wm.save_as_mainfile(filepath=path)
        # Reacquire all proxies only after loading the disposable saved fixture.
        bpy.ops.wm.open_mainfile(filepath=path, use_scripts=False)
        first, second = (bpy.data.objects[name].omsi_human_settings for name in names)
        assert first.normalize_arms and not second.normalize_arms
        close(first.walk_params, (1.3, 45, .9, 1.1, .2))
        close(second.walk_params, (1.4, 80, 1, 1, 0))
        first.status, second.status = 'First ready', 'Second ready'
        second.normalize_arms = True
        assert first.normalize_arms and first.status == 'First ready'
        assert second.status == 'Settings changed; refresh/check again'
        first.normalize_arms = False
        assert not first.normalize_arms and second.normalize_arms
        assert first.status == 'Settings changed; refresh/check again'
    print('ARM_NORMALIZATION_PANEL_PERSISTENCE_OK', bpy.app.version_string)


def assert_arm_normalization_panel(addon):
    # Catches a shared/nonpersistent toggle, stale/missing Refresh plans, dropped
    # operator arguments, transformed overrides, gait edits and missing UI guidance.
    from smoke_human import RecordingHumanLayout, cancel_native, select_only
    human = importlib.import_module(addon.__name__ + '.o3d_io.omsi_human')
    panel = importlib.import_module(addon.__name__ + '.o3d_io.omsi_character_panel')
    normalization = importlib.import_module(addon.__name__ + '.o3d_io.human_arm_normalization')
    props = bpy.context.scene.omsi_character_data
    pointers = props.source_mesh, props.source_armature
    caller = (bpy.context.scene, bpy.data.filepath, bpy.context.scene.frame_current,
              bpy.context.view_layer.objects.active, tuple(bpy.context.selected_objects), bpy.context.mode)
    with preserve_context():
        try:
            with bundle_fixture(addon) as (rig, meshes, points, weights, source_points), arm_fixture(addon) as (other, _):
                first, second = rig.omsi_human_settings, other.omsi_human_settings
                assert not first.normalize_arms and not second.normalize_arms
                close(first.walk_params, (1.4, 80, 1, 1, 0))
                close(second.walk_params, (1.4, 80, 1, 1, 0))
                first.walk_params = (1.3, 45, .9, 1.1, .2)
                first.status, second.status = 'First ready', 'Second ready'
                first.normalize_arms = True
                assert first.normalize_arms and not second.normalize_arms
                assert first.status == 'Settings changed; refresh/check again'
                assert second.status == 'Second ready'
                close(first.walk_params, (1.3, 45, .9, 1.1, .2))
                first.normalize_arms = False
                props.source_mesh, props.source_armature = meshes[0], rig
                select_only(rig)
                measure, export, planner = human.measure_human, human.export_human, normalization.build_arm_transforms
                measurements, exports, plans = [], [], []

                def observed_measure(*args, **kwargs):
                    result = measure(*args, **kwargs)
                    measurements.append((args, kwargs, result))
                    return result

                def observed_export(*args, **kwargs):
                    record = {'args': args, 'kwargs': kwargs}
                    exports.append(record)
                    try:
                        record['result'] = export(*args, **kwargs)
                        return record['result']
                    except (ValueError, TypeError, RuntimeError, OSError) as error:
                        record['error'] = str(error)
                        raise

                def observed_plan(target):
                    result = planner(target)
                    plans.append((target, result))
                    return result

                def geometry():
                    state = rig_state(rig)
                    return state[:4], state[5:], repr(tuple(mesh_state(obj) for obj in meshes))

                class Layout(RecordingHumanLayout):
                    def __init__(self):
                        super().__init__()
                        self.properties = []

                    def prop(self, data, name, **kwargs):
                        super().prop(data, name, **kwargs)
                        self.properties.append((name, kwargs))

                human.measure_human, human.export_human = observed_measure, observed_export
                normalization.build_arm_transforms = observed_plan
                try:
                    with tempfile.TemporaryDirectory(prefix='o3d-arm-panel-') as directory:
                        root = Path(directory)
                        for enabled in (False, True):
                            first.normalize_arms = enabled
                            before, disk_before = geometry(), bundle_bytes(root)
                            count = len(plans)
                            assert bpy.ops.omsi.refresh_human_measurements() == {'FINISHED'}
                            args, kwargs, refreshed = measurements[-1]
                            assert args[0] is rig and args[1] == meshes
                            assert len(plans) == count + int(enabled)
                            assert kwargs['arm_transforms'] is (plans[-1][1] if enabled else None)
                            assert not first.errors and first.status == 'Measurements refreshed'
                            expected = bundle_expected(points, source_points, normalized=enabled,
                                                       turn_180=False, scale=1)
                            close(refreshed['links'], expected)
                            expected_mesh = (expected_skin(meshes[0], points, weights[0]) if enabled else
                                             [vertex.co for vertex in meshes[0].data.vertices])
                            height = max(p.z for p in expected_mesh) - min(p.z for p in expected_mesh)
                            assert abs(first.measured_height - height) < 2e-5
                            assert first.has_measurement
                            if enabled:
                                prior = plans[-1][1]
                                assert bpy.ops.omsi.refresh_human_measurements() == {'FINISHED'}
                                assert len(plans) == count + 2 and plans[-1][1] is not prior
                                assert all(target is rig for target, _ in plans)
                                assert measurements[-1][1]['arm_transforms'] is plans[-1][1]
                            count = len(plans)
                            assert bpy.ops.omsi.human_preflight() == {'FINISHED'}
                            preview = exports[-1]
                            assert preview['kwargs']['normalize_arms'] is enabled
                            assert preview['kwargs']['preflight_only'] is True
                            assert preview['args'][2] is rig and preview['args'][3] == meshes
                            assert not Path(preview['args'][0]).parent.exists()
                            assert bundle_bytes(root) == disk_before
                            close(preview['result']['measurements']['links'], expected)
                            assert abs(first.measured_height - height) < 2e-5
                            assert not first.errors and first.status.startswith('Readiness passed;')
                            path = root / ('on' if enabled else 'off') / 'character.hum'
                            assert bpy.ops.omsi.export_human(filepath=str(path)) == {'FINISHED'}
                            emitted = exports[-1]
                            assert emitted['kwargs']['normalize_arms'] is enabled
                            assert emitted['args'][2] is rig and emitted['args'][3] == meshes
                            assert not emitted['kwargs'].get('preflight_only', False)
                            assert first.status == 'Exported: ' + str(path) and not first.errors
                            links, actual_height = hum_records(path)
                            close(links, expected)
                            assert abs(actual_height - height) < 2e-5
                            for mesh_path in emitted['result']['mesh_paths']:
                                assert Path(mesh_path).is_file()
                            assert Path(emitted['result']['cfg_path']).is_file()
                            lines = path.read_text(encoding='cp1252').splitlines()
                            start = lines.index('[walk_param]') + 1
                            close([float(v) for v in lines[start:start + 5]], (1.3, 45, .9, 1.1, .2))
                            assert len(plans) == count, 'Refresh planner leaked into backend toggle calls'
                            assert geometry() == before

                        # Final-coordinate overrides survive scale/yaw/normalization.
                        first.scale, first.turn_180 = 2, True
                        first.use_hand_override = first.use_finger_override = True
                        first.hand_override, first.finger_override = (.81, -.08, 1.92), (.94, -.09, 1.93)
                        expected = bundle_expected(points, source_points, normalized=True, turn_180=True, scale=2)
                        expected[16:19], expected[19:22] = tuple(first.hand_override), tuple(first.finger_override)
                        before = geometry()
                        assert bpy.ops.omsi.refresh_human_measurements() == {'FINISHED'}
                        close(measurements[-1][2]['links'], expected)
                        assert 'hand' in first.warnings and 'finger' in first.warnings
                        assert bpy.ops.omsi.human_preflight() == {'FINISHED'}
                        close(exports[-1]['result']['measurements']['links'], expected)
                        path = root / 'overrides.hum'
                        assert bpy.ops.omsi.export_human(filepath=str(path)) == {'FINISHED'}
                        close(hum_records(path)[0], expected)
                        close(first.hand_override, (.81, -.08, 1.92))
                        close(first.finger_override, (.94, -.09, 1.93))
                        assert 'normalized' in first.warnings
                        assert geometry() == before

                        # Actual invalid override results populate Refresh feedback;
                        # real readiness/export refusal leaves destinations unchanged.
                        first.hand_override = (-.81, -.08, 1.92)
                        before, disk_before = geometry(), bundle_bytes(root)
                        assert bpy.ops.omsi.refresh_human_measurements() == {'FINISHED'}
                        assert first.status == 'Measurements need attention'
                        assert 'hand' in first.errors and measurements[-1][2]['errors']
                        cancel_native(lambda: bpy.ops.omsi.human_preflight())
                        assert first.status == 'Human export needs attention' and 'hand' in first.errors
                        assert 'hand' in exports[-1]['error']
                        cancel_native(lambda: bpy.ops.omsi.export_human(filepath=str(root / 'invalid.hum'), overwrite=True))
                        assert 'hand' in exports[-1]['error'] and 'hand' in first.errors
                        assert geometry() == before and bundle_bytes(root) == disk_before
                        first.use_hand_override = first.use_finger_override = False

                        # Exact RNA and drawn guidance are part of the opt-in UI contract.
                        prop = first.bl_rna.properties['normalize_arms']
                        assert prop.name == 'Normalize Arm Rest Pose'
                        assert prop.description == ('Export a temporary horizontal arm rest pose; '
                                                    'keep the editable rig and meshes unchanged')
                        first.show_walking = True
                        help_text = ('Walking arm lowering applies after normalization; '
                                     'remove earlier A-pose compensation.')
                        for enabled in (True, False):
                            first.normalize_arms = enabled
                            before = geometry()
                            counts = len(measurements), len(exports), len(plans)
                            layout = Layout()
                            panel.VIEW3D_PT_omsi_character_human.draw(SimpleNamespace(layout=layout), bpy.context)
                            names = [name for name, _ in layout.properties]
                            assert names[names.index('scale'):names.index('selection_only') + 1] == [
                                'scale', 'turn_180', 'normalize_arms', 'selection_only']
                            walking = [kwargs for name, kwargs in layout.properties if name == 'walk_params']
                            assert [(kw['index'], kw['text']) for kw in walking] == [
                                (0, 'Walk Parameter 1'), (1, 'Arm Lowering (degrees)'),
                                (2, 'Walk Parameter 3'), (3, 'Walk Parameter 4'), (4, 'Walk Parameter 5')]
                            labels = [text for kind, text, _ in layout.records if kind == 'label']
                            assert (help_text in labels) is enabled
                            close(first.walk_params, (1.3, 45, .9, 1.1, .2))
                            assert counts == (len(measurements), len(exports), len(plans))
                            assert geometry() == before
                        # A real planner refusal must reach all three operator error paths.
                        first.normalize_arms = first.confirm_stale = True
                        select_only(rig)
                        bpy.ops.object.mode_set(mode='EDIT')
                        rig.data.edit_bones['Hand_L'].head.y += .3
                        bpy.ops.object.mode_set(mode='OBJECT')
                        before, disk_before = geometry(), bundle_bytes(root)
                        count = len(measurements)
                        cancel_native(lambda: bpy.ops.omsi.refresh_human_measurements())
                        assert len(measurements) == count, 'invalid plan reached measurement'
                        assert first.status == 'Human export needs attention' and 'UA_L' in first.errors
                        cancel_native(lambda: bpy.ops.omsi.human_preflight())
                        assert 'UA_L' in exports[-1]['error'] and 'UA_L' in first.errors
                        cancel_native(lambda: bpy.ops.omsi.export_human(filepath=str(root / 'invalid.hum'), overwrite=True))
                        assert 'UA_L' in exports[-1]['error'] and 'UA_L' in first.errors
                        assert geometry() == before and bundle_bytes(root) == disk_before
                        first.normalize_arms = False
                        assert bpy.ops.omsi.refresh_human_measurements() == {'FINISHED'}
                        assert not first.errors and measurements[-1][1]['arm_transforms'] is None
                        assert geometry() == before
                        assert not second.normalize_arms and second.status == 'Second ready'
                finally:
                    human.measure_human, human.export_human = measure, export
                    normalization.build_arm_transforms = planner
        finally:
            props.source_mesh, props.source_armature = pointers
    # Native save/reload must not invalidate objects held by a root integration caller.
    expression = (f'import sys; sys.path.insert(0, {str(HERE)!r}); '
                  'import smoke_arm_normalization as t; a=t.load_addon(); a.register(); '
                  't._assert_arm_normalization_persistence(a); a.unregister()')
    result = subprocess.run([bpy.app.binary_path, '--background', '--factory-startup', '--disable-autoexec',
                             '--python-exit-code', '1', '--python-expr', expression],
                            capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'ARM_NORMALIZATION_PANEL_PERSISTENCE_OK' in result.stdout, result.stdout
    assert caller == (bpy.context.scene, bpy.data.filepath, bpy.context.scene.frame_current,
                      bpy.context.view_layer.objects.active, tuple(bpy.context.selected_objects), bpy.context.mode)
    assert (props.source_mesh, props.source_armature) == pointers
    print('ARM_NORMALIZATION_PANEL_PERSISTENCE_OK', 'isolated subprocess')


def runtime_arm_matrices(joints, state, phase=0, *, beta=80):
    """Independent original-animation arm graph, never the enhanced IK model.

    Equation provenance: retained native func-00626b98.c:531-625,1501-1802
    and openOMSI human_omsi.rs at a19eac8:34-140,414-503,528-609.
    D3DX uses row vectors p M in (X right,Y up,Z forward). Here mathutils
    column vectors use M.T in those SAME file/D3D coordinates. If displayed
    in Blender, C swaps Y/Z, so the display matrix is C M.T C.
    Degrees use openOMSI's .017453292 radians factor, not native .01745;
    this is structural equation coverage, not bitwise native equivalence.
    Torso B9=identity, zero stoop/reach/hold/running and no smoothing.
    Walking deliberately fixes A=18 degrees to isolate the arm graph and
    retains unequal 1.5/1.2 elbow coefficients. beta80 gives standing80 and
    walking77; beta45 gives standing45/walking42. Seated lowering stays fixed67.
    Anatomical names are kept;
    procedural side/sign follows exported shoulder X, not the name suffix.
    """
    if state == 'standing':
        lower, axial, swings, elbows, hand = beta, -30, (-3, -3), (29, 29), (0, 0, 0)
    elif state == 'walking':
        q, amplitude = math.sin(2 * math.pi * phase), 18
        lower, axial = beta - 3, -30
        swings = ((q - .2) * amplitude, (-q - .2) * amplitude)
        elbows = (1.5 * (q + 1) * amplitude, 1.2 * (1 - q) * amplitude)
        hand = (0, 0, 0)
    elif state == 'seated':
        lower, axial, swings, elbows, hand = 67, -58, (35, 35), (46, 46), (41, -26, 5)
    else:
        raise ValueError('unknown runtime state: ' + state)
    def rotation(degrees, axis):
        return Matrix.Rotation(degrees * .017453292, 4, axis)
    def about(point, matrix):
        return Matrix.Translation(point) @ matrix @ Matrix.Translation(-point)
    result = {'Main': Matrix.Identity(4)}
    for anatomy in ('L', 'R'):
        oa, ua, hn = (stem + '_' + anatomy for stem in ('OA', 'UA', 'Hand'))
        shoulder, elbow, wrist = (joints[name] for name in (oa, ua, hn))
        # Native B4/6/11 are negative-X; B5/7/12 are positive-X.
        index, mirror = (0, 1) if shoulder.x < 0 else (1, -1)
        upper = about(shoulder, rotation(-3 * mirror, 'Y') @ rotation(lower * mirror, 'Z')
                      @ rotation(swings[index] * mirror, 'Y')
                      @ rotation(axial * mirror, elbow - shoulder))
        forearm = upper @ about(elbow, rotation(elbows[index] * mirror, 'Y'))
        hx, hz, hy = hand
        palm = forearm @ about(wrist, rotation(-hx, 'X')
                              @ rotation(hz * mirror, 'Z') @ rotation(hy * mirror, 'Y'))
        result.update({oa: upper, ua: forearm, hn: palm})
    return result


def runtime_cases():
    return [('standing', 0), *(('walking', phase) for phase in (0, .25, .5, .75)), ('seated', 0)]


def weighted_point(point, weights, matrices):
    # Native func-005fdf40.c:152-230: independent normalized weighted positions.
    mass = sum(weights.values())
    return sum((weight / mass * (matrices.get(name, Matrix.Identity(4)) @ point)
                for name, weight in weights.items()), Vector())


def literal_upward(points):
    """Scalar two-segment elevation oracle; preserve authored depth, never roll.

    Rotation in Blender XZ: (x,z)->(c*x+s*z,-s*x+c*z). Each segment's
    raw elevation fixes its rotation; forearm pivot translates to raised elbow.
    This is also used for independent one-way private mixed-weight expectations.
    """
    result = {'Main': Matrix.Identity(4)}
    for side in ('L', 'R'):
        oa, ua, hand = (stem + '_' + side for stem in ('OA', 'UA', 'Hand'))
        s, e, h = (points[name] for name in (oa, ua, hand))
        sign = 1 if s.x > 0 else -1
        a = math.degrees(math.atan2(sign * (e.z - s.z), sign * (e.x - s.x)))
        b = math.degrees(math.atan2(sign * (h.z - e.z), sign * (h.x - e.x)))
        raised = s + yaw(e - s, a)
        result[oa] = Matrix.Translation(s) @ Matrix.Rotation(math.radians(a), 4, 'Y') @ Matrix.Translation(-s)
        result[ua] = Matrix.Translation(raised) @ Matrix.Rotation(math.radians(b), 4, 'Y') @ Matrix.Translation(-e)
        result[hand] = result[ua].copy()
    return result


@contextmanager
def runtime_fixture(addon, *, left_sign, horizontal=False):
    """Literal horizontal triangles, independently lowered rigid and mixed input.

    Catches wrong normalization axes/pivots, dropped mixed skinning, incorrect
    anatomical/name swaps, mirrored hands and exporter corner/winding changes.
    B^-1 constructs each mixed A-pose sample: opposite LBS blends do NOT invert.
    """
    angle = 0 if horizontal else 35
    with arm_fixture(addon, left_sign=left_sign, upper=angle,
                     forearm=0 if horizontal else 10) as (rig, points):
        up = literal_upward(points)
        reference, bindings, faces, hand_samples, seams = [], [], [], {}, []
        def patch(vertices, weights, triangles):
            start = len(reference)
            reference.extend(Vector(point) for point in vertices)
            bindings.extend(dict(weights) for _ in vertices)
            faces.extend(tuple(start + index for index in face) for face in triangles)
            return list(range(start, len(reference)))
        for side, sign in (('L', left_sign), ('R', -left_sign)):
            s, e, h = (Vector((sign * x, 0, 1.4)) for x in (.2, .5, .75))
            body = patch((s, s + Vector((0, .025, 0)), s + Vector((0, 0, .025))),
                         {'Main': 1}, ((0, 1, 2),))
            upper = patch((s, e, e + Vector((0, .025, 0)), s + Vector((0, .025, 0))),
                          {'OA_' + side: 1}, ((0, 1, 2), (0, 2, 3)))
            forearm = patch((e, h, h + Vector((0, .025, 0)), e + Vector((0, .025, 0))),
                            {'UA_' + side: 1}, ((0, 1, 2), (0, 2, 3)))
            palm = patch((h, (sign * .86, 0, 1.4), (sign * .78, -.045, 1.4),
                          (sign * .78, 0, 1.435)), {'Hand_' + side: 1},
                         ((0, 1, 2), (0, 3, 1), (1, 3, 2), (2, 3, 0)))
            hand_samples[side] = palm  # wrist, finger, thumb side, palm normal tip
            seams.extend(((body[0], upper[0]), (upper[1], forearm[0]), (forearm[1], palm[0])))
            # Known reference points; expected upward B is composed independently.
            start = len(reference)
            for point, weights in ((s + Vector((sign * .02, -.02, .015)), {'Main': .25, 'OA_' + side: .75}),
                                   (e + Vector((0, -.02, .01)), {'OA_' + side: .4, 'UA_' + side: .6}),
                                   (h + Vector((0, -.02, .025)), {'UA_' + side: .3, 'Hand_' + side: .7})):
                reference.append(point)
                bindings.append(weights)
            faces.append((start, start + 1, start + 2))
        original = []
        for point, weights in zip(reference, bindings):
            blend = sum((weight * up.get(name, Matrix.Identity(4)) for name, weight in weights.items()),
                        Matrix(((0.,) * 4,) * 4))
            original.append(blend.inverted() @ point)
        data = bpy.data.meshes.new('Independent runtime samples')
        data.from_pydata(original, [], faces)
        data.update()
        obj = bpy.data.objects.new('Independent runtime samples', data)
        bpy.context.scene.collection.objects.link(obj)
        material = bpy.data.materials.new('Runtime sample material')
        data.materials.append(material)
        try:
            uv = data.uv_layers.new(name='Sample identity')
            for loop in data.loops:
                uv.uv[loop.index].vector = ((loop.vertex_index + 1) / (len(reference) + 1), .25)
            for name in {name for weights in bindings for name in weights}:
                group = obj.vertex_groups.new(name=name)
                for index, weights in enumerate(bindings):
                    if name in weights:
                        group.add([index], weights[name], 'REPLACE')
            mod = obj.modifiers.new('Runtime rest', 'ARMATURE')
            mod.object = rig
            yield rig, obj, points, reference, bindings, faces, hand_samples, seams
        finally:
            bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.meshes.remove(data)
            bpy.data.materials.remove(material)


def runtime_records(addon, rig, obj, path, *, normalized):
    from o3d_export_support import read_export
    normalizer = importlib.import_module(addon.__name__ + '.o3d_io.human_arm_normalization')
    callback = (normalizer.make_rest_deformer(rig, normalizer.build_arm_transforms(rig))
                if normalized else None)
    addon.o3d_io.io_o3d_export.do_export(str(path), bpy.context, Matrix.Identity(4), False, 7,
                                       objects=[obj], rest_deformer=callback)
    return read_export(path.read_bytes())


def runtime_decoded(records, count):
    # UV identity disambiguates coincident shoulder/elbow corners and split normals.
    result, ids = {}, []
    for vertex in records['vertices']:
        index = round(vertex[6] * (count + 1)) - 1
        assert 0 <= index < count
        point = Vector(vertex[:3])
        if index in result:
            close(point, result[index])
        result[index] = point
        ids.append(index)
    assert set(result) == set(range(count))
    weights = [{} for _ in ids]
    for name, entries in records['bones']:
        for index, weight in entries:
            weights[index][name] = weight
    return result, ids, weights


def assert_arm_normalization_runtime(addon):
    # Literal D3DX ROW-vector B4/6/11 and B5/7/12 multiplication anchors.
    # These were calculated separately in double precision, not with this helper.
    # Noncommuting seated hand angles lock down transposition/composition order;
    # comparing two geometries under the same wrong runtime graph would miss it.
    anchor_joints = {stem + '_' + side: Vector((sign * x, 1.4, 0))
                     for side, sign in (('L', -1), ('R', 1))
                     for stem, x in (('OA', .2), ('UA', .5), ('Hand', .75))}
    seated = runtime_arm_matrices(anchor_joints, 'seated')
    for side, sign in (('L', -1), ('R', 1)):
        for source, expected in zip(((.75, 1.4, 0), (.86, 1.4, 0), (.78, 1.4, -.045), (.78, 1.435, 0)),
                ((.208180582326, 1.033566594533, .349797649477),
                 (.205147070088, .993881994960, .452344859875),
                 (.226662778550, .984647457619, .363593535325),
                 (.238952511049, 1.036440525532, .384000411402))):
            x, y, z = source
            ex, ey, ez = expected
            close(seated['Hand_' + side] @ Vector((sign * x, y, z)), (sign * ex, ey, ez))
    # The oracle must reject missing rest conversion even with beta45 compensation.
    render_data = None
    with preserve_context(), tempfile.TemporaryDirectory(prefix='o3d-arm-runtime-') as directory:
        for left_sign in (-1, 1):
            with runtime_fixture(addon, left_sign=left_sign) as fixture:
                rig, obj, points, reference, bindings, faces, hands, seams = fixture
                before = rig_state(rig), repr([(tuple(v.co), tuple((g.group, g.weight) for g in v.groups))
                                               for v in obj.data.vertices])
                root = Path(directory)
                after = runtime_records(addon, rig, obj, root / 'after.o3d', normalized=True)
                off = runtime_records(addon, rig, obj, root / 'before.o3d', normalized=False)
                actual, ids, emitted = runtime_decoded(after, len(reference))
                off_points, _, _ = runtime_decoded(off, len(reference))
                convert = lambda p: Vector((p.x, p.z, p.y))
                expected = [convert(point) for point in reference]
                normalized_joints = {name: convert(literal_upward(points).get(name, Matrix.Identity(4)) @ point)
                                     for name, point in points.items()}
                raw_joints = {name: convert(point) for name, point in points.items()}
                # Source triangle winding must be reversed once for the XZY reflection.
                expected_faces = {min(face[i:] + face[:i] for i in range(3))
                                  for a, b, c in faces for face in ((a, c, b),)}
                actual_faces = {min(face[i:] + face[:i] for i in range(3))
                                for a, b, c, _ in after['triangles']
                                for face in ((ids[a], ids[b], ids[c]),)}
                assert actual_faces == expected_faces, 'serialized triangle winding/coverage changed'
                assert len(after['triangles']) == len(faces)
                for index, weights in enumerate(emitted):
                    expected_weights = bindings[ids[index]]
                    assert weights.keys() == expected_weights.keys()
                    close(tuple(weights[name] for name in sorted(weights)),
                          tuple(expected_weights[name] for name in sorted(weights)))
                failures = []
                for state, phase in runtime_cases():
                    matrices = runtime_arm_matrices(normalized_joints, state, phase)
                    if state == 'seated':
                        seated_beta45 = runtime_arm_matrices(normalized_joints, state, phase, beta=45)
                        for name in matrices:
                            matrix_close(matrices[name], seated_beta45[name])
                    reference_pose = [weighted_point(p, w, matrices) for p, w in zip(expected, bindings)]
                    actual_pose = [weighted_point(actual[i], bindings[i], matrices) for i in range(len(expected))]
                    orientation_dots = []
                    for side, (wrist, finger, thumb, palm) in hands.items():
                        for tip in (finger, thumb, palm):
                            a = actual_pose[tip] - actual_pose[wrist]
                            e = reference_pose[tip] - reference_pose[wrist]
                            dot = a.normalized().dot(e.normalized())
                            assert dot > 1 - 1e-5, (state, phase, side, tip, dot)
                            orientation_dots.append(dot)
                    for a, e in zip(actual_pose, reference_pose):
                        assert (a - e).length < 2e-5, (state, phase, a, e)
                    for a, b, c, _ in after['triangles']:
                        ai, bi, ci = ids[a], ids[b], ids[c]
                        an = (actual_pose[bi] - actual_pose[ai]).cross(actual_pose[ci] - actual_pose[ai])
                        en = (reference_pose[bi] - reference_pose[ai]).cross(reference_pose[ci] - reference_pose[ai])
                        assert an.dot(en) > 0, (state, phase, ai, bi, ci)
                    for a, b in seams:
                        close(actual_pose[a], actual_pose[b])
                    # Real model-specific A-pose elbow/wrist pivots and axis in the
                    # disabled graph; beta reduction cannot fix twist/hand direction.
                    disabled = runtime_arm_matrices(raw_joints, state, phase, beta=45)
                    off_pose = [weighted_point(off_points[i], bindings[i], disabled) for i in range(len(expected))]
                    side_failures = []
                    for side, (wrist, finger, thumb, palm) in hands.items():
                        dots = [(off_pose[tip] - off_pose[wrist]).normalized().dot(
                                (reference_pose[tip] - reference_pose[wrist]).normalized())
                                for tip in (finger, thumb, palm)]
                        assert min(dots) < 1 - 1e-5, ('beta45 accidentally matches full orientation', state, phase, side, dots)
                        side_failures.append(min(dots))
                    failures.append({'state': state, 'phase': phase, 'off_beta45_min_dots': side_failures,
                                     'normalized_min_orientation_dot': min(orientation_dots),
                                     'normalized_max_position_error_m': max((a - e).length for a, e in zip(actual_pose, reference_pose)),
                                     'normalized_max_seam_error_m': max((actual_pose[a] - actual_pose[b]).length for a, b in seams)})
                assert (rig_state(rig), repr([(tuple(v.co), tuple((g.group, g.weight) for g in v.groups))
                                             for v in obj.data.vertices])) == before
                if left_sign == 1:
                    render_data = {'after': after, 'before': off, 'reference_points': expected,
                                   'bindings': bindings, 'joints': normalized_joints, 'raw_joints': raw_joints,
                                   'negative_orientation': failures}
        if RENDER_OUTPUT_DIR is not None:
            # Reference is independently authored horizontal geometry, also serialized.
            with runtime_fixture(addon, left_sign=1, horizontal=True) as fixture:
                rig, obj = fixture[:2]
                render_data['reference'] = runtime_records(addon, rig, obj, Path(directory) / 'reference.o3d', normalized=False)
            render_runtime_comparison(render_data, RENDER_OUTPUT_DIR, 'synthetic')
    print('ARM_RUNTIME_ORIENTATION_OK', '2 anatomical conventions; standing/walking[0,.25,.5,.75]/seated; beta45 rejected')


RENDER_OUTPUT_DIR = None


def render_runtime_comparison(data, output_dir, label):
    """Optional Blender CPU renders of decoded exported triangles and skinning.

    Synthetic has independently authored AND exported horizontal reference.
    Private compares the original A-pose export to normalized actual character;
    it has no independently authored private T-pose and no target-game claim.
    Neutral diagnostic materials expose shape/orientation; source textures are
    neither edited nor represented as a game-material rendering validation.
    """
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    variants = [name for name in ('before', 'after', 'reference') if name in data]
    collections = (bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.cameras,
                   bpy.data.lights, bpy.data.curves, bpy.data.worlds, bpy.data.scenes)
    original_ids = [set(items) for items in collections]
    caller = bpy.context.window.scene
    evidence = {'coverage': label, 'coordinate_display': 'C swaps D3D Y-up to Blender Z-up',
                'radians_per_degree': .017453292, 'torso': 'identity', 'walking_A_degrees': 18,
                'variants': variants, 'target_game': 'unverified', 'states': [],
                'reference': 'independently authored horizontal geometry' if label == 'synthetic' else
                             'no independent private reference; actual before/after geometry',
                'negative_orientation': data.get('negative_orientation', [])}
    try:
        scene = bpy.data.scenes.new('Arm normalization diagnostic render')
        bpy.context.window.scene = scene
        scene.render.engine = 'CYCLES'
        scene.cycles.device = 'CPU'
        scene.cycles.samples = 16
        scene.render.threads_mode, scene.render.threads = 'FIXED', 4
        scene.render.resolution_x, scene.render.resolution_y = 400 * len(variants), 600
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = 'PNG'
        world = bpy.data.worlds.new('Diagnostic studio')
        world.use_nodes = True
        world.node_tree.nodes['Background'].inputs['Color'].default_value = (.18, .18, .18, 1)
        world.node_tree.nodes['Background'].inputs['Strength'].default_value = .8
        scene.world = world
        camera_data = bpy.data.cameras.new('Diagnostic camera')
        camera = bpy.data.objects.new('Diagnostic camera', camera_data)
        scene.collection.objects.link(camera)
        # The installed-inferred private Turn180 faces +Y; inspect its front so
        # the original long hair does not hide the arm comparison.
        view_sign = -1 if label == 'private' else 1
        camera.location = (0, -8 * view_sign, 3.4)
        camera.rotation_euler = (Vector((0, 0, .85)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
        camera_data.type = 'ORTHO'
        camera_data.ortho_scale = 1.95 * len(variants)
        scene.camera = camera
        light_data = bpy.data.lights.new('Diagnostic key', 'AREA')
        light_data.energy, light_data.shape, light_data.size = 650, 'DISK', 5
        light = bpy.data.objects.new('Diagnostic key', light_data)
        scene.collection.objects.link(light)
        light.location = (-2, -4 * view_sign, 5)
        light.rotation_euler = (-light.location).to_track_quat('-Z', 'Y').to_euler()
        palette = ((.22, .48, .85, 1), (.85, .31, .18, 1), (.32, .35, .40, 1), (.8, .67, .53, 1))
        materials = []
        for index, color in enumerate(palette):
            material = bpy.data.materials.new('Diagnostic ' + str(index))
            material.diffuse_color = color
            material.use_nodes = True
            material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = color
            material.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .7
            materials.append(material)
        mesh_objects = []
        for slot, variant in enumerate(variants):
            records = data[variant]
            mesh = bpy.data.meshes.new(label + ' ' + variant)
            mesh.from_pydata([(0, 0, 0)] * len(records['vertices']), [],
                             [(a, c, b) for a, b, c, _ in records['triangles']])
            mesh.update()
            obj = bpy.data.objects.new(label + ' ' + variant, mesh)
            scene.collection.objects.link(obj)
            obj.location.x = (slot - (len(variants) - 1) / 2) * 1.85 * view_sign
            for material in materials:
                mesh.materials.append(material)
            weights = [{} for _ in records['vertices']]
            for name, entries in records['bones']:
                for index, weight in entries:
                    weights[index][name] = weight
            for polygon in mesh.polygons:
                bone = max(weights[polygon.vertices[0]], key=weights[polygon.vertices[0]].get)
                polygon.material_index = 0 if bone.endswith('_L') else 1 if bone.endswith('_R') else 2
            mesh_objects.append((obj, records, weights))
            font = bpy.data.curves.new('Diagnostic label', 'FONT')
            font.body = variant + (' / beta45' if variant == 'before' else ' / beta80')
            font.align_x, font.size = 'CENTER', .10
            caption = bpy.data.objects.new('Diagnostic label', font)
            scene.collection.objects.link(caption)
            caption.location = (obj.location.x, -.05, -.1)
            caption.rotation_euler = (math.pi / 2, 0, math.pi if view_sign < 0 else 0)
        for state, phase in (('standing', 0), ('walking', .25), ('seated', 0)):
            matrices_by_variant = {}
            for (obj, records, weights), variant in zip(mesh_objects, variants):
                raw = variant == 'before'
                matrices = runtime_arm_matrices(data['raw_joints'] if raw else data['joints'], state, phase,
                                                beta=45 if raw else 80)
                matrices_by_variant[variant] = {name: [list(row) for row in matrix] for name, matrix in matrices.items()}
                for vertex, source, binding in zip(obj.data.vertices, records['vertices'], weights):
                    point = weighted_point(Vector(source[:3]), binding, matrices)
                    vertex.co = (point.x, point.z, point.y)
                obj.data.update()
            scene.render.filepath = str((output / (label + '-' + state + '.png')).resolve())
            bpy.ops.render.render(write_still=True, scene=scene.name)
            evidence['states'].append({'state': state, 'phase': phase, 'image': Path(scene.render.filepath).name,
                                       'matrices': matrices_by_variant})
        (output / (label + '-render-evidence.json')).write_text(json.dumps(evidence, indent=2))
        (output / (label + '-exported-records.json')).write_text(json.dumps({k: data[k] for k in variants}))
    finally:
        bpy.context.window.scene = caller
        for collection, previous in zip(collections, original_ids):
            for item in set(collection) - previous:
                collection.remove(item, do_unlink=True)
    print('ARM_BLENDER_RENDER_OK', label, str(output), 'standing/walking phase .25/seated; neutral materials')


def private_geometry_expected(obj, transforms):
    expected, bindings = [], []
    names = {group.index: group.name for group in obj.vertex_groups}
    for vertex in obj.data.vertices:
        weights = {names[g.group]: g.weight for g in vertex.groups if g.weight > 0}
        bindings.append(weights)
        expected.append(weighted_point(obj.matrix_world @ vertex.co, weights, transforms))
    return expected, bindings


def assert_private_records(records, obj, expected, bindings):
    """Match actual corners by UV/position/weights, not exporter vertex ordering."""
    candidates = {}
    for loop in obj.data.loops:
        uv = obj.data.uv_layers.active.uv[loop.index].vector
        key = tuple(round(v, 5) for v in (uv.x, 1 - uv.y))
        candidates.setdefault(key, []).append(loop.vertex_index)
    weights = [{} for _ in records['vertices']]
    for name, entries in records['bones']:
        for index, weight in entries:
            weights[index][name] = weight
    covered, actual_to_source = set(), []
    for vertex, binding in zip(records['vertices'], weights):
        assert all(math.isfinite(v) for v in vertex)
        assert abs(Vector(vertex[3:6]).length - 1) < 1e-4
        # Float32's serialized (1-v) can cross a rounding boundary even when
        # the central bucket contains OTHER source corners. Always search all
        # neighboring UV buckets; exact position/weight tolerances still decide.
        u, v = vertex[6:]
        possible = {index for du in (-1e-5, 0, 1e-5) for dv in (-1e-5, 0, 1e-5)
                    for index in candidates.get((round(u + du, 5), round(v + dv, 5)), [])}
        matches = [index for index in possible
                   if (Vector(vertex[:3]) - expected[index]).length < 2e-5
                   and binding.keys() == bindings[index].keys()
                   and all(abs(binding[name] - bindings[index][name]) < 1e-6 for name in binding)]
        assert matches, (obj.name, vertex, binding, sorted(possible)[:8])
        covered.update(matches)
        actual_to_source.append(matches)
    # O3D serializes triangle corners. Reduced LODs retain loose source vertices
    # (LOD1 has 38); they must stay unchanged but are not exported surface points.
    used = {loop.vertex_index for loop in obj.data.loops}
    assert covered == used, (obj.name, len(covered), len(used), sorted(used - covered))
    # Check serialized oriented surfaces against the source topology with XZY's
    # single reflection, including the real mixed-weight seam triangles.
    wanted = {min(face[i:] + face[:i] for i in range(3)) for polygon in obj.data.polygons
              for a, b, c in (tuple(polygon.vertices),) for face in ((a, c, b),)}
    # Retain all matching source identities at coincident/nearby UV corners.
    # Arbitrarily selecting matches[0] loses topology on reduced seam duplicates.
    from itertools import product
    got = set()
    for a, b, c, _ in records['triangles']:
        alternatives = {min(face[i:] + face[:i] for i in range(3))
                        for face in product(actual_to_source[a], actual_to_source[b], actual_to_source[c])}
        matching_faces = wanted & alternatives
        assert matching_faces, (obj.name, a, b, c, alternatives)
        got.update(matching_faces)
    assert len(records['triangles']) == len(obj.data.polygons)
    assert got == wanted, (obj.name, len(got), len(wanted))
    return weights


def assert_arm_normalization_private(addon, path, *, evidence_files=(), render_output_dir=None):
    """Opt-in supplied fixture, no autoexec/save or installed-output writes.

    Turn180=True is installed-output inference (all 22 links), NOT a saved bool.
    Only canonical rig + its three owned LODs are selected. Optional hash manifests
    contain {absolute_path: {size, sha256}} and are read only in this private call.
    No external checkout or private evidence is needed by any public check.
    """
    from smoke_human import source_snapshot, select_only
    from o3d_export_support import read_export
    human = importlib.import_module(addon.__name__ + '.o3d_io.omsi_human')
    expected_hashes = {}
    for evidence in evidence_files:
        expected_hashes.update(json.loads(Path(evidence).read_text()))
    protected = {Path(name) for name in expected_hashes} | {path.resolve()}
    def hashes():
        return {str(p): {'size': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                for p in sorted(protected)}
    before_hashes = hashes()
    for name, value in expected_hashes.items():
        assert before_hashes[name] == value, ('protected input differs from evidence', name)
    assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
    try:
        bpy.ops.wm.open_mainfile(filepath=str(path.resolve()), use_scripts=False)
        assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
        rig = bpy.data.objects['knd_mesh Materials Materials OMSI Rig']
        meshes = [bpy.data.objects[name] for name in ('knd_mesh Materials Materials Converted',
                  'knd_mesh Materials Materials Converted_LOD1', 'knd_mesh Materials Materials Converted_LOD2')]
        assert len(rig.data.bones) == 13
        for lod, obj in enumerate(meshes):
            assert obj.parent == rig and obj.get('omsi_lod_level', 0) == lod
            assert len(obj.modifiers) == 1 and obj.modifiers[0].object == rig
            assert obj.get('omsi_lod_source_id') == meshes[0].get('omsi_lod_source_id')
        assert dict(meshes[0]['omsi_lod_outputs']) == {'1': meshes[1], '2': meshes[2]}
        assert all(obj.get('omsi_lod_owner') == meshes[0] for obj in meshes[1:])
        select_only(rig, *meshes)
        settings = rig.omsi_human_settings
        # Explicit installed-inferred orientation, never recovered saved UI state.
        settings.turn_180, settings.normalize_arms = True, True
        settings.walk_params = (1.4, 80, 1, 1, 0)
        assert settings.turn_180 and settings.normalize_arms
        close(settings.walk_params, (1.4, 80, 1, 1, 0))
        points = {bone.name: rig.matrix_world @ bone.head_local for bone in rig.data.bones}
        independent = literal_upward(points)
        normalized_points = {name: independent.get(name, Matrix.Identity(4)) @ point for name, point in points.items()}
        metadata = rig['omsi_human_landmarks']
        assert metadata['version'] == 1 and not metadata.get('missing')
        captured = {name: Vector(point) for name, point in metadata['points'].items()}
        def expected_links(normalized, turn=True, scale=1):
            result = []
            for stem in ('OS', 'US', 'Main', 'OA', 'UA', 'neck', 'Hand', 'finger'):
                if stem in ('Main', 'neck'):
                    point = points['Main'] if stem == 'Main' else rig.matrix_world @ captured['neck']
                else:
                    pair = []
                    for side in ('L', 'R'):
                        name = ('Hand' if stem == 'finger' else stem) + '_' + side
                        p = rig.matrix_world @ captured['finger_' + side] if stem == 'finger' else points[name]
                        pair.append(independent.get(name, Matrix.Identity(4)) @ p if normalized else p)
                    point = Vector((sum(abs(p.x) for p in pair) / 2, sum(p.y for p in pair) / 2,
                                    sum(p.z for p in pair) / 2))
                x, y, z = point * scale
                result.extend(((-y if turn else y), z) if stem in ('Main', 'neck') else
                              (abs(x), -y if turn else y, z))
            return result
        # Recheck all-22-link Turn180 evidence when an installed HUM was supplied.
        installed = [Path(name) for name in expected_hashes if Path(name).suffix.lower() == '.hum']
        for hum in installed:
            links, _ = hum_records(hum)
            close(links, expected_links(False))
            assert max(abs(a - b) for a, b in zip(links, expected_links(False, False))) > .1
        target_images = {node.image for obj in meshes for material in obj.data.materials
                         for node in material.node_tree.nodes if node.type == 'TEX_IMAGE' and node.image}
        assert len(target_images) == 3
        def snapshot():
            # Include authored corner normals/UVs and the three target source-image
            # bytes/paths, in addition to source IDs/rest/pose/metadata/weights/context.
            images = [(image.name, image.filepath, image.colorspace_settings.name,
                       hashlib.sha256(Path(bpy.path.abspath(image.filepath, library=image.library)).read_bytes()).hexdigest())
                      for image in sorted(target_images, key=lambda item: item.name)]
            extra = [(obj.name, tuple(tuple(n.vector) for n in obj.data.corner_normals),
                      tuple((uv.name, tuple(tuple(v.vector) for v in uv.uv)) for uv in obj.data.uv_layers),
                      tuple((p.name, tuple(p.head_local), tuple(p.tail_local)) for p in rig.data.bones))
                     for obj in meshes]
            return source_snapshot(), repr(extra), rig_state(rig)[:4], images
        before = snapshot()
        with tempfile.TemporaryDirectory(prefix='o3d-private-arms-') as directory:
            root = Path(directory)
            kwargs = {'settings': {'walk_params': tuple(settings.walk_params)}, 'turn_180': settings.turn_180,
                      'normalize_arms': settings.normalize_arms}
            preview = human.export_human(str(root / 'after' / 'character.hum'), bpy.context, rig, meshes,
                                         preflight_only=True, **kwargs)
            assert not list(root.iterdir())
            result = human.export_human(str(root / 'after' / 'character.hum'), bpy.context, rig, meshes, **kwargs)
            close(hum_records(Path(result['hum_path']))[0], expected_links(True))
            close(preview['measurements']['links'], expected_links(True))
            assert not preview['measurements']['errors']
            cfg = Path(result['cfg_path']).read_text(encoding='cp1252')
            assert cfg.count('[mesh]') == cfg.count('[smoothskin]') == 3
            slots = {'Main': -11, 'Hip': -10, 'Head': -12, 'OA_L': -6, 'OA_R': -7,
                     'UA_L': -8, 'UA_R': -9, 'Hand_L': -13, 'Hand_R': -14,
                     'OS_L': -2, 'OS_R': -3, 'US_L': -4, 'US_R': -5}
            after_records = []
            for obj, emitted_path in zip(meshes, result['mesh_paths']):
                expected, weights = private_geometry_expected(obj, independent)
                expected = [Vector((-p.x, p.z, -p.y)) for p in expected]
                records = read_export(Path(emitted_path).read_bytes())
                assert {name for name, _ in records['bones']} == set(points)
                assert_private_records(records, obj, expected, weights)
                block = cfg.split('[mesh]\n' + Path(emitted_path).name + '\n', 1)[1].split('[mesh]', 1)[0]
                for name, slot in slots.items():
                    assert f'[setbone]\n{name}\n{slot}\n' in block, (name, block)
                after_records.append(records)
            # Every limb joint and captured finger must agree with the same
            # independent elevation plan, no redundant numeric baseline overrides.
            links = hum_records(Path(result['hum_path']))[0]
            close((links[13], links[18]), (points['OA_L'].z,) * 2)
            height = max(v[1] for v in after_records[0]['vertices']) - min(v[1] for v in after_records[0]['vertices'])
            assert abs(hum_records(Path(result['hum_path']))[1] - height) < 2e-5
            assert snapshot() == before
            # Distinct sentinel overrides stay final coordinates at nonunit scale,
            # independent of either yaw state. Export, do not just measure previews.
            overrides = {'elbow': (.71, -.12, 1.81), 'hand': (.82, -.13, 1.82),
                         'finger': (.93, -.14, 1.83), 'neck': (.15, 1.95), 'waist': (0, -.16, 1.21)}
            for turn in (False, True):
                emitted = human.export_human(str(root / ('override-' + str(turn)) / 'character.hum'),
                    bpy.context, rig, meshes, normalize_arms=True, turn_180=turn, scale=1.7, overrides=overrides)
                links, _ = hum_records(Path(emitted['hum_path']))
                for name, start in (('elbow', 11), ('hand', 16), ('finger', 19)):
                    close(links[start:start + 3], overrides[name])
                    assert any(name in w and 'normalized' in w for w in emitted['warnings'])
                close(links[6:8], overrides['waist'][1:])
                close(links[14:16], overrides['neck'])
                assert snapshot() == before
            if render_output_dir is not None:
                legacy = human.export_human(str(root / 'before' / 'character.hum'), bpy.context, rig, meshes,
                    settings={'walk_params': (1.4, 45, 1, 1, 0)}, turn_180=True, normalize_arms=False)
                before_records = read_export(Path(legacy['mesh_paths'][0]).read_bytes())
                render_runtime_comparison({'before': before_records, 'after': after_records[0],
                    'joints': {name: Vector((-p.x, p.z, -p.y)) for name, p in normalized_points.items()},
                    'raw_joints': {name: Vector((-p.x, p.z, -p.y)) for name, p in points.items()}},
                    render_output_dir, 'private')
                assert snapshot() == before
            assert settings.turn_180 and settings.normalize_arms
            close(settings.walk_params, (1.4, 80, 1, 1, 0))
            after = snapshot()
            assert after == before
            if render_output_dir is not None:
                (Path(render_output_dir) / 'private-source-image-hashes.json').write_text(json.dumps(
                    {'before': before[-1], 'after': after[-1]}, indent=2))
            print('ARM_PRIVATE_SOURCE_IMAGES_OK', len(after[-1]), json.dumps(after[-1]))
    finally:
        after_hashes = hashes()
        assert after_hashes == before_hashes, 'protected private/source/installed bytes changed'
        if render_output_dir is not None:
            output = Path(render_output_dir)
            output.mkdir(parents=True, exist_ok=True)
            (output / 'private-protected-hashes.json').write_text(json.dumps(
                {'before': before_hashes, 'after': after_hashes, 'count': len(protected)}, indent=2))
        print('ARM_PRIVATE_HASHES_OK', len(protected), json.dumps(after_hashes, sort_keys=True))
    print('ARM_PRIVATE_FIXTURE_OK', 'canonical rig + owned 3 LODs; installed-inferred Turn180=True; beta80')


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', choices=(*PUBLIC_CHECKS, 'private', 'all'), default='all')
    parser.add_argument('--with-private-fixtures', action='store_true')
    parser.add_argument('--private-blend', type=Path)
    parser.add_argument('--private-evidence-file', type=Path, action='append', default=[])
    parser.add_argument('--render-output-dir', type=Path)
    args = parser.parse_args(argv)
    if args.with_private_fixtures != (args.private_blend is not None):
        parser.error('--with-private-fixtures and --private-blend must be supplied together')
    if (args.check == 'private' or args.private_evidence_file) and not args.with_private_fixtures:
        parser.error('private checks/evidence require both private opt-in flags')
    for path in ([args.private_blend] if args.with_private_fixtures else []) + args.private_evidence_file:
        if not path.is_file() or not os.access(path, os.R_OK):
            parser.error('private input must be an existing readable file: ' + str(path))
    return args


def assert_arm_normalization_cli(addon):
    # Exercise behavior: default no private dependency, strict paired opt-in,
    # invalid input/unknown checks fail, and a named check does not run all.
    from contextlib import redirect_stderr
    import io
    default = parse_args([])
    assert not default.with_private_fixtures and default.private_blend is None
    assert not default.private_evidence_file and default.render_output_dir is None
    assert parse_args(['--check', 'runtime']).check == 'runtime'
    with tempfile.TemporaryDirectory(prefix='o3d-arm-cli-') as directory:
        readable = Path(directory) / 'input.blend'
        readable.write_bytes(b'parser-only fixture; never opened as a scene')
        supplied = parse_args(['--with-private-fixtures', '--private-blend', str(readable), '--check', 'private'])
        assert supplied.private_blend == readable and supplied.check == 'private'
        for arguments in (['--check', 'typo'], ['--check', 'private'], ['--with-private-fixtures'],
                          ['--private-blend', str(readable)], ['--private-evidence-file', str(readable)],
                          ['--with-private-fixtures', '--private-blend', str(readable.parent)],
                          ['--with-private-fixtures', '--private-blend', str(readable) + '.missing']):
            with redirect_stderr(io.StringIO()) as output:
                try:
                    parse_args(arguments)
                except SystemExit as error:
                    assert error.code == 2 and 'error:' in output.getvalue(), arguments
                else:
                    raise AssertionError('invalid CLI accepted: ' + repr(arguments))


PUBLIC_CHECKS = {'plan': assert_arm_transform_plan, 'mesh': assert_arm_mesh_deformation,
                 'normals': assert_arm_normalization_normals, 'bundle': assert_arm_normalization_bundle,
                 'panel': assert_arm_normalization_panel, 'runtime': assert_arm_normalization_runtime,
                 'cli': assert_arm_normalization_cli}
# Root caller owns add-on registration. Public CHECKS never open private files.
CHECKS = list(PUBLIC_CHECKS.values())


def run():
    global RENDER_OUTPUT_DIR
    args = parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    RENDER_OUTPUT_DIR = args.render_output_dir
    addon = load_addon()
    try:
        addon.register()
        for name, check in PUBLIC_CHECKS.items():
            if args.check in (name, 'all'):
                check(addon)
                print('ARM_NORMALIZATION_CHECK_OK', name, bpy.app.version_string)
        if args.with_private_fixtures:
            assert_arm_normalization_private(addon, args.private_blend, evidence_files=args.private_evidence_file,
                                             render_output_dir=args.render_output_dir)
    finally:
        addon.unregister()


if __name__ == '__main__':
    run()
