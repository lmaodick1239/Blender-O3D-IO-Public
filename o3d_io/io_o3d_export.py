# ==============================================================================
#  Copyright (c) 2022-2023 Thomas Mathieson.
# ==============================================================================

import os
import json
import time
from contextlib import contextmanager
from io import BytesIO
from math import isfinite

import numpy as np

import bpy
from mathutils import Euler, Matrix, Vector
from . import blender_compat, o3d_cfg_parser, o3dconvert, omsi_paths

from bpy_extras import node_shader_utils


def log(*args):
    print("[O3D_Export]", *args)


def _material_wrapper(material):
    """Keep geometry, embedded materials and CFG extraction on the same shader."""
    outputs = [node for node in material.node_tree.nodes
               if node.bl_idname == 'ShaderNodeOutputMaterial' and node.is_active_output]
    if len(outputs) != 1:
        raise ValueError(f"Unsupported material {material.name!r}: ambiguous active Material Outputs")
    surface = outputs[0].inputs['Surface']
    if not surface.is_linked or surface.links[0].from_node.bl_idname != 'ShaderNodeBsdfPrincipled':
        raise ValueError(f"Unsupported material {material.name!r}: expected direct Principled active surface")
    wrapper = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=True)
    if wrapper.node_out != outputs[0] or wrapper.node_principled_bsdf != surface.links[0].from_node:
        raise ValueError(f"Unsupported material {material.name!r}: ambiguous inactive Principled selection")
    return wrapper


def _material_input(wrapper, name, *, image=False):
    """Resolve only unlinked defaults and direct RGB/Value constants.

    Established CFG image routes keep their independent fallback constants;
    they are never treated as evaluated shader values.
    """
    socket = wrapper.node_principled_bsdf.inputs[name]
    value = socket.default_value
    linked_image = False
    if socket.is_linked:
        link = socket.links[0]
        node = link.from_node
        if node.bl_idname in ('ShaderNodeRGB', 'ShaderNodeValue'):
            value = link.from_socket.default_value
        elif image and node.bl_idname == 'ShaderNodeTexImage' and node.image is not None:
            if name == 'Base Color' and link.from_socket.name != 'Color':
                raise ValueError(f"Unsupported material {wrapper.material.name!r}: image Alpha to Base Color")
            if name != 'Base Color':
                log(f"Material {wrapper.material.name!r} {name}: CFG image fallback constant, not evaluated graph value")
            linked_image = True
        else:
            raise ValueError(f"Unsupported material {wrapper.material.name!r} input {name}: {node.bl_idname}")
    if socket.type == 'RGBA':
        value = tuple(value[:3]) if hasattr(value, '__len__') else (value,) * 3
    elif hasattr(value, '__len__'):
        raise ValueError(f"Unsupported material {wrapper.material.name!r}: color to scalar {name}")
    values = value if isinstance(value, tuple) else (value,)
    if not all(isfinite(float(v)) for v in values):
        raise ValueError(f"Non-finite material {wrapper.material.name!r} input {name}")
    return value, linked_image


def _material_preview(wrapper, names):
    """Small per-component edit baseline, including source socket/image identity."""
    state = []
    for name in names:
        socket = wrapper.node_principled_bsdf.inputs[name]
        value = socket.default_value
        entry = [name, list(value) if hasattr(value, '__len__') else value]
        for link in socket.links:
            node = link.from_node
            source = [node.name, node.bl_idname, link.from_socket.name]
            if node.bl_idname == 'ShaderNodeTexImage':
                source.append([node.image.name, node.image.filepath] if node.image else None)
            elif node.bl_idname in ('ShaderNodeRGB', 'ShaderNodeValue'):
                constant = link.from_socket.default_value
                source.append(list(constant) if hasattr(constant, '__len__') else constant)
            entry.append(source)
        state.append(entry)
    return json.dumps(state, separators=(',', ':'))


_MATERIAL_COMPONENTS = {
    'diffuse': ('Base Color',), 'alpha': ('Alpha',),
    'specular': ('Specular Tint', 'Specular IOR Level'),
    'emission': ('Emission Color', 'Emission Strength'),
}


def _raw_material_component(material, wrapper, component, authored):
    raw = material.get('o3d_raw_' + component)
    baseline = material.get('o3d_preview_' + component)
    if raw is not None and baseline == _material_preview(wrapper, _MATERIAL_COMPONENTS[component]):
        values = tuple(raw)
        if all(isfinite(float(value)) for value in values):
            return values
    return authored


def _o3d_specular_power(material, wrapper, roughness=None):
    roughness = float(wrapper.roughness if roughness is None else roughness)
    stored = material.get("o3d_specular_power")
    baseline = material.get("o3d_specular_roughness")
    if stored is not None and baseline is not None:
        try:
            if isfinite(float(stored)) and abs(roughness - float(baseline)) <= 1e-6:
                return float(stored)
        except (TypeError, ValueError):
            pass
    return 1000.0 * (1.0 - roughness)


def default_o3d_material():
    """
    Neutral white material used for empty material slots and for objects Blender has no material on at all,
    since OMSI expects every o3d file to carry at least one material.
    """
    # (diffuse_r, diffuse_g, diffuse_b, diffuse_a, specular_r, specular_g, specular_b, emission_r, emission_g,
    #  emission_b, specular_power, texture_name)
    return [1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, ""]


def _armature_bone_names(blender_obj):
    source = getattr(blender_obj, "original", blender_obj)
    names = set()
    found = False
    for modifier in source.modifiers:
        if (modifier.type != "ARMATURE" or modifier.object is None
                or not (modifier.show_viewport or modifier.show_render)):
            continue
        found = True
        names.update(bone.name for bone in modifier.object.data.bones)
    return names if found else None


def collect_o3d_bones(blender_obj, source_vertex_count, source_to_export, mesh=None, allowed_names=None):
    """Map evaluated deform weights to every serialized UV/normal split."""
    mesh = mesh if mesh is not None else blender_obj.data
    groups = [group for group in blender_obj.vertex_groups
              if allowed_names is None or group.name in allowed_names]
    omitted = [group.name for group in blender_obj.vertex_groups
               if allowed_names is not None and group.name not in allowed_names
               and any(entry.group == group.index and entry.weight > 0 for vertex in mesh.vertices for entry in vertex.groups)]
    for name in omitted:
        log(f"Omitting populated helper vertex group {name!r} from armature-backed O3D export")
    influences = {group.index: {} for group in groups}
    for vertex in mesh.vertices:
        for entry in vertex.groups:
            if entry.group not in influences or not isfinite(entry.weight) or entry.weight <= 0:
                continue
            for index in source_to_export.get(vertex.index, ()):
                influences[entry.group].setdefault(index, entry.weight)
    return [(group.name, sorted(influences[group.index].items()))
            for group in groups if influences[group.index]]


def _export_corner_data(mesh, authored_snapshot=None):
    """Capture corners before baking; optionally use validated authored local normals.

    The callback-only snapshot maps ``vertices`` (loop-order vertex indices) to
    ``normals`` (finite 3-vectors). It bypasses native custom-normal quantization;
    generated normals and the sole export-space conversion remain independent.
    """
    mesh.calc_loop_triangles()
    normals = [tuple(normal.vector) for normal in mesh.corner_normals]
    generated = normals
    if authored_snapshot is not None:
        try:
            vertices = tuple(authored_snapshot['vertices'])
            authored = [tuple(normal) for normal in authored_snapshot['normals']]
            valid = (mesh.has_custom_normals
                     and vertices == tuple(loop.vertex_index for loop in mesh.loops)
                     and len(authored) == len(mesh.loops)
                     and all(len(normal) == 3 and all(isfinite(value) for value in normal)
                             for normal in authored))
        except (KeyError, TypeError, AttributeError):
            valid = False
        if not valid:
            raise ValueError('Invalid callback authored normal snapshot')
        normals = authored
    if mesh.has_custom_normals:
        plain = mesh.copy()
        try:
            blender_compat.prepare_export_mesh(plain, False)
            generated = [tuple(normal.vector) for normal in plain.corner_normals]
        finally:
            bpy.data.meshes.remove(plain)
    return {"normals": normals, "generated_normals": generated,
            "triangles": [[*triangle.loops, triangle.material_index] for triangle in mesh.loop_triangles]}


def _uv_source_link(link, prefix):
    """Look through group outputs, validating the actual UV source rather than its label."""
    while link.from_node.bl_idname == 'ShaderNodeGroup':
        group = link.from_node
        tree = group.node_tree
        if group.mute or tree is None:
            raise ValueError(prefix + 'muted or missing coordinate group')
        animation = tree.animation_data
        if animation and (animation.action or animation.drivers or animation.nla_tracks):
            raise ValueError(prefix + 'animated node group coordinates are not supported')
        outputs = [node for node in tree.nodes
                   if node.bl_idname == 'NodeGroupOutput' and node.is_active_output]
        if len(outputs) != 1:
            raise ValueError(prefix + 'ambiguous coordinate group output')
        socket = next((socket for socket in outputs[0].inputs
                       if socket.identifier == link.from_socket.identifier), None)
        if socket is None or not socket.is_linked:
            raise ValueError(prefix + 'unlinked coordinate group output is not a UV source')
        if socket.type != 'VECTOR' or socket.links[0].from_socket.type != 'VECTOR':
            raise ValueError(prefix + 'coordinate group output requires vector sockets')
        link = socket.links[0]
    return link


def _image_uvs(mesh, material, image, loops):
    """Resolve UVs (including group outputs) -> optional static Mapping -> flat image."""
    layer = next((uv for uv in mesh.uv_layers if uv.active_render), None)
    if layer is None:
        layer = mesh.uv_layers.active or next(iter(mesh.uv_layers), None)
    mode, rotation, scale, location = None, None, None, None
    if image is not None:
        prefix = f"Unsupported coordinates for material {material.name!r}, image {image.name!r}: "
        if image.projection != 'FLAT' or image.mute:
            raise ValueError(prefix + 'requires an unmuted FLAT image')
        animation = material.node_tree.animation_data
        # Conservative static-only boundary; do not freeze animated coordinates
        # (including drivers/NLA) at an arbitrary export frame.
        if animation and (animation.action or animation.drivers or animation.nla_tracks):
            raise ValueError(prefix + 'animated node tree coordinates are not supported')
        socket = image.inputs['Vector']
        if socket.is_linked and socket.links[0].from_node.bl_idname == 'ShaderNodeMapping':
            mapping = socket.links[0].from_node
            mode = mapping.vector_type
            if mode not in ('POINT', 'TEXTURE', 'VECTOR') or mapping.mute:
                raise ValueError(prefix + f'unsupported Mapping {mode} or muted node')
            values = {}
            for name in ('Rotation', 'Scale') + (('Location',) if mode != 'VECTOR' else ()):
                transform = mapping.inputs[name]
                if transform.is_linked:
                    raise ValueError(prefix + f'linked Mapping {name}')
                values[name] = Vector(transform.default_value)
                if not all(isfinite(value) for value in values[name]):
                    raise ValueError(prefix + f'non-finite Mapping {name}')
            rotation = Euler(values['Rotation'], 'XYZ').to_matrix()
            scale = values['Scale']
            location = values.get('Location', Vector((0., 0., 0.)))
            if mode == 'TEXTURE' and any(value == 0 for value in scale):
                log(f"Material {material.name!r}: singular TEXTURE Mapping; shader safe divide yields zero on zero-scale components")
            socket = mapping.inputs['Vector']
            if not socket.is_linked:
                raise ValueError(prefix + 'unlinked Mapping Vector is not a UV source')
        if socket.is_linked:
            link = _uv_source_link(socket.links[0], prefix)
            source = link.from_node
            if source.mute or getattr(source, 'from_instancer', False):
                raise ValueError(prefix + 'muted or From Instances coordinate source')
            if source.bl_idname == 'ShaderNodeUVMap' and link.from_socket.name == 'UV':
                if source.uv_map:
                    layer = mesh.uv_layers.get(source.uv_map)
                    if layer is None:
                        raise ValueError(prefix + f'missing named UV map {source.uv_map!r}')
            elif source.bl_idname != 'ShaderNodeTexCoord' or link.from_socket.name != 'UV':
                raise ValueError(prefix + f'{source.bl_idname} {link.from_socket.name} is not a supported UV source')
    result = {}
    for loop in loops:
        uv = Vector((*layer.uv[loop].vector, 0.)) if layer is not None else Vector((0., 0., 0.))
        if mode == 'TEXTURE':
            uv = rotation.transposed() @ (uv - location)
            uv = Vector(tuple(uv[i] / scale[i] if scale[i] != 0 else 0. for i in range(3)))
        elif mode:
            uv = rotation @ Vector(tuple(uv[i] * scale[i] for i in range(3)))
            if mode == 'POINT':
                uv += location
        result[loop] = (uv.x, 1. - uv.y)
    return result


def _material_uvs(mesh, material, loops):
    if material is None or not material.use_nodes:
        return _image_uvs(mesh, material, None, loops)
    wrapper = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=True)
    shader, output = wrapper.node_principled_bsdf, wrapper.node_out
    # Geometry-only readiness also serves unconverted MMD graphs. Resolve only
    # the supported active image path here; actual export still validates every
    # material strictly in _build_o3d_materials before publishing any file.
    if shader is None or output is None or not output.is_active_output:
        return _image_uvs(mesh, material, None, loops)
    surface = output.inputs['Surface']
    if not surface.is_linked or surface.links[0].from_node != shader:
        return _image_uvs(mesh, material, None, loops)
    socket = shader.inputs['Base Color']
    if not socket.is_linked:
        return _image_uvs(mesh, material, None, loops)
    link = socket.links[0]
    base = link.from_node
    if base.bl_idname != 'ShaderNodeTexImage' or base.image is None or link.from_socket.name != 'Color':
        return _image_uvs(mesh, material, None, loops)
    result = _image_uvs(mesh, material, base, loops)
    # These are the established CFG texture routes, NOT a graph traversal or
    # new env/light/night conversion policy. All share the one serialized UV0.
    images = [('Alpha', wrapper.alpha_texture.node_image),
              ('Emission', wrapper.emission_color_texture.node_image)]
    alpha = wrapper.alpha_texture.image
    transmap = alpha is not None and alpha.filepath != base.image.filepath
    if wrapper.roughness <= .1 and wrapper.specular > .0001 and not transmap:
        images.append(('Specular mask', wrapper.specular_texture.node_image))
    if blender_compat.find_bump_map(wrapper) is not None:
        normal = wrapper.node_principled_bsdf.inputs['Normal'].links[0].from_node
        socket = normal.inputs['Height' if normal.bl_idname == 'ShaderNodeBump' else 'Color']
        source = socket.links[0].from_node
        if source.bl_idname == 'ShaderNodeBump':
            source = source.inputs['Height'].links[0].from_node
        images.append(('Bump', source))
    checked = {base}
    for channel, image in images:
        if image is None or image.image is None or image in checked:
            continue
        checked.add(image)
        other = _image_uvs(mesh, material, image, loops)
        if any(abs(a-b) > 1e-6 for loop in loops for a, b in zip(result[loop], other[loop])):
            raise ValueError(f"Material {material.name!r}: conflicting Base Color and {channel} texture coordinates; O3D has one UV stream")
    return result


def prepare_o3d_geometry(blender_obj, mesh, export_custom_normals=True, filter_helpers=True, allowed_names=None,
                         *, materials=None):
    """Prepare the exact serialized vertices, triangles and populated bone order."""
    corners = mesh.get("_o3d_export_corners")
    if corners is None:
        corners = _export_corner_data(mesh)
    normals = corners["normals" if export_custom_normals else "generated_normals"]
    materials = blender_obj.material_slots if materials is None else materials
    material_loops = {}
    for triangle in corners['triangles']:
        material_loops.setdefault(triangle[3], set()).update(triangle[:3])
    uvs = {}
    for index, loops in material_loops.items():
        material = materials[index].material if 0 <= index < len(materials) else None
        uvs[index] = _material_uvs(mesh, material, loops)
    weighted = any(vertex.groups for vertex in mesh.vertices)
    verts, tris, vert_map, source_to_export = [], [], {}, {}
    for triangle in corners["triangles"]:
        tri = []
        loops = triangle[:3][::-1] if corners.get("reverse_winding", False) else triangle[:3]
        for loop in loops:
            source = mesh.loops[loop].vertex_index
            co = tuple(mesh.vertices[source].co)
            normal = tuple(normals[loop])
            uv = uvs[triangle[3]][loop]
            key = (co, normal, uv, source if weighted else None)
            if key not in vert_map:
                vert_map[key] = len(verts)
                verts.append([*co, *normal, *uv])
            index = vert_map[key]
            tri.append(index)
            source_to_export.setdefault(source, set()).add(index)
        tris.append([*tri, triangle[3]])
    if filter_helpers and allowed_names is None:
        allowed_names = _armature_bone_names(blender_obj)
    bones = collect_o3d_bones(
        blender_obj, len(mesh.vertices), source_to_export, mesh, allowed_names
    )
    influence_counts = {}
    for _, entries in bones:
        for index, weight in entries:
            if weight > 0:
                influence_counts[index] = influence_counts.get(index, 0) + 1
    return {
        "verts": verts,
        "tris": tris,
        "bones": bones,
        "source_to_export": source_to_export,
        "smoothskin": any(count > 1 for count in influence_counts.values()),
    }


def validate_o3d_geometry(geometry, o3d_version=7, character_runtime=False):
    """Validate file grammar; optionally enforce stricter OMSI human skin limits."""
    verts, tris, bones = (geometry[key] for key in ("verts", "tris", "bones"))
    if o3d_version < 3:
        if len(verts) > 65535:
            raise ValueError(f"O3D version {o3d_version} supports at most 65535 vertices")
        if len(tris) > 65535:
            raise ValueError(f"O3D version {o3d_version} supports at most 65535 triangles")
    max_index = max((index for tri in tris for index in tri[:3]), default=0)
    if o3d_version < 3 and max_index > 65535:
        raise ValueError(f"O3D version {o3d_version} does not support triangle indices above 65535")
    if len(bones) > 65535:
        raise ValueError("O3D supports at most 65535 file bones")
    dominant = {}
    for bone_index, (name, entries) in enumerate(bones):
        try:
            encoded = name.encode("cp1252")
        except UnicodeEncodeError as error:
            raise ValueError(f"Bone name {name!r} is not CP1252 encodable") from error
        if len(encoded) > 255:
            raise ValueError(f"Bone name {name!r} exceeds 255 CP1252 bytes")
        if len(entries) > 65535:
            raise ValueError(f"Bone {name!r} has more than 65535 influences")
        for index, weight in entries:
            if not 0 <= index <= 65535:
                raise ValueError(f"Vertex group {name!r} has weighted vertex index {index}, above the 65535 limit")
            if index >= len(verts):
                raise ValueError(f"Vertex group {name!r} has weighted vertex index {index}, "
                                 f"outside the {len(verts)} serialized vertices")
            if not isfinite(weight) or weight <= 0:
                raise ValueError(f"Invalid influence for bone {name!r}")
            if weight > dominant.get(index, (0, 0))[0]:
                dominant[index] = (weight, bone_index)
    if bones:
        if len(verts) > 65535:
            raise ValueError("OMSI supports at most 65535 serialized skinned vertices")
        if any(index >= 128 for _, index in dominant.values()):
            raise ValueError("dominant exported bone index must be below 128")
    return max_index > 65535


@contextmanager
def prepared_export_mesh(obj, context=None, global_matrix=None, *, rest_deformer=None):
    """Yield an export-space mesh/frame tuple with preserved corner tessellation.

    A callback may set temporary mesh ``_o3d_local_authored_normals`` to the
    loop-associated local snapshot documented by ``_export_corner_data`` and
    return None. Only a fresh callback payload is authoritative: copied source
    metadata is ignored without a callback and cleared before invoking one.
    """
    context = context or bpy.context
    states = [(modifier, modifier.show_viewport, modifier.show_render)
              for modifier in obj.modifiers if modifier.type == "ARMATURE"]
    evaluated = mesh = None
    try:
        for modifier, _, _ in states:
            modifier.show_viewport = modifier.show_render = False
        evaluated = obj.evaluated_get(context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=context.evaluated_depsgraph_get())
        authored_snapshot = None
        if rest_deformer is not None:
            if '_o3d_local_authored_normals' in mesh:
                del mesh['_o3d_local_authored_normals']
            rest_deformer(evaluated, mesh)
            authored_snapshot = mesh.get('_o3d_local_authored_normals')
        axis = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
        export_matrix = global_matrix if global_matrix is not None else Matrix.Identity(4)
        frame_matrix = export_matrix @ axis @ obj.matrix_world @ axis
        frame_matrix.transpose()
        corners = _export_corner_data(mesh, authored_snapshot)
        # Compose directions in float64: finite sequential position baking can
        # survive G*M overflowing Blender's float32 matrix (e.g. huge UI scale).
        linear = (np.asarray(export_matrix, dtype=np.float64)[:3, :3]
                  @ np.asarray(axis, dtype=np.float64)[:3, :3]
                  @ np.asarray(obj.matrix_world, dtype=np.float64)[:3, :3])
        sign, _ = np.linalg.slogdet(linear)
        # This is the sole direction-transform/normalization owner. A singular
        # inverse-transpose is undefined: keep exportable degenerate geometry,
        # but record zero directions rather than inventing an axis/perturbation.
        normal_matrix = np.linalg.inv(linear).T if sign else np.zeros((3, 3))
        for key in ("normals", "generated_normals"):
            transformed = []
            for normal in corners[key]:
                direction = normal_matrix @ normal
                length = np.linalg.norm(direction)
                transformed.append(tuple(direction / length if length else direction))
            corners[key] = transformed
        # The codec already reverses once for the established XZY reflection.
        # Compensate the full baked determinant separately, not shading normals.
        corners["reverse_winding"] = bool(sign > 0)
        # Preserve established sequential baking: composing first can overflow
        # even when these final positions remain finite (human preflight).
        mesh.transform(obj.matrix_world)
        mesh.transform(axis)
        mesh.transform(export_matrix)
        # Only this temporary mesh owns the snapshot; cleanup shares its lifetime.
        mesh["_o3d_export_corners"] = corners
        yield evaluated, mesh, [value for row in frame_matrix for value in row]
    finally:
        if mesh is not None:
            evaluated.to_mesh_clear()
        for modifier, viewport, render in states:
            modifier.show_viewport, modifier.show_render = viewport, render


def validate_character_export(obj, context=None, global_matrix=None, export_custom_normals=True):
    """Validate exactly what export serializes, without writing or changing context."""
    with prepared_export_mesh(obj, context, global_matrix) as (evaluated, mesh, _):
        geometry = prepare_o3d_geometry(evaluated, mesh, export_custom_normals, filter_helpers=False)
        validate_o3d_geometry(geometry, character_runtime=True)
        return {"vertices": len(geometry["verts"]),
                "bones": tuple(name for name, _ in geometry["bones"]),
                "smoothskin": geometry["smoothskin"]}


def _build_o3d_materials(filepath, materials, texture_filepath=None, texture_names=None):
    texture_filepath = texture_filepath or filepath
    o3d_mats = []
    for material_slot in materials:
        if material_slot.material is None:
            o3d_mats.append(default_o3d_material())
            continue
        material = material_slot.material
        if material.get("o3d_layered_material"):
            raise ValueError(
                f"Layered material {material.name!r} cannot be represented by one O3D texture"
            )
        if not material.use_nodes:
            # Preserve the wrapper's established non-node Material-property
            # fallback (alpha1, black tint/emission), without creating nodes.
            o3d_mats.append([*material.diffuse_color[:3], 1., *([0.] * 6),
                             _o3d_specular_power(material, material), ''])
            continue
        mat = _material_wrapper(material)
        base, textured = _material_input(mat, 'Base Color', image=True)
        alpha, _ = _material_input(mat, 'Alpha', image=textured)
        level, _ = _material_input(mat, 'Specular IOR Level', image=textured)
        tint, _ = _material_input(mat, 'Specular Tint')
        roughness, _ = _material_input(mat, 'Roughness')
        emission, emission_image = _material_input(mat, 'Emission Color', image=textured)
        strength, _ = _material_input(mat, 'Emission Strength')
        o3d_mat = [*_raw_material_component(material, mat, 'diffuse', (1., 1., 1.) if textured else base),
                   *_raw_material_component(material, mat, 'alpha', (alpha,))]
        o3d_mat.extend(_raw_material_component(material, mat, 'specular', tuple(channel * level for channel in tint)))
        # A CFG light/night image has its own existing strength routing. Its
        # inactive color is a fallback, not a constant emission to bake.
        emitted = emission if emission_image else tuple(channel * strength if strength else 0. for channel in emission)
        o3d_mat.extend(_raw_material_component(material, mat, 'emission', emitted))
        o3d_mat.append(_o3d_specular_power(material, mat, roughness))
        if mat.base_color_texture is not None and mat.base_color_texture.image is not None:
            o3d_mat.append(o3d_cfg_parser.texture_name(texture_filepath, mat.base_color_texture.image, texture_names))
        else:
            o3d_mat.append("")
        o3d_mats.append(o3d_mat)
    if not o3d_mats:
        o3d_mats.append(default_o3d_material())
    for material in o3d_mats:
        o3dconvert._validate_material(material)
    return o3d_mats


def export_mesh(filepath, context, blender_obj, mesh, transform_matrix, materials, o3d_version,
                export_custom_normals, allow_smoothskin=False, allowed_names=None,
                texture_filepath=None, texture_names=None):
    if len(materials) > 65535:
        raise ValueError("O3D supports at most 65535 materials")
    geometry = prepare_o3d_geometry(
        blender_obj, mesh, export_custom_normals, allowed_names=allowed_names, materials=materials
    )
    long_triangle_indices = validate_o3d_geometry(
        geometry, o3d_version, character_runtime=bool(geometry["bones"])
    )
    verts, tris, bones = (geometry[key] for key in ("verts", "tris", "bones"))
    if geometry["smoothskin"] and not allow_smoothskin:
        log("WARNING: direct O3D export cannot express [smoothskin]; blended weights may load rigidly")
    o3d_mats = _build_o3d_materials(filepath, materials, texture_filepath, texture_names)
    # Reuse human preflight's real in-memory codec path before destructive open:
    # validation AND packing failures must leave an existing destination intact.
    payload = BytesIO()
    o3dconvert.export_o3d(
        payload, verts, tris, o3d_mats, bones, transform_matrix,
        version=o3d_version,
        encrypted=False,
        encryption_key=0x0,
        long_triangle_indices=long_triangle_indices,
        alt_encryption_seed=True,
        invert_triangle_winding=True,
    )
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(payload.getvalue())
    return {"smoothskin": geometry["smoothskin"], "bones": tuple(bones)}


def do_export(filepath, context, global_matrix, use_selection, o3d_version, export_custom_normals=True,
              *, objects=None, human_bindings=False, human_bone_slots=None,
              texture_names=None, mesh_paths=None, rest_deformer=None, allowed_names=None):
    """
    Exports the selected CFG/SCO/O3D file.
    allowed_names overrides bone admission for this batch; None retains per-object discovery.
    :param o3d_version: O3D version to export the file as
    :param use_selection: export only the selected objects
    :param global_matrix: transformation matrix to apply before export
    :param filepath: the path to the file to import
    :param context: blender context
    :return: success message
    """
    obj_root = os.path.dirname(filepath)
    start_time = time.time()
    active = context.view_layer.objects.active
    mode = active.mode if active else "OBJECT"

    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')

    if objects is not None:
        obs = objects
    elif use_selection:
        obs = context.selected_objects
    else:
        obs = context.scene.objects

    obs = list(obs)
    bpy.context.window_manager.progress_begin(0, len(obs))
    single_o3d = filepath.lower().endswith(".o3d")
    try:
        outputs, lexical_destinations, resolved_destinations = [], {}, {}
        cfg_lexical_key = os.path.abspath(filepath).casefold() if not single_o3d else None
        cfg_resolved_key = os.path.realpath(filepath).casefold() if not single_o3d else None
        # Validate every candidate before any geometry/CFG file can be opened.
        for ob in obs:
            if "skip_export" in ob or ob.type not in {"MESH", "CURVE", "SURFACE", "FONT", "META"}:
                continue
            if single_o3d and len(obs) == 1:
                path = omsi_paths.safe_export_path(obj_root, os.path.basename(filepath))
            else:
                relative = (os.path.basename(filepath)[:-4] + "-" + ob.name + ".o3d" if single_o3d
                            else str((mesh_paths or {}).get(id(ob), ob.get("export_path", ob.name + ".o3d"))))
                path = omsi_paths.safe_export_path(obj_root, relative)
            # abspath normalizes lexical paths without losing symlink spellings.
            lexical_key = os.path.abspath(path).casefold()
            resolved_key = os.path.realpath(path).casefold()
            if lexical_key == cfg_lexical_key or resolved_key == cfg_resolved_key:
                raise ValueError(f"Output path for {ob.name!r} collides with CFG destination {filepath!r}")
            previous_lexical = lexical_destinations.get(lexical_key)
            previous_resolved = resolved_destinations.get(resolved_key)
            for previous in (previous_lexical, previous_resolved):
                if previous is not None and previous != ob:
                    raise ValueError(f"Output paths for {previous.name!r} and {ob.name!r} collide at {path!r}")
            if previous_lexical is not None or previous_resolved is not None:
                continue
            lexical_destinations[lexical_key] = resolved_destinations[resolved_key] = ob
            outputs.append((ob, path))
        export_metadata = {}
        for index, (ob, path) in enumerate(outputs):
            log("Exporting " + ob.name + "...")
            bpy.context.window_manager.progress_update(index)
            mesh_allowed_names = _armature_bone_names(ob) if allowed_names is None else allowed_names
            with prepared_export_mesh(ob, context, global_matrix, rest_deformer=rest_deformer) as (evaluated, mesh, matrix):
                export_metadata[id(ob)] = export_mesh(
                    path, context, evaluated, mesh, matrix, evaluated.material_slots,
                    o3d_version, export_custom_normals,
                    allow_smoothskin=not single_o3d,
                    allowed_names=mesh_allowed_names,
                    texture_filepath=filepath if not single_o3d else path,
                    texture_names=texture_names,
                )
        if not single_o3d:
            bindings = None
            if human_bindings:
                from .mmd_rig import CANONICAL_SLOTS
                slots = CANONICAL_SLOTS if human_bone_slots is None else human_bone_slots
                bindings = {key: {name: slots[name] for name, _ in data["bones"] if name in slots}
                            for key, data in export_metadata.items()}
            o3d_cfg_parser.write_cfg(
                filepath, obs, context, use_selection,
                smoothskin_by_object=export_metadata,
                objects_override=obs if objects is not None else None,
                human_bindings_by_object=bindings,
                texture_names=texture_names, mesh_paths=mesh_paths,
            )
    finally:
        bpy.context.window_manager.progress_end()
        if active is not None and mode != "OBJECT":
            context.view_layer.objects.active = active
            bpy.ops.object.mode_set(mode=mode)
    log("Exported {0} models in {1} seconds!".format(len(obs), time.time() - start_time))
