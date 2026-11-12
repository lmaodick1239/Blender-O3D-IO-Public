"""Native regressions for the four resumed conversion/export review findings."""
from pathlib import Path
import sys
import tempfile

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import bpy
from mathutils import Matrix

from smoke_character import _mmd_character, _rig, _remove_objects
from smoke_character_fix_round_1 import _source_snapshot, _edit_context, _object_mode
from smoke_character_repair import _refuses
from smoke_lod import _triangle, _collection, _scan


def _constraints(mesh):
    return tuple((c.as_pointer(), c.name, c.type, c.mute, c.influence,
                  c.target.as_pointer() if c.target else None, c.subtarget, c.use_offset)
                 for c in mesh.constraints)


def assert_conversion_constraint_refusal(addon):
    """A live offset COPY_LOCATION to a source bone must refuse without staging."""
    rig = _rig(addon)
    mesh, source = _mmd_character()
    constraint = mesh.constraints.new('COPY_LOCATION')
    constraint.target, constraint.subtarget, constraint.use_offset = source, '頭', True
    bpy.context.view_layer.update()
    assert tuple(mesh.matrix_world.translation) == (4, 5, 8)
    _edit_context(mesh)
    before, constraints = _source_snapshot(mesh, source), _constraints(mesh)
    try:
        _refuses(lambda: rig.convert(mesh, source, rig.ConversionOptions()), 'constraint')
        assert _source_snapshot(mesh, source) == before
        assert _constraints(mesh) == constraints
    finally:
        _object_mode()
        _remove_objects(mesh, source)


def assert_conversion_inactive_constraints_detached(addon):
    """Muted/zero constraints cannot reactivate or retain the old rig on the copy."""
    rig = _rig(addon)
    for inactive in ('mute', 'influence'):
        mesh, source = _mmd_character()
        constraint = mesh.constraints.new('COPY_LOCATION')
        constraint.target, constraint.subtarget, constraint.use_offset = source, '頭', True
        setattr(constraint, inactive, True if inactive == 'mute' else 0)
        bpy.context.view_layer.update()
        world = mesh.matrix_world.copy()
        before, constraints = _source_snapshot(mesh, source), _constraints(mesh)
        result = None
        try:
            result = rig.convert(mesh, source, rig.ConversionOptions())
            assert not result.mesh.constraints, 'inactive source constraints survived copying'
            assert _constraints(mesh) == constraints
            # Source data/context survive success (new IDs are expected).
            assert _source_snapshot(mesh, source)[1:] == before[1:]
            source.location.x += 5
            bpy.context.view_layer.update()
            assert max(abs(a - b) for ar, br in zip(result.mesh.matrix_world, world)
                       for a, b in zip(ar, br)) < 1e-5
            with tempfile.TemporaryDirectory() as tmp:
                bpy.ops.object.select_all(action='DESELECT')
                result.mesh.select_set(True)
                path = Path(tmp) / 'character.o3d'
                addon.o3d_io.io_o3d_export.do_export(str(path), bpy.context, Matrix.Identity(4), True, 7)
                parsed = addon.o3d_io.o3dconvert.import_o3d(path.read_bytes())
                expected = [world @ point.co for point in mesh.data.shape_keys.reference_key.data]
                for vertex in parsed[1]:
                    xyz = (vertex[0][0], vertex[0][2], vertex[0][1])
                    assert min(sum((point[i] - xyz[i]) ** 2 for i in range(3))
                               for point in expected) < 1e-9
        finally:
            _remove_objects(mesh, source, result.mesh if result else None, result.armature if result else None)


def _collection_snapshot():
    return tuple((col.as_pointer(), tuple(obj.as_pointer() for obj in col.objects),
                  tuple(child.as_pointer() for child in col.children)) for col in bpy.data.collections)


def _destination_refuses(addon, mesh, source, destination, fragment):
    _edit_context(mesh)
    before, collections = _source_snapshot(mesh, source), _collection_snapshot()
    try:
        _refuses(lambda: _rig(addon).convert(mesh, source, _rig(addon).ConversionOptions(
            target_collection=destination.name)), fragment)
        assert _source_snapshot(mesh, source) == before
        assert _collection_snapshot() == collections
    finally:
        _object_mode()


def assert_conversion_destination_refusal(addon):
    """Global, foreign, excluded, hidden and LOD destinations refuse before mutation."""
    for case in ('unlinked', 'foreign', 'shared_scene', 'excluded', 'layer_hidden',
                 'collection_hidden', 'ancestor_hidden', 'lod', 'lod_ancestor'):
        mesh, source = _mmd_character()
        parent = _collection('LOD_0.314' if case == 'lod_ancestor' else 'Review parent')
        destination = bpy.data.collections.new('LOD_0.271' if case == 'lod' else 'Review target')
        other = None
        if case not in ('unlinked', 'foreign'):
            parent.children.link(destination)
        if case in ('foreign', 'shared_scene'):
            other = bpy.data.scenes.new('Review foreign scene')
            other.collection.children.link(destination)
        bpy.context.view_layer.update()
        layer = bpy.context.view_layer.layer_collection.children[parent.name]
        if case in ('excluded', 'layer_hidden'):
            setattr(layer.children[destination.name], 'exclude' if case == 'excluded' else 'hide_viewport', True)
        elif case == 'collection_hidden':
            destination.hide_viewport = True
        elif case == 'ancestor_hidden':
            layer.hide_viewport = True
        try:
            _destination_refuses(addon, mesh, source, destination, 'target')
        finally:
            _remove_objects(mesh, source)
            bpy.data.collections.remove(destination)
            bpy.data.collections.remove(parent)
            if other:
                bpy.data.scenes.remove(other)


def assert_conversion_new_lod_destination_refusal(addon):
    """A new LOD-named target must not silently change CFG level membership."""
    mesh, source = _mmd_character()
    _edit_context(mesh)
    before = _source_snapshot(mesh, source)
    try:
        _refuses(lambda: _rig(addon).convert(mesh, source, _rig(addon).ConversionOptions(
            target_collection='LOD_0.987')), 'target')
        assert _source_snapshot(mesh, source) == before
    finally:
        _object_mode()
        _remove_objects(mesh, source)


def assert_conversion_library_destination_refusal(addon):
    """Real linked and override collection IDs are never conversion write targets."""
    with tempfile.TemporaryDirectory() as tmp:
        path = str(Path(tmp) / 'destination.blend')
        local = bpy.data.collections.new('Review library target')
        bpy.data.libraries.write(path, {local})
        bpy.data.collections.remove(local)
        with bpy.data.libraries.load(path, link=True) as (data_from, data_to):
            data_to.collections = ['Review library target']
        linked = data_to.collections[0]
        bpy.context.scene.collection.children.link(linked)
        override = linked.override_create(remap_local_usages=False)
        override.name = 'Review override target'
        bpy.context.scene.collection.children.link(override)
        try:
            for destination in (linked, override):
                mesh, source = _mmd_character()
                try:
                    _destination_refuses(addon, mesh, source, destination, 'target')
                finally:
                    _remove_objects(mesh, source)
        finally:
            bpy.data.collections.remove(override)
            bpy.data.collections.remove(linked)


def assert_conversion_valid_destination(addon):
    """A visible editable nested destination retains supported conversion and context."""
    mesh, source = _mmd_character()
    parent = _collection('Review editable parent')
    destination = _collection('Review editable target', parent)
    _edit_context(mesh)
    before = _source_snapshot(mesh, source)
    result = None
    try:
        result = _rig(addon).convert(mesh, source, _rig(addon).ConversionOptions(target_collection=destination.name))
        assert _source_snapshot(mesh, source)[1:] == before[1:]
        assert set(destination.objects) == {result.mesh, result.armature}
        for obj in (result.mesh, result.armature):
            assert obj.name in bpy.context.scene.objects and obj.name in bpy.context.view_layer.objects
            assert obj.visible_get()
    finally:
        _object_mode()
        _remove_objects(mesh, source, result.mesh if result else None, result.armature if result else None)
        bpy.data.collections.remove(destination)
        bpy.data.collections.remove(parent)


def _export_pair(addon, paths, *, rejected=False, fragment=None, setup=None):
    first = _triangle('Review first geometry', bpy.context.scene.collection)
    second = _triangle('Review second geometry', bpy.context.scene.collection)
    first['export_path'], second['export_path'] = paths
    second.location.x = 10
    bpy.ops.object.select_all(action='DESELECT')
    first.select_set(True)
    second.select_set(True)
    bpy.context.view_layer.objects.active = first
    # scene.objects order is the exporter order, so the safe first file proves
    # that a late invalid/colliding second path cannot cause partial output.
    ordered = list(bpy.context.selected_objects)
    with tempfile.TemporaryDirectory() as tmp:
        root, path = Path(tmp), Path(tmp) / 'model.cfg'
        if setup:
            setup(root)
        before_paths = set(root.rglob('*'))
        before_bytes = {item: item.read_bytes() for item in before_paths if item.is_file()}
        before_links = {item: item.readlink() for item in before_paths if item.is_symlink()}
        try:
            call = lambda: addon.o3d_io.io_o3d_export.do_export(str(path), bpy.context, Matrix.Identity(4), True, 7)
            if rejected:
                try:
                    call()
                except ValueError as error:
                    if fragment:
                        assert fragment.lower() in str(error).lower(), str(error)
                    if fragment == 'collid':
                        assert first.name in str(error) and second.name in str(error), str(error)
                        assert repr(str(root))[1:-1] in str(error), str(error)
                else:
                    raise AssertionError('distinct objects with colliding output paths were accepted')
                assert set(root.rglob('*')) == before_paths, 'path rejection left partial output files'
                assert {item: item.read_bytes() for item in before_bytes} == before_bytes, \
                    'path rejection changed preexisting output bytes'
                assert {item: item.readlink() for item in before_links} == before_links, \
                    'path rejection changed preexisting symlinks'
            else:
                call()
                assert _scan(path) == ([], [(None, obj['export_path']) for obj in ordered])
                for obj, expected_x in ((first, [0, 0, 1]), (second, [10, 10, 11])):
                    disk_path = root / obj['export_path'].replace('\\', '/')
                    parsed = addon.o3d_io.o3dconvert.import_o3d(disk_path.read_bytes())
                    assert sorted(vertex[0][0] for vertex in parsed[1]) == expected_x
        finally:
            _remove_objects(first, second)


def _symlink_outputs(root, target, aliases):
    (root / target).write_bytes(b'preexisting destination bytes\x00\xff')
    for alias in aliases:
        (root / alias).symlink_to(target)


def assert_export_path_collision_refusal(addon):
    """Lexical duplicates and real symlink aliases cannot lose geometry."""
    for paths in (('same.o3d', 'same.o3d'), ('nested/same.o3d', r'nested\same.o3d'),
                  ('same.o3d', 'SAME.O3D'), ('nested/./same.o3d', 'nested/same.o3d')):
        _export_pair(addon, paths, rejected=True, fragment='collid')
    # Resolution masks the declared case-only collision on a case-sensitive host.
    _export_pair(addon, ('same.o3d', 'SAME.O3D'), rejected=True, fragment='collid',
                 setup=lambda root: _symlink_outputs(root, 'actual.o3d', ('same.o3d',)))
    # Conversely, distinct declared paths can address one real output file.
    _export_pair(addon, ('first.o3d', 'second.o3d'), rejected=True, fragment='collid',
                 setup=lambda root: _symlink_outputs(root, 'actual.o3d', ('first.o3d', 'second.o3d')))


def assert_export_all_paths_prevalidated(addon):
    """A late traversal or symlink escape cannot leave an earlier valid O3D."""
    _export_pair(addon, ('first.o3d', '../escape.o3d'), rejected=True, fragment='path')
    with tempfile.TemporaryDirectory() as outside:
        _export_pair(addon, ('first.o3d', 'alias/escape.o3d'), rejected=True, fragment='path',
                     setup=lambda root: (root / 'alias').symlink_to(outside, target_is_directory=True))
        assert not list(Path(outside).iterdir())
    # A CFG path itself must not also be a geometry output destination.
    _export_pair(addon, ('first.o3d', 'model.cfg'), rejected=True, fragment='CFG')
    # A CFG symlink must not mask a declared case-only collision with geometry.
    _export_pair(addon, ('first.o3d', 'MODEL.CFG'), rejected=True, fragment='CFG',
                 setup=lambda root: _symlink_outputs(root, 'actual.cfg', ('model.cfg',)))
    # The geometry path may itself be the symlink hiding that lexical collision.
    _export_pair(addon, ('first.o3d', 'MODEL.CFG'), rejected=True, fragment='CFG',
                 setup=lambda root: _symlink_outputs(root, 'actual.o3d', ('MODEL.CFG',)))
    # Distinct CFG/geometry declarations can resolve to the same existing bytes.
    _export_pair(addon, ('first.o3d', 'geometry.o3d'), rejected=True, fragment='CFG',
                 setup=lambda root: _symlink_outputs(root, 'actual.cfg', ('model.cfg', 'geometry.o3d')))


def assert_export_safe_paths_and_shared_lods(addon):
    """Distinct nested files carry distinct coordinates; one Object may serve two LODs."""
    _export_pair(addon, ('high/first.o3d', 'low/second.o3d'))
    _export_pair(addon, ('nested/first.o3d', 'NESTED/second.o3d'))
    # Probe the same temporary filesystem used by _export_pair, not the OS.
    with tempfile.TemporaryDirectory() as tmp:
        probe = Path(tmp) / 'case-probe'
        probe.write_bytes(b'case probe')
        case_sensitive = not probe.with_name('CASE-PROBE').exists()
        print('EXPORT_TEMP_FS_CASE_SENSITIVE', case_sensitive, str(probe.parent), flush=True)
    if case_sensitive:
        # The second lexical key equals the first resolved key, but the
        # declarations and actual symlink targets are distinct.
        _export_pair(addon, ('alias.o3d', 'TARGET.O3D'), setup=lambda root: (
            _symlink_outputs(root, 'target.o3d', ('alias.o3d',)),
            _symlink_outputs(root, 'other.o3d', ('TARGET.O3D',))))
    else:
        # Both declarations resolve to one sentinel; refusal must preserve it
        # and the alias without leaving any partial export output.
        _export_pair(addon, ('alias.o3d', 'TARGET.O3D'), rejected=True, fragment='collid',
                     setup=lambda root: _symlink_outputs(root, 'target.o3d', ('alias.o3d',)))
    high, low = _collection('LOD_0.456'), _collection('LOD_0.123')
    shared = _triangle('Review shared geometry', high)
    low.objects.link(shared)
    shared['export_path'] = 'shared.o3d'
    bpy.ops.object.select_all(action='DESELECT')
    shared.select_set(True)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'shared.cfg'
            addon.o3d_io.io_o3d_export.do_export(str(path), bpy.context, Matrix.Identity(4), True, 7)
            assert _scan(path) == ([.456, .123], [(.456, 'shared.o3d'), (.123, 'shared.o3d')])
            parsed = addon.o3d_io.o3dconvert.import_o3d((Path(tmp) / 'shared.o3d').read_bytes())
            assert len(parsed[1]) == 3
    finally:
        _remove_objects(shared)
        bpy.data.collections.remove(high)
        bpy.data.collections.remove(low)


def _influence_bounds(addon, strict):
    validate = addon.o3d_io.io_o3d_export.validate_o3d_geometry
    geometry = {'verts': [[0] * 8, [0] * 8], 'tris': [], 'bones': [('Main', [(1, 1.0)])]}
    assert validate(geometry, character_runtime=strict) is False  # valid last vertex
    for index in (2, 65535):
        geometry['bones'] = [('Main', [(index, 1.0)])]
        _refuses(lambda: validate(geometry, character_runtime=strict), 'vertex')
    for index in (-1, 65536):
        geometry['bones'] = [('Main', [(index, 1.0)])]
        _refuses(lambda: validate(geometry, character_runtime=strict), '65535')
    geometry['bones'] = [('Main', [(0, 1.0)])]
    geometry['verts'] = []
    _refuses(lambda: validate(geometry, character_runtime=strict), 'vertex')
    geometry['verts'] = [[0] * 8]
    for weight in (0, -1, float('nan'), float('inf')):
        geometry['bones'] = [('Main', [(0, weight)])]
        _refuses(lambda: validate(geometry, character_runtime=strict), 'influence')


def assert_generic_influence_array_bounds(addon):
    """u16 influence indices must also reference an existing serialized vertex."""
    _influence_bounds(addon, False)


def assert_strict_influence_array_bounds(addon):
    """The same serialized array boundary applies to character validation."""
    _influence_bounds(addon, True)


CHECKS = [assert_conversion_constraint_refusal, assert_conversion_inactive_constraints_detached,
          assert_conversion_destination_refusal, assert_conversion_new_lod_destination_refusal,
          assert_conversion_library_destination_refusal,
          assert_conversion_valid_destination, assert_export_path_collision_refusal,
          assert_export_all_paths_prevalidated, assert_export_safe_paths_and_shared_lods,
          assert_generic_influence_array_bounds, assert_strict_influence_array_bounds]


if __name__ == '__main__':
    from smoke_support import load_addon
    addon = load_addon()
    requested = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    checks = [check for check in CHECKS if not requested or check.__name__ in requested]
    assert checks, requested
    for check in checks:
        check(addon)
        print('REVIEW_CHECK_OK', check.__name__, flush=True)
    print('CHARACTER_REVIEW_SMOKE_OK', len(checks), bpy.app.version_string)
