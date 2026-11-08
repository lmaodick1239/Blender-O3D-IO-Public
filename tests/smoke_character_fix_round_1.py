"""Real Blender regressions for the six confirmed Task3 review findings."""
from pathlib import Path
import tempfile

import bpy
from mathutils import Matrix

from smoke_character import _rig, _mmd_character, _armature_with_bones, _weight_snapshot, _remove_objects
from smoke_character_repair import _counts, _refuses


def _properties(value):
    if isinstance(value, bpy.types.ID):
        return value.as_pointer()
    if hasattr(value, "items"):
        return tuple((key, _properties(item)) for key, item in value.items())
    if isinstance(value, (str, int, float, bool, type(None))):
        return repr(value)
    return tuple(_properties(item) for item in value)


def _source_snapshot(mesh, source):
    """Include source keys, properties, bindings, texts and caller context."""
    return (
        _counts(), repr(_weight_snapshot(mesh)),
        (mesh.data.shape_keys.as_pointer(),
         tuple((key.name, key.value, tuple(tuple(point.co) for point in key.data))
               for key in mesh.data.shape_keys.key_blocks)) if mesh.data.shape_keys else None,
        _properties(dict(mesh.items())), _properties(dict(mesh.data.items())),
        tuple((slot.link, slot.material.as_pointer() if slot.material else None,
               _properties(dict(slot.material.items())) if slot.material else None) for slot in mesh.material_slots),
        tuple((mod.name, mod.type, mod.show_viewport, mod.show_render,
               getattr(mod, "vertex_group", None),
               getattr(mod, "object", None).as_pointer() if getattr(mod, "object", None) else None)
              for mod in mesh.modifiers),
        tuple((bone.name, tuple(bone.head_local), tuple(bone.tail_local)) for bone in source.data.bones),
        tuple((text.name, text.as_string()) for text in bpy.data.texts),
        bpy.context.view_layer.objects.active, tuple(bpy.context.selected_objects), mesh.mode,
    )


def _edit_context(mesh):
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    bpy.context.view_layer.objects.active = mesh
    bpy.ops.object.mode_set(mode="EDIT")


def _object_mode():
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")


def assert_deletion_external_id_users(addon):
    """Deleting a rig/root must not null drivers or any extra incoming ID reference."""
    rig = _rig(addon)
    cases = ("foreign_driver", "foreign_custom", "mesh_driver", "mesh_custom", "mesh_hook",
             "scene_custom", "collection_custom", "material_custom", "root_driver", "root_custom",
             "root_source_custom")
    for case in cases:
        mesh, source = _mmd_character()
        root = bpy.data.objects.new("Dependency MMD root", None)
        root["mmd_type"] = "ROOT"
        bpy.context.scene.collection.objects.link(root)
        source.parent = root
        mesh.parent = source
        other = bpy.data.objects.new("External dependency", None)
        bpy.context.scene.collection.objects.link(other)
        target = root if case.startswith("root_") else source
        owner = (mesh if case.startswith("mesh_") else source if case == "root_source_custom"
                 else bpy.context.scene if case == "scene_custom"
                 else mesh.data.materials[0] if case == "material_custom" else other)
        collection = None
        if case == "collection_custom":
            collection = bpy.data.collections.new("Structural plus extra ref")
            bpy.context.scene.collection.children.link(collection)
            collection.objects.link(source)
            owner = collection
        is_driver = case.endswith("driver")
        if is_driver:
            curve = owner.driver_add("location", 0)
            variable = curve.driver.variables.new()
            variable.type = "SINGLE_PROP"
            variable.targets[0].id = target
            variable.targets[0].data_path = "location.x"
        elif case == "mesh_hook":
            owner.modifiers.new("Extra unapproved rig target", "HOOK").object = target
        else:
            owner["task3_dependency"] = target
        _edit_context(mesh)
        before = _source_snapshot(mesh, source)
        try:
            _refuses(lambda: rig.convert(mesh, source, rig.ConversionOptions(delete_source_rig=True)), "depend")
            assert _source_snapshot(mesh, source) == before, case
            actual_target = (variable.targets[0].id if is_driver else owner.modifiers[-1].object
                             if case == "mesh_hook" else owner["task3_dependency"])
            assert actual_target == target, case
        finally:
            _object_mode()
            if not is_driver and "task3_dependency" in owner:
                del owner["task3_dependency"]
            _remove_objects(mesh, source, root, other)
            if collection:
                bpy.data.collections.remove(collection)

    # Ordinary collections/view layers, opted-in mesh parent + armature links,
    # and an unrelated shared armature DATA user remain legitimate.
    mesh, source = _mmd_character()
    root = bpy.data.objects.new("Clean MMD root", None)
    root["mmd_type"] = "ROOT"
    bpy.context.scene.collection.objects.link(root)
    source.parent, mesh.parent = root, source
    collection = bpy.data.collections.new("Legitimate rig membership")
    bpy.context.scene.collection.children.link(collection)
    collection.objects.link(source)
    layer = bpy.context.scene.view_layers.new("Dependency second layer")
    shared = bpy.data.objects.new("Shared armature data", source.data)
    bpy.context.scene.collection.objects.link(shared)
    bpy.context.view_layer.update()
    result = None
    source_name, root_name = source.name, root.name
    try:
        result = rig.convert(mesh, source, rig.ConversionOptions(delete_source_rig=True))
        assert bpy.data.objects.get(source_name) is None
        assert bpy.data.objects.get(root_name) is None
        assert shared.data is not None
    finally:
        _remove_objects(mesh, shared, root, result.mesh if result else None, result.armature if result else None)
        bpy.context.scene.view_layers.remove(layer)
        bpy.data.collections.remove(collection)


def _textured_material(name, texture):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    image = bpy.data.images.new(name + " image", 1, 1)
    image.filepath = "//texture/" + texture
    node = material.node_tree.nodes.new("ShaderNodeTexImage")
    node.image = image
    material.node_tree.links.new(node.outputs["Color"], material.node_tree.nodes.get("Principled BSDF").inputs["Base Color"])
    return material, image


def assert_textured_object_material_cfg(addon):
    """CFG and O3D consume actual OBJECT slots, including shared and empty slots."""
    rig = _rig(addon)
    mesh, source = _mmd_character()
    underlying, underlying_image = _textured_material("Underlying stale data", "stale-data.bmp")
    override, override_image = _textured_material("Actual object override", "actual-object.bmp")
    for material in (underlying, override):
        material["cfg_data"] = [["[setbone]", "Main", "-2"], ["[smoothskin]"], ["[matl_noZwrite]"]]
        material["unchanged"] = "source material"
    mesh.data.materials[0] = underlying
    mesh.material_slots[0].link = "OBJECT"
    mesh.material_slots[0].material = override
    mesh.data.materials.append(underlying)
    mesh.material_slots[1].link = "OBJECT"
    mesh.material_slots[1].material = override
    mesh.data.polygons[-1].material_index = 1
    snapshot = _source_snapshot(mesh, source)
    source_materials = [_properties(dict(mat.items())) for mat in (underlying, override)]
    result = None
    try:
        result = rig.convert(mesh, source, rig.ConversionOptions(max_influences=1))
        assert result.mesh.material_slots[0].material == result.mesh.material_slots[1].material
        assert result.mesh.material_slots[0].material != override
        assert result.mesh.data.materials[0] == underlying
        with tempfile.TemporaryDirectory(prefix="task3-textured-slots-") as temporary:
            root = Path(temporary)
            bpy.ops.object.select_all(action="DESELECT")
            result.mesh.select_set(True)
            path = root / "model.cfg"
            addon.o3d_io.io_o3d_export.do_export(str(path), bpy.context, Matrix.Identity(4), True, 7)
            text = path.read_text(encoding="utf-8")
            assert text.count("[setbone]\nMain\n-11\n") == 1, text
            assert "[setbone]\nMain\n-2\n" not in text, text
            assert "[smoothskin]" not in text, text
            assert "[matl]\nactual-object.bmp\n0\n" in text, text
            assert "[matl]\nactual-object.bmp\n1\n" in text, text
            assert "stale-data.bmp" not in text, text
            # Empty material slots must remain harmless to both real writers.
            result.mesh.data.materials.append(None)
            addon.o3d_io.io_o3d_export.do_export(str(path), bpy.context, Matrix.Identity(4), True, 7)
            assert result.mesh.material_slots[2].material is None
            parsed = addon.o3d_io.o3dconvert.import_o3d((root / result.mesh["export_path"]).read_bytes())
            assert [material[-1] for material in parsed[3]] == ["actual-object.bmp", "actual-object.bmp", ""]
            influences = {}
            for _, entries in parsed[4]:
                for index, _ in entries:
                    influences[index] = influences.get(index, 0) + 1
            assert set(influences.values()) == {1}
        assert [_properties(dict(mat.items())) for mat in (underlying, override)] == source_materials
        assert repr(_weight_snapshot(mesh)) == snapshot[1]
        assert mesh.material_slots[0].material == override and mesh.data.materials[0] == underlying
    finally:
        _remove_objects(mesh, source, result.mesh if result else None, result.armature if result else None)
        for image in (underlying_image, override_image):
            bpy.data.images.remove(image)


def assert_pre_v3_section_count_preservation(addon):
    """u16 section count overflow refuses before truncating/creating any output."""
    exporter = addon.o3d_io.io_o3d_export
    verts = [[0, 0, 0, 0, 0, 1, 0, 0]] * 65535
    geometry = {"verts": verts, "tris": [[0, 1, 2, 0]] * 65535, "bones": []}
    assert exporter.validate_o3d_geometry(geometry, 2) is False
    for section in ("verts", "tris"):
        invalid = dict(geometry)
        invalid[section] = geometry[section] + [geometry[section][0]]
        _refuses(lambda: exporter.validate_o3d_geometry(invalid, 2), "65535")
        assert exporter.validate_o3d_geometry(invalid, 3) is False

    # Real evaluated/exported repeated triangles reproduce low-index count overflow.
    for count in (65535, 65536):
        data = bpy.data.meshes.new("v2 triangle count")
        data.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)] * count)
        obj = bpy.data.objects.new("v2 triangle count", data)
        bpy.context.scene.collection.objects.link(obj)
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        try:
            with tempfile.TemporaryDirectory(prefix="task3-v2-count-") as temporary:
                root = Path(temporary)
                existing, fresh = root / "existing.o3d", root / "new.o3d"
                existing.write_bytes(b"keep existing bytes")
                if count == 65535:
                    exporter.do_export(str(existing), bpy.context, Matrix.Identity(4), True, 2)
                    parsed = addon.o3d_io.o3dconvert.import_o3d(existing.read_bytes())
                    assert len(parsed[2]) == 65535
                else:
                    for path in (existing, fresh):
                        _refuses(lambda: exporter.do_export(str(path), bpy.context, Matrix.Identity(4), True, 2), "65535")
                    assert existing.read_bytes() == b"keep existing bytes"
                    assert not fresh.exists()
        finally:
            _remove_objects(obj)

    # Real serialized vertex count: 65535 succeeds, one extra corner refuses.
    for count in (65535, 65536):
        data = bpy.data.meshes.new("v2 vertex count")
        faces = [(index, index + 1, index + 2) for index in range(0, 65535, 3)]
        if count == 65536:
            faces.append((65534, 65533, 65535))
        data.from_pydata([(float(index), float(index % 2), 0) for index in range(count)], [], faces)
        obj = bpy.data.objects.new("v2 vertex count", data)
        bpy.context.scene.collection.objects.link(obj)
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        try:
            with tempfile.TemporaryDirectory(prefix="task3-v2-vertices-") as temporary:
                root = Path(temporary)
                existing, fresh = root / "existing.o3d", root / "new.o3d"
                existing.write_bytes(b"keep vertex count overflow")
                if count == 65535:
                    exporter.do_export(str(existing), bpy.context, Matrix.Identity(4), True, 2)
                    assert len(addon.o3d_io.o3dconvert.import_o3d(existing.read_bytes())[1]) == 65535
                else:
                    for path in (existing, fresh):
                        _refuses(lambda: exporter.do_export(str(path), bpy.context, Matrix.Identity(4), True, 2), "65535")
                    assert existing.read_bytes() == b"keep vertex count overflow"
                    assert not fresh.exists()
        finally:
            _remove_objects(obj)

    # Materials remain u16 in ALL versions, independent of long geometry headers.
    data = bpy.data.meshes.new("Material section guard")
    data.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    obj = bpy.data.objects.new("Material section guard", data)
    bpy.context.scene.collection.objects.link(obj)
    try:
        with tempfile.TemporaryDirectory(prefix="task3-material-count-") as temporary:
            path = Path(temporary) / "existing.o3d"
            path.write_bytes(b"preserve material overflow")
            for version in (2, 7):
                with exporter.prepared_export_mesh(obj) as (evaluated, prepared, transform):
                    _refuses(lambda: exporter.export_mesh(str(path), bpy.context, evaluated, prepared,
                             transform, [None] * 65536, version, True), "65535")
                assert path.read_bytes() == b"preserve material overflow"
    finally:
        _remove_objects(obj)


def _serialized_triangle_count(addon, mesh, path):
    # Japanese source names intentionally cannot serialize as bones. Export real
    # evaluated geometry with its transient weights removed, leaving source intact.
    exporter = addon.o3d_io.io_o3d_export
    with exporter.prepared_export_mesh(mesh) as (evaluated, prepared, transform):
        import bmesh
        bm = bmesh.new()
        try:
            bm.from_mesh(prepared)
            deform = bm.verts.layers.deform.active
            if deform is not None:
                bm.verts.layers.deform.remove(deform)
            bm.to_mesh(prepared)
        finally:
            bm.free()
        exporter.export_mesh(str(path), bpy.context, evaluated, prepared, transform,
                             evaluated.material_slots, 7, True)
    return len(addon.o3d_io.o3dconvert.import_o3d(path.read_bytes())[2])


def assert_group_modifier_refusal(addon):
    """An affected MASK refuses before staging instead of silently changing geometry."""
    rig = _rig(addon)
    data = bpy.data.meshes.new("Mask source square")
    data.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [], [(0, 1, 2), (0, 2, 3)])
    mesh = bpy.data.objects.new("Mask source square", data)
    bpy.context.scene.collection.objects.link(mesh)
    mesh.vertex_groups.new(name="上半身").add([0, 1, 2], 1, "REPLACE")
    mesh.vertex_groups.new(name="頭").add([3], 1, "REPLACE")
    source = _armature_with_bones("Mask source rig", [("上半身", (0, 0, 0), (0, 0, 1), None)])
    mesh.modifiers.new("Source rig", "ARMATURE").object = source
    mask = mesh.modifiers.new("Japanese membership mask", "MASK")
    mask.vertex_group = "上半身"
    result = None
    try:
        with tempfile.TemporaryDirectory(prefix="task3-group-modifier-") as temporary:
            path = Path(temporary) / "source.o3d"
            assert _serialized_triangle_count(addon, mesh, path) == 1
            _edit_context(mesh)
            before = _source_snapshot(mesh, source)
            _refuses(lambda: rig.convert(mesh, source, rig.ConversionOptions()), "apply")
            assert _source_snapshot(mesh, source) == before
            _object_mode()
            assert _serialized_triangle_count(addon, mesh, path) == 1
            # Render-only modifiers can be enabled later: also refuse.
            mask.show_viewport, mask.show_render = False, True
            before = _source_snapshot(mesh, source)
            _refuses(lambda: rig.convert(mesh, source, rig.ConversionOptions()), "apply")
            assert _source_snapshot(mesh, source) == before
            # Disabled in BOTH channels is retained dormant; no evaluation changes.
            mask.show_render = False
            result = rig.convert(mesh, source, rig.ConversionOptions())
            retained = result.mesh.modifiers["Japanese membership mask"]
            assert not retained.show_viewport and not retained.show_render
            assert retained.vertex_group == "上半身"
            assert _serialized_triangle_count(addon, result.mesh, Path(temporary) / "disabled.o3d") == 2
    finally:
        _object_mode()
        _remove_objects(mesh, source, result.mesh if result else None, result.armature if result else None)

    # Group-independent ARRAY/SUBSURF still evaluate through the shared strict helper.
    mesh, source = _mmd_character()
    array = mesh.modifiers.new("Supported array", "ARRAY")
    array.count = 2
    result = None
    try:
        result = rig.convert(mesh, source, rig.ConversionOptions())
        with tempfile.TemporaryDirectory(prefix="task3-array-supported-") as temporary:
            assert _serialized_triangle_count(addon, result.mesh, Path(temporary) / "array.o3d") == 22
    finally:
        _remove_objects(mesh, source, result.mesh if result else None, result.armature if result else None)


def assert_resolved_export_path_containment(addon):
    """Directory/file symlinks cannot redirect a relative export outside its root."""
    from smoke_support import create_source_object
    obj = create_source_object(addon)
    try:
        with tempfile.TemporaryDirectory(prefix="task3-resolved-path-") as temporary:
            base = Path(temporary)
            root, outside = base / "chosen", base / "outside"
            root.mkdir()
            outside.mkdir()
            existing = outside / "existing.o3d"
            existing.write_bytes(b"outside stays unchanged")
            try:
                (root / "linked").symlink_to(outside, target_is_directory=True)
                (root / "file.o3d").symlink_to(existing)
                (base / "chosen-alias").symlink_to(root, target_is_directory=True)
            except (OSError, NotImplementedError):
                print("SKIP export symlink check: symlinks unavailable")
                return
            for relative in ("linked/existing.o3d", "linked/new.o3d", "file.o3d"):
                obj["export_path"] = relative
                _refuses(lambda: addon.o3d_io.io_o3d_export.do_export(
                    str(root / "model.cfg"), bpy.context, Matrix.Identity(4), True, 7), "escapes")
                assert existing.read_bytes() == b"outside stays unchanged"
                assert not (outside / "new.o3d").exists()
                assert not (root / "model.cfg").exists()
            obj["export_path"] = r"\normal\inside.o3d"
            addon.o3d_io.io_o3d_export.do_export(str(base / "chosen-alias" / "model.cfg"),
                                               bpy.context, Matrix.Identity(4), True, 7)
            assert (root / "normal" / "inside.o3d").is_file()
    finally:
        _remove_objects(obj)


def assert_nonfinite_rig_preflight(addon):
    """All supplied world matrices/segments refuse NaN/Inf/collapse without source edits."""
    rig = _rig(addon)
    for owner_kind in ("source", "template", "mesh"):
        for invalid in (float("nan"), float("inf"), -float("inf"), "singular", "collapsed", "overflow"):
            mesh, source = _mmd_character()
            template = _armature_with_bones("Finite template", [("Main", (0, 0, 0), (0, 0, 1), None)])
            owner = {"source": source, "template": template, "mesh": mesh}[owner_kind]
            transform = Matrix.Identity(4)
            if invalid == "singular":
                transform[2][2] = 0
            elif invalid == "overflow":
                if owner_kind == "mesh":
                    _remove_objects(mesh, source, template)
                    continue
                # Finite endpoints/determinant, but segment distance overflows
                # mathutils float32: proximity must never consume this segment.
                transform = Matrix.Diagonal((1, 1, 1e20, 1))
            elif invalid == "collapsed":
                if owner_kind == "mesh":
                    _remove_objects(mesh, source, template)
                    continue
                # Finite, invertible transform whose float32 world endpoints coincide.
                transform.translation = (1e20, 1e20, 1e20)
            else:
                transform[0][3] = invalid
            _edit_context(mesh)
            owner.matrix_world = transform
            before = _source_snapshot(mesh, source)
            options = rig.ConversionOptions(rig_mode="TEMPLATE", template_armature=template)
            try:
                _refuses(lambda: rig.convert(mesh, source, options))
                assert _source_snapshot(mesh, source) == before, (owner_kind, invalid)
            finally:
                _object_mode()
                _remove_objects(mesh, source, template)
    # Source validation is also required for AUTO, before anatomical fallbacks.
    mesh, source = _mmd_character()
    source.matrix_world[1][3] = float("nan")
    try:
        before = _source_snapshot(mesh, source)
        _refuses(lambda: rig.convert(mesh, source, rig.ConversionOptions()), "finite")
        assert _source_snapshot(mesh, source) == before
    finally:
        _remove_objects(mesh, source)


CHECKS = (
    assert_deletion_external_id_users,
    assert_textured_object_material_cfg,
    assert_pre_v3_section_count_preservation,
    assert_group_modifier_refusal,
    assert_resolved_export_path_containment,
    assert_nonfinite_rig_preflight,
)
