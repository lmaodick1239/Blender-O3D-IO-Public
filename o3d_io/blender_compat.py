from collections.abc import Sequence
from typing import Literal, Optional, Tuple, cast

import bpy


AlphaMode = Literal["OPAQUE", "CLIP", "HASHED", "BLEND"]


def shader_utils():
    if bpy.app.version >= (4, 0):
        from bpy_extras import node_shader_utils
    else:
        from . import o3d_node_shader_utils as node_shader_utils
    return node_shader_utils


def principled_wrapper(material: bpy.types.Material, is_readonly: bool = True):
    return shader_utils().PrincipledBSDFWrapper(material, is_readonly=is_readonly)


def enable_material_nodes(material: bpy.types.Material) -> None:
    """
    Gives the material a shader node tree. Blender 5.x always provides one and deprecates use_nodes,
    so the property is only touched when a node tree is actually missing.
    """
    if material.node_tree is not None:
        return
    if hasattr(material, "use_nodes"):
        material.use_nodes = True


def prepare_import_mesh(
    mesh: bpy.types.Mesh,
    normals: Sequence[Sequence[float]],
    use_custom_normals: bool,
) -> None:
    mesh.validate(verbose=False, clean_customdata=True)
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    if use_custom_normals and len(normals) == len(mesh.vertices):
        create_normals = getattr(mesh, "create_normals_split", None)
        if create_normals is not None:
            create_normals()
        mesh.normals_split_custom_set_from_vertices(normals)
        if hasattr(mesh, "use_auto_smooth"):
            mesh.use_auto_smooth = True
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
    alpha: Optional[float] = None,
) -> bpy.types.Material:
    if len(diffuse) < 3 or len(specular) < 3:
        raise ValueError("Material colors require at least three channels")
    material = bpy.data.materials.new("Solid Material")
    enable_material_nodes(material)
    wrapper = principled_wrapper(material, is_readonly=False)
    wrapper.base_color = tuple(diffuse[:3])
    wrapper.specular = sum(specular[:3]) / 3
    wrapper.roughness = roughness
    if alpha is None and len(diffuse) > 3:
        alpha = diffuse[3]
    if alpha is not None:
        wrapper.alpha = alpha
    material.use_backface_culling = True
    set_material_alpha_mode(material, "HASHED")
    return material


def apply_bump_map(
    material_wrapper,
    image: bpy.types.Image,
    strength: float,
) -> None:
    normalmap_texture = material_wrapper.normalmap_texture
    if normalmap_texture is None:
        return
    if hasattr(normalmap_texture, "is_bump_map"):
        normalmap_texture.is_bump_map = True
        normalmap_texture.image = image
        material_wrapper.normalmap_strength = strength
        return

    normalmap_texture.image = image
    image_node = normalmap_texture.node_image
    normalmap_node = material_wrapper.node_normalmap
    principled_node = material_wrapper.node_principled_bsdf
    if image_node is None or normalmap_node is None or principled_node is None:
        return

    node_tree = material_wrapper.material.node_tree
    bump_node = node_tree.nodes.new(type="ShaderNodeBump")
    bump_node.location = normalmap_node.location
    bump_node.inputs["Strength"].default_value = min(max(strength, 0.0), 10.0)
    node_tree.links.new(image_node.outputs["Color"], bump_node.inputs["Height"])
    node_tree.links.new(bump_node.outputs["Normal"], principled_node.inputs["Normal"])
    material_wrapper._textures.pop((normalmap_node, normalmap_node.inputs["Color"]), None)
    node_tree.nodes.remove(normalmap_node)
    material_wrapper._node_normalmap = None


def _linked_image_node(socket) -> Optional[bpy.types.Node]:
    if not socket.is_linked:
        return None
    node = socket.links[0].from_node
    if node.bl_idname == "ShaderNodeTexImage" and node.image is not None:
        return node
    return None


def find_bump_map(
    material_wrapper,
) -> Optional[Tuple[bpy.types.Image, float]]:
    principled_node = material_wrapper.node_principled_bsdf
    if principled_node is None:
        return None
    normal_input = principled_node.inputs["Normal"]
    if not normal_input.is_linked:
        return None

    source_node = normal_input.links[0].from_node
    if source_node.bl_idname == "ShaderNodeBump":
        image_node = _linked_image_node(source_node.inputs["Height"])
    elif source_node.bl_idname == "ShaderNodeNormalMap":
        color_input = source_node.inputs["Color"]
        image_node = _linked_image_node(color_input)
        if image_node is None and color_input.is_linked:
            nested_node = color_input.links[0].from_node
            if nested_node.bl_idname == "ShaderNodeBump":
                image_node = _linked_image_node(nested_node.inputs["Height"])
    else:
        return None

    if image_node is None:
        return None
    return image_node.image, source_node.inputs["Strength"].default_value
