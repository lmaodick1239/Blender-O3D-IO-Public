"""Read-only MMD bone mapping and normalized OMSI weight preparation."""
from math import isfinite

from mathutils import Vector


CANONICAL_NAMES = (
    "Main", "Hip", "Head", "OA_L", "OA_R", "UA_L", "UA_R", "Hand_L", "Hand_R",
    "OS_L", "OS_R", "US_L", "US_R",
)
IGNORED_GROUPS = ("mmd_edge_scale", "mmd_vertex_order", "_shadow*", "_dummy*")
# First matching rule wins; sided targets require an explicit side marker.
BONE_RULES = (
    (("手首", "手先", "指"), "Hand"),
    (("腕捩",), "OA"),
    (("手捩", "ひじ"), "UA"),
    (("腕", "肩"), "OA"),
    (("足先EX", "つま先", "足首", "ひざ"), "US"),
    (("足",), "OS"),
    (("上半身", "胸"), "Main"),
    (("センター", "グルーブ", "腰", "下半身", "スカート"), "Hip"),
    (("頭", "首", "両目", "目", "眉", "口", "あご", "髪", "发", "马尾", "アホ毛", "UV_"), "Head"),
)


def _ignored(name):
    return any(name.startswith(pattern[:-1]) if pattern.endswith("*") else name == pattern
               for pattern in IGNORED_GROUPS)


def map_bone_name(name, target_names) -> str | None:
    """Match exact template names before ordered MMD rules, excluding controls."""
    if _ignored(name):
        return None
    if name in target_names:
        return name
    for fragments, target in BONE_RULES:
        if any(fragment in name for fragment in fragments):
            if target in ("Hand", "OA", "UA", "OS", "US"):
                left = name.endswith((".L", "_L")) or "左" in name
                right = name.endswith((".R", "_R")) or "右" in name
                if left == right:
                    return None
                target += "_L" if left else "_R"
            return target if target in target_names else None
    return None


def read_source_rig(armature) -> dict:
    """Return independent world-space rest segments in source bone order."""
    return {bone.name: (armature.matrix_world @ bone.head_local,
                        armature.matrix_world @ bone.tail_local)
            for bone in armature.data.bones}


def _nearest(point, segments):
    nearest, best = None, float("inf")
    for name, (head, tail) in segments.items():
        head, tail = Vector(head), Vector(tail)
        direction = tail - head
        factor = ((point - head).dot(direction) / direction.length_squared
                  if direction.length_squared else 0)
        closest = head + min(1, max(0, factor)) * direction
        distance = (point - closest).length_squared
        if distance < best:
            nearest, best = name, distance
    return nearest


def build_mapping(mesh, target_segments, keep_extra_bones=False) -> dict:
    """Map each weighted group once, using its world centroid for fallback."""
    mapping = {}
    centroids = {}
    masses = {}
    ignored = proximity = 0
    for group in mesh.vertex_groups:
        if _ignored(group.name):
            mapping[group.name] = None
            ignored += 1
            continue
        mapping[group.name] = map_bone_name(group.name, target_segments)
        if mapping[group.name] is None:
            centroids[group.index] = Vector((0, 0, 0))
            masses[group.index] = 0.0
    for vertex in mesh.data.vertices:
        for entry in vertex.groups:
            if entry.group in masses and isfinite(entry.weight) and entry.weight > 0:
                centroids[entry.group] += (mesh.matrix_world @ vertex.co) * entry.weight
                masses[entry.group] += entry.weight
    for group in mesh.vertex_groups:
        mass = masses.get(group.index, 0)
        if mass <= 0:
            continue
        if keep_extra_bones:
            base = f"mmd_{group.index}"
            target, index = base, 1
            while target in target_segments or target in mapping.values():
                target = f"{base}_{index}"
                index += 1
            mapping[group.name] = target
        else:
            mapping[group.name] = _nearest(centroids[group.index] / mass, target_segments)
            proximity += mapping[group.name] is not None
    print(f"[MMD_Rig] {mesh.name}: mapping ignored={ignored} proximity={proximity} "
          f"extras={sum(name is not None and name.startswith('mmd_') for name in mapping.values())}")
    return mapping


def merge_weights(mesh, mapping, max_influences=4, target_segments=None) -> dict:
    """Merge positive finite weights, cap by mass/source order, then normalize.

    Zero sums are repaired when world target segments are supplied; otherwise
    those vertices remain unweighted for the caller to handle.
    """
    if type(max_influences) is not int or not 1 <= max_influences <= 8:
        raise ValueError("max_influences must be an integer from 1 to 8")
    targets = {}
    order = {}
    for group in mesh.vertex_groups:
        target = None if _ignored(group.name) else mapping.get(group.name)
        targets[group.index] = target
        if target is not None:
            order.setdefault(target, group.index)
    result = {}
    mass = discarded = 0.0
    ignored = zero = 0
    for vertex in mesh.data.vertices:
        merged = {}
        for entry in vertex.groups:
            if not isfinite(entry.weight) or entry.weight <= 0:
                continue
            mass += entry.weight
            target = targets.get(entry.group)
            if target is None:
                ignored += 1
                discarded += entry.weight
                continue
            merged[target] = merged.get(target, 0.0) + entry.weight
        ranked = sorted(merged.items(), key=lambda item: (-item[1], order[item[0]]))
        discarded += sum(weight for _, weight in ranked[max_influences:])
        kept = ranked[:max_influences]
        total = sum(weight for _, weight in kept)
        if total > 0:
            for name, weight in kept:
                result.setdefault(name, []).append((vertex.index, weight / total))
        else:
            zero += 1
            if target_segments:
                name = _nearest(mesh.matrix_world @ vertex.co, target_segments)
                if name is not None:
                    result.setdefault(name, []).append((vertex.index, 1.0))
    print(f"[MMD_Rig] {mesh.name}: weights mass={mass:.6g} discarded_mass={discarded:.6g} "
          f"ignored={ignored} zero={zero}")
    return result


# Task 3 conversion API.  Keep the mapping/weight functions above pure so the
# UI and smoke checks can reuse them without mutating an MMD source object.
from copy import deepcopy
from dataclasses import dataclass

import bpy
from mathutils import Matrix

from .o3d_armature import CANONICAL_PARENTS


CANONICAL_SLOTS = {
    "OS_L": -2, "OS_R": -3, "US_L": -4, "US_R": -5,
    "OA_L": -6, "OA_R": -7, "UA_L": -8, "UA_R": -9,
    "Hip": -10, "Main": -11, "Head": -12, "Hand_L": -13, "Hand_R": -14,
}


@dataclass
class ConversionOptions:
    rig_mode: str = "AUTO"
    template_armature: object | None = None
    max_influences: int = 4
    remove_shape_keys: bool = True
    keep_extra_bones: bool = False
    delete_source_rig: bool = False
    target_collection: str = "OMSI_Converted"


@dataclass
class ConversionResult:
    mesh: object
    armature: object
    vertices: int
    groups: tuple
    bones: tuple
    merged_groups: tuple
    ignored_groups: tuple


def _is_armature_modifier(modifier):
    return modifier.type == "ARMATURE" and modifier.object is not None \
        and modifier.object.type == "ARMATURE"


def _mmd_root(obj):
    # mmd_tools registers mmd_root on EVERY Object; its presence is not evidence.
    return obj is not None and obj.type == "EMPTY" and (
        str(getattr(obj, "mmd_type", "")).upper() == "ROOT"
        or str(obj.get("mmd_type", "")).upper() == "ROOT")


def find_mmd_source(mesh):
    """Return modifier/parent source and confidence from actual MMD evidence."""
    if mesh is None or getattr(mesh, "type", None) != "MESH":
        return None, False
    names = [group.name for group in mesh.vertex_groups]
    evidence = any(name.startswith("mmd_") or any("\u3000" <= char <= "\u9fff" for char in name)
                   for name in names)
    chain = []
    parent = mesh.parent
    while parent is not None:
        chain.append(parent)
        parent = parent.parent
    root = next((obj for obj in chain if _mmd_root(obj)), None)
    for modifier in mesh.modifiers:
        if _is_armature_modifier(modifier):
            source = modifier.object
            ancestor = source.parent
            while ancestor is not None and not _mmd_root(ancestor):
                ancestor = ancestor.parent
            return source, bool(evidence or ancestor or root)
    for obj in chain:
        if obj.type == "ARMATURE":
            return obj, bool(evidence or root)
    if root:
        candidates = [obj for obj in root.children_recursive if obj.type == "ARMATURE"]
        if len(candidates) == 1:
            return candidates[0], True
    return None, False


def _unique_name(base, datablocks):
    if datablocks.get(base) is None:
        return base
    index = 1
    while datablocks.get(f"{base}.{index:03d}") is not None:
        index += 1
    return f"{base}.{index:03d}"


def _unique_export_path(source):
    from .omsi_paths import unique_export_path
    return unique_export_path(source, bpy.data.objects)


def _mesh_bounds(mesh):
    points = [mesh.matrix_world @ vertex.co for vertex in mesh.data.vertices]
    if not points:
        return Vector((0, 0, 0)), Vector((0, 0, 1))
    return (Vector((min(point[i] for point in points) for i in range(3))),
            Vector((max(point[i] for point in points) for i in range(3))))


def _source_segment(segments, fragments, side=None):
    # Ordered exact joint names: helper/twist substrings are not anatomical joints.
    for fragment in fragments:
        for name, segment in segments.items():
            left = name.endswith((".L", "_L")) or "左" in name
            right = name.endswith((".R", "_R")) or "右" in name
            if side and (left == right or (side == "L") != left):
                continue
            base = name
            if base.endswith((".L", "_L", ".R", "_R")):
                base = base[:-2]
            base = base.replace("左", "").replace("右", "")
            if base == fragment and (side or not (left or right)):
                return segment
    return None


def _canonical_points(mesh, source_armature):
    """Build world-space canonical segments from named MMD bones and bounds."""
    minimum, maximum = _mesh_bounds(mesh)
    center = (minimum + maximum) * 0.5
    scale = max((maximum - minimum).length, 0.001)
    source = read_source_rig(source_armature) if source_armature else {}

    def point(fragments, side=None, end=0):
        segment = _source_segment(source, fragments, side)
        if segment is None:
            return None
        return Vector(segment[end])

    def choose(value, fallback):
        return value if value is not None else fallback

    main = choose(point(("上半身", "上半身1", "胸")), center)
    hip = choose(point(("下半身", "腰", "センター")), center)
    head = choose(point(("頭", "首")), Vector((center.x, center.y, maximum.z)))
    points = {"Main": [main, head], "Hip": [hip, hip.copy()],
              "Head": [head, head + Vector((0, 0, max(scale * 0.1, 0.001)))]}
    for side, sign in (("L", -1), ("R", 1)):
        arm_direction = Vector((sign * scale * 0.15, 0, -scale * 0.1))
        leg_direction = Vector((sign * scale * 0.04, 0, -scale * 0.25))
        oa = choose(point(("腕", "肩"), side), main + Vector((sign * scale * 0.15, 0, scale * 0.15)))
        wrist = point(("手首",), side)
        ua = choose(point(("ひじ",), side), (oa + wrist) * 0.5 if wrist is not None else oa + arm_direction)
        wrist = choose(wrist, ua + (ua - oa if (ua - oa).length >= 0.001 else arm_direction))
        upper_leg = choose(point(("足",), side), hip + leg_direction)
        ankle = point(("足首",), side)
        knee = choose(point(("ひざ",), side), (upper_leg + ankle) * 0.5 if ankle is not None else upper_leg + leg_direction)
        ankle = choose(ankle, knee + Vector((0, 0, -max(scale * 0.25, 0.001))))
        points[f"OA_{side}"] = [oa, ua]
        points[f"UA_{side}"] = [ua, wrist]
        points[f"Hand_{side}"] = [wrist, wrist + (wrist - ua)]
        points[f"OS_{side}"] = [upper_leg, knee]
        points[f"US_{side}"] = [knee, ankle]
    points["Hip"][1] = (points["OS_L"][0] + points["OS_R"][0]) * 0.5
    for name, (head, tail) in points.items():
        if (tail - head).length < 0.001:
            points[name][1] = head + Vector((0, 0, -0.001 if name.startswith(("OS", "US", "Hip")) else 0.001))
    return {name: points[name] for name in CANONICAL_NAMES}


def _link_object(obj, collection):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    collection.objects.link(obj)


def _create_armature(name, segments, collection, matrix_world=None, extras=None):
    data = bpy.data.armatures.new(_unique_name(name + " Data", bpy.data.armatures))
    obj = bpy.data.objects.new(_unique_name(name, bpy.data.objects), data)
    collection.objects.link(obj)
    try:
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        if bpy.context.object and bpy.context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.mode_set(mode="EDIT")
        edit = {}
        for bone_name, (head, tail) in segments.items():
            bone = data.edit_bones.new(bone_name)
            bone.head, bone.tail = head, tail
            edit[bone_name] = bone
        for bone_name, parent_name in CANONICAL_PARENTS.items():
            if bone_name in edit and parent_name in edit:
                edit[bone_name].parent = edit[parent_name]
        for bone_name, (head, tail, parent_name) in (extras or {}).items():
            bone = data.edit_bones.new(bone_name)
            bone.head, bone.tail = head, tail
            if parent_name in edit:
                bone.parent = edit[parent_name]
        bpy.ops.object.mode_set(mode="OBJECT")
        obj.matrix_world = matrix_world if matrix_world is not None else Matrix.Identity(4)
        return obj
    except Exception:
        if bpy.context.object and bpy.context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.data.objects.remove(obj, do_unlink=True)
        if data.users == 0:
            bpy.data.armatures.remove(data)
        raise


def _extra_segments(mesh, mapping, segments):
    minimum, maximum = _mesh_bounds(mesh)
    scale = max((maximum - minimum).length, 0.001)
    extras = {}
    for target in dict.fromkeys(value for value in mapping.values() if value and value not in segments):
        source_names = [name for name, value in mapping.items() if value == target]
        weighted = []
        for group_name in source_names:
            group = mesh.vertex_groups.get(group_name)
            if group is None:
                continue
            for vertex in mesh.data.vertices:
                for entry in vertex.groups:
                    if entry.group == group.index and isfinite(entry.weight) and entry.weight > 0:
                        weighted.append((mesh.matrix_world @ vertex.co, entry.weight))
        if weighted:
            total = sum(weight for _, weight in weighted)
            head = sum((point * weight for point, weight in weighted), Vector()) / total
        else:
            head = (minimum + maximum) * 0.5
        extras[target] = (head, head + Vector((0, 0, max(scale * 0.05, 0.001))), _nearest(head, segments))
    return extras


def build_auto_armature(mesh, source_armature, mapping):
    """Create an identity, world-space OMSI armature with canonical parents."""
    points = _canonical_points(mesh, source_armature)
    return _create_armature(mesh.name + " OMSI Rig", points,
                            mesh.users_collection[0] if mesh.users_collection else bpy.context.scene.collection,
                            extras=_extra_segments(mesh, mapping, points))


def _add_template_extras(obj, extras):
    if not extras:
        return
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    inverse = obj.matrix_world.inverted()
    try:
        for name, (head, tail, parent) in extras.items():
            bone = obj.data.edit_bones.new(name)
            bone.head, bone.tail = inverse @ head, inverse @ tail
            if parent:
                bone.parent = obj.data.edit_bones[parent]
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")


def build_template_armature(template_armature):
    """Duplicate a template armature without changing rest bones or transform."""
    if template_armature is None or template_armature.type != "ARMATURE":
        raise ValueError("template_armature must be an armature object")
    data = template_armature.data.copy()
    obj = bpy.data.objects.new(_unique_name(template_armature.name + " Converted", bpy.data.objects), data)
    obj.matrix_world = template_armature.matrix_world.copy()
    collection = (template_armature.users_collection[0]
                  if template_armature.users_collection else bpy.context.scene.collection)
    collection.objects.link(obj)
    obj.name = _unique_name(template_armature.name + " Converted", bpy.data.objects)
    return obj


def _target_segments(armature):
    return read_source_rig(armature)


def _validate_targets(mesh, bone_names, merged_weights):
    for name, entries in merged_weights.items():
        if entries and name not in bone_names:
            raise ValueError(f"Weighted target {name!r} is absent from final rig")
        for vertex, weight in entries:
            if not 0 <= vertex < len(mesh.data.vertices) or not isfinite(weight) or weight <= 0:
                raise ValueError("invalid OMSI influence")


def validate_character_export(obj, **kwargs):
    """Shared evaluated rest-space HUMAN validation used by conversion and LODs."""
    from .io_o3d_export import validate_character_export as validate
    return validate(obj, **kwargs)


def preflight(mesh):
    """Report character export readiness without changing data, pointers or context."""
    import os
    from . import mmd_materials, omsi_paths

    messages = []
    if mesh is None or getattr(mesh, "type", None) != "MESH":
        messages.append(("ERROR", "Select a mesh object for character readiness"))
    else:
        try:
            # No chosen directory exists at this stage. Resolve against the
            # blend directory using the exact exporter containment/grammar helper.
            root = bpy.path.abspath('//')
            path = omsi_paths.safe_export_path(root, mesh.get('export_path', mesh.name + '.o3d'))
            key = os.path.normpath(path).casefold()
            for other in bpy.context.scene.objects:
                if other == mesh or other.type != 'MESH' or 'skip_export' in other:
                    continue
                try:
                    other_path = omsi_paths.safe_export_path(root, other.get('export_path', other.name + '.o3d'))
                except ValueError:
                    continue
                if os.path.normpath(other_path).casefold() == key:
                    raise ValueError(f"Output path collides with {other.name!r}: {path}")
        except ValueError as error:
            messages.append(("ERROR", str(error)))
        try:
            serialized = validate_character_export(mesh)
            extras = [name for name in serialized["bones"] if name not in CANONICAL_SLOTS]
            if extras:
                messages.append(("WARNING", f"Unbound extra bones need .hum bindings: {', '.join(extras)}"))
        except ValueError as error:
            messages.append(("ERROR", str(error)))
        if any(abs(sum(entry.weight for entry in vertex.groups
                       if isfinite(entry.weight) and entry.weight > 0) - 1) > .01
               for vertex in mesh.data.vertices):
            messages.append(("WARNING", "Vertex weights are not normalized (sum differs from 1 by more than 0.01)"))
        if any(_ignored(group.name) for group in mesh.vertex_groups):
            messages.append(("WARNING", "Helper vertex groups remain on the mesh"))
        if mesh.data.shape_keys is not None:
            messages.append(("WARNING", "Remaining shape keys must be removed before character LOD generation"))
        materials = {slot.material for slot in mesh.material_slots if slot.material is not None}
        if find_mmd_source(mesh)[1] or any(mmd_materials.mmd_nodes(mat) for mat in materials):
            messages.append(("WARNING", "MMD source or shader nodes remain; convert/flatten before export"))
        images = {node.image for mat in materials if mat.node_tree is not None
                  for node in mat.node_tree.nodes if node.type == 'TEX_IMAGE' and node.image is not None}
        for image in sorted(images, key=lambda item: item.name):
            if image.source in {'GENERATED', 'VIEWER'} or image.packed_file or image.packed_files:
                continue
            path = bpy.path.abspath(image.filepath, library=image.library)
            if not path or not os.path.isfile(omsi_paths.resolve_case_insensitive_path(path)):
                messages.append(("WARNING", f"Missing unpacked disk image: {image.name} ({image.filepath})"))
    if not messages:
        messages.append(("INFO", "Character export readiness checks passed; compatible .hum pivots are still required"))
    for severity, message in messages:
        print(f"[MMD_Preflight] {severity}: {message}")
    return messages


def _remove_shape_keys(obj):
    if obj.data.shape_keys is None:
        return
    basis = [point.co.copy() for point in obj.data.shape_keys.reference_key.data]
    obj.shape_key_clear()
    for vertex, coordinate in zip(obj.data.vertices, basis):
        vertex.co = coordinate
    obj.data.update()


def _copy_cfg_blocks(mesh):
    try:
        value = mesh.data.get("cfg_data", [])
        return deepcopy(list(value))
    except (TypeError, ValueError):
        return []


def _emit_cfg(mesh, has_smoothskin, bone_names=None):
    blocks = [block for block in _copy_cfg_blocks(mesh)
              if not block or str(block[0]).strip().lower() not in {"[setbone]", "[smoothskin]"}]
    for name in CANONICAL_NAMES:
        if bone_names is None or name in bone_names:
            blocks.append(["[setbone]", name, str(CANONICAL_SLOTS[name])])
    if has_smoothskin:
        blocks.append(["[smoothskin]"])
    mesh.data["cfg_data"] = blocks
    return blocks


def reconcile_character_bindings(mesh, bone_names, owned_materials=None):
    """Replace mesh bindings and privately remove conflicting material overrides."""
    # Modifiers can interpolate rigid source groups into blended exported vertices.
    serialized = validate_character_export(mesh)
    _emit_cfg(mesh, serialized["smoothskin"], bone_names)
    copies = {}
    for slot in mesh.material_slots:
        material = slot.material
        if material is None or "cfg_data" not in material:
            continue
        blocks = [list(block) for block in material["cfg_data"]]
        cleaned = [block for block in blocks if not block or
                   str(block[0]).strip().lower() not in {"[setbone]", "[smoothskin]"}]
        if cleaned == blocks:
            continue
        if material not in copies:
            copy = material.copy()
            copies[material] = copy
            if owned_materials is not None:
                owned_materials.append(copy)
            copy["cfg_data"] = cleaned
        slot.material = copies[material]
    return tuple(copies.values())


def _write_mapping_text(pairs):
    if not pairs:
        return None, None, False
    text = bpy.data.texts.get("mmd_bone_name_map")
    created = text is None
    if created:
        text = bpy.data.texts.new("mmd_bone_name_map")
    old = text.as_string()
    additions = "".join(f"{source}\t{target}\n" for source, target in pairs)
    if additions not in old:
        text.write(("\n" if old and not old.endswith("\n") else "") + additions)
    return text, old, created


def _restore_context(active, selected, mode):
    try:
        active_name = active.name if active else None
    except ReferenceError:
        active_name = None
    try:
        selected_names = []
        for obj in selected:
            try:
                selected_names.append(obj.name)
            except ReferenceError:
                continue
        if bpy.context.object and bpy.context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        for name in selected_names:
            obj = bpy.data.objects.get(name)
            if obj is not None:
                obj.select_set(True)
        surviving_active = bpy.data.objects.get(active_name) if active_name else None
        bpy.context.view_layer.objects.active = surviving_active
        if surviving_active is not None:
            if mode != "OBJECT" and surviving_active.mode == "OBJECT":
                bpy.ops.object.mode_set(mode=mode)
    except (ReferenceError, RuntimeError):
        pass


def _validate_id_deletion(target, allowed_object=None, allowed_references=0):
    # user_map includes drivers/custom ID refs; .users is not a dependency count.
    for user in bpy.data.user_map(subset={target}).get(target, ()):
        expected = 0
        if isinstance(target, bpy.types.Object) and isinstance(user, bpy.types.Collection):
            expected = int(target.name in user.objects)
        elif isinstance(target, bpy.types.Object) and isinstance(user, bpy.types.Scene):
            expected = int(target.name in user.collection.objects)
            expected += sum(target.name in layer.objects for layer in user.view_layers)
        elif user == allowed_object:
            expected = allowed_references
        if user.user_of_id(target) != expected:
            raise ValueError(f"{target.name!r} has dependent ID user {user.name!r}")


def _validate_source_deletion(source, mesh):
    expected = int(mesh.parent == source)
    expected += sum(modifier.type == "ARMATURE" and modifier.object == source
                    for modifier in mesh.modifiers)
    _validate_id_deletion(source, mesh, expected)
    parent = source.parent
    if _mmd_root(parent) and all(child == source for child in parent.children):
        _validate_id_deletion(parent, source, 1)


def _remove_source_rig(source):
    parent = source.parent
    data = source.data
    # Explicit deletion leaves the source mesh unrigged, preserving its world pose.
    children = [(child, child.matrix_world.copy()) for child in source.children]
    for child, world in children:
        child.parent = None
        child.matrix_world = world
    bpy.data.objects.remove(source, do_unlink=True)
    if data and data.users == 0:
        bpy.data.armatures.remove(data)
    if _mmd_root(parent) and not parent.children:
        bpy.data.objects.remove(parent, do_unlink=True)


def _validate_world_transform(obj):
    matrix = obj.matrix_world
    determinant = matrix.determinant()
    if not all(isfinite(value) for row in matrix for value in row) or not isfinite(determinant):
        raise ValueError(f"{obj.name!r} world transform must be finite")
    if abs(determinant) < 1e-12:
        raise ValueError(f"{obj.name!r} world transform is singular")


def _validate_world_segments(armature):
    for name, (head, tail) in read_source_rig(armature).items():
        if not all(isfinite(value) for point in (head, tail) for value in point):
            raise ValueError(f"{armature.name!r} bone {name!r} world segment must be finite")
        length_squared = (tail - head).length_squared
        if not isfinite(length_squared) or length_squared <= 0:
            raise ValueError(f"{armature.name!r} bone {name!r} world segment has invalid length")


def _validate_group_modifiers(mesh):
    for modifier in mesh.modifiers:
        if modifier.type == "ARMATURE" or not (modifier.show_viewport or modifier.show_render):
            continue
        # Only known settings owners: never recurse through arbitrary RNA/IDs.
        owners = [modifier]
        if modifier.type in {"CLOTH", "SOFT_BODY"}:
            owners.append(modifier.settings)
        if modifier.type == "CLOTH":
            owners.append(modifier.collision_settings)
        elif modifier.type == "FLUID":
            owners.append(modifier.flow_settings)
        elif modifier.type == "PARTICLE_SYSTEM":
            particle = modifier.particle_system
            owners.append(particle)
            if particle is not None and particle.use_hair_dynamics and particle.cloth is not None:
                owners.extend((particle.cloth.settings, particle.cloth.collision_settings))
        # Conversion may merge, normalize or remove memberships. Keeping a
        # referenced name alone cannot preserve the modifier's semantics.
        for owner in owners:
            if owner is None:
                continue
            for prop in owner.bl_rna.properties:
                if prop.type == "STRING" and "vertex_group" in prop.identifier and getattr(owner, prop.identifier):
                    raise ValueError(f"Modifier {modifier.name!r} depends on vertex groups; "
                                     "apply/bake it before character conversion")


def _conversion_destination(name):
    # Reuse the LOD scene/layer interpretation; conversion must not implicitly
    # assign a character to an LOD bucket or write into a foreign scene.
    from .mesh_lod import _scene_paths

    collection = bpy.data.collections.get(name)
    if collection is None:
        if name.startswith('LOD_'):
            try:
                factor = float(name[4:])
            except ValueError:
                factor = None
            if factor is not None and isfinite(factor) and factor >= 0:
                raise ValueError(f"Conversion target {name!r} is an LOD bucket; choose an ordinary collection")
        return None
    scene = bpy.context.scene
    paths = _scene_paths(scene)
    if (collection.library or collection.override_library or not collection.is_editable
            or collection not in paths):
        raise ValueError(f"Conversion target {name!r} must be local, editable and in the active scene")
    if paths[collection]:
        raise ValueError(f"Conversion target {name!r} has LOD ancestry; choose an ordinary collection")
    if any(other != scene and collection in _scene_paths(other) for other in bpy.data.scenes):
        raise ValueError(f"Conversion target {name!r} belongs to another scene")

    def visible(layer):
        if layer.exclude or layer.hide_viewport or layer.collection.hide_viewport:
            return False
        return layer.collection == collection or any(visible(child) for child in layer.children)

    if not visible(bpy.context.view_layer.layer_collection):
        raise ValueError(f"Conversion target {name!r} must be visible in the active view layer")
    return collection


def convert(mesh, armature, options, *, on_complete=None):
    """Duplicate and bind an MMD mesh, then commit optional UI state atomically.

    on_complete(result) runs before optional source deletion. Its successful
    selection/context is retained; failures remove outputs and restore context.
    Callers without a callback retain the original context restoration behavior.
    """
    if not isinstance(options, ConversionOptions):
        raise TypeError("options must be ConversionOptions")
    if mesh is None or mesh.type != "MESH":
        raise ValueError("mesh must be a mesh object")
    if mesh.get("mmd_converted"):
        raise ValueError("mesh is already converted")
    if not mesh.data.vertices:
        raise ValueError("mesh must contain vertices")
    if options.rig_mode not in {"AUTO", "TEMPLATE"}:
        raise ValueError("rig_mode must be AUTO or TEMPLATE")
    if type(options.max_influences) is not int or not 1 <= options.max_influences <= 8:
        raise ValueError("max_influences must be an integer from 1 to 8")
    if not options.target_collection:
        raise ValueError("target_collection must not be empty")
    if armature is None:
        armature, is_mmd = find_mmd_source(mesh)
        if armature is None or not is_mmd:
            raise ValueError("no MMD armature source found")
    if armature.type != "ARMATURE":
        raise ValueError("armature must be an armature object")
    if not armature.data.bones:
        raise ValueError("source armature must contain bones")
    if mesh.data.shape_keys is not None and not options.remove_shape_keys:
        raise ValueError("remaining shape keys require remove_shape_keys=True")
    if options.rig_mode == "TEMPLATE":
        template = options.template_armature
        if template is None or template.type != "ARMATURE":
            raise ValueError("template_armature must be an armature object")
        if not template.data.bones:
            raise ValueError("template armature must contain bones")
        _validate_world_transform(template)
        _validate_world_segments(template)
    _validate_world_transform(mesh)
    _validate_world_transform(armature)
    _validate_world_segments(armature)
    _validate_group_modifiers(mesh)
    for constraint in mesh.constraints:
        if not constraint.mute and constraint.influence != 0:
            raise ValueError(f"Object constraint {constraint.name!r} ({constraint.type}) on {mesh.name!r} "
                             "must be applied/baked or disabled before character conversion")
    target_collection = _conversion_destination(options.target_collection)

    if options.delete_source_rig:
        _validate_source_deletion(armature, mesh)
    active = bpy.context.view_layer.objects.active
    selected = list(bpy.context.selected_objects)
    mode = active.mode if active else "OBJECT"
    created_collection = None
    new_mesh = new_armature = None
    map_text = old_text = None
    map_created = False
    owned_materials = []
    committed = False
    try:
        if bpy.context.object and bpy.context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        if target_collection is None:
            target_collection = bpy.data.collections.new(options.target_collection)
            bpy.context.scene.collection.children.link(target_collection)
            created_collection = target_collection

        # Build mapping and all weights before making any new Blender data.
        source_segments = (_canonical_points(mesh, armature)
                           if options.rig_mode == "AUTO" else _target_segments(options.template_armature))
        mapping = build_mapping(mesh, source_segments, options.keep_extra_bones)
        if options.rig_mode == "AUTO":
            new_armature = build_auto_armature(mesh, armature, mapping)
        else:
            new_armature = build_template_armature(options.template_armature)
            _add_template_extras(new_armature, _extra_segments(mesh, mapping, source_segments))
        _link_object(new_armature, target_collection)
        target_segments = _target_segments(new_armature)
        merged_weights = merge_weights(mesh, mapping, options.max_influences, target_segments)
        bone_names = [bone.name for bone in new_armature.data.bones]
        extra_names = [name for name in bone_names if name.startswith("mmd_")]
        _validate_targets(mesh, bone_names, merged_weights)
        print(f"[MMD_Rig] unbound bones: {[name for name in bone_names if name not in CANONICAL_SLOTS]}")
        print(f"[MMD_Rig] unused bones: {[name for name in bone_names if not merged_weights.get(name)]}")
        for name in extra_names:
            if name not in merged_weights:
                merged_weights[name] = []

        new_mesh = mesh.copy()
        new_mesh.data = mesh.data.copy()
        new_mesh.name = _unique_name(mesh.name + " Converted", bpy.data.objects)
        # Disabled source constraints must not later reactivate on the copy.
        for constraint in list(new_mesh.constraints):
            new_mesh.constraints.remove(constraint)
        target_collection.objects.link(new_mesh)
        if options.remove_shape_keys and new_mesh.data.shape_keys:
            private_key = new_mesh.data.shape_keys
            private_key_name = private_key.name
            try:
                _remove_shape_keys(new_mesh)
            finally:
                # Newer Blender clears the Key ID too; older versions leave it
                # orphaned. Clean only the surviving exact owned copy, including
                # helper failures before/after clear, while its Mesh is alive.
                if bpy.data.shape_keys.get(private_key_name) == private_key:
                    _validate_id_deletion(
                        private_key, new_mesh.data, new_mesh.data.user_of_id(private_key))
                    bpy.data.batch_remove(ids=(private_key,))
        for modifier in list(new_mesh.modifiers):
            if modifier.type == "ARMATURE":
                new_mesh.modifiers.remove(modifier)
        for group in list(new_mesh.vertex_groups):
            new_mesh.vertex_groups.remove(group)
        output_groups = list(bone_names)
        for name in output_groups:
            new_mesh.vertex_groups.new(name=name)
        for name, entries in merged_weights.items():
            group = new_mesh.vertex_groups.get(name)
            if group is None:
                raise ValueError(f"Weighted target {name!r} is absent from final rig")
            for vertex, weight in entries:
                group.add([vertex], weight, "REPLACE")
        modifier = new_mesh.modifiers.new("Armature", "ARMATURE")
        modifier.object = new_armature
        world = mesh.matrix_world.copy()
        new_mesh.parent = new_armature
        new_mesh.parent_type = "OBJECT"
        new_mesh.parent_bone = ""
        new_mesh.matrix_parent_inverse = new_armature.matrix_world.inverted()
        new_mesh.matrix_world = world
        new_mesh["mmd_converted"] = True
        new_mesh["export_path"] = _unique_export_path(mesh)
        reconcile_character_bindings(new_mesh, bone_names, owned_materials)

        pairs = [(name, mapping[name]) for name in mapping
                 if isinstance(mapping.get(name), str) and mapping[name].startswith("mmd_")]
        if pairs:
            map_text = bpy.data.texts.get("mmd_bone_name_map")
            map_created = map_text is None
            if map_text is None:
                map_text = bpy.data.texts.new("mmd_bone_name_map")
            old_text = map_text.as_string()
            _write_mapping_text(pairs)
        # Capture source-only anatomy inside rollback, before callbacks/deletion.
        # Missing neck/fingers remain explicit metadata, not conversion failures.
        from .omsi_human import capture_landmarks
        capture_landmarks(armature, new_armature,
                          template_armature=(options.template_armature
                                             if options.rig_mode == "TEMPLATE" else None))
        result = ConversionResult(
            mesh=new_mesh,
            armature=new_armature,
            vertices=len(new_mesh.data.vertices),
            groups=tuple(output_groups),
            bones=tuple(bone_names),
            merged_groups=tuple(name for name, target in mapping.items() if target is not None),
            ignored_groups=tuple(name for name, target in mapping.items() if target is None),
        )
        if on_complete is not None:
            on_complete(result)
        if options.delete_source_rig:
            _remove_source_rig(armature)
        committed = True
        return result
    except Exception:
        if map_text is not None:
            if map_created:
                bpy.data.texts.remove(map_text)
            else:
                map_text.clear()
                if old_text:
                    map_text.write(old_text)
        if new_mesh is not None and new_mesh.name in bpy.data.objects:
            data = new_mesh.data
            bpy.data.objects.remove(new_mesh, do_unlink=True)
            if data and data.users == 0:
                bpy.data.meshes.remove(data)
        if new_armature is not None and new_armature.name in bpy.data.objects:
            data = new_armature.data
            bpy.data.objects.remove(new_armature, do_unlink=True)
            if data and data.users == 0:
                bpy.data.armatures.remove(data)
        for material in owned_materials:
            if material.users == 0:
                bpy.data.materials.remove(material)
        if created_collection is not None and not created_collection.objects and not created_collection.children:
            bpy.data.collections.remove(created_collection)
        raise
    finally:
        if not committed or on_complete is None:
            _restore_context(active, selected, mode)
