"""Standalone: blender --background --factory-startup --disable-autoexec
--python-exit-code 1 --python tests/smoke_human.py [-- --check NAME].
Real Blender fixtures; never resave the supplied integration scene.
"""
from contextlib import contextmanager
import builtins
import importlib
import math
import os
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


def assert_nested_collection_lods(addon, human):
    rig, mesh, source = fixture(addon)
    human.capture_landmarks(source, rig)
    primary = bpy.data.collections.new('LOD_1')
    lower = bpy.data.collections.new('LOD_0.5')
    try:
        root = bpy.context.scene.collection
        root.children.link(primary)
        root.children.link(lower)
        root.objects.unlink(mesh)
        primary.objects.link(mesh)
        low = mesh.copy()
        low.data = mesh.data.copy()
        low.data.vertices[1].co.z = 20
        lower.objects.link(low)
        # Separate lower buckets are excluded from the primary 1.8-high bounds.
        result = human.measure_human(rig, [mesh, low])
        assert not result['errors'], result
        assert abs(result['height'] - 1.8) < 1e-5, result
        # Nested factors are ambiguous, just as in mesh_lod target validation.
        primary.children.link(lower)
        root.children.unlink(lower)
        result = human.measure_human(rig, [mesh, low])
        assert result['errors'], result
        assert any(low.name in error and 'LOD' in error for error in result['errors']), result
        assert result['height'] is None and result['links'] is None, result
        refuses(lambda: human.serialize_hum('nested.cfg', result))
    finally:
        bpy.data.collections.remove(lower)
        bpy.data.collections.remove(primary)


def assert_multiple_collection_lods(addon, human):
    rig, mesh, source = fixture(addon)
    human.capture_landmarks(source, rig)
    primary = bpy.data.collections.new('LOD_1')
    lower = bpy.data.collections.new('LOD_0.5')
    child = bpy.data.collections.new('Human Parts')
    try:
        root = bpy.context.scene.collection
        root.children.link(primary)
        root.children.link(lower)
        primary.children.link(child)
        root.objects.unlink(mesh)
        primary.objects.link(mesh)
        child.objects.link(mesh)
        # Multiple ownership paths with the same factor remain valid.
        result = human.measure_human(rig, [mesh])
        assert not result['errors'], result
        assert abs(result['height'] - 1.8) < 1e-5, result
        for shared_child in (False, True):
            if shared_child:
                lower.objects.unlink(mesh)
                lower.children.link(child)
            else:
                lower.objects.link(mesh)
            result = human.measure_human(rig, [mesh])
            assert result['errors'], result
            assert any(mesh.name in error and 'LOD' in error for error in result['errors']), result
            assert result['height'] is None and result['links'] is None, result
            refuses(lambda: human.serialize_hum('multiple.cfg', result))
    finally:
        bpy.data.collections.remove(child)
        bpy.data.collections.remove(lower)
        bpy.data.collections.remove(primary)


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


def source_snapshot():
    """Source IDs, rest data, pose, context and modifier flags must be untouched."""
    ids = [*bpy.data.objects, *bpy.data.meshes, *bpy.data.armatures, *bpy.data.images,
           *bpy.data.materials, *bpy.data.scenes, *bpy.data.collections,
           *(material.node_tree for material in bpy.data.materials if material.node_tree)]
    properties = [(item.as_pointer(),
                   repr({key: item[key].to_dict() if hasattr(item[key], 'to_dict') else
                         item[key].to_list() if hasattr(item[key], 'to_list') else item[key]
                         for key in item.keys()})) for item in ids]
    objects = [(obj.as_pointer(), obj.name, obj.data.as_pointer() if obj.data else None,
                tuple(value for row in obj.matrix_world for value in row), obj.mode,
                obj.select_get(), obj.hide_get(),
                [(mod.name, mod.show_viewport, mod.show_render) for mod in obj.modifiers],
                [(bone.name, tuple(value for row in bone.matrix_basis for value in row))
                 for bone in obj.pose.bones] if obj.type == 'ARMATURE' else [])
               for obj in bpy.context.scene.objects]
    vertices = [(mesh.as_pointer(), [(tuple(v.co), [(g.group, g.weight) for g in v.groups])
                                    for v in mesh.vertices]) for mesh in bpy.data.meshes]
    active = bpy.context.view_layer.objects.active
    return repr((properties, objects, vertices, active.as_pointer() if active else None))


@contextmanager
def export_fixture(addon):
    collections = (bpy.data.objects, bpy.data.meshes, bpy.data.armatures,
                   bpy.data.materials, bpy.data.images, bpy.data.collections)
    before = [set(items) for items in collections]
    rig, mesh, source = fixture(addon)
    mesh['export_path'] = 'body.o3d'
    try:
        yield rig, mesh, source
    finally:
        if bpy.context.object and bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        for items, saved in zip(collections, before):
            for item in set(items) - saved:
                items.remove(item, do_unlink=True)


def select_only(*objects):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0] if objects else None


def copy_mesh(mesh, name, collection=None):
    obj = mesh.copy()
    obj.data = mesh.data.copy()
    obj.name = name
    (collection or bpy.context.scene.collection).objects.link(obj)
    obj['export_path'] = name + '.o3d'
    return obj


REQUIRED_OVERRIDES = {'neck': (-.01, 1.55), 'finger': (.75, -.02, 1.38)}


def disk_snapshot(root):
    return {str(path.relative_to(root)): ('link', str(path.readlink())) if path.is_symlink()
            else ('file', path.read_bytes()) if path.is_file() else ('directory',)
            for path in root.rglob('*')}


def assert_export_bundle(addon, human):
    """Real serialized bones, per-LOD bindings and source immutability."""
    with export_fixture(addon) as (rig, mesh, source), tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        mesh.vertex_groups.new(name='Hip').add([0, 1, 2], .3, 'REPLACE')
        mesh.vertex_groups.new(name='OA_L')  # Empty canonical groups must not get bindings.
        mesh.vertex_groups.new(name='helper😀').add([0], .5, 'REPLACE')
        mesh.data['cfg_data'] = [['[setbone]', 'stale_mesh', '42'], ['[smoothskin]'], ['[visible]', '1']]
        material = bpy.data.materials.new('Human preserved material')
        material.use_nodes = True
        image = bpy.data.images.new('Human texture', width=1, height=1)
        image.filepath = str(root / 'texture' / 'body.bmp')
        texture = material.node_tree.nodes.new('ShaderNodeTexImage')
        texture.image = image
        shader = material.node_tree.nodes.get('Principled BSDF')
        material.node_tree.links.new(texture.outputs['Color'], shader.inputs['Base Color'])
        material['cfg_data'] = [['[setbone]', 'stale_material', '99'], ['[smoothskin]'], ['[matl_noZwrite]']]
        mesh.data.materials.append(material)
        high = bpy.data.collections.new('LOD_0.92')
        low_collection = bpy.data.collections.new('LOD_0.23')
        bpy.context.scene.collection.children.link(high)
        bpy.context.scene.collection.children.link(low_collection)
        bpy.context.scene.collection.objects.unlink(mesh)
        high.objects.link(mesh)
        low = copy_mesh(mesh, 'body_low', low_collection)
        low['omsi_lod_level'] = 1
        low.vertex_groups.remove(low.vertex_groups['Hip'])
        low.vertex_groups.remove(low.vertex_groups['helper😀'])
        # Pose, disabled modifier flag and edit mode must survive both preflight/export.
        rig.pose.bones['Main'].location.z = 3
        mesh.modifiers[0].show_render = False
        select_only(rig)
        bpy.ops.object.mode_set(mode='POSE')
        bpy.context.view_layer.update()
        before = source_snapshot()
        result = human.export_human(str(root / 'character.hum'), bpy.context, rig, [mesh, low],
                                    overrides=REQUIRED_OVERRIDES, scale=2)
        assert source_snapshot() == before
        assert Path(result['hum_path']).is_file() and Path(result['cfg_path']).is_file()
        assert {Path(path).name for path in result['mesh_paths']} == {'body.o3d', 'body_low.o3d'}
        assert all(Path(path).is_file() for path in result['mesh_paths'])
        payload = Path(result['hum_path']).read_bytes()
        assert b'[model]\r\ncharacter.cfg\r\n' in payload
        lines = payload.decode('cp1252').splitlines()
        links = lines.index('[links]') + 1
        close([float(value) for value in lines[links + 14:links + 16]], (-.01, 1.55))
        close([float(value) for value in lines[links + 19:links + 22]], (.75, -.02, 1.38))
        cfg = Path(result['cfg_path']).read_bytes().decode('cp1252')
        assert 'stale_mesh' not in cfg and 'stale_material' not in cfg
        assert '[visible]\n1' in cfg and '[matl_noZwrite]' in cfg
        assert cfg.count('[smoothskin]') == 1, cfg
        slots = importlib.import_module(addon.__name__ + '.o3d_io.mmd_rig').CANONICAL_SLOTS
        for part, expected in ((mesh, {'Main', 'Hip'}), (low, {'Main'})):
            parsed = addon.o3d_io.o3dconvert.import_o3d((root / part['export_path']).read_bytes())
            names = {bone[0] for bone in parsed[4]}
            assert names == expected, names
            block = cfg.split('[mesh]\n' + part['export_path'] + '\n', 1)[1].split('[LOD]', 1)[0]
            for name in names:
                assert f'[setbone]\n{name}\n{slots[name]}\n' in block, block
            assert '[setbone]\nOA_L\n' not in block
        assert any(abs(vertex[0][1] - 3.6) < 1e-5 for vertex in
                   addon.o3d_io.o3dconvert.import_o3d((root / 'body.o3d').read_bytes())[1])
        assert isinstance(result['warnings'], list)


def assert_export_candidates(addon, human):
    with export_fixture(addon) as (rig, mesh, source), tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        low_collection = bpy.data.collections.new('LOD_0.37')
        bpy.context.scene.collection.children.link(low_collection)
        low = copy_mesh(mesh, 'candidate_low', low_collection)
        low['omsi_lod_level'] = 1
        low.hide_set(True)
        sibling = copy_mesh(mesh, 'candidate_sibling')
        unrelated = copy_mesh(mesh, 'candidate_unrelated')
        unrelated.modifiers.clear()
        skipped = copy_mesh(mesh, 'candidate_skipped')
        skipped['skip_export'] = False  # Existing generic convention is key presence.
        collider = copy_mesh(mesh, 'candidate_physics')
        select_only(collider)
        bpy.ops.rigidbody.object_add()
        joint_mesh = copy_mesh(mesh, 'candidate_joint')
        select_only(joint_mesh)
        bpy.ops.rigidbody.constraint_add()
        select_only(rig, collider, joint_mesh)
        before = source_snapshot()
        assert set(human.human_meshes(bpy.context, rig)) == {mesh, low, sibling}
        assert source_snapshot() == before
        select_only(rig, unrelated)
        assert human.human_meshes(bpy.context, rig) == [], 'explicit unrelated mesh must not expand scope'
        select_only(mesh, rig, collider, joint_mesh, unrelated)
        assert human.human_meshes(bpy.context, rig) == [mesh]
        assert set(human.human_meshes(bpy.context, rig, selection_only=False)) == {mesh, low, sibling}
        result = human.export_human(str(root / 'scope.hum'), bpy.context, rig,
                                    [mesh, collider, joint_mesh, unrelated, skipped],
                                    overrides=REQUIRED_OVERRIDES)
        assert {path.name for path in root.rglob('*.o3d')} == {'body.o3d'}
        cfg = Path(result['cfg_path']).read_bytes().decode('cp1252')
        assert cfg.count('[mesh]') == 1 and '[mesh]\nbody.o3d\n' in cfg
        assert not any(obj['export_path'] in cfg for obj in (low, sibling, collider, joint_mesh, unrelated, skipped))
        assert human.physics_diagnostics(rig, [mesh])['body_count'] == 0
        select_only(rig, source)
        refuses(lambda: human.human_meshes(bpy.context, rig), 'rig')
        foreign = copy_mesh(mesh, 'foreign_rig')
        foreign.modifiers[0].object = source
        select_only(mesh, foreign)
        refuses(lambda: human.human_meshes(bpy.context, rig), 'rig')
        dual = mesh.modifiers.new('Other rig', 'ARMATURE')
        dual.object = source
        refuses(lambda: human.export_human(str(root / 'multiple.hum'), bpy.context, rig, [mesh],
                                           overrides=REQUIRED_OVERRIDES), 'rig')
        assert not (root / 'multiple.hum').exists()
        mesh.modifiers.remove(dual)
        # Membership, not bpy.data, excludes meshes in other scenes.
        bpy.context.scene.collection.objects.unlink(foreign)
        select_only(rig)
        assert foreign not in human.human_meshes(bpy.context, rig)


def assert_export_preflight(addon, human):
    """Every refusal leaves the entire pre-existing file set untouched."""
    with export_fixture(addon) as (rig, mesh, source):
        second = copy_mesh(mesh, 'late_body')
        def attempt(paths=('body.o3d', 'late_body.o3d'), *, setup=None, overrides=None,
                    settings=None, filename='character.hum', overwrite=True, version=7):
            mesh['export_path'], second['export_path'] = paths
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                for name in ('character.hum', 'character.cfg', 'body.o3d', 'late_body.o3d'):
                    (root / name).write_bytes(b'SENTINEL\x00\xff ' + name.encode())
                if setup:
                    setup(root)
                before, source_before = disk_snapshot(root), source_snapshot()
                refuses(lambda: human.export_human(str(root / filename), bpy.context, rig, [mesh, second],
                                                   overrides=REQUIRED_OVERRIDES if overrides is None else overrides,
                                                   settings=settings, overwrite=overwrite, o3d_version=version))
                assert disk_snapshot(root) == before
                assert source_snapshot() == source_before
        for existing in ('character.hum', 'character.cfg', 'body.o3d', 'late_body.o3d', 'BODY.O3D'):
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                (root / existing).write_bytes(b'overwrite sentinel')
                before = disk_snapshot(root)
                refuses(lambda: human.export_human(str(root / 'character.hum'), bpy.context, rig, [mesh, second],
                                                   overrides=REQUIRED_OVERRIDES), 'overwrite')
                assert disk_snapshot(root) == before
        attempt(overrides={})
        attempt(overrides=dict(REQUIRED_OVERRIDES, hip=(0, 0, 1)))
        attempt(settings={'voice': 'M2\n[mass]'})
        attempt(settings={'mass_kg': float('nan')})
        attempt(filename='😀.hum')
        attempt(filename='bad\nname.hum')
        attempt(version=999)
        for paths in (('same.o3d', 'SAME.O3D'), ('nested/same.o3d', r'nested\same.o3d'),
                      ('body.o3d', 'CHARACTER.HUM'), ('body.o3d', 'CHARACTER.CFG'),
                      ('body.o3d', '../escape.o3d'), ('body.o3d', 'bad\npath.o3d'),
                      ('body.o3d', '😀.o3d'), ('body.o3d', 'x[mesh].o3d'),
                      ('body.o3d', 'character.hum/inner.o3d'),
                      ('body.o3d', 'character.cfg/inner.o3d'),
                      ('fresh.o3d', 'fresh.o3d/inner.o3d')):
            attempt(paths)
        def aliases(root):
            (root / 'actual.o3d').write_bytes(b'alias sentinel')
            (root / 'one.o3d').symlink_to('actual.o3d')
            (root / 'two.o3d').symlink_to('actual.o3d')
        attempt(('one.o3d', 'two.o3d'), setup=aliases)
        def masked_case(root):
            (root / 'actual.o3d').write_bytes(b'masked lexical sentinel')
            (root / 'same.o3d').symlink_to('actual.o3d')
        attempt(('same.o3d', 'SAME.O3D'), setup=masked_case)
        for destination in ('character.hum', 'character.cfg'):
            def alias_bundle(root, destination=destination):
                (root / 'bundle_alias.o3d').symlink_to(destination)
            attempt(('body.o3d', 'bundle_alias.o3d'), setup=alias_bundle)
        with tempfile.TemporaryDirectory() as outside:
            def escape(root):
                (root / 'escape').symlink_to(outside, target_is_directory=True)
            attempt(('body.o3d', 'escape/out.o3d'), setup=escape)
            assert not list(Path(outside).iterdir())
        # A bad late material/bone/geometry/CFG string must not truncate the first file.
        select_only(rig)
        bpy.ops.object.mode_set(mode='EDIT')
        extra = rig.data.edit_bones.new('😀')
        extra.head, extra.tail = (0, 0, 1), (0, 0, 1.1)
        bpy.ops.object.mode_set(mode='OBJECT')
        second.vertex_groups.new(name='😀').add([0], .5, 'REPLACE')
        attempt()
        second.vertex_groups.remove(second.vertex_groups['😀'])
        material = bpy.data.materials.new('Unserializable human material')
        material['o3d_layered_material'] = True
        second.data.materials.append(material)
        attempt()
        second.data.materials.clear()
        second.data.vertices[0].co.x = float('nan')
        attempt()
        second.data.vertices[0].co.x = 0
        second.data['cfg_data'] = [['[visible]', '1\n[mesh]\nevil.o3d']]
        attempt()
        del second.data['cfg_data']
        scene = bpy.context.scene
        saved = scene.get('friendlyname')
        scene['friendlyname'] = '😀'
        attempt()
        if saved is None:
            del scene['friendlyname']
        else:
            scene['friendlyname'] = saved
        saved_cfg = [list(block) for block in scene['cfg_data']] if 'cfg_data' in scene else None
        scene['cfg_data'] = [['[setbone]', 'Main\n[mesh]\nevil.o3d', '-11']]
        attempt()
        if saved_cfg is None:
            del scene['cfg_data']
        else:
            scene['cfg_data'] = saved_cfg


def assert_export_transform_preflight(addon, human):
    """Finite vertices do not imply a finite serialized object-frame matrix."""
    with export_fixture(addon) as (rig, mesh, source), tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        for vertex in mesh.data.vertices:
            vertex.co *= 1e-10
        mesh.scale = (1e10,) * 3
        bpy.context.view_layer.update()
        measurements = human.measure_human(rig, [mesh], overrides=REQUIRED_OVERRIDES, scale=1e30)
        assert not measurements['errors'], measurements
        before = source_snapshot()
        refuses(lambda: human.export_human(str(root / 'character.hum'), bpy.context, rig, [mesh],
                                           overrides=REQUIRED_OVERRIDES, scale=1e30))
        assert not list(root.iterdir()) and source_snapshot() == before


def assert_export_texture_preflight(addon, human):
    """Non-base CFG texture names share the same prewrite trust boundary."""
    with export_fixture(addon) as (rig, mesh, source), tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        material = bpy.data.materials.new('Human texture preflight')
        material.use_nodes = True
        mesh.data.materials.append(material)
        shader = material.node_tree.nodes.get('Principled BSDF')
        base = material.node_tree.nodes.new('ShaderNodeTexImage')
        base.image = bpy.data.images.new('Base texture', width=1, height=1)
        base.image.filepath = 'base.bmp'
        material.node_tree.links.new(base.outputs['Color'], shader.inputs['Base Color'])
        alpha = material.node_tree.nodes.new('ShaderNodeTexImage')
        alpha.image = bpy.data.images.new('Alpha texture', width=1, height=1)
        material.node_tree.links.new(alpha.outputs['Color'], shader.inputs['Alpha'])
        for filename in ('alpha\n[mesh].bmp', 'alpha\x85.bmp', 'alpha😀.bmp'):
            alpha.image.filepath = filename
            for name in ('character.hum', 'character.cfg', 'body.o3d'):
                (root / name).write_bytes(b'texture preflight sentinel')
            before, source_before = disk_snapshot(root), source_snapshot()
            refuses(lambda: human.export_human(str(root / 'character.hum'), bpy.context, rig, [mesh],
                                               overrides=REQUIRED_OVERRIDES, overwrite=True))
            assert disk_snapshot(root) == before and source_snapshot() == source_before


def assert_export_io_failure(addon, human):
    """Inject only at the real destination open, never the serializer API."""
    with export_fixture(addon) as (rig, mesh, source), tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        cfg = root / 'failure.cfg'
        cfg.write_bytes(b'CFG sentinel')
        body = root / 'body.o3d'
        body.write_bytes(b'geometry sentinel')
        select_only(rig)
        bpy.ops.object.mode_set(mode='POSE')
        mesh.modifiers[0].show_render = False
        before = source_snapshot()
        real_open = builtins.open
        def fail_destination(path, mode='r', *args, **kwargs):
            if os.path.abspath(os.fspath(path)) == str(body) and 'w' in mode:
                raise OSError('injected model destination open failure')
            return real_open(path, mode, *args, **kwargs)
        builtins.open = fail_destination
        try:
            try:
                human.export_human(str(root / 'failure.hum'), bpy.context, rig, [mesh],
                                   overrides=REQUIRED_OVERRIDES, overwrite=True)
            except OSError as error:
                assert 'injected' in str(error)
            else:
                raise AssertionError('injected file open failure was swallowed')
        finally:
            builtins.open = real_open
        assert body.read_bytes() == b'geometry sentinel' and cfg.read_bytes() == b'CFG sentinel'
        assert not (root / 'failure.hum').exists()
        assert source_snapshot() == before
        # A write error can leave a partial O3D: no multi-file rollback is claimed.
        class FailingWriter:
            def __init__(self, stream):
                self.stream = stream
            def __enter__(self):
                self.stream.__enter__()
                return self
            def __exit__(self, *args):
                return self.stream.__exit__(*args)
            def write(self, payload):
                self.stream.write(payload[:1])
                raise OSError('injected model serialization write failure')
        def fail_write(path, mode='r', *args, **kwargs):
            stream = real_open(path, mode, *args, **kwargs)
            return FailingWriter(stream) if os.path.abspath(os.fspath(path)) == str(body) and 'w' in mode else stream
        builtins.open = fail_write
        try:
            try:
                human.export_human(str(root / 'failure.hum'), bpy.context, rig, [mesh],
                                   overrides=REQUIRED_OVERRIDES, overwrite=True)
            except OSError as error:
                assert 'serialization write failure' in str(error)
            else:
                raise AssertionError('injected serializer destination write failure was swallowed')
        finally:
            builtins.open = real_open
        assert cfg.read_bytes() == b'CFG sentinel' and not (root / 'failure.hum').exists()
        assert body.read_bytes() == b'\x84'  # Real first codec byte, not a fabricated output.
        assert source_snapshot() == before
        # Consent permits real replacement of the existing complete bundle.
        result = human.export_human(str(root / 'failure.hum'), bpy.context, rig, [mesh],
                                    overrides=REQUIRED_OVERRIDES, overwrite=True)
        assert Path(result['hum_path']).is_file() and body.read_bytes() != b'geometry sentinel'


CHECKS = [assert_serializer, assert_measurements, assert_missing_and_overrides,
          assert_conversion_metadata, assert_template_metadata, assert_stale,
          assert_alignment_and_transforms, assert_symmetry, assert_bounds_and_physics,
          assert_nested_collection_lods, assert_multiple_collection_lods,
          assert_coordinate_golden, assert_save_reload,
          assert_export_bundle, assert_export_candidates, assert_export_preflight,
          assert_export_transform_preflight, assert_export_texture_preflight,
          assert_export_io_failure, assert_supplied_physics]


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
