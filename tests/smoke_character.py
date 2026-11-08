"""Synthetic MMD character conversion checks; no mmd_tools dependency."""
import importlib
from types import ModuleType

import bpy


def _materials(addon):
    return importlib.import_module(addon.__name__ + ".o3d_io.mmd_materials")


def _mmd_material(addon, *, alpha=0.4, textured=True):
    material = bpy.data.materials.new("MMD Smoke Material")
    addon.o3d_io.blender_compat.enable_material_nodes(material)
    tree = material.node_tree
    tree.nodes.clear()
    group = bpy.data.node_groups.new("User-renamed MMD graph", "ShaderNodeTree")
    for name, socket_type in (
        ("Base Tex", "NodeSocketColor"),
        ("Base Alpha", "NodeSocketFloat"),
        ("Toon Tex", "NodeSocketColor"),
        ("Toon Tex Alpha", "NodeSocketFloat"),
        ("Toon Tex Fac", "NodeSocketFloat"),
        ("Sphere Tex", "NodeSocketColor"),
        ("Sphere Tex Alpha", "NodeSocketFloat"),
        ("Sphere Tex Fac", "NodeSocketFloat"),
        ("Diffuse Color", "NodeSocketColor"),
        ("Alpha", "NodeSocketFloat"),
    ):
        group.interface.new_socket(name=name, in_out="INPUT", socket_type=socket_type)
    group.interface.new_socket(name="Shader", in_out="OUTPUT", socket_type="NodeSocketShader")
    shader = tree.nodes.new("ShaderNodeGroup")
    shader.node_tree = group
    shader.name = "User-renamed shader"
    shader.inputs["Toon Tex Fac"].default_value = 1
    shader.inputs["Sphere Tex Fac"].default_value = 1
    shader.inputs["Diffuse Color"].default_value = (0.2, 0.4, 0.6, 1)
    shader.inputs["Alpha"].default_value = alpha
    output = tree.nodes.new("ShaderNodeOutputMaterial")
    tree.links.new(shader.outputs[0], output.inputs["Surface"])
    uv = tree.nodes.new("ShaderNodeUVMap")
    uv.uv_map = "Character UV"
    mapping = tree.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (2, 3, 1)
    tree.links.new(uv.outputs["UV"], mapping.inputs["Vector"])
    textures = {}
    for name in ("Base", "Toon", "Sphere"):
        texture = tree.nodes.new("ShaderNodeTexImage")
        texture.name = "User-renamed " + name
        texture.image = bpy.data.images.new("Character " + name, width=1, height=1)
        textures[name] = texture
        if name != "Base" or textured:
            tree.links.new(texture.outputs["Color"], shader.inputs[name + " Tex"])
        if name == "Base" and textured:
            tree.links.new(mapping.outputs["Vector"], texture.inputs["Vector"])
            tree.links.new(texture.outputs["Alpha"], shader.inputs["Base Alpha"])
        elif name != "Base":
            tree.links.new(texture.outputs["Alpha"], shader.inputs[name + " Tex Alpha"])
            helper = tree.nodes.new("ShaderNodeVectorMath")
            tree.links.new(mapping.outputs["Vector"], helper.inputs[0])
            tree.links.new(helper.outputs["Vector"], texture.inputs["Vector"])
    unrelated = tree.nodes.new("ShaderNodeValue")
    unrelated.name = "Unrelated keep me"
    return material, shader, textures, mapping, uv, output


def assert_toon_reset(addon: ModuleType) -> None:
    # Catches name-based detection, incomplete unlinking, sphere resets by default,
    # per-node instead of per-material counts, and non-idempotent changes.
    materials = _materials(addon)
    mat, shader, textures, mapping, uv, output = _mmd_material(addon)
    plain = addon.o3d_io.blender_compat.create_solid_material((0.8, 0.7, 0.6, 1))
    plain_nodes = list(plain.node_tree.nodes)
    assert materials.mmd_nodes(mat) == [shader]
    assert materials.mmd_nodes(plain) == []
    assert materials.reset_toon([plain]) == 0
    assert list(plain.node_tree.nodes) == plain_nodes
    assert materials.reset_toon([mat]) == 1
    assert shader.inputs["Toon Tex Fac"].default_value == 0
    assert not shader.inputs["Toon Tex"].is_linked
    assert not shader.inputs["Toon Tex Alpha"].is_linked
    assert shader.inputs["Sphere Tex Alpha"].is_linked
    assert shader.inputs["Sphere Tex Fac"].default_value == 1
    assert shader.inputs["Sphere Tex"].is_linked
    assert materials.reset_toon([mat]) == 0
    assert materials.reset_toon([mat], reset_sphere=True) == 1
    assert shader.inputs["Sphere Tex Fac"].default_value == 0
    assert not shader.inputs["Sphere Tex"].is_linked
    assert not shader.inputs["Sphere Tex Alpha"].is_linked
    assert materials.reset_toon([mat], reset_sphere=True) == 0
    second = mat.node_tree.nodes.new("ShaderNodeGroup")
    second.node_tree = shader.node_tree
    second.inputs["Toon Tex Fac"].default_value = 1
    factor = mat.node_tree.nodes.new("ShaderNodeValue")
    mat.node_tree.links.new(factor.outputs[0], second.inputs["Toon Tex Fac"])
    shader.inputs["Toon Tex Fac"].default_value = 1
    assert materials.reset_toon([mat, mat]) == 1
    assert not second.inputs["Toon Tex Fac"].is_linked
    assert second.inputs["Toon Tex Fac"].default_value == 0
    assert shader.inputs["Toon Tex Fac"].default_value == 0


def assert_material_flatten(addon: ModuleType) -> None:
    # Catches lost base UV/alpha, inactive output wiring, destructive node clears,
    # missing mmd_tools overrides/fallbacks, and repeated flatten mutations.
    materials = _materials(addon)
    compat = addon.o3d_io.blender_compat
    mat, shader, textures, mapping, uv, output = _mmd_material(addon)
    base = textures["Base"]
    base_image = base.image
    removed = {shader.name, textures["Toon"].name, textures["Sphere"].name}
    removed.update(node.name for node in mat.node_tree.nodes if node.bl_idname == "ShaderNodeVectorMath")
    # An inactive Principled output must not distract conversion from active one.
    other = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
    old_principled = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    old_principled.inputs["Base Color"].default_value = (0.9, 0.1, 0.2, 1)
    old_principled.inputs["Alpha"].default_value = 0.65
    old_base = mat.node_tree.nodes.new("ShaderNodeTexImage")
    old_base.image = bpy.data.images.new("Unrelated base", width=1, height=1)
    old_alpha = mat.node_tree.nodes.new("ShaderNodeValue")
    old_alpha.outputs[0].default_value = 0.35
    mat.node_tree.links.new(old_base.outputs["Color"], old_principled.inputs["Base Color"])
    mat.node_tree.links.new(old_alpha.outputs[0], old_principled.inputs["Alpha"])
    old_base_link = old_principled.inputs["Base Color"].links[0]
    old_alpha_link = old_principled.inputs["Alpha"].links[0]
    old_base_default = tuple(old_principled.inputs["Base Color"].default_value)
    old_alpha_default = old_principled.inputs["Alpha"].default_value
    mat.node_tree.links.new(old_principled.outputs[0], other.inputs["Surface"])
    output.is_active_output = True
    assert materials.flatten_material(mat)
    principled = output.inputs["Surface"].links[0].from_node
    assert old_principled.inputs["Base Color"].links[0] == old_base_link
    assert old_principled.inputs["Alpha"].links[0] == old_alpha_link
    assert tuple(old_principled.inputs["Base Color"].default_value) == old_base_default
    assert old_principled.inputs["Alpha"].default_value == old_alpha_default
    assert principled.bl_idname == "ShaderNodeBsdfPrincipled"
    assert output.is_active_output
    assert principled.inputs["Base Color"].links[0].from_node == base
    assert principled.inputs["Alpha"].links[0].from_node == base
    assert principled.inputs["Alpha"].links[0].from_socket == base.outputs["Alpha"]
    assert base.inputs["Vector"].links[0].from_node == mapping
    assert mapping.inputs["Vector"].links[0].from_node == uv
    assert tuple(mapping.inputs["Scale"].default_value) == (2, 3, 1)
    assert all(mat.node_tree.nodes.get(name) is None for name in removed)
    assert mat.node_tree.nodes.get("Unrelated keep me") is not None
    assert all(abs(a - b) < 0.001 for a, b in zip(mat.diffuse_color, (0.2, 0.4, 0.6, 0.4)))
    assert compat.get_material_alpha_mode(mat) == "BLEND"
    nodes = list(mat.node_tree.nodes)
    links = list(mat.node_tree.links)
    assert not materials.flatten_material(mat)
    assert list(mat.node_tree.nodes) == nodes
    assert list(mat.node_tree.links) == links

    reset, shader, textures, mapping, uv, output = _mmd_material(addon)
    toon_name = textures["Toon"].name
    sphere_name = textures["Sphere"].name
    # Keep helpers feeding unrelated nodes even when they also fed MMD.
    shared = reset.node_tree.nodes.new("ShaderNodeVectorMath")
    shared_texture = reset.node_tree.nodes.new("ShaderNodeTexImage")
    reset.node_tree.links.new(shared.outputs[0], textures["Toon"].inputs["Vector"])
    reset.node_tree.links.new(shared.outputs[0], shared_texture.inputs["Vector"])
    assert materials.reset_toon([reset], reset_sphere=True) == 1
    assert materials.flatten_material(reset)
    assert reset.node_tree.nodes.get(toon_name) is None
    assert reset.node_tree.nodes.get(sphere_name) is None
    assert shared_texture.inputs["Vector"].links[0].from_node == shared
    assert output.is_active_output
    assert output.inputs["Surface"].links[0].from_node.bl_idname == "ShaderNodeBsdfPrincipled"
    assert sum(node.bl_idname == "ShaderNodeOutputMaterial" for node in reset.node_tree.nodes) == 1

    opaque, shader, *_ = _mmd_material(addon, alpha=1, textured=False)
    assert materials.flatten_material(opaque)
    assert compat.principled_wrapper(opaque).base_color_texture.image is None
    assert compat.get_material_alpha_mode(opaque) == "OPAQUE"
    opaque_textured, shader, *_ = _mmd_material(addon, alpha=1, textured=True)
    assert materials.flatten_material(opaque_textured)
    assert compat.get_material_alpha_mode(opaque_textured) == "OPAQUE"
    white, shader, *_ = _mmd_material(addon, alpha=1, textured=False)
    shader.node_tree.interface.remove(next(item for item in shader.node_tree.interface.items_tree if item.name == "Diffuse Color"))
    shader.node_tree.interface.remove(next(item for item in shader.node_tree.interface.items_tree if item.name == "Alpha"))
    assert materials.flatten_material(white)
    assert tuple(compat.principled_wrapper(white).base_color) == (1, 1, 1)
    assert compat.principled_wrapper(white).alpha == 1

    class SmokeMMDMaterial(bpy.types.PropertyGroup):
        diffuse_color: bpy.props.FloatVectorProperty(size=3, default=(1, 1, 1))
        alpha: bpy.props.FloatProperty(default=1)

    owns_property = not hasattr(bpy.types.Material, "mmd_material")
    if owns_property:
        bpy.utils.register_class(SmokeMMDMaterial)
        bpy.types.Material.mmd_material = bpy.props.PointerProperty(type=SmokeMMDMaterial)
    try:
        override, *_ = _mmd_material(addon, textured=False)
        override.mmd_material.diffuse_color = (0.7, 0.3, 0.1)
        override.mmd_material.alpha = 0.25
        assert materials.flatten_material(override)
        wrapper = compat.principled_wrapper(override)
        assert all(abs(a - b) < 0.001 for a, b in zip(wrapper.base_color, (0.7, 0.3, 0.1)))
        assert abs(wrapper.alpha - 0.25) < 0.001
    finally:
        if owns_property:
            del bpy.types.Material.mmd_material
            bpy.utils.unregister_class(SmokeMMDMaterial)

    plain = compat.create_solid_material((0.8, 0.7, 0.6, 1))
    original = (list(plain.node_tree.nodes), list(plain.node_tree.links), tuple(plain.diffuse_color))
    assert not materials.flatten_material(plain)
    assert (list(plain.node_tree.nodes), list(plain.node_tree.links), tuple(plain.diffuse_color)) == original


def _rig(addon):
    return importlib.import_module(addon.__name__ + ".o3d_io.mmd_rig")


def _weighted_mesh(name, coordinates, groups):
    data = bpy.data.meshes.new(name)
    data.from_pydata(coordinates, [], [])
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    for name, weights in groups:
        group = obj.vertex_groups.new(name=name)
        for vertex, weight in weights:
            group.add([vertex], weight, "REPLACE")
    return obj


def _weight_snapshot(obj):
    return (
        obj.data.as_pointer(), tuple(tuple(row) for row in obj.matrix_world),
        tuple(group.name for group in obj.vertex_groups),
        tuple((tuple(vertex.co), tuple((entry.group, entry.weight) for entry in vertex.groups))
              for vertex in obj.data.vertices),
    )


def assert_bone_name_mapping(addon: ModuleType) -> None:
    # Catches overlapping rules in the wrong order, guessed sides, control groups,
    # and local/head-only proximity instead of weighted world segment distances.
    from mathutils import Matrix, Vector
    from contextlib import redirect_stdout
    from io import StringIO

    rig = _rig(addon)
    cases = [
        ("頭", "Head"), ("首", "Head"), ("ひじ.L", "UA_L"),
        ("腕捩.R", "OA_R"), ("手首.L", "Hand_L"),
        ("足.R", "OS_R"), ("足首.L", "US_L"), ("スカート_0_1", "Hip"),
        ("左手先", "Hand_L"), ("右人差指", "Hand_R"), ("手捩_R", "UA_R"),
        ("肩_L", "OA_L"), ("足先EX_R", "US_R"), ("つま先.L", "US_L"),
        ("右ひざ", "US_R"), ("上半身2", "Main"), ("胸", "Main"),
        ("センター", "Hip"), ("グルーブ", "Hip"), ("腰", "Hip"), ("下半身", "Hip"),
        *((name, "Head") for name in ("両目", "目", "眉", "口", "あご", "髪", "发", "马尾", "アホ毛", "UV_1")),
        *((name, None) for name in ("腕", "ひじ", "手首", "足", "つま先", "unknown")),
    ]
    for name, expected in cases:
        assert rig.map_bone_name(name, rig.CANONICAL_NAMES) == expected, name
    for name in rig.CANONICAL_NAMES:
        assert rig.map_bone_name(name, rig.CANONICAL_NAMES) == name
    assert rig.map_bone_name("Custom", ("Custom",)) == "Custom"
    assert rig.map_bone_name("頭", ("Hip",)) is None
    assert rig.map_bone_name("腕.L", ("OA_R",)) is None
    for name in ("mmd_edge_scale", "mmd_vertex_order", "_shadow", "_shadowFoo", "_dummy", "_dummy.L"):
        assert rig.map_bone_name(name, (name, *rig.CANONICAL_NAMES)) is None

    segments = {
        "Main": (Vector((10, 0, 0)), Vector((10, 10, 0))),
        "Hip": (Vector((12, 9, 0)), Vector((12, 9, 0))),
    }
    mesh = _weighted_mesh("MMD mapping", [(0, 9, 0), (2, 9, 0)], [
        ("mmd_edge_scale", [(0, 1)]), ("Mystery", [(0, 0.9), (1, 0.1)]),
        ("_shadowFoo", [(1, 1)]), ("Empty", []),
        ("Mystery2", [(0, 0.1), (1, 0.9)]), ("Main", [(1, 1)]),
    ])
    mesh.matrix_world = Matrix.Translation((10, 0, 0))
    before = _weight_snapshot(mesh)
    segment_before = {name: (head.copy(), tail.copy()) for name, (head, tail) in segments.items()}
    logs = StringIO()
    with redirect_stdout(logs):
        mapping = rig.build_mapping(mesh, segments)
    assert mapping == {"mmd_edge_scale": None, "Mystery": "Main", "_shadowFoo": None,
                       "Empty": None, "Mystery2": "Hip", "Main": "Main"}
    assert "ignored=2" in logs.getvalue() and "proximity=2" in logs.getvalue()
    print(logs.getvalue(), end="")
    assert rig.build_mapping(mesh, segments, keep_extra_bones=True) == {
        "mmd_edge_scale": None, "Mystery": "mmd_1", "_shadowFoo": None,
        "Empty": None, "Mystery2": "mmd_4", "Main": "Main"}
    assert rig.build_mapping(mesh, {})["Mystery"] is None
    assert _weight_snapshot(mesh) == before
    assert segments == segment_before

    # Segment ties use supplied rig order, independent of alphabetical names.
    tie = {"Hip": segments["Main"], "Main": segments["Main"]}
    assert rig.build_mapping(mesh, tie)["Mystery"] == "Hip"

    data = bpy.data.armatures.new("MMD source rest rig")
    armature = bpy.data.objects.new("MMD source rest rig", data)
    bpy.context.scene.collection.objects.link(armature)
    old_active = bpy.context.view_layer.objects.active
    old_selection = list(bpy.context.selected_objects)
    bpy.ops.object.select_all(action="DESELECT")
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="EDIT")
    bone = data.edit_bones.new("頭")
    bone.head, bone.tail = (1, 0, 0), (1, 2, 0)
    bpy.ops.object.mode_set(mode="OBJECT")
    armature.matrix_world = Matrix.Translation((5, 6, 7)) @ Matrix.Diagonal((2, 3, 4, 1))
    armature.pose.bones["頭"].location = (9, 9, 9)
    rest = rig.read_source_rig(armature)
    assert list(rest) == ["頭"]
    assert tuple(rest["頭"][0]) == (7, 6, 7)
    assert tuple(rest["頭"][1]) == (7, 12, 7)
    rest["頭"][0].x = 100
    assert tuple(data.bones["頭"].head_local) == (1, 0, 0)
    assert tuple(armature.pose.bones["頭"].location) == (9, 9, 9)
    armature.select_set(False)
    for obj in old_selection:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = old_active


def assert_weight_merge(addon: ModuleType) -> None:
    # Catches per-group normalization, capping before merges, alphabetical ties,
    # missing zero repairs, invalid caps, and source weight/transform mutation.
    from contextlib import redirect_stdout
    from io import StringIO
    from math import isclose, isfinite
    from mathutils import Matrix, Vector

    rig = _rig(addon)
    mesh = _weighted_mesh("MMD weights", [(0, 0, 0), (0, 2, 0), (0, 4, 0), (0, 3, 0)], [
        ("首", [(0, 0.25)]), ("頭", [(0, 0.25)]), ("Hip", [(0, 0.5)]),
        ("mmd_edge_scale", [(1, 1)]), ("Zero", [(2, 0)]),
    ])
    mesh.matrix_world = Matrix.Translation((10, 0, 0)) @ Matrix.Rotation(-1.5707963267948966, 4, "Z")
    segments = {"Head": (Vector((10, 0, 0)), Vector((10, 0, 0))),
                "Hip": (Vector((13, 0, 0)), Vector((15, 0, 0)))}
    mapping = {"首": "Head", "頭": "Head", "Hip": "Hip", "mmd_edge_scale": None, "Zero": "Head"}
    before = _weight_snapshot(mesh)
    mapping_before = mapping.copy()
    segments_before = {name: (head.copy(), tail.copy()) for name, (head, tail) in segments.items()}
    logs = StringIO()
    with redirect_stdout(logs):
        weights = rig.merge_weights(mesh, mapping, target_segments=segments)
    assert weights == {"Head": [(0, 0.5)], "Hip": [(0, 0.5), (1, 1.0), (2, 1.0), (3, 1.0)]}
    assert all(word in logs.getvalue() for word in ("mass=", "ignored=", "zero=3"))
    print(logs.getvalue(), end="")
    assert rig.merge_weights(mesh, mapping, max_influences=1, target_segments=segments) == {
        "Head": [(0, 1.0)], "Hip": [(1, 1.0), (2, 1.0), (3, 1.0)]}
    assert _weight_snapshot(mesh) == before
    assert mapping == mapping_before and segments == segments_before
    for cap in (0, 9, -1, 1.5, True, None):
        try:
            rig.merge_weights(mesh, mapping, max_influences=cap)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Invalid cap accepted: {cap!r}")

    # Nine distinct targets force the default four and explicit upper cap eight.
    # Reverse mapping insertion order to prove source group order breaks ties.
    tied = _weighted_mesh("MMD tied weights", [(0, 0, 0)], [
        (name, [(0, 0.25)]) for name in ("Z", "Y", "X", "W", "V", "U", "T", "S", "R")
    ])
    tie_mapping = {name: name for name in ("R", "S", "T", "U", "V", "W", "X", "Y", "Z")}
    assert rig.merge_weights(tied, tie_mapping) == {
        "Z": [(0, 0.25)], "Y": [(0, 0.25)], "X": [(0, 0.25)], "W": [(0, 0.25)]}
    eight = rig.merge_weights(tied, tie_mapping, max_influences=8)
    assert list(eight) == ["Z", "Y", "X", "W", "V", "U", "T", "S"]
    assert all(entries == [(0, 0.125)] for entries in eight.values())
    assert rig.merge_weights(tied, tie_mapping) == rig.merge_weights(tied, tie_mapping)

    uneven = _weighted_mesh("MMD unequal weights", [(0, 0, 0)], [
        ("first", [(0, 0.1)]), ("second", [(0, 0.2)]), ("third", [(0, 0.3)]),
        ("fourth", [(0, 0.4)]), ("fifth", [(0, 0.5)]),
    ])
    merged = rig.merge_weights(uneven, {group.name: group.name for group in uneven.vertex_groups})
    assert "first" not in merged
    assert isclose(sum(entries[0][1] for entries in merged.values()), 1, abs_tol=1e-7)
    assert isclose(merged["fifth"][0][1], 5 / 14, abs_tol=1e-7)

    invalid = _weighted_mesh("MMD nonfinite weights", [(0, 0, 0)], [
        ("bad", [(0, float("nan"))]), ("good", [(0, 0.5)]),
    ])
    # Blender stores NaN group weights; they must not poison centroid or merge.
    assert not isfinite(invalid.data.vertices[0].groups[0].weight)
    assert rig.merge_weights(invalid, {"bad": "Head", "good": "Hip"}) == {"Hip": [(0, 1.0)]}
    assert rig.build_mapping(invalid, segments)["bad"] is None
    assert rig.merge_weights(mesh, {}) == {}


def _armature_with_bones(name, bones, matrix=None):
    from mathutils import Matrix

    data = bpy.data.armatures.new(name + " Data")
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    edit = {}
    for bone_name, head, tail, parent in bones:
        bone = data.edit_bones.new(bone_name)
        bone.head, bone.tail = head, tail
        edit[bone_name] = bone
        if parent:
            bone.parent = edit[parent]
    bpy.ops.object.mode_set(mode="OBJECT")
    if matrix is not None:
        obj.matrix_world = matrix
    obj.select_set(False)
    return obj


def _mmd_character():
    from mathutils import Matrix

    vertices = [
        (0, 0, 0), (0, 0, 1), (0, 0, 2),
        (-1, 0, 1.5), (-2, 0, 1.0), (-3, 0, 0.8),
        (1, 0, 1.5), (2, 0, 1.0), (3, 0, 0.8),
        (-0.5, 0, -1), (-0.5, 0, -2),
        (0.5, 0, -1), (0.5, 0, -2),
    ]
    data = bpy.data.meshes.new("MMD Character Data")
    data.from_pydata(vertices, [], [(0, index, index + 1) for index in range(1, len(vertices) - 1)])
    data.uv_layers.new(name="UVMap")
    mesh = bpy.data.objects.new("MMD Character", data)
    bpy.context.scene.collection.objects.link(mesh)
    mesh.matrix_world = Matrix.Translation((4, 5, 6)) @ Matrix.Rotation(0.25, 4, "Z")
    material = bpy.data.materials.new("MMD Character Material")
    mesh.data.materials.append(material)
    mesh.shape_key_add(name="Basis")
    mesh.shape_key_add(name="Smile")

    names = [
        ("上半身", [(0, 1), (1, 0.5)]), ("下半身", [(0, 0.5), (9, 1)]),
        ("頭", [(2, 1)]), ("腕.L", [(3, 1)]), ("腕.R", [(6, 1)]),
        ("ひじ.L", [(4, 1)]), ("ひじ.R", [(7, 1)]),
        ("手首.L", [(5, 1)]), ("手首.R", [(8, 1)]),
        ("足.L", [(9, 1)]), ("足.R", [(11, 1)]),
        ("ひざ.L", [(10, 1)]), ("ひざ.R", [(12, 1)]),
        ("mmd_edge_scale", [(0, 1)]),
    ]
    for group_name, weights in names:
        group = mesh.vertex_groups.new(name=group_name)
        for index, weight in weights:
            group.add([index], weight, "REPLACE")
    mesh.data["cfg_data"] = [
        ["[setbone]", "Obsolete", "-99"],
        ["[smoothskin]", "Obsolete"],
        ["[matl]", "character.bmp"],
    ]
    bones = [
        ("上半身", (0, 0, 1), (0, 0, 2), None),
        ("下半身", (0, 0, -1), (0, 0, 0), None),
        ("腰", (0, 0, 0), (0, 0, 1), "下半身"),
        ("頭", (0, 0, 2), (0, 0, 3), "上半身"),
        ("腕.L", (-1, 0, 1.5), (-2, 0, 1), "上半身"),
        ("腕.R", (1, 0, 1.5), (2, 0, 1), "上半身"),
        ("ひじ.L", (-2, 0, 1), (-3, 0, 0.8), "腕.L"),
        ("ひじ.R", (2, 0, 1), (3, 0, 0.8), "腕.R"),
        ("手首.L", (-3, 0, 0.8), (-3.2, 0, 0.8), "ひじ.L"),
        ("手首.R", (3, 0, 0.8), (3.2, 0, 0.8), "ひじ.R"),
        ("足.L", (-0.5, 0, -1), (-0.5, 0, -2), "下半身"),
        ("足.R", (0.5, 0, -1), (0.5, 0, -2), "下半身"),
        ("ひざ.L", (-0.5, 0, -2), (-0.5, 0, -3), "足.L"),
        ("ひざ.R", (0.5, 0, -2), (0.5, 0, -3), "足.R"),
    ]
    source = _armature_with_bones("MMD Source", bones)
    modifier = mesh.modifiers.new("Source Armature", "ARMATURE")
    modifier.object = source
    return mesh, source


def _remove_objects(*objects):
    for obj in objects:
        try:
            name = obj.name if obj is not None else None
        except ReferenceError:
            continue
        if name and bpy.data.objects.get(name) is not None:
            bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)


def assert_auto_armature_build(addon: ModuleType) -> None:
    from contextlib import redirect_stdout
    from io import StringIO

    rig = _rig(addon)
    mesh, source = _mmd_character()
    before_world = mesh.matrix_world.copy()
    source_snapshot = tuple(bone.name for bone in source.data.bones)
    result = None
    try:
        detected, is_mmd = rig.find_mmd_source(mesh)
        assert detected == source and is_mmd
        with redirect_stdout(StringIO()):
            result = rig.convert(mesh, source, rig.ConversionOptions())
        assert result.mesh is not mesh and result.mesh.data is not mesh.data
        assert result.mesh["mmd_converted"]
        assert set(group.name for group in result.mesh.vertex_groups) == set(rig.CANONICAL_NAMES)
        assert result.mesh.parent == result.armature
        assert max(abs(result.mesh.matrix_world[row][col] - before_world[row][col])
                   for row in range(4) for col in range(4)) < 1e-6
        assert tuple(bone.name for bone in source.data.bones) == source_snapshot
        assert result.armature.data.bones["Hip"].parent.name == "Main"
        assert result.armature.data.bones["UA_L"].parent.name == "OA_L"
        assert result.armature.data.bones["Hand_R"].parent.name == "UA_R"
        assert result.mesh.data.shape_keys is None
        blocks = [list(block) for block in result.mesh.data["cfg_data"]]
        assert ["[setbone]", "OS_L", "-2"] in blocks
        assert ["[setbone]", "Main", "-11"] in blocks
        assert ["[matl]", "character.bmp"] in blocks
        assert any(block[0] == "[smoothskin]" for block in blocks)
        try:
            rig.convert(result.mesh, result.armature, rig.ConversionOptions())
        except ValueError:
            pass
        else:
            raise AssertionError("Repeated conversion was accepted")
    finally:
        _remove_objects(mesh, source, result.mesh if result else None, result.armature if result else None)


def assert_template_conversion(addon: ModuleType) -> None:
    from mathutils import Matrix

    rig = _rig(addon)
    mesh, source = _mmd_character()
    template = _armature_with_bones(
        "Template Rig",
        [("Main", (0, 0, 0), (0, 0, 1), None),
         ("Hip", (0, 0, 1), (0, 0, 2), "Main"),
         ("Custom", (2, 0, 0), (2, 0, 2), "Main")],
        Matrix.Translation((2, 3, 4)) @ Matrix.Scale(1.5, 4),
    )
    bpy.context.view_layer.objects.active = template
    template.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    template.data.edit_bones["Custom"].roll = 0.37
    bpy.ops.object.mode_set(mode="OBJECT")
    template.select_set(False)
    result = None
    try:
        options = rig.ConversionOptions(rig_mode="TEMPLATE", template_armature=template,
                                         remove_shape_keys=False)
        before = set(bpy.data.objects)
        try:
            rig.convert(mesh, source, options)
        except ValueError as error:
            assert "shape" in str(error).lower()
        else:
            raise AssertionError("shape keys were silently retained")
        assert set(bpy.data.objects) == before
        options.remove_shape_keys = True
        result = rig.convert(mesh, source, options)
        assert result.armature.matrix_world == template.matrix_world
        assert result.armature.data.bones["Custom"].parent.name == "Main"
        assert result.armature.data.bones["Custom"].matrix == template.data.bones["Custom"].matrix
        assert result.mesh.vertex_groups.get("Custom") is not None
        expected_inverse = template.matrix_world.inverted_safe()
        assert max(abs(result.mesh.matrix_parent_inverse[row][col] - expected_inverse[row][col])
                   for row in range(4) for col in range(4)) < 1e-6
        assert result.mesh.data.shape_keys is None
        assert mesh.data.shape_keys.key_blocks.get("Smile") is not None
    finally:
        _remove_objects(mesh, source, template, result.mesh if result else None, result.armature if result else None)


def assert_extra_bones(addon: ModuleType) -> None:
    rig = _rig(addon)
    mesh, source = _mmd_character()
    extra = mesh.vertex_groups.new(name="TailControl")
    extra.add([0], 1, "REPLACE")
    result = None
    try:
        result = rig.convert(mesh, source, rig.ConversionOptions(keep_extra_bones=True))
        assert result.mesh.vertex_groups.get("mmd_14") is not None
        assert result.armature.data.bones.get("mmd_14") is not None
        assert result.armature.data.bones["mmd_14"].parent is not None
        mapping = bpy.data.texts.get("mmd_bone_name_map")
        assert mapping is not None and "TailControl" in mapping.as_string()
        assert "TailControl" in result.merged_groups
    finally:
        _remove_objects(mesh, source, result.mesh if result else None, result.armature if result else None)


def assert_conversion_export_round_trip(addon: ModuleType) -> None:
    import tempfile
    from pathlib import Path
    from mathutils import Matrix

    rig = _rig(addon)
    mesh, source = _mmd_character()
    result = None
    try:
        result = rig.convert(mesh, source, rig.ConversionOptions())
        with tempfile.TemporaryDirectory(prefix="mmd-character-convert-") as temporary:
            filepath = Path(temporary) / "character.o3d"
            bpy.ops.object.select_all(action="DESELECT")
            result.mesh.select_set(True)
            bpy.context.view_layer.objects.active = result.mesh
            addon.o3d_io.io_o3d_export.do_export(
                str(filepath), bpy.context, Matrix.Identity(4), True, 7, True,
            )
            with open(filepath, "rb") as handle:
                imported = addon.o3d_io.o3dconvert.import_o3d(handle.read())
            bone_names = {name for name, _ in imported[4]}
            assert set(rig.CANONICAL_NAMES).issubset(bone_names)
            assert 0 < len(imported[1])
            # Independent expected normalized source weights, replicated on each seam.
            expected = {
                0: {"Main": 2 / 3, "Hip": 1 / 3}, 1: {"Main": 1.0},
                2: {"Head": 1.0}, 3: {"OA_L": 1.0}, 4: {"UA_L": 1.0},
                5: {"Hand_L": 1.0}, 6: {"OA_R": 1.0}, 7: {"UA_R": 1.0},
                8: {"Hand_R": 1.0}, 9: {"Hip": 0.5, "OS_L": 0.5},
                10: {"US_L": 1.0}, 11: {"OS_R": 1.0}, 12: {"US_R": 1.0},
            }
            actual = {}
            for name, entries in imported[4]:
                for index, weight in entries:
                    actual.setdefault(index, {})[name] = weight
            world = [result.mesh.matrix_world @ vertex.co for vertex in result.mesh.data.vertices]
            for index, vertex in enumerate(imported[1]):
                point = (vertex[0][0], vertex[0][2], vertex[0][1])
                source_index = min(range(len(world)), key=lambda i: sum((world[i][j] - point[j]) ** 2 for j in range(3)))
                assert set(actual[index]) == set(expected[source_index])
                assert all(abs(actual[index][name] - weight) < 1e-6
                           for name, weight in expected[source_index].items())
            reconstructed = addon.o3d_io.io_o3d_import.do_import(str(filepath), bpy.context, False, "", False)
            assert len(reconstructed) == 2
            imported_mesh = next(obj for obj in reconstructed if obj.type == "MESH")
            try:
                for vertex in imported_mesh.data.vertices:
                    groups = {imported_mesh.vertex_groups[entry.group].name: entry.weight
                              for entry in vertex.groups if entry.weight > 0}
                    assert set(groups) == set(actual[vertex.index])
                    assert all(abs(weight - actual[vertex.index][name]) < 1e-6 for name, weight in groups.items())
            finally:
                _remove_objects(imported_mesh.parent, imported_mesh)
            assert all(index < 65535 for _, influences in imported[4] for index, _ in influences)
            assert all(len(name.encode("cp1252")) <= 255 for name in bone_names)
        blocks = [list(block) for block in result.mesh.data["cfg_data"]]
        assert "[smoothskin]" in [block[0] for block in blocks]
        assert ["[setbone]", "Hand_L", "-13"] in blocks
    finally:
        _remove_objects(mesh, source, result.mesh if result else None, result.armature if result else None)


def assert_conversion_rollback_and_source_delete(addon: ModuleType) -> None:
    rig = _rig(addon)
    mesh, source = _mmd_character()
    extra = mesh.vertex_groups.new(name="TailControl")
    extra.add([0], 1, "REPLACE")
    shared_data = source.data
    shared = source.copy()
    shared.data = shared_data
    bpy.context.scene.collection.objects.link(shared)
    root = bpy.data.objects.new("MMD_Root", None)
    bpy.context.scene.collection.objects.link(root)
    source.parent = root
    root["mmd_type"] = "ROOT"
    before_objects = set(bpy.data.objects)
    before_texts = set(bpy.data.texts)
    original_delete = rig._remove_source_rig
    result = None
    try:
        def fail_delete(_source):
            raise RuntimeError("forced source deletion failure")

        rig._remove_source_rig = fail_delete
        try:
            rig.convert(mesh, source, rig.ConversionOptions(
                keep_extra_bones=True, delete_source_rig=True,
            ))
        except RuntimeError as error:
            assert str(error) == "forced source deletion failure"
        else:
            raise AssertionError("forced rollback did not fail")
        assert set(bpy.data.objects) == before_objects
        assert set(bpy.data.texts) == before_texts
        assert mesh.get("mmd_converted") is None
        assert shared.data == shared_data
    finally:
        rig._remove_source_rig = original_delete
        _remove_objects(mesh, source, shared, root)

    mesh, source = _mmd_character()
    shared_data = source.data
    shared = source.copy()
    shared.data = shared_data
    bpy.context.scene.collection.objects.link(shared)
    root = bpy.data.objects.new("MMD_Root", None)
    bpy.context.scene.collection.objects.link(root)
    source.parent = root
    root["mmd_type"] = "ROOT"
    result = None
    source_name = source.name
    root_name = root.name
    try:
        result = rig.convert(mesh, source, rig.ConversionOptions(delete_source_rig=True))
        assert bpy.data.objects.get(source_name) is None
        assert shared.name in bpy.data.objects
        assert shared.data == shared_data
        assert bpy.data.objects.get(root_name) is None
        assert result.mesh.name in bpy.data.objects
    finally:
        _remove_objects(mesh, shared, root, result.mesh if result else None,
                        result.armature if result else None)


def assert_conversion_runtime_validation(addon: ModuleType) -> None:
    rig = _rig(addon)
    mesh, source = _mmd_character()
    invalid = _armature_with_bones(
        "Invalid Template",
        [("Main", (0, 0, 0), (0, 0, 1), None),
         ("漢", (0, 0, 1), (0, 0, 2), "Main")],
    )
    weighted = mesh.vertex_groups.new(name="漢")
    weighted.add([0], 1, "REPLACE")
    before_objects = set(bpy.data.objects)
    try:
        try:
            rig.convert(mesh, source, rig.ConversionOptions(
                rig_mode="TEMPLATE", template_armature=invalid,
            ))
        except ValueError as error:
            assert "CP1252" in str(error)
        else:
            raise AssertionError("non-CP1252 template bone was accepted")
        assert set(bpy.data.objects) == before_objects
        assert mesh.get("mmd_converted") is None
    finally:
        _remove_objects(mesh, source, invalid)
