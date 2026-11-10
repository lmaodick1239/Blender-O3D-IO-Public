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


if __name__ == "__main__":
    unittest.main()
