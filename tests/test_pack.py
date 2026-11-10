import unittest
from pathlib import Path
import tempfile
import shutil

import pack


class TestManifestParsing(unittest.TestCase):
    def test_read_manifest_valid(self):
        root = Path(__file__).resolve().parent.parent
        manifest = pack.read_manifest(root / "blender_manifest.toml")
        self.assertEqual(manifest["id"], "blender_o3d_io")
        self.assertEqual(manifest["version"], "1.3.4")
        self.assertIn("/docs/", manifest["paths_exclude_pattern"])

    def test_is_excluded(self):
        patterns = [
            "__pycache__/",
            ".*",
            "/.git/",
            "/dist/",
            "/docs/",
            "/tests/",
            "*.pyc",
            "*.zip",
        ]
        self.assertTrue(pack.is_excluded("__pycache__/foo.cpython-311.pyc", patterns))
        self.assertTrue(pack.is_excluded(".git/config", patterns))
        self.assertTrue(pack.is_excluded("tests/blender_smoke.py", patterns))
        self.assertTrue(pack.is_excluded("docs/research/notes.md", patterns))
        self.assertTrue(pack.is_excluded("dist/output.zip", patterns))
        self.assertTrue(pack.is_excluded("some/nested/file.pyc", patterns))
        self.assertTrue(pack.is_excluded("pack.py", patterns))

        self.assertFalse(pack.is_excluded("blender_manifest.toml", patterns))
        self.assertFalse(pack.is_excluded("__init__.py", patterns))
        self.assertFalse(pack.is_excluded("o3d_io/__init__.py", patterns))
        self.assertFalse(pack.is_excluded("o3d_io/io_o3d_export.py", patterns))
        self.assertFalse(pack.is_excluded("LICENSE", patterns))
        self.assertFalse(pack.is_excluded("README.md", patterns))

    def test_collect_files(self):
        root = Path(__file__).resolve().parent.parent
        manifest = pack.read_manifest(root / "blender_manifest.toml")
        files = pack.collect_files(root, manifest["paths_exclude_pattern"])
        rel_names = {f.relative_to(root).as_posix() for f in files}

        self.assertIn("blender_manifest.toml", rel_names)
        self.assertIn("__init__.py", rel_names)
        self.assertIn("o3d_io/__init__.py", rel_names)
        self.assertIn("LICENSE", rel_names)

        # Ensure no excluded files leaked
        for name in rel_names:
            self.assertFalse(name.startswith("tests/"), f"tests leaked: {name}")
            self.assertFalse(name.startswith("docs/"), f"docs leaked: {name}")
            self.assertFalse(name.startswith(".git/"), f".git leaked: {name}")
            self.assertFalse(name.endswith(".pyc"), f".pyc leaked: {name}")
            self.assertNotEqual(name, "pack.py")

    def test_build_and_validate_package(self):
        root = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            zip_path, file_count, size_bytes = pack.build_package(
                repo_root=root,
                output_dir=out_dir,
                quiet=True,
            )
            self.assertTrue(zip_path.is_file())
            self.assertGreater(file_count, 10)
            self.assertGreater(size_bytes, 1000)

            # Validate the created zip
            pack.validate_package(zip_path, expected_id="blender_o3d_io", expected_version="1.3.4")

    def test_dry_run(self):
        root = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            zip_path, file_count, size_bytes = pack.build_package(
                repo_root=root,
                output_dir=out_dir,
                dry_run=True,
                quiet=True,
            )
            self.assertFalse(zip_path.exists())
            self.assertGreater(file_count, 10)
            self.assertEqual(size_bytes, 0)


if __name__ == "__main__":
    unittest.main()
