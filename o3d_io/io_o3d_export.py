# ==============================================================================
#  Copyright (c) 2022-2023 Thomas Mathieson.
# ==============================================================================

import os
import time

import numpy as np

import bmesh
import bpy
from mathutils import Matrix
from . import blender_compat, o3d_cfg_parser, o3dconvert

from bpy_extras import node_shader_utils


def log(*args):
    print("[O3D_Export]", *args)


def default_o3d_material():
    """
    Neutral white material used for empty material slots and for objects Blender has no material on at all,
    since OMSI expects every o3d file to carry at least one material.
    """
    # (diffuse_r, diffuse_g, diffuse_b, diffuse_a, specular_r, specular_g, specular_b, emission_r, emission_g,
    #  emission_b, specular_power, texture_name)
    return [1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, ""]


def collect_o3d_bones(blender_obj, source_vertex_count, source_to_export):
    """
    Collect validated bone weights mapped to exported vertex indices.

    Args:
        blender_obj: Blender object with vertex groups
        source_vertex_count: Number of vertices in the source mesh
        source_to_export: dict mapping source vertex index to list of export vertex indices

    Returns:
        List of (bone_name, [(export_index, weight), ...]) tuples
    """
    bones = []
    for v_group in blender_obj.vertex_groups:
        influences = []

        # Query weights from source vertex indices
        for source_idx in range(source_vertex_count):
            try:
                weight = v_group.weight(source_idx)

                # Validate weight
                if not (isinstance(weight, (int, float)) and weight >= 0.0 and weight != float('inf') and weight != float('-inf') and weight == weight):
                    log(f"Warning: Skipping invalid weight {weight} for object '{blender_obj.name}', group '{v_group.name}', vertex {source_idx}")
                    continue

                # Map to all corresponding export indices
                if source_idx in source_to_export:
                    for export_idx in source_to_export[source_idx]:
                        influences.append((export_idx, weight))
            except RuntimeError:
                # Vertex not in this group
                pass

        # Only include groups with at least one valid influence
        if influences:
            bones.append((v_group.name, influences))

    return bones



def export_mesh(filepath, context, blender_obj, mesh, transform_matrix, materials, o3d_version, export_custom_normals):
    # Create o3d file
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "wb") as f:
        has_uvs = len(mesh.uv_layers) > 0
        if has_uvs:
            uv_layer = mesh.uv_layers.active.data[:]
        else:
            uv_layer = None

        # Extract mesh data
        tris = []
        verts = []  # Array of (xp, yp, zp, xn, yn, zn, u, v)
        vert_map = {}
        vert_count = 0
        source_to_export = {}  # Map source vertex index to list of export vertex indices

        blender_compat.prepare_export_mesh(mesh, export_custom_normals)
        for tri_loop in mesh.loop_triangles:
            tri = []
            tris.append(tri)

            for tri_vert, loop, normal in zip(tri_loop.vertices, tri_loop.loops, tri_loop.split_normals):
                vert = mesh.vertices[tri_vert]
                v_co = vert.co[:]
                v_nrm = normal[:]
                if uv_layer is not None:
                    v_uv = uv_layer[loop].uv[:2]
                else:
                    v_uv = (0, 0)

                if (v_co, v_nrm, v_uv) in vert_map:
                    export_idx = vert_map[(v_co, v_nrm, v_uv)]
                    tri.append(export_idx)
                    # Map source vertex to this existing export vertex
                    if tri_vert not in source_to_export:
                        source_to_export[tri_vert] = []
                    if export_idx not in source_to_export[tri_vert]:
                        source_to_export[tri_vert].append(export_idx)
                else:
                    vert_map[(v_co, v_nrm, v_uv)] = vert_count
                    verts.append(
                        [v_co[0], v_co[1], v_co[2],
                         -v_nrm[0], -v_nrm[1], -v_nrm[2],
                         v_uv[0], 1 - v_uv[1]])
                    tri.append(vert_count)
                    # Map source vertex to this new export vertex
                    if tri_vert not in source_to_export:
                        source_to_export[tri_vert] = []
                    source_to_export[tri_vert].append(vert_count)
                    vert_count += 1

            tri.append(tri_loop.material_index)

        # Construct embedded material array
        o3d_mats = []
        for material_slot in materials:
            if material_slot.material is None:
                # Keep the material indices written into the triangles aligned with the slots
                o3d_mats.append(default_o3d_material())
                continue

            # O3D mat structure:
            # (diffuse_r, diffuse_g, diffuse_b, diffuse_a, specular_r, specular_g, specular_b, emission_r, emission_g,
            #  emission_b, specular_power, texture_name)
            o3d_mat = []
            o3d_mats.append(o3d_mat)
            mat = node_shader_utils.PrincipledBSDFWrapper(material_slot.material, is_readonly=True)
            o3d_mat.extend(mat.base_color[:3])
            o3d_mat.append(mat.alpha)
            if bpy.app.version >= (4, 0):
                o3d_mat.extend(np.array(mat.specular_tint[:3]) * mat.specular)
            else:
                o3d_mat.extend([mat.specular, mat.specular, mat.specular])
            o3d_mat.extend(mat.emission_color[:3])
            o3d_mat.append(1 - mat.roughness)
            if mat.base_color_texture is not None and mat.base_color_texture.image is not None:
                o3d_mat.append(os.path.basename(mat.base_color_texture.image.filepath))
            else:
                o3d_mat.append("")

        if not o3d_mats:
            o3d_mats.append(default_o3d_material())

        # Construct bones with validated weights mapped to export vertices
        bones = collect_o3d_bones(blender_obj, len(mesh.vertices), source_to_export)

        # 32-bit triangle indices are driven by triangle indices only. Bone
        # influence indices are always 16-bit in OMSI, regardless of options bit 0.
        max_triangle_index = max((idx for tri in tris for idx in tri[:3]), default=0)
        long_triangle_indices = max_triangle_index > 65535

        # Reject wide triangle indices for pre-v3 formats
        if o3d_version < 3 and long_triangle_indices:
            raise ValueError(
                f"O3D version {o3d_version} does not support triangle indices above 65535. "
                f"Maximum triangle index in this mesh is {max_triangle_index}. "
                f"Use version 3 or higher, or reduce the vertex count."
            )

        # OMSI addresses bone influences with a 16-bit index, so weighted vertices
        # above index 65535 cannot be skinned. Reject before writing the bone
        # section. (The file is opened above, so like the pre-v3 rejection this
        # can leave a partial file behind on failure.)
        for bone_name, influences in bones:
            for idx, _ in influences:
                if idx > 65535:
                    raise ValueError(
                        f"Vertex group '{bone_name}' has weighted vertex index {idx}, "
                        f"above the 65535 limit OMSI uses for bone influences. "
                        f"Reduce the vertex count or move weights to lower vertices."
                    )

        o3dconvert.export_o3d(f, verts, tris, o3d_mats, bones, transform_matrix,
                              version=o3d_version,
                              encrypted=False, encryption_key=0x0,
                              long_triangle_indices=long_triangle_indices,
                              alt_encryption_seed=True,
                              invert_triangle_winding=True)


def do_export(filepath, context, global_matrix, use_selection, o3d_version, export_custom_normals=True):
    """
    Exports the selected CFG/SCO/O3D file
    :param o3d_version: O3D version to export the file as
    :param use_selection: export only the selected objects
    :param global_matrix: transformation matrix to apply before export
    :param filepath: the path to the file to import
    :param context: blender context
    :return: success message
    """
    obj_root = os.path.dirname(filepath)
    start_time = time.time()

    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')

    if use_selection:
        obs = context.selected_objects
    else:
        obs = context.scene.objects

    deps_graph = context.evaluated_depsgraph_get()

    bpy.context.window_manager.progress_begin(0, len(obs))

    single_o3d = False
    if filepath[-3:] == "o3d":
        single_o3d = True

    index = 0
    exported_paths = set()
    for ob in obs:
        if "skip_export" in ob:
            log("Skipping {0}...".format(ob.name))
            index += 1
            continue

        log("Exporting " + ob.name + "...")
        bpy.context.window_manager.progress_update(index)

        # Identify Armature modifiers before evaluation to export rest-space geometry
        armature_modifiers = []
        if hasattr(ob, 'modifiers'):
            for mod in ob.modifiers:
                if mod.type == 'ARMATURE':
                    armature_modifiers.append(mod)

        # Store original visibility states for all Armature modifiers
        original_modifier_states = []
        for mod in armature_modifiers:
            original_modifier_states.append({
                'modifier': mod,
                'show_viewport': mod.show_viewport,
                'show_render': mod.show_render
            })

        try:
            # Temporarily disable Armature modifiers to obtain rest-space geometry
            for mod in armature_modifiers:
                mod.show_viewport = False
                mod.show_render = False

            # Obtain a local dependency graph for armature-disabled evaluation
            # Do not overwrite the shared deps_graph used by later objects
            local_deps_graph = context.evaluated_depsgraph_get() if armature_modifiers else deps_graph

            ob_eval = ob.evaluated_get(local_deps_graph)

            me = None
            try:
                me = ob_eval.to_mesh()
            except RuntimeError:
                # Cannot convert to mesh, skip this object
                index += 1
                continue

            try:
                axis_conversion_matrix = Matrix((
                    (1, 0, 0, 0),
                    (0, 0, 1, 0),
                    (0, 1, 0, 0),
                    (0, 0, 0, 1)
                ))

                o3d_matrix = axis_conversion_matrix @ ob.matrix_world @ axis_conversion_matrix
                o3d_matrix.transpose()
                me.transform(ob.matrix_world)
                me.transform(axis_conversion_matrix)
                if ob.matrix_world.is_negative:
                    me.flip_normals()

                log("Exported matrix: \n{0}".format(o3d_matrix))

                bm = bmesh.new()
                bm.from_mesh(me)

                if global_matrix is not None:
                    bm.transform(global_matrix)

                bmesh.ops.triangulate(bm, faces=bm.faces)

                bm.to_mesh(me)
                bm.free()

                # Export individual model
                if "export_path" in ob:
                    path = os.path.join(obj_root, ob["export_path"])
                else:
                    path = os.path.join(obj_root, ob.name + ".o3d")

                if single_o3d:
                    if len(obs) == 1:
                        path = filepath
                    else:
                        path = os.path.join(obj_root, os.path.basename(filepath)[:-4] + "-" + ob.name + ".o3d")

                # Export the mesh if it hasn't already been exported
                if path not in exported_paths:
                    exported_paths.add(path)
                    export_mesh(path, context, ob_eval, me, [x for y in o3d_matrix for x in y], ob_eval.material_slots,
                                o3d_version, export_custom_normals)
            finally:
                # Clean up evaluated mesh whenever to_mesh() succeeded
                if me is not None:
                    ob_eval.to_mesh_clear()

            index += 1
        finally:
            # Restore original modifier visibility states
            for state in original_modifier_states:
                state['modifier'].show_viewport = state['show_viewport']
                state['modifier'].show_render = state['show_render']

    if not single_o3d:
        cfg_materials = o3d_cfg_parser.write_cfg(filepath, obs, context, use_selection)

    bpy.context.window_manager.progress_end()
    log("Exported {0} models in {1} seconds!".format(len(obs), time.time() - start_time))
