# Standalone Add-on Packaging Script Design

## Status and Goal

Design approved on 2026-11-10: create a standalone Python 3 packaging script (`pack.py`) at the repository root that packs the Blender add-on into a distribution-ready ZIP archive formatted for Blender 4.2+ extensions. The script requires no external dependencies or Blender installations, parses version and metadata dynamically from `blender_manifest.toml`, enforces build exclusions, places output in `dist/`, and performs post-packaging structural validation.

## Scope

The script provides a zero-dependency, executable packaging tool (`./pack.py` or `python3 pack.py`) tailored to this add-on repository.

### In Scope
- Standalone executable Python 3 script `pack.py` placed at the workspace root.
- Reading package ID, version, and exclude patterns directly from `blender_manifest.toml`.
- Collecting repository files and packing them into `dist/<id>-<version>.zip` (e.g. `dist/blender_o3d_io-1.3.4.zip`).
- Structuring the archive for Blender 4.2+ "Install from Disk" extension packaging (manifest, `__init__.py`, `o3d_io/`, `LICENSE`, `README.md`, etc., situated at archive root).
- Respecting and standardizing build exclusions (`.git`, `.github`, `dist`, `tests`, `docs`, `render`, `__pycache__`, `*.pyc`, `*.zip`, editor temp files).
- Updating `blender_manifest.toml` to include `/docs/` in `paths_exclude_pattern` to keep research disassemblies out of builds.
- CLI options (`--output-dir`, `--output-name`, `--dry-run`, `--quiet`, `--verbose`).
- Integrity validation of the generated ZIP (verifying root manifest, entry point, absence of excluded directories).
- Automated test coverage verifying the packaging script under `tests/`.

### Non-Goals
- Invoking Blender runtime binaries or `blender --command extension build` subprocesses.
- Creating legacy subfolder-wrapped ZIPs (user selected pure extension format).
- Modifying add-on code or functional runtime behavior.

## Components and Architecture

### 1. Manifest Parser (`read_manifest`)
- Parses `blender_manifest.toml` to extract:
  - `id`: Package identifier (default: `blender_o3d_io`).
  - `version`: Semantic version string (default: `1.3.4`).
  - `paths_exclude_pattern`: List of glob/path exclusion patterns.
- Implementation:
  - Uses standard library `tomllib` on Python 3.11+.
  - Falls back to a robust regex-based parser on Python 3.10 and older to ensure cross-version compatibility without `pip install` requirements.

### 2. File Collector & Exclusion Matcher (`collect_files`)
- Traverses repository files starting from repository root.
- Evaluates relative POSIX paths against exclusion rules:
  - Directory prefix patterns: `__pycache__/`, `tests/`, `docs/`, `dist/`, `render/`, `.git/`, `.github/`, `.vscode/`, `.idea/`.
  - File glob patterns: `*.pyc`, `*.pyo`, `*.zip`, `*.swp`, `*~`, `.DS_Store`, `pack.py`.
  - Root-level hidden files/directories starting with `.` (e.g. `.gitignore`).
- Ensures mandatory core files are present:
  - `blender_manifest.toml`
  - `__init__.py`
  - `o3d_io/__init__.py`
  - `LICENSE`

### 3. Archive Builder (`build_package`)
- Target location: `dist/<id>-<version>.zip` (unless overridden by `--output-dir` or `--output-name`).
- Automatically creates output directory if missing.
- Archives files using `zipfile.ZipFile(..., mode='w', compression=zipfile.ZIP_DEFLATED)`.
- Normalizes internal zip entry paths to POSIX slashes (`/`).
- Sets standard file attributes (`0o644` for files, `0o755` for directories) to maintain reproducible archives across platforms.

### 4. Archive Validator (`validate_package`)
- Inspects the newly written ZIP archive:
  - Confirms `blender_manifest.toml` exists at archive root.
  - Confirms `__init__.py` exists at archive root.
  - Confirms no entry starts with any excluded prefix (`tests/`, `docs/`, `__pycache__/`, `.git/`, `dist/`).
- Computes archive stats: file count and uncompressed/compressed byte size.

### 5. CLI Interface (`main`)
- Arguments:
  - `--output-dir`, `-o`: Directory to store the resulting zip (default: `dist`).
  - `--output-name`, `-n`: Explicit filename for the zip (default: `<id>-<version>.zip`).
  - `--dry-run`: Display all matched files and exclusions without creating the zip.
  - `--quiet`, `-q`: Suppress detailed file listings, printing only the final status.
  - `--verbose`, `-v`: Print debug info on exclusion matches.
- Exit code: 0 on success, non-zero on validation or file errors.

## Test Strategy

1. **Unit & Functional Tests (`tests/test_pack.py`)**:
   - Manifest parsing test (valid manifest, missing manifest error handling).
   - Exclusion matching test (ensures tests, docs, pycache, git are excluded; ensures code and manifest are included).
   - Dry-run test (verifies file list without writing archive).
   - End-to-end packaging test (builds into a temporary directory, verifies zip integrity, checks internal archive listing).
2. **Command Verification**:
   - Execute `./pack.py` directly from bash.
   - Inspect generated `dist/blender_o3d_io-1.3.4.zip`.
