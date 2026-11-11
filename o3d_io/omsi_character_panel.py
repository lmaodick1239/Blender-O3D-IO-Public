"""OMSI character sidebar; low-level tools remain usable without the UI."""
import os
import tempfile

import bpy
from bpy.props import (BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty,
                       IntProperty, PointerProperty, StringProperty)
from bpy_extras.io_utils import ExportHelper

from . import mmd_materials, mmd_rig, mesh_lod, omsi_human
from .omsi_paths import safe_export_path, unique_export_path


def _mesh(self, obj):
    return obj.type == 'MESH'


def _armature(self, obj):
    return obj.type == 'ARMATURE'


class OMSICharacterProps(bpy.types.PropertyGroup):
    source_mesh: PointerProperty(name='Source Mesh', type=bpy.types.Object, poll=_mesh)
    source_armature: PointerProperty(name='Source Armature', type=bpy.types.Object, poll=_armature)
    template_armature: PointerProperty(name='Template Armature', type=bpy.types.Object, poll=_armature)
    rig_mode: EnumProperty(name='Rig Source', items=(
        ('AUTO', 'Auto from MMD joints', ''), ('TEMPLATE', 'Copy template', '')), default='AUTO')
    max_influences: IntProperty(name='Max Influences', min=1, max=8, default=4)
    remove_shape_keys: BoolProperty(name='Remove shape keys', default=True)
    keep_extra_bones: BoolProperty(name='Keep unmapped MMD bones as extras', default=False)
    delete_source_rig: BoolProperty(name='Delete source MMD armature', default=False)
    reset_sphere: BoolProperty(name='Also reset sphere factor', default=True)
    material_scope_all: BoolProperty(name='Apply to every material in the file', default=False)
    target_collection: StringProperty(name='Target Collection', default='OMSI_Converted')
    lod_count: IntProperty(name='LOD Count', min=1, max=3, default=3)
    lod_ratios: FloatVectorProperty(name='Reduced Ratios', size=2, default=(.5, .25))
    lod_factors: FloatVectorProperty(name='LOD Factors', size=3, default=(.2, .1, 0))


def _source_mesh(context):
    props = context.scene.omsi_character_data
    return props.source_mesh or (context.object if context.object and context.object.type == 'MESH' else
                                 next((obj for obj in context.selected_objects if obj.type == 'MESH'), None))


def fill_source_defaults(context):
    """Fill empty pointers at operator execution, never during panel drawing."""
    props = context.scene.omsi_character_data
    if props.source_mesh is None:
        props.source_mesh = _source_mesh(context)
    if props.source_armature is None and props.source_mesh is not None:
        props.source_armature = mmd_rig.find_mmd_source(props.source_mesh)[0]


def _select(context, objects, active):
    if context.object and context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    context.view_layer.objects.active = active


def _needs_material_change(material, flatten, reset_sphere):
    shaders = mmd_materials.mmd_nodes(material)
    if flatten:
        return bool(shaders)
    prefixes = ('Toon Tex', 'Sphere Tex') if reset_sphere else ('Toon Tex',)
    return any(socket.is_linked or (socket.name == prefix + ' Fac' and socket.default_value != 0)
               for shader in shaders for prefix in prefixes for socket in shader.inputs
               if socket.name.startswith(prefix))


def _remove_owned(ids):
    """Remove the exact private closure, including native self/driver references."""
    owned = set(ids)
    if not owned:
        return
    for target, users in bpy.data.user_map(subset=owned).items():
        # Material node trees are embedded IDs owned by their material.
        foreign = [user for user in users if user not in owned and
                   getattr(user, 'owner_id', None) not in owned]
        if foreign:
            raise ValueError(f'Private ID {target.name!r} acquired an external user')
    bpy.data.batch_remove(ids=owned)


def _value(value):
    return value[:] if hasattr(value, '__len__') and not isinstance(value, str) else value


_MATERIAL_FIELDS = ('diffuse_color', 'use_nodes', 'surface_render_method',
                    'use_transparency_overlap', 'blend_method', 'shadow_method')


def _material_journal(material):
    """Snapshot only state the two material helpers change; keep nodes alive."""
    tree = material.node_tree
    nodes = list(tree.nodes)
    inputs = [(socket, _value(socket.default_value)) for node in nodes for socket in node.inputs
              if hasattr(socket, 'default_value') and not socket.is_property_readonly('default_value')]
    markers = [(node, node.get('o3d_mmd_helper')) for node in nodes]
    outputs = [(node, node.is_active_output) for node in nodes if hasattr(node, 'is_active_output')]
    fields = {name: _value(getattr(material, name)) for name in _MATERIAL_FIELDS
              if hasattr(material, name)}
    return (material, nodes, inputs, markers, outputs, fields,
            material.get('o3d_alpha_mode'), tree.nodes.active,
            [(link.from_socket, link.to_socket) for link in tree.links])


def _restore_material(journal):
    material, nodes, inputs, markers, outputs, fields, alpha, active, links = journal
    tree = material.node_tree
    for node in list(tree.nodes):
        if node not in nodes:
            tree.nodes.remove(node)
    for name, value in fields.items():
        setattr(material, name, value)
    if alpha is None:
        if 'o3d_alpha_mode' in material:
            del material['o3d_alpha_mode']
    else:
        material['o3d_alpha_mode'] = alpha
    for socket, value in inputs:
        socket.default_value = value
    for node, marker in markers:
        if marker is None:
            if 'o3d_mmd_helper' in node:
                del node['o3d_mmd_helper']
        else:
            node['o3d_mmd_helper'] = marker
    for node, active_output in outputs:
        node.is_active_output = active_output
    tree.nodes.active = active
    tree.links.clear()
    for source, target in links:
        tree.links.new(source, target)


def _stage_material_edit(material, staged):
    """Apply the helpers' staged delta, deferring destruction of original nodes."""
    tree = material.node_tree
    originals = {node.name: node for node in tree.nodes}
    mapping = {}
    for node in staged.node_tree.nodes:
        target = originals.get(node.name)
        if target is None:
            # flatten_material creates only these native nodes. Do not serialize
            # arbitrary user graphs: unchanged user nodes retain their identities.
            if node.bl_idname not in {'ShaderNodeBsdfPrincipled', 'ShaderNodeOutputMaterial'}:
                raise ValueError('Unsupported node created by material conversion')
            target = tree.nodes.new(node.bl_idname)
            target.name, target.label = node.name, node.label
            target.location, target.width = node.location, node.width
        mapping[node.name] = target
        changed_inputs = {'Toon Tex Fac', 'Sphere Tex Fac'}
        if node.bl_idname == 'ShaderNodeBsdfPrincipled':
            changed_inputs = {'Base Color', 'Alpha'}
        for source, socket in zip(node.inputs, target.inputs):
            if source.name in changed_inputs and hasattr(source, 'default_value'):
                socket.default_value = source.default_value
        if 'o3d_mmd_helper' in node:
            target['o3d_mmd_helper'] = node['o3d_mmd_helper']
        if hasattr(node, 'is_active_output'):
            target.is_active_output = node.is_active_output
    tree.links.clear()
    for link in staged.node_tree.links:
        source, target = mapping[link.from_node.name], mapping[link.to_node.name]
        tree.links.new(source.outputs[list(link.from_node.outputs).index(link.from_socket)],
                       target.inputs[list(link.to_node.inputs).index(link.to_socket)])
    for name in _MATERIAL_FIELDS:
        if hasattr(staged, name) and getattr(material, name) != getattr(staged, name):
            setattr(material, name, getattr(staged, name))
    if 'o3d_alpha_mode' in staged:
        material['o3d_alpha_mode'] = staged['o3d_alpha_mode']
    tree.nodes.active = mapping.get(staged.node_tree.nodes.active.name) if staged.node_tree.nodes.active else None
    return [node for name, node in originals.items() if name not in mapping]


def _edit_all_materials(materials, apply):
    if any(mat.library or mat.override_library or not mat.is_editable for mat in materials):
        raise ValueError('All materials to convert must be local and editable')
    copies, journals = [], []
    try:
        for material in materials:
            private = material.copy()
            copies.append(private)
            apply(private)
        # Every helper has succeeded privately. Retain original nodes until all
        # reversible in-place edits pass, preserving Material IDs and ID users.
        removals = []
        for material, staged in zip(materials, copies):
            journals.append(_material_journal(material))
            removals.append((material.node_tree, _stage_material_edit(material, staged)))
        _remove_owned(copies)
        copies.clear()
    except Exception:
        for journal in reversed(journals):
            _restore_material(journal)
        raise
    finally:
        _remove_owned(copies)
    # Final boundary: only native removal of already-validated owned graph nodes.
    for tree, nodes in removals:
        for node in nodes:
            tree.nodes.remove(node)
    return len(materials)


def _edit_materials(context, flatten):
    props = context.scene.omsi_character_data
    objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
    if not objects and _source_mesh(context) is not None:
        objects = [_source_mesh(context)]
    if not props.material_scope_all and not objects:
        raise ValueError('Select a mesh for material conversion')
    materials = list(bpy.data.materials) if props.material_scope_all else list(dict.fromkeys(
        slot.material for obj in objects for slot in obj.material_slots if slot.material is not None))
    materials = [mat for mat in materials if _needs_material_change(mat, flatten, props.reset_sphere)]
    if not materials:
        return 0

    def apply(material):
        return (mmd_materials.flatten_material(material) if flatten else
                mmd_materials.reset_toon([material], props.reset_sphere))

    if props.material_scope_all:
        return _edit_all_materials(materials, apply)
    if any(obj.library or obj.override_library or obj.name not in context.view_layer.objects for obj in objects):
        raise ValueError('Material source meshes must be local and in the active view layer')
    copies, staged, data_copies, key_copies = {}, [], [], []
    active = context.view_layer.objects.active
    selected = list(context.selected_objects)
    mode = active.mode if active else 'OBJECT'
    try:
        if context.object and context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        for material in materials:
            private = material.copy()
            copies[material] = private
            apply(private)
        for obj in objects:
            if not any(slot.material in copies for slot in obj.material_slots):
                continue
            work = obj.copy()
            staged.append(work)
            work.data = obj.data.copy()
            data_copies.append(work.data)
            if work.data.shape_keys:
                key_copies.append(work.data.shape_keys)
            work.name = obj.name + ' Materials'
            work['export_path'] = unique_export_path(obj, bpy.data.objects, suffix='materials')
            # An independent material work copy is not a managed LOD family.
            mesh_lod._clear_family(work)
            for slot in work.material_slots:
                if slot.material in copies:
                    slot.material = copies[slot.material]
            for collection in obj.users_collection:
                collection.objects.link(work)
        _select(context, staged, staged[0])
        armature = mmd_rig.find_mmd_source(staged[0])[0]
        props.source_mesh, props.source_armature = staged[0], armature
        return len(copies)
    except Exception:
        # Unlink owned objects first, then remove the exact private dependency
        # closure together: self references must not keep copied IDs alive.
        for obj in staged:
            for collection in list(obj.users_collection):
                collection.objects.unlink(obj)
        # Blender 5.2 keeps unlinked bases until view-layer synchronization;
        # flush those before distinguishing real foreign users of private IDs.
        context.view_layer.update()
        _remove_owned([*staged, *data_copies, *key_copies, *copies.values()])
        mmd_rig._restore_context(active, selected, mode)
        raise


class _CharacterOperator:
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.omsi_character_data
        pointers = props.source_mesh, props.source_armature
        try:
            message = self.run(context)
        except ValueError as error:
            props.source_mesh, props.source_armature = pointers
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        except Exception:
            props.source_mesh, props.source_armature = pointers
            raise
        self.report({'INFO'}, message)
        return {'FINISHED'}


class ResetMMDToon(_CharacterOperator, bpy.types.Operator):
    """Disable missing toon and optional sphere inputs on private working copies"""
    bl_idname = 'omsi.reset_mmd_toon'
    bl_label = 'Reset MMD Toon Factor'

    def run(self, context):
        count = _edit_materials(context, False)
        return f'Reset toon factors on {count} material(s)'


class FlattenMMDMaterials(_CharacterOperator, bpy.types.Operator):
    """Flatten MMD shaders to exporter-readable Principled materials"""
    bl_idname = 'omsi.flatten_mmd_materials'
    bl_label = 'Flatten MMD Materials'

    def run(self, context):
        count = _edit_materials(context, True)
        return f'Flattened {count} material(s)'


class ConvertMMDToOMSI(_CharacterOperator, bpy.types.Operator):
    """Create a separate OMSI character mesh and rig"""
    bl_idname = 'omsi.convert_mmd_to_omsi'
    bl_label = 'Convert to OMSI Armature'

    def run(self, context):
        fill_source_defaults(context)
        props = context.scene.omsi_character_data
        options = mmd_rig.ConversionOptions(
            rig_mode=props.rig_mode, template_armature=props.template_armature,
            max_influences=props.max_influences, remove_shape_keys=props.remove_shape_keys,
            keep_extra_bones=props.keep_extra_bones, delete_source_rig=props.delete_source_rig,
            target_collection=props.target_collection)
        source_armature = props.source_armature
        if options.delete_source_rig:
            # This UI-owned reference must not defeat conservative ID-user checks.
            # execute restores it if conversion refuses or staging fails.
            props.source_armature = None
        def complete(result):
            # The converter calls this before source deletion, so UI failures
            # still roll back outputs while execute can restore live pointers.
            props.source_mesh, props.source_armature = result.mesh, result.armature
            _select(context, [result.mesh], result.mesh)
        result = mmd_rig.convert(props.source_mesh, source_armature, options, on_complete=complete)
        return f'Converted {result.vertices} vertices to {len(result.bones)} bones'


class GenerateMeshLODs(_CharacterOperator, bpy.types.Operator):
    """Generate validated independent decimal-factor character LODs"""
    bl_idname = 'omsi.generate_mesh_lods'
    bl_label = 'Generate LODs'

    def run(self, context):
        fill_source_defaults(context)
        props = context.scene.omsi_character_data
        factors = [float(format(value, '.7g')) for value in props.lod_factors[:props.lod_count]]
        factors[-1] = 0
        levels = mesh_lod.generate_lods(props.source_mesh,
            props.lod_ratios[:props.lod_count - 1], factors,
            remove_shape_keys=props.remove_shape_keys)
        return f'Generated {len(levels)} total LOD level(s)'


class CharacterPreflight(bpy.types.Operator):
    """Report strict character export readiness without changing the scene"""
    bl_idname = 'omsi.character_preflight'
    bl_label = 'Check Export Readiness'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        messages = mmd_rig.preflight(_source_mesh(context))
        for severity, message in messages:
            self.report({severity}, message)
        if messages:
            worst = max((severity for severity, _ in messages),
                        key={'INFO': 0, 'WARNING': 1, 'ERROR': 2}.__getitem__)
            self.report({worst}, f'Export readiness: {worst.lower()} ({len(messages)} findings)')
        return {'FINISHED'}


class VIEW3D_PT_omsi_character(bpy.types.Panel):
    bl_label = 'OMSI Character Tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'OMSI'

    def draw(self, context):
        self.layout.label(text='MMD to OMSI character workflow')


class VIEW3D_PT_omsi_character_materials(bpy.types.Panel):
    bl_label = 'MMD Materials'
    bl_parent_id = 'VIEW3D_PT_omsi_character'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'OMSI'

    def draw(self, context):
        layout, props = self.layout, context.scene.omsi_character_data
        layout.prop(props, 'reset_sphere')
        layout.prop(props, 'material_scope_all')
        layout.operator('omsi.reset_mmd_toon')
        layout.operator('omsi.flatten_mmd_materials')


class VIEW3D_PT_omsi_character_convert(bpy.types.Panel):
    bl_label = 'Convert to OMSI Armature'
    bl_parent_id = 'VIEW3D_PT_omsi_character'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'OMSI'

    def draw(self, context):
        layout, props = self.layout, context.scene.omsi_character_data
        for name in ('source_mesh', 'source_armature', 'rig_mode'):
            layout.prop(props, name)
        if props.rig_mode == 'TEMPLATE':
            layout.prop(props, 'template_armature')
        for name in ('max_influences', 'remove_shape_keys', 'keep_extra_bones',
                     'delete_source_rig', 'target_collection'):
            layout.prop(props, name)
        layout.operator('omsi.convert_mmd_to_omsi')


class VIEW3D_PT_omsi_character_lods(bpy.types.Panel):
    bl_order = 30
    bl_label = 'Mesh LODs'
    bl_parent_id = 'VIEW3D_PT_omsi_character'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'OMSI'

    def draw(self, context):
        layout, props = self.layout, context.scene.omsi_character_data
        layout.prop(props, 'lod_count')
        for index in range(props.lod_count - 1):
            layout.prop(props, 'lod_ratios', index=index, text=f'Reduced Ratio {index + 1}')
        for index in range(props.lod_count - 1):
            layout.prop(props, 'lod_factors', index=index, text=f'LOD Factor {index + 1}')
        layout.label(text='Final LOD factor: 0')
        layout.operator('omsi.generate_mesh_lods')
        layout.operator('omsi.character_preflight')


def _human_changed(self, context):
    self.status = 'Settings changed; refresh/check again'


class OMSIHumanSettings(bpy.types.PropertyGroup):
    voice: StringProperty(name='Voice', default='M2', update=_human_changed)
    mass_kg: FloatProperty(name='Mass (kg)', default=70, update=_human_changed)
    seat_height: FloatProperty(name='Seat Height', default=.9, update=_human_changed)
    feetdist: FloatProperty(name='Feet Distance', default=.04, update=_human_changed)
    use_height_override: BoolProperty(name='Override Height', update=_human_changed)
    height_override: FloatProperty(name='Height', default=1.8, update=_human_changed)
    walk_params: FloatVectorProperty(name='Walking Parameters', size=5,
        default=(1.4, 80, 1, 1, 0), update=_human_changed)
    show_walking: BoolProperty(name='Advanced Walking Parameters')
    show_landmarks: BoolProperty(name='Landmark Overrides')
    confirm_stale: BoolProperty(name='Use Stale Source Landmarks',
        description='Explicitly accept captured neck/finger points after rest edits; overrides are safer',
        update=_human_changed)
    scale: FloatProperty(name='Export Scale', default=1, update=_human_changed)
    selection_only: BoolProperty(name='Selection Only', default=True, update=_human_changed)
    export_custom_normals: BoolProperty(name='Custom Normals', default=True, update=_human_changed)
    o3d_version: EnumProperty(name='O3D Version', default='7', items=(
        ('7', '7 (OMSI 2)', ''), ('3', '3', ''), ('1', '1 (Legacy)', '')), update=_human_changed)
    status: StringProperty(default='Not measured; refresh/check before export')
    errors: StringProperty()
    warnings: StringProperty()
    measured_height: FloatProperty()
    has_measurement: BoolProperty()
    measured_landmarks: StringProperty()


_HUMAN_LANDMARKS = ('hip', 'knee', 'waist', 'shoulder', 'elbow', 'neck', 'hand', 'finger')
for _name in _HUMAN_LANDMARKS:
    OMSIHumanSettings.__annotations__['use_' + _name + '_override'] = BoolProperty(
        name='Override ' + _name.title(), update=_human_changed)
    OMSIHumanSettings.__annotations__[_name + '_override'] = FloatVectorProperty(
        name=_name.title() + (' Y/Z' if _name in ('waist', 'neck') else ' X/Y/Z'),
        size=2 if _name in ('waist', 'neck') else 3, update=_human_changed)


def _human_target(context):
    """Resolve existing source pointers without filling them or guessing another rig."""
    props = context.scene.omsi_character_data
    mesh, target = props.source_mesh, props.source_armature
    if target is None:
        obj = mesh if mesh is not None else context.object
        if obj is not None and obj.type == 'ARMATURE':
            target = obj
        elif obj is not None and obj.type == 'MESH':
            rigs = omsi_human._mesh_rigs(obj)
            if len(rigs) == 1:
                target = next(iter(rigs))
    if target is None or target.type != 'ARMATURE' or target.name not in context.scene.objects:
        raise ValueError('Choose a compatible target in the existing Source Mesh/Armature fields')
    if mesh is not None and omsi_human._mesh_rigs(mesh) != {target}:
        raise ValueError('Source Mesh is not bound exclusively to the target armature')
    if set(mmd_rig.CANONICAL_NAMES) - set(target.data.bones.keys()):
        raise ValueError(f'{target.name}: not a compatible canonical OMSI target; convert the source first')
    if target.library or target.override_library or not target.is_editable:
        raise ValueError(f'{target.name}: human settings require a local editable target')
    return target


def _human_values(settings):
    values = {name: getattr(settings, name) for name in
              ('voice', 'mass_kg', 'seat_height', 'feetdist', 'walk_params')}
    overrides = {name: tuple(getattr(settings, name + '_override')) for name in _HUMAN_LANDMARKS
                 if getattr(settings, 'use_' + name + '_override')}
    if settings.use_height_override:
        overrides['height'] = settings.height_override
    return values, overrides


def _human_inputs(context):
    target = _human_target(context)
    settings = target.omsi_human_settings
    meshes = omsi_human.human_meshes(context, target, selection_only=settings.selection_only)
    # Match the backend refusal before any readiness/refresh evaluation.
    for obj in (context.view_layer.objects.active, target, *meshes):
        if obj is not None and obj.type in {'MESH', 'ARMATURE'} and obj.mode == 'EDIT':
            raise ValueError(f'{obj.name}: switch to Object Mode before human export; pending edits are unsupported')
    values, overrides = _human_values(settings)
    return target, settings, meshes, values, overrides


def _human_scope_warnings(context):
    helpers = [obj.name for obj in context.selected_objects
               if obj.rigid_body or obj.rigid_body_constraint or 'skip_export' in obj]
    return ['Excluded selected helpers: ' + ', '.join(helpers)] if helpers else []


def _cache_human(settings, result, status):
    settings.errors = '\n'.join(result['errors'])
    settings.warnings = '\n'.join(result['warnings'])
    settings.has_measurement = result['height'] is not None
    if settings.has_measurement:
        settings.measured_height = result['height']
    settings.measured_landmarks = '\n'.join(
        f"{name.title()}: " + ', '.join(format(value, '.5g') for value in point)
        for name, point in result['landmarks'].items())
    settings.status = status


def _human_failure(context, error):
    # Never write cached findings onto a fallback/source rig after target refusal.
    try:
        settings = _human_target(context).omsi_human_settings
    except ValueError:
        return
    settings.errors = str(error)
    settings.status = 'Human export needs attention'


class RefreshHumanMeasurements(bpy.types.Operator):
    """Read rest geometry explicitly, preserving every user override"""
    bl_idname = 'omsi.refresh_human_measurements'
    bl_label = 'Refresh Measurements'

    def execute(self, context):
        context.window.cursor_set('WAIT')
        try:
            target, settings, meshes, values, overrides = _human_inputs(context)
            result = omsi_human.measure_human(target, meshes, overrides=overrides,
                scale=settings.scale, context=context, confirm_stale=settings.confirm_stale)
            result['warnings'].extend(_human_scope_warnings(context))
            _cache_human(settings, result, 'Measurements need attention' if result['errors'] else 'Measurements refreshed')
            self.report({'WARNING'} if result['errors'] else {'INFO'}, settings.status)
            return {'FINISHED'}
        except (ValueError, TypeError, RuntimeError) as error:
            _human_failure(context, error)
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        finally:
            context.window.cursor_set('DEFAULT')


class HumanPreflight(bpy.types.Operator):
    """Check human inputs before choosing the final destination"""
    bl_idname = 'omsi.human_preflight'
    bl_label = 'Check Export Readiness'

    def execute(self, context):
        context.window.cursor_set('WAIT')
        try:
            target, settings, meshes, values, overrides = _human_inputs(context)
            # No destination has been chosen yet. Reuse the complete reviewed
            # preparation against a disposable root, without creating model files.
            with tempfile.TemporaryDirectory(prefix='omsi-human-readiness-') as root:
                reserved = {os.path.relpath(safe_export_path(root,
                                obj.get('export_path', obj.name + '.o3d')), root).split(os.sep)[0].casefold()
                            for obj in meshes}
                stem = '__readiness__'
                while stem + '.hum' in reserved or stem + '.cfg' in reserved:
                    stem += '_'
                result = omsi_human.export_human(os.path.join(root, stem + '.hum'),
                    context, target, meshes, settings=values, overrides=overrides,
                    scale=settings.scale, confirm_stale=settings.confirm_stale,
                    o3d_version=int(settings.o3d_version),
                    export_custom_normals=settings.export_custom_normals, preflight_only=True)
            result['measurements']['warnings'].extend(_human_scope_warnings(context))
            _cache_human(settings, result['measurements'],
                'Readiness passed; chosen destination is revalidated on export')
            self.report({'INFO'}, settings.status)
            return {'FINISHED'}
        except (ValueError, TypeError, RuntimeError, OSError) as error:
            _human_failure(context, error)
            self.report({'ERROR'}, 'Human readiness refused: ' + str(error))
            return {'CANCELLED'}
        finally:
            context.window.cursor_set('DEFAULT')


class ExportHuman(bpy.types.Operator, ExportHelper):
    """Write the sibling HUM/CFG/O3D set using the shared human backend"""
    bl_idname = 'omsi.export_human'
    bl_label = 'Export Human'
    filename_ext = '.hum'
    filter_glob: StringProperty(default='*.hum', options={'HIDDEN'})
    overwrite: BoolProperty(name='Overwrite Entire Generated File Set', default=False, options={'SKIP_SAVE'},
        description='Consent to replace any existing HUM, sibling CFG and referenced O3D files')

    def invoke(self, context, event):
        self.overwrite = False
        try:
            _human_target(context)
        except ValueError as error:
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        return ExportHelper.invoke(self, context, event)

    def draw(self, context):
        self.layout.prop(self, 'overwrite')
        self.layout.label(text='Consent covers HUM + sibling CFG + all O3D files')
        self.layout.label(text='Export settings belong to the target in Character Tools')

    def execute(self, context):
        context.window.cursor_set('WAIT')
        try:
            target, settings, meshes, values, overrides = _human_inputs(context)
            result = omsi_human.export_human(self.filepath, context, target, meshes,
                settings=values, overrides=overrides, scale=settings.scale,
                overwrite=self.overwrite, confirm_stale=settings.confirm_stale,
                o3d_version=int(settings.o3d_version), export_custom_normals=settings.export_custom_normals)
            settings.errors = ''
            settings.warnings = '\n'.join(result['warnings'] + _human_scope_warnings(context))
            settings.status = 'Exported: ' + result['hum_path']
            self.report({'INFO'}, settings.status)
            return {'FINISHED'}
        except (ValueError, TypeError, RuntimeError) as error:
            _human_failure(context, error)
            self.report({'ERROR'}, 'Human export refused: ' + str(error))
            return {'CANCELLED'}
        except OSError as error:
            _human_failure(context, error)
            self.report({'ERROR'}, 'Human export I/O failure (partial model files may remain): ' + str(error))
            return {'CANCELLED'}
        finally:
            context.window.cursor_set('DEFAULT')


class VIEW3D_PT_omsi_character_human(bpy.types.Panel):
    bl_label = 'Human Configuration & Export'
    bl_parent_id = 'VIEW3D_PT_omsi_character'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'OMSI'
    bl_order = 40

    def draw(self, context):
        layout = self.layout
        try:
            target = _human_target(context)
        except ValueError as error:
            layout.label(text=str(error), icon='ERROR')
            row = layout.column()
            row.enabled = False
            for action in ('refresh_human_measurements', 'human_preflight', 'export_human'):
                row.operator('omsi.' + action)
            return
        settings = target.omsi_human_settings
        layout.label(text='Target: ' + target.name, icon='ARMATURE_DATA')
        for name in ('voice', 'mass_kg', 'seat_height', 'feetdist', 'use_height_override'):
            layout.prop(settings, name)
        if settings.use_height_override:
            layout.prop(settings, 'height_override')
        layout.operator('omsi.refresh_human_measurements')
        layout.label(text=settings.status)
        if settings.has_measurement:
            layout.label(text=f'Last measured height: {settings.measured_height:.5g}')
        layout.label(text='Cached feedback; recheck after rest/mesh edits')
        for message in settings.errors.splitlines():
            layout.label(text=message, icon='ERROR')
        for message in settings.warnings.splitlines():
            layout.label(text=message, icon='INFO')
        layout.prop(settings, 'show_walking', icon='TRIA_DOWN' if settings.show_walking else 'TRIA_RIGHT', emboss=False)
        if settings.show_walking:
            for index in range(5):
                layout.prop(settings, 'walk_params', index=index, text=f'Walk Parameter {index + 1}')
        layout.prop(settings, 'show_landmarks', icon='TRIA_DOWN' if settings.show_landmarks else 'TRIA_RIGHT', emboss=False)
        if settings.show_landmarks:
            layout.label(text='Final scaled file coordinates; paired X must be positive')
            for name in _HUMAN_LANDMARKS:
                layout.prop(settings, 'use_' + name + '_override')
                if getattr(settings, 'use_' + name + '_override'):
                    layout.prop(settings, name + '_override')
            layout.prop(settings, 'confirm_stale')
            for message in settings.measured_landmarks.splitlines():
                layout.label(text=message)
        for name in ('scale', 'selection_only', 'export_custom_normals', 'o3d_version'):
            layout.prop(settings, name)
        layout.operator('omsi.human_preflight')
        layout.operator('omsi.export_human')


def get_classes():
    return (OMSICharacterProps, OMSIHumanSettings, ResetMMDToon, FlattenMMDMaterials, ConvertMMDToOMSI,
            GenerateMeshLODs, CharacterPreflight, RefreshHumanMeasurements, HumanPreflight, ExportHuman,
            VIEW3D_PT_omsi_character, VIEW3D_PT_omsi_character_materials, VIEW3D_PT_omsi_character_convert,
            VIEW3D_PT_omsi_character_lods, VIEW3D_PT_omsi_character_human)


def register():
    bpy.types.Scene.omsi_character_data = PointerProperty(type=OMSICharacterProps)
    bpy.types.Object.omsi_human_settings = PointerProperty(type=OMSIHumanSettings)


def unregister():
    if hasattr(bpy.types.Object, 'omsi_human_settings'):
        del bpy.types.Object.omsi_human_settings
    if hasattr(bpy.types.Scene, 'omsi_character_data'):
        del bpy.types.Scene.omsi_character_data
