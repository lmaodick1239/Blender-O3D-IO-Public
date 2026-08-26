import importlib
import sys
import tempfile
from pathlib import Path
from types import ModuleType

import bpy
from bpy_extras import node_shader_utils
from mathutils import Matrix


def load_addon() -> ModuleType:
    repository = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repository.parent))
    return importlib.import_module(repository.name)


def create_source_object(addon: ModuleType) -> bpy.types.Object:
    bpy.ops.object.select_all(action="DESELECT")
    mesh = bpy.data.meshes.new("O3D Smoke Mesh")
    mesh.from_pydata(
        [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)],
        [],
        [(0, 1, 2)],
    )
    mesh.uv_layers.new(name="UV Map")
    for loop, uv in zip(mesh.loops, ((0.0, 0.0), (1.0, 0.0), (0.0, 1.0))):
        mesh.uv_layers.active.data[loop.index].uv = uv
    mesh.polygons[0].use_smooth = True
    mesh.normals_split_custom_set_from_vertices(
        [(0.0, 0.0, 1.0), (0.0, 0.0, 1.0), (0.0, 0.0, 1.0)]
    )
    material = bpy.data.materials.new("O3D Smoke Material")
    material.use_nodes = True
    wrapper = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=False)
    image = bpy.data.images.new("smoke.png", width=1, height=1)
    image.filepath = "smoke.png"
    wrapper.base_color_texture.image = image
    wrapper.alpha_texture.image = image
    wrapper.specular = 0.6
    wrapper.specular_tint = (0.5, 1.0, 0.25)
    addon.o3d_io.blender_compat.set_material_alpha_mode(material, "CLIP")
    mesh.materials.append(material)
    source = bpy.data.objects.new("O3D Smoke Object", mesh)
    bpy.context.scene.collection.objects.link(source)
    source.select_set(True)
    bpy.context.view_layer.objects.active = source
    return source


def assert_material_compatibility(addon: ModuleType) -> None:
    material = bpy.data.materials.new("O3D Alpha Material")
    addon.o3d_io.io_o3d_import.blender_compat.set_material_alpha_mode(
        material, "HASHED"
    )
    assert material.surface_render_method == "DITHERED"


def assert_spline_material_compatibility(addon: ModuleType) -> None:
    mesh = bpy.data.meshes.new("O3D Spline Material Mesh")
    addon.o3d_io.io_omsi_spline.generate_materials(
        mesh,
        "missing.sli",
        {0: {"diffuse": "missing.png", "alpha": 1}},
    )
    assert len(mesh.materials) == 1
    assert (
        addon.o3d_io.blender_compat.get_material_alpha_mode(mesh.materials[0])
        == "HASHED"
    )
    solid = addon.o3d_io.blender_compat.create_solid_material(
        (0.8, 0.8, 0.8, 1.0)
    )
    assert solid.surface_render_method == "DITHERED"


def assert_round_trip(addon: ModuleType) -> None:
    source = create_source_object(addon)
    with tempfile.TemporaryDirectory(prefix="blender-o3d-io-") as temporary:
        filepath = Path(temporary) / "round-trip.o3d"
        addon.o3d_io.io_o3d_export.do_export(
            str(filepath), bpy.context, Matrix.Identity(4), True, 7, True
        )
        assert filepath.is_file()
        cfg_path = Path(temporary) / "round-trip.cfg"
        addon.o3d_io.io_o3d_export.do_export(
            str(cfg_path), bpy.context, Matrix.Identity(4), True, 7, False
        )
        assert cfg_path.is_file()
        assert "[matl_alpha]\n1" in cfg_path.read_text(encoding="utf-8")
        assert (Path(temporary) / "O3D Smoke Object.o3d").is_file()
        bpy.data.objects.remove(source, do_unlink=True)
        imported = addon.o3d_io.io_o3d_import.do_import(
            str(filepath), bpy.context, False, "", False
        )
        assert len(imported) == 1
        assert len(imported[0].data.vertices) == 3
        assert len(imported[0].data.polygons) == 1
        assert imported[0].data.has_custom_normals
        assert all(normal.vector.z > 0.99 for normal in imported[0].data.corner_normals)
        assert len(imported[0].data.materials) == 1
        imported_wrapper = node_shader_utils.PrincipledBSDFWrapper(
            imported[0].data.materials[0], is_readonly=True
        )
        assert abs(imported_wrapper.specular - 0.6) < 0.001
        assert all(
            abs(actual - expected) < 0.001
            for actual, expected in zip(
                imported_wrapper.specular_tint,
                (0.5, 1.0, 0.25),
            )
        )
        bpy.data.objects.remove(imported[0], do_unlink=True)
        imported_cfg = addon.o3d_io.io_o3d_import.do_import(
            str(cfg_path), bpy.context, False, "", False
        )
        assert len(imported_cfg) == 1
        assert len(imported_cfg[0].data.vertices) == 3


def run() -> None:
    addon = load_addon()
    metadata = addon.bl_info.copy()
    del addon.bl_info
    addon.register()
    assert metadata["blender"] == (4, 0, 0)
    assert addon.ADDON_VERSION == (1, 3, 1)
    assert hasattr(bpy.ops.import_scene, "omsi_model_cfg")
    assert hasattr(bpy.ops.export_scene, "omsi_model_cfg")
    assert hasattr(bpy.ops.import_scene, "omsi_tile")
    assert_material_compatibility(addon)
    assert_spline_material_compatibility(addon)
    assert_round_trip(addon)
    addon.unregister()
    print("BLENDER_O3D_IO_SMOKE_OK", bpy.app.version_string)


run()
