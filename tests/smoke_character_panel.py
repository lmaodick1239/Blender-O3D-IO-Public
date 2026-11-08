"""Task 5 sidebar integration: native operators, transactions and readiness."""
import importlib
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from smoke_character import _mmd_character, _mmd_material, _rig, _weight_snapshot
from smoke_lod import _clear, _triangle


def _panel(addon):
    return importlib.import_module(addon.__name__ + '.o3d_io.omsi_character_panel')


def _select(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def _snapshot():
    props = bpy.context.scene.omsi_character_data
    return (tuple((name, tuple(item.as_pointer() for item in getattr(bpy.data, name)))
                  for name in ('objects', 'meshes', 'armatures', 'materials', 'shape_keys',
                               'node_groups', 'images', 'actions', 'texts', 'collections')),
            bpy.context.view_layer.objects.active, tuple(bpy.context.selected_objects),
            bpy.context.object.mode if bpy.context.object else 'OBJECT',
            props.source_mesh, props.source_armature)


def _cancel(operation):
    # bpy.ops turns ERROR reports into RuntimeError; execute still returns CANCELLED.
    try:
        assert operation() == {'CANCELLED'}
    except RuntimeError as error:
        assert str(error).startswith('Error:'), error


def assert_character_preflight(addon):
    # Catches missing exact CP1252 validation and mutations of data/context/pointers.
    _clear()
    mesh, armature = _mmd_character()
    assert callable(getattr(_rig(addon), 'preflight', None)), 'Task 5 read-only preflight is missing'
    mat, *_ = _mmd_material(addon)
    mesh.data.materials.append(mat)
    image = mat.node_tree.nodes.new('ShaderNodeTexImage')
    image.image = bpy.data.images.new('Missing disk image', 1, 1)
    image.image.source = 'FILE'
    image.image.filepath = '//definitely-missing-character.png'
    _select(mesh)
    bpy.context.scene.omsi_character_data.source_mesh = None
    bpy.context.scene.omsi_character_data.source_armature = None
    before, weights = _snapshot(), _weight_snapshot(mesh)
    messages = _rig(addon).preflight(mesh)
    assert any(s == 'ERROR' and 'CP1252' in text for s, text in messages), messages
    for word in ('normal', 'helper', 'image', 'shape', 'MMD'):
        assert any(s == 'WARNING' and word.lower() in text.lower() for s, text in messages), (word, messages)
    assert _snapshot() == before and _weight_snapshot(mesh) == weights
    flags = [(m.show_viewport, m.show_render) for m in mesh.modifiers]
    try:
        assert bpy.ops.omsi.character_preflight() == {'FINISHED'}
    except RuntimeError as error:
        # Blender raises for genuine ERROR reports even from a read-only FINISHED operator.
        assert str(error).startswith('Error:'), error
    assert _snapshot() == before
    assert flags == [(m.show_viewport, m.show_render) for m in mesh.modifiers]
    assert any(s == 'ERROR' for s, _ in _rig(addon).preflight(None))
    _clear()


def assert_preflight_images_and_runtime(addon):
    # Catches false missing-image warnings for generated/packed data, blanket bone
    # caps, tie order changes, byte limits, and omitting strict serialized totals.
    _clear()
    mesh = _triangle('Readiness', bpy.context.scene.collection)
    mat, _, textures, *_ = _mmd_material(addon)
    mesh.data.materials.append(mat)
    textures['Base'].image.pack()
    for index in range(129):
        mesh.vertex_groups.new(name=f'Bone{index}').add([0, 1, 2], .001 if index < 127 else .5, 'REPLACE')
    messages = _rig(addon).preflight(mesh)
    assert not any(s == 'ERROR' for s, _ in messages), messages
    assert not any('missing' in text.lower() and 'image' in text.lower() for _, text in messages)
    assert any('unbound' in text.lower() for _, text in messages)
    mesh.vertex_groups[-1].add([0], .75, 'REPLACE')
    assert any(s == 'ERROR' and '128' in text for s, text in _rig(addon).preflight(mesh))
    # Blender truncates group names; inject only serialization preparation for
    # disk grammar cases RNA cannot represent, retaining the real strict helper.
    exporter = addon.o3d_io.io_o3d_export
    original = exporter.prepare_o3d_geometry
    try:
        for bones, phrase in (([('x' * 256, [(0, 1)])], '255'),
                              ([('Main', [(65536, 1)])], '65535'),
                              ([('Main', [(0, 1)])] * 65536, 'file bones'),
                              ([('Main', [(0, 1)] * 65536)], 'influences')):
            exporter.prepare_o3d_geometry = lambda *a, **k: {'verts': [(0,) * 8], 'tris': [], 'bones': bones}
            assert any(s == 'ERROR' and phrase in text for s, text in _rig(addon).preflight(mesh))
    finally:
        exporter.prepare_o3d_geometry = original
    _clear()
    from smoke_io import _make_wide_unique_uv_mesh
    data, _ = _make_wide_unique_uv_mesh('Preflight serialized total')
    mesh = bpy.data.objects.new('Preflight serialized total', data)
    bpy.context.scene.collection.objects.link(mesh)
    mesh.vertex_groups.new(name='Main').add([0], 1, 'REPLACE')
    assert any(s == 'ERROR' and '65535' in text for s, text in _rig(addon).preflight(mesh))
    _clear()


def assert_preflight_output_paths(addon):
    # Catches preflight ignoring shared path safety, inherited root slash
    # normalization, and case-insensitive collisions with another output.
    _clear()
    mesh = _triangle('Path readiness', bpy.context.scene.collection)
    for path in ('../escape.o3d', 'C:\\escape.o3d', '//host/share/escape.o3d'):
        mesh['export_path'] = path
        assert any(s == 'ERROR' and 'path' in text.lower() for s, text in _rig(addon).preflight(mesh))
    mesh['export_path'] = '/nested/Character.o3d'
    assert not any(s == 'ERROR' for s, _ in _rig(addon).preflight(mesh))
    other = _triangle('Other output', bpy.context.scene.collection)
    other['export_path'] = 'NESTED/character.o3d'
    assert any(s == 'ERROR' and 'collid' in text.lower() for s, text in _rig(addon).preflight(mesh))
    other['skip_export'] = True
    assert not any(s == 'ERROR' for s, _ in _rig(addon).preflight(mesh))
    _clear()


def assert_character_panel(addon):
    # Catches wrong defaults that alter real material scope, missing registration,
    # unsafe draw defaults and teardown that leaves operators or Scene RNA alive.
    panel = _panel(addon)
    props = bpy.context.scene.omsi_character_data
    assert props.max_influences == 4 and props.lod_count == 3
    assert tuple(round(x, 4) for x in props.lod_factors) == (.2, .1, 0)
    assert tuple(props.lod_ratios) == (.5, .25)
    assert props.remove_shape_keys and props.reset_sphere
    assert not props.keep_extra_bones and not props.delete_source_rig and not props.material_scope_all
    assert props.rig_mode == 'AUTO' and props.target_collection == 'OMSI_Converted'
    assert props.bl_rna.properties['lod_factors'].unit == 'NONE'
    for cls in panel.get_classes():
        assert cls.is_registered, cls
    _clear()
    mesh, armature = _mmd_character()
    _select(mesh)
    props.source_mesh = props.source_armature = None
    panel.fill_source_defaults(bpy.context)
    assert props.source_mesh == mesh and props.source_armature == armature
    _clear()


def assert_material_operator_copies(addon):
    # Catches modifying sources, duplicate material copies per slot, repeat churn,
    # failing to select the working mesh, and all-material opt-in not acting in place.
    _clear()
    props = bpy.context.scene.omsi_character_data
    props.source_mesh = props.source_armature = None
    mesh = _triangle('Material source', bpy.context.scene.collection)
    mat, shader, *_ = _mmd_material(addon)
    mesh.data.materials.append(mat)
    mesh.data.materials.append(mat)
    _select(mesh)
    original_data = mesh.data
    assert bpy.ops.omsi.reset_mmd_toon() == {'FINISHED'}
    working = bpy.context.object
    assert working != mesh and working.data != original_data and mesh.data == original_data
    assert shader.inputs['Toon Tex Fac'].default_value == 1
    assert working.material_slots[0].material == working.material_slots[1].material != mat
    private = working.material_slots[0].material
    assert _panel(addon).mmd_materials.mmd_nodes(private)[0].inputs['Sphere Tex Fac'].default_value == 0
    before = _snapshot()
    assert bpy.ops.omsi.reset_mmd_toon() == {'FINISHED'}
    assert _snapshot() == before
    assert bpy.ops.omsi.flatten_mmd_materials() == {'FINISHED'}
    flat = bpy.context.object
    assert flat != working and _panel(addon).mmd_materials.mmd_nodes(private)
    assert not _panel(addon).mmd_materials.mmd_nodes(flat.material_slots[0].material)
    before = _snapshot()
    assert bpy.ops.omsi.flatten_mmd_materials() == {'FINISHED'}
    assert _snapshot() == before
    props.material_scope_all = True
    objects = tuple(bpy.data.objects)
    assert bpy.ops.omsi.flatten_mmd_materials() == {'FINISHED'}
    assert not _panel(addon).mmd_materials.mmd_nodes(mat)
    assert mesh.data.materials[0] == mat and mesh.data.materials[1] == mat
    assert tuple(bpy.data.objects) == objects
    output = next(node for node in mat.node_tree.nodes
                  if node.bl_idname == 'ShaderNodeOutputMaterial' and node.is_active_output)
    principled = output.inputs['Surface'].links[0].from_node
    assert principled.bl_idname == 'ShaderNodeBsdfPrincipled'
    base = principled.inputs['Base Color'].links[0].from_node
    assert base.image is not None and base.inputs['Vector'].is_linked
    assert principled.inputs['Alpha'].links[0].from_node == base
    assert all(abs(value - want) < .001 for value, want in zip(mat.diffuse_color, (.2, .4, .6, .4)))
    assert addon.o3d_io.blender_compat.get_material_alpha_mode(mat) == 'BLEND'
    before = _snapshot()
    assert bpy.ops.omsi.flatten_mmd_materials() == {'FINISHED'}
    assert _snapshot() == before
    props.material_scope_all = False
    _clear()


def assert_material_operator_rollback(addon):
    # A failure after one private material changes must leave no staged IDs,
    # source graph edits, pointer defaults, selection or mode changes behind.
    _clear()
    panel = _panel(addon)
    props = bpy.context.scene.omsi_character_data
    props.source_mesh = props.source_armature = None
    mesh = _triangle('Rollback material', bpy.context.scene.collection)
    mats = [_mmd_material(addon)[0] for _ in range(2)]
    for mat in mats:
        mesh.data.materials.append(mat)
    _select(mesh)
    bpy.ops.object.mode_set(mode='EDIT')
    before = _snapshot()
    original = panel.mmd_materials.flatten_material
    calls = []
    def fail_second(material):
        calls.append(material)
        if len(calls) == 2:
            raise ValueError('injected material failure')
        return original(material)
    panel.mmd_materials.flatten_material = fail_second
    try:
        _cancel(lambda: bpy.ops.omsi.flatten_mmd_materials())
    finally:
        panel.mmd_materials.flatten_material = original
    assert _snapshot() == before
    assert all(panel.mmd_materials.mmd_nodes(mat) for mat in mats)
    bpy.ops.object.mode_set(mode='OBJECT')
    _clear()


def assert_material_commit_rollback(addon):
    # A late selection failure must clean copied Mesh and Key IDs as well as
    # materials, and restore original pointers/context after staging completes.
    _clear()
    panel = _panel(addon)
    props = bpy.context.scene.omsi_character_data
    props.source_mesh = props.source_armature = None
    mesh = _triangle('Keyed material rollback', bpy.context.scene.collection)
    mesh.shape_key_add(name='Basis')
    mesh.shape_key_add(name='Smile')
    mat, *_ = _mmd_material(addon)
    mesh.data.materials.append(mat)
    mesh.data['self'] = mesh.data
    mat['self'] = mat
    mat.node_tree['material'] = mat
    key = mesh.data.shape_keys
    key['self'] = key
    key['mesh'] = mesh.data
    mesh.data['key'] = key
    # Driver targets participate in native ID ownership as well as custom props.
    driver = key.driver_add('eval_time').driver
    target = driver.variables.new().targets[0]
    target.id_type = 'KEY'
    target.id = key
    target.data_path = '["probe"]'
    key['probe'] = 0.0
    _select(mesh)
    before = _snapshot()
    original = panel._select
    def fail_selection(*args):
        original(*args)
        raise ValueError('injected material commit failure')
    panel._select = fail_selection
    try:
        _cancel(lambda: bpy.ops.omsi.flatten_mmd_materials())
    finally:
        panel._select = original
    assert _snapshot() == before
    assert panel.mmd_materials.mmd_nodes(mat)
    assert mesh.data['self'] == mesh.data and mat['self'] == mat
    assert key['self'] == key and key['mesh'] == mesh.data and mesh.data['key'] == key
    assert target.id == key
    _clear()


def assert_material_source_lookup_rollback(addon):
    # Lookup refusal after real selection must not make a Scene pointer retain
    # private IDs or lose the original pointers, context and source references.
    panel = _panel(addon)
    for explicit_pointers in (False, True):
        _clear()
        props = bpy.context.scene.omsi_character_data
        mesh, armature = _mmd_character()
        mat, *_ = _mmd_material(addon)
        mesh.data.materials.append(mat)
        mesh.data['self'] = mesh.data
        mat['self'] = mat
        mat.node_tree['material'] = mat
        props.source_mesh, props.source_armature = ((mesh, armature) if explicit_pointers else (None, None))
        _select(mesh)
        bpy.ops.object.mode_set(mode='EDIT')
        before, state, weights = _snapshot(), _material_state(mat), _weight_snapshot(mesh)
        data = mesh.data
        original = panel.mmd_rig.find_mmd_source
        def fail_lookup(private):
            assert private != mesh and private.data != data
            assert bpy.context.object == private and tuple(bpy.context.selected_objects) == (private,)
            assert bpy.context.object.mode == 'OBJECT'
            raise ValueError('injected material source lookup failure')
        panel.mmd_rig.find_mmd_source = fail_lookup
        try:
            _cancel(lambda: bpy.ops.omsi.flatten_mmd_materials())
        finally:
            panel.mmd_rig.find_mmd_source = original
        assert _snapshot() == before, 'source lookup refusal leaked IDs or changed context/pointers'
        assert _material_state(mat) == state and _weight_snapshot(mesh) == weights
        assert mesh.data == data and data['self'] == data and mat['self'] == mat
        assert mat.node_tree['material'] == mat
        assert mesh.modifiers['Source Armature'].object == armature
        bpy.ops.object.mode_set(mode='OBJECT')
        props.source_mesh = props.source_armature = None
        _clear()


def _material_state(material):
    tree = material.node_tree
    return (material.as_pointer(), tree.as_pointer(), tuple(material.diffuse_color),
            material.get('o3d_alpha_mode'),
            tuple((node.as_pointer(), node.name, node.bl_idname, tuple(node.location),
                   tuple((socket.name, tuple(socket.default_value) if hasattr(socket.default_value, '__len__')
                          else socket.default_value) for socket in node.inputs
                         if hasattr(socket, 'default_value')), tuple(node.keys())) for node in tree.nodes),
            tuple((link.from_node.name, link.from_socket.identifier,
                   link.to_node.name, link.to_socket.identifier) for link in tree.links),
            tuple((name, getattr(material, name)) for name in ('surface_render_method',
                  'use_transparency_overlap', 'blend_method', 'shadow_method') if hasattr(material, name)),
            tree.nodes.active, getattr(material, 'use_nodes', True))


def assert_all_material_atomicity(addon):
    # Refusals during staging and in-place commit retain original Material/tree IDs,
    # existing nodes/graphs, properties, external references and exact inventories.
    panel = _panel(addon)
    for commit_failure, flatten in ((False, True), (True, True), (True, False)):
        _clear()
        props = bpy.context.scene.omsi_character_data
        props.material_scope_all = True
        mesh = _triangle('All material rollback', bpy.context.scene.collection)
        mats = [_mmd_material(addon)[0] for _ in range(2)]
        for mat in mats:
            mat['self'] = mat
            tree = mat.node_tree
            inactive = tree.nodes.new('ShaderNodeOutputMaterial')
            principled = tree.nodes.new('ShaderNodeBsdfPrincipled')
            principled.inputs['Base Color'].default_value = (.8, .1, .2, 1)
            tree.links.new(principled.outputs[0], inactive.inputs['Surface'])
            tree.nodes['Material Output'].is_active_output = True
            tree.nodes.active = principled
            mesh.data.materials.append(mat)
        bpy.context.scene['material_reference'] = mats[0]
        _select(mesh)
        before, states = _snapshot(), tuple(_material_state(mat) for mat in mats)
        owner = panel if commit_failure else panel.mmd_materials
        method = '_stage_material_edit' if commit_failure else 'flatten_material'
        original = getattr(owner, method)
        calls = []
        def fail_second(material, *args):
            calls.append(material)
            result = original(material, *args)
            if len(calls) == 2:
                raise ValueError('injected all-material failure')
            return result
        setattr(owner, method, fail_second)
        try:
            operation = bpy.ops.omsi.flatten_mmd_materials if flatten else bpy.ops.omsi.reset_mmd_toon
            _cancel(operation)
        finally:
            setattr(owner, method, original)
            props.material_scope_all = False
        assert tuple(_material_state(mat) for mat in mats) == states
        assert _snapshot() == before
        assert list(mesh.data.materials) == mats
        assert bpy.context.scene['material_reference'] == mats[0]
        assert all(mat['self'] == mat for mat in mats)
        del bpy.context.scene['material_reference']
        _clear()


def assert_all_material_reset_render_settings(addon):
    # A toon-only reset must preserve an existing alpha tag and customized
    # rendering, matching the low-level reset without replacing Material/nodes.
    _clear()
    panel = _panel(addon)
    props = bpy.context.scene.omsi_character_data
    mesh = _triangle('Reset render settings', bpy.context.scene.collection)
    mat, shader, *_ = _mmd_material(addon)
    mesh.data.materials.append(mat)
    addon.o3d_io.blender_compat.set_material_alpha_mode(mat, 'BLEND')
    mat.use_transparency_overlap = True
    reference = mat.copy()
    fields = ('surface_render_method', 'use_transparency_overlap', 'blend_method', 'shadow_method')
    render_before = tuple((name, getattr(mat, name)) for name in fields if hasattr(mat, name))
    nodes = tuple(mat.node_tree.nodes)
    tree = mat.node_tree
    _select(mesh)
    before = _snapshot()
    try:
        assert panel.mmd_materials.reset_toon([reference], True) == 1
        assert tuple((name, getattr(reference, name)) for name, _ in render_before) == render_before
        props.material_scope_all = True
        assert bpy.ops.omsi.reset_mmd_toon() == {'FINISHED'}
        assert _snapshot() == before
        assert mesh.data.materials[0] == mat and mat.node_tree == tree
        assert tuple(tree.nodes) == nodes and shader in tree.nodes.values()
        assert mat['o3d_alpha_mode'] == reference['o3d_alpha_mode'] == 'BLEND'
        assert mat.use_transparency_overlap is True
        assert tuple((name, getattr(mat, name)) for name, _ in render_before) == render_before
        expected = panel.mmd_materials.mmd_nodes(reference)[0]
        for name in ('Toon Tex Fac', 'Sphere Tex Fac'):
            assert shader.inputs[name].default_value == expected.inputs[name].default_value == 0
        links = lambda material: tuple((link.from_node.name, link.from_socket.identifier,
                                       link.to_node.name, link.to_socket.identifier)
                                      for link in material.node_tree.links)
        assert links(mat) == links(reference)
    finally:
        props.material_scope_all = False
        bpy.data.materials.remove(reference)
        _clear()


def assert_readiness_severity(addon):
    # A later warning must not obscure the actual ERROR result in the info line.
    panel = _panel(addon)
    original = panel.mmd_rig.preflight
    reports = []
    class Reporter:
        def report(self, severity, message):
            reports.append((severity, message))
    panel.mmd_rig.preflight = lambda mesh: [('ERROR', 'unsafe output'), ('WARNING', 'shape keys remain')]
    try:
        assert panel.CharacterPreflight.execute(Reporter(), bpy.context) == {'FINISHED'}
    finally:
        panel.mmd_rig.preflight = original
    assert any(severity == {'ERROR'} and 'unsafe output' in message for severity, message in reports)
    assert reports[-1][0] == {'ERROR'}


def assert_conversion_commit_rollback(addon):
    # Late UI failures must stay inside conversion, before optional rig deletion.
    panel = _panel(addon)
    for delete_source in (False, True):
        _clear()
        props = bpy.context.scene.omsi_character_data
        mesh, armature = _mmd_character()
        props.source_mesh, props.source_armature = mesh, armature
        props.delete_source_rig = delete_source
        _select(mesh)
        bpy.ops.object.mode_set(mode='EDIT')
        before, weights = _snapshot(), _weight_snapshot(mesh)
        original = panel._select
        def fail_selection(*args):
            original(*args)
            raise ValueError('injected conversion UI commit failure')
        panel._select = fail_selection
        try:
            _cancel(lambda: bpy.ops.omsi.convert_mmd_to_omsi())
        finally:
            panel._select = original
            props.delete_source_rig = False
        assert _snapshot() == before
        assert _weight_snapshot(mesh) == weights
        assert mesh.parent is None and mesh.modifiers['Source Armature'].object == armature
        bpy.ops.object.mode_set(mode='OBJECT')
        props.source_mesh = props.source_armature = None
        _clear()


def assert_conversion_and_lod_operators(addon):
    # Catches losing converted pointers, missing collection/options and wrong
    # count-to-ratios/factors slicing (including single-level final-zero behavior).
    _clear()
    props = bpy.context.scene.omsi_character_data
    props.source_mesh = props.source_armature = None
    mesh, armature = _mmd_character()
    _select(mesh)
    assert bpy.ops.omsi.convert_mmd_to_omsi() == {'FINISHED'}
    result = props.source_mesh
    assert result != mesh and result['mmd_converted']
    assert props.source_armature != armature and result.parent == props.source_armature
    assert bpy.context.object == result and tuple(bpy.context.selected_objects) == (result,)
    before = _snapshot()
    _cancel(lambda: bpy.ops.omsi.convert_mmd_to_omsi())
    assert _snapshot() == before
    for count, want in ((1, ['LOD_0']), (2, ['LOD_0.2', 'LOD_0']), (3, ['LOD_0.2', 'LOD_0.1', 'LOD_0'])):
        props.lod_count = count
        assert bpy.ops.omsi.generate_mesh_lods() == {'FINISHED'}
        outputs = [result, *result.get('omsi_lod_outputs', {}).values()]
        assert [obj.users_collection[0].name for obj in outputs] == want
    props.lod_factors = (1e-8, 1e-9, 0)
    assert bpy.ops.omsi.generate_mesh_lods() == {'FINISHED'}
    props.lod_factors = (.1, .2, 0)
    before = _snapshot()
    _cancel(lambda: bpy.ops.omsi.generate_mesh_lods())
    assert _snapshot() == before
    props.lod_factors = (.2, .1, 0)
    props.source_mesh = props.source_armature = None
    _clear()
    mesh, armature = _mmd_character()
    _select(mesh)
    props.source_mesh, props.source_armature = mesh, armature
    armature_name = armature.name
    props.delete_source_rig = True
    assert bpy.ops.omsi.convert_mmd_to_omsi() == {'FINISHED'}
    assert bpy.data.objects.get(armature_name) is None
    assert props.source_armature == props.source_mesh.parent
    props.delete_source_rig = False
    props.source_mesh = props.source_armature = None
    _clear()
    before = _snapshot()
    _cancel(lambda: bpy.ops.omsi.convert_mmd_to_omsi())
    assert _snapshot() == before


def assert_character_panel_unregistered(addon):
    assert not hasattr(bpy.types.Scene, 'omsi_character_data')
    for cls in _panel(addon).get_classes():
        assert not cls.is_registered, cls
    for name in ('reset_mmd_toon', 'flatten_mmd_materials', 'convert_mmd_to_omsi',
                 'generate_mesh_lods', 'character_preflight'):
        try:
            getattr(bpy.ops.omsi, name).get_rna_type()
        except (RuntimeError, KeyError):
            pass
        else:
            raise AssertionError(f'operator remained registered: {name}')


CHECKS = [assert_character_preflight, assert_preflight_images_and_runtime, assert_preflight_output_paths,
          assert_character_panel,
          assert_material_operator_copies, assert_material_operator_rollback,
          assert_material_commit_rollback, assert_material_source_lookup_rollback,
          assert_all_material_atomicity, assert_all_material_reset_render_settings,
          assert_readiness_severity, assert_conversion_commit_rollback,
          assert_conversion_and_lod_operators]

if __name__ == '__main__':
    from smoke_support import load_addon
    addon = load_addon()
    addon.register()
    for check in CHECKS:
        check(addon)
    addon.unregister()
    assert_character_panel_unregistered(addon)
    print('BLENDER_O3D_IO_CHARACTER_PANEL_OK', bpy.app.version_string)
