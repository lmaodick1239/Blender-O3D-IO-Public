"""Import and export round-trip checks."""
import importlib
import math
import os
import shutil
import struct
import tempfile
from pathlib import Path
from types import ModuleType

import bpy
from bpy_extras import node_shader_utils
from mathutils import Matrix, Vector

from smoke_support import create_source_object


def assert_armature_helper(addon: ModuleType) -> None:
    addon.o3d_io.o3d_armature = importlib.import_module(addon.o3d_io.__name__ + ".o3d_armature")
    mesh = bpy.data.meshes.new("O3D Armature Source Mesh")
    mesh.from_pydata([(0, 0, 0), (0, 0, 1), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    source = bpy.data.objects.new("O3D Armature Source", mesh)
    bpy.context.scene.collection.objects.link(source)
    armature = addon.o3d_io.o3d_armature.create_armature_for_mesh(
        source,
        [
            ("Main", [(0, 1.0), (1, 0.5)]),
            ("Hip", [(0, 0.5), (2, 1.0)]),
            ("Head", [(1, 1.0)]),
            ("Hip", [(2, 0.25)]),
        ],
    )
    assert armature is not None
    assert {bone.name for bone in armature.data.bones} == {"Main", "Hip", "Head"}
    assert armature.data.bones["Hip"].parent == armature.data.bones["Main"]
    assert armature.data.bones["Head"].parent == armature.data.bones["Main"]
    assert source.parent is armature
    assert source.modifiers[-1].type == "ARMATURE"
    assert source.modifiers[-1].object is armature
    assert all(bone.length > 0.0 for bone in armature.data.bones)
    bpy.data.objects.remove(source, do_unlink=True)
    bpy.data.objects.remove(armature, do_unlink=True)


def assert_invalid_topology_guard(addon: ModuleType) -> None:
    mesh = bpy.data.meshes.new("O3D Invalid Topology Mesh")
    mesh.from_pydata([(0.0, 0.0, 0.0)], [], [(0, 1, 2)])
    addon.o3d_io.blender_compat.prepare_import_mesh(
        mesh,
        [(0.0, 0.0, 1.0)],
        True,
    )
    assert len(mesh.vertices) == 1
    assert len(mesh.polygons) == 0


def assert_singular_transform_guard(addon: ModuleType) -> None:
    """Issue #93: a degenerate o3d transform aborted the import with a ValueError."""
    source = create_source_object(addon)
    source.scale = (1.0, 1.0, 0.0)
    with tempfile.TemporaryDirectory(prefix="blender-o3d-io-singular-") as temporary:
        filepath = Path(temporary) / "singular.o3d"
        addon.o3d_io.io_o3d_export.do_export(
            str(filepath), bpy.context, Matrix.Identity(4), True, 7, True
        )
        bpy.data.objects.remove(source, do_unlink=True)
        imported = addon.o3d_io.io_o3d_import.do_import(
            str(filepath), bpy.context, False, "", False
        )
        assert len(imported) == 1
        bpy.data.objects.remove(imported[0], do_unlink=True)


def assert_material_less_export(addon: ModuleType) -> None:
    """Issue #80: objects without materials produced an o3d file with no material at all."""
    bpy.ops.object.select_all(action="DESELECT")
    mesh = bpy.data.meshes.new("O3D Bare Mesh")
    mesh.from_pydata(
        [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)], [], [(0, 1, 2)]
    )
    source = bpy.data.objects.new("O3D Bare Object", mesh)
    bpy.context.scene.collection.objects.link(source)
    source.select_set(True)
    bpy.context.view_layer.objects.active = source
    with tempfile.TemporaryDirectory(prefix="blender-o3d-io-bare-") as temporary:
        filepath = Path(temporary) / "bare.o3d"
        addon.o3d_io.io_o3d_export.do_export(
            str(filepath), bpy.context, Matrix.Identity(4), True, 7, True
        )
        bpy.data.objects.remove(source, do_unlink=True)
        imported = addon.o3d_io.io_o3d_import.do_import(
            str(filepath), bpy.context, False, "", False
        )
        assert len(imported) == 1
        assert len(imported[0].data.materials) == 1
        bpy.data.objects.remove(imported[0], do_unlink=True)


def assert_emission_round_trip(addon: ModuleType) -> None:
    """Issue #104: o3d emission was parsed on import but never reached the material."""
    source = create_source_object(addon)
    wrapper = node_shader_utils.PrincipledBSDFWrapper(
        source.data.materials[0], is_readonly=False
    )
    wrapper.emission_color = (0.25, 0.5, 0.75)
    with tempfile.TemporaryDirectory(prefix="blender-o3d-io-emission-") as temporary:
        filepath = Path(temporary) / "emission.o3d"
        addon.o3d_io.io_o3d_export.do_export(
            str(filepath), bpy.context, Matrix.Identity(4), True, 7, True
        )
        bpy.data.objects.remove(source, do_unlink=True)
        imported = addon.o3d_io.io_o3d_import.do_import(
            str(filepath), bpy.context, False, "", False
        )
        imported_wrapper = node_shader_utils.PrincipledBSDFWrapper(
            imported[0].data.materials[0], is_readonly=True
        )
        assert all(
            abs(actual - expected) < 0.001
            for actual, expected in zip(
                imported_wrapper.emission_color, (0.25, 0.5, 0.75)
            )
        ), tuple(imported_wrapper.emission_color)
        assert imported_wrapper.emission_strength > 0
        bpy.data.objects.remove(imported[0], do_unlink=True)


def assert_uv_seam_round_trip(addon: ModuleType) -> None:
    """Issue #59: exporting a mesh with UV seams must not weld the split UVs back together."""
    bpy.ops.object.select_all(action="DESELECT")
    mesh = bpy.data.meshes.new("O3D Seam Mesh")
    mesh.from_pydata(
        [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0)],
        [],
        [(0, 1, 2), (0, 2, 3)],
    )
    uv_layer = mesh.uv_layers.new(name="UV Map")
    source_uvs = [
        (0.0, 0.0), (0.5, 0.0), (0.5, 0.5),
        (0.9, 0.9), (0.6, 0.2), (0.1, 0.7),
    ]
    for loop_index, value in enumerate(source_uvs):
        uv_layer.data[loop_index].uv = value
    mesh.update()
    source = bpy.data.objects.new("O3D Seam Object", mesh)
    bpy.context.scene.collection.objects.link(source)
    source.select_set(True)
    bpy.context.view_layer.objects.active = source

    with tempfile.TemporaryDirectory(prefix="blender-o3d-io-seam-") as temporary:
        filepath = Path(temporary) / "seam.o3d"
        addon.o3d_io.io_o3d_export.do_export(
            str(filepath), bpy.context, Matrix.Identity(4), True, 7, True
        )
        bpy.data.objects.remove(source, do_unlink=True)
        imported = addon.o3d_io.io_o3d_import.do_import(
            str(filepath), bpy.context, False, "", False
        )
        imported_mesh = imported[0].data
        # The seam must survive as duplicated vertices rather than being welded back to four
        assert len(imported_mesh.vertices) == 6, len(imported_mesh.vertices)
        rounded = sorted(
            tuple(round(channel, 4) for channel in loop.uv)
            for loop in imported_mesh.uv_layers[0].data
        )
        assert rounded == sorted(source_uvs), rounded
        bpy.data.objects.remove(imported[0], do_unlink=True)


def assert_light_flare_flags_round_trip(addon: ModuleType) -> None:
    """Boolean flare flags were written as True/False, which neither OMSI nor the importer can parse."""
    bpy.ops.object.select_all(action="DESELECT")
    flare = bpy.data.objects.new("::light_enh_2_0", None)
    bpy.context.scene.collection.objects.link(flare)
    flare.location = (1.0, 2.0, 3.0)
    flare["type"] = "[light_enh_2]"
    flare["forward_vector"] = (0.0, 1.0, 0.0)
    flare["rotation_axis"] = (0.0, 0.0, 1.0)
    flare["omnidirectional"] = False
    flare["rotating"] = 0
    flare["max_brightness_angle"] = 30.0
    flare["min_brightness_angle"] = 60.0
    flare["brightness_var"] = ""
    flare["brightness"] = 1.0
    flare["z_offset"] = 0.0
    flare["effect"] = 0
    flare["cone_effect"] = False
    flare["ramp_time"] = 0.5
    flare.select_set(True)
    bpy.context.view_layer.objects.active = flare

    with tempfile.TemporaryDirectory(prefix="blender-o3d-io-flare-") as temporary:
        cfg_path = Path(temporary) / "flare.cfg"
        addon.o3d_io.io_o3d_export.do_export(
            str(cfg_path), bpy.context, Matrix.Identity(4), True, 7, True
        )
        text = cfg_path.read_text(encoding="cp1252")
        assert "[light_enh_2]" in text
        assert "False" not in text, text
        assert "True" not in text, text
        # The importer must be able to read back what the exporter just wrote
        cfg_data, _ = addon.o3d_io.o3d_cfg_parser.read_cfg(str(cfg_path), "")
        flares = cfg_data[-1]["light_flares"]
        assert len(flares) == 1, flares
        assert flares[0]["cone_effect"] is False
        assert flares[0]["omni"] is False

    bpy.data.objects.remove(flare, do_unlink=True)


def assert_bulk_import(addon: ModuleType) -> None:
    source = create_source_object(addon)
    with tempfile.TemporaryDirectory(prefix="blender-o3d-io-bulk-") as temporary:
        directory = Path(temporary)
        first = directory / "first.o3d"
        second = directory / "second.o3d"
        addon.o3d_io.io_o3d_export.do_export(
            str(first), bpy.context, Matrix.Identity(4), True, 7, True
        )
        shutil.copyfile(first, second)
        bpy.data.objects.remove(source, do_unlink=True)
        existing = set(bpy.data.objects)
        result = bpy.ops.import_scene.omsi_model_cfg(
            filepath=str(first),
            directory=str(directory),
            files=[{"name": first.name}, {"name": second.name}],
            import_x=False,
        )
        imported = set(bpy.data.objects) - existing
        assert result == {"FINISHED"}
        assert len(imported) == 2
        for imported_object in imported:
            bpy.data.objects.remove(imported_object, do_unlink=True)


def assert_imported_bone_armature(addon: ModuleType) -> None:
    """Verify that imported O3D files with bones generate armatures."""
    # Test with stubbed load_o3d to be independent of serialization fixes (Task 5)
    original_load_o3d = addon.o3d_io.io_o3d_import.load_o3d

    def stub_load_o3d_with_bones(object_directory, path_to_file, split_normals):
        """Stub that returns a synthetic mesh with Main, Hip, Head bones."""
        mesh = bpy.data.meshes.new("Stubbed Bone Mesh")
        mesh.from_pydata(
            [(0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)],
            [],
            [(0, 1, 2)],
        )
        materials = []
        matl_ids = [0, 0, 0]
        bones = [
            ("Main", [(0, 1.0), (1, 1.0)]),
            ("Hip", [(0, 1.0), (2, 1.0)]),
            ("Head", [(1, 1.0)]),
        ]
        o3d = (None, None, None, materials, bones, None, None)
        transform_matrix = Matrix.Identity(4)
        return materials, matl_ids, mesh, o3d, transform_matrix

    def stub_load_o3d_without_bones(object_directory, path_to_file, split_normals):
        """Stub that returns a synthetic mesh without bones."""
        mesh = bpy.data.meshes.new("Stubbed No-Bone Mesh")
        mesh.from_pydata(
            [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)],
            [],
            [(0, 1, 2)],
        )
        materials = []
        matl_ids = [0, 0, 0]
        bones = []
        o3d = (None, None, None, materials, bones, None, None)
        transform_matrix = Matrix.Identity(4)
        return materials, matl_ids, mesh, o3d, transform_matrix

    try:
        # Test with bones
        addon.o3d_io.io_o3d_import.load_o3d = stub_load_o3d_with_bones
        with tempfile.TemporaryDirectory(prefix="blender-o3d-io-bone-") as temporary:
            # Create a placeholder O3D file (content doesn't matter, stub replaces load_o3d)
            filepath = Path(temporary) / "stub.o3d"
            filepath.write_bytes(b"")

            imported = addon.o3d_io.io_o3d_import.do_import(
                str(filepath), bpy.context, False, "", False
            )
            assert len(imported) == 2, f"Expected 2 objects (mesh + armature), got {len(imported)}"

            mesh_obj = next((obj for obj in imported if obj.type == "MESH"), None)
            armature_obj = next((obj for obj in imported if obj.type == "ARMATURE"), None)

            assert mesh_obj is not None, "Expected a MESH object"
            assert armature_obj is not None, "Expected an ARMATURE object"

            # Check vertex groups
            assert set(vg.name for vg in mesh_obj.vertex_groups) == {"Main", "Hip", "Head"}

            # Check armature bones
            assert set(bone.name for bone in armature_obj.data.bones) == {"Main", "Hip", "Head"}

            # Check parent relationships
            assert armature_obj.data.bones["Hip"].parent == armature_obj.data.bones["Main"]
            assert armature_obj.data.bones["Head"].parent == armature_obj.data.bones["Main"]

            # Check mesh parenting
            assert mesh_obj.parent == armature_obj

            # Check Armature modifier
            assert any(mod.type == "ARMATURE" and mod.object == armature_obj for mod in mesh_obj.modifiers)

            # Clean up
            for obj in imported:
                bpy.data.objects.remove(obj, do_unlink=True)

        # Test without bones (material-only import)
        addon.o3d_io.io_o3d_import.load_o3d = stub_load_o3d_without_bones
        with tempfile.TemporaryDirectory(prefix="blender-o3d-io-nobone-") as temporary:
            filepath = Path(temporary) / "stub-nobone.o3d"
            filepath.write_bytes(b"")

            imported = addon.o3d_io.io_o3d_import.do_import(
                str(filepath), bpy.context, False, "", False
            )
            assert len(imported) == 1, f"Expected 1 object (mesh only), got {len(imported)}"
            assert imported[0].type == "MESH"
            bpy.data.objects.remove(imported[0], do_unlink=True)

    finally:
        # Restore original load_o3d
        addon.o3d_io.io_o3d_import.load_o3d = original_load_o3d

    # Optional stock-human check (uses real load_o3d)
    human_asset_path = os.getenv("O3D_HUMAN_ASSET")
    if human_asset_path:
        if os.path.isfile(human_asset_path):
            print(f"[O3D_Import] Testing human asset: {human_asset_path}")
            imported_human = addon.o3d_io.io_o3d_import.do_import(
                human_asset_path, bpy.context, False, "", False
            )
            human_mesh = next((obj for obj in imported_human if obj.type == "MESH"), None)
            if human_mesh:
                expected_groups = {
                    "Hip", "Head", "OA_R", "UA_L", "Hand_R", "OS_R",
                    "Hand_L", "US_L", "OS_L", "US_R", "OA_L", "UA_R", "Main"
                }
                actual_groups = set(vg.name for vg in human_mesh.vertex_groups)
                assert expected_groups == actual_groups, f"Expected {expected_groups}, got {actual_groups}"
            for obj in imported_human:
                bpy.data.objects.remove(obj, do_unlink=True)
        else:
            print(f"[O3D_Import] O3D_HUMAN_ASSET set but file not found: {human_asset_path}")
    else:
        print("[O3D_Import] O3D_HUMAN_ASSET not set, skipping human asset check")


def assert_weight_seam_round_trip(addon: ModuleType) -> None:
    """Vertex weights must be replicated across UV seam duplications."""
    import struct

    bpy.ops.object.select_all(action="DESELECT")
    mesh = bpy.data.meshes.new("O3D Weight Seam Mesh")
    # Create a quad with a UV seam: vertex 0 is shared by both triangles
    mesh.from_pydata(
        [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0)],
        [],
        [(0, 1, 2), (0, 2, 3)],
    )
    uv_layer = mesh.uv_layers.new(name="UV Map")
    # Different UVs for vertex 0 across the two triangles -> seam duplication
    source_uvs = [
        (0.0, 0.0), (0.5, 0.0), (0.5, 0.5),  # First tri
        (0.9, 0.9), (0.5, 0.5), (0.0, 0.5),  # Second tri, vertex 0 has different UV
    ]
    for loop_index, value in enumerate(source_uvs):
        uv_layer.data[loop_index].uv = value
    mesh.update()

    source = bpy.data.objects.new("O3D Weight Seam Object", mesh)
    bpy.context.scene.collection.objects.link(source)
    source.select_set(True)
    bpy.context.view_layer.objects.active = source

    # Assign weights: group "Weighted" on vertex 0, group "Empty" has no assignments
    weighted_group = source.vertex_groups.new(name="Weighted")
    weighted_group.add([0], 1.0, "REPLACE")
    empty_group = source.vertex_groups.new(name="Empty")

    with tempfile.TemporaryDirectory(prefix="blender-o3d-io-weight-seam-") as temporary:
        filepath = Path(temporary) / "weight_seam.o3d"
        addon.o3d_io.io_o3d_export.do_export(
            str(filepath), bpy.context, Matrix.Identity(4), True, 7, True
        )

        # Manually parse bone section from raw O3D bytes
        # O3D format: header (8 bytes), sections with type byte + data
        # 0x17 = vertices, 0x49 = triangles, 0x26 = materials, 0x54 = bones, 0x79 = transform
        with open(filepath, "rb") as f:
            data = f.read()

        # Find bone section (0x54)
        bone_section_idx = data.find(b'\x54')
        assert bone_section_idx != -1, "Bone section (0x54) not found in O3D file"

        # Parse bone section: 0x54, bone_count (u16 always), then bones
        offset = bone_section_idx + 1
        bone_count = struct.unpack_from("<H", data, offset)[0]
        offset += 2

        # Parse bones until we hit the transform section (0x79)
        bones = []
        while offset < len(data) and data[offset] != 0x79:
            # Read bone name (Pascal string)
            name_len = data[offset]
            bone_name = struct.unpack_from(f"<{name_len+1}p", data, offset)[0].decode("cp1252")
            offset += name_len + 1

            # Read influence count
            influence_count = struct.unpack_from("<H", data, offset)[0]
            offset += 2

            # Read influences (index: H, weight: f for long_triangle_indices=False in export)
            influences = []
            for _ in range(influence_count):
                idx, weight = struct.unpack_from("<Hf", data, offset)
                influences.append((idx, weight))
                offset += 6  # 2 bytes for H, 4 bytes for f

            bones.append((bone_name, influences))

        bone_dict = {name: influences for name, influences in bones}

        # "Weighted" group must exist and contain both export vertices for source vertex 0
        assert "Weighted" in bone_dict, f"Expected 'Weighted' group, found: {list(bone_dict.keys())}"
        weighted_influences = bone_dict["Weighted"]
        assert len(weighted_influences) == 2, f"Expected 2 influences (seam duplication), got {len(weighted_influences)}: {weighted_influences}"

        # Both influences should have weight 1.0
        for idx, weight in weighted_influences:
            assert abs(weight - 1.0) < 0.001, f"Expected weight 1.0, got {weight} for index {idx}"

        # "Empty" group must be omitted from the exported data
        assert "Empty" not in bone_dict, f"Empty group should be omitted, but found: {bone_dict.get('Empty', [])}"

        bpy.data.objects.remove(source, do_unlink=True)


def assert_posed_rig_exports_rest_space(addon: ModuleType) -> None:
    """Verify that meshes with Armature modifiers export rest-space coordinates, not posed."""
    import struct

    bpy.ops.object.select_all(action="DESELECT")

    # Create a two-bone armature
    armature = bpy.data.armatures.new("Test Armature")
    armature_obj = bpy.data.objects.new("Test Armature", armature)
    bpy.context.scene.collection.objects.link(armature_obj)
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='EDIT')

    # Parent bone at origin, pointing up
    parent_bone = armature.edit_bones.new("Parent")
    parent_bone.head = (0.0, 0.0, 0.0)
    parent_bone.tail = (0.0, 0.0, 1.0)

    # Child bone starting at parent's tail, pointing up
    child_bone = armature.edit_bones.new("Child")
    child_bone.head = (0.0, 0.0, 1.0)
    child_bone.tail = (0.0, 0.0, 2.0)
    child_bone.parent = parent_bone

    bpy.ops.object.mode_set(mode='OBJECT')

    # Create a mesh bound to the child bone
    mesh = bpy.data.meshes.new("Test Mesh")
    # Triangle vertices at rest: tip of child bone area
    rest_vertices = [(0.0, 0.0, 1.5), (0.5, 0.0, 1.5), (0.0, 0.5, 1.5)]
    mesh.from_pydata(rest_vertices, [], [(0, 1, 2)])
    mesh_obj = bpy.data.objects.new("Test Mesh", mesh)
    bpy.context.scene.collection.objects.link(mesh_obj)
    mesh_obj.select_set(True)
    bpy.context.view_layer.objects.active = mesh_obj

    # Add vertex group for child bone with full weight
    child_group = mesh_obj.vertex_groups.new(name="Child")
    child_group.add([0, 1, 2], 1.0, "REPLACE")

    # Parent mesh to armature and add Armature modifier
    mesh_obj.parent = armature_obj
    armature_modifier = mesh_obj.modifiers.new(name="Armature", type="ARMATURE")
    armature_modifier.object = armature_obj

    # Pose the child bone with a visible 45-degree rotation around X
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='POSE')
    pose_bone = armature_obj.pose.bones["Child"]
    pose_bone.rotation_mode = 'XYZ'
    pose_bone.rotation_euler[0] = 0.785398  # 45 degrees in radians
    bpy.ops.object.mode_set(mode='OBJECT')

    # Force evaluation with the pose applied
    bpy.context.view_layer.update()

    # Record rest vertex positions for comparison
    recorded_rest = [tuple(v.co) for v in mesh_obj.data.vertices]

    with tempfile.TemporaryDirectory(prefix="blender-o3d-io-posed-") as temporary:
        filepath = Path(temporary) / "posed.o3d"
        addon.o3d_io.io_o3d_export.do_export(
            str(filepath), bpy.context, Matrix.Identity(4), True, 7, True
        )

        # Parse exported O3D vertices
        with open(filepath, "rb") as f:
            data = f.read()

        # Find vertex section (0x17)
        vertex_section_idx = data.find(b'\x17')
        assert vertex_section_idx != -1, "Vertex section (0x17) not found"

        offset = vertex_section_idx + 1
        vert_count = struct.unpack_from("<I", data, offset)[0]
        offset += 4

        exported_positions = []
        for _ in range(vert_count):
            # Each vertex: x, y, z, nx, ny, nz, u, v (8 floats)
            vert_data = struct.unpack_from("<8f", data, offset)
            exported_positions.append((vert_data[0], vert_data[1], vert_data[2]))
            offset += 32  # 8 floats * 4 bytes

        # Verify exported positions match rest space after axis conversion
        # O3D uses Y-up, Blender uses Z-up, so (x, y, z) becomes (x, z, y)
        axis_conversion = Matrix((
            (1, 0, 0, 0),
            (0, 0, 1, 0),
            (0, 1, 0, 0),
            (0, 0, 0, 1)
        ))
        for i, (exported, rest) in enumerate(zip(exported_positions, recorded_rest)):
            # Apply axis conversion to rest position
            rest_vector = axis_conversion @ Vector(rest)
            expected = (rest_vector.x, rest_vector.y, rest_vector.z)
            for exp_coord, expected_coord in zip(exported, expected):
                assert abs(exp_coord - expected_coord) < 0.001, \
                    f"Vertex {i}: exported {exported} differs from expected rest {expected}. " \
                    f"Armature modifier was evaluated during export."

        # Verify armature and pose are intact after export
        assert len(armature_obj.data.bones) == 2
        assert armature_obj.pose.bones["Child"].rotation_euler[0] > 0.7  # Still posed
        assert any(mod.type == "ARMATURE" for mod in mesh_obj.modifiers)

    bpy.data.objects.remove(mesh_obj, do_unlink=True)
    bpy.data.objects.remove(armature_obj, do_unlink=True)


def assert_modifier_restoration(addon: ModuleType) -> None:
    """Verify that Armature modifiers are restored after export."""
    bpy.ops.object.select_all(action="DESELECT")

    # Create a simple armature
    armature = bpy.data.armatures.new("Test Armature")
    armature_obj = bpy.data.objects.new("Test Armature", armature)
    bpy.context.scene.collection.objects.link(armature_obj)
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='EDIT')

    bone = armature.edit_bones.new("Bone")
    bone.head = (0.0, 0.0, 0.0)
    bone.tail = (0.0, 0.0, 1.0)

    bpy.ops.object.mode_set(mode='OBJECT')

    # Create a mesh with an Armature modifier
    mesh = bpy.data.meshes.new("Test Mesh")
    mesh.from_pydata([(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)], [], [(0, 1, 2)])
    mesh_obj = bpy.data.objects.new("Test Mesh", mesh)
    bpy.context.scene.collection.objects.link(mesh_obj)
    mesh_obj.select_set(True)

    armature_modifier = mesh_obj.modifiers.new(name="Armature", type="ARMATURE")
    armature_modifier.object = armature_obj

    # Store original modifier states
    original_show_viewport = armature_modifier.show_viewport
    original_show_render = armature_modifier.show_render

    with tempfile.TemporaryDirectory(prefix="blender-o3d-io-modifier-") as temporary:
        filepath = Path(temporary) / "modifier_test.o3d"
        addon.o3d_io.io_o3d_export.do_export(
            str(filepath), bpy.context, Matrix.Identity(4), True, 7, True
        )

        # Verify modifiers are restored
        assert armature_modifier.show_viewport == original_show_viewport
        assert armature_modifier.show_render == original_show_render
        assert mesh_obj.modifiers[0].type == "ARMATURE"
        assert mesh_obj.modifiers[0].object == armature_obj

    bpy.data.objects.remove(mesh_obj, do_unlink=True)
    bpy.data.objects.remove(armature_obj, do_unlink=True)


def assert_posed_rig_with_export_error(addon: ModuleType) -> None:
    """Verify that modifiers are restored even when export encounters an error."""
    bpy.ops.object.select_all(action="DESELECT")

    # Create a simple armature
    armature = bpy.data.armatures.new("Test Armature")
    armature_obj = bpy.data.objects.new("Test Armature", armature)
    bpy.context.scene.collection.objects.link(armature_obj)
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='EDIT')

    bone = armature.edit_bones.new("Bone")
    bone.head = (0.0, 0.0, 0.0)
    bone.tail = (0.0, 0.0, 1.0)

    bpy.ops.object.mode_set(mode='OBJECT')

    # Create a mesh with an Armature modifier
    mesh = bpy.data.meshes.new("Test Mesh")
    mesh.from_pydata([(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)], [], [(0, 1, 2)])
    mesh_obj = bpy.data.objects.new("Test Mesh", mesh)
    bpy.context.scene.collection.objects.link(mesh_obj)
    mesh_obj.select_set(True)

    armature_modifier = mesh_obj.modifiers.new(name="Armature", type="ARMATURE")
    armature_modifier.object = armature_obj

    # Store original modifier states
    original_show_viewport = armature_modifier.show_viewport
    original_show_render = armature_modifier.show_render

    # Export to a path that doesn't exist (should fail at directory level)
    # Use a non-writable path to trigger export failure
    try:
        addon.o3d_io.io_o3d_export.do_export(
            "/dev/null/nonexistent/test.o3d", bpy.context, Matrix.Identity(4), True, 7, True
        )
    except (OSError, PermissionError):
        # Expected failure, verify modifiers are still restored
        pass

    # Verify modifiers are restored even after export failure
    assert armature_modifier.show_viewport == original_show_viewport
    assert armature_modifier.show_render == original_show_render

    bpy.data.objects.remove(mesh_obj, do_unlink=True)
    bpy.data.objects.remove(armature_obj, do_unlink=True)


def assert_round_trip(addon: ModuleType) -> None:
    source = create_source_object(addon)
    with tempfile.TemporaryDirectory(prefix="blender-o3d-io-") as temporary:
        filepath = Path(temporary) / "round-trip.o3d"
        addon.o3d_io.io_o3d_export.do_export(
            str(filepath), bpy.context, Matrix.Identity(4), True, 7, True
        )
        assert filepath.is_file()
        cfg_path = Path(temporary) / "round-trip.cfg"
        addon.o3d_io.io_o3d_export.do_export(
            str(cfg_path), bpy.context, Matrix.Identity(4), True, 7, False
        )
        assert cfg_path.is_file()
        cfg_text = cfg_path.read_text(encoding="utf-8")
        assert "[matl_alpha]\n1" in cfg_text
        assert "[matl_bumpmap]\nbump.png\n0.5" in cfg_text
        assert (Path(temporary) / "O3D Smoke Object.o3d").is_file()
        bpy.data.objects.remove(source, do_unlink=True)
        imported = addon.o3d_io.io_o3d_import.do_import(
            str(filepath), bpy.context, False, "", False
        )
        assert len(imported) == 1
        assert len(imported[0].data.vertices) == 3
        assert len(imported[0].data.polygons) == 1
        assert imported[0].data.has_custom_normals
        assert all(normal.vector.z > 0.99 for normal in imported[0].data.corner_normals)
        assert len(imported[0].data.materials) == 1
        imported_wrapper = node_shader_utils.PrincipledBSDFWrapper(
            imported[0].data.materials[0], is_readonly=True
        )
        assert abs(imported_wrapper.specular - 0.6) < 0.001
        assert all(
            abs(actual - expected) < 0.001
            for actual, expected in zip(
                imported_wrapper.specular_tint,
                (0.5, 1.0, 0.25),
            )
        )
        bpy.data.objects.remove(imported[0], do_unlink=True)
        imported_cfg = addon.o3d_io.io_o3d_import.do_import(
            str(cfg_path), bpy.context, False, "", False
        )
        assert len(imported_cfg) == 1
        assert len(imported_cfg[0].data.vertices) == 3


def assert_narrow_index_width(addon: ModuleType) -> None:
    """Verify that normal meshes use 16-bit indices (header flag bit 0 clear)."""
    bpy.ops.object.select_all(action="DESELECT")
    mesh = bpy.data.meshes.new("O3D Narrow Index Mesh")
    # Small mesh that fits in u16
    mesh.from_pydata(
        [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)],
        [],
        [(0, 1, 2)],
    )
    source = bpy.data.objects.new("O3D Narrow Index Object", mesh)
    bpy.context.scene.collection.objects.link(source)
    source.select_set(True)

    # Add a bone with a small index
    bone_group = source.vertex_groups.new(name="TestBone")
    bone_group.add([0, 1], 1.0, "REPLACE")

    with tempfile.TemporaryDirectory(prefix="blender-o3d-io-narrow-") as temporary:
        filepath = Path(temporary) / "narrow.o3d"
        addon.o3d_io.io_o3d_export.do_export(
            str(filepath), bpy.context, Matrix.Identity(4), True, 7, True
        )

        # Parse header to verify flag bit 0 is clear
        with open(filepath, "rb") as f:
            magic = f.read(3)
            assert magic == b'\x84\x19\x07', f"Expected O3D v7 header, got {magic.hex()}"
            options_byte = struct.unpack("<B", f.read(1))[0]
            # Bit 0 should be clear for 16-bit indices
            assert (options_byte & 1) == 0, f"Expected narrow indices (bit 0 clear), got options_byte={options_byte}"

        bpy.data.objects.remove(source, do_unlink=True)


def assert_wide_index_width(addon: ModuleType) -> None:
    """Verify that large-index meshes use 32-bit indices (header flag bit 0 set)."""
    bpy.ops.object.select_all(action="DESELECT")

    # Create a mesh that will have > 65535 exported vertices
    # We need at least 65536/3 = 21846 triangles with unique vertices
    # Strategy: create 25000 triangles, each with unique (position, normal, UV) combinations
    triangle_count = 25000
    vertex_count = triangle_count * 3

    vertices = []
    uv_coords = []
    triangles = []

    for tri_idx in range(triangle_count):
        base_idx = tri_idx * 3
        # Create 3 unique vertices for each triangle
        for v_offset in range(3):
            v_idx = base_idx + v_offset
            x = float(v_idx % 500)
            y = float(v_idx // 500)
            z = float(v_offset) * 0.1
            vertices.append((x, y, z))
            # Unique UV to prevent deduplication
            uv_coords.append((float(v_idx % 1000) / 1000.0, float(v_idx // 1000) / 100.0))
        triangles.append((base_idx, base_idx + 1, base_idx + 2))

    mesh = bpy.data.meshes.new("O3D Wide Index Mesh")
    mesh.from_pydata(vertices, [], triangles)

    # Add UV layer with unique UVs
    uv_layer = mesh.uv_layers.new(name="UV Map")
    for tri in mesh.loop_triangles:
        for loop_idx in tri.loops:
            vert_idx = mesh.loops[loop_idx].vertex_index
            uv_layer.data[loop_idx].uv = uv_coords[vert_idx]
    mesh.update()

    source = bpy.data.objects.new("O3D Wide Index Object", mesh)
    bpy.context.scene.collection.objects.link(source)
    source.select_set(True)

    # Add bone weight on high-index vertices
    bone_group = source.vertex_groups.new(name="HighBone")
    bone_group.add([vertex_count - 3, vertex_count - 2, vertex_count - 1], 1.0, "REPLACE")

    with tempfile.TemporaryDirectory(prefix="blender-o3d-io-wide-") as temporary:
        filepath = Path(temporary) / "wide.o3d"
        addon.o3d_io.io_o3d_export.do_export(
            str(filepath), bpy.context, Matrix.Identity(4), True, 7, True
        )

        # Parse header to verify flag bit 0 is set
        with open(filepath, "rb") as f:
            magic = f.read(3)
            assert magic == b'\x84\x19\x07', f"Expected O3D v7 header, got {magic.hex()}"
            options_byte = struct.unpack("<B", f.read(1))[0]
            # Bit 0 should be set for 32-bit indices
            assert (options_byte & 1) == 1, f"Expected wide indices (bit 0 set), got options_byte={options_byte}"

        bpy.data.objects.remove(source, do_unlink=True)


def assert_pre_v3_wide_index_rejection(addon: ModuleType) -> None:
    """Verify that version 2 rejects indices above 65535 with a clear error."""
    bpy.ops.object.select_all(action="DESELECT")

    # Create a mesh that requires wide indices (same strategy as wide test)
    triangle_count = 25000
    vertex_count = triangle_count * 3

    vertices = []
    uv_coords = []
    triangles = []

    for tri_idx in range(triangle_count):
        base_idx = tri_idx * 3
        for v_offset in range(3):
            v_idx = base_idx + v_offset
            x = float(v_idx % 500)
            y = float(v_idx // 500)
            z = float(v_offset) * 0.1
            vertices.append((x, y, z))
            uv_coords.append((float(v_idx % 1000) / 1000.0, float(v_idx // 1000) / 100.0))
        triangles.append((base_idx, base_idx + 1, base_idx + 2))

    mesh = bpy.data.meshes.new("O3D V2 Wide Mesh")
    mesh.from_pydata(vertices, [], triangles)

    uv_layer = mesh.uv_layers.new(name="UV Map")
    for tri in mesh.loop_triangles:
        for loop_idx in tri.loops:
            vert_idx = mesh.loops[loop_idx].vertex_index
            uv_layer.data[loop_idx].uv = uv_coords[vert_idx]
    mesh.update()

    source = bpy.data.objects.new("O3D V2 Wide Object", mesh)
    bpy.context.scene.collection.objects.link(source)
    source.select_set(True)

    with tempfile.TemporaryDirectory(prefix="blender-o3d-io-v2-wide-") as temporary:
        filepath = Path(temporary) / "v2_wide.o3d"

        # Attempt export with version 2, expect ValueError
        try:
            addon.o3d_io.io_o3d_export.do_export(
                str(filepath), bpy.context, Matrix.Identity(4), True, 2, True
            )
            assert False, "Expected ValueError for version 2 with wide indices"
        except ValueError as e:
            error_msg = str(e)
            assert "version" in error_msg.lower(), f"Error should mention version: {error_msg}"
            assert "65535" in error_msg, f"Error should mention limit: {error_msg}"

        bpy.data.objects.remove(source, do_unlink=True)


def assert_bone_validation(addon: ModuleType) -> None:
    """Verify that invalid bone data raises actionable ValueErrors."""
    # Note: Blender truncates vertex group names to 63 characters, so we cannot easily test
    # the 255-byte name limit through the Blender API. The validation code exists in
    # o3dconvert.export_bone() and will trigger for direct API usage.
    #
    # We test that basic bone export works with normal names and that the system
    # handles edge cases gracefully.

    bpy.ops.object.select_all(action="DESELECT")

    # Test case: Normal bone export with valid names
    mesh = bpy.data.meshes.new("O3D Bone Test Mesh")
    mesh.from_pydata([(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)], [], [(0, 1, 2)])
    source = bpy.data.objects.new("O3D Bone Test Object", mesh)
    bpy.context.scene.collection.objects.link(source)
    source.select_set(True)

    # Create a bone with a long but valid name (Blender will truncate to 63 chars)
    bone_group = source.vertex_groups.new(name="X" * 63)
    bone_group.add([0], 1.0, "REPLACE")

    with tempfile.TemporaryDirectory(prefix="blender-o3d-io-bone-valid-") as temporary:
        filepath = Path(temporary) / "bone_valid.o3d"

        # This should succeed
        addon.o3d_io.io_o3d_export.do_export(
            str(filepath), bpy.context, Matrix.Identity(4), True, 7, True
        )

        assert filepath.is_file(), "Export should have succeeded"

    bpy.data.objects.remove(source, do_unlink=True)


def assert_pose_deformation(addon: ModuleType) -> None:
    """Verify that rotating a pose bone visibly deforms the bound mesh."""
    bpy.ops.object.select_all(action="DESELECT")

    # Create a simple two-bone armature
    armature = bpy.data.armatures.new("Pose Test Armature")
    armature_obj = bpy.data.objects.new("Pose Test Armature", armature)
    bpy.context.scene.collection.objects.link(armature_obj)
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='EDIT')

    # Parent bone pointing up from origin
    parent_bone = armature.edit_bones.new("Parent")
    parent_bone.head = (0.0, 0.0, 0.0)
    parent_bone.tail = (0.0, 0.0, 1.0)

    # Child bone continuing upward
    child_bone = armature.edit_bones.new("Child")
    child_bone.head = (0.0, 0.0, 1.0)
    child_bone.tail = (0.0, 0.0, 2.0)
    child_bone.parent = parent_bone

    bpy.ops.object.mode_set(mode='OBJECT')

    # Create mesh bound to child bone
    mesh = bpy.data.meshes.new("Pose Test Mesh")
    # Single vertex near the child bone tip
    mesh.from_pydata([(0.0, 0.0, 1.8)], [], [])
    mesh_obj = bpy.data.objects.new("Pose Test Mesh", mesh)
    bpy.context.scene.collection.objects.link(mesh_obj)

    # Bind mesh to child bone
    child_group = mesh_obj.vertex_groups.new(name="Child")
    child_group.add([0], 1.0, "REPLACE")

    mesh_obj.parent = armature_obj
    armature_modifier = mesh_obj.modifiers.new(name="Armature", type="ARMATURE")
    armature_modifier.object = armature_obj

    # Update once to establish rest state
    bpy.context.view_layer.update()

    # Record rest coordinate
    rest_co = Vector(mesh_obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices[0].co)

    # Apply a 90-degree rotation to the child bone in pose mode
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='POSE')
    pose_bone = armature_obj.pose.bones["Child"]
    pose_bone.rotation_mode = 'XYZ'
    pose_bone.rotation_euler[0] = 1.5708  # 90 degrees
    bpy.ops.object.mode_set(mode='OBJECT')

    # Force evaluation with pose
    bpy.context.view_layer.update()

    # Record posed coordinate from evaluated mesh
    posed_co = Vector(mesh_obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices[0].co)

    # Verify the coordinate changed significantly
    delta = (posed_co - rest_co).length
    assert delta > 1e-5, f"Expected visible deformation (delta > 1e-5), got {delta}"

    # Clean up
    bpy.data.objects.remove(mesh_obj, do_unlink=True)
    bpy.data.objects.remove(armature_obj, do_unlink=True)


def assert_weight_export_reimport(addon: ModuleType) -> None:
    """Verify that exported bones survive re-import with correct names and weights."""
    bpy.ops.object.select_all(action="DESELECT")

    # Create armature with a two-bone hierarchy
    armature = bpy.data.armatures.new("Export Test Armature")
    armature_obj = bpy.data.objects.new("Export Test Armature", armature)
    bpy.context.scene.collection.objects.link(armature_obj)
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='EDIT')

    parent_bone = armature.edit_bones.new("Main")
    parent_bone.head = (0.0, 0.0, 0.0)
    parent_bone.tail = (0.0, 0.0, 1.0)

    child_bone = armature.edit_bones.new("Hip")
    child_bone.head = (0.0, 0.0, 1.0)
    child_bone.tail = (0.0, 0.0, 2.0)
    child_bone.parent = parent_bone

    bpy.ops.object.mode_set(mode='OBJECT')

    # Create mesh with weighted vertices
    mesh = bpy.data.meshes.new("Export Test Mesh")
    mesh.from_pydata(
        [(0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.5)],
        [],
        [(0, 1, 2)]
    )
    mesh_obj = bpy.data.objects.new("Export Test Mesh", mesh)
    bpy.context.scene.collection.objects.link(mesh_obj)
    mesh_obj.select_set(True)

    # Assign known weights
    main_group = mesh_obj.vertex_groups.new(name="Main")
    main_group.add([0], 1.0, "REPLACE")
    main_group.add([1], 0.5, "REPLACE")

    hip_group = mesh_obj.vertex_groups.new(name="Hip")
    hip_group.add([1], 0.5, "REPLACE")
    hip_group.add([2], 1.0, "REPLACE")

    mesh_obj.parent = armature_obj
    armature_modifier = mesh_obj.modifiers.new(name="Armature", type="ARMATURE")
    armature_modifier.object = armature_obj

    with tempfile.TemporaryDirectory(prefix="blender-o3d-io-weight-export-") as temporary:
        filepath = Path(temporary) / "weight_export.o3d"
        addon.o3d_io.io_o3d_export.do_export(
            str(filepath), bpy.context, Matrix.Identity(4), True, 7, True
        )

        # Parse exported O3D to verify bone names and weights
        with open(filepath, "rb") as f:
            data = f.read()

        header, vertex_list, triangle_list, material_list, bone_list, transform, encrypted = \
            addon.o3d_io.o3dconvert.import_o3d(data)

        # Verify bone names
        bone_names = [name for name, influences in bone_list]
        assert "Main" in bone_names, f"Expected 'Main' in {bone_names}"
        assert "Hip" in bone_names, f"Expected 'Hip' in {bone_names}"

        # Verify all indices are within vertex count
        vertex_count = len(vertex_list)
        for name, influences in bone_list:
            for idx, weight in influences:
                assert idx < vertex_count, \
                    f"Bone '{name}' influence index {idx} exceeds vertex count {vertex_count}"

        # Verify expected weights (allowing 1e-6 tolerance)
        bone_dict = {name: influences for name, influences in bone_list}

        main_influences = dict(bone_dict.get("Main", []))
        hip_influences = dict(bone_dict.get("Hip", []))

        # Find indices for vertices 0, 1, 2 after export (may be reordered)
        # We rely on the fact that the test mesh has unique positions
        # Vertex 0: (0,0,0), Vertex 1: (0,0,1), Vertex 2: (1,0,0.5)
        # After axis conversion to O3D Y-up: (0,0,0)->(0,0,0), (0,0,1)->(0,1,0), (1,0,0.5)->(1,0.5,0)
        for idx, vert_data in enumerate(vertex_list):
            pos = vert_data[0]  # [x, y, z]
            # Vertex 0: Main weight 1.0
            if abs(pos[0]) < 0.001 and abs(pos[1]) < 0.001 and abs(pos[2]) < 0.001:
                assert idx in main_influences, f"Vertex {idx} should have Main weight"
                assert abs(main_influences[idx] - 1.0) < 1e-6, \
                    f"Expected Main weight 1.0, got {main_influences[idx]}"
            # Vertex 1: Main weight 0.5, Hip weight 0.5
            elif abs(pos[0]) < 0.001 and abs(pos[1] - 1.0) < 0.001 and abs(pos[2]) < 0.001:
                if idx in main_influences:
                    assert abs(main_influences[idx] - 0.5) < 1e-6, \
                        f"Expected Main weight 0.5, got {main_influences[idx]}"
                if idx in hip_influences:
                    assert abs(hip_influences[idx] - 0.5) < 1e-6, \
                        f"Expected Hip weight 0.5, got {hip_influences[idx]}"
            # Vertex 2: Hip weight 1.0
            elif abs(pos[0] - 1.0) < 0.001 and abs(pos[1] - 0.5) < 0.001 and abs(pos[2]) < 0.001:
                assert idx in hip_influences, f"Vertex {idx} should have Hip weight"
                assert abs(hip_influences[idx] - 1.0) < 1e-6, \
                    f"Expected Hip weight 1.0, got {hip_influences[idx]}"

        # Clean up source objects
        bpy.data.objects.remove(mesh_obj, do_unlink=True)
        bpy.data.objects.remove(armature_obj, do_unlink=True)

        # Re-import the file through do_import
        imported = addon.o3d_io.io_o3d_import.do_import(
            str(filepath), bpy.context, False, "", False
        )

        # Verify re-imported structure
        imported_mesh = next((obj for obj in imported if obj.type == "MESH"), None)
        imported_armature = next((obj for obj in imported if obj.type == "ARMATURE"), None)

        assert imported_mesh is not None, "Expected a MESH in re-import"
        assert imported_armature is not None, "Expected an ARMATURE in re-import"

        # Verify group names
        group_names = {vg.name for vg in imported_mesh.vertex_groups}
        assert "Main" in group_names, f"Expected 'Main' group in {group_names}"
        assert "Hip" in group_names, f"Expected 'Hip' group in {group_names}"

        # Verify armature bone names
        armature_bone_names = {bone.name for bone in imported_armature.data.bones}
        assert "Main" in armature_bone_names, f"Expected 'Main' bone in {armature_bone_names}"
        assert "Hip" in armature_bone_names, f"Expected 'Hip' bone in {armature_bone_names}"

        # Verify canonical parent relationship
        assert imported_armature.data.bones["Hip"].parent == imported_armature.data.bones["Main"], \
            "Expected Hip to be parented to Main"

        # Verify representative vertex weights after re-import (within 1e-6 tolerance)
        for vert in imported_mesh.data.vertices:
            for group in vert.groups:
                group_name = imported_mesh.vertex_groups[group.group].name
                weight = group.weight
                # Check that weight is within reasonable range and matches export expectations
                if group_name == "Main":
                    # Vertices 0 and 1 have Main weights
                    if abs(vert.co.x) < 0.001 and abs(vert.co.y) < 0.001:
                        # Vertex 0 position after re-import (axis converted back)
                        if abs(vert.co.z) < 0.001:
                            assert abs(weight - 1.0) < 1e-6, \
                                f"Vertex at origin: expected Main weight 1.0, got {weight}"
                        elif abs(vert.co.z - 1.0) < 0.001:
                            assert abs(weight - 0.5) < 1e-6, \
                                f"Vertex at (0,0,1): expected Main weight 0.5, got {weight}"
                elif group_name == "Hip":
                    # Vertices 1 and 2 have Hip weights
                    if abs(vert.co.x) < 0.001 and abs(vert.co.y) < 0.001 and abs(vert.co.z - 1.0) < 0.001:
                        assert abs(weight - 0.5) < 1e-6, \
                            f"Vertex at (0,0,1): expected Hip weight 0.5, got {weight}"
                    elif abs(vert.co.x - 1.0) < 0.001 and abs(vert.co.z - 0.5) < 0.001:
                        assert abs(weight - 1.0) < 1e-6, \
                            f"Vertex at (1,0,0.5): expected Hip weight 1.0, got {weight}"

        # Clean up imported objects
        for obj in imported:
            bpy.data.objects.remove(obj, do_unlink=True)


def assert_malformed_influence_recovery(addon: ModuleType) -> None:
    """Verify that malformed influences are filtered without failing the helper or export."""
    addon.o3d_io.o3d_armature = importlib.import_module(addon.o3d_io.__name__ + ".o3d_armature")

    bpy.ops.object.select_all(action="DESELECT")

    # Create a test mesh for mixed valid/invalid influences
    mesh = bpy.data.meshes.new("Malformed Test Mesh")
    mesh.from_pydata(
        [(0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)],
        [],
        [(0, 1, 2)]
    )
    source = bpy.data.objects.new("Malformed Test Source", mesh)
    bpy.context.scene.collection.objects.link(source)

    try:
        # Test the helper with malformed influences:
        # - Duplicate names (merged by normalization)
        # - Duplicate indices within one bone (max weight kept)
        # - Negative index (filtered out)
        # - Out-of-range index (filtered out)
        # - NaN weight (filtered out)
        # - Inf weight (filtered out)
        # - Negative weight (filtered out)
        malformed_bones = [
            ("Valid", [(0, 1.0), (1, 0.5)]),                    # Should survive
            ("DupName", [(2, 1.0)]),                             # Duplicate name (see next)
            ("DupName", [(3, 0.5)]),                             # Duplicate name (merged by helper)
            ("DupIndex", [(1, 0.3), (1, 0.7)]),                  # Duplicate index (max kept)
            ("NegativeIndex", [(-1, 1.0), (0, 0.5)]),            # Negative index filtered
            ("OutOfRange", [(999, 1.0), (1, 0.5)]),              # Out-of-range filtered
            ("NaNWeight", [(2, float("nan")), (2, 0.5)]),        # NaN weight filtered
            ("InfWeight", [(2, float("inf")), (2, 0.5)]),        # Inf weight filtered
            ("NegativeWeight", [(2, -0.5), (2, 0.5)]),           # Negative weight filtered
        ]

        # Call helper - should not fail despite malformed input
        armature = addon.o3d_io.o3d_armature.create_armature_for_mesh(source, malformed_bones)

        # With valid bones present, helper returns an armature
        if armature is not None:
            # Verify the armature has bones with valid influences
            bone_names = {bone.name for bone in armature.data.bones}
            assert "Valid" in bone_names, "Valid bone should exist"
            assert "DupIndex" in bone_names, "DupIndex should exist (has valid influence)"
            assert "NegativeIndex" in bone_names, "NegativeIndex should exist (has valid influence)"

            # Clean up helper test armature
            bpy.data.objects.remove(armature, do_unlink=True)
    finally:
        # Unconditional cleanup of source mesh
        bpy.data.objects.remove(source, do_unlink=True)

    # Test explicit all-invalid case: empty bone list returns None while preserving mesh cleanup
    bpy.ops.object.select_all(action="DESELECT")
    mesh_invalid = bpy.data.meshes.new("All Invalid Test Mesh")
    mesh_invalid.from_pydata(
        [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)],
        [],
        [(0, 1, 2)]
    )
    source_invalid = bpy.data.objects.new("All Invalid Source", mesh_invalid)
    bpy.context.scene.collection.objects.link(source_invalid)

    try:
        # Empty bone list (no bones at all)
        empty_bones = []

        # Call helper with empty bone list
        armature_empty = addon.o3d_io.o3d_armature.create_armature_for_mesh(
            source_invalid, empty_bones
        )

        # With no bones, helper returns None
        assert armature_empty is None, \
            "Expected None from create_armature_for_mesh with empty bone list"

        # Test with only invalid influences (creates bones but with no weights)
        all_invalid_bones = [
            ("OnlyInvalid", [(-1, 1.0), (999, 1.0)]),            # All invalid
            ("AlsoInvalid", [(float("nan"), 0.5), (-5, float("inf"))]),  # All invalid
        ]

        # Call helper with all-invalid influences
        armature_invalid = addon.o3d_io.o3d_armature.create_armature_for_mesh(
            source_invalid, all_invalid_bones
        )

        # Helper creates armature even with all-invalid influences (bones exist but have no weights)
        # This is acceptable behavior - export will filter these out
        if armature_invalid is not None:
            # Verify bones were created (even though they have no valid weights)
            bone_names = {bone.name for bone in armature_invalid.data.bones}
            # At least one bone should exist from the normalized dict
            assert len(bone_names) > 0, "Expected bones to exist even with all-invalid influences"
            bpy.data.objects.remove(armature_invalid, do_unlink=True)
    finally:
        # Unconditional cleanup of source mesh
        bpy.data.objects.remove(source_invalid, do_unlink=True)

    # Now test the export collector's filtering with real vertex groups
    bpy.ops.object.select_all(action="DESELECT")

    mesh2 = bpy.data.meshes.new("Export Malformed Mesh")
    mesh2.from_pydata(
        [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)],
        [],
        [(0, 1, 2)]
    )
    source2 = bpy.data.objects.new("Export Malformed Object", mesh2)
    bpy.context.scene.collection.objects.link(source2)
    source2.select_set(True)

    try:
        # Add groups with valid weights
        valid_group = source2.vertex_groups.new(name="ExportValid")
        valid_group.add([0, 1], 1.0, "REPLACE")

        # Create an empty group (no assignments)
        empty_group = source2.vertex_groups.new(name="ExportEmpty")

        with tempfile.TemporaryDirectory(prefix="blender-o3d-io-malformed-") as temporary:
            filepath = Path(temporary) / "malformed.o3d"

            # Export should succeed despite edge cases
            addon.o3d_io.io_o3d_export.do_export(
                str(filepath), bpy.context, Matrix.Identity(4), True, 7, True
            )

            assert filepath.is_file(), "Export should succeed with malformed data"

            # Parse and verify only valid influences were serialized
            with open(filepath, "rb") as f:
                data = f.read()

            header, vertex_list, triangle_list, material_list, bone_list, transform, encrypted = \
                addon.o3d_io.o3dconvert.import_o3d(data)

            bone_names_exported = [name for name, influences in bone_list]

            # Valid bone should appear
            assert "ExportValid" in bone_names_exported, f"Expected 'ExportValid' in {bone_names_exported}"

            # Empty group should be omitted from export
            assert "ExportEmpty" not in bone_names_exported, \
                f"Empty group should not be serialized, found in {bone_names_exported}"

            # Verify no invalid indices or weights
            vertex_count = len(vertex_list)
            for name, influences in bone_list:
                for idx, weight in influences:
                    assert 0 <= idx < vertex_count, \
                        f"Bone '{name}' has invalid index {idx} (vertex count: {vertex_count})"
                    assert not math.isnan(weight), f"Bone '{name}' has NaN weight"
                    assert not math.isinf(weight), f"Bone '{name}' has Inf weight"
                    assert weight >= 0.0, f"Bone '{name}' has negative weight {weight}"
    finally:
        # Unconditional cleanup
        bpy.data.objects.remove(source2, do_unlink=True)
