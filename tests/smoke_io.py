"""Import and export round-trip checks."""
import os
import shutil
import tempfile
from pathlib import Path
from types import ModuleType

import bpy
from bpy_extras import node_shader_utils
from mathutils import Matrix

from smoke_support import create_source_object


def assert_invalid_topology_guard(addon: ModuleType) -> None:
    mesh = bpy.data.meshes.new("O3D Invalid Topology Mesh")
    mesh.from_pydata([(0.0, 0.0, 0.0)], [], [(0, 1, 2)])
    addon.o3d_io.blender_compat.prepare_import_mesh(
        mesh,
        [(0.0, 0.0, 1.0)],
        True,
    )
    assert len(mesh.vertices) == 1
    assert len(mesh.polygons) == 0


def assert_leading_separator_mesh_path(addon: ModuleType) -> None:
    """Issue #72: a [mesh] path written with a leading separator resolved to the drive root."""
    join = addon.o3d_io.omsi_paths.join_omsi_path
    base = os.path.join("models", "bus")
    expected = os.path.join(base, "seat", "LChair3.o3d")
    assert join(base, r"\seat\LChair3.o3d") == expected
    assert join(base, r"seat\LChair3.o3d") == expected
    assert join(base, "/seat/LChair3.o3d") == expected

    with tempfile.TemporaryDirectory(prefix="blender-o3d-io-cfg-") as temporary:
        directory = Path(temporary)
        (directory / "seat").mkdir()
        mesh_file = directory / "seat" / "LChair3.o3d"
        mesh_file.write_bytes(b"")
        cfg_path = directory / "model.cfg"
        cfg_path.write_text("[mesh]" + "\n" + r"\seat\LChair3.o3d" + "\n\n", encoding="cp1252")
        cfg_data, _ = addon.o3d_io.o3d_cfg_parser.read_cfg(str(cfg_path), "")
        paths = [
            mesh["path"]
            for lod in cfg_data.values()
            for mesh in lod["meshes"].values()
        ]
        assert paths == [str(mesh_file)], paths


def assert_singular_transform_guard(addon: ModuleType) -> None:
    """Issue #93: a degenerate o3d transform aborted the import with a ValueError."""
    source = create_source_object(addon)
    source.scale = (1.0, 1.0, 0.0)
    with tempfile.TemporaryDirectory(prefix="blender-o3d-io-singular-") as temporary:
        filepath = Path(temporary) / "singular.o3d"
        addon.o3d_io.io_o3d_export.do_export(
            str(filepath), bpy.context, Matrix.Identity(4), True, 7, True
        )
        bpy.data.objects.remove(source, do_unlink=True)
        imported = addon.o3d_io.io_o3d_import.do_import(
            str(filepath), bpy.context, False, "", False
        )
        assert len(imported) == 1
        bpy.data.objects.remove(imported[0], do_unlink=True)


def assert_material_less_export(addon: ModuleType) -> None:
    """Issue #80: objects without materials produced an o3d file with no material at all."""
    bpy.ops.object.select_all(action="DESELECT")
    mesh = bpy.data.meshes.new("O3D Bare Mesh")
    mesh.from_pydata(
        [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)], [], [(0, 1, 2)]
    )
    source = bpy.data.objects.new("O3D Bare Object", mesh)
    bpy.context.scene.collection.objects.link(source)
    source.select_set(True)
    bpy.context.view_layer.objects.active = source
    with tempfile.TemporaryDirectory(prefix="blender-o3d-io-bare-") as temporary:
        filepath = Path(temporary) / "bare.o3d"
        addon.o3d_io.io_o3d_export.do_export(
            str(filepath), bpy.context, Matrix.Identity(4), True, 7, True
        )
        bpy.data.objects.remove(source, do_unlink=True)
        imported = addon.o3d_io.io_o3d_import.do_import(
            str(filepath), bpy.context, False, "", False
        )
        assert len(imported) == 1
        assert len(imported[0].data.materials) == 1
        bpy.data.objects.remove(imported[0], do_unlink=True)


def assert_emission_round_trip(addon: ModuleType) -> None:
    """Issue #104: o3d emission was parsed on import but never reached the material."""
    source = create_source_object(addon)
    wrapper = node_shader_utils.PrincipledBSDFWrapper(
        source.data.materials[0], is_readonly=False
    )
    wrapper.emission_color = (0.25, 0.5, 0.75)
    with tempfile.TemporaryDirectory(prefix="blender-o3d-io-emission-") as temporary:
        filepath = Path(temporary) / "emission.o3d"
        addon.o3d_io.io_o3d_export.do_export(
            str(filepath), bpy.context, Matrix.Identity(4), True, 7, True
        )
        bpy.data.objects.remove(source, do_unlink=True)
        imported = addon.o3d_io.io_o3d_import.do_import(
            str(filepath), bpy.context, False, "", False
        )
        imported_wrapper = node_shader_utils.PrincipledBSDFWrapper(
            imported[0].data.materials[0], is_readonly=True
        )
        assert all(
            abs(actual - expected) < 0.001
            for actual, expected in zip(
                imported_wrapper.emission_color, (0.25, 0.5, 0.75)
            )
        ), tuple(imported_wrapper.emission_color)
        assert imported_wrapper.emission_strength > 0
        bpy.data.objects.remove(imported[0], do_unlink=True)


def assert_uv_seam_round_trip(addon: ModuleType) -> None:
    """Issue #59: exporting a mesh with UV seams must not weld the split UVs back together."""
    bpy.ops.object.select_all(action="DESELECT")
    mesh = bpy.data.meshes.new("O3D Seam Mesh")
    mesh.from_pydata(
        [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0)],
        [],
        [(0, 1, 2), (0, 2, 3)],
    )
    uv_layer = mesh.uv_layers.new(name="UV Map")
    source_uvs = [
        (0.0, 0.0), (0.5, 0.0), (0.5, 0.5),
        (0.9, 0.9), (0.6, 0.2), (0.1, 0.7),
    ]
    for loop_index, value in enumerate(source_uvs):
        uv_layer.data[loop_index].uv = value
    mesh.update()
    source = bpy.data.objects.new("O3D Seam Object", mesh)
    bpy.context.scene.collection.objects.link(source)
    source.select_set(True)
    bpy.context.view_layer.objects.active = source

    with tempfile.TemporaryDirectory(prefix="blender-o3d-io-seam-") as temporary:
        filepath = Path(temporary) / "seam.o3d"
        addon.o3d_io.io_o3d_export.do_export(
            str(filepath), bpy.context, Matrix.Identity(4), True, 7, True
        )
        bpy.data.objects.remove(source, do_unlink=True)
        imported = addon.o3d_io.io_o3d_import.do_import(
            str(filepath), bpy.context, False, "", False
        )
        imported_mesh = imported[0].data
        # The seam must survive as duplicated vertices rather than being welded back to four
        assert len(imported_mesh.vertices) == 6, len(imported_mesh.vertices)
        rounded = sorted(
            tuple(round(channel, 4) for channel in loop.uv)
            for loop in imported_mesh.uv_layers[0].data
        )
        assert rounded == sorted(source_uvs), rounded
        bpy.data.objects.remove(imported[0], do_unlink=True)


def assert_bulk_import(addon: ModuleType) -> None:
    source = create_source_object(addon)
    with tempfile.TemporaryDirectory(prefix="blender-o3d-io-bulk-") as temporary:
        directory = Path(temporary)
        first = directory / "first.o3d"
        second = directory / "second.o3d"
        addon.o3d_io.io_o3d_export.do_export(
            str(first), bpy.context, Matrix.Identity(4), True, 7, True
        )
        shutil.copyfile(first, second)
        bpy.data.objects.remove(source, do_unlink=True)
        existing = set(bpy.data.objects)
        result = bpy.ops.import_scene.omsi_model_cfg(
            filepath=str(first),
            directory=str(directory),
            files=[{"name": first.name}, {"name": second.name}],
            import_x=False,
        )
        imported = set(bpy.data.objects) - existing
        assert result == {"FINISHED"}
        assert len(imported) == 2
        for imported_object in imported:
            bpy.data.objects.remove(imported_object, do_unlink=True)


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
        cfg_text = cfg_path.read_text(encoding="utf-8")
        assert "[matl_alpha]\n1" in cfg_text
        assert "[matl_bumpmap]\nbump.png\n0.5" in cfg_text
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
