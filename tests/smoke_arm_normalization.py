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


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', choices=('plan',), default='plan')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    checks = {'plan': assert_arm_transform_plan}
    addon = load_addon()
    try:
        addon.register()
        checks[args.check](addon)
        print('ARM_NORMALIZATION_CHECK_OK', args.check, bpy.app.version_string)
    finally:
        addon.unregister()


if __name__ == '__main__':
    run()
