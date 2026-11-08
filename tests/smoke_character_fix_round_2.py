"""Real nested physics group references must refuse before conversion staging."""
import bpy

from smoke_character import _rig, _mmd_character, _remove_objects
from smoke_character_fix_round_1 import _source_snapshot, _edit_context, _object_mode


# Literal native fields: a missed nested owner must fail independently of the
# production RNA query. Each field is populated alone, so no sibling masks it.
_CLOTH_FIELDS = (
    "vertex_group_mass", "vertex_group_shrink", "vertex_group_structural_stiffness",
    "vertex_group_shear_stiffness", "vertex_group_bending", "vertex_group_intern",
    "vertex_group_pressure",
)
_COLLISION_FIELDS = ("vertex_group_self_collisions", "vertex_group_object_collisions")
_CASES = (
    ("CLOTH", "settings", _CLOTH_FIELDS),
    ("CLOTH", "collision_settings", _COLLISION_FIELDS),
    ("SOFT_BODY", "settings", ("vertex_group_mass", "vertex_group_goal", "vertex_group_spring")),
    ("PARTICLE_SYSTEM", "particle_system", (
        "vertex_group_density", "vertex_group_velocity", "vertex_group_length",
        "vertex_group_clump", "vertex_group_kink", "vertex_group_roughness_1",
        "vertex_group_roughness_2", "vertex_group_roughness_end", "vertex_group_size",
        "vertex_group_tangent", "vertex_group_rotation", "vertex_group_field", "vertex_group_twist",
    )),
    ("FLUID", "flow_settings", ("density_vertex_group",)),
    ("HAIR_DYNAMICS", "settings", _CLOTH_FIELDS),
    ("HAIR_DYNAMICS", "collision_settings", _COLLISION_FIELDS),
)


def _physics_modifier(mesh, kind, owner_name):
    if kind in {"PARTICLE_SYSTEM", "HAIR_DYNAMICS"}:
        bpy.context.view_layer.objects.active = mesh
        mesh.select_set(True)
        bpy.ops.object.particle_system_add()
        modifier = mesh.modifiers[-1]
        modifier.particle_system.settings.count = 1
        if kind == "HAIR_DYNAMICS":
            particle = modifier.particle_system
            particle.settings.type = "HAIR"
            particle.use_hair_dynamics = True
            owners = (particle.cloth.settings, particle.cloth.collision_settings)
            owner = getattr(particle.cloth, owner_name)
        else:
            owner = modifier.particle_system
            owners = (owner,)
    else:
        modifier = mesh.modifiers.new("Nested " + kind + " membership", kind)
        if kind == "FLUID":
            modifier.fluid_type = "FLOW"
            owners = (modifier.flow_settings,)
        elif kind == "CLOTH":
            owners = (modifier.settings, modifier.collision_settings)
        else:
            owners = (modifier.settings,)
        owner = getattr(modifier, owner_name)
    return modifier, owner, owners


def _nested_snapshot(mesh, source, owners):
    return (
        _source_snapshot(mesh, source),
        tuple((owner.as_pointer(), tuple((prop.identifier, getattr(owner, prop.identifier))
              for prop in owner.bl_rna.properties if prop.type == "STRING")) for owner in owners),
        tuple(item.as_pointer() for item in bpy.data.particles),
    )


def assert_nested_group_modifier_refusal(addon):
    """Missing nested checks would accept real cloth pins and lose their binding."""
    rig = _rig(addon)
    checked = 0
    for kind, owner_name, fields in _CASES:
        mesh, source = _mmd_character()
        modifier, owner, owners = _physics_modifier(mesh, kind, owner_name)
        result = None
        try:
            for field in fields:
                setattr(owner, field, "上半身")
                assert getattr(owner, field) == "上半身", (kind, field, "fixture not populated")
                for viewport, render in ((True, True), (True, False), (False, True)):
                    modifier.show_viewport, modifier.show_render = viewport, render
                    _edit_context(mesh)
                    before = _nested_snapshot(mesh, source, owners)
                    try:
                        result = rig.convert(mesh, source, rig.ConversionOptions(delete_source_rig=True))
                    except ValueError as error:
                        message = str(error)
                        assert modifier.name in message and "apply/bake" in message, message
                    else:
                        raise AssertionError(f"invalid conversion accepted: {kind}.{owner_name}.{field}")
                    assert _nested_snapshot(mesh, source, owners) == before, (kind, owner_name, field)
                    assert getattr(owner, field) == "上半身"
                    assert (modifier.show_viewport, modifier.show_render) == (viewport, render)
                    _object_mode()
                    checked += 1
                setattr(owner, field, "")
        finally:
            _object_mode()
            _remove_objects(mesh, source, result.mesh if result else None, result.armature if result else None)

    # Both-channel-disabled dependencies keep the established dormant policy.
    mesh, source = _mmd_character()
    cloth, owner, owners = _physics_modifier(mesh, "CLOTH", "settings")
    owner.vertex_group_mass = "上半身"
    cloth.show_viewport = cloth.show_render = False
    before = _nested_snapshot(mesh, source, owners)
    result = None
    try:
        result = rig.convert(mesh, source, rig.ConversionOptions())
        retained = result.mesh.modifiers[cloth.name]
        assert not retained.show_viewport and not retained.show_render
        assert owner.vertex_group_mass == "上半身"
        # Conversion legitimately adds IDs, but the original source stays intact.
        after = _nested_snapshot(mesh, source, owners)
        assert after[0][1:7] == before[0][1:7]
        assert after[1:] == before[1:]
    finally:
        _remove_objects(mesh, source, result.mesh if result else None, result.armature if result else None)
    print("NESTED_GROUP_MODIFIER_REFUSALS", checked)
