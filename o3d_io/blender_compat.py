from collections.abc import Sequence
from typing import Literal, cast

import bpy


AlphaMode = Literal["OPAQUE", "CLIP", "HASHED", "BLEND"]


def prepare_import_mesh(
    mesh: bpy.types.Mesh,
    normals: Sequence[Sequence[float]],
    use_custom_normals: bool,
) -> None:
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    if use_custom_normals:
        create_normals = getattr(mesh, "create_normals_split", None)
        if create_normals is not None:
            create_normals()
        mesh.normals_split_custom_set_from_vertices(normals)
        if hasattr(mesh, "use_auto_smooth"):
            mesh.use_auto_smooth = True
    if bpy.app.version < (2, 80):
        mesh.update(calc_tessface=True)
    else:
        mesh.update()
        mesh.calc_loop_triangles()
    calculate_normals = getattr(mesh, "calc_normals_split", None)
    if calculate_normals is not None:
        calculate_normals()


def prepare_export_mesh(
    mesh: bpy.types.Mesh,
    use_custom_normals: bool,
) -> None:
    if use_custom_normals and mesh.has_custom_normals:
        if hasattr(mesh, "use_auto_smooth"):
            mesh.use_auto_smooth = True
    else:
        free_normals = getattr(mesh, "free_normals_split", None)
        if free_normals is not None:
            free_normals()
        elif mesh.has_custom_normals:
            mesh.normals_split_custom_set([(0.0, 0.0, 0.0)] * len(mesh.loops))
    calculate_normals = getattr(mesh, "calc_normals_split", None)
    if calculate_normals is not None:
        calculate_normals()
    mesh.calc_loop_triangles()


def set_material_alpha_mode(
    material: bpy.types.Material,
    mode: AlphaMode,
) -> None:
    if mode not in {"OPAQUE", "CLIP", "HASHED", "BLEND"}:
        raise ValueError(f"Unsupported material alpha mode: {mode}")
    material["o3d_alpha_mode"] = mode
    if hasattr(material, "surface_render_method"):
        material.surface_render_method = "BLENDED" if mode == "BLEND" else "DITHERED"
        if hasattr(material, "use_transparency_overlap"):
            material.use_transparency_overlap = False
        return
    material.blend_method = mode
    if hasattr(material, "shadow_method"):
        material.shadow_method = mode


def get_material_alpha_mode(material: bpy.types.Material) -> AlphaMode:
    saved_mode = material.get("o3d_alpha_mode")
    valid_modes = {"OPAQUE", "CLIP", "HASHED", "BLEND"}
    if saved_mode in valid_modes:
        return cast(AlphaMode, saved_mode)
    if getattr(material, "surface_render_method", None) == "BLENDED":
        return "BLEND"
    legacy_mode = getattr(material, "blend_method", "HASHED")
    if legacy_mode in valid_modes:
        return cast(AlphaMode, legacy_mode)
    return "HASHED"


def create_solid_material(
    diffuse: Sequence[float],
    specular: Sequence[float] = (0.0, 0.0, 0.0),
    roughness: float = 1.0,
) -> bpy.types.Material:
    if len(diffuse) < 3 or len(specular) < 3:
        raise ValueError("Material colors require at least three channels")
    material = bpy.data.materials.new("Solid Material")
    material.use_nodes = True
    if bpy.app.version >= (4, 0):
        from bpy_extras import node_shader_utils
    else:
        from . import o3d_node_shader_utils as node_shader_utils
    wrapper = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=False)
    wrapper.base_color = tuple(diffuse[:3])
    wrapper.specular = sum(specular[:3]) / 3
    wrapper.roughness = roughness
    set_material_alpha_mode(material, "HASHED")
    return material
