# Panel-Led Human Configuration Export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add rig-derived `.hum` generation and a complete Export Human action directly to the OMSI Character Tools panel.

**Architecture:** One focused `omsi_human` module measures rest landmarks, preserves conversion metadata, serializes human text, and coordinates human export. The native sidebar owns persistent rig settings and operators; actual O3D/CFG serialization continues through the existing backend with explicit human-only candidate and binding overrides. Generic export remains unchanged.

**Tech Stack:** Python standard library, Blender Python/RNA/mathutils, existing O3D/CFG serializers and assertion-based Blender smoke tests. Blender 5.0.1 is available locally.

## Global Constraints

- Approved spec: `docs/superpowers/specs/2026-11-09-human-config-export-design.md`; the panel-led revision governs.
- The existing **OMSI > OMSI Character Tools** sidebar panel is the primary workflow, with **Human Configuration & Export**, **Refresh Measurements**, **Check Export Readiness**, and **Export Human**.
- For a chosen destination `character.hum`, write the sibling `character.cfg`; the HUM uses `character.cfg` as its relative `[model]` reference.
- Exactly 22 `[links]` scalars: hip XYZ, knee XYZ, waist YZ, shoulder XYZ, elbow XYZ, neck YZ, hand XYZ, finger XYZ.
- Write Windows-compatible CP1252 text with CRLF line endings and finite locale-independent numeric values.
- Editable starting values: seat height `0.90`, feet distance `0.04`, walking `1.4 / 80 / 1.0 / 1.0 / 0.0`, voice `M2`, mass 70 kg serialized as `0.07` tonnes.
- Rest-space geometry, object transforms and export scale exactly once. Do not derive pivots from collider centers or human mass from physics masses.
- Missing essential landmarks block human generation unless overridden; stale captured points require confirmation or overrides. No copied stock joint geometry or zero fallbacks.
- One canonical rig and its intended meshes/LODs per export. Exclude rigid bodies and joint helpers from human meshes, CFG, and bounds; missing physics is normal.
- Existing generic CFG/SCO/O3D behavior, source data, pose, selection, modifier flags, and unrelated scene objects must remain unchanged.
- Reuse the existing serializers, canonical slot table, safe paths, and existing assertion-based test conventions; no added dependency or generalized exporter framework.
- New logic requires a failing test first, then a passing test and a reviewed commit. Keep full command/output evidence in the task report.
- User explicitly chose implementation in the current `blender-5.2-support` checkout, not a new worktree. Do not switch branches or touch the older MMD worktree.
- Do not modify/resave `tests/Untitled2.blend`; do not claim OMSI in-game validation without running OMSI.

## File Responsibilities

- Create `o3d_io/omsi_human.py`: human data/landmark measurement, metadata capture, diagnostics, serialization, and orchestration.
- Modify `o3d_io/mmd_rig.py`: call metadata capture at the successful conversion boundary before source deletion; preserve rollback semantics.
- Modify `o3d_io/io_o3d_export.py`: optional explicit candidate set and human binding mode, preserving default calls.
- Modify `o3d_io/o3d_cfg_parser.py`: thread explicit candidates and serialized human bindings, filtering conflicting preserved skin commands only for human mode.
- Modify `o3d_io/omsi_character_panel.py`: rig-owned settings, native child panel, measurement/readiness/export operators, clean registration.
- Create `tests/smoke_human.py`: real Blender fixtures and core/export/panel checks; reusable `CORE_CHECKS`, `EXPORT_CHECKS`, `PANEL_CHECKS`, `CHECKS` lists.
- Modify `tests/blender_smoke.py`: add the completed human checks to the established suite.
- Modify `README.md` and `docs/tutorials/mmd-to-omsi-human.md`: document the implemented panel workflow and limits.

## Task 1: Human Measurements, Conversion Landmarks, and Text Serialization

**Files:** Create `o3d_io/omsi_human.py`, `tests/smoke_human.py`; modify `o3d_io/mmd_rig.py`.

**Interfaces:**

- `DEFAULT_SETTINGS`: dict with `seat_height`, `feetdist`, `walk_params` (five numbers), `voice`, `mass_kg` using the exact global defaults.
- `capture_landmarks(source_armature, target_armature, *, template_armature=None) -> None`: persist versioned target-armature-local metadata under `omsi_human_landmarks`, including rest fingerprint and available true neck/finger landmarks. AUTO captures source; TEMPLATE copies compatible target-template metadata or leaves the missing points explicit. Absence of source landmarks must not break generic conversion.
- `measure_human(armature, meshes, *, overrides=None, scale=1.0, context=None, confirm_stale=False) -> dict`: keys `errors` and `warnings` (lists of strings), `links` (22 floats, or None when unresolved), `height` (float or None), and `landmarks` (named final file-space vectors). Overrides are keyed by `hip`, `knee`, `waist`, `shoulder`, `elbow`, `neck`, `hand`, `finger`, `height`; paired overrides represent the symmetric file point, not two different bodies. Scalars/vectors must be validated.
- `serialize_hum(cfg_name, measurements, settings=None) -> bytes`: validate measurements/settings/string safety and return CP1252/CRLF text, not write files.
- `physics_diagnostics(armature, objects) -> dict`: body/joint counts, explicit bone associations and secondary joint categories; no physics-derived measurements.

- [x] **Step 1: Write failing core checks and standalone runner.** Use actual Blender armature/mesh fixtures, not mocks of the production functions. A serializer check must assert the exact output block shape:

```python
measurements = {'errors': [], 'warnings': [], 'height': 1.8,
                'links': [float(i) / 10 for i in range(22)], 'landmarks': {}}
payload = human.serialize_hum('character.cfg', measurements)
assert b'[model]\r\ncharacter.cfg\r\n' in payload
assert b'[mass]\r\n0.07\r\n' in payload
lines = payload.decode('cp1252').splitlines()
start = lines.index('[links]') + 1
end = lines.index('[walk_param]')
assert len([line for line in lines[start:end] if line.strip()]) == 22
```

Add meaningful checks for source metadata surviving source deletion, template metadata using target rather than source rest points, missing neck/fingers versus numeric overrides, stale rest edits, true MMD names versus dummy/shadow helpers, symmetry/off-center warnings, invalid transforms, positive geometry/settings, and string/control-character rejection.

- [x] **Step 2: Run RED.** Run `blender --background --factory-startup --disable-autoexec --python tests/smoke_human.py`. Record expected feature-missing assertion/import failure, with exit status and Blender traceback; use `--python-exit-code 1` for every new test run so exceptions cannot masquerade as a successful process.

- [x] **Step 3: Implement the minimal core and conversion hook.** Use the local native parser evidence in `docs/research/evidence/omsi-bones/func-00624b40.c` plus the shipped-file documentation to establish input XYZ versus internal XZY. Keep file serialization ordered XYZ; write a golden fixture projecting a measured rest point to exported O3D coordinates and compare them numerically with nonzero Y and Z. Use the existing `prepared_export_mesh` context manager for evaluated rest bounds, excluding physics and lower LOD duplicates; do not apply object scale or display units twice. Use a deterministic rest-geometry fingerprint for staleness. Capture metadata before the conversion callback/source-deletion commit so rollback still removes failed outputs. Use explicit missing-point errors instead of synthesized hand-tail anatomy.

A minimal scalar formatter must reject nonfinite values before formatting:

```python
from math import isfinite

def _number(value):
    value = float(value)
    if not isfinite(value):
        raise ValueError('Human values must be finite')
    return format(value, '.9g')
```

- [x] **Step 4: Run GREEN and regression checks.** Run the new human script with `--python-exit-code 1`, `python3 -m unittest discover -s tests -p 'test_*.py'`, and the existing Blender smoke script. Include exact RED/GREEN commands and final pass markers in the report. Verify metadata survives a temporary save/reload without touching the supplied fixture.
- [x] **Step 5: Self-review and commit only task files.** `git diff --check`; stage the three task files and commit `feat(human): derive and serialize rig geometry`. Report public signatures, coordinate proof, test evidence, and any unresolved concern.

## Task 2: Safe Human Export Through Shared O3D/CFG Backends

**Files:** Modify `o3d_io/omsi_human.py`, `o3d_io/io_o3d_export.py`, `o3d_io/o3d_cfg_parser.py`, `tests/smoke_human.py`.

**Consumes:** Task 1 `measure_human`, `serialize_hum`, `DEFAULT_SETTINGS`, `physics_diagnostics` exactly as defined above.

**Produces:**

- `human_meshes(context, armature, *, selection_only=True) -> list`: use intended scene membership; mesh selection keeps scope, armature-only selection expands to its bound meshes/LODs; reject multiple rigs and exclude physics/skip_export helpers. Do not alter selection to communicate the set.
- `export_human(filepath, context, armature, meshes, *, settings=None, overrides=None, scale=1.0, overwrite=False, confirm_stale=False, o3d_version=7, export_custom_normals=True) -> dict`: preflight all outputs and serialized geometry, export model via shared backend, publish HUM last. Return `hum_path`, `cfg_path`, `mesh_paths`, `warnings`.
- Extend `do_export` with optional keyword-only `objects=None, human_bindings=False`; default existing calls retain behavior. Extend `write_cfg` with optional `objects_override=None, human_bindings_by_object=None`; explicit human objects must constrain CFG independently of scene selection.

- [x] **Step 1: Write RED export checks.** Use temporary output directories and real serialized O3D/CFG files. Begin with a real fixture and final file checks:

```python
result = human.export_human(str(root / 'character.hum'), bpy.context,
                            armature, [mesh], overrides=required_overrides)
assert Path(result['hum_path']).is_file()
assert Path(result['cfg_path']).is_file()
assert all(Path(path).is_file() for path in result['mesh_paths'])
assert b'[model]\r\ncharacter.cfg\r\n' in Path(result['hum_path']).read_bytes()
assert source_snapshot() == before
```

Add checks for unrelated/selected rigid-body/joint exclusion from both CFG and O3D candidates, repeated LOD canonical bindings, smoothskin state, conflicting mesh/material preserved `[setbone]` blocks, no source ID-property changes, armature-only selection, explicit mesh subset selection, and absence of physics. Validate existing generic exporter output against its established checks.

Add failure checks that put sentinel bytes at destinations and prove unchanged bytes after overwrite refusal, invalid landmarks/settings, case-insensitive lexical/resolved collisions, traversal/symlink escape, multiple rigs, unencodable model names, and an injected model serialization failure. Fault injection is permitted only at the actual file-I/O boundary; assertions must inspect preserved files and absent HUM output, not mock call counts.

- [x] **Step 2: Run RED.** Run the new human script with `--python-exit-code 1`; verify the failure names the missing export API or observable candidate leak, not a malformed fixture.
- [x] **Step 3: Implement safe orchestration and explicit serializer plumbing.** The current CFG writer ignores its deprecated `objs` parameter and rebuilds candidates from scene selection: add the explicit override and thread it all the way through LOD buckets. Use actual serialized bone names for canonical slot emission and skip conflicting preserved skin commands at both mesh and material levels only in human mode. Reuse `CANONICAL_SLOTS`; do not duplicate its numeric table.

Preflight object geometry and all casefolded lexical/resolved output destinations, including HUM/CFG collisions with mesh paths, before any file opens. Validate CP1252 strings and numbers before writes. Require `overwrite=True` for any existing destination in the generated set. For human-mode CFG defaults, use local scene groups/friendlyname fallbacks rather than inserting persistent source scene properties. Publish the prepared HUM bytes only after shared mesh/CFG export succeeds:

```python
# payload and the complete destination set are validated before this point.
io_o3d_export.do_export(cfg_path, context, global_matrix, False, o3d_version,
                       export_custom_normals, objects=meshes, human_bindings=True)
with open(hum_path, 'wb') as stream:
    stream.write(payload)
```

Do not promise multi-file transactional rollback for later OS write failures. Preserve context/pose/modifier flags and never use source-property mutations as an argument-passing mechanism.

- [x] **Step 4: Run GREEN and generic regressions.** Run human checks, codec tests, existing Blender smoke with `--python-exit-code 1`, and `git diff --check`. Report fresh commands and pass markers; distinguish expected existing negative-test diagnostics from new errors.
- [x] **Step 5: Self-review and commit only task files.** Commit `feat(human): export safe HUM and model bundle`. Report exact public interfaces and any file-I/O limitations.

## Task 3: Character Tools Panel, Native Operators, and Full Workflow

**Files:** Modify `o3d_io/omsi_character_panel.py`, `tests/smoke_human.py`, `tests/blender_smoke.py`, `README.md`, `docs/tutorials/mmd-to-omsi-human.md`; modify `o3d_io/omsi_human.py` only for an interface correction required by panel integration.

**Consumes:** The public APIs from Tasks 1 and 2; default generic `ExportModelCFG` remains untouched.

**Produces:** Rig-owned `Object.omsi_human_settings` property group, native operators `omsi.refresh_human_measurements`, `omsi.human_preflight`, `omsi.export_human`, and child panel `VIEW3D_PT_omsi_character_human` under `VIEW3D_PT_omsi_character` after Mesh LODs.

- [x] **Step 1: Write failing panel/operator checks.** Extend the existing real Blender registration and recording-layout pattern. Test defaults and rig-owned persistence, correct parent/category/order, visible Refresh/Readiness/Export actions, collapsed detailed landmark/walking controls, target labeling, no draw-time measurement/evaluation, no compatible target disabling, stale/missing data display, and independent settings for two rigs. Verify native operator execution, cancellation/error state restoration, unregister cleanup, and actual file output from `bpy.ops.omsi.export_human(filepath=..., ...)`.

```python
assert hasattr(bpy.ops.omsi, 'export_human')
settings = armature.omsi_human_settings
assert settings.voice == 'M2' and settings.mass_kg == 70
assert bpy.ops.omsi.refresh_human_measurements() == {'FINISHED'}
assert bpy.ops.omsi.export_human(filepath=str(root / 'panel.hum')) == {'FINISHED'}
assert (root / 'panel.hum').is_file() and (root / 'panel.cfg').is_file()
```

Reuse actual `UILayout` recording conventions from `tests/smoke_character_panel.py`. The test fixture must set real source pointers and required landmark overrides, not bypass the actual context/selection resolver.

- [x] **Step 2: Run RED.** Run human checks with `--python-exit-code 1`; confirm the missing RNA/operator/panel assertion fails before writing production UI code.
- [x] **Step 3: Implement native controls without new web UI or dependencies.** Keep data on the target armature using a registered Object pointer property; registration must add its property-group class before installing pointers and unregister must remove pointers before classes. The existing scene source fields resolve the target; do not introduce another global settings store. Show the settings/measurement status read-only until an explicit action evaluates geometry. Use per-landmark numeric override controls following the eight field groups, respecting vector lengths. Cache findings for display; full validation still runs on export.

The panel action uses an ExportHelper `.hum` picker, with generated-set overwrite consent reset on each new invocation (`SKIP_SAVE` or equivalent per-invocation state). Expose scale, Selection Only, normals, and O3D version only as needed for the shared export call. On errors return CANCELLED and restore WAIT cursor in `finally`; context/UI input errors must be reported clearly, not swallowed. Invalid/missing targets must never fall back to a preserved MMD rig or another character.

Add the new checks to the established suite:

```python
import smoke_human
# In CHECKS, before addon.unregister():
# Expand the actual list with the new module's complete checks.
CHECKS.extend(smoke_human.CHECKS)
```

- [x] **Step 4: Update user documentation.** Replace the tutorial's unconditional manual-only claim with the actual Character Tools section, refresh/override/readiness/export sequence, `.hum` destination picker, sibling file layout, CP1252/22-value format, supported rig/alignment limits, and in-game acceptance checklist. Keep the manual template as an alternative. Add a concise README feature/workflow note without unrelated cleanup.
- [x] **Step 5: Run full GREEN, fixture integration, and cleanup checks.** Run codec tests; standalone human checks; full Blender smoke with `--python-exit-code 1`; and a read-only `tests/Untitled2.blend` integration probe in a separate Blender process with autoexec disabled. The probe must inspect the known 51 bodies/34 secondary joints, convert a temporary in-memory working character, and either export a valid bundle or report explicitly required overrides, never substitute collider measurements. Hash the fixture before/after to prove it was not resaved. Verify RNA/operator cleanup after unregister and no changes under the older worktree. Run `git diff --check`.
- [x] **Step 6: Self-review and commit.** Commit `feat(human): add Character Tools export panel`. Provide paths and test evidence in the task report. Do not claim in-game correctness or addon hot reload in an existing Blender process.

## Review and Completion

Each task gets a fresh implementer, its own RED/GREEN report, and a read-only spec/quality reviewer receiving a generated diff package. Fix Important/Critical findings through the implementer and scoped re-review before progressing. Only one implementation agent writes at a time.

At feature completion, run fresh codec/human/full Blender verification and inspect the integrated diff. Obtain a whole-feature review against the approved spec and this plan; dispatch one combined fix wave for substantive final findings. Record all decisions, commits, and test evidence in this plan's SDD ledger. Leave the feature on the user's selected checkout and report the actual panel location, output workflow, verified results, and any remaining OMSI-only acceptance checks.
