"""Low-level MMD material edits; callers own material copying and undo."""
from . import blender_compat


def mmd_nodes(material) -> list:
    """Find MMD shader groups by sockets, independent of user node names."""
    tree = material.node_tree
    if tree is None:
        return []
    return [
        node for node in tree.nodes
        if node.bl_idname == "ShaderNodeGroup" and "Toon Tex Fac" in node.inputs
    ]


def reset_toon(materials, reset_sphere=False) -> int:
    """Disable toon (and optionally sphere) contributions; count changed materials."""
    changed_count = 0
    for material in materials:
        changed = False
        for shader in mmd_nodes(material):
            for prefix in (("Toon Tex", "Sphere Tex") if reset_sphere else ("Toon Tex",)):
                for socket in shader.inputs:
                    if socket.name.startswith(prefix):
                        for link in list(socket.links):
                            # Remember detached branches for a later flatten, even after renames.
                            link.from_node["o3d_mmd_helper"] = True
                            material.node_tree.links.remove(link)
                            changed = True
                factor = shader.inputs.get(prefix + " Fac")
                if factor is not None and factor.default_value != 0:
                    factor.default_value = 0
                    changed = True
        if changed:
            changed_count += 1
            print(f"[MMD_Materials] {material.name}: reset toon" + (" and sphere" if reset_sphere else ""))
    return changed_count


def _upstream(nodes) -> set:
    """Collect input dependencies, including shared UV/mapping nodes."""
    found = set()
    pending = list(nodes)
    while pending:
        node = pending.pop()
        if node in found:
            continue
        found.add(node)
        pending.extend(link.from_node for socket in node.inputs for link in socket.links)
    return found


def flatten_material(material) -> bool:
    """Replace MMD shaders with an exporter-readable Principled material."""
    shaders = mmd_nodes(material)
    if not shaders:
        return False
    tree = material.node_tree
    outputs = [node for node in tree.nodes if node.bl_idname == "ShaderNodeOutputMaterial"]
    output = next((node for node in outputs if node.is_active_output), None)
    # Prefer the MMD shader used by the active output, if there are several.
    active_nodes = _upstream([output]) if output is not None else set()
    shader = next((node for node in shaders if node in active_nodes), shaders[0])
    base_socket = shader.inputs.get("Base Tex")
    base = None
    if base_socket is not None and base_socket.is_linked:
        candidate = base_socket.links[0].from_node
        if candidate.bl_idname == "ShaderNodeTexImage" and candidate.image is not None:
            base = candidate
    diffuse_socket = shader.inputs.get("Diffuse Color")
    alpha_socket = shader.inputs.get("Alpha")
    mmd = getattr(material, "mmd_material", None)
    diffuse = tuple(getattr(mmd, "diffuse_color",
                            diffuse_socket.default_value if diffuse_socket is not None else (1, 1, 1)))[:3]
    alpha = getattr(mmd, "alpha", alpha_socket.default_value if alpha_socket is not None else 1)

    detached = [node for node in tree.nodes if node.get("o3d_mmd_helper")]
    candidates = _upstream([*shaders, *detached])
    # Keep base mapping and any MMD inputs also used by unrelated parts of the graph.
    keep = _upstream([base]) if base is not None else set()
    shared = [node for node in candidates if node not in shaders and any(
        link.to_node not in candidates for socket in node.outputs for link in socket.links
    )]
    keep.update(_upstream(shared))

    # The compatibility wrapper selects the first linked Principled/output pair,
    # even when that output is inactive. Isolate it while creating conversion nodes.
    principled_links = []
    for node in tree.nodes:
        if node.bl_idname != "ShaderNodeBsdfPrincipled":
            continue
        principled_links.extend(
            (link.from_socket, link.to_socket)
            for link in list(node.outputs["BSDF"].links)
        )
    for from_socket, to_socket in principled_links:
        tree.links.remove(next(link for link in from_socket.links if link.to_socket == to_socket))
    try:
        wrapper = blender_compat.principled_wrapper(material, is_readonly=False)
    finally:
        for from_socket, to_socket in principled_links:
            tree.links.new(from_socket, to_socket)
    principled = wrapper.node_principled_bsdf
    if output is None:
        output = wrapper.node_out
    elif wrapper.node_out not in outputs:
        # The wrapper creates an output when no Principled/output pair exists.
        tree.nodes.remove(wrapper.node_out)
    tree.links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    wrapper.base_color = diffuse
    wrapper.alpha = alpha
    for name in ("Base Color", "Alpha"):
        for link in list(principled.inputs[name].links):
            tree.links.remove(link)
    if base is not None:
        tree.links.new(base.outputs["Color"], principled.inputs["Base Color"])
        tree.links.new(base.outputs["Alpha"], principled.inputs["Alpha"])
    material.diffuse_color = (*diffuse, alpha)
    blender_compat.set_material_alpha_mode(material, "BLEND" if alpha < 1 else "OPAQUE")
    for node in candidates - keep:
        tree.nodes.remove(node)
    print(f"[MMD_Materials] {material.name}: flattened")
    return True
