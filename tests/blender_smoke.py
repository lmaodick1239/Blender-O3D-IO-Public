"""Entry point: blender --background --factory-startup --python tests/blender_smoke.py"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import bpy

import smoke_io
import smoke_paths
import smoke_materials
from smoke_support import load_addon

CHECKS = [
    smoke_materials.assert_material_compatibility,
    smoke_materials.assert_spline_material_compatibility,
    smoke_materials.assert_solid_material_compatibility,
    smoke_materials.assert_layered_material_compatibility,
    smoke_materials.assert_terrain_material_compatibility,
    smoke_materials.assert_bump_map,
    smoke_materials.assert_import_preserves_material_slots,
    smoke_materials.assert_import_preserves_validated_face_materials,
    smoke_io.assert_armature_helper,
    smoke_io.assert_invalid_topology_guard,
    smoke_paths.assert_leading_separator_mesh_path,
    smoke_io.assert_singular_transform_guard,
    smoke_io.assert_material_less_export,
    smoke_io.assert_emission_round_trip,
    smoke_io.assert_uv_seam_round_trip,
    smoke_io.assert_light_flare_flags_round_trip,
    smoke_io.assert_light_flare_optional_texture,
    smoke_paths.assert_regional_codepage_paths,
    smoke_paths.assert_case_insensitive_import_paths,
    smoke_paths.assert_missing_meshes_are_reported,
    smoke_paths.assert_import_failure_tally,
    smoke_io.assert_bulk_import,
    smoke_io.assert_imported_bone_armature,
    smoke_io.assert_weight_seam_round_trip,
    smoke_io.assert_posed_rig_exports_rest_space,
    smoke_io.assert_modifier_restoration,
    smoke_io.assert_posed_rig_with_export_error,
    smoke_io.assert_narrow_index_width,
    smoke_io.assert_wide_index_width,
    smoke_io.assert_wide_mesh_bone_indices_are_u16,
    smoke_io.assert_weighted_index_above_u16_rejected,
    smoke_io.assert_pre_v3_wide_index_rejection,
    smoke_io.assert_v3_header_layout,
    smoke_io.assert_bone_validation,
    smoke_io.assert_pose_deformation,
    smoke_io.assert_weight_export_reimport,
    smoke_io.assert_malformed_influence_recovery,
    smoke_io.assert_unbound_setbone_warning,
    smoke_io.assert_round_trip,
]


def run() -> None:
    addon = load_addon()
    metadata = addon.bl_info.copy()
    del addon.bl_info
    addon.register()
    assert metadata["blender"] == (4, 0, 0)
    assert addon.ADDON_VERSION == (1, 3, 4)
    assert hasattr(bpy.ops.import_scene, "omsi_model_cfg")
    assert hasattr(bpy.ops.export_scene, "omsi_model_cfg")
    assert hasattr(bpy.ops.import_scene, "omsi_tile")
    for check in CHECKS:
        check(addon)
    addon.unregister()
    print("BLENDER_O3D_IO_SMOKE_OK", bpy.app.version_string)


run()
