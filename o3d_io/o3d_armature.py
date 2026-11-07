"""Build Blender armatures from O3D bone influence records."""
import math

import bpy
from mathutils import Vector


CANONICAL_PARENTS = {
    "Hip": "Main",
    "Head": "Main",
    "OA_L": "Main",
    "OA_R": "Main",
    "UA_L": "OA_L",
    "UA_R": "OA_R",
    "Hand_L": "UA_L",
    "Hand_R": "UA_R",
    "OS_L": "Hip",
    "OS_R": "Hip",
    "US_L": "OS_L",
    "US_R": "OS_R",
}

_TEMPLATE = {
    "Main": (0.0, 0.0, 0.50),
    "Hip": (0.0, 0.0, 0.42),
    "Head": (0.0, 0.0, 0.88),
    "OA_L": (-0.16, 0.0, 0.78),
    "OA_R": (0.16, 0.0, 0.78),
    "UA_L": (-0.32, 0.0, 0.56),
    "UA_R": (0.32, 0.0, 0.56),
    "Hand_L": (-0.43, 0.0, 0.38),
    "Hand_R": (0.43, 0.0, 0.38),
    "OS_L": (-0.10, 0.0, 0.30),
    "OS_R": (0.10, 0.0, 0.30),
    "US_L": (-0.12, 0.0, 0.10),
    "US_R": (0.12, 0.0, 0.10),
}


def create_armature_for_mesh(
    mesh_object: bpy.types.Object,
    bones: list[tuple[str, list[tuple[int, float]]]],
) -> bpy.types.Object | None:
    """Create an armature, parent the mesh to it, and add its modifier."""
    if mesh_object.type != "MESH":
        print(f"[O3D_Armature] {mesh_object.name}: source is not a mesh")
        return None

    normalized = {}
    for bone_name, influences in bones:
        if not bone_name:
            continue
        weights = normalized.setdefault(bone_name, {})
        for vertex_index, weight in influences:
            try:
                valid = (
                    0 <= vertex_index < len(mesh_object.data.vertices)
                    and math.isfinite(weight)
                    and weight >= 0.0
                )
            except (TypeError, ValueError):
                valid = False
            if not valid:
                print(
                    f"[O3D_Armature] {mesh_object.name}: ignoring invalid influence "
                    f"for {bone_name!r}: ({vertex_index!r}, {weight!r})"
                )
                continue
            weights[vertex_index] = max(weights.get(vertex_index, 0.0), weight)

    if not normalized:
        return None

    coordinates = [vertex.co.copy() for vertex in mesh_object.data.vertices]
    if coordinates:
        minimum = Vector(tuple(min(co[axis] for co in coordinates) for axis in range(3)))
        maximum = Vector(tuple(max(co[axis] for co in coordinates) for axis in range(3)))
        scale = max((maximum - minimum).length, 0.001)
        center = (minimum + maximum) * 0.5
    else:
        scale = 0.001
        center = Vector((0.0, 0.0, 0.0))

    centroids = {}
    for bone_name, weights in normalized.items():
        total = sum(weight for weight in weights.values() if weight > 0.0)
        if total:
            centroids[bone_name] = sum(
                (coordinates[index] * weight for index, weight in weights.items() if weight > 0.0),
                Vector((0.0, 0.0, 0.0)),
            ) / total
        else:
            centroids[bone_name] = None

    def position(name):
        point = centroids[name]
        if point is not None:
            return point.copy()
        template = _TEMPLATE.get(name, (0.0, 0.0, 0.5))
        return center + Vector(template) * scale

    armature_data = None
    armature_object = None
    try:
        armature_data = bpy.data.armatures.new(f"{mesh_object.name} Armature")
        armature_object = bpy.data.objects.new(f"{mesh_object.name} Armature", armature_data)
        collections = mesh_object.users_collection
        (collections[0] if collections else bpy.context.scene.collection).objects.link(armature_object)

        if bpy.context.object and bpy.context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        armature_object.select_set(True)
        bpy.context.view_layer.objects.active = armature_object
        bpy.ops.object.mode_set(mode="EDIT")
        edit_bones = {}
        for name in normalized:
            bone = armature_data.edit_bones.new(name)
            bone.head = position(name)
            child = next(
                (child_name for child_name, parent_name in CANONICAL_PARENTS.items()
                 if parent_name == name and child_name in normalized
                 and centroids[child_name] is not None
                 and (position(child_name) - bone.head).length > 1e-6),
                None,
            )
            if child is not None:
                bone.tail = position(child)
            else:
                template = _TEMPLATE.get(name, (0.0, 0.0, 0.5))
                direction = Vector(template)
                if direction.length <= 1e-6:
                    direction = Vector((0.0, 0.0, 1.0))
                bone.tail = bone.head + direction.normalized() * max(scale * 0.1, 0.001)
            if (bone.tail - bone.head).length <= 1e-6:
                bone.tail = bone.head + Vector((0.0, 0.0, max(scale * 0.1, 0.001)))
            edit_bones[name] = bone

        for name, parent_name in CANONICAL_PARENTS.items():
            if name in edit_bones and parent_name in edit_bones:
                edit_bones[name].parent = edit_bones[parent_name]
        bpy.ops.object.mode_set(mode="OBJECT")
        mesh_object.parent = armature_object
        modifier = mesh_object.modifiers.new("Armature", "ARMATURE")
        modifier.object = armature_object
        return armature_object
    except Exception as exception:
        print(f"[O3D_Armature] {mesh_object.name}: armature construction failed: {exception}")
        if bpy.context.object and bpy.context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        if armature_object is not None and armature_object.name in bpy.data.objects:
            bpy.data.objects.remove(armature_object, do_unlink=True)
        elif armature_data is not None and armature_data.name in bpy.data.armatures:
            bpy.data.armatures.remove(armature_data)
        return None
