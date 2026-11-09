"""Standalone: blender --background --factory-startup --disable-autoexec
--python-exit-code 1 --python tests/smoke_human.py [-- --check NAME].
Real Blender fixtures; never resave the supplied integration scene.
"""
import importlib
import math
import sys
import tempfile
import traceback
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from smoke_support import load_addon

# Independent anatomical values, not derived from the measurement implementation.
POINTS = {
    'Main': (0, .02, 1.15), 'Hip': (0, .03, .95), 'Head': (0, -.01, 1.65),
    'OS_L': (-.1, .03, .95), 'OS_R': (.1, .03, .95),
    'US_L': (-.1, -.02, .5), 'US_R': (.1, -.02, .5),
    'OA_L': (-.2, -.04, 1.45), 'OA_R': (.2, -.04, 1.45),
    'UA_L': (-.45, -.03, 1.4), 'UA_R': (.45, -.03, 1.4),
    'Hand_L': (-.65, -.02, 1.38), 'Hand_R': (.65, -.02, 1.38),
}
EXPECTED = [.1, .03, .95, .1, -.02, .5, .02, 1.15, .2, -.04, 1.45,
            .45, -.03, 1.4, -.01, 1.55, .65, -.02, 1.38, .75, -.02, 1.38]
SOURCE_NAMES = {'Main': '上半身', 'Hip': '下半身', 'Head': '頭'}
for stem, japanese in [('OS', '足'), ('US', 'ひざ'), ('OA', '腕'),
                       ('UA', 'ひじ'), ('Hand', '手首')]:
    for side in ('L', 'R'):
        SOURCE_NAMES[stem + '_' + side] = japanese + '.' + side


def close(actual, expected):
    assert len(actual) == len(expected), (actual, expected)
    assert all(abs(a - b) < 2e-5 for a, b in zip(actual, expected)), (actual, expected)


def refuses(call, word=None):
    try:
        call()
    except (ValueError, TypeError) as error:
        if word:
            assert word.lower() in str(error).lower(), str(error)
    else:
        raise AssertionError('invalid human input was accepted')


def fixture(addon, *, source_points=True):
    rigmod = importlib.import_module(addon.__name__ + '.o3d_io.mmd_rig')
    segments = {name: (Vector(point), Vector(point) + Vector((0, 0, .08)))
                for name, point in POINTS.items()}
    rig = rigmod._create_armature('Human Canonical', segments, bpy.context.scene.collection)
    # Helpers deliberately precede genuine joints, including broad substring traps.
    source_segments = {name: (Vector((9, 9, 9)), Vector((9, 9, 10)))
                       for name in ('_dummy首', '_shadow中指１.L', '中指１_dummy.R',
                                    '首捩', '中指１IK.L')}
    source_segments.update({SOURCE_NAMES[name]: pair for name, pair in segments.items()})
    if source_points:
        for name, point in {'首': (0, -.01, 1.55), '中指１.L': (-.75, -.02, 1.38),
                            '中指１.R': (.75, -.02, 1.38)}.items():
            source_segments[name] = (Vector(point), Vector(point) + Vector((0, 0, .03)))
    source = rigmod._create_armature('Human Source', source_segments, bpy.context.scene.collection)
    data = bpy.data.meshes.new('Human Geometry')
    data.from_pydata([(0, 0, 0), (.1, 0, 1.8), (-.1, 0, 1.8),
                      (.2, -.04, 1.45), (.25, -.04, 1.45), (.2, .01, 1.45)],
                     [], [(0, 1, 2), (3, 4, 5)])
    mesh = bpy.data.objects.new('Human Mesh', data)
    bpy.context.scene.collection.objects.link(mesh)
    modifier = mesh.modifiers.new('Human Armature', 'ARMATURE')
    modifier.object = rig
    mesh.vertex_groups.new(name='Main').add(list(range(6)), 1, 'REPLACE')
    bpy.context.view_layer.update()
    return rig, mesh, source


def assert_serializer(addon, human):
    measurements = {'errors': [], 'warnings': [], 'height': 1.8,
                    'links': [float(i) / 10 for i in range(22)], 'landmarks': {}}
    payload = human.serialize_hum('character.cfg', measurements)
    assert b'[model]\r\ncharacter.cfg\r\n' in payload
    assert b'[mass]\r\n0.07\r\n' in payload
    assert b'\n' not in payload.replace(b'\r\n', b'')
    lines = payload.decode('cp1252').splitlines()
    assert [line for line in lines if line.startswith('[')] == [
        '[model]', '[seatheight]', '[humangeom]', '[links]', '[walk_param]', '[voice]', '[mass]']
    start, end = lines.index('[links]') + 1, lines.index('[walk_param]')
    assert [float(line) for line in lines[start:end] if line.strip()] == measurements['links']
    assert lines[lines.index('[seatheight]') + 1] == '0.9'
    assert lines[lines.index('[walk_param]') + 1:lines.index('[walk_param]') + 6] == ['1.4', '80', '1', '1', '0']
    assert lines[lines.index('[voice]') + 1] == 'M2'
    custom = human.serialize_hum('modèle.cfg', measurements, {'mass_kg': 90, 'voice': 'M4'})
    assert b'0.09\r\n' in custom and 'modèle.cfg'.encode('cp1252') in custom
    for bad in ('x\n[mass]', 'x\r.cfg', 'x\x00.cfg', 'x\x85.cfg', 'x[model].cfg',
                '/tmp/x.cfg', 'C:\\x.cfg', '..\\x.cfg', '😀.cfg', ''):
        refuses(lambda: human.serialize_hum(bad, measurements))
    for key, value in [('voice', ''), ('voice', 'M2\n[mass]'), ('voice', '😀'),
                       ('mass_kg', 0), ('mass_kg', float('nan')), ('seat_height', -1),
                       ('feetdist', -1), ('walk_params', [1, 2]),
                       ('walk_params', [1, 2, 3, 4, float('inf')])]:
        refuses(lambda: human.serialize_hum('x.cfg', measurements, {key: value}))
    for patch in ({'errors': ['neck missing']}, {'height': 0}, {'height': float('inf')},
                  {'links': [0] * 21}, {'links': [float('nan')] * 22}, {'links': None}):
        refuses(lambda: human.serialize_hum('x.cfg', dict(measurements, **patch)))


def assert_measurements(addon, human):
    rig, mesh, source = fixture(addon)
    human.capture_landmarks(source, rig)
    result = human.measure_human(rig, [mesh])
    assert not result['errors'], result
    close(result['links'], EXPECTED)
    assert abs(result['height'] - 1.8) < 1e-5
    close(result['landmarks']['neck'], (0, -.01, 1.55))
    close(result['landmarks']['finger'], (.75, -.02, 1.38))
    # Pose and display units must not change rest measurements or modifier state.
    rig.pose.bones['Main'].location.z = 10
    bpy.context.scene.unit_settings.scale_length = .001
    bpy.context.view_layer.update()
    posed = human.measure_human(rig, [mesh])
    close(posed['links'], EXPECTED)
    assert abs(posed['height'] - 1.8) < 1e-5
    assert mesh.modifiers[0].show_viewport and mesh.modifiers[0].show_render
    bpy.context.scene.unit_settings.scale_length = 1


def assert_missing_and_overrides(addon, human):
    rig, mesh, source = fixture(addon, source_points=False)
    human.capture_landmarks(source, rig)
    result = human.measure_human(rig, [mesh])
    assert result['links'] is None
    assert any('neck' in error.lower() for error in result['errors']), result
    assert any('finger' in error.lower() for error in result['errors']), result
    overrides = {'neck': (-.01, 1.55), 'finger': (.75, -.02, 1.38), 'height': 1.9}
    fixed = human.measure_human(rig, [mesh], overrides=overrides)
    assert not fixed['errors'], fixed
    close(fixed['links'], EXPECTED)
    assert fixed['height'] == 1.9
    metadata = rig['omsi_human_landmarks'].to_dict()
    metadata['points'] = {'finger_L': [float('nan'), 0, 1], 'finger_R': [.75, -.02, 1.38]}
    rig['omsi_human_landmarks'] = metadata
    assert not human.measure_human(rig, [mesh], overrides=overrides)['errors']
    for patch in ({'neck': [1]}, {'finger': [1, 2, float('nan')]}, {'height': -1},
                  {'height': float('inf')}, {'hip': [-1, 0, 1]}, {'hip': [1e300, 0, 1]},
                  {'waist': [1, 2, 3, 4]}):
        assert human.measure_human(rig, [mesh], overrides=dict(overrides, **patch))['errors']
    rigmod = importlib.import_module(addon.__name__ + '.o3d_io.mmd_rig')
    converted = rigmod.convert(mesh, source, rigmod.ConversionOptions())
    assert converted.mesh and converted.armature  # Missing anatomy never breaks generic conversion.


def assert_conversion_metadata(addon, human):
    rigmod = importlib.import_module(addon.__name__ + '.o3d_io.mmd_rig')
    rig, mesh, source = fixture(addon)
    mesh.modifiers[0].object = source
    for group in list(mesh.vertex_groups):
        mesh.vertex_groups.remove(group)
    mesh.vertex_groups.new(name='上半身').add(list(range(6)), 1, 'REPLACE')
    seen = []
    def callback(result):
        assert 'omsi_human_landmarks' in result.armature
        seen.append(result.armature.name)
    source_name = source.name
    result = rigmod.convert(mesh, source, rigmod.ConversionOptions(delete_source_rig=True), on_complete=callback)
    assert seen and bpy.data.objects.get(source_name) is None
    measured = human.measure_human(result.armature, [result.mesh])
    assert not measured['errors'], measured
    close(measured['landmarks']['neck'], (0, -.01, 1.55))
    close(measured['landmarks']['finger'], (.75, -.02, 1.38))
    # Capture must occur inside conversion's rollback boundary, before callback/deletion.
    rig, mesh, source = fixture(addon)
    before = set(bpy.data.objects)
    def fail(result):
        assert 'omsi_human_landmarks' in result.armature
        raise ValueError('test callback rollback')
    refuses(lambda: rigmod.convert(mesh, source, rigmod.ConversionOptions(delete_source_rig=True), on_complete=fail), 'rollback')
    assert set(bpy.data.objects) == before and source.name in bpy.data.objects


def assert_template_metadata(addon, human):
    rigmod = importlib.import_module(addon.__name__ + '.o3d_io.mmd_rig')
    rig, mesh, source = fixture(addon)
    human.capture_landmarks(source, rig)
    template = rig
    # Different source neck must not be transplanted onto the template shape.
    bpy.context.view_layer.objects.active = source
    bpy.ops.object.mode_set(mode='EDIT')
    source.data.edit_bones['首'].head.z = 4
    bpy.ops.object.mode_set(mode='OBJECT')
    converted = rigmod.convert(mesh, source, rigmod.ConversionOptions(rig_mode='TEMPLATE', template_armature=template))
    result = human.measure_human(converted.armature, [converted.mesh])
    assert not result['errors'], result
    close(result['landmarks']['neck'], (0, -.01, 1.55))
    metadata = template['omsi_human_landmarks'].to_dict()
    del template['omsi_human_landmarks']
    other = rigmod.convert(mesh, source, rigmod.ConversionOptions(rig_mode='TEMPLATE', template_armature=template))
    assert human.measure_human(other.armature, [other.mesh])['links'] is None
    # Corrupt optional measurement metadata is incompatible, not a conversion failure.
    metadata['points']['neck'] = [float('nan'), 0, 1]
    template['omsi_human_landmarks'] = metadata
    other = rigmod.convert(mesh, source, rigmod.ConversionOptions(rig_mode='TEMPLATE', template_armature=template))
    assert human.measure_human(other.armature, [other.mesh])['links'] is None


def assert_stale(addon, human):
    rig, mesh, source = fixture(addon)
    human.capture_landmarks(source, rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    rig.data.edit_bones['Main'].head.z += .03
    bpy.ops.object.mode_set(mode='OBJECT')
    stale = human.measure_human(rig, [mesh])
    assert stale['links'] is None and any('stale' in message.lower() for message in stale['errors'])
    accepted = human.measure_human(rig, [mesh], confirm_stale=True)
    assert not accepted['errors'] and any('stale' in message.lower() for message in accepted['warnings'])
    fixed = human.measure_human(rig, [mesh], overrides={'neck': (-.01, 1.55), 'finger': (.75, -.02, 1.38)})
    assert not fixed['errors'], fixed


def assert_alignment_and_transforms(addon, human):
    rig, mesh, source = fixture(addon)
    human.capture_landmarks(source, rig)
    for matrix in (Matrix.Diagonal((1, 2, 1, 1)), Matrix.Diagonal((-1, 1, 1, 1)),
                   Matrix.Diagonal((0, 1, 1, 1)), Matrix.Rotation(.2, 4, 'X'),
                   Matrix(((1, .2, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)))):
        rig.matrix_world = matrix
        bpy.context.view_layer.update()
        assert human.measure_human(rig, [mesh])['errors'], matrix
    rig.matrix_world = Matrix.Identity(4)
    mesh.scale = (1, 2, 1)
    bpy.context.view_layer.update()
    assert human.measure_human(rig, [mesh])['errors']
    mesh.scale = (1, 1, 1)
    for bad in (0, -1, float('nan'), float('inf')):
        assert human.measure_human(rig, [mesh], scale=bad)['errors']
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    rig.data.edit_bones['OS_L'].head.x = .15
    rig.data.edit_bones['OS_R'].head.x = .2
    bpy.ops.object.mode_set(mode='OBJECT')
    assert any('opposite' in error.lower() for error in human.measure_human(rig, [mesh], confirm_stale=True)['errors'])
    # Identity object transforms are not proof that rest anatomy is upright.
    rig, mesh, source = fixture(addon)
    human.capture_landmarks(source, rig)
    rig.data.transform(Matrix.Rotation(math.pi / 2, 4, 'Y'))
    assert human.measure_human(rig, [mesh], confirm_stale=True)['errors']


def assert_symmetry(addon, human):
    rig, mesh, source = fixture(addon)
    human.capture_landmarks(source, rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    rig.data.edit_bones['OA_R'].head.x += .05
    rig.data.edit_bones['Main'].head.x = .03
    bpy.ops.object.mode_set(mode='OBJECT')
    result = human.measure_human(rig, [mesh], confirm_stale=True)
    assert not result['errors'], result
    assert any('symmetr' in warning.lower() for warning in result['warnings'])
    assert any('off-center' in warning.lower() for warning in result['warnings'])
    assert abs(result['landmarks']['shoulder'][0] - .225) < 1e-5


def assert_bounds_and_physics(addon, human):
    rig, mesh, source = fixture(addon)
    human.capture_landmarks(source, rig)
    low = mesh.copy()
    low.data = mesh.data.copy()
    bpy.context.scene.collection.objects.link(low)
    low['omsi_lod_level'] = 1
    low.data.vertices[1].co.z = 20
    collider = mesh.copy()
    collider.data = mesh.data.copy()
    bpy.context.scene.collection.objects.link(collider)
    bpy.ops.object.select_all(action='DESELECT')
    collider.select_set(True)
    bpy.context.view_layer.objects.active = collider
    bpy.ops.rigidbody.object_add()
    collider.data.vertices[1].co.z = 30
    constraint = collider.constraints.new('CHILD_OF')
    constraint.target, constraint.subtarget = rig, 'Head'
    result = human.measure_human(rig, [mesh, low, collider])
    assert not result['errors'], result
    assert abs(result['height'] - 1.8) < 1e-5
    diagnostic = human.physics_diagnostics(rig, [mesh, collider])
    assert diagnostic['body_count'] == 1 and diagnostic['joint_count'] == 0
    assert diagnostic['bone_associations'][collider.name] == 'Head'
    bpy.ops.object.empty_add()
    joint = bpy.context.object
    joint.name = 'Unclassified Joint'
    bpy.ops.rigidbody.constraint_add()
    joint.rigid_body_constraint.object1 = collider
    assert human.physics_diagnostics(rig, [collider, joint])['joint_categories'] == {'other': 1}
    assert human.measure_human(rig, [])['errors']
    assert human.measure_human(rig, [collider, low])['errors']
    # Evaluated non-armature modifiers contribute, rather than raw datablock bounds.
    array = mesh.modifiers.new('Rest vertical copies', 'ARRAY')
    array.count = 2
    array.relative_offset_displace = (0, 0, 1)
    bpy.context.view_layer.update()
    measured = human.measure_human(rig, [mesh])
    assert abs(measured['height'] - 3.6) < 1e-5, measured
    assert array.show_viewport


def assert_coordinate_golden(addon, human):
    rig, mesh, source = fixture(addon)
    human.capture_landmarks(source, rig)
    transform = Matrix.Translation((0, .3, .2)) @ Matrix.Scale(1.25, 4)
    rig.matrix_world = mesh.matrix_world = transform
    bpy.context.view_layer.update()
    result = human.measure_human(rig, [mesh], scale=2)
    assert not result['errors'], result
    close(result['landmarks']['shoulder'], (.5, .5, 4.025))
    assert abs(result['height'] - 4.5) < 1e-5
    assert any('ground' in warning.lower() for warning in result['warnings'])
    bpy.ops.object.select_all(action='DESELECT')
    mesh.select_set(True)
    with tempfile.TemporaryDirectory(prefix='omsi-human-coordinate-') as temporary:
        path = Path(temporary) / 'golden.o3d'
        addon.o3d_io.io_o3d_export.do_export(str(path), bpy.context, Matrix.Scale(2, 4), True, 7)
        parsed = addon.o3d_io.o3dconvert.import_o3d(path.read_bytes())
        expected_o3d = (.5, 4.025, .5)
        assert any((Vector(vertex[0]) - Vector(expected_o3d)).length < 1e-5 for vertex in parsed[1])
        # Native HUM parser consumes XYZ then stores XZY. No axis sign negation.
        x, y, z = result['landmarks']['shoulder']
        close((x, z, y), expected_o3d)
        lines = human.serialize_hum('golden.cfg', result).decode('cp1252').splitlines()
        start = lines.index('[links]') + 1
        close([float(line) for line in lines[start + 8:start + 11]], (.5, .5, 4.025))
    print('HUMAN_COORDINATE_GOLDEN_OK HUM=(0.5,0.5,4.025) O3D=(0.5,4.025,0.5)')


def assert_save_reload(addon, human):
    rig, mesh, source = fixture(addon)
    human.capture_landmarks(source, rig)
    rig['omsi_human_settings'] = dict(human.DEFAULT_SETTINGS)
    name, mesh_name = rig.name, mesh.name
    bpy.data.objects.remove(source, do_unlink=True)
    with tempfile.TemporaryDirectory(prefix='omsi-human-metadata-') as temporary:
        path = str(Path(temporary) / 'metadata.blend')
        bpy.ops.wm.save_as_mainfile(filepath=path)
        bpy.ops.wm.open_mainfile(filepath=path)
        result = human.measure_human(bpy.data.objects[name], [bpy.data.objects[mesh_name]])
        assert not result['errors'], result
        close(result['links'], EXPECTED)
        settings = bpy.data.objects[name]['omsi_human_settings']
        assert settings['mass_kg'] == 70
        assert b'[mass]\r\n0.07\r\n' in human.serialize_hum('reloaded.cfg', result, settings)
    print('HUMAN_METADATA_RELOAD_OK')


def assert_supplied_physics(addon, human):
    path = HERE / 'Untitled2.blend'
    bpy.ops.wm.open_mainfile(filepath=str(path), use_scripts=False)
    rig = next(obj for obj in bpy.context.scene.objects if obj.type == 'ARMATURE')
    dirty_before = bpy.data.is_dirty  # Blender version migration can already dirty a loaded file.
    file_before = (path.stat().st_size, path.stat().st_mtime_ns)
    result = human.physics_diagnostics(rig, bpy.context.scene.objects)
    assert result['body_count'] == 51 and result['joint_count'] == 34, result
    assert result['joint_categories'] == {'skirt': 19, 'hair': 14, 'accessory': 1}, result
    assert result['bone_associations'], result
    assert bpy.data.is_dirty == dirty_before
    assert (path.stat().st_size, path.stat().st_mtime_ns) == file_before
    print('HUMAN_SUPPLIED_PHYSICS_OK', result['body_count'], result['joint_count'], result['joint_categories'])


CHECKS = [assert_serializer, assert_measurements, assert_missing_and_overrides,
          assert_conversion_metadata, assert_template_metadata, assert_stale,
          assert_alignment_and_transforms, assert_symmetry, assert_bounds_and_physics,
          assert_coordinate_golden, assert_save_reload, assert_supplied_physics]


def run():
    addon = load_addon()
    human = importlib.import_module(addon.__name__ + '.o3d_io.omsi_human')
    checks = CHECKS
    if '--check' in sys.argv:
        checks = [check for check in CHECKS if check.__name__ == sys.argv[sys.argv.index('--check') + 1]]
        assert checks, 'unknown human check'
    failures = []
    for check in checks:
        try:
            check(addon, human)
            print('HUMAN_CHECK_OK', check.__name__)
        except Exception:
            traceback.print_exc()
            failures.append(check.__name__)
    assert not failures, failures
    print('BLENDER_HUMAN_SMOKE_OK', len(checks), bpy.app.version_string)


if __name__ == '__main__':
    run()
