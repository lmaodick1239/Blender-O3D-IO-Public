# Standalone Add-on Packaging Script Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a standalone Python 3 script `pack.py` at the repository root that packs the Blender add-on into a distribution-ready ZIP archive formatted for Blender 4.2+ extensions, along with tests and updating `blender_manifest.toml`.

**Architecture:** Pure Python standard library tool (`pack.py`) using `tomllib`/regex for manifest parsing, glob/prefix matching for exclusion filtering, and `zipfile` for reproducible archive creation and verification in `dist/`.

**Tech Stack:** Python 3 standard library (`zipfile`, `pathlib`, `argparse`, `tomllib`/`re`, `fnmatch`), `unittest`.

## Global Constraints

- Standalone executable Python 3 script `pack.py` at repository root with `#!/usr/bin/env python3` and executable permissions.
- Zero third-party dependencies (no pip packages, no external CLI dependencies).
- Blender 4.2+ extension archive layout (`blender_manifest.toml` and `__init__.py` at the root of the archive).
- Output placed into `dist/<id>-<version>.zip` by default.
- Build exclusions must omit `tests/`, `docs/`, `dist/`, `render/`, `.git/`, `.github/`, `__pycache__/`, `pack.py`, `*.pyc`, `*.zip`, and dotfiles.

---

### Task 1: Update Extension Manifest Exclude Patterns

**Files:**
- Modify: `blender_manifest.toml`

**Interfaces:**
- Produces: `paths_exclude_pattern` including `"/docs/"` in `blender_manifest.toml`.

- [ ] **Step 1: Check existing manifest build section**

Inspect `blender_manifest.toml` to verify current `paths_exclude_pattern`.

- [ ] **Step 2: Add "/docs/" to paths_exclude_pattern**

Update `blender_manifest.toml`:
```toml
paths_exclude_pattern = [
    "__pycache__/",
    ".*",
    "/.git/",
    "/.github/",
    "/dist/",
    "/docs/",
    "/render/",
    "/tests/",
    "*.pyc",
    "*.zip",
]
```

- [ ] **Step 3: Validate manifest with blender CLI if available**

Run: `blender --factory-startup --command extension validate .`
Expected: `Success parsing TOML in "."`

- [ ] **Step 4: Commit**

```bash
git add blender_manifest.toml
git commit -m "build: exclude docs directory from extension package

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 2: Manifest Parsing and Pattern Matching Core

**Files:**
- Create: `pack.py`
- Create: `tests/test_pack.py`

**Interfaces:**
- Produces:
  - `pack.read_manifest(manifest_path: pathlib.Path) -> dict`
  - `pack.is_excluded(rel_path: str, patterns: list[str]) -> bool`

- [ ] **Step 1: Write failing unit tests for manifest parsing and path exclusion**

In `tests/test_pack.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest discover -s tests -p 'test_pack.py' -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pack'`

- [ ] **Step 3: Implement read_manifest and is_excluded in pack.py**

In `pack.py`:
```python
#!/usr/bin/env python3
"""
Standalone packaging script for Blender O3D IO add-on.
Packs the add-on into a distribution-ready ZIP archive for Blender 4.2+ extensions.
"""

from __future__ import annotations

import fnmatch
import os
from pathlib import Path
import re
import sys
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:
    tomllib = None  # type: ignore[assignment]


def read_manifest(manifest_path: Path) -> dict[str, Any]:
    """Parse blender_manifest.toml for id, version, and exclude patterns."""
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    text = manifest_path.read_text(encoding="utf-8")
    if tomllib is not None:
        data = tomllib.loads(text)
        pkg_id = data.get("id", "")
        version = data.get("version", "")
        build = data.get("build", {})
        patterns = list(build.get("paths_exclude_pattern", []))
    else:
        # Regex fallback for Python < 3.11
        id_match = re.search(r'^\s*id\s*=\s*"([^"]+)"', text, re.MULTILINE)
        ver_match = re.search(r'^\s*version\s*=\s*"([^"]+)"', text, re.MULTILINE)
        pkg_id = id_match.group(1) if id_match else ""
        version = ver_match.group(1) if ver_match else ""

        # Extract paths_exclude_pattern array
        pat_match = re.search(
            r"paths_exclude_pattern\s*=\s*\[(.*?)\]", text, re.DOTALL
        )
        patterns = []
        if pat_match:
            patterns = re.findall(r'"([^"]+)"', pat_match.group(1))

    if not pkg_id:
        raise ValueError(f"Could not parse 'id' from {manifest_path}")
    if not version:
        raise ValueError(f"Could not parse 'version' from {manifest_path}")

    return {
        "id": pkg_id,
        "version": version,
        "paths_exclude_pattern": patterns,
    }


def is_excluded(rel_path: str, patterns: list[str]) -> bool:
    """Return True if rel_path (POSIX-style) matches any exclude pattern."""
    norm_path = rel_path.replace("\\", "/").strip("/")

    # Always exclude packaging tool and editor temporary files
    if norm_path == "pack.py" or norm_path.endswith(("/pack.py",)):
        return True
    if norm_path.endswith((".swp", ".swo", "~")):
        return True

    # Root dotfiles / hidden entries (e.g. .git, .gitignore)
    parts = norm_path.split("/")
    if any(p.startswith(".") for p in parts):
        return True

    for raw_pat in patterns:
        pat = raw_pat.strip()
        is_dir_pattern = pat.endswith("/")
        clean_pat = pat.strip("/")

        # Leading slash means match from repo root
        if pat.startswith("/"):
            if is_dir_pattern:
                if norm_path == clean_pat or norm_path.startswith(clean_pat + "/"):
                    return True
            else:
                if fnmatch.fnmatch(norm_path, clean_pat):
                    return True
        else:
            # Pattern without leading slash matches any path segment or filename
            if is_dir_pattern:
                if clean_pat in parts:
                    return True
            else:
                if fnmatch.fnmatch(parts[-1], clean_pat) or fnmatch.fnmatch(norm_path, clean_pat):
                    return True

    return False
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest discover -s tests -p 'test_pack.py' -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add pack.py tests/test_pack.py
git commit -m "feat(pack): add manifest parser and exclusion matching

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 3: File Collection, Archive Generation, and Validation

**Files:**
- Modify: `pack.py`
- Modify: `tests/test_pack.py`

**Interfaces:**
- Produces:
  - `pack.collect_files(repo_root: Path, patterns: list[str]) -> list[Path]`
  - `pack.build_package(repo_root: Path, output_dir: Path, output_name: str | None = None, dry_run: bool = False, verbose: bool = False, quiet: bool = False) -> tuple[Path, int, int]`
  - `pack.validate_package(zip_path: Path, expected_id: str, expected_version: str) -> None`

- [ ] **Step 1: Write unit tests for file collection, archive building, and validation**

In `tests/test_pack.py`, add:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest discover -s tests -p 'test_pack.py' -v`
Expected: FAIL with `AttributeError: module 'pack' has no attribute 'collect_files'`

- [ ] **Step 3: Implement collect_files, build_package, validate_package in pack.py**

Implement the functions in `pack.py`:
- `collect_files`: walks `repo_root` using `os.walk(..., topdown=True)`, skipping excluded directory subtrees in-place, and gathering remaining regular files.
- `build_package`:
  - Determines destination path `output_dir / output_name` (defaulting to `<id>-<version>.zip`).
  - If `dry_run`, returns `(target_path, len(files), 0)`.
  - Opens `zipfile.ZipFile(target_path, "w", compression=zipfile.ZIP_DEFLATED)`.
  - Writes each file into the zip using `arcname = file.relative_to(repo_root).as_posix()`.
  - Normalizes zip entry metadata (POSIX permissions).
  - Validates the resulting zip with `validate_package`.
- `validate_package`:
  - Inspects `zipfile.ZipFile(zip_path, "r")`.
  - Checks that `blender_manifest.toml` and `__init__.py` exist at zip root.
  - Checks that no entries match forbidden patterns (`tests/`, `docs/`, `__pycache__/`, `.git/`, `.github/`).

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest discover -s tests -p 'test_pack.py' -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add pack.py tests/test_pack.py
git commit -m "feat(pack): add packaging and archive validation logic

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 4: CLI Interface, Executable Permissions & Smoke Verification

**Files:**
- Modify: `pack.py`
- Modify: `tests/test_pack.py`
- Modify: `README.md` (mentioning the pack script)

**Interfaces:**
- Produces:
  - `pack.main(argv: list[str] | None = None) -> int`
  - CLI usage: `./pack.py [--output-dir DIR] [--output-name NAME] [--dry-run] [--quiet] [--verbose]`

- [ ] **Step 1: Write test for CLI argument parsing and main()**

In `tests/test_pack.py`, add:
```python
    def test_cli_help(self):
        with self.assertRaises(SystemExit) as ctx:
            pack.main(["--help"])
        self.assertEqual(ctx.exception.code, 0)

    def test_cli_dry_run(self):
        exit_code = pack.main(["--dry-run", "--quiet"])
        self.assertEqual(exit_code, 0)

    def test_cli_custom_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exit_code = pack.main(["--output-dir", tmpdir, "--output-name", "custom_addon.zip", "--quiet"])
            self.assertEqual(exit_code, 0)
            self.assertTrue((Path(tmpdir) / "custom_addon.zip").is_file())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest discover -s tests -p 'test_pack.py' -v`
Expected: FAIL with `AttributeError: module 'pack' has no attribute 'main'`

- [ ] **Step 3: Implement main() in pack.py and set executable permissions**

Add `main()` with `argparse.ArgumentParser` in `pack.py`:
```python
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Pack Blender O3D IO add-on into a distribution ZIP."
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=Path("dist"),
        help="Output directory for the generated ZIP (default: dist).",
    )
    parser.add_argument(
        "--output-name",
        "-n",
        type=str,
        default=None,
        help="Custom filename for the ZIP (default: <id>-<version>.zip).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show files that would be packaged without creating the ZIP.",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress non-essential output.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed file exclusion decisions.",
    )

    args = parser.parse_args(argv)
    ...
```
Make `pack.py` executable:
`chmod +x pack.py`

- [ ] **Step 4: Update README.md with packaging instructions**

Add a brief note in `README.md` under development/building on how to pack the add-on using `./pack.py`.

- [ ] **Step 5: Run tests and execute ./pack.py directly**

Run: `python3 -m unittest discover -s tests -p 'test_pack.py' -v`
Run: `./pack.py`
Verify: `dist/blender_o3d_io-1.3.4.zip` is created and valid.

- [ ] **Step 6: Commit**

```bash
git add pack.py tests/test_pack.py README.md
git commit -m "feat(pack): add CLI entry point and documentation

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```
