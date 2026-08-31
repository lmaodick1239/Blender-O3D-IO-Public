"""Shared helpers for the Blender smoke test."""
import importlib
import sys
from pathlib import Path
from types import ModuleType

import bpy
from bpy_extras import node_shader_utils


def load_addon() -> ModuleType:
    repository = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repository.parent))
    return importlib.import_module(repository.name)


def create_source_object(addon: ModuleType) -> bpy.types.Object:
    bpy.ops.object.select_all(action="DESELECT")
    mesh = bpy.data.meshes.new("O3D Smoke Mesh")
    mesh.from_pydata(
        [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)],
        [],
        [(0, 1, 2)],
    )
    mesh.uv_layers.new(name="UV Map")
    for loop, uv in zip(mesh.loops, ((0.0, 0.0), (1.0, 0.0), (0.0, 1.0))):
        mesh.uv_layers.active.data[loop.index].uv = uv
    mesh.polygons[0].use_smooth = True
    mesh.normals_split_custom_set_from_vertices(
        [(0.0, 0.0, 1.0), (0.0, 0.0, 1.0), (0.0, 0.0, 1.0)]
    )
    material = bpy.data.materials.new("O3D Smoke Material")
    addon.o3d_io.blender_compat.enable_material_nodes(material)
    wrapper = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=False)
    image = bpy.data.images.new("smoke.png", width=1, height=1)
    image.filepath = "smoke.png"
    wrapper.base_color_texture.image = image
    wrapper.alpha_texture.image = image
    wrapper.specular = 0.6
    wrapper.specular_tint = (0.5, 1.0, 0.25)
    bump_image = bpy.data.images.new("bump.png", width=1, height=1)
    bump_image.filepath = "bump.png"
    addon.o3d_io.blender_compat.apply_bump_map(wrapper, bump_image, 0.5)
    addon.o3d_io.blender_compat.set_material_alpha_mode(material, "CLIP")
    mesh.materials.append(material)
    source = bpy.data.objects.new("O3D Smoke Object", mesh)
    bpy.context.scene.collection.objects.link(source)
    source.select_set(True)
    bpy.context.view_layer.objects.active = source
    return source
