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
                    tri.append(vert_map[(v_co, v_nrm, v_uv)])
                else:
                    vert_map[(v_co, v_nrm, v_uv)] = vert_count
                    verts.append(
                        [v_co[0], v_co[1], v_co[2],
                         -v_nrm[0], -v_nrm[1], -v_nrm[2],
                         v_uv[0], 1 - v_uv[1]])
                    tri.append(vert_count)
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

        # Construct bones
        bones = []
        for v_group in blender_obj.vertex_groups:
            bone = (v_group.name, [])
            bones.append(bone)
            for index in range(len(verts)):
                try:
                    bone[1].append((index, v_group.weight(index)))
                except Exception as e:
                    pass

        o3dconvert.export_o3d(f, verts, tris, o3d_mats, bones, transform_matrix,
                              version=o3d_version,
                              encrypted=False, encryption_key=0x0,
                              long_triangle_indices=False,
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
        ob_eval = ob.evaluated_get(deps_graph)

        try:
            me = ob_eval.to_mesh()
        except RuntimeError:
            continue

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

        ob_eval.to_mesh_clear()

        index += 1

    if not single_o3d:
        cfg_materials = o3d_cfg_parser.write_cfg(filepath, obs, context, use_selection)

    bpy.context.window_manager.progress_end()
    log("Exported {0} models in {1} seconds!".format(len(obs), time.time() - start_time))
