"""Material and shader wrapper checks."""
import os
import tempfile
from pathlib import Path
from types import ModuleType

import bpy
from bpy_extras import node_shader_utils


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
