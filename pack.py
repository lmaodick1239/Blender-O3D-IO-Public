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
