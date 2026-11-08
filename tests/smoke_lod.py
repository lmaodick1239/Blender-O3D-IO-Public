"""Native character LOD transactions and actual CFG/O3D integration checks."""
import importlib
import math
from pathlib import Path
import tempfile

import bpy
from mathutils import Matrix


def _module(addon):
    return importlib.import_module(addon.__name__ + '.o3d_io.mesh_lod')


def _clear():
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for collection in list(bpy.data.collections):
        bpy.data.collections.remove(collection)


def _triangle(name, collection):
    data = bpy.data.meshes.new(name + ' Data')
    data.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    return obj


def _collection(name, parent=None):
    col = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(col)
    return col


def _scan(path):
    result, factor = [], None
    lines = path.read_text().splitlines()
    factors = []
    for index, line in enumerate(lines):
        if line == '[LOD]':
            factor = float(lines[index + 1])
            factors.append(factor)
        elif line == '[mesh]':
            result.append((factor, lines[index + 1]))
    return factors, result


def assert_cfg_lod_membership(addon):
    # Catches global nested/multilink duplication, inactive-scene leakage, skip
    # mismatch, same-factor overwrite and visibility filtering of imported LODs.
    _clear()
    parent = _collection('Ordinary Parent')
    high = _collection('LOD_0.2', parent)
    same = _collection('LOD_0.20')
    low = _collection('LOD_0')
    a = _triangle('high', high)
    parent.objects.link(a)
    bpy.context.scene.collection.objects.link(a)
    _triangle('same-factor', same)
    same.objects.link(a)
    c = _triangle('low-hidden', low)
    c.hide_set(True)
    c.hide_render = True
    shared = _triangle('shared', high)
    low.objects.link(shared)
    _triangle('global', parent)
    skipped = _triangle('skipped', high)
    skipped['skip_export'] = False
    unlinked = bpy.data.collections.new('LOD_0.1')
    _triangle('unlinked', unlinked)
    other = bpy.data.scenes.new('Other LOD Scene')
    other_col = bpy.data.collections.new('LOD_0.05')
    other.collection.children.link(other_col)
    _triangle('other-scene', other_col)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'model.cfg'
            addon.o3d_io.io_o3d_export.do_export(str(path), bpy.context, Matrix.Identity(4), False, 7)
            factors, entries = _scan(path)
            assert factors == [.2, 0], factors
            assert len(entries) == 6 and set(entries) == {
                (None, 'global.o3d'), (.2, 'high.o3d'), (.2, 'same-factor.o3d'),
                (.2, 'shared.o3d'), (0, 'low-hidden.o3d'), (0, 'shared.o3d')}, entries
            for _, relative in entries:
                assert (Path(tmp) / relative).is_file(), relative
            bpy.ops.object.select_all(action='DESELECT')
            a.select_set(True)
            skipped.select_set(True)
            addon.o3d_io.io_o3d_export.do_export(str(path), bpy.context, Matrix.Identity(4), True, 7)
            assert _scan(path) == ([.2], [(.2, 'high.o3d')]), _scan(path)
            malformed = _collection('LOD_not-a-factor')
            _triangle('ordinary-invalid-name', malformed)
            addon.o3d_io.io_o3d_export.do_export(str(path), bpy.context, Matrix.Identity(4), False, 7)
            assert (None, 'ordinary-invalid-name.o3d') in _scan(path)[1]
    finally:
        _clear()
        bpy.data.scenes.remove(other)


def _fixture(addon, *, keys=False, topology=False):
    from smoke_character import _armature_with_bones
    names = ['Main', 'Hip', 'Head', 'OA_L', 'UA_L', 'Hand_L', 'OA_R',
             'UA_R', 'Hand_R', 'OS_L', 'US_L', 'OS_R', 'US_R']
    rig = _armature_with_bones('LOD Rig', [(name, (i, 0, 0), (i, 0, 1), None)
                                         for i, name in enumerate(names)],
                              Matrix.Translation((3, 4, 5)) @ Matrix.Rotation(.3, 4, 'Z'))
    rig.pose.bones['Main'].location = (10, 20, 30)
    n = 12
    coords = [(x / n, y / n, 0) for y in range(n + 1) for x in range(n + 1)]
    faces = []
    for y in range(n):
        for x in range(n):
            a = y * (n + 1) + x
            if (x + y) % 2:
                faces.append((a, a + 1, a + n + 2, a + n + 1))
            else:
                faces.extend([(a, a + 1, a + n + 2), (a, a + n + 2, a + n + 1)])
    data = bpy.data.meshes.new('LOD Grid Data')
    data.from_pydata(coords, [], faces)
    uv = data.uv_layers.new(name='Character UV')
    for loop in data.loops:
        uv.data[loop.index].uv = data.vertices[loop.vertex_index].co.xy
    source = bpy.data.objects.new('Character Grid', data)
    ordinary = _collection('Character Parent')
    ordinary.objects.link(source)
    source.parent = rig
    source.matrix_world = Matrix.Translation((7, 8, 9)) @ Matrix.Rotation(.2, 4, 'X')
    source['export_path'] = '/old.o3d'
    source['skip_export'] = False
    source.data['cfg_data'] = [['[setbone]', 'Stale', '-2'], ['[smoothskin]'],
                               ['[visible]', 'keep', '1']]
    source.data['custom_metadata'] = 'preserved'
    material = bpy.data.materials.new('LOD Material')
    source.data.materials.append(material)
    for name in names:
        source.vertex_groups.new(name=name)
    for vertex in data.vertices:
        # Every level must preserve >4 influences, all canonical names and
        # independently predictable numeric weights: 1/91 through 13/91.
        for index, group in enumerate(source.vertex_groups):
            group.add([vertex.index], (index + 1) / 91, 'REPLACE')
    arm = source.modifiers.new('Character Armature', 'ARMATURE')
    arm.object = rig
    arm.show_viewport, arm.show_render = False, True
    if topology:
        sub = source.modifiers.new('Once-only Subdivision', 'SUBSURF')
        sub.levels = 1
        sub.render_levels = 1
    if keys:
        basis = source.shape_key_add(name='Basis')
        smile = source.shape_key_add(name='Smile')
        for point in basis.data:
            point.co.z = 2
        for point in smile.data:
            point.co.z = 7
        smile.value = 1
    bpy.ops.object.select_all(action='DESELECT')
    source.select_set(True)
    bpy.context.view_layer.objects.active = source
    bpy.context.view_layer.update()
    return source, rig


def _props(owner):
    def plain(value):
        if hasattr(value, 'to_dict'):
            return {k: plain(v) for k, v in value.to_dict().items()}
        if hasattr(value, 'to_list'):
            return value.to_list()
        if isinstance(value, (tuple, list)):
            return [plain(v) for v in value]
        return value
    return {key: plain(owner[key]) for key in owner.keys()}


def _snapshot(source):
    return (set(bpy.data.objects), set(bpy.data.meshes), set(bpy.data.materials),
            set(bpy.data.collections), set(bpy.data.texts), source.data,
            tuple(source.users_collection), _props(source), _props(source.data),
            tuple(slot.material for slot in source.material_slots),
            tuple(bpy.context.selected_objects), bpy.context.view_layer.objects.active,
            bpy.context.object.mode if bpy.context.object else 'OBJECT',
            tuple((m.name, m.show_viewport, m.show_render) for m in source.modifiers),
            set(bpy.data.shape_keys), source.data.shape_keys,
            tuple((block.name, block.value, tuple(tuple(point.co) for point in block.data))
                  for block in source.data.shape_keys.key_blocks) if source.data.shape_keys else None)


def _refuses(call):
    try:
        call()
    except (ValueError, RuntimeError):
        return
    raise AssertionError('unsafe/invalid LOD request accepted')


def assert_lod_generation_and_export(addon):
    # Missing generator, ratio compounding, pose baking, cfg metadata loss,
    # influence caps and stale/non-relative file paths all break this fixture.
    _clear()
    source, rig = _fixture(addon)
    original_data = source.data
    original_coords = [v.co.copy() for v in source.data.vertices]
    world = source.matrix_world.copy()
    pose = rig.pose.bones['Main'].matrix.copy()
    context = (bpy.context.view_layer.objects.active, tuple(bpy.context.selected_objects))
    lod = _module(addon)
    try:
        levels = lod.generate_lods(source, [.5, .25], [.2, .1, 0])
        assert levels[0] == source and len(levels) == 3
        assert source.data == original_data
        assert [tuple(o.users_collection)[0].name for o in levels] == ['LOD_0.2', 'LOD_0.1', 'LOD_0']
        assert all(len(o.users_collection) == 1 for o in levels)
        assert len({o.data for o in levels}) == 3
        assert all(o.parent == rig and o.matrix_world == world for o in levels)
        assert rig.pose.bones['Main'].matrix == pose
        assert (bpy.context.view_layer.objects.active, tuple(bpy.context.selected_objects)) == context
        assert [v.co for v in source.data.vertices] == original_coords
        assert len(levels[2].data.polygons) < len(levels[1].data.polygons) < len(source.data.polygons)
        for obj in levels:
            assert obj.data.uv_layers.get('Character UV') is not None
            assert obj.data['custom_metadata'] == 'preserved'
            assert obj.material_slots[0].material == source.material_slots[0].material
            assert 'skip_export' not in obj
            arm = obj.modifiers.get('Character Armature')
            assert arm and (arm.show_viewport, arm.show_render) == (False, True)
            assert all(abs(v.co.z) < 1e-5 for v in obj.data.vertices), 'pose baked'
            for vertex in obj.data.vertices:
                weights = [g.weight for g in vertex.groups if g.weight > 0]
                assert len(weights) == 13 and abs(sum(weights) - 1) < 1e-5
            assert ['[visible]', 'keep', '1'] in [list(b) for b in obj.data['cfg_data']]
            assert addon.o3d_io.io_o3d_export.validate_character_export(obj)['smoothskin']
        paths = [o['export_path'] for o in levels]
        assert len({p.casefold() for p in paths}) == 3
        assert all(not p.startswith(('/', '\\')) and '..' not in p and p != '/old.o3d' for p in paths)
        # Nested LOD ordinary ancestor + root multilink must still classify once.
        parent = bpy.data.collections['Character Parent']
        parent.children.link(bpy.data.collections['LOD_0.2'])
        bpy.context.scene.collection.objects.link(source)
        bpy.ops.object.select_all(action='DESELECT')
        for obj in levels:
            obj.select_set(True)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'character.cfg'
            addon.o3d_io.io_o3d_export.do_export(str(path), bpy.context, Matrix.Identity(4), True, 7)
            factors, entries = _scan(path)
            assert factors == [.2, .1, 0] and entries == list(zip(factors, paths)), (factors, entries)
            text = path.read_text()
            assert text.count('[setbone]') == 39 and text.count('[smoothskin]') == 3, text
            assert 'Stale' not in text
            for relative in paths:
                output = Path(tmp) / relative
                assert output.is_file() and output.resolve().is_relative_to(Path(tmp).resolve())
                decoded = addon.o3d_io.o3dconvert.import_o3d(output.read_bytes())
                bones = decoded[4]
                assert len(bones) == 13, bones
                for index, (name, weights) in enumerate(bones):
                    assert weights and all(abs(weight - (index + 1) / 91) < 1e-5 for _, weight in weights)
                sums = {}
                for _, weights in bones:
                    for vertex, weight in weights:
                        sums[vertex] = sums.get(vertex, 0) + weight
                assert len(sums) == len(decoded[1]) and all(abs(total - 1) < 1e-5 for total in sums.values())
    finally:
        _clear()


def assert_lod_invalid_requests(addon):
    # Invalid inputs must fail without even private datablock or property leaks.
    _clear()
    source, rig = _fixture(addon)
    lod = _module(addon)
    cases = [([], []), ([], [.2, 0]), ([.5], [0]), ([0], [.2, 0]),
             ([-.1], [.2, 0]), ([1], [.2, 0]), ([1.1], [.2, 0]),
             ([float('nan')], [.2, 0]), ([float('inf')], [.2, 0]),
             ([True], [.2, 0]), ([.5], [-.2, 0]), ([.5], [0, .2]),
             ([.5], [.2, .1]), ([.5], [0, 0]), ([.5], [float('nan'), 0]),
             ([.5], [float('inf'), 0]), ([.5], [True, 0]),
             ([.5, .4, .3], [.3, .2, .1, 0])]
    try:
        for ratios, factors in cases:
            before = _snapshot(source)
            _refuses(lambda: lod.generate_lods(source, ratios, factors))
            assert _snapshot(source) == before, (ratios, factors)
        before = _snapshot(source)
        _refuses(lambda: lod.generate_lods(rig, [], [0]))
        assert _snapshot(source) == before
        source.shape_key_add(name='Basis')
        before = _snapshot(source)
        _refuses(lambda: lod.generate_lods(source, [.5], [.2, 0]))
        assert _snapshot(source) == before
        source.shape_key_clear()
        source.vertex_groups[0].name = '日本語'
        before = _snapshot(source)
        _refuses(lambda: lod.generate_lods(source, [.5], [.2, 0]))
        assert _snapshot(source) == before
    finally:
        _clear()


def assert_lod_regeneration_ownership(addon):
    # UUID/name-only ownership would delete copied outputs or another family;
    # removing shared mesh data would destroy the unrelated user's geometry.
    _clear()
    source, rig = _fixture(addon)
    lod = _module(addon)
    try:
        collision = _triangle(source.name + '_LOD1', bpy.context.scene.collection)
        collision['export_path'] = 'OLD_LOD0.O3D'
        foreign_low = _triangle('foreign target content', _collection('LOD_0'))
        levels = lod.generate_lods(source, [.5, .25], [.2, .1, 0])
        old_names = [obj.name for obj in levels[1:]]
        old_paths = [obj['export_path'] for obj in levels]
        old_id = source['omsi_lod_source_id']
        copied_output = levels[1].copy()
        copied_output.data = levels[1].data.copy()
        bpy.context.scene.collection.objects.link(copied_output)
        external = bpy.data.objects.new('external old mesh user', levels[2].data)
        bpy.context.scene.collection.objects.link(external)
        external_data = external.data
        other = source.copy()
        other.data = source.data.copy()
        bpy.context.scene.collection.objects.link(other)
        # A copied source initially refers to old outputs. Original must refuse
        # until the duplicate gets its own manifest; never mutate it implicitly.
        before = _snapshot(source)
        _refuses(lambda: lod.generate_lods(source, [.4], [.3, 0]))
        assert _snapshot(source) == before
        other_levels = lod.generate_lods(other, [.6], [.4, 0])
        assert other['omsi_lod_source_id'] != old_id
        assert other_levels[1]['omsi_lod_owner'] == other
        levels = lod.generate_lods(source, [.35], [.3, 0])
        assert source['omsi_lod_source_id'] == old_id
        assert all(bpy.data.objects.get(name) is None for name in old_names)
        assert all(obj.name in bpy.data.objects for obj in [copied_output, external, collision, foreign_low] + other_levels)
        assert external.data == external_data and external_data.name in bpy.data.meshes
        assert len(levels) == 2 and len(levels[1].data.polygons) < 120
        assert not set(old_paths).intersection(obj['export_path'] for obj in levels)
        before = _snapshot(source)
        _refuses(lambda: lod.generate_lods(levels[1], [], [0]))
        assert _snapshot(source) == before
        removed = levels[1].name
        levels = lod.generate_lods(source, [], [0])
        assert levels == [source] and tuple(source.users_collection) == (bpy.data.collections['LOD_0'],)
        assert bpy.data.objects.get(removed) is None
        assert len(source['omsi_lod_outputs']) == 0
        bpy.ops.object.select_all(action='DESELECT')
        source.select_set(True)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'one.cfg'
            addon.o3d_io.io_o3d_export.do_export(str(path), bpy.context, Matrix.Identity(4), True, 7)
            assert _scan(path) == ([0], [(0, source['export_path'])])
    finally:
        _clear()


def assert_lod_dependent_id_refusal(addon):
    # Native remove(do_unlink=True) silently nulls each dependency below unless
    # user_map is checked, including the source's extra nonmanifest reference.
    lod = _module(addon)
    for kind in ['parent', 'constraint', 'modifier', 'driver', 'custom', 'collection', 'scene', 'source']:
        _clear()
        source, rig = _fixture(addon)
        levels = lod.generate_lods(source, [.5], [.2, 0])
        old = levels[1]
        foreign = bpy.data.objects.new('Foreign dependant', None)
        bpy.context.scene.collection.objects.link(foreign)
        if kind == 'parent':
            foreign.parent = old
        elif kind == 'constraint':
            foreign.constraints.new('COPY_LOCATION').target = old
        elif kind == 'modifier':
            target = _triangle('Modifier dependant', bpy.context.scene.collection)
            target.modifiers.new('Boolean', 'BOOLEAN').object = old
        elif kind == 'driver':
            variable = foreign.driver_add('location', 0).driver.variables.new()
            variable.type = 'SINGLE_PROP'
            variable.targets[0].id = old
            variable.targets[0].data_path = 'location.x'
        elif kind == 'custom':
            foreign['target'] = old
        elif kind == 'collection':
            old.users_collection[0]['target'] = old
        elif kind == 'scene':
            bpy.context.scene['lod_target'] = old
        else:
            source.modifiers.new('Extra source dependency', 'BOOLEAN').object = old
        bpy.context.view_layer.update()
        before = _snapshot(source)
        try:
            _refuses(lambda: lod.generate_lods(source, [], [0]))
            assert _snapshot(source) == before, kind
            assert bpy.data.objects.get(old.name) == old
        finally:
            if 'lod_target' in bpy.context.scene:
                del bpy.context.scene['lod_target']
            _clear()
    # Structural links and multiple view layers are legitimate, not foreign.
    source, rig = _fixture(addon)
    levels = lod.generate_lods(source, [.5], [.2, 0])
    col = _collection('Extra structural link')
    col.objects.link(levels[1])
    bpy.context.scene.collection.objects.link(levels[1])
    layer = bpy.context.scene.view_layers.new('Extra LOD View Layer')
    bpy.context.view_layer.update()
    try:
        lod.generate_lods(source, [], [0])
    finally:
        bpy.context.scene.view_layers.remove(layer)
        _clear()


def assert_lod_transaction_rollback(addon):
    # Failure after real first decimation and a source move must preserve old
    # family IDs, exact data/material/collection/property/context sets.
    lod = _module(addon)
    for boundary in ['decimate', 'link', 'late-context']:
        _clear()
        source, rig = _fixture(addon)
        levels = lod.generate_lods(source, [.5, .25], [.2, .1, 0])
        material = source.material_slots[0].material
        material['cfg_data'] = [['[setbone]', 'Stale', '-2'], ['[smoothskin]'], ['[matl_alpha]', '2']]
        if boundary == 'late-context':
            source.shape_key_add(name='Basis')
            source.shape_key_add(name='Smile').value = 1
        before = _snapshot(source)
        old_props = [_props(obj) for obj in levels[1:]]
        owner = lod.mmd_rig if boundary == 'late-context' else lod
        name = {'decimate': '_apply_decimate', 'link': '_link_level',
                'late-context': '_restore_context'}[boundary]
        original = getattr(owner, name)
        calls = []
        def failing(*args):
            calls.append(args)
            if (boundary == 'late-context' and len(calls) == 1) or (boundary != 'late-context' and len(calls) == 2):
                raise RuntimeError('injected transaction failure')
            return original(*args)
        setattr(owner, name, failing)
        try:
            _refuses(lambda: lod.generate_lods(source, [.45, .2], [.4, .3, 0],
                                              remove_shape_keys=boundary == 'late-context'))
            assert len(calls) == 2
            assert _snapshot(source) == before, boundary
            assert [_props(obj) for obj in levels[1:]] == old_props
        finally:
            setattr(owner, name, original)
            _clear()


def assert_lod_basis_and_local_stack(addon):
    # Clearing keys alone loses edited Basis; applying nonfirst Decimate while
    # leaving SUBSURF would evaluate topology twice. World-space baking or
    # active morph/pose baking changes the literal local plane z2.
    _clear()
    source, rig = _fixture(addon, keys=True, topology=True)
    original_data = source.data
    lod = _module(addon)
    original_apply = lod._apply_decimate
    calls = []
    def failing(obj, ratio):
        calls.append(ratio)
        if len(calls) == 2:
            raise RuntimeError('injected keyed stage failure')
        return original_apply(obj, ratio)
    before = _snapshot(source)
    lod._apply_decimate = failing
    try:
        _refuses(lambda: lod.generate_lods(source, [.5, .25], [.2, .1, 0], remove_shape_keys=True))
        assert _snapshot(source) == before
        assert source.data == original_data and source.data.shape_keys.key_blocks['Smile'].value == 1
        assert all(v.co.z == 0 for v in source.data.vertices)
    finally:
        lod._apply_decimate = original_apply
    try:
        levels = lod.generate_lods(source, [.5, .25], [.2, .1, 0], remove_shape_keys=True)
        assert source.data != original_data and source.data.shape_keys is None
        assert source.modifiers.get('Once-only Subdivision') is not None
        assert all(obj.data.shape_keys is None for obj in levels)
        assert all(abs(v.co.z - 2) < 1e-5 for obj in levels for v in obj.data.vertices)
        assert all(all(m.type == 'ARMATURE' for m in obj.modifiers) for obj in levels[1:])
        # Mixed 72 quads + 144 triangles subdivide to 720 quads, or 1440
        # triangles. Independent .5/.25 must yield 720/360 triangles.
        for obj in levels[1:]:
            obj.data.calc_loop_triangles()
        counts = [len(obj.data.loop_triangles) for obj in levels[1:]]
        assert counts == [720, 360], counts
        assert counts[1] > counts[0] * .45, counts
        assert all(obj.data['custom_metadata'] == 'preserved' for obj in levels)
    finally:
        _clear()


def assert_lod_no_orphan_sanitized_material(addon):
    # Sanitizing before evaluated mesh conversion can leave a private copy
    # unused when new_from_object resolves an OBJECT-linked override itself.
    _clear()
    source, rig = _fixture(addon)
    stale = source.material_slots[0].material
    stale['cfg_data'] = [['[setbone]', 'Old', '-2'], ['[smoothskin]'], ['[matl_alpha]', '2']]
    source.material_slots[0].link = 'OBJECT'
    source.material_slots[0].material = stale
    before = set(bpy.data.materials)
    try:
        levels = _module(addon).generate_lods(source, [.5, .25], [.2, .1, 0])
        created = set(bpy.data.materials) - before
        assert all(material.users > 0 for material in created), [(m.name, m.users) for m in created]
        assert all(not any(list(block)[0] in {'[setbone]', '[smoothskin]'}
                           for block in obj.material_slots[0].material['cfg_data']) for obj in levels)
        assert list(stale['cfg_data'][0]) == ['[setbone]', 'Old', '-2']
    finally:
        _clear()


def assert_lod_broken_dependencies_and_bindings(addon):
    # An empty Armature pointer is a broken character dependency. Canonical
    # groups without a corresponding rig bone must not become new CFG bindings.
    _clear()
    source, rig = _fixture(addon)
    lod = _module(addon)
    source.modifiers[0].object = None
    before = _snapshot(source)
    try:
        _refuses(lambda: lod.generate_lods(source, [.5], [.2, 0]))
        assert _snapshot(source) == before
    finally:
        _clear()
    from smoke_character import _armature_with_bones
    source = _triangle('Main only', bpy.context.scene.collection)
    source.vertex_groups.new(name='Main').add([0, 1, 2], 1, 'REPLACE')
    source.vertex_groups.new(name='Head')
    rig = _armature_with_bones('Main rig', [('Main', (0, 0, 0), (0, 0, 1), None)])
    source.modifiers.new('Armature', 'ARMATURE').object = rig
    try:
        levels = lod.generate_lods(source, [], [0])
        blocks = [list(block) for block in source.data['cfg_data']]
        assert blocks == [['[setbone]', 'Main', '-11']], blocks
    finally:
        _clear()


def assert_lod_unsafe_contexts_and_collections(addon):
    lod = _module(addon)
    for kind in ['edit', 'prefix', 'shared-data', 'other-scene', 'unlinked-source',
                 'unlinked-target', 'other-scene-target', 'nested-lod-target',
                 'excluded-target', 'hidden-target', 'selected-old', 'corrupt-manifest']:
        _clear()
        source, rig = _fixture(addon)
        kwargs = {}
        other_scene = None
        if kind == 'edit':
            bpy.ops.object.mode_set(mode='EDIT')
        elif kind == 'prefix':
            kwargs['collection_prefix'] = 'Other_'
        elif kind == 'shared-data':
            external = bpy.data.objects.new('Shared base', source.data)
            bpy.context.scene.collection.objects.link(external)
        elif kind in {'other-scene', 'other-scene-target'}:
            other_scene = bpy.data.scenes.new('Other source scene')
            if kind == 'other-scene':
                other_scene.collection.objects.link(source)
            else:
                col = _collection('LOD_0.2')
                other_scene.collection.children.link(col)
        elif kind == 'unlinked-source':
            for col in tuple(source.users_collection):
                col.objects.unlink(source)
        elif kind == 'unlinked-target':
            bpy.data.collections.new('LOD_0.2')
        elif kind == 'nested-lod-target':
            _collection('LOD_0.2', _collection('LOD_0.3'))
        elif kind in {'excluded-target', 'hidden-target'}:
            col = _collection('LOD_0.2')
            if kind == 'excluded-target':
                bpy.context.view_layer.layer_collection.children[col.name].exclude = True
            else:
                col.hide_viewport = True
        else:
            levels = lod.generate_lods(source, [.5], [.2, 0])
            if kind == 'selected-old':
                levels[1].select_set(True)
            else:
                levels[1]['omsi_lod_owner'] = rig
        bpy.context.view_layer.update()
        before = _snapshot(source)
        try:
            try:
                _refuses(lambda: lod.generate_lods(source, [.4], [.2, 0], **kwargs))
            except AssertionError as error:
                raise AssertionError(kind) from error
            assert _snapshot(source) == before, kind
        finally:
            _clear()
            if other_scene is not None:
                bpy.data.scenes.remove(other_scene)


def assert_lod_rest_metadata_failure_cleanup(addon):
    # Evaluated new_from_object allocates a persistent mesh BEFORE custom
    # metadata is copied. A copy failure must still own and remove that mesh.
    _clear()
    source, rig = _fixture(addon)
    lod = _module(addon)
    original = lod._plain
    def fail_metadata(value):
        if value == 'preserved':
            raise RuntimeError('injected metadata copy failure')
        return original(value)
    before = _snapshot(source)
    lod._plain = fail_metadata
    try:
        _refuses(lambda: lod.generate_lods(source, [.5], [.2, 0]))
        assert _snapshot(source) == before
    finally:
        lod._plain = original
        _clear()


def assert_lod_private_key_cleanup(addon):
    # Mesh.copy creates a separate Key; shape_key_clear detaches it without
    # removing the Key datablock. Track exact IDs on both success and failure.
    lod = _module(addon)
    for fail in [True, False, True, False]:
        _clear()
        source, rig = _fixture(addon, keys=True)
        original_key = source.data.shape_keys
        keys_before = set(bpy.data.shape_keys)
        keys_after_success = keys_before - {original_key}
        before = _snapshot(source)
        original = lod._apply_decimate
        calls = []
        def fail_second(obj, ratio):
            calls.append(ratio)
            if len(calls) == 2:
                raise RuntimeError('injected second keyed decimation')
            return original(obj, ratio)
        try:
            if fail:
                lod._apply_decimate = fail_second
                _refuses(lambda: lod.generate_lods(source, [.5, .25], [.2, .1, 0], remove_shape_keys=True))
                assert _snapshot(source) == before
                assert set(bpy.data.shape_keys) == keys_before
            else:
                levels = lod.generate_lods(source, [.5, .25], [.2, .1, 0], remove_shape_keys=True)
                assert set(bpy.data.shape_keys) == keys_after_success
                assert all(obj.data.shape_keys is None for obj in levels)
                assert all(abs(vertex.co.z - 2) < 1e-5 for obj in levels for vertex in obj.data.vertices)
        finally:
            lod._apply_decimate = original
            _clear()


def assert_lod_foreign_key_consumers(addon):
    # Purging a Mesh implicitly deletes its Key even when a foreign custom or
    # driver reference consumes that Key. Refuse before any family mutation.
    lod = _module(addon)
    for old_output in [False, True]:
        for consumer in ['custom', 'driver']:
            _clear()
            source, rig = _fixture(addon, keys=not old_output)
            if old_output:
                victim = lod.generate_lods(source, [.5], [.2, 0])[1]
                victim.shape_key_add(name='Basis')
                victim.shape_key_add(name='Smile').value = 1
            else:
                victim = source
            key = victim.data.shape_keys
            foreign = bpy.data.objects.new('Foreign Key consumer', None)
            bpy.context.scene.collection.objects.link(foreign)
            if consumer == 'custom':
                foreign['key_dependency'] = key
                target = None
            else:
                variable = foreign.driver_add('location', 0).driver.variables.new()
                variable.type = 'SINGLE_PROP'
                target = variable.targets[0]
                target.id_type = 'KEY'
                target.id = key
                target.data_path = 'key_blocks["Smile"].value'
            before = _snapshot(source)
            try:
                _refuses(lambda: lod.generate_lods(source, [], [0], remove_shape_keys=True))
                assert _snapshot(source) == before
                assert victim.data.shape_keys == key
                assert (foreign['key_dependency'] if target is None else target.id) == key
            finally:
                _clear()
    # A retained external mesh user prevents old-data purge; its Key/foreign
    # consumer can safely remain while the old managed Object is removed.
    source, rig = _fixture(addon)
    victim = lod.generate_lods(source, [.5], [.2, 0])[1]
    victim.shape_key_add(name='Basis')
    victim.shape_key_add(name='Smile')
    key = victim.data.shape_keys
    external = bpy.data.objects.new('Shared keyed old mesh', victim.data)
    bpy.context.scene.collection.objects.link(external)
    external['key_dependency'] = key
    try:
        lod.generate_lods(source, [], [0])
        assert external.data.shape_keys == key and external['key_dependency'] == key
    finally:
        _clear()
    # Key-owned animation is outgoing data, not an incoming foreign consumer.
    # An ordinary Action must not prevent successful LODs.
    for old_output in [False, True]:
        source, rig = _fixture(addon, keys=not old_output)
        victim = lod.generate_lods(source, [.5], [.2, 0])[1] if old_output else source
        if old_output:
            victim.shape_key_add(name='Basis')
            victim.shape_key_add(name='Smile')
        key = victim.data.shape_keys
        key.key_blocks['Smile'].keyframe_insert(data_path='value', frame=1)
        action = key.animation_data.action
        try:
            lod.generate_lods(source, [], [0], remove_shape_keys=True)
            assert source.data.shape_keys is None
            assert action.name in bpy.data.actions
        finally:
            _clear()


def assert_cfg_unsupported_only_lod(addon):
    # An ARMATURE can make a factor bucket nonempty without emitting CFG data.
    # Preserve supported light/typed-empty output when filtering those buckets.
    _clear()
    col = _collection('LOD_0.8')
    rig = bpy.data.objects.new('Selected unsupported rig', bpy.data.armatures.new('Unsupported data'))
    col.objects.link(rig)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    try:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'supported.cfg'
            addon.o3d_io.io_o3d_export.do_export(str(path), bpy.context, Matrix.Identity(4), True, 7)
            assert _scan(path) == ([], []), path.read_text()
            light = bpy.data.objects.new('Supported light', bpy.data.lights.new('Point', 'POINT'))
            col.objects.link(light)
            light.select_set(True)
            empty = bpy.data.objects.new('Supported enhanced light', None)
            col.objects.link(empty)
            empty['type'] = '[light_enh]'
            for name, value in [('brightness_var', '1'), ('brightness', 1.0),
                                ('z_offset', 0.0), ('effect', 0), ('ramp_time', 0.0)]:
                empty[name] = value
            empty.select_set(True)
            addon.o3d_io.io_o3d_export.do_export(str(path), bpy.context, Matrix.Identity(4), True, 7)
            text = path.read_text()
            assert _scan(path) == ([.8], [])
            assert text.count('[interiorlight]') == 1 and text.count('[light_enh]') == 1, text
    finally:
        _clear()


CHECKS = [assert_cfg_lod_membership, assert_lod_generation_and_export, assert_lod_invalid_requests,
          assert_lod_regeneration_ownership, assert_lod_dependent_id_refusal,
          assert_lod_transaction_rollback, assert_lod_basis_and_local_stack,
          assert_lod_no_orphan_sanitized_material, assert_lod_broken_dependencies_and_bindings,
          assert_lod_unsafe_contexts_and_collections, assert_lod_rest_metadata_failure_cleanup,
          assert_lod_private_key_cleanup, assert_lod_foreign_key_consumers, assert_cfg_unsupported_only_lod]
