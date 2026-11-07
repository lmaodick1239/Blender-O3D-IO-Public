"""Resource path resolution and missing-file reporting checks."""
import io
import os
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from types import ModuleType

import bpy


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


def assert_regional_codepage_paths(addon: ModuleType) -> None:
    """A Turkish mesh name read as cp1252 does not exist on disk, so the other codepages are tried."""
    dotless_i = chr(0x131)
    name = "kap" + dotless_i + "buton.o3d"

    with tempfile.TemporaryDirectory(prefix="blender-o3d-io-codepage-") as temporary:
        directory = Path(temporary)
        model = directory / "PROCITY"
        model.mkdir()
        (model / name).write_bytes(b"")

        as_written = ("PROCITY/" + name).encode("cp1254").decode("cp1252")
        assert as_written != "PROCITY/" + name

        resolved = addon.o3d_io.omsi_paths.resolve_omsi_path(str(directory), as_written)
        assert resolved == str(model / name), resolved

        cfg_path = directory / "model.cfg"
        cfg_path.write_bytes(("[mesh]\n" + "PROCITY/" + name + "\n\n").encode("cp1254"))
        cfg_data, _ = addon.o3d_io.o3d_cfg_parser.read_cfg(str(cfg_path), "")
        paths = [
            mesh["path"]
            for lod in cfg_data.values()
            for mesh in lod["meshes"].values()
        ]
        assert paths == [str(model / name)], paths


def assert_case_insensitive_import_paths(addon: ModuleType) -> None:
    """Resolve real on-disk casing for imported assets, including directory components."""
    paths = addon.o3d_io.omsi_paths
    textures = addon.o3d_io.blender_texture_io
    importer = addon.o3d_io.io_o3d_import
    parser = addon.o3d_io.o3d_cfg_parser
    with tempfile.TemporaryDirectory(prefix="blender-o3d-io-case-") as temporary:
        directory = Path(temporary)
        model = directory / "Model"
        model.mkdir()
        mesh = model / "Seat.O3D"
        mesh.write_bytes(b"")
        assert paths.resolve_omsi_path(str(directory), r"model\SEAT.o3d") == str(mesh)
        assert paths.resolve_omsi_path(str(directory / "MODEL"), "seat.o3d") == str(mesh)
        missing = str(model / "missing.o3d")
        assert paths.resolve_omsi_path(str(model), "missing.o3d") == missing
        assert paths.resolve_omsi_path(str(model), "Seat.O3D") == str(mesh)
        other_case = model / "seat.o3d"
        if not other_case.exists():
            other_case.write_bytes(b"")
            assert paths.resolve_omsi_path(str(model), "seat.o3d") == str(other_case)
            other_case.unlink()
        regional = model / "KAPı.O3D"
        regional.write_bytes(b"")
        encoded = r"model\KAPı.o3d".encode("cp1254").decode("cp1252")
        assert paths.resolve_omsi_path(str(directory), encoded) == str(regional)
        cfg = directory / "Vehicle.SCO"
        cfg.write_text("[mesh]\nseat.o3d\n\n", encoding="cp1252")
        cfg_data, _ = parser.read_cfg(str(directory / "vehicle.sco"), "")
        mesh_paths = [entry["path"] for lod in cfg_data.values() for entry in lod["meshes"].values()]
        assert mesh_paths == [str(mesh)], mesh_paths
        assert importer.resolve_import_filepaths(str(cfg), str(directory), ["vehicle.sco"]) == [str(cfg)]
        assert importer.resolve_import_filepaths(str(cfg), str(directory), ["../outside.sco"]) == []
        assert importer.resolve_import_filepaths(str(mesh), str(model), [r"..\Vehicle.SCO"]) == []
        texture_dir = directory / "Texture" / "Details"
        texture_dir.mkdir(parents=True)
        texture = texture_dir / "Seat.BMP"
        texture.write_bytes(b"")
        declared = r"details\SEAT.bmp"
        assert textures.find_image_path(str(cfg), declared) == str(texture)
        assert textures.find_image_path(str(model / "test.o3d"), declared) == str(texture)
        assert textures.find_image_path(str(directory / "vehicle.sco"), declared) == str(texture)
        assert textures.find_image_path(str(cfg), str(directory / "texture" / "details" / "seat.bmp"), True) == str(texture)
        sidecar = texture_dir / "Seat.BMP.CFG"
        sidecar.write_text("[terrainmapping]\n", encoding="utf-8")
        assert textures.find_image_path(str(cfg), declared, find_cfg=True) == str(sidecar)
        assert "[terrainmapping]" in parser.read_generic_cfg_file(str(sidecar).swapcase())
        dds = texture_dir / "Seat.DDS"
        dds.write_bytes(b"")
        assert textures.find_image_path(str(cfg), declared) == str(dds)
        assert textures.find_image_path(str(cfg), r"details\missing.bmp") is None
        shared = directory / "Shared"
        shared.mkdir()
        shared_texture = shared / "Panel.PNG"
        shared_texture.write_bytes(b"")
        assert textures.find_image_path(str(model / "test.o3d"), r"shared\panel.png") == str(shared_texture)
        spline_dir = directory / "Splines"
        spline_dir.mkdir()
        spline = spline_dir / "Road.SLI"
        spline.write_text("[profile]\n0\n[profilepnt]\n0\n1\n0\n1\n", encoding="utf-8")
        points, _ = addon.o3d_io.io_omsi_spline.load_spline(r"splines\road.sli", str(directory))
        assert points == [[[0.0, 1.0, 0.0, 1.0, 0]]], points
        map_dir = directory / "Maps" / "Town"
        map_dir.mkdir(parents=True)
        map_path = map_dir / "Tile.MAP"
        map_path.write_text("", encoding="utf-8")
        terrain = map_dir / "Tile.MAP.TERRAIN"
        terrain.write_bytes(bytes(4 + 61 * 61 * 4))
        splat_dir = map_dir / "Texture" / "Map"
        splat_dir.mkdir(parents=True)
        splat = splat_dir / "tile.map.1.PNG"
        for image_path in (splat, directory / "Texture" / "Grass.PNG", directory / "Texture" / "Gravel.PNG"):
            image = bpy.data.images.new("case-path-fixture", width=1, height=1)
            image.file_format = "PNG"
            image.filepath_raw = str(image_path)
            image.save()
            bpy.data.images.remove(image)
        global_cfg = {"[groundtex]": [
            [r"texture\grass.png", "", "", "10"],
            [r"texture\gravel.png", "", "", "10"],
        ]}
        obj, heights = addon.o3d_io.io_omsi_tile.import_terrain_mesh(str(map_path), global_cfg)
        assert len(heights) == 61 and heights[0] == [0.0] * 61
        assert any(image.filepath == str(splat) for image in bpy.data.images)
        assert any(
            node.type == "TEX_IMAGE" and node.image
            and node.image.filepath == str(directory / "Texture" / "Gravel.PNG")
            for node in obj.data.materials[0].node_tree.nodes
        )


def assert_missing_meshes_are_reported(addon: ModuleType) -> None:
    """Unreadable meshes used to be skipped silently; the caller must be able to see them."""
    with tempfile.TemporaryDirectory(prefix="blender-o3d-io-missing-") as temporary:
        directory = Path(temporary)
        cfg_path = directory / "model.cfg"
        cfg_path.write_text("[mesh]\ngone.o3d\n\n", encoding="cp1252")
        missing = []
        imported = addon.o3d_io.io_o3d_import.do_import(
            str(cfg_path), bpy.context, False, "", False, missing_files=missing
        )
        assert imported == []
        assert len(missing) == 1, missing
        assert missing[0].endswith("gone.o3d"), missing


def assert_import_failure_tally(addon: ModuleType) -> None:
    """Count repeated failures by filename at the end, without leaking between imports."""
    with tempfile.TemporaryDirectory(prefix="blender-o3d-io-tally-") as temporary:
        directory = Path(temporary)
        vertices = [
            (0, 0, 0, 0, 0, 1, 0, 0),
            (1, 0, 0, 0, 0, 1, 1, 0),
            (0, 1, 0, 0, 0, 1, 0, 1),
        ]
        transform = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
        material = (1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, "gone.png")
        for name, materials in (("textured.o3d", [material]), ("clean.o3d", [])):
            with (directory / name).open("wb") as file:
                addon.o3d_io.o3dconvert.export_o3d(
                    file, vertices, [(0, 1, 2, 0)], materials, [], transform
                )
        cfg_path = directory / "model.cfg"
        cfg_path.write_text(
            "[mesh]\ntextured.o3d\n\n[mesh]\ngone.o3d\n\n"
            "[LOD]\n100\n\n[mesh]\ntextured.o3d\n\n[mesh]\ngone.o3d\n\n",
            encoding="cp1252",
        )
        missing = ["previous.o3d"]
        for collector in (missing, None):
            output = io.StringIO()
            with redirect_stdout(output):
                imported = addon.o3d_io.io_o3d_import.do_import(
                    str(cfg_path), bpy.context, False, "", False, missing_files=collector
                )
            try:
                assert len(imported) == 2, imported
                lines = output.getvalue().splitlines()
                loaded_index = next(i for i, line in enumerate(lines) if line.startswith("[O3D_Import] Loaded "))
                tally = lines[loaded_index + 1:]
                assert tally == [
                    "[O3D_Import] Unreadable meshes: 2 occurrences, 1 unique filename(s)",
                    "[O3D_Import]   2x gone.o3d",
                    "[O3D_Import] Missing textures: 2 occurrences, 1 unique filename(s)",
                    "[O3D_Import]   2x gone.png",
                ], tally
                assert "WARNING: 2 of 4 meshes" in output.getvalue(), output.getvalue()
            finally:
                for obj in imported:
                    bpy.data.objects.remove(obj, do_unlink=True)
        assert len(missing) == 3 and missing[0] == "previous.o3d", missing

        output = io.StringIO()
        with redirect_stdout(output):
            imported = addon.o3d_io.io_o3d_import.do_import(
                str(directory / "clean.o3d"), bpy.context, False, "", False, missing_files=missing
            )
        try:
            assert len(imported) == 1, imported
            assert output.getvalue().splitlines()[-2:] == [
                "[O3D_Import] Unreadable meshes: 0 occurrences, 0 unique filename(s)",
                "[O3D_Import] Missing textures: 0 occurrences, 0 unique filename(s)",
            ], output.getvalue()
            assert "meshes could not be read" not in output.getvalue(), output.getvalue()
        finally:
            for obj in imported:
                bpy.data.objects.remove(obj, do_unlink=True)
