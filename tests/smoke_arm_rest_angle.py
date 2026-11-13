"""Public synthetic target-angle checks; never open a private scene.

blender --background --factory-startup --disable-autoexec --python-exit-code 1
--python tests/smoke_arm_rest_angle.py -- --check all
CHECKS accepts an already-registered add-on, like smoke_arm_normalization.
"""
import argparse
import importlib
import math
from pathlib import Path
import sys
import tempfile

import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from smoke_arm_normalization import (arm_fixture, bundle_bytes, bundle_fixture, close,
                                     hum_records, mesh_state, preserve_context, refuses, rig_state)
from smoke_human import disk_snapshot, source_snapshot
from smoke_support import load_addon
from o3d_export_support import read_export


INVALID_ANGLES = (-89.01, -90, 89.01, float('nan'), float('inf'), -float('inf'),
                  '15', b'15', None, True, False, complex(15, 0), complex(0, 0), [], {})


def segment_target(delta, sign, target):
    # Endpoint oracle uses only original segment depth/length and scalar trig.
    d = math.radians(target)
    radius = math.hypot(delta.x, delta.z)
    return Vector((sign * radius * math.cos(d), delta.y, -radius * math.sin(d)))


def scalar_point(point, name, points, target):
    if name not in {'OA_L', 'UA_L', 'Hand_L', 'OA_R', 'UA_R', 'Hand_R'}:
        return point.copy()
    side = name[-1]
    shoulder, elbow, wrist = (points[stem + '_' + side] for stem in ('OA', 'UA', 'Hand'))
    sign = 1 if shoulder.x > 0 else -1
    upper = name.startswith('OA_')
    pivot = shoulder if upper else elbow
    delta = elbow - shoulder if upper else wrist - elbow
    destination = shoulder if upper else shoulder + segment_target(elbow - shoulder, sign, target)
    angle = math.atan2(sign * delta.z, sign * delta.x) + sign * math.radians(target)
    c, s = math.cos(angle), math.sin(angle)
    x, y, z = point - pivot
    return destination + Vector((c * x + s * z, y, -s * x + c * z))


def source_state(rig, meshes=()):
    return source_snapshot(), rig_state(rig)[:4], repr(tuple(mesh_state(obj) for obj in meshes))


def refuses_angle(call):
    try:
        call()
    except ValueError as error:
        assert 'angle' in str(error).lower(), str(error)
    else:
        raise AssertionError('invalid rest angle was accepted')


def assert_arm_rest_angle_plan(addon):
    # Breaks on wrong signs, target ignored on either segment, coupled source
    # elevations, lost input depth, altered fingers/non-arms or source mutation.
    normalization = importlib.import_module(addon.__name__ + '.o3d_io.human_arm_normalization')
    identity = Matrix.Identity(4)
    with preserve_context():
        for left_sign in (-1, 1):
            # Original upper10/forearm50 at +/-80 catches validation against
            # an upper-rotated forearm instead of the valid original segment.
            for upper, forearm, depth in ((35, 10, (.015, -.012)),
                                          (20, -10, (-.01, .02)), (10, 50, (.015, -.012)),
                                          (-20, 40, (0, 0)), (0, 0, (0, 0))):
                with arm_fixture(addon, left_sign=left_sign, upper=upper,
                                 forearm=forearm, y_offsets=depth) as (rig, points):
                    before = source_state(rig)
                    default = normalization.build_arm_transforms(rig)
                    for target in (-15, -89, -80, 0, 15, 35, 80, 89):
                        transforms = normalization.build_arm_transforms(rig, rest_angle_degrees=target)
                        if target == 0:
                            assert transforms == default
                        assert set(transforms) == set(points)
                        for side, sign in (('L', left_sign), ('R', -left_sign)):
                            oa, ua, hand = (stem + '_' + side for stem in ('OA', 'UA', 'Hand'))
                            shoulder, elbow, wrist = (points[name] for name in (oa, ua, hand))
                            e_expected = shoulder + segment_target(elbow - shoulder, sign, target)
                            w_expected = e_expected + segment_target(wrist - elbow, sign, target)
                            assert (transforms[oa] @ elbow - e_expected).length < 2e-6
                            assert (transforms[ua] @ elbow - e_expected).length < 2e-6
                            assert (transforms[ua] @ wrist - w_expected).length < 2e-6
                            assert (transforms[oa] @ shoulder - shoulder).length < 2e-6
                            assert transforms[hand] == transforms[ua]
                            for bone, a, b in ((oa, shoulder, elbow), (ua, elbow, wrist)):
                                assert abs((transforms[bone] @ b - transforms[bone] @ a).length
                                           - (b - a).length) < 2e-6
                            delta = wrist - elbow
                            finger = wrist + delta * .4 + Vector((0, .025, 0))
                            close(normalization.transform_landmark(transforms, hand, finger),
                                  w_expected + segment_target(delta, sign, target) * .4 + Vector((0, .025, 0)))
                        for name in set(points) - {'OA_L', 'UA_L', 'Hand_L', 'OA_R', 'UA_R', 'Hand_R'}:
                            assert transforms[name] == identity
                            assert normalization.transform_landmark(transforms, name, points[name]) == points[name]
                        neck = Vector((0, .02, 1.55))
                        assert normalization.transform_landmark(transforms, 'extra_neck', neck) == neck
                    assert source_state(rig) == before

        # World coordinates, including a translated/scaled pivot, precede target rotation.
        world = Matrix.Translation((.025, .07, .5)) @ Matrix.Scale(1.5, 4)
        with arm_fixture(addon, upper=20, forearm=10, y_offsets=(.01, -.01), world=world) as (rig, points):
            points = {name: world @ point for name, point in points.items()}
            for target in (-15, 15):
                transforms = normalization.build_arm_transforms(rig, rest_angle_degrees=target)
                for name in ('OA_L', 'UA_L', 'Hand_R'):
                    point = points['Hand_' + name[-1]]
                    assert (transforms[name] @ point - scalar_point(point, name, points, target)).length < 2e-6

        # A nonzero target still refuses malformed original source segments.
        for side, sign in (('L', -1), ('R', 1)):
            shoulder = Vector((sign * .2, 0, 1.4))
            elbow = Vector((sign * .5, 0, 1.4))
            for name, origin, bone in ((f'UA_{side}', shoulder, f'OA_{side}'),
                                       (f'Hand_{side}', elbow, f'UA_{side}')):
                for delta in ((0, 0, 0), (-sign * .2, 0, 0), (0, 0, -.2), (sign * .2, .1, 0)):
                    with arm_fixture(addon, upper=0, forearm=0,
                                     patch={name: origin + Vector(delta)}) as (rig, _):
                        before = source_state(rig)
                        refuses(lambda: normalization.build_arm_transforms(rig, rest_angle_degrees=35), bone)
                        assert source_state(rig) == before


def assert_arm_rest_angle_identity(addon):
    # Catches narrowing/removing the existing 1e-6 rad identity tolerance, or
    # treating materially different target/source angles as identity.
    normalization = importlib.import_module(addon.__name__ + '.o3d_io.human_arm_normalization')
    identity = Matrix.Identity(4)
    with preserve_context():
        for left_sign in (-1, 1):
            for target in (-15, -89, 0, 15, 35, 89):
                for difference in (0, -.5e-6, .5e-6, -3e-6, 3e-6):
                    source = target + math.degrees(difference)
                    with arm_fixture(addon, left_sign=left_sign, upper=source, forearm=source,
                                     y_offsets=(.001, -.001)) as (rig, _):
                        before = source_state(rig)
                        transforms = normalization.build_arm_transforms(rig, rest_angle_degrees=target)
                        for side in ('L', 'R'):
                            for stem in ('OA', 'UA', 'Hand'):
                                assert (transforms[stem + '_' + side] == identity) == (abs(difference) <= 1e-6), (
                                    target, difference, stem, transforms[stem + '_' + side])
                        assert source_state(rig) == before
        with arm_fixture(addon) as (rig, _):
            before = source_state(rig)
            for angle in INVALID_ANGLES:
                refuses_angle(lambda: normalization.build_arm_transforms(rig, rest_angle_degrees=angle))
                assert source_state(rig) == before


def expected_skin(obj, points, bindings, target):
    result = []
    for vertex, entries in zip(obj.data.vertices, bindings):
        point = obj.matrix_world @ vertex.co
        admitted = [(name, weight) for name, weight in entries.items()
                    if name != 'helper' and math.isfinite(weight) and weight > 0]
        mass = sum(weight for _, weight in admitted)
        result.append(sum((weight / mass * scalar_point(point, name, points, target)
                           for name, weight in admitted), Vector()) if mass else point)
    return result


def expected_links(points, source_points, target, scale, turn_180):
    values = []
    for stem in ('OS', 'US', 'Main', 'OA', 'UA', 'neck', 'Hand', 'finger'):
        if stem in ('Main', 'neck'):
            point = points['Main'] if stem == 'Main' else source_points['首']
        else:
            pair = []
            for side in ('L', 'R'):
                name = stem + '_' + side
                point = source_points['中指１.' + side] if stem == 'finger' else points[name]
                pair.append(scalar_point(point, 'Hand_' + side if stem == 'finger' else name, points, target))
            point = Vector(((abs(pair[0].x) + abs(pair[1].x)) / 2,
                            (pair[0].y + pair[1].y) / 2, (pair[0].z + pair[1].z) / 2))
        x, y, z = point * scale
        values.extend(((-y if turn_180 else y), z) if stem in ('Main', 'neck')
                      else (abs(x), -y if turn_180 else y, z))
    return values


def assert_angle_bundle(result, meshes, points, weights, source_points, *, target,
                        scale, turn_180, overrides=None, walk=(1.4, 80, 1, 1, 0)):
    cfg = Path(result['cfg_path']).read_text(encoding='cp1252')
    assert cfg.count('[mesh]') == cfg.count('[smoothskin]') == 3
    expected = expected_links(points, source_points, target, scale, turn_180)
    for offset, name in ((11, 'elbow'), (16, 'hand'), (19, 'finger')):
        if overrides and name in overrides:
            expected[offset:offset + 3] = overrides[name]
    if overrides and 'neck' in overrides:
        expected[14:16] = overrides['neck']
    links, height = hum_records(Path(result['hum_path']))
    close(links, expected)
    lines = Path(result['hum_path']).read_text(encoding='cp1252').splitlines()
    offset = lines.index('[walk_param]') + 1
    close([float(value) for value in lines[offset:offset + 5]], walk)
    for lod, (obj, bindings, path) in enumerate(zip(meshes, weights, result['mesh_paths'])):
        world = expected_skin(obj, points, bindings, target)
        if lod == 0:
            assert abs(height - (max(p.z for p in world) - min(p.z for p in world)) * scale) < 2e-5
        expected_points = [Vector(((-p.x if turn_180 else p.x) * scale, p.z * scale,
                                   (-p.y if turn_180 else p.y) * scale)) for p in world]
        records = read_export(Path(path).read_bytes())
        actual_weights = [{} for _ in records['vertices']]
        names = {name for name, _ in records['bones']}
        assert 'helper' not in names and 'Extra' in names
        for name, entries in records['bones']:
            for index, weight in entries:
                actual_weights[index][name] = weight
            if name == 'Extra':
                assert '[setbone]\nExtra\n' not in cfg
            else:
                side = 'L' if points[name].x * (-1 if turn_180 else 1) < 0 else 'R'
                slot = -11 if name == 'Main' else {'OA_L': -6, 'OA_R': -7, 'UA_L': -8,
                                                  'UA_R': -9, 'Hand_L': -13, 'Hand_R': -14}[name[:-1] + side]
                assert f'[setbone]\n{name}\n{slot}\n' in cfg
        samples = []
        for loop in obj.data.loops:
            u, v = obj.data.uv_layers.active.uv[loop.index].vector
            binding = {name: weight for name, weight in bindings[loop.vertex_index].items() if name != 'helper'}
            samples.append((expected_points[loop.vertex_index], (u, 1 - v), binding))

        def matches(index, sample):
            vertex = records['vertices'][index]
            point, uv, binding = sample
            return ((Vector(vertex[:3]) - point).length < 2e-5
                    and all(abs(a - b) < 1e-6 for a, b in zip(vertex[6:], uv))
                    and actual_weights[index].keys() == binding.keys()
                    and all(abs(actual_weights[index][name] - weight) < 1e-6 for name, weight in binding.items()))

        assert all(any(matches(index, sample) for sample in samples) for index in range(len(records['vertices'])))
        assert all(any(matches(index, sample) for index in range(len(records['vertices']))) for sample in samples)
    return links, height


def assert_arm_rest_angle_bundle(addon):
    # Real 3-LOD decoded corners and weights catch disconnected angle forwarding,
    # wrong admission, wrong measured bounds/pivots and double-scaled overrides.
    human = importlib.import_module(addon.__name__ + '.o3d_io.omsi_human')
    with preserve_context(), tempfile.TemporaryDirectory(prefix='o3d-rest-angle-') as directory:
        root = Path(directory)
        for left_sign in (-1, 1):
            for binding in ('active', 'disabled', 'parent'):
                with bundle_fixture(addon, left_sign=left_sign, binding_form=binding,
                                    extra=True, custom=True) as (rig, meshes, points, weights, source_points):
                    before = source_state(rig, meshes)
                    for target in (-15, -89, 15, 35):
                        for turn_180, scale in ((False, 1), (True, 2)):
                            path = root / f'{left_sign}-{binding}-{target}-{turn_180}' / 'character.hum'
                            options = dict(normalize_arms=True, arm_rest_angle=target,
                                           turn_180=turn_180, scale=scale)
                            preview = human.export_human(str(path), bpy.context, rig, meshes,
                                                         preflight_only=True, **options)
                            assert not path.parent.exists()
                            assert source_state(rig, meshes) == before
                            result = human.export_human(str(path), bpy.context, rig, meshes, **options)
                            links, height = assert_angle_bundle(result, meshes, points, weights, source_points,
                                                                target=target, scale=scale, turn_180=turn_180)
                            close(preview['measurements']['links'], links)
                            assert abs(preview['measurements']['height'] - height) < 2e-5
                            assert preview['warnings'] == result['warnings']
                            assert source_state(rig, meshes) == before

                    overrides = {'elbow': (.61, -.07, 1.91), 'hand': (.81, -.08, 1.92),
                                 'finger': (.94, -.09, 1.93), 'neck': (-.03, 1.61)}
                    walk = (1.3, 45, .9, 1.1, 0)
                    path = root / f'{left_sign}-{binding}-override' / 'character.hum'
                    options = dict(normalize_arms=True, arm_rest_angle=35, overrides=overrides,
                                   scale=2, turn_180=True, settings={'walk_params': walk})
                    preview = human.export_human(str(path), bpy.context, rig, meshes, preflight_only=True, **options)
                    assert not path.parent.exists()
                    result = human.export_human(str(path), bpy.context, rig, meshes, **options)
                    links, height = assert_angle_bundle(result, meshes, points, weights, source_points,
                        target=35, scale=2, turn_180=True, overrides=overrides, walk=walk)
                    close(links, preview['measurements']['links'])
                    assert abs(preview['measurements']['height'] - height) < 2e-5
                    for name in ('elbow', 'hand', 'finger'):
                        assert any(name in warning and 'normalized' in warning.lower() for warning in result['warnings'])
                    assert source_state(rig, meshes) == before


def assert_arm_rest_angle_shared_plan(addon):
    # Observe the real planner, deformation and codec paths: a per-LOD rebuild or
    # a freshly discovered admission set would disconnect preflight/publication.
    human = importlib.import_module(addon.__name__ + '.o3d_io.omsi_human')
    exporter = importlib.import_module(addon.__name__ + '.o3d_io.io_o3d_export')
    planner, factory = human.build_arm_transforms, human.make_rest_deformer
    prepare = exporter.prepare_o3d_geometry
    plans, callbacks, admissions, uses = [], [], [], []

    def plan_once(armature, *, rest_angle_degrees):
        assert rest_angle_degrees == 35
        plan = planner(armature, rest_angle_degrees=rest_angle_degrees)
        plans.append(plan)
        return plan

    def deform_once(armature, plan, *, allowed_names):
        assert plan is plans[-1]
        assert allowed_names == set(armature.data.bones.keys())
        admissions.append(allowed_names)
        callback = factory(armature, plan, allowed_names=allowed_names)
        callbacks.append(callback)

        def observed(obj, mesh):
            uses.append(obj.original)
            callback(obj, mesh)
        return observed

    def prepare_same(*args, allowed_names=None, **kwargs):
        assert allowed_names is admissions[-1]
        return prepare(*args, allowed_names=allowed_names, **kwargs)

    with preserve_context(), bundle_fixture(addon, binding_form='parent', extra=True) as fixture:
        rig, meshes, _, _, _ = fixture
        before = source_state(rig, meshes)
        human.build_arm_transforms, human.make_rest_deformer = plan_once, deform_once
        exporter.prepare_o3d_geometry = prepare_same
        try:
            with tempfile.TemporaryDirectory(prefix='o3d-rest-shared-') as directory:
                path = Path(directory) / 'character.hum'
                for preflight in (True, False):
                    uses.clear()
                    count = len(plans)
                    human.export_human(str(path), bpy.context, rig, meshes, normalize_arms=True,
                                       arm_rest_angle=35, preflight_only=preflight)
                    assert len(plans) == len(callbacks) == count + 1
                    assert uses.count(meshes[0]) == (2 if preflight else 3)
                    assert all(uses.count(obj) == (1 if preflight else 2) for obj in meshes[1:])
                    assert source_state(rig, meshes) == before
                    if preflight:
                        assert not path.exists()
        finally:
            human.build_arm_transforms, human.make_rest_deformer = planner, factory
            exporter.prepare_o3d_geometry = prepare


def assert_arm_rest_angle_compatibility(addon):
    # Default/explicit zero and unused invalid angles retain exact historical
    # bytes; active invalid angles must preserve every destination sentinel.
    human = importlib.import_module(addon.__name__ + '.o3d_io.omsi_human')
    with preserve_context(), bundle_fixture(addon, extra=True, custom=True) as fixture:
        rig, meshes, _, _, _ = fixture
        before = source_state(rig, meshes)
        with tempfile.TemporaryDirectory(prefix='o3d-rest-compat-') as directory:
            root = Path(directory)
            for normalized in (False, True):
                default = root / f'{normalized}-default'
                human.export_human(str(default / 'character.hum'), bpy.context, rig, meshes, normalize_arms=normalized)
                expected = bundle_bytes(default)
                angles = (0,) if normalized else (0, -15, -89, 35, *INVALID_ANGLES)
                for index, angle in enumerate(angles):
                    destination = root / f'{normalized}-{index}'
                    human.export_human(str(destination / 'character.hum'), bpy.context, rig, meshes,
                                       normalize_arms=normalized, arm_rest_angle=angle)
                    assert bundle_bytes(destination) == expected
                    assert source_state(rig, meshes) == before
            sentinel = root / 'sentinels'
            for name in ('character.hum', 'model/character.cfg',
                         *(f'model/arm_lod_{i}.o3d' for i in range(3))):
                path = sentinel / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'REST ANGLE SENTINEL ' + name.encode())
            disk_before = disk_snapshot(sentinel)
            for angle in INVALID_ANGLES:
                for preflight in (False, True):
                    refuses_angle(lambda: human.export_human(str(sentinel / 'character.hum'), bpy.context,
                        rig, meshes, normalize_arms=True, arm_rest_angle=angle,
                        overwrite=True, preflight_only=preflight))
                    assert disk_snapshot(sentinel) == disk_before
                    assert source_state(rig, meshes) == before


PUBLIC_CHECKS = {'plan': assert_arm_rest_angle_plan, 'identity': assert_arm_rest_angle_identity,
                 'bundle': assert_arm_rest_angle_bundle, 'shared': assert_arm_rest_angle_shared_plan,
                 'compatibility': assert_arm_rest_angle_compatibility}
CHECKS = list(PUBLIC_CHECKS.values())


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', choices=(*PUBLIC_CHECKS, 'all'), default='all')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    addon = load_addon()
    try:
        addon.register()
        for name, check in PUBLIC_CHECKS.items():
            if args.check in (name, 'all'):
                check(addon)
                print('ARM_REST_ANGLE_CHECK_OK', name, bpy.app.version_string)
    finally:
        addon.unregister()


if __name__ == '__main__':
    run()
