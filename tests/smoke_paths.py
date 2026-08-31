"""Resource path resolution and missing-file reporting checks."""
import os
import tempfile
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
