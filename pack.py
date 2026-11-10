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


def collect_files(repo_root: Path, patterns: list[str], verbose: bool = False) -> list[Path]:
    """Walk repo_root and return all non-excluded regular files."""
    collected: list[Path] = []

    for root, dirnames, filenames in os.walk(repo_root, topdown=True):
        rel_root = Path(root).relative_to(repo_root).as_posix()
        if rel_root == ".":
            rel_root = ""

        # Filter out subdirectories in-place so os.walk does not recurse into them
        surviving_dirs: list[str] = []
        for d in dirnames:
            rel_dir = f"{rel_root}/{d}" if rel_root else d
            # Treat directory check with trailing slash
            if is_excluded(rel_dir + "/", patterns):
                if verbose:
                    print(f"  [exclude dir]  {rel_dir}/", file=sys.stderr)
            else:
                surviving_dirs.append(d)
        dirnames[:] = surviving_dirs

        for f in filenames:
            rel_file = f"{rel_root}/{f}" if rel_root else f
            if is_excluded(rel_file, patterns):
                if verbose:
                    print(f"  [exclude file] {rel_file}", file=sys.stderr)
            else:
                full_path = Path(root) / f
                if full_path.is_file():
                    collected.append(full_path)

    collected.sort()

    # Validate essential core files exist
    rel_set = {p.relative_to(repo_root).as_posix() for p in collected}
    if "blender_manifest.toml" not in rel_set:
        raise FileNotFoundError("Missing required blender_manifest.toml in collected files")
    if "__init__.py" not in rel_set:
        raise FileNotFoundError("Missing required __init__.py in collected files")

    return collected


def format_bytes(num_bytes: int) -> str:
    """Return human-readable byte size."""
    if num_bytes < 1024:
        return f"{num_bytes} B"
    elif num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    else:
        return f"{num_bytes / (1024 * 1024):.2f} MB"


def validate_package(
    zip_path: Path,
    expected_id: str | None = None,
    expected_version: str | None = None,
) -> None:
    """Inspect and validate the integrity of a generated add-on ZIP package."""
    import zipfile

    if not zip_path.is_file():
        raise FileNotFoundError(f"Package file not found: {zip_path}")

    with zipfile.ZipFile(zip_path, "r") as zf:
        namelist = zf.namelist()
        if "blender_manifest.toml" not in namelist:
            raise ValueError(f"Invalid package {zip_path}: missing blender_manifest.toml at root")
        if "__init__.py" not in namelist:
            raise ValueError(f"Invalid package {zip_path}: missing __init__.py at root")

        forbidden_prefixes = ("tests/", "docs/", "__pycache__/", ".git/", ".github/", "dist/")
        for name in namelist:
            if any(name.startswith(p) for p in forbidden_prefixes):
                raise ValueError(f"Forbidden entry leaked into package {zip_path}: {name}")
            if name.endswith(".pyc"):
                raise ValueError(f"Python bytecode leaked into package {zip_path}: {name}")

        if expected_id or expected_version:
            manifest_text = zf.read("blender_manifest.toml").decode("utf-8")
            if expected_id and f'id = "{expected_id}"' not in manifest_text:
                raise ValueError(f"Package manifest ID does not match expected {expected_id}")
            if expected_version and f'version = "{expected_version}"' not in manifest_text:
                raise ValueError(f"Package manifest version does not match expected {expected_version}")


def build_package(
    repo_root: Path,
    output_dir: Path,
    output_name: str | None = None,
    dry_run: bool = False,
    verbose: bool = False,
    quiet: bool = False,
) -> tuple[Path, int, int]:
    """Collect add-on files and write a distribution ZIP package."""
    import zipfile

    manifest = read_manifest(repo_root / "blender_manifest.toml")
    pkg_id = manifest["id"]
    pkg_version = manifest["version"]
    patterns = manifest["paths_exclude_pattern"]

    filename = output_name if output_name else f"{pkg_id}-{pkg_version}.zip"
    target_zip = output_dir / filename

    files = collect_files(repo_root, patterns, verbose=verbose)

    if dry_run:
        if not quiet:
            print(f"Dry run: {len(files)} files to pack into {target_zip}:")
            for f in files:
                print(f"  {f.relative_to(repo_root).as_posix()}")
        return target_zip, len(files), 0

    output_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(target_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            arcname = f.relative_to(repo_root).as_posix()
            zinfo = zipfile.ZipInfo.from_file(f, arcname=arcname)
            # Normalize file attributes (rw-r--r--)
            zinfo.external_attr = 0o644 << 16
            with f.open("rb") as fp:
                zf.writestr(zinfo, fp.read(), compress_type=zipfile.ZIP_DEFLATED)

    validate_package(target_zip, expected_id=pkg_id, expected_version=pkg_version)
    size_bytes = target_zip.stat().st_size

    if not quiet:
        print(f"Built {target_zip} ({len(files)} files, {format_bytes(size_bytes)})")

    return target_zip, len(files), size_bytes


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for pack.py."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Pack Blender O3D IO add-on into a distribution ZIP archive."
    )
    parser.add_argument(
        "--source-dir",
        "-s",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Repository root directory containing blender_manifest.toml (default: script directory).",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=None,
        help="Output directory for the generated ZIP (default: <source-dir>/dist).",
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

    repo_root = args.source_dir.resolve()
    output_dir = args.output_dir.resolve() if args.output_dir else (repo_root / "dist")

    try:
        build_package(
            repo_root=repo_root,
            output_dir=output_dir,
            output_name=args.output_name,
            dry_run=args.dry_run,
            verbose=args.verbose,
            quiet=args.quiet,
        )
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())


