"""Reviewed Task3 regressions, split from material/mapping smoke fixtures."""
import importlib
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import tempfile

import bpy
from mathutils import Matrix, Vector

from smoke_character import (_rig, _mmd_character, _armature_with_bones,
                             _weighted_mesh, _weight_snapshot, _remove_objects)


def _counts():
    return tuple(frozenset(item.as_pointer() for item in getattr(bpy.data, kind))
                 for kind in ("objects", "meshes", "armatures", "materials", "texts", "collections", "shape_keys"))


def _refuses(call, fragment=None):
    try:
        call()
    except ValueError as error:
        if fragment:
            assert fragment.lower() in str(error).lower(), str(error)
    else:
        raise AssertionError("invalid conversion accepted")


def _close(actual, expected):
    assert (Vector(actual) - Vector(expected)).length < 1e-5, (tuple(actual), tuple(expected))


def assert_conversion_input_guards(addon):
    """Invalid keys/rigs/transforms refuse before staging any datablock."""
    rig = _rig(addon)
    mesh, source = _mmd_character()
    empty = _armature_with_bones("Empty source", [])
    template = _armature_with_bones("Template guards", [("Main", (0, 0, 0), (0, 0, 1), None)])
    try:
        cases = [(mesh, source, rig.ConversionOptions(remove_shape_keys=False), "shape"),
                 (mesh, empty, rig.ConversionOptions(), "bones"),
                 (mesh, source, rig.ConversionOptions(rig_mode="TEMPLATE", template_armature=mesh), "armature"),
                 (mesh, source, rig.ConversionOptions(rig_mode="TEMPLATE", template_armature=empty), "bones")]
        for obj, arm, options, message in cases:
            before = _counts()
            _refuses(lambda: rig.convert(obj, arm, options), message)
            assert _counts() == before
        template.matrix_world = Matrix.Diagonal((1, 1, 0, 1))
        before = _counts()
        _refuses(lambda: rig.convert(mesh, source, rig.ConversionOptions(
            rig_mode="TEMPLATE", template_armature=template)), "singular")
        assert _counts() == before
        bare = _weighted_mesh("Empty conversion mesh", [], [])
        try:
            before = _counts()
            _refuses(lambda: rig.convert(bare, source, rig.ConversionOptions()), "vertices")
            assert _counts() == before
        finally:
            _remove_objects(bare)
    finally:
        _remove_objects(mesh, source, empty, template)


def assert_source_detection_evidence(addon):
    """A modifier identifies a generic source; MMD root chains work without it."""
    rig = _rig(addon)
    arm = _armature_with_bones("Generic rig", [("Main", (0, 0, 0), (0, 0, 1), None)])
    mesh = _weighted_mesh("Generic mesh", [(0, 0, 0)], [("Main", [(0, 1)])])
    root = bpy.data.objects.new("Arbitrary root label", None)
    bridge = bpy.data.objects.new("MMD intermediate", None)
    bpy.context.scene.collection.objects.link(root)
    bpy.context.scene.collection.objects.link(bridge)
    root["mmd_type"] = "ROOT"
    try:
        mod = mesh.modifiers.new("Rig", "ARMATURE")
        mod.object = arm
        assert rig.find_mmd_source(mesh) == (arm, False)
        mesh.modifiers.remove(mod)
        arm.parent = root
        bridge.parent = root
        mesh.parent = bridge
        assert rig.find_mmd_source(mesh) == (arm, True)
        mesh.parent = arm
        assert rig.find_mmd_source(mesh) == (arm, True)
    finally:
        _remove_objects(mesh, arm, bridge, root)


def assert_canonical_joint_geometry(addon):
    """Ordered exact joints drive heads then chain tails, never helper substrings."""
    rig = _rig(addon)
    mesh = _weighted_mesh("Joint bounds", [(-2, 0, -4), (2, 0, 4)], [])
    bones = [
        ("胸", (9, 0, 1), (9, 0, 2), None),
        ("上半身1", (8, 0, 1), (8, 0, 2), None),
        ("上半身", (0, 0, 1), (0, 0, 2), None),
        ("センター", (7, 0, 0), (7, 0, 1), None),
        ("腰", (6, 0, 0), (6, 0, 1), None),
        ("下半身", (0, 0, 0), (0, 0, 1), None),
        ("首", (5, 0, 3), (5, 0, 4), None),
        ("頭", (0, 0, 4), (2, 0, 4), None),
        ("腕", (99, 0, 1), (99, 0, 2), None),
        ("左腕.R", (88, 0, 1), (88, 0, 2), None),
        ("腕捩.L", (77, 0, 1), (77, 0, 2), None),
        ("肩_L", (-2, 0, 3), (-3, 0, 3), None),
        ("腕.L", (-3, 0, 3), (-4, 0, 3), None),
        ("手首_L", (-7, 0, 1), (-8, 0, 1), None),
        ("右腕", (3, 0, 3), (4, 0, 3), None),
        ("ひじ.R", (5, 0, 2), (6, 0, 2), None),
        ("足首.L", (-1, 0, -4), (-1, 0, -5), None),
        ("足_L", (-1, 0, -1), (-1, 0, -2), None),
        ("右足", (1, 0, -1), (1, 0, -2), None),
        ("ひざ_R", (1, 0, -2), (1, 0, -3), None),
    ]
    transform = Matrix.Translation((10, 20, 30)) @ Matrix.Diagonal((2, 3, 4, 1))
    arm = _armature_with_bones("Joint priorities", bones, transform)
    result = None
    try:
        result = rig.build_auto_armature(mesh, arm, {})
        assert result.matrix_world == Matrix.Identity(4)
        expected = {
            "Main": ((10, 20, 34), (10, 20, 46)),
            "Head": ((10, 20, 46), (10, 20, 46 + (80 ** 0.5) * 0.1)),
            "Hip": ((10, 20, 30), (10, 20, 26)),
            "OA_L": ((4, 20, 42), (0, 20, 38)),
            "UA_L": ((0, 20, 38), (-4, 20, 34)),
            "Hand_L": ((-4, 20, 34), (-8, 20, 30)),
            "OA_R": ((16, 20, 42), (20, 20, 38)),
            "UA_R": ((20, 20, 38), (24, 20, 34)),
            "OS_L": ((8, 20, 26), (8, 20, 20)),
            "US_L": ((8, 20, 20), (8, 20, 14)),
            "OS_R": ((12, 20, 26), (12, 20, 22)),
            "US_R": ((12, 20, 22), (12, 20, 22 - (80 ** 0.5) * 0.25)),
        }
        for name, (head, tail) in expected.items():
            bone = result.data.bones[name]
            _close(bone.head_local, head)
            _close(bone.tail_local, tail)
        assert all(bone.length >= 0.000999 for bone in result.data.bones)
    finally:
        _remove_objects(mesh, arm, result)


def assert_sparse_auto_mapping(addon):
    """AUTO maps named weights against complete final segments, including fallback Head."""
    rig = _rig(addon)
    arm = _armature_with_bones("Sparse rig", [("上半身", (0, 0, 0), (0, 0, 1), None)])
    mesh = _weighted_mesh("Sparse head", [(0, 0, 0), (1, 0, 0), (0, 0, 2)], [("頭", [(0, 1), (1, 1), (2, 1)])])
    mesh.data.polygons # Synthetic face-free mapping also checks fallback-only conversion.
    result = None
    try:
        result = rig.convert(mesh, arm, rig.ConversionOptions())
        group = result.mesh.vertex_groups["Head"]
        assert [group.weight(index) for index in range(3)] == [1, 1, 1]
        _close(result.armature.data.bones["Head"].head_local, (0.5, 0, 2))
    finally:
        _remove_objects(mesh, arm, result.mesh if result else None, result.armature if result else None)


def assert_template_extras_and_rest_clone(addon):
    """TEMPLATE creates collision-free extras near their real parent and drops live pose/action."""
    rig = _rig(addon)
    mesh, source = _mmd_character()
    extra = mesh.vertex_groups.new(name="TailControl")
    extra.add([2], 1, "REPLACE")
    template = _armature_with_bones("Template extras", [
        ("Main", (0, 0, 0), (0, 0, 1), None),
        ("Head", (0, 0, 2), (0, 0, 3), "Main"),
        ("mmd_14", (99, 0, 0), (99, 0, 1), "Main"),
        ("漢", (99, 0, 2), (99, 0, 3), "Main"),
    ], mesh.matrix_world.copy())
    template.constraints.new("COPY_LOCATION").target = source
    template.pose.bones["Head"].location = (7, 8, 9)
    template.animation_data_create()
    template.animation_data.action = bpy.data.actions.new("Template live action")
    bpy.context.view_layer.update()
    expected_world = template.matrix_world.copy()
    result = None
    try:
        logs = StringIO()
        with redirect_stdout(logs):
            result = rig.convert(mesh, source, rig.ConversionOptions(
                rig_mode="TEMPLATE", template_armature=template, keep_extra_bones=True))
        assert result.mesh.vertex_groups.get("mmd_14_1") is not None
        bone = result.armature.data.bones["mmd_14_1"]
        assert bone.parent.name == "Head"
        assert result.mesh.vertex_groups["mmd_14_1"].weight(2) == 0.5
        assert not result.armature.constraints
        assert not result.armature.animation_data
        _close(result.armature.pose.bones["Head"].location, (0, 0, 0))
        assert max(abs(a-b) for ar, br in zip(result.armature.matrix_world, expected_world)
                   for a,b in zip(ar,br)) < 1e-5
        assert "TailControl\tmmd_14_1" in bpy.data.texts["mmd_bone_name_map"].as_string()
        assert "unbound" in logs.getvalue().lower() and "unused" in logs.getvalue().lower()
    finally:
        _remove_objects(mesh, source, template, result.mesh if result else None, result.armature if result else None)


def assert_serialized_runtime_limits(addon):
    """Strict limits use populated serialized order, UV expansion and evaluated topology."""
    rig = _rig(addon)
    exporter = addon.o3d_io.io_o3d_export
    mesh, source = _mmd_character()
    for group in list(mesh.vertex_groups):
        mesh.vertex_groups.remove(group)
    mesh.vertex_groups.new(name="Main").add(list(range(len(mesh.data.vertices))), 1, "REPLACE")
    template = _armature_with_bones("Empty-first template", [
        *[(f"Empty{index}", (index, 0, 0), (index, 0, 1), None) for index in range(128)],
        ("Main", (0, 0, 0), (0, 0, 1), None),
        ("漢", (0, 0, 0), (0, 0, 1), None)])
    result = None
    try:
        result = rig.convert(mesh, source, rig.ConversionOptions(rig_mode="TEMPLATE", template_armature=template))
        assert rig.validate_character_export(result.mesh)["bones"] == ("Main",)
    finally:
        _remove_objects(mesh, source, template, result.mesh if result else None, result.armature if result else None)

    # Boundary65535 passes;65536 total fails despite low weighted index.
    vertices = [(float(index), float(index % 2), 0) for index in range(65536)]
    faces = [(index, index + 1, index + 2) for index in range(0, 65535, 3)]
    data = bpy.data.meshes.new("Runtime boundary")
    data.from_pydata(vertices[:65535], [], faces)
    obj = bpy.data.objects.new("Runtime boundary", data)
    bpy.context.scene.collection.objects.link(obj)
    obj.vertex_groups.new(name="Main").add([0], 1, "REPLACE")
    try:
        assert exporter.validate_character_export(obj)["vertices"] == 65535
        # Append one independent corner sharing two existing vertices.
        replacement = bpy.data.meshes.new("Runtime boundary over")
        replacement.from_pydata(vertices, [], [*faces, (65534, 65533, 65535)])
        obj.data = replacement
        obj.vertex_groups.new(name="Main").add([0], 1, "REPLACE")
        _refuses(lambda: exporter.validate_character_export(obj), "65535")
    finally:
        _remove_objects(obj)

    # Populated index127 tie wins before index128; stronger index128 must refuse.
    data = bpy.data.meshes.new("Dominant order")
    data.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    obj = bpy.data.objects.new("Dominant order", data)
    bpy.context.scene.collection.objects.link(obj)
    try:
        for index in range(129):
            obj.vertex_groups.new(name=f"Bone{index}").add([0, 1, 2], 0.01 if index < 127 else 0.5, "REPLACE")
        assert exporter.validate_character_export(obj)["bones"][-1] == "Bone128"
        obj.vertex_groups["Bone128"].add([0], 0.75, "REPLACE")
        _refuses(lambda: exporter.validate_character_export(obj), "128")
    finally:
        _remove_objects(obj)

    # A repeated UV fan has21848 source vertices but65538 serialized vertices.
    data = bpy.data.meshes.new("Runtime UV fan")
    data.from_pydata([(0, 0, 0), *[(float(index), 1, 0) for index in range(21847)]], [],
                     [(0, index, index + 1) for index in range(1, 21847)])
    uv = data.uv_layers.new()
    for index, loop in enumerate(uv.data):
        loop.uv = (index / 100000, 0)
    obj = bpy.data.objects.new("Runtime UV fan", data)
    bpy.context.scene.collection.objects.link(obj)
    obj.vertex_groups.new(name="Main").add(list(range(len(data.vertices))), 1, "REPLACE")
    source = _armature_with_bones("Fan source", [("上半身", (0, 0, 0), (0, 0, 1), None)])
    try:
        before = _counts()
        _refuses(lambda: rig.convert(obj, source, rig.ConversionOptions()), "65535")
        assert _counts() == before
    finally:
        _remove_objects(obj, source)

    # Strict total includes unweighted serialized vertices; disk-only grammar stays permissive.
    from smoke_io import _make_wide_unique_uv_mesh
    data, count = _make_wide_unique_uv_mesh("Runtime total")
    obj = bpy.data.objects.new("Runtime total", data)
    bpy.context.scene.collection.objects.link(obj)
    obj.vertex_groups.new(name="Main").add([0], 1, "REPLACE")
    try:
        _refuses(lambda: exporter.validate_character_export(obj), "65535")
    finally:
        _remove_objects(obj)


def assert_owned_rollback_and_deletion(addon):
    """Only an evidenced MMD EMPTY root can delete; all staged state rolls back."""
    rig = _rig(addon)
    class SmokeMMDRoot(bpy.types.PropertyGroup):
        name_j: bpy.props.StringProperty()

    owns_root_property = not hasattr(bpy.types.Object, "mmd_root")
    if owns_root_property:
        bpy.utils.register_class(SmokeMMDRoot)
        bpy.types.Object.mmd_root = bpy.props.PointerProperty(type=SmokeMMDRoot)
    try:
        _assert_deletion_roots_with_metadata(addon)
    finally:
        if owns_root_property:
            del bpy.types.Object.mmd_root
            bpy.utils.unregister_class(SmokeMMDRoot)
    _assert_deletion_dependants_and_rollback(addon)


def _assert_deletion_roots_with_metadata(addon):
    rig = _rig(addon)
    for root_kind in ("MESH", "EMPTY", "MMD"):
        mesh, source = _mmd_character()
        root_data = bpy.data.meshes.new("Unrelated root mesh") if root_kind == "MESH" else None
        root = bpy.data.objects.new("Root", root_data)
        bpy.context.scene.collection.objects.link(root)
        if root_kind == "MMD":
            root["mmd_type"] = "ROOT"
        source.parent = root
        mesh.parent = source
        world = mesh.matrix_world.copy()
        shared = source.copy()
        bpy.context.scene.collection.objects.link(shared)
        shared.parent = None
        shared_data = source.data
        source_name, root_name = source.name, root.name
        result = None
        try:
            result = rig.convert(mesh, source, rig.ConversionOptions(delete_source_rig=True))
            assert bpy.data.objects.get(source_name) is None
            assert (bpy.data.objects.get(root_name) is None) == (root_kind == "MMD")
            assert shared.data == shared_data
            assert max(abs(a-b) for ar, br in zip(mesh.matrix_world, world) for a,b in zip(ar,br)) < 1e-5
        finally:
            _remove_objects(mesh, shared, root, result.mesh if result else None, result.armature if result else None)

def _assert_deletion_dependants_and_rollback(addon):
    rig = _rig(addon)
    for dependency in ("child", "modifier", "constraint"):
        mesh, source = _mmd_character()
        other = bpy.data.objects.new("Dependent", None if dependency != "modifier" else mesh.data.copy())
        bpy.context.scene.collection.objects.link(other)
        if dependency == "child":
            other.parent = source
        elif dependency == "modifier":
            other.modifiers.new("Dependent rig", "ARMATURE").object = source
        else:
            other.constraints.new("COPY_LOCATION").target = source
        before = _counts()
        try:
            _refuses(lambda: rig.convert(mesh, source, rig.ConversionOptions(delete_source_rig=True)), "depend")
            assert _counts() == before
        finally:
            _remove_objects(mesh, source, other)

    mesh, source = _mmd_character()
    mesh.vertex_groups.new(name="TailControl").add([2], 1, "REPLACE")
    material = mesh.data.materials[0]
    material["cfg_data"] = [["[setbone]", "Main", "-2"]]
    text = bpy.data.texts.get("mmd_bone_name_map") or bpy.data.texts.new("mmd_bone_name_map")
    text.clear()
    text.write("original mapping\n")
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    bpy.context.view_layer.objects.active = mesh
    bpy.ops.object.mode_set(mode="EDIT")
    before, weights, original = _counts(), _weight_snapshot(mesh), rig._write_mapping_text
    def fail_after_text(pairs):
        original(pairs)
        raise RuntimeError("injected after mapping write")
    rig._write_mapping_text = fail_after_text
    try:
        try:
            rig.convert(mesh, source, rig.ConversionOptions(keep_extra_bones=True, delete_source_rig=True))
        except RuntimeError as error:
            assert str(error) == "injected after mapping write"
        else:
            raise AssertionError("injected failure missing")
        assert _counts() == before
        assert text.as_string() == "original mapping\n"
        assert bpy.context.view_layer.objects.active == mesh
        assert bpy.context.selected_objects == [mesh] and mesh.mode == "EDIT"
        assert _weight_snapshot(mesh) == weights
        assert mesh.modifiers[0].object == source
    finally:
        rig._write_mapping_text = original
        if bpy.context.object and bpy.context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        _remove_objects(mesh, source)


def assert_basis_and_evaluated_blend_preservation(addon):
    """Key removal retains edited Basis, while evaluated blending controls actual CFG."""
    rig = _rig(addon)
    mesh, source = _mmd_character()
    mesh.data.shape_keys.reference_key.data[0].co.z = 2
    mesh.data.shape_keys.key_blocks["Smile"].data[0].co.z = 7
    mesh.data.shape_keys.key_blocks["Smile"].value = 1
    snapshot = _weight_snapshot(mesh)
    result = None
    try:
        result = rig.convert(mesh, source, rig.ConversionOptions())
        assert result.mesh.data.vertices[0].co.z == 2
        assert result.mesh.data.shape_keys is None
        assert mesh.data.shape_keys.reference_key.data[0].co.z == 2
        assert mesh.data.shape_keys.key_blocks["Smile"].data[0].co.z == 7
        assert mesh.data.shape_keys.key_blocks["Smile"].value == 1
        assert _weight_snapshot(mesh) == snapshot
    finally:
        _remove_objects(mesh, source, result.mesh if result else None, result.armature if result else None)

    data = bpy.data.meshes.new("Evaluated blend")
    data.from_pydata([(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)], [], [(0, 1, 2, 3)])
    mesh = bpy.data.objects.new("Evaluated blend", data)
    bpy.context.scene.collection.objects.link(mesh)
    mesh.vertex_groups.new(name="上半身").add([0, 1], 1, "REPLACE")
    mesh.vertex_groups.new(name="頭").add([2, 3], 1, "REPLACE")
    subdiv = mesh.modifiers.new("Blending topology", "SUBSURF")
    subdiv.levels = 1
    source = _armature_with_bones("Blend source", [("上半身", (0, 0, 0), (0, 0, 1), None),
                                                     ("頭", (0, 0, 1), (0, 0, 2), None)])
    modifier = mesh.modifiers.new("Armature", "ARMATURE")
    modifier.object = source
    modifier.show_viewport, modifier.show_render = True, False
    result = None
    try:
        result = rig.convert(mesh, source, rig.ConversionOptions())
        with tempfile.TemporaryDirectory(prefix="evaluated-blend-cfg-") as temporary:
            bpy.ops.object.select_all(action="DESELECT")
            result.mesh.select_set(True)
            path = Path(temporary) / "model.cfg"
            addon.o3d_io.io_o3d_export.do_export(str(path), bpy.context, Matrix.Identity(4), True, 7)
            parsed = addon.o3d_io.o3dconvert.import_o3d((Path(temporary) / result.mesh["export_path"]).read_bytes())
            counts = {}
            for _, entries in parsed[4]:
                for index, weight in entries:
                    if weight > 0:
                        counts[index] = counts.get(index, 0) + 1
            assert any(count > 1 for count in counts.values())
            assert "[smoothskin]" in path.read_text(encoding="utf-8")
        assert modifier.show_viewport and not modifier.show_render
        assert len(mesh.data.vertices) == 4 and mesh.modifiers[0] == subdiv
    finally:
        _remove_objects(mesh, source, result.mesh if result else None, result.armature if result else None)


def assert_conversion_empty_context_restored(addon):
    """Successful conversion must restore an explicitly empty active/selection context."""
    rig = _rig(addon)
    mesh, source = _mmd_character()
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = None
    result = None
    try:
        result = rig.convert(mesh, source, rig.ConversionOptions())
        assert bpy.context.view_layer.objects.active is None
        assert not bpy.context.selected_objects
    finally:
        _remove_objects(mesh, source, result.mesh if result else None, result.armature if result else None)


def assert_missing_weighted_target_refuses(addon):
    """An absent final target must refuse before serializer masks it as index0."""
    rig = _rig(addon)
    mesh, source = _mmd_character()
    original = rig.merge_weights
    rig.merge_weights = lambda *args, **kwargs: {"MissingTarget": [(0, 1)]}
    try:
        before = _counts()
        _refuses(lambda: rig.convert(mesh, source, rig.ConversionOptions()), "absent")
        assert _counts() == before
    finally:
        rig.merge_weights = original
        _remove_objects(mesh, source)


def assert_conversion_parent_material_paths(addon):
    """BONE parent metadata, material override blocks and inherited paths cannot leak."""
    rig = _rig(addon)
    mesh, source = _mmd_character()
    template = _armature_with_bones("Parent template", [("Main", (0, 0, 0), (0, 0, 1), None)])
    mesh.parent = template
    mesh.parent_type = "BONE"
    mesh.parent_bone = "Main"
    template.pose.bones["Main"].location = (3, 4, 5)
    bpy.context.view_layer.update()
    world = mesh.matrix_world.copy()
    material = mesh.data.materials[0]
    material["cfg_data"] = [["[setbone]", "Main", "-2"], ["[smoothskin]"], ["[matl_noZwrite]"]]
    material["keep_property"] = "original"
    mesh.data.materials.append(material)
    mesh.material_slots[1].link = "OBJECT"
    mesh.material_slots[1].material = material
    plain = bpy.data.materials.new("Unaffected material")
    mesh.data.materials.append(plain)
    mesh["export_path"] = "/Woman03.o3d"
    collision = bpy.data.objects.new("Output collision", None)
    collision["export_path"] = "WOMAN03_CONVERTED.O3D"
    bpy.context.scene.collection.objects.link(collision)
    result = second = None
    snapshot = _weight_snapshot(mesh)
    try:
        result = rig.convert(mesh, source, rig.ConversionOptions(
            rig_mode="TEMPLATE", template_armature=template, max_influences=1))
        assert result.mesh.parent_type == "OBJECT" and result.mesh.parent_bone == ""
        bpy.context.view_layer.update()
        assert max(abs(a-b) for ar, br in zip(result.mesh.matrix_world, world) for a,b in zip(ar,br)) < 1e-5
        copied = result.mesh.data.materials[0]
        assert copied is not material and result.mesh.material_slots[1].material == copied
        assert result.mesh.data.materials[2] == plain
        assert copied["keep_property"] == "original"
        assert [list(block) for block in copied["cfg_data"]] == [["[matl_noZwrite]"]]
        assert [list(block) for block in material["cfg_data"]][0] == ["[setbone]", "Main", "-2"]
        assert result.mesh["export_path"] == "Woman03_converted_1.o3d"
        second = rig.convert(mesh, source, rig.ConversionOptions(max_influences=1))
        assert second.mesh["export_path"] == "Woman03_converted_2.o3d"
        assert mesh["export_path"] == "/Woman03.o3d" and _weight_snapshot(mesh) == snapshot
        with tempfile.TemporaryDirectory(prefix="converted-cfg-") as temporary:
            bpy.ops.object.select_all(action="DESELECT")
            result.mesh.select_set(True)
            path = Path(temporary) / "model.cfg"
            addon.o3d_io.io_o3d_export.do_export(str(path), bpy.context, Matrix.Identity(4), True, 7)
            text = path.read_text(encoding="utf-8")
            assert text.count("[setbone]\nMain\n-11\n") == 1, text
            assert "[setbone]\nMain\n-2\n" not in text
            assert "[smoothskin]" not in text
            assert "[setbone]\nHead\n" not in text
            assert (Path(temporary) / result.mesh["export_path"]).is_file()
    finally:
        _remove_objects(mesh, source, template, collision,
                        result.mesh if result else None, result.armature if result else None,
                        second.mesh if second else None, second.armature if second else None)
