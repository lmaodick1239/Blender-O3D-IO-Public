# ==============================================================================
#  Copyright (c) 2022-2023 Thomas Mathieson.
# ==============================================================================
import math
import os

import mathutils

import bpy
if bpy.app.version >= (4, 0):
    from bpy_extras import node_shader_utils as o3d_node_shader_utils
else:
    from . import o3d_node_shader_utils
from . import blender_compat
from .omsi_paths import resolve_omsi_path, resolve_case_insensitive_path


def log(*args):
    print("[O3D_CFG_Parser]", *args)


def read_generic_cfg_file(cfg_path):
    """
    Loads and parses a generic cfg file into a dictionary
    :param cfg_path: the absolute file path to load the cfg from
    :return: a dict with the cfg command (including square brackets) as the key and a list of instances (which are
             lists of lines) as values
    """
    cfg_path = resolve_case_insensitive_path(cfg_path)
    try:
        with open(cfg_path, 'r', encoding="utf-8") as f:
            lines = [l.rstrip() for l in f.readlines()]
    except:
        with open(cfg_path, 'r', encoding="utf-16-le", errors="replace") as f:
            lines = [l.rstrip() for l in f.readlines()]

    cfg_data = {}

    current_command = None
    current_command_start = None
    param_ind = -1
    for i, line in enumerate(lines):
        if len(line) > 2 and line[0] == "[" and line[-1] == "]":
            # Append the line number to the end of the arguments list for order sensitive commands
            if current_command is not None:
                cfg_data[current_command][-1].append(current_command_start)
                cfg_data[current_command][-1].append(current_command)

            current_command = line
            current_command_start = str(i)
            param_ind = -1
        else:
            param_ind += 1

        if current_command is not None:
            # Current command is not currently parsed
            if param_ind == -1:
                if current_command in cfg_data:
                    cfg_data[current_command].append([])
                else:
                    cfg_data[current_command] = [[]]
            if param_ind >= 0:
                cfg_data[current_command][-1].append(line)

    # Append the line number to the end of the arguments list for order sensitive commands
    if current_command is not None:
        cfg_data[current_command][-1].append(current_command_start)
        cfg_data[current_command][-1].append(current_command)

    return cfg_data


def read_cfg(filepath, override_text_encoding):
    r"""
    Reads the CFG file for a mesh and parses relevant information such as materials.

    The `cfg_data` dictionary returned is of the following form:
    ::
        cfg_data = {
            0.06: {
                "SD85\SD85_spiegel.o3d": {
                    "viewpoint": ...
                    "matls": {
                        ("sd84-85_03.bmp", 0): {
                            "diffuse": ("SD84-85_03.bmp", 0),
                            "mat_id": 0,
                            "envmap": 0.5,
                            "last_line": 4673
                        },
                    }
                }
            },
        }

    :param filepath: Path to the CFG file to parse
    :param override_text_encoding: the text encoding to use to read the file instead of utf8/cp1252
    :return: (An array of model file paths (.o3d/.x),
      An array of light entity names,
      The cfg_data dictionary: {lod: {mesh/path: {'matls': {(texture_path, mat_id):{ material properties...}}, mesh properties}}},
      The root folder of the material).
    """
    filepath = resolve_case_insensitive_path(filepath)
    # get the folder
    folder = (os.path.dirname(filepath))
    folder_model = os.path.join(folder, "model")

    # log("Loading " + filepath)
    encoding = override_text_encoding if override_text_encoding.strip() != "" else "1252"
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            lines = [l.rstrip() for l in f.readlines()]
    except:
        # Try a different encoding
        with open(filepath, 'r', encoding="utf-8") as f:
            lines = [l.rstrip() for l in f.readlines()]

    cfg_data = {
        -1: {
            "meshes": {},
            "surface": False,
            "cfg_data": [],
            "maplights": [],
            "light_flares": [],
            "interior_lights": [],
            "spotlights": [],
        }
    }
    lights = []

    current_command = None
    current_lod = -1
    current_mat = None
    current_mesh = None
    param_ind = -1
    interior_light_ind = 0
    spotlight_ind = 0
    iter_lines = iter(enumerate(lines))
    for i, line in iter_lines:
        if len(line) > 2 and line[0] == "[" and line[-1] == "]":
            current_command = line
            param_ind = -1
        else:
            param_ind += 1

        if current_command == "[LOD]":
            if param_ind == 0:
                current_lod = float(line)
                current_mesh = None
                current_mat = None
                cfg_data[current_lod] = {
                    "meshes": {},
                    "surface": False,
                    "cfg_data": [],
                    "maplights": [],
                    "light_flares": [],
                    "interior_lights": [],
                    "spotlights": [],
                }

        elif current_command == "[groups]":
            if param_ind == -1:
                cfg_data[current_lod]["groups"] = {}
            elif param_ind == 0:
                cfg_data[current_lod]["groups"]["ind"] = int(line)
            elif param_ind == 1:
                cfg_data[current_lod]["groups"]["group"] = line

        elif current_command == "[friendlyname]":
            if param_ind == 0:
                cfg_data[current_lod]["friendlyname"] = line

        elif current_command == "[surface]":
            cfg_data[current_lod]["surface"] = True

        elif current_command == "[editor_only]":
            cfg_data[current_lod]["editor_only"] = True

        elif current_command == "[maplight]":
            if param_ind == -1:
                cfg_data[current_lod]["maplights"].append({})
                cfg_data[current_lod]["maplights"][-1]["x"] = float(next(iter_lines)[1])
                cfg_data[current_lod]["maplights"][-1]["y"] = float(next(iter_lines)[1])
                cfg_data[current_lod]["maplights"][-1]["z"] = float(next(iter_lines)[1])
                cfg_data[current_lod]["maplights"][-1]["r"] = float(next(iter_lines)[1])
                cfg_data[current_lod]["maplights"][-1]["g"] = float(next(iter_lines)[1])
                cfg_data[current_lod]["maplights"][-1]["b"] = float(next(iter_lines)[1])
                cfg_data[current_lod]["maplights"][-1]["range"] = float(next(iter_lines)[1])
                lights.append(cfg_data[current_lod]["maplights"][-1])

        elif current_command == "[tree]":
            if param_ind == -1:
                cfg_data[current_lod]["tree"] = {}
                cfg_data[current_lod]["tree"]["texture"] = next(iter_lines)[1]
                cfg_data[current_lod]["tree"]["min_height"] = float(next(iter_lines)[1])
                cfg_data[current_lod]["tree"]["max_height"] = float(next(iter_lines)[1])
                cfg_data[current_lod]["tree"]["min_aspect"] = float(next(iter_lines)[1])
                cfg_data[current_lod]["tree"]["max_aspect"] = float(next(iter_lines)[1])

        elif current_command == "[mesh]":
            if param_ind == 0:
                current_mat = None
                mesh_path = resolve_omsi_path(folder, line, encoding)
                if not os.path.isfile(mesh_path):
                    mesh_path = resolve_omsi_path(folder_model, line, encoding)
                current_mesh = line

                cfg_data[current_lod]["meshes"][current_mesh] = {
                    "path": mesh_path,
                    "matls": {},
                    "cfg_data": []
                }

        # elif current_command == "[viewpoint]":
        #     if param_ind == 0:
        #         cfg_data[current_lod]["meshes"][current_mesh]["viewpoint"] = (int(line), i)

        elif current_command == "[interiorlight]":
            if param_ind == -1:
                interior_light_ind += 1
                cfg_data[current_lod]["interior_lights"].append({})
                lights.append(cfg_data[current_lod]["interior_lights"][-1])
                cfg_data[current_lod]["interior_lights"][-1]["variable"] = next(iter_lines)[1]
                cfg_data[current_lod]["interior_lights"][-1]["range"] = float(next(iter_lines)[1])
                cfg_data[current_lod]["interior_lights"][-1]["red"] = float(next(iter_lines)[1]) / 255
                cfg_data[current_lod]["interior_lights"][-1]["green"] = float(next(iter_lines)[1]) / 255
                cfg_data[current_lod]["interior_lights"][-1]["blue"] = float(next(iter_lines)[1]) / 255
                cfg_data[current_lod]["interior_lights"][-1]["x_pos"] = float(next(iter_lines)[1])
                cfg_data[current_lod]["interior_lights"][-1]["y_pos"] = float(next(iter_lines)[1])
                cfg_data[current_lod]["interior_lights"][-1]["z_pos"] = float(next(iter_lines)[1])

        elif current_command == "[spotlight]":
            if param_ind == -1:
                spotlight_ind += 1
                cfg_data[current_lod]["spotlights"].append({})
                lights.append(cfg_data[current_lod]["spotlights"][-1])

                m_light = cfg_data[current_lod]["spotlights"][-1]
                m_light["x_pos"] = float(next(iter_lines)[1])
                m_light["y_pos"] = float(next(iter_lines)[1])
                m_light["z_pos"] = float(next(iter_lines)[1])
                m_light["x_fwd"] = float(next(iter_lines)[1])
                m_light["y_fwd"] = float(next(iter_lines)[1])
                m_light["z_fwd"] = float(next(iter_lines)[1])
                m_light["col_r"] = float(next(iter_lines)[1]) / 255
                m_light["col_g"] = float(next(iter_lines)[1]) / 255
                m_light["col_b"] = float(next(iter_lines)[1]) / 255
                m_light["range"] = float(next(iter_lines)[1])
                m_light["inner_angle"] = float(next(iter_lines)[1])
                m_light["outer_angle"] = float(next(iter_lines)[1])

        elif current_command == "[light_enh]":
            if param_ind == -1:
                cfg_data[current_lod]["light_flares"].append({"type": "[light_enh]", "texture": ""})
                light_flare = cfg_data[current_lod]["light_flares"][-1]
                light_flare["x_pos"] = float(next(iter_lines)[1])
                light_flare["y_pos"] = float(next(iter_lines)[1])
                light_flare["z_pos"] = float(next(iter_lines)[1])
                light_flare["col_r"] = float(next(iter_lines)[1]) / 255
                light_flare["col_g"] = float(next(iter_lines)[1]) / 255
                light_flare["col_b"] = float(next(iter_lines)[1]) / 255
                light_flare["size"] = float(next(iter_lines)[1])
                light_flare["brightness_var"] = next(iter_lines)[1]
                light_flare["brightness"] = float(next(iter_lines)[1])
                light_flare["z_offset"] = float(next(iter_lines)[1])
                light_flare["effect"] = int(next(iter_lines)[1])
                light_flare["ramp_time"] = float(next(iter_lines)[1])
            elif param_ind == 0:
                light_flare["texture"] = line

        elif current_command == "[light_enh_2]":
            if param_ind == -1:
                cfg_data[current_lod]["light_flares"].append({"type": "[light_enh_2]", "texture": ""})
                light_flare = cfg_data[current_lod]["light_flares"][-1]
                light_flare["x_pos"] = float(next(iter_lines)[1])
                light_flare["y_pos"] = float(next(iter_lines)[1])
                light_flare["z_pos"] = float(next(iter_lines)[1])
                light_flare["x_fwd"] = float(next(iter_lines)[1])
                light_flare["y_fwd"] = float(next(iter_lines)[1])
                light_flare["z_fwd"] = float(next(iter_lines)[1])
                light_flare["x_rot"] = float(next(iter_lines)[1])
                light_flare["y_rot"] = float(next(iter_lines)[1])
                light_flare["z_rot"] = float(next(iter_lines)[1])
                light_flare["omni"] = int(next(iter_lines)[1]) == 1
                light_flare["rotating"] = int(next(iter_lines)[1])
                light_flare["col_r"] = float(next(iter_lines)[1]) / 255
                light_flare["col_g"] = float(next(iter_lines)[1]) / 255
                light_flare["col_b"] = float(next(iter_lines)[1]) / 255
                light_flare["size"] = float(next(iter_lines)[1])
                light_flare["max_brightness_angle"] = float(next(iter_lines)[1])
                light_flare["min_brightness_angle"] = float(next(iter_lines)[1])
                light_flare["brightness_var"] = next(iter_lines)[1]
                light_flare["brightness"] = float(next(iter_lines)[1])
                light_flare["z_offset"] = float(next(iter_lines)[1])
                light_flare["effect"] = int(next(iter_lines)[1])
                light_flare["cone_effect"] = int(next(iter_lines)[1]) == 1
                light_flare["ramp_time"] = float(next(iter_lines)[1])
            elif param_ind == 0:
                light_flare["texture"] = line

        elif current_command == "[matl]" or current_command == "[matl_change]":
            if param_ind == 0:
                matl = line.lower()
                current_mat = (matl, None)
                cfg_data[current_lod]["meshes"][current_mesh]["matls"][current_mat] = {
                    "diffuse": (line, i),
                    "type": current_command,
                    "cfg_data": []
                }
            elif param_ind == 1:
                matls = cfg_data[current_lod]["meshes"][current_mesh]["matls"]
                material = matls.pop(current_mat)
                material["mat_id"] = int(line)
                current_mat = (material["diffuse"][0].lower(), material["mat_id"])
                matls[current_mat] = material
            elif current_command == "[matl_change]" and param_ind == 2:
                cfg_data[current_lod]["meshes"][current_mesh]["matls"][current_mat]["change_var"] = line

        elif current_command == "[matl_alpha]":
            if current_mat is None:
                log("Invalid command {0} at line {1}! Must precede a [matl] command!".format(current_command, i))
                continue

            if param_ind == 0:
                try:
                    cfg_data[current_lod]["meshes"][current_mesh]["matls"][current_mat]["alpha"] = (int(line), i)
                except ValueError:
                    log("Found matl_alpha tag with invalid parameter! Line=" + str(i))

        elif current_command == "[matl_transmap]":
            if current_mat is None:
                log("Invalid command {0} at line {1}! Must precede a [matl] command!".format(current_command, i))
                continue

            if param_ind == 0:
                cfg_data[current_lod]["meshes"][current_mesh]["matls"][current_mat]["transmap"] = (line, i)

        elif current_command == "[matl_envmap]":
            if current_mat is None:
                log("Invalid command {0} at line {1}! Must precede a [matl] command!".format(current_command, i))
                continue

            # TODO: Load the actual transmap
            if param_ind == 0:
                cfg_data[current_lod]["meshes"][current_mesh]["matls"][current_mat]["envmap_tex"] = line
            if param_ind == 1:
                cfg_data[current_lod]["meshes"][current_mesh]["matls"][current_mat]["envmap"] = (float(line), i)

        elif current_command == "[matl_envmap_mask]":
            if current_mat is None:
                log("Invalid command {0} at line {1}! Must precede a [matl] command!".format(current_command, i))
                continue

            if param_ind == 0:
                cfg_data[current_lod]["meshes"][current_mesh]["matls"][current_mat]["envmap_mask"] = (line, i)

        elif current_command == "[matl_bumpmap]":
            if current_mat is None:
                log("Invalid command {0} at line {1}! Must precede a [matl] command!".format(current_command, i))
                continue

            if param_ind == 0:
                cfg_data[current_lod]["meshes"][current_mesh]["matls"][current_mat]["bumpmap"] = (line, i)
            if param_ind == 1:
                cfg_data[current_lod]["meshes"][current_mesh]["matls"][current_mat]["bumpmap_strength"] = (
                    float(line), i)

        elif current_command == "[alphascale]":
            if current_mat is None:
                log("Invalid command {0} at line {1}! Must precede a [matl] command!".format(current_command, i))
                continue

            if param_ind == 0:
                cfg_data[current_lod]["meshes"][current_mesh]["matls"][current_mat]["alphascale"] = (line, i)

            # alphascale is not currently exported correctly, so we'll re-add it to the cfg_data as an unparsed command
            # so that it re-exports correctly
            if param_ind == -1:
                cfg_data[current_lod]["meshes"][current_mesh]["matls"][current_mat][current_command] = []
            else:
                cfg_data[current_lod]["meshes"][current_mesh]["matls"][current_mat][current_command].append(line)

        elif current_command == "[matl_noZwrite]":
            if current_mat is None:
                log("Invalid command {0} at line {1}! Must precede a [matl] command!".format(current_command, i))
                continue

            if param_ind == -1:
                cfg_data[current_lod]["meshes"][current_mesh]["matls"][current_mat]["noZwrite"] = True

            # alphascale is not currently exported correctly, so we'll re-add it to the cfg_data as an unparsed command
            # so that it re-exports correctly
            if param_ind == -1:
                cfg_data[current_lod]["meshes"][current_mesh]["matls"][current_mat][current_command] = []
            else:
                cfg_data[current_lod]["meshes"][current_mesh]["matls"][current_mat][current_command].append(line)

        elif current_command == "[matl_noZcheck]":
            if current_mat is None:
                log("Invalid command {0} at line {1}! Must precede a [matl] command!".format(current_command, i))
                continue

            if param_ind == -1:
                cfg_data[current_lod]["meshes"][current_mesh]["matls"][current_mat]["noZcheck"] = True

            # alphascale is not currently exported correctly, so we'll re-add it to the cfg_data as an unparsed command
            # so that it re-exports correctly
            if param_ind == -1:
                cfg_data[current_lod]["meshes"][current_mesh]["matls"][current_mat][current_command] = []
            else:
                cfg_data[current_lod]["meshes"][current_mesh]["matls"][current_mat][current_command].append(line)

        elif current_command == "[matl_allcolor]":
            if current_mat is None:
                log("Invalid command {0} at line {1}! Must precede a [matl] command!".format(current_command, i))
                continue

            if param_ind == -1:
                cfg_data[current_lod]["meshes"][current_mesh]["matls"][current_mat]["allcolor"] = []
            elif param_ind < 14:
                cfg_data[current_lod]["meshes"][current_mesh]["matls"][current_mat]["allcolor"].append((float(line), i))

            # Allcolor is not currently exported correctly, so we'll re-add it to the cfg_data as an unparsed command
            # so that it re-exports correctly
            if param_ind == -1:
                cfg_data[current_lod]["meshes"][current_mesh]["matls"][current_mat][current_command] = []
            else:
                cfg_data[current_lod]["meshes"][current_mesh]["matls"][current_mat][current_command].append(line)

        elif current_command == "[matl_nightmap]":
            if current_mat is None:
                log("Invalid command {0} at line {1}! Must precede a [matl] command!".format(current_command, i))
                continue

            if param_ind == 0:
                cfg_data[current_lod]["meshes"][current_mesh]["matls"][current_mat]["nightmap"] = (line, i)

        elif current_command == "[matl_lightmap]":
            if current_mat is None:
                log("Invalid command {0} at line {1}! Must precede a [matl] command!".format(current_command, i))
                continue

            if param_ind == 0:
                cfg_data[current_lod]["meshes"][current_mesh]["matls"][current_mat]["lightmap"] = (line, i)

        # Unused commands are parsed and stored in the cfg_data dictionary, but they keep their square brackets so they
        # can be differentiated later.
        elif current_mat is not None:
            # Current command is not currently parsed
            if param_ind == -1:
                cfg_data[current_lod]["meshes"][current_mesh]["matls"][current_mat]["cfg_data"].append([current_command])
            else:
                cfg_data[current_lod]["meshes"][current_mesh]["matls"][current_mat]["cfg_data"][-1].append(line)

        elif current_mesh is not None:
            # Current command is not currently parsed
            if param_ind == -1:
                cfg_data[current_lod]["meshes"][current_mesh]["cfg_data"].append([current_command])
            else:
                cfg_data[current_lod]["meshes"][current_mesh]["cfg_data"][-1].append(line)

        elif current_lod is not None and current_command is not None:
            # Current command is not currently parsed
            if param_ind == -1:
                cfg_data[current_lod]["cfg_data"].append([current_command])
            else:
                cfg_data[current_lod]["cfg_data"][-1].append(line)

    return cfg_data, (folder + os.path.sep)


def write_additional_cfg_props(cfg_props, f, skip_commands=()):
    skip_commands = {str(command).strip().lower() for command in skip_commands}
    if cfg_props is not None and "cfg_data" in cfg_props:
        for prop in cfg_props["cfg_data"]:
            if prop and str(prop[0]).strip().lower() in skip_commands:
                continue
            f.write(prop[0] + "\n")
            f.write("\n".join(prop[1:]))
            f.write("\n")

            if len(prop) > 1 and prop[-1].strip() != "":
                f.write("\n")


def find_unbound_setbone_names(obj):
    """
    Return the names from preserved [setbone] entries that no longer match a
    vertex group with at least one vertex assigned a weight above zero.

    OMSI binds a bone name to an integer slot through [setbone], and skips
    entries whose name matches no loaded bone. The CFG parser stores [setbone]
    blocks verbatim under obj.data["cfg_data"], and under each material's
    "cfg_data" when the block followed a [matl] command. If a user renames or
    empties a vertex group in Blender, the preserved entry no longer matches any
    exported bone and OMSI silently stops deforming that bone. Comparison is
    exact and case-sensitive.
    """
    def _populated_group_names():
        names = set()
        for vert in obj.data.vertices:
            for group in vert.groups:
                if group.weight > 0.0:
                    names.add(obj.vertex_groups[group.group].name)
        return names

    entries = []
    data_cfg = obj.data.get("cfg_data")
    if data_cfg is not None:
        entries.extend(data_cfg)
    for slot in obj.material_slots:
        mat = slot.material
        if mat is None:
            continue
        mat_cfg = mat.get("cfg_data")
        if mat_cfg is not None:
            entries.extend(mat_cfg)

    populated = _populated_group_names()
    unbound = set()
    for entry in entries:
        # Entries are [command, line, ...]; trailing blank lines may follow.
        if not entry or str(entry[0]).strip() != "[setbone]":
            continue
        if len(entry) < 2:
            continue
        name = str(entry[1]).strip()
        if name and name not in populated:
            unbound.add(name)
    return unbound


def write_cfg_mesh(f, filepath, context, obj, smoothskin=None):
    if "export_path" in obj:
        export_path = obj["export_path"]
    else:
        export_path = obj.name + ".o3d"

    f.write("---------------------------------------------------------------\n"
            "\t\t{0}\n\n".format(export_path[:-4].upper()))
    f.write("[mesh]\n{0}\n\n".format(export_path))

    for name in sorted(find_unbound_setbone_names(obj)):
        log(f"Warning: [setbone] name '{name}' on object '{obj.name}' no longer matches "
            f"a vertex group with weights; OMSI will skip this bone.")

    write_additional_cfg_props(obj.data, f, skip_commands=("[smoothskin]",))
    if smoothskin:
        f.write("[smoothskin]\n\n")
    write_cfg_materials(f, obj)


def col_float_to_int(col):
    """
    Converts a Blender colour (rgb in the 0-1 range into the 0-255 (int) range)
    :param col:
    :return:
    """
    return (max(min(int(x*255), 255), 0) for x in col)


def write_cfg_empty(f, filepath, context, obj):
    if "type" not in obj:
        return

    pos = obj.location
    texture = os.path.basename(obj.data.filepath) if obj.data is not None else ""
    if texture == "licht.bmp":
        texture = ""

    f.write("----------\n")
    if obj["type"] == "[light_enh]":
        size = obj.empty_display_size

        f.write("[light_enh]\n")
        f.write("\n".join(map(str, (*pos[:3],
                                    *col_float_to_int(obj.color[:3]),
                                    size,
                                    obj["brightness_var"], obj["brightness"],
                                    obj["z_offset"], obj["effect"], obj["ramp_time"],
                                    texture))))
        f.write("\n\n")
    elif obj["type"] == "[light_enh_2]":
        size = obj.empty_display_size

        f.write("[light_enh_2]\n")
        f.write("\n".join(map(str, (*pos[:3],
                                    *obj["forward_vector"],
                                    *obj["rotation_axis"],
                                    1 if obj["omnidirectional"] else 0,
                                    obj["rotating"],
                                    *col_float_to_int(obj.color[:3]),
                                    size,
                                    obj["max_brightness_angle"], obj["min_brightness_angle"],
                                    obj["brightness_var"], obj["brightness"],
                                    obj["z_offset"], obj["effect"],
                                    1 if obj["cone_effect"] else 0, obj["ramp_time"],
                                    texture))))
        f.write("\n\n")

    write_additional_cfg_props(obj.data, f)


def write_cfg_light(f, filepath, context, obj):
    f.write("----------\n")
    if obj.data.type == "SPOT":
        spot_vec = mathutils.Vector((0, 0, 1))
        eul = mathutils.Euler(obj.rotation_euler, "XYZ")
        spot_vec.rotate(eul)
        spot_vec[2] = -spot_vec[2]
        spot_vec[1] = -spot_vec[1]

        f.write("[spotlight]\n")
        f.write("\n".join(map(str, (*obj.location,
                                    *spot_vec,
                                    *col_float_to_int(obj.data.color[:3]),
                                    obj.data.energy / 10,
                                    math.degrees(obj.data.spot_size * obj.data.spot_blend),
                                    math.degrees(obj.data.spot_size)))))
        f.write("\n\n")
    elif obj.data.type == "POINT":
        if "variable" in obj.data:
            light_var = obj.data["variable"]
        else:
            light_var = ""
        f.write("[interiorlight]\n")
        f.write("\n".join(map(str, (light_var,
                                    obj.data.energy / 10,
                                    *col_float_to_int(obj.data.color[:3]),
                                    *obj.location))))
        f.write("\n\n")

    write_additional_cfg_props(obj.data, f)


def write_cfg_materials(f, obj):
    for i, slot in enumerate(obj.material_slots):
        mat_blender = slot.material
        if mat_blender is None:
            continue
        mat = o3d_node_shader_utils.PrincipledBSDFWrapper(mat_blender, is_readonly=True)
        if mat.base_color_texture is not None and mat.base_color_texture.image is not None:
            f.write("----------\n")
            if "type" in mat_blender and mat_blender["type"] == "[matl_change]":
                f.write("[matl_change]\n{0}\n{1}\n{2}\n\n".format(
                    os.path.basename(mat.base_color_texture.image.filepath),
                    i,
                    mat_blender["change_var"]))
            else:
                f.write("[matl]\n{0}\n{1}\n\n".format(os.path.basename(mat.base_color_texture.image.filepath), i))

            transmap = False
            alpha_mode = 0
            envmap = False
            specular = 0
            bumpmap = None
            bumpmap_strength = 1.0
            emission_tex = None
            if mat.alpha_texture.image is not None:
                alpha_mode = 2
                if blender_compat.get_material_alpha_mode(mat_blender) == "CLIP":
                    alpha_mode = 1

                if mat.alpha_texture.image.filepath != mat.base_color_texture.image.filepath:
                    transmap = True

            if mat.roughness <= 0.1:
                envmap = True

            specular = math.sqrt(mat.specular)

            bump_map = blender_compat.find_bump_map(mat)
            if bump_map is not None:
                bumpmap = os.path.basename(bump_map[0].filepath)
                bumpmap_strength = bump_map[1]

            if mat.emission_color_texture is not None and mat.emission_color_texture.image is not None:
                emission_tex = os.path.basename(mat.emission_color_texture.image.filepath)

            if alpha_mode > 0:
                f.write("[matl_alpha]\n{0}\n\n".format(alpha_mode))

            if transmap:
                f.write("[matl_transmap]\n{0}\n\n".format(os.path.basename(mat.alpha_texture.image.filepath)))

            if envmap and specular > 0.01:
                envmap_tex = "envmap.bmp"
                if "envmap_tex" in mat_blender:
                    envmap_tex = mat_blender["envmap_tex"]

                f.write("[matl_envmap]\n{0}\n{1}\n\n".format(envmap_tex, specular))

                if not transmap and mat.specular_texture is not None and mat.specular_texture.image is not None:
                    f.write(
                        "[matl_envmap_mask]\n{0}\n\n".format(os.path.basename(mat.specular_texture.image.filepath)))

            if bumpmap is not None:
                f.write("[matl_bumpmap]\n{0}\n{1}\n\n".format(bumpmap, round(bumpmap_strength, 6)))

            if emission_tex is not None:
                # Again, this is a bit of a rubbish heuristic, it should be improved at some point
                if mat.emission_strength > 1:
                    f.write("[matl_lightmap]\n{0}\n\n".format(emission_tex))
                else:
                    f.write("[matl_nightmap]\n{0}\n\n".format(emission_tex))

            write_additional_cfg_props(mat_blender, f)


def write_cfg_object(context, f, filepath, obj, smoothskin=None):
    o_type = obj.type
    if o_type == "MESH":
        write_cfg_mesh(f, filepath, context, obj, smoothskin)
    elif o_type == "LIGHT":
        write_cfg_light(f, filepath, context, obj)
    elif o_type == "LAMP":
        write_cfg_light(f, filepath, context, obj)
    elif o_type == "EMPTY":
        write_cfg_empty(f, filepath, context, obj)
    else:
        log("Unsupported object type for export: {0} for {1}".format(obj.type, obj.name))


def write_cfg(filepath, objs, context, selection_only, *, smoothskin_by_object=None):
    """
    Writes the blender objects out as a new CFG/SCO file, replacing any file already at that path
    :param selection_only: whether to only export selected objects
    :param context: the current Blender context
    :param filepath: path to the cfg file to write
    :param objs: [Deprecated] the array of Blender objects to export
    :return:
    """
    with open(filepath, "w") as f:
        log("Writing cfg file...")
        scene = bpy.data.scenes[context.scene.name]
        if "groups" not in scene:
            scene["groups"] = {
                "ind": 1,
                "group": "BlenderExport"
            }
        if "friendlyname" not in scene:
            scene["friendlyname"] = os.path.basename(filepath)[:-4]

        # Create a new minimal CFG file
        f.write("""
###############################################################
# GENERATED BY BLENDER-O3D-IO COPYRIGHT THOMAS MATHIESON 2023 #
###############################################################

[groups]
{0}
{1}

[friendlyname]
{2}
    
""".format(scene["groups"]["ind"], scene["groups"]["group"], scene["friendlyname"]))

        # Populate any cfg data in the scene
        write_additional_cfg_props(scene, f)

        if "tree" in scene:
            tree = scene["tree"]
            f.write("[tree]\n{0}\n{1}\n{2}\n{3}\n{4}\n\n".format(*tree))

        if "editor_only" in scene and scene["editor_only"]:
            f.write("[editor_only]\n\n")

        f.write("\n###############################################################\n"
                "\t\tBEGIN MODEL DATA\n"
                "###############################################################\n\n")

        # Use active-scene membership, including hidden imported lower levels.
        selected = set(context.selected_objects) if selection_only else None
        eligible = [obj for obj in context.scene.objects
                    if obj.type in {"MESH", "LIGHT", "LAMP", "EMPTY"}
                    and "skip_export" not in obj and (selected is None or obj in selected)]
        eligible_set = set(eligible)
        buckets, visited = {}, set()
        pending = [context.scene.collection]
        while pending:
            collection = pending.pop()
            if collection in visited:
                continue
            visited.add(collection)
            pending.extend(collection.children)
            if not collection.name.startswith("LOD_"):
                continue
            try:
                factor = float(collection.name[4:])
                if not math.isfinite(factor) or factor < 0:
                    raise ValueError()
            except ValueError:
                log(f"Warning: ignoring invalid LOD collection name {collection.name!r}")
                continue
            buckets.setdefault(factor, set()).update(
                eligible_set.intersection(collection.all_objects))

        lod_objects = set().union(*buckets.values()) if buckets else set()
        for obj in eligible:
            if obj not in lod_objects:
                write_cfg_object(
                    context, f, filepath, obj,
                    (smoothskin_by_object or {}).get(id(obj), {}).get("smoothskin"),
                )

        for factor, members in sorted(buckets.items(), reverse=True):
            if not members:
                continue
            f.write("\n###############################################################\n"
                    "\t\tBEGIN LOD {0}\n"
                    "###############################################################\n\n".format(factor))
            f.write("[LOD]\n{0}\n\n".format(factor))
            for obj in eligible:
                if obj in members:
                    write_cfg_object(
                        context, f, filepath, obj,
                        (smoothskin_by_object or {}).get(id(obj), {}).get("smoothskin"),
                    )
