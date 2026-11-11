"""Transactional decimal-factor OMSI character LOD generation."""
from math import isfinite
from numbers import Real
from uuid import uuid4

import bpy
from mathutils.kdtree import KDTree

from . import mmd_rig
from .omsi_paths import unique_export_path

_SOURCE_ID = 'omsi_lod_source_id'
_OUTPUTS = 'omsi_lod_outputs'
_OWNER = 'omsi_lod_owner'
_LEVEL = 'omsi_lod_level'
_FAMILY_KEYS = (_SOURCE_ID, _OUTPUTS, _OWNER, _LEVEL)
_MISSING = object()


def _plain(value):
    if hasattr(value, 'to_dict'):
        return {key: _plain(item) for key, item in value.to_dict().items()}
    if hasattr(value, 'to_list'):
        return value.to_list()
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    return value


def _clear_family(obj):
    for key in _FAMILY_KEYS:
        if key in obj:
            del obj[key]


def _factor(collection):
    if not collection.name.startswith('LOD_'):
        return None
    try:
        value = float(collection.name[4:])
    except ValueError:
        return None
    return value if isfinite(value) and value >= 0 else None


def _scene_paths(scene):
    # A collection may have several parents. Keep every ancestor-factor path.
    paths = {}
    def visit(collection, ancestors, seen):
        if collection in seen:
            raise ValueError('cyclic collection hierarchy')
        own = _factor(collection)
        effective = ancestors | ({own} if own is not None else set())
        paths.setdefault(collection, set()).update(effective)
        for child in collection.children:
            visit(child, effective, seen | {collection})
    visit(scene.collection, set(), set())
    return paths


def _targets(factors, prefix):
    if prefix != 'LOD_':
        raise ValueError("collection_prefix must be 'LOD_' for CFG export")
    paths = _scene_paths(bpy.context.scene)
    visible = set()
    def visit_layer(layer, hidden=False):
        hidden = hidden or layer.exclude or layer.hide_viewport or layer.collection.hide_viewport
        if not hidden:
            visible.add(layer.collection)
        for child in layer.children:
            visit_layer(child, hidden)
    visit_layer(bpy.context.view_layer.layer_collection)
    targets = []
    for factor in factors:
        name = prefix + ('0' if factor == 0 else str(factor).removesuffix('.0'))
        col = bpy.data.collections.get(name)
        if col is not None:
            if (col.library or col.override_library or col not in paths or paths[col] != {factor}
                    or col not in visible):
                raise ValueError(f'Unsafe existing LOD target {name!r}')
            for scene in bpy.data.scenes:
                if scene != bpy.context.scene and col in _scene_paths(scene):
                    raise ValueError(f'LOD target {name!r} belongs to another scene')
        targets.append((name, col))
    return targets


def _owned_outputs(source):
    if _OWNER in source or _LEVEL in source:
        raise ValueError('A generated LOD cannot be used as a new source')
    manifest = source.get(_OUTPUTS)
    identity = source.get(_SOURCE_ID)
    if manifest is None:
        if identity is not None and not isinstance(identity, str):
            raise ValueError('Invalid LOD source identity')
        return []
    if not hasattr(manifest, 'items') or not isinstance(identity, str) or not identity:
        raise ValueError('Invalid LOD ownership manifest')
    entries = list(manifest.items())
    if len(entries) > 2 or {key for key, _ in entries} != {str(i + 1) for i in range(len(entries))}:
        raise ValueError('Invalid LOD manifest levels')
    owners, outputs = set(), []
    for key, obj in sorted(entries):
        if (not isinstance(obj, bpy.types.Object) or bpy.data.objects.get(obj.name) != obj
                or obj.type != 'MESH' or obj.get(_SOURCE_ID) != identity
                or type(obj.get(_LEVEL)) is not int or obj.get(_LEVEL) != int(key)):
            raise ValueError('Invalid LOD manifest object')
        owner = obj.get(_OWNER)
        if not isinstance(owner, bpy.types.Object):
            raise ValueError('Invalid LOD owner pointer')
        owners.add(owner)
        outputs.append(obj)
    if len(set(outputs)) != len(outputs) or len(owners) > 1:
        raise ValueError('Ambiguous LOD ownership')
    if owners and owners != {source}:
        # source.copy() copies the original manifest, whose outputs still point
        # to the original. Accept only a complete proven copied manifest.
        original = next(iter(owners))
        original_manifest = original.get(_OUTPUTS, {})
        if original.get(_SOURCE_ID) != identity or any(original_manifest.get(key) != obj for key, obj in entries):
            raise ValueError('Foreign or corrupt LOD manifest')
        return []
    return outputs


def _validate_old(source, outputs):
    bpy.context.view_layer.update()
    for obj in outputs:
        if obj.library or obj.override_library or obj.data.library:
            raise ValueError('Managed LOD is not locally editable')
        if obj == bpy.context.view_layer.objects.active or obj in bpy.context.selected_objects:
            raise ValueError('Deselect old generated LODs before regeneration')
        for scene in bpy.data.scenes:
            if scene != bpy.context.scene and obj.name in scene.objects:
                raise ValueError('Managed LOD belongs to another scene')
        count = sum(value == obj for value in source[_OUTPUTS].values())
        mmd_rig._validate_id_deletion(obj, source, count)


def _validate_mesh_key_deletion(data):
    key = data.shape_keys
    if key is not None:
        mmd_rig._validate_id_deletion(key, data, data.user_of_id(key))


def _apply_decimate(obj, ratio):
    modifier = obj.modifiers.new('OMSI LOD Decimate', 'DECIMATE')
    modifier.decimate_type = 'COLLAPSE'
    modifier.ratio = ratio
    flags = [(m, m.show_viewport, m.show_render) for m in obj.modifiers if m.type == 'ARMATURE']
    try:
        for armature, _, _ in flags:
            armature.show_viewport = armature.show_render = False
        bpy.context.view_layer.update()
        with bpy.context.temp_override(object=obj, active_object=obj, selected_objects=[obj],
                                       selected_editable_objects=[obj]):
            result = bpy.ops.object.modifier_apply(modifier=modifier.name)
        if 'FINISHED' not in result:
            raise RuntimeError('Decimate modifier did not finish')
    finally:
        for armature, viewport, render in flags:
            armature.show_viewport, armature.show_render = viewport, render


def _rest_mesh(work):
    flags = [(m, m.show_viewport, m.show_render) for m in work.modifiers if m.type == 'ARMATURE']
    try:
        for modifier, _, _ in flags:
            modifier.show_viewport = modifier.show_render = False
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        data = bpy.data.meshes.new_from_object(work.evaluated_get(depsgraph),
                    preserve_all_data_layers=True, depsgraph=depsgraph)
    finally:
        for modifier, viewport, render in flags:
            modifier.show_viewport, modifier.show_render = viewport, render
    try:
        for key in work.data.keys():
            data[key] = _plain(work.data[key])
    except Exception:
        bpy.data.meshes.remove(data)
        raise
    return data


def _normalize_weights(obj):
    donors = []
    for vertex in obj.data.vertices:
        weights = [(g.group, g.weight) for g in vertex.groups if isfinite(g.weight) and g.weight > 0]
        if weights:
            total = sum(weight for _, weight in weights)
            donors.append((vertex.co.copy(), [(group, weight / total) for group, weight in weights]))
    if not donors:
        return
    tree = KDTree(len(donors))
    for index, (coordinate, _) in enumerate(donors):
        tree.insert(coordinate, index)
    tree.balance()
    for vertex in obj.data.vertices:
        weights = [(g.group, g.weight) for g in vertex.groups if isfinite(g.weight) and g.weight > 0]
        if weights:
            total = sum(weight for _, weight in weights)
            weights = [(group, weight / total) for group, weight in weights]
        else:
            _, index, _ = tree.find(vertex.co)
            weights = donors[index][1]
        for group, weight in weights:
            obj.vertex_groups[group].add([vertex.index], weight, 'REPLACE')


def _link_level(collection, obj):
    collection.objects.link(obj)


def generate_lods(mesh, ratios, factors, collection_prefix='LOD_', remove_shape_keys=False):
    """Return source plus independent reduced levels; replace only proven owned IDs.

    Staging/link/property/data-swap failures roll back before old ID deletion.
    Native deletion is the final irreversible boundary; host failures during
    deletion cannot recreate removed Blender IDs. Old selected levels refuse.
    """
    ratios, factors = list(ratios), list(factors)
    if not 1 <= len(factors) <= 3 or len(ratios) != len(factors) - 1:
        raise ValueError('One to three factors require exactly one fewer ratios')
    if any(isinstance(v, bool) or not isinstance(v, Real) or not isfinite(v) or v < 0 for v in factors):
        raise ValueError('LOD factors must be finite nonnegative numbers')
    factors = [float(value) for value in factors]
    if factors[-1] != 0 or any(a <= b for a, b in zip(factors, factors[1:])):
        raise ValueError('LOD factors must strictly descend to zero')
    if any(isinstance(v, bool) or not isinstance(v, Real) or not isfinite(v) or not 0 < v < 1 for v in ratios):
        raise ValueError('LOD ratios must be finite numbers strictly between zero and one')
    if mesh is None or not isinstance(mesh, bpy.types.Object) or mesh.type != 'MESH':
        raise ValueError('mesh must be a mesh object')
    scene = bpy.context.scene
    if mesh.name not in scene.objects or mesh.name not in bpy.context.view_layer.objects:
        raise ValueError('Source must be in the active scene and view layer')
    if mesh.library or mesh.override_library or mesh.data.library or mesh.data.users != 1:
        raise ValueError('Source object and its mesh data must be local and unshared')
    if any(other != scene and mesh.name in other.objects for other in bpy.data.scenes):
        raise ValueError('Source belongs to another scene')
    if not mesh.data.vertices or not mesh.data.polygons:
        raise ValueError('Source must contain mesh faces')
    if mesh.data.shape_keys and not remove_shape_keys:
        raise ValueError('Source has shape keys; enable remove_shape_keys')
    # Explicitly refuse non-Object callers before mutation: temp_override does
    # not make modifier_apply valid while the caller remains in Edit mode.
    if bpy.context.mode != 'OBJECT':
        raise ValueError('Generate LODs in Object mode')
    mmd_rig._validate_world_transform(mesh)
    for modifier in mesh.modifiers:
        if modifier.type == 'ARMATURE':
            rig = modifier.object
            if rig is None or rig.type != 'ARMATURE' or rig.name not in scene.objects:
                raise ValueError('Source has a missing or inactive Armature dependency')
            mmd_rig._validate_world_transform(rig)
    old = _owned_outputs(mesh)
    _validate_old(mesh, old)
    # Removing an unused Mesh also deletes its Key, irrespective of foreign
    # Key consumers. Validate only data that final owned-object removal purges.
    if mesh.data.shape_keys:
        _validate_mesh_key_deletion(mesh.data)
    for data in {obj.data for obj in old}:
        if data.users == sum(obj.data == data for obj in old):
            _validate_mesh_key_deletion(data)
    targets = _targets(factors, collection_prefix)
    active, selected = bpy.context.view_layer.objects.active, tuple(bpy.context.selected_objects)
    original_data = mesh.data
    original_collections = tuple(mesh.users_collection)
    keys = _FAMILY_KEYS + ('export_path', 'skip_export')
    properties = {key: _plain(mesh[key]) if key in mesh else _MISSING for key in keys}
    original_cfg = _plain(original_data['cfg_data']) if 'cfg_data' in original_data else _MISSING
    slots = [(slot.link, slot.material) for slot in mesh.material_slots]
    created_objects, created_data, created_materials, created_collections = [], [], [], []
    stage = None
    committed = False
    try:
        stage = bpy.data.collections.new('OMSI LOD staging')
        created_collections.append(stage)
        scene.collection.children.link(stage)
        work = mesh.copy()
        created_objects.append(work)
        _clear_family(work)
        work.animation_data_clear()
        if 'skip_export' in work:
            del work['skip_export']
        work.data = mesh.data.copy()
        created_data.append(work.data)
        stage.objects.link(work)
        if work.data.shape_keys:
            private_key = work.data.shape_keys
            private_key_name = private_key.name
            try:
                mmd_rig._remove_shape_keys(work)
            finally:
                # Newer Blender clears the Key ID too; older versions leave it
                # orphaned. Remove only this surviving exact owned ID before
                # its Mesh; never scan/purge unrelated orphan keys.
                if bpy.data.shape_keys.get(private_key_name) == private_key:
                    mmd_rig._validate_id_deletion(
                        private_key, work.data, work.data.user_of_id(private_key))
                    bpy.data.batch_remove(ids=(private_key,))
        # The source's unbaked stack remains unchanged. The private base is
        # validated/sanitized; only cfg/material metadata is committed normally.
        rigs = [modifier.object for modifier in work.modifiers if modifier.type == 'ARMATURE']
        bone_names = ({name for rig in rigs for name in rig.data.bones.keys()} if rigs
                      else set(work.vertex_groups.keys()))
        mmd_rig.reconcile_character_bindings(work, bone_names, created_materials)
        work['export_path'] = unique_export_path(mesh, bpy.data.objects, suffix='LOD0')
        reduced = []
        if ratios:
            rest = _rest_mesh(work)
            created_data.append(rest)
            for index, ratio in enumerate(ratios, 1):
                obj = work.copy()
                created_objects.append(obj)
                _clear_family(obj)
                obj.name = f'{mesh.name}_LOD{index}'
                obj.data = rest.copy()
                created_data.append(obj.data)
                stage.objects.link(obj)
                for modifier in list(obj.modifiers):
                    if modifier.type != 'ARMATURE':
                        obj.modifiers.remove(modifier)
                _apply_decimate(obj, float(ratio))
                _normalize_weights(obj)
                mmd_rig.reconcile_character_bindings(obj, bone_names, created_materials)
                obj['export_path'] = unique_export_path(mesh, bpy.data.objects, suffix=f'LOD{index}')
                reduced.append(obj)
        identity = mesh.get(_SOURCE_ID)
        if not identity or any(obj != mesh and obj.get(_SOURCE_ID) == identity and _OWNER not in obj
                               for obj in bpy.data.objects if obj not in created_objects):
            identity = uuid4().hex
        # Complete ownership validation while copied manifests are cleared.
        _validate_old(mesh, old)
        levels = [mesh] + reduced
        for index, ((name, collection), obj) in enumerate(zip(targets, levels)):
            if collection is None:
                collection = bpy.data.collections.new(name)
                created_collections.append(collection)
                scene.collection.children.link(collection)
            if obj.name not in collection.objects:
                _link_level(collection, obj)
            for previous in tuple(obj.users_collection):
                if previous != collection:
                    previous.objects.unlink(obj)
        if original_data.shape_keys:
            mesh.data = work.data
        else:
            original_data['cfg_data'] = _plain(work.data['cfg_data'])
        for slot, prepared in zip(mesh.material_slots, work.material_slots):
            slot.material = prepared.material
        mesh['export_path'] = work['export_path']
        if 'skip_export' in mesh:
            del mesh['skip_export']
        mesh[_SOURCE_ID] = identity
        mesh[_OUTPUTS] = {str(index): obj for index, obj in enumerate(reduced, 1)}
        for index, obj in enumerate(reduced, 1):
            obj[_SOURCE_ID], obj[_OWNER], obj[_LEVEL] = identity, mesh, index
        # All fallible links/metadata/cleanup/context restoration precede old
        # deletion. Clear no foreign IDs and never purge global orphans.
        bpy.data.objects.remove(work, do_unlink=True)
        created_objects.remove(work)
        for data in list(created_data):
            if data.users == 0:
                bpy.data.meshes.remove(data)
                created_data.remove(data)
        bpy.data.collections.remove(stage)
        created_collections.remove(stage)
        mmd_rig._restore_context(active, selected, 'OBJECT')
        for obj in old:
            mmd_rig._validate_id_deletion(obj)
        committed = True
    except Exception:
        # Old objects are still alive at this point. Restore exact source ID,
        # direct memberships, family/path presence and shared metadata.
        mesh.data = original_data
        for collection in original_collections:
            if mesh.name not in collection.objects:
                collection.objects.link(mesh)
        for collection in tuple(mesh.users_collection):
            if collection not in original_collections:
                collection.objects.unlink(mesh)
        for key, value in properties.items():
            if value is _MISSING:
                if key in mesh:
                    del mesh[key]
            else:
                mesh[key] = value
        if original_cfg is _MISSING:
            if 'cfg_data' in original_data:
                del original_data['cfg_data']
        else:
            original_data['cfg_data'] = original_cfg
        for slot, (link, material) in zip(mesh.material_slots, slots):
            slot.link, slot.material = link, material
        raise
    finally:
        if not committed:
            for obj in reversed(created_objects):
                bpy.data.objects.remove(obj, do_unlink=True)
            for data in created_data:
                if data.users == 0:
                    bpy.data.meshes.remove(data)
            for material in created_materials:
                if material.users == 0:
                    bpy.data.materials.remove(material)
            for collection in reversed(created_collections):
                bpy.data.collections.remove(collection)
            mmd_rig._restore_context(active, selected, 'OBJECT')
    # Irreversible boundary. No fallible staging/validation/commit follows.
    old_data = {obj.data for obj in old}
    for obj in old:
        bpy.data.objects.remove(obj, do_unlink=True)
    for data in old_data | ({original_data} if original_data != mesh.data else set()):
        if data.users == 0:
            bpy.data.meshes.remove(data)
    return levels
