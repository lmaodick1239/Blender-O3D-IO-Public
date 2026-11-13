"""Public synthetic suite; opt in to private scenes with -- --with-private-fixtures."""
import argparse
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import bpy

import smoke_io
import smoke_import_normals
import smoke_paths
import smoke_materials
import smoke_character
import smoke_character_panel
import smoke_character_review
import smoke_character_repair
import smoke_character_fix_round_1
import smoke_character_fix_round_2
import smoke_character_final_fix
import smoke_lod
import smoke_human
import smoke_human_textures
import smoke_export_fidelity
import smoke_arm_normalization
import smoke_arm_rest_angle
import smoke_arm_preview
from smoke_support import load_addon

CHECKS = [
    # Factory-byte arm baselines precede legacy checks that seed scene CFG metadata.
    *smoke_arm_normalization.CHECKS,
    *smoke_arm_rest_angle.CHECKS,
    *smoke_arm_preview.CHECKS,
    smoke_character.assert_toon_reset,
    smoke_character.assert_material_flatten,
    smoke_character.assert_mmd_group_uv_export,
    smoke_character.assert_bone_name_mapping,
    smoke_character.assert_weight_merge,
    smoke_character.assert_auto_armature_build,
    smoke_character.assert_template_conversion,
    smoke_character.assert_extra_bones,
    smoke_character.assert_conversion_export_round_trip,
    smoke_character.assert_conversion_rollback_and_source_delete,
    smoke_character.assert_conversion_runtime_validation,
    smoke_character_repair.assert_conversion_input_guards,
    smoke_character_repair.assert_source_detection_evidence,
    smoke_character_repair.assert_canonical_joint_geometry,
    smoke_character_repair.assert_sparse_auto_mapping,
    smoke_character_repair.assert_template_extras_and_rest_clone,
    smoke_character_repair.assert_conversion_parent_material_paths,
    smoke_character_repair.assert_serialized_runtime_limits,
    smoke_character_repair.assert_owned_rollback_and_deletion,
    smoke_character_repair.assert_basis_and_evaluated_blend_preservation,
    smoke_character_repair.assert_missing_weighted_target_refuses,
    smoke_character_repair.assert_conversion_empty_context_restored,
    smoke_character_fix_round_1.assert_deletion_external_id_users,
    smoke_character_fix_round_1.assert_textured_object_material_cfg,
    smoke_character_fix_round_1.assert_pre_v3_section_count_preservation,
    smoke_character_fix_round_1.assert_group_modifier_refusal,
    smoke_character_fix_round_1.assert_resolved_export_path_containment,
    smoke_character_fix_round_1.assert_nonfinite_rig_preflight,
    smoke_character_fix_round_2.assert_nested_group_modifier_refusal,
    *smoke_lod.CHECKS,
    *smoke_character_final_fix.CHECKS,
    *smoke_character_panel.CHECKS,
    *smoke_character_review.CHECKS,
    smoke_io.assert_skin_distinct_coincident_export,
    smoke_io.assert_evaluated_topology_skin_export,
    smoke_io.assert_invalid_export_preserves_file,
    smoke_io.assert_export_context_restoration,
    smoke_paths.assert_safe_export_mesh_paths,
    smoke_materials.assert_material_compatibility,
    smoke_materials.assert_spline_material_compatibility,
    smoke_materials.assert_solid_material_compatibility,
    smoke_materials.assert_layered_material_compatibility,
    smoke_materials.assert_layered_material_export_rejected,
    smoke_materials.assert_terrain_material_compatibility,
    smoke_materials.assert_bump_map,
    smoke_materials.assert_import_preserves_material_slots,
    smoke_materials.assert_import_preserves_validated_face_materials,
    smoke_io.assert_armature_helper,
    smoke_io.assert_invalid_topology_guard,
    *smoke_import_normals.CHECKS,
    smoke_paths.assert_leading_separator_mesh_path,
    smoke_io.assert_singular_transform_guard,
    smoke_io.assert_generic_smoothskin_cfg,
    smoke_io.assert_singular_transform_geometry,
    smoke_io.assert_material_less_export,
    smoke_io.assert_embedded_material_round_trip,
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
    smoke_io.assert_long_import_name_mapping,
    smoke_io.assert_weight_seam_round_trip,
    smoke_io.assert_posed_rig_exports_rest_space,
    smoke_io.assert_modifier_restoration,
    smoke_io.assert_posed_rig_with_export_error,
    smoke_io.assert_scaled_origin_frame,
    smoke_io.assert_generic_skinned_runtime_limits,
    smoke_io.assert_armature_helper_group_filter,
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--with-private-fixtures', action='store_true')
    parser.add_argument('--fidelity-output-dir', type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    human_checks = smoke_human.select_checks(with_private=args.with_private_fixtures)
    addon = load_addon()
    metadata = addon.bl_info.copy()
    del addon.bl_info
    addon.register()
    try:
        assert metadata["blender"] == (4, 2, 0)
        assert addon.ADDON_VERSION == (1, 3, 4)
        assert hasattr(bpy.ops.import_scene, "omsi_model_cfg")
        assert hasattr(bpy.ops.export_scene, "omsi_model_cfg")
        assert hasattr(bpy.ops.import_scene, "omsi_tile")
        for check in CHECKS:
            check(addon)
            print('ROOT_CHECK_OK', check.__name__)
        # The root owns registration; run fidelity before human save/reload checks.
        before = smoke_human.source_snapshot()
        previous_output = smoke_export_fidelity.OUTPUT_DIR
        caller_scene = bpy.context.window.scene
        fidelity_scene = bpy.data.scenes.new('O3D Fidelity Smoke')
        try:
            # Cycles can materialize scene settings even when restoring defaults.
            # Keep that fixture state out of the caller's scene on every series.
            bpy.context.window.scene = fidelity_scene
            with tempfile.TemporaryDirectory(prefix='o3d-integrated-fidelity-') as temporary:
                smoke_export_fidelity.OUTPUT_DIR = args.fidelity_output_dir or Path(temporary)
                smoke_export_fidelity.run_checks(addon)
        finally:
            bpy.context.window.scene = caller_scene
            bpy.data.scenes.remove(fidelity_scene)
            smoke_export_fidelity.OUTPUT_DIR = previous_output
        assert smoke_human.source_snapshot() == before, 'fidelity changed caller scene/source/context'
        print('FIDELITY_CALLER_RESTORATION_OK')
        # Human checks use (addon, human), unlike the historical addon-only list.
        import importlib
        human = importlib.import_module(addon.__name__ + '.o3d_io.omsi_human')
        for check in human_checks:
            check(addon, human)
            print('HUMAN_CHECK_OK', check.__name__)
    finally:
        addon.unregister()
        smoke_character_panel.assert_character_panel_unregistered(addon)
        smoke_human.assert_human_unregistered(addon)
    # This standalone-compatible runner owns its registration cycle and fixtures.
    smoke_human_textures.run()
    smoke_character_panel.assert_character_panel_unregistered(addon)
    smoke_human.assert_human_unregistered(addon)
    print('BLENDER_O3D_IO_PUBLIC_SYNTHETIC_SMOKE_OK', bpy.app.version_string,
          'root_checks', len(CHECKS), 'human_synthetic_checks', len(smoke_human.CHECKS),
          'optional_private_checks', len(smoke_human.PRIVATE_CHECKS) if args.with_private_fixtures else 0)


run()
