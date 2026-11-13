# ==============================================================================
#  Copyright (c) 2022-2023 Thomas Mathieson.
# ==============================================================================
import math
import time
from collections import Counter
from math import radians

import numpy as np

import bpy
import os

if bpy.app.version >= (4, 0):
    from bpy_extras import node_shader_utils as o3d_node_shader_utils
else:
    from . import o3d_node_shader_utils
from . import blender_compat, o3dconvert, o3d_armature

# from . import log
from mathutils import Matrix, Vector
from .o3d_cfg_parser import read_cfg, material_texture_key
from .blender_texture_io import TextureSlotWrapper, load_texture_into_new_slot, load_image, missing_texture_files
from .omsi_paths import platform_related_path, resolve_case_insensitive_path


def log(*args):
    print("[O3D_Import]", *args)


def _safe_vertex_group_name(name, used_names, max_length=63):
    base = str(name)[:max_length]
    if not base:
        return ""
    candidate = base
    suffix = 1
    while candidate in used_names:
        marker = f".{suffix:03d}"
        candidate = f"{base[:max_length - len(marker)]}{marker}"
        suffix += 1
    used_names.add(candidate)
    return candidate


def resolve_import_filepaths(filepath, directory, filenames):
    supported_extensions = {".cfg", ".sco", ".o3d", ".rdy"}
    base_directory = os.path.abspath(directory or os.path.dirname(filepath))
    selected_names = filenames or [os.path.basename(filepath)]
    resolved = []
    for filename in selected_names:
        candidate = os.path.abspath(os.path.join(base_directory, platform_related_path(filename)))
        if os.path.normcase(os.path.dirname(candidate)) != os.path.normcase(base_directory):
            continue
        if os.path.splitext(candidate)[1].lower() not in supported_extensions:
            continue
        candidate = resolve_case_insensitive_path(candidate)
        if os.path.isfile(candidate):
            resolved.append(candidate)
    return resolved


def do_import(filepath, context, import_x, override_text_encoding, hide_lods, import_lods=True, parent_collection=None,
              split_normals=True, missing_files=None):
    """
    Imports the selected CFG/SCO/O3D file
    :param override_text_encoding: the text encoding to use to read the file instead of utf8/cp1252
    :param import_x: whether to attempt to import referenced .x files
    :param hide_lods: whether additional LODs should be hidden by default
    :param filepath: the path to the file to import
    :param context: blender context
    :param import_lods: whether additional LODs should be loaded
    :param parent_collection: which current_collection to parent the imported objects to, use None for the scene current_collection
    :param missing_files: optional list which collects the paths of meshes that could not be read
    :return: success message
    """
    filepath = resolve_case_insensitive_path(filepath)
    obj_root = os.path.dirname(filepath)
    start_time = time.time()
    if os.path.splitext(filepath)[1].lower() in {".o3d", ".rdy"}:
        cfg_data = {
            -1: {
                "meshes": {
                    filepath: {
                        "path": filepath,
                    }
                }
            }
        }
    else:
        (cfg_data, obj_root) = read_cfg(filepath, override_text_encoding)

    n_meshes = len([0 for lod in cfg_data for mesh in cfg_data[lod]["meshes"]])
    bpy.context.window_manager.progress_begin(0, n_meshes)
    unreadable_meshes = []
    missing_textures = []
    texture_token = missing_texture_files.set(missing_textures)
    try:
        sorted_lods = sorted(cfg_data.keys(), reverse=True)

        # Work out where to put any custom data belonging to the root of the CFG file
        # In this case we CAN'T use the scene collection since it doesn't expose custom data in the editor for some reason
        custom_data_object = parent_collection
        if custom_data_object is None \
                or custom_data_object == context.scene.collection:
            custom_data_object = bpy.data.scenes[context.scene.name]

        # Iterate through the selected files
        blender_objs = []
        mat_counter = 0
        mesh_index = 0
        is_highest_lod = True
        current_collection = None
        for current_lod in sorted_lods:
            if not import_lods and not is_highest_lod:
                continue

            if current_lod == -1 or not import_lods:
                current_collection = bpy.context.scene.collection
                if parent_collection is not None:
                    current_collection = parent_collection
            else:
                collection_name = "LOD_{0}".format(current_lod)
                if collection_name not in bpy.data.collections:
                    current_collection = bpy.data.collections.new(collection_name)
                    if parent_collection is not None:
                        parent_collection.children.link(current_collection)
                    else:
                        bpy.context.scene.collection.children.link(current_collection)
                else:
                    current_collection = bpy.data.collections[collection_name]

            for current_mesh in cfg_data[current_lod]["meshes"]:
                # Generate full path to file
                path_to_file = cfg_data[current_lod]["meshes"][current_mesh]["path"]
                path_to_file = platform_related_path(path_to_file)
                bpy.context.window_manager.progress_update(mesh_index)
                log("[{0:.2f}%] Loading {1}...".format((mesh_index + 1) / n_meshes * 100, path_to_file))

                if path_to_file[-1:].lower() == "x":
                    if not import_x:
                        bpy.ops.object.select_all(action='DESELECT')
                        continue

                    # X files are not supported by this importer
                    try:
                        x_file_path = {"name": os.path.basename(path_to_file)}
                        # Clunky solution to work out what has been imported because the x importer doesn't set selection
                        old_objs = set(context.scene.objects)
                        # For now the x file importer doesn't handle omsi x files very well, materials aren't imported
                        # correctly
                        bpy.ops.object.select_all(action='DESELECT')
                        bpy.ops.import_scene.x(filepath=path_to_file, files=[x_file_path], axis_forward='Y', axis_up='Z',
                                               use_split_objects=False, use_split_groups=False, parented=False,
                                               quickmode=True)
                        # mat_counter = generate_materials(cfg_materials, filepath, mat_counter, materials, mesh,
                        #                                  object_directory, path_to_file)
                        new_objs = set(context.scene.objects) - old_objs

                        for o in new_objs:
                            if current_collection is not None:
                                if current_collection != bpy.context.scene.collection:
                                    bpy.context.scene.collection.objects.unlink(o)
                                if current_collection in o.users_collection:
                                    continue
                                current_collection.objects.link(o)

                        # Create lights
                        create_lights(blender_objs, cfg_data[current_lod]["meshes"][current_mesh], filepath,
                                      current_collection)
                        blender_objs.extend(new_objs)
                        continue
                    except Exception as e:
                        log("WARNING: {0} was not imported! A compatible X importer was not found! Please use: "
                            "https://github.com/Poikilos/io_import_x\n"
                            "Exception: {1}".format(path_to_file, e))
                        continue

                # Load mesh
                materials, matl_ids, mesh, o3d, o3d_transform_matrix = load_o3d(obj_root, path_to_file, split_normals)
                if mesh is None:
                    unreadable_meshes.append(path_to_file)
                    if missing_files is not None:
                        missing_files.append(path_to_file)
                    continue

                # Create blender object
                blender_obj = None
                blender_obj = bpy.data.objects.new(path_to_file[len(obj_root):-4], mesh)
                blender_obj["export_path"] = path_to_file[len(obj_root):]
                blender_objs.append(blender_obj)

                current_collection.objects.link(blender_obj)

                if hide_lods and not is_highest_lod:
                    blender_obj.hide_set(True)
                    blender_obj.hide_render = True

                # Transform object
                blender_obj.matrix_basis = o3d_transform_matrix

                # Generate materials
                cfg_mats = cfg_data[current_lod]["meshes"][current_mesh].get("matls", {})
                mat_counter = generate_materials(cfg_mats, filepath,
                                                 mat_counter, materials, mesh)

                # Populate remaining properties on the mesh
                bpy.data.meshes[mesh.name]["cfg_data"] = cfg_data[current_lod]["meshes"][current_mesh].get("cfg_data", {})
                # for prop in cfg_data[current_file[2]]["meshes"][current_file[1]].items():
                #     if prop[0][0] == "[" and prop[0][-1] == "]":
                #         # This must be an unparsed property, therefore we add it to the custom properties of the mesh
                #         bpy.data.meshes[mesh.name][prop[0]] = prop[1]

                for ind, tri in enumerate(mesh.polygons):
                    tri.material_index = matl_ids[ind]

                mesh.update()

                # Generate bones
                mapped_bones = []
                original_bone_names = []
                used_group_names = set()
                for bone_index, bone in enumerate(o3d[4]):
                    bone_name = bone[0] if bone[0] else ""

                    if not bone_name:
                        log(f"{path_to_file}: skipping bone: empty names are unsupported by Blender")
                        continue

                    group_name = _safe_vertex_group_name(bone_name, used_group_names)
                    group = blender_obj.vertex_groups.new(name=group_name)
                    mapped_influences = []
                    seen_influences = set()
                    for vert in bone[1]:
                        vertex_index = vert[0]
                        weight = vert[1]

                        # Validate influence data
                        try:
                            index_valid = 0 <= vertex_index < len(blender_obj.data.vertices)
                            weight_valid = isinstance(weight, (int, float)) and math.isfinite(weight) and weight >= 0.0
                        except (TypeError, ValueError):
                            index_valid = False
                            weight_valid = False

                        if not index_valid:
                            log(f"{path_to_file}: skipping influence for {bone_name!r}: "
                                f"vertex index {vertex_index!r} out of range (mesh has {len(blender_obj.data.vertices)} vertices)")
                            continue

                        if not weight_valid:
                            log(f"{path_to_file}: skipping influence for {bone_name!r}: "
                                f"weight {weight!r} is invalid (must be non-negative finite number)")
                            continue

                        if vertex_index in seen_influences:
                            continue
                        seen_influences.add(vertex_index)
                        group.add([vertex_index], weight, "REPLACE")
                        mapped_influences.append((vertex_index, weight))

                    mapped_bones.append((group_name, mapped_influences))
                    original_bone_names.append((bone_index, bone_name, group_name))

                if original_bone_names:
                    mesh["o3d_bone_names"] = "\n".join(
                        f"{index}\t{original}\t{mapped}"
                        for index, original, mapped in original_bone_names
                    )

                # Create armature if bones are present
                if mapped_bones:
                    armature = o3d_armature.create_armature_for_mesh(blender_obj, mapped_bones)
                    if armature:
                        blender_objs.append(armature)
                    else:
                        log(f"{path_to_file}: no armature created (construction failed or no valid bones)")



                mesh_index += 1

            # Remove the is_highest_lod flag once we've imported the highest LOD, note that LOD -1 should always import
            # first, but isn't the highest LOD (unless no other LODs are loaded)
            if current_lod != -1:
                is_highest_lod = False

            # Create lights
            create_lights(blender_objs, cfg_data[current_lod], filepath, current_collection)

        # Populate remaining properties on the cfg
        if "cfg_data" in cfg_data[-1]:
            custom_data_object["cfg_data"] = cfg_data[-1]["cfg_data"]
        if "groups" in cfg_data[-1]:
            custom_data_object["groups"] = cfg_data[-1]["groups"]
        if "friendlyname" in cfg_data[-1]:
            custom_data_object["friendlyname"] = cfg_data[-1]["friendlyname"]
        if "editor_only" in cfg_data[-1]:
            custom_data_object["editor_only"] = cfg_data[-1]["editor_only"]
        if "tree" in cfg_data[-1]:
            custom_data_object["tree"] = cfg_data[-1]["tree"]

        bpy.ops.object.select_all(action='DESELECT')
        try:
            for x in blender_objs:
                x.select_set(True)
        except Exception as e:
            log("WARNING: Couldn't select loaded objects:", e)

        if n_meshes == 0:
            log("WARNING: 0 models loaded! File:", filepath)

        if unreadable_meshes:
            log("WARNING: {0} of {1} meshes could not be read and are missing from the import!".format(
                len(unreadable_meshes), n_meshes))
        log("Loaded {0} models in {1} seconds!".format(n_meshes, time.time() - start_time))
        for label, paths in (("Unreadable meshes", unreadable_meshes), ("Missing textures", missing_textures)):
            counts = Counter(os.path.basename(path.replace("\\", "/")) for path in paths)
            log("{0}: {1} occurrences, {2} unique filename(s)".format(label, len(paths), len(counts)))
            for filename, count in counts.most_common():
                log("  {0}x {1}".format(count, filename))
        return blender_objs
    finally:
        missing_texture_files.reset(texture_token)
        bpy.context.window_manager.progress_end()


def create_lights(blender_objs, cfg_data, filepath, collection):
    interior_lights = cfg_data.get("interior_lights", [])
    for light_ind, light_cfg in enumerate(interior_lights):
        light_name = "::interior_light_{0}".format(light_ind)

        light_data = bpy.data.lights.new(name=light_name, type='POINT')
        light_data.energy = light_cfg["range"] * 10.0
        light_data.color = (light_cfg["red"], light_cfg["green"], light_cfg["blue"])
        light_data.shadow_soft_size = 0.02
        light_data["variable"] = light_cfg["variable"]
        light_data["cfg_type"] = "interiorlight"

        light_object = bpy.data.objects.new(name=light_name, object_data=light_data)

        collection.objects.link(light_object)

        blender_objs.append(light_object)
        # light_object.parent = blender_obj
        # Change light position
        light_object.location = (light_cfg["x_pos"], light_cfg["y_pos"], light_cfg["z_pos"])

    spotlights = cfg_data.get("spotlights", {})
    for light_ind, light_cfg in enumerate(spotlights):
        light_name = "::spotlight_{0}".format(light_ind)

        light_data = bpy.data.lights.new(name=light_name, type='SPOT')
        light_data.energy = light_cfg["range"] * 10.0
        light_data.color = (light_cfg["col_r"], light_cfg["col_g"], light_cfg["col_b"])
        light_data.shadow_soft_size = 0.02
        light_data.spot_size = math.radians(light_cfg["outer_angle"])
        light_data.spot_blend = light_cfg["inner_angle"] / light_cfg["outer_angle"]
        light_data["cfg_type"] = "spotlight"

        light_object = bpy.data.objects.new(name=light_name, object_data=light_data)

        collection.objects.link(light_object)

        blender_objs.append(light_object)
        # light_object.parent = blender_obj

        # Change light position
        light_object.location = (light_cfg["x_pos"], light_cfg["y_pos"], light_cfg["z_pos"])

        v0 = Vector((0, 0, 1))
        v1 = Vector((light_cfg["x_fwd"], light_cfg["y_fwd"], -light_cfg["z_fwd"]))

        light_object.rotation_euler = v1.rotation_difference(v0).to_euler()

    maplights = cfg_data.get("maplights", [])
    for light_ind, light_cfg in enumerate(maplights):
        light_name = "::maplight_{0}".format(light_ind)

        light_data = bpy.data.lights.new(name=light_name, type='POINT')
        light_data.energy = light_cfg["range"] * 50.0
        light_data.color = (light_cfg["r"], light_cfg["g"], light_cfg["b"])
        light_data.shadow_soft_size = 0.3
        light_data["cfg_type"] = "maplight"

        light_object = bpy.data.objects.new(name=light_name, object_data=light_data)

        collection.objects.link(light_object)

        blender_objs.append(light_object)
        # light_object.parent = blender_obj

        # Change light position
        light_object.location = (light_cfg["x"], light_cfg["y"], light_cfg["z"])

    # Create lens flares
    flares = cfg_data.get("light_flares", [])
    for flare_ind, flare in enumerate(flares):
        flare_name = "::light_enh{0}_{1}".format("" if flare["type"] == "[light_enh]" else "_2", flare_ind)
        flare_obj = bpy.data.objects.new(flare_name, None)
        collection.objects.link(flare_obj)

        flare_obj.empty_display_size = flare["size"]
        flare_obj.empty_display_type = "IMAGE"
        flare_obj.use_empty_image_alpha = True

        flare_obj.empty_image_offset = (-0.5, -0.5)
        flare_obj.color = (flare["col_r"], flare["col_g"], flare["col_b"], 0.5)
        # flare_obj.parent = blender_obj
        flare_obj.location = (flare["x_pos"], flare["y_pos"], flare["z_pos"])
        flare_obj.rotation_euler = (-math.pi / 2, 0, 0)

        if "texture" in flare and flare["texture"] != "":
            tex_path = flare["texture"]
        else:
            tex_path = "licht.bmp"
        image = load_image(filepath, tex_path)
        flare_obj.data = image

        # Copy across all the parameters' blender can't render...
        flare_obj["type"] = flare["type"]
        if flare["type"] == "[light_enh_2]":
            flare_obj["forward_vector"] = (flare["x_fwd"], flare["y_fwd"], flare["z_fwd"])
            flare_obj["rotation_axis"] = (flare["x_rot"], flare["y_rot"], flare["z_rot"])
            flare_obj["omnidirectional"] = flare["omni"]
            flare_obj["rotating"] = flare["rotating"]
            flare_obj["max_brightness_angle"] = flare["max_brightness_angle"]
            flare_obj["min_brightness_angle"] = flare["min_brightness_angle"]
            flare_obj["cone_effect"] = flare["cone_effect"]
        flare_obj["brightness_var"] = flare["brightness_var"]
        flare_obj["brightness"] = flare["brightness"]
        flare_obj["z_offset"] = flare["z_offset"]
        flare_obj["effect"] = flare["effect"]
        flare_obj["ramp_time"] = flare["ramp_time"]

        blender_objs.append(flare_obj)


def load_o3d(object_directory, path_to_file, split_normals):
    """
    Imports an o3d file and creates a Blender mesh for it.
    :param object_directory: path to the root directory of the model
    :param path_to_file: path to the o3d file to load
    :return:
    """
    path_to_file = resolve_case_insensitive_path(path_to_file)
    try:
        with open(path_to_file, "rb") as f:
            o3d_bytes = f.read()
    except IOError:
        log("WARNING: Couldn't open {0}!".format(path_to_file))
        return [], [], None, None, None

    o3d = o3dconvert.import_o3d(o3d_bytes)
    verts = o3d[1]
    edges = []
    faces = o3d[2]

    mesh = bpy.data.meshes.new(name=path_to_file[len(object_directory):-4])

    vertex_pos = [x[0] for x in verts]
    normals = [x[1] for x in verts]  # [(x[1][0], x[1][2], x[1][1]) for x in verts]
    uvs = [(x[2][0], 1 - x[2][1]) for x in verts]
    face_list = [x[0] for x in faces]
    matl_ids = [x[1] for x in faces]
    materials = o3d[3]

    mesh.from_pydata(vertex_pos, edges, face_list)
    # Keep material IDs attached to their faces when validation removes invalid geometry.
    mesh.polygons.foreach_set("material_index", matl_ids)

    mesh.uv_layers.new(name="UV Map")

    axis_conversion_matrix = Matrix((
        (1, 0, 0, 0),
        (0, 0, 1, 0),
        (0, 1, 0, 0),
        (0, 0, 0, 1)
    ))
    # log("Imported matrix (pre-rounding): \n{0}".format(o3d[5]))
    o3d_transform = [tuple(0 if -1e-7 < x < 1e-7 else x for x in y) for y in o3d[5]]
    o3d_transform_matrix = Matrix(o3d_transform)
    o3d_transform_matrix.transpose()
    # log("Imported matrix: \n{0}".format(o3d_transform_matrix))
    o3d_transform_matrix = axis_conversion_matrix @ o3d_transform_matrix @ axis_conversion_matrix
    if abs(o3d_transform_matrix.determinant()) <= 1e-8:
        log("WARNING: {0} has a non-invertible transform, importing it untransformed!".format(path_to_file))
        o3d_transform_matrix = Matrix.Identity(4)
        mesh_matrix = axis_conversion_matrix
    else:
        i_o3d_transform_matrix = o3d_transform_matrix.inverted()
        mesh_matrix = i_o3d_transform_matrix @ axis_conversion_matrix
    # log("Converted matrix: \n{0}".format(o3d_transform_matrix))
    # log("Inverted matrix: \n{0}".format(i_o3d_transform_matrix))
    # log("Mesh matrix: \n{0}".format(mesh_matrix))

    blender_compat.prepare_import_mesh(
        mesh, normals, split_normals, transform_matrix=mesh_matrix
    )

    for face in mesh.polygons:
        for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
            mesh.uv_layers[0].data[loop_idx].uv = uvs[vert_idx]

    matl_ids = [face.material_index for face in mesh.polygons]
    return materials, matl_ids, mesh, o3d, o3d_transform_matrix


def generate_materials(cfg_materials, cfg_file_path, mat_counter, materials, mesh):
    """
    Generates Blender materials for an o3d file.

    :param cfg_materials: the material dictionary for this particular mesh as defined in the model.cfg file
    :param cfg_file_path: the path to the model.cfg file
    :param mat_counter: the global material counter
    :param materials: the o3d material definition
    :param mesh: the Blender mesh to generate materials for
    :return: the new global material counter
    """

    # Per-texture repeat ordinals select CFG overrides; mesh face slots stay absolute.
    from .io_o3d_export import _material_preview, _MATERIAL_COMPONENTS
    repeats = Counter()
    for mat_index, matl in enumerate(materials):
        texture_key = material_texture_key(matl[4])
        key = (texture_key, repeats[texture_key])
        repeats[texture_key] += 1
        # log(matl)
        diffuse_r = matl[0][0]
        diffuse_g = matl[0][1]
        diffuse_b = matl[0][2]
        diffuse_a = matl[0][3]
        spec_r = matl[1][0]
        spec_g = matl[1][1]
        spec_b = matl[1][2]
        emit_r = matl[2][0]
        emit_g = matl[2][1]
        emit_b = matl[2][2]
        spec_h = matl[3]

        mat_blender = bpy.data.materials.new("{0}-{1}".format(matl[4], str(mat_counter)))
        blender_compat.enable_material_nodes(mat_blender)
        mat = o3d_node_shader_utils.PrincipledBSDFWrapper(mat_blender, is_readonly=False)
        mat.base_color = (diffuse_r, diffuse_g, diffuse_b)
        mat.alpha = diffuse_a
        mat.roughness = max(0., min(1., 1. - spec_h / 1000.))
        if max(emit_r, emit_g, emit_b) > 0:
            mat.emission_color = (emit_r, emit_g, emit_b)
            mat.emission_strength = 1.0
        if bpy.app.version >= (4, 0):
            specular_strength = max(spec_r, spec_g, spec_b)
            mat.specular = specular_strength
            if specular_strength > 0:
                mat.specular_tint = tuple(
                    channel / specular_strength
                    for channel in (spec_r, spec_g, spec_b)
                )
            else:
                mat.specular_tint = (0, 0, 0)
        else:
            mat.specular = spec_r
            mat.specular_tint = 0

        mat_blender.use_backface_culling = True
        blender_compat.set_material_alpha_mode(mat_blender, "HASHED")

        # Load the diffuse texture and assign it to a new texture slot
        diff_tex = load_texture_into_new_slot(cfg_file_path, matl[4], mat) if matl[4] else None
        if diff_tex is None and matl[4]:
            image = bpy.data.images.new(matl[4], width=1, height=1)
            image.source = 'FILE'
            image.filepath = matl[4]
            diff_tex = TextureSlotWrapper(image)
        if diff_tex:
            mat.base_color_texture.image = diff_tex.texture.image

            # In some versions of Blender the colourspace isn't correctly detected, force it to sRGB for diffuse
            diff_tex.texture.image.colorspace_settings.name = 'sRGB'
            diff_tex.texture.image.alpha_mode = "NONE"
        # Read the material config to see if we need to apply transparency
        if key in cfg_materials and "diffuse" in cfg_materials[key]:
            if diff_tex and "alpha" in cfg_materials[key] and cfg_materials[key]["alpha"][0] > 0:
                # Material uses alpha stored in diffuse texture alpha channel
                mat.alpha_texture.image = diff_tex.texture.image
                if cfg_materials[key]["alpha"][0] == 1:
                    blender_compat.set_material_alpha_mode(mat_blender, "CLIP")
                else:
                    blender_compat.set_material_alpha_mode(mat_blender, "HASHED")

                mat.alpha = 0

            if "transmap" in cfg_materials[key]:
                # Material uses dedicated transparency texture
                # Set the specular texture to the alpha channel of the diffuse texture
                if diff_tex:
                    mat.specular_texture.image = diff_tex.texture.image
                # Load the new transmap
                trans_map = load_texture_into_new_slot(cfg_file_path, cfg_materials[key]["transmap"][0], mat)
                if trans_map:
                    mat.alpha_texture.image = trans_map.texture.image
                    blender_compat.set_material_alpha_mode(mat_blender, "HASHED")
                else:
                    mat.alpha = 1

            if "envmap" in cfg_materials[key]:
                mat.specular = cfg_materials[key]["envmap"][0] ** 2
                mat.roughness = 0.01

                if "envmap_mask" in cfg_materials[key]:
                    # Load the new transmap
                    envmap_mask = load_texture_into_new_slot(cfg_file_path, cfg_materials[key]["envmap_mask"][0],
                                                             mat)
                    if envmap_mask:
                        # TODO: Doesn't multiply by the envmap strength
                        mat.specular_texture.image = envmap_mask.texture.image

            if "bumpmap" in cfg_materials[key]:
                bump = load_texture_into_new_slot(cfg_file_path, cfg_materials[key]["bumpmap"][0], mat)
                if bump is not None:
                    blender_compat.apply_bump_map(mat, bump.texture.image,
                                                  cfg_materials[key]["bumpmap_strength"][0])

            if "alphascale" in cfg_materials[key]:
                # TODO: parameterize the default alphascale value
                # mat_blender.blend_method = "BLEND"
                # TODO: alpha_hash doesn't work correctly on  z-intersecting faces (a frequent problem with dirt maps)
                pass

            if "allcolor" in cfg_materials[key]:
                # TODO: Work out if this is meant to override the material values or not
                # Allcolor allows material properties to be set to constant values
                allcolor = cfg_materials[key]["allcolor"]
                mat.base_color = [x[0] for x in allcolor[0:3]]
                mat.alpha = allcolor[3][0]
                emission = [allcolor[4][0] * 0.1 + allcolor[10][0],
                            allcolor[5][0] * 0.1 + allcolor[11][0],
                            allcolor[6][0] * 0.1 + allcolor[12][0]]
                mat.emission_color = emission
                # The allcolor emission values always seem to look bad, for now it's just disabled
                mat.emission_strength = 0
                mat.specular = sum([x[0] for x in allcolor[7:10]]) / 3
                spec_h = allcolor[13][0]
                mat.roughness = max(0., min(1., 1. - spec_h / 1000.))

            if "nightmap" in cfg_materials[key]:
                # A nightmap is an emission texture which is automatically toggled at night
                nightmap = load_texture_into_new_slot(cfg_file_path, cfg_materials[key]["nightmap"][0], mat)
                if nightmap is not None:
                    mat.emission_color_texture.image = nightmap.texture.image
                    # TODO: Parameterise the nightmaps and lightmaps
                    mat.emission_strength = 0.5

            if "lightmap" in cfg_materials[key]:
                # A lightmap is an emission texture which is controlled by a script_var
                lightmap = load_texture_into_new_slot(cfg_file_path, cfg_materials[key]["lightmap"][0], mat)
                if lightmap is not None:
                    mat.emission_color_texture.image = lightmap.texture.image
                    mat.emission_strength = 1.5

            # Populate some useful properties
            bpy.data.materials[mat_blender.name]["type"] = cfg_materials[key]["type"]
            # bpy.data.materials[mat_blender.name]["mat_id"] = cfg_materials[key]["mat_id"]
            if cfg_materials[key]["type"] == "[matl_change]":
                bpy.data.materials[mat_blender.name]["change_var"] = cfg_materials[key]["change_var"]
            if "envmap_tex" in cfg_materials[key]:
                bpy.data.materials[mat_blender.name]["envmap_tex"] = cfg_materials[key]["envmap_tex"]

            # Preserve explicit raw blocks independently of lossy preview inputs.
            blocks = [list(block) for block in cfg_materials[key].get('cfg_data', [])]
            blocks.extend([name, *values] for name, values in cfg_materials[key].items()
                          if name.startswith('[') and name.endswith(']'))
            mat_blender['cfg_data'] = blocks

        # Capture each component only after all effective CFG preview processing.
        # Embedded RGB/A remain native truth; power follows explicit allcolor.
        mat_blender['o3d_specular_power'] = float(spec_h)
        mat_blender['o3d_specular_roughness'] = float(mat.roughness)
        raw = {'diffuse': matl[0][:3], 'alpha': (matl[0][3],),
               'specular': matl[1], 'emission': matl[2]}
        for component, names in _MATERIAL_COMPONENTS.items():
            mat_blender['o3d_raw_' + component] = list(raw[component])
            mat_blender['o3d_preview_' + component] = _material_preview(mat, names)

        mesh.materials.append(mat_blender)
        mat_counter += 1
    return mat_counter
