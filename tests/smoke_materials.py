"""Material and shader wrapper checks."""
import os
import tempfile
from pathlib import Path
from types import ModuleType

import bpy
from bpy_extras import node_shader_utils
from mathutils import Matrix


def assert_material_compatibility(addon: ModuleType) -> None:
    material = bpy.data.materials.new("O3D Alpha Material")
    addon.o3d_io.io_o3d_import.blender_compat.set_material_alpha_mode(
        material, "HASHED"
    )
    assert material.surface_render_method == "DITHERED"


def assert_spline_material_compatibility(addon: ModuleType) -> None:
    mesh = bpy.data.meshes.new("O3D Spline Material Mesh")
    addon.o3d_io.io_omsi_spline.generate_materials(
        mesh,
        "missing.sli",
        {0: {"diffuse": "missing.png", "alpha": 1}},
    )
    assert len(mesh.materials) == 1
    assert (
        addon.o3d_io.blender_compat.get_material_alpha_mode(mesh.materials[0])
        == "HASHED"
    )
    solid = addon.o3d_io.blender_compat.create_solid_material(
        (0.8, 0.8, 0.8, 1.0)
    )
    assert solid.surface_render_method == "DITHERED"


def assert_solid_material_compatibility(addon: ModuleType) -> None:
    material = addon.o3d_io.blender_compat.create_solid_material((0.15, 0.5, 0.15, 1.0))
    assert material.surface_render_method == "DITHERED"
    assert material.use_backface_culling
    wrapper = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=True)
    assert abs(wrapper.alpha - 1.0) < 0.001
    translucent = addon.o3d_io.blender_compat.create_solid_material(
        (0.0, 0.0, 0.0), alpha=0.25
    )
    assert abs(
        node_shader_utils.PrincipledBSDFWrapper(translucent, is_readonly=True).alpha - 0.25
    ) < 0.001


def assert_layered_material_compatibility(addon: ModuleType) -> None:
    material = bpy.data.materials.new("O3D Layered Material")
    addon.o3d_io.blender_compat.enable_material_nodes(material)
    wrapper = addon.o3d_io.layered_shader.LayeredBSDFWrapper(material, is_readonly=False)
    wrapper.base_color = (0.5, 0.5, 0.5)
    wrapper.specular = 0.1
    wrapper.roughness = 0.7
    wrapper.base_color_n_textures = 3
    assert len(wrapper.base_color_textures) == 3
    assert wrapper.base_color_textures[-1][1] is None
    assert all(texture[0] is not None for texture in wrapper.base_color_textures)
    wrapper.base_color_n_textures = 1
    assert len(wrapper.base_color_textures) == 1


def assert_layered_material_export_rejected(addon: ModuleType) -> None:
    """Ordinary O3D export rejects layered diffuse stacks instead of dropping layers."""
    mesh = bpy.data.meshes.new("O3D Layered Export Mesh")
    mesh.from_pydata(
        [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)],
        [], [(0, 1, 2)],
    )
    material = bpy.data.materials.new("O3D Layered Export Material")
    addon.o3d_io.blender_compat.enable_material_nodes(material)
    wrapper = addon.o3d_io.layered_shader.LayeredBSDFWrapper(material, is_readonly=False)
    wrapper.base_color_n_textures = 2
    mesh.materials.append(material)
    source = bpy.data.objects.new("O3D Layered Export Object", mesh)
    bpy.context.scene.collection.objects.link(source)
    bpy.ops.object.select_all(action="DESELECT")
    source.select_set(True)
    try:
        with tempfile.TemporaryDirectory(prefix="blender-o3d-io-layered-export-") as temporary:
            filepath = Path(temporary) / "layered.o3d"
            try:
                addon.o3d_io.io_o3d_export.do_export(
                    str(filepath), bpy.context, Matrix.Identity(4), True, 7, True
                )
            except ValueError as error:
                assert "layered" in str(error).lower(), error
            else:
                raise AssertionError("layered material export was accepted")
            assert not filepath.exists()
    finally:
        bpy.data.objects.remove(source, do_unlink=True)




def assert_terrain_material_compatibility(addon: ModuleType) -> None:
    mesh = bpy.data.meshes.new("O3D Terrain Mesh")
    with tempfile.TemporaryDirectory(prefix="blender-o3d-io-terrain-") as temporary:
        directory = Path(temporary)
        splat_dir = directory / "texture" / "map"
        splat_dir.mkdir(parents=True)
        map_path = directory / "tile.map"
        (splat_dir / "tile.map.1.dds").touch()
        global_cfg = {
            "[groundtex]": [
                ["grass.bmp", "", "", "10"],
                ["gravel.bmp", "", "", "10"],
            ]
        }
        addon.o3d_io.io_omsi_tile.generate_terrain_materials(
            mesh, str(map_path), global_cfg
        )
    assert len(mesh.materials) == 1
    assert mesh.materials[0].use_backface_culling
    assert any(
        node.bl_idname == "ShaderNodeMixRGB"
        for node in mesh.materials[0].node_tree.nodes
    )


def assert_import_preserves_material_slots(addon: ModuleType) -> None:
    with tempfile.TemporaryDirectory(prefix="blender-o3d-io-slots-") as temporary:
        directory = Path(temporary)
        texture_dir = directory / "texture"
        for name in ("present.png", "a/panel.png", "b/panel.png"):
            path = texture_dir / name
            path.parent.mkdir(parents=True, exist_ok=True)
            image = bpy.data.images.new(name, width=1, height=1)
            image.filepath_raw = str(path)
            image.file_format = "PNG"
            image.save()
            bpy.data.images.remove(image)

        names = ("present.png", "present.png", "missing.png", "missing.png",
                 "a/panel.png", "b/panel.png", "")
        material_ids = [3, 0, 5, 1, 2, 4, 6]
        vertices = []
        triangles = []
        for index, material_id in enumerate(material_ids):
            start = len(vertices)
            vertices.extend([
                (index * 2, 0, 0, 0, 0, 1, 0, 0),
                (index * 2 + 1, 0, 0, 0, 0, 1, 1, 0),
                (index * 2, 1, 0, 0, 0, 1, 0, 1),
            ])
            triangles.append((start, start + 1, start + 2, material_id))
        materials = [(1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, name) for name in names]
        with (directory / "slots.o3d").open("wb") as file:
            addon.o3d_io.o3dconvert.export_o3d(
                file, vertices, triangles, materials, [], None
            )
        cfg_path = directory / "slots.sco"
        cfg_path.write_text(
            "[mesh]\nslots.o3d\n\n"
            "[matl]\npresent.png\n0\n[matl_alpha]\n1\n\n"
            "[matl]\npresent.png\n1\n[matl_alpha]\n2\n\n"
            "[matl]\nmissing.png\n0\n[matl_alpha]\n1\n\n"
            "[matl]\nmissing.png\n1\n[matl_alpha]\n2\n\n",
            encoding="cp1252",
        )
        imported = addon.o3d_io.io_o3d_import.do_import(
            str(cfg_path), bpy.context, False, "", False
        )
        try:
            mesh = imported[0].data
            assert len(mesh.materials) == 7
            assert len({material.as_pointer() for material in mesh.materials}) == 7
            assert [face.material_index for face in mesh.polygons] == material_ids
            images = []
            for index, material in enumerate(mesh.materials):
                wrapper = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=True)
                image = wrapper.base_color_texture.image if wrapper.base_color_texture else None
                if index == 6:
                    assert image is None
                else:
                    assert image is not None, (index, names[index])
                    images.append(image)
            assert len({image.as_pointer() for image in images}) == 6
            for image in (images[0], images[1], images[4], images[5]):
                assert len(image.pixels) == 4
                assert image.has_data
            assert not images[2].has_data and not images[3].has_data
            assert images[2].filepath == images[3].filepath == "missing.png"
            assert Path(images[4].filepath).parent.name == "a"
            assert Path(images[5].filepath).parent.name == "b"
            assert [addon.o3d_io.blender_compat.get_material_alpha_mode(material)
                    for material in mesh.materials[:4]] == ["CLIP", "HASHED", "CLIP", "HASHED"]
            assert mesh.materials[2]["type"] == "[matl]"
            blend_path = directory / "slots.blend"
            bpy.data.libraries.write(str(blend_path), {mesh})
            with bpy.data.libraries.load(str(blend_path)) as (source, target):
                target.meshes = source.meshes
            saved_mesh = target.meshes[0]
            assert len(saved_mesh.materials) == 7
            assert [face.material_index for face in saved_mesh.polygons] == material_ids
            saved_images = [
                node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=True)
                .base_color_texture.image
                for material in saved_mesh.materials[:6]
            ]
            assert len({image.as_pointer() for image in saved_images}) == 6
            assert saved_images[2].filepath == saved_images[3].filepath == "missing.png"
        finally:
            for obj in imported:
                bpy.data.objects.remove(obj, do_unlink=True)


def assert_import_preserves_validated_face_materials(addon: ModuleType) -> None:
    with tempfile.TemporaryDirectory(prefix="blender-o3d-io-face-slots-") as temporary:
        path = Path(temporary) / "faces.o3d"
        vertices = [
            (0, 0, 0, 0, 0, 1, 0, 0),
            (1, 0, 0, 0, 0, 1, 1, 0),
            (0, 1, 0, 0, 0, 1, 0, 1),
            (1, 1, 0, 0, 0, 1, 1, 1),
        ]
        materials = [(1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, "")] * 3
        with path.open("wb") as file:
            addon.o3d_io.o3dconvert.export_o3d(
                file, vertices, [(0, 0, 0, 0), (0, 1, 2, 1), (1, 3, 2, 2)],
                materials, [], None,
            )
        imported = addon.o3d_io.io_o3d_import.do_import(
            str(path), bpy.context, False, "", False
        )
        try:
            mesh = imported[0].data
            assert len(mesh.materials) == 3
            assert [face.material_index for face in mesh.polygons] == [1, 2]
        finally:
            for obj in imported:
                bpy.data.objects.remove(obj, do_unlink=True)


def assert_bump_map(addon: ModuleType) -> None:
    material = bpy.data.materials.new("O3D Bump Material")
    addon.o3d_io.blender_compat.enable_material_nodes(material)
    wrapper = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=False)
    image = bpy.data.images.new("bump.png", width=1, height=1)
    addon.o3d_io.blender_compat.apply_bump_map(wrapper, image, 0.5)
    normal_link = wrapper.node_principled_bsdf.inputs["Normal"].links[0]
    bump_node = normal_link.from_node
    assert bump_node.bl_idname == "ShaderNodeBump"
    assert abs(bump_node.inputs["Strength"].default_value - 0.5) < 0.001
    assert bump_node.inputs["Height"].links[0].from_node.image is image
    found_image, found_strength = addon.o3d_io.blender_compat.find_bump_map(wrapper)
    assert found_image is image
    assert abs(found_strength - 0.5) < 0.001
    assert all(
        node.bl_idname != "ShaderNodeNormalMap" for node in material.node_tree.nodes
    )
