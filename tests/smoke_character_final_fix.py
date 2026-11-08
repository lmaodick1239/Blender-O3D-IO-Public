"""Two final integration regressions: ID-type guards and conversion Key ownership."""
import bpy

from smoke_character import _rig, _mmd_character
from smoke_character_fix_round_1 import _source_snapshot
from smoke_lod import _clear, _fixture, _module, _snapshot, _refuses


def assert_key_object_name_dependency_collision(addon):
    # Object and Key ID namespaces are independent. Structural Object allowances
    # must never excuse Collection/Scene custom references to a same-named Key.
    for kind in ['collection', 'scene']:
        _clear()
        source, rig = _fixture(addon, keys=True)
        key = source.data.shape_keys
        collision = bpy.data.objects.new(key.name, None)
        bpy.context.scene.collection.objects.link(collision)
        assert collision.name == key.name
        owner = collision.users_collection[0] if kind == 'collection' else bpy.context.scene
        if kind == 'scene':
            # Two view layers plus a direct root link would grant three false
            # structural references by name; match that count with real Key refs.
            layer = bpy.context.scene.view_layers.new('Collision layer')
            bpy.context.view_layer.update()
            for index in range(3):
                owner['key_dependency_' + str(index)] = key
        else:
            layer = None
            # Use an ordinary Collection, not the root's Scene structural link.
            collection = bpy.data.collections.new('Collision Collection')
            bpy.context.scene.collection.children.link(collection)
            collection.objects.link(collision)
            owner = collection
            owner['key_dependency_0'] = key
        before = _snapshot(source)
        keys = [name for name in owner.keys() if name.startswith('key_dependency_')]
        try:
            _refuses(lambda: _module(addon).generate_lods(source, [], [0], remove_shape_keys=True))
            assert _snapshot(source) == before
            assert all(owner[name] == key for name in keys)
            assert source.data.shape_keys == key
        finally:
            for name in keys:
                del owner[name]
            if layer is not None:
                bpy.context.scene.view_layers.remove(layer)
            _clear()


def assert_conversion_private_key_ownership(addon):
    # Conversion's Mesh.copy allocates a private Key. Removing shapes detaches
    # it, so owned cleanup is required on success, late failure and clear errors.
    rig = _rig(addon)
    for boundary in ['success', 'late-bindings', 'before-clear', 'after-clear']:
        _clear()
        mesh, source = _mmd_character()
        original_key = mesh.data.shape_keys
        for point in original_key.key_blocks['Basis'].data:
            point.co.z = 2
        for point in original_key.key_blocks['Smile'].data:
            point.co.z = 7
        original_key.key_blocks['Smile'].value = 1
        unrelated = bpy.data.objects.new('Unrelated Key user', None)
        bpy.context.scene.collection.objects.link(unrelated)
        unrelated['source_key'] = original_key
        bpy.ops.object.select_all(action='DESELECT')
        mesh.select_set(True)
        bpy.context.view_layer.objects.active = mesh
        before = _source_snapshot(mesh, source)
        keys_before = set(bpy.data.shape_keys)
        original_clear = rig._remove_shape_keys
        original_bind = rig.reconcile_character_bindings
        def fail_clear(obj):
            if boundary == 'before-clear':
                raise RuntimeError('injected before private clear')
            original_clear(obj)
            raise RuntimeError('injected after private clear')
        def fail_bind(*args, **kwargs):
            original_bind(*args, **kwargs)
            raise RuntimeError('injected after real bindings')
        if boundary in {'before-clear', 'after-clear'}:
            rig._remove_shape_keys = fail_clear
        elif boundary == 'late-bindings':
            rig.reconcile_character_bindings = fail_bind
        try:
            if boundary == 'success':
                result = rig.convert(mesh, source, rig.ConversionOptions())
                assert result.mesh.data.shape_keys is None
                assert all(abs(vertex.co.z - 2) < 1e-5 for vertex in result.mesh.data.vertices)
            else:
                _refuses(lambda: rig.convert(mesh, source, rig.ConversionOptions()))
                assert _source_snapshot(mesh, source) == before, boundary
            assert set(bpy.data.shape_keys) == keys_before, boundary
            assert mesh.data.shape_keys == original_key and unrelated['source_key'] == original_key
            assert original_key.key_blocks['Smile'].value == 1
            assert all(point.co.z == 2 for point in original_key.key_blocks['Basis'].data)
            assert all(point.co.z == 7 for point in original_key.key_blocks['Smile'].data)
        finally:
            rig._remove_shape_keys = original_clear
            rig.reconcile_character_bindings = original_bind
            _clear()


CHECKS = [assert_key_object_name_dependency_collision, assert_conversion_private_key_ownership]
