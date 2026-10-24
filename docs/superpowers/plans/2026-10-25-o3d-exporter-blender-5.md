# O3D Exporter Blender 5 Port Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate the ignored `Blender-OMSI-Exporter/io_export_o3d` implementation as the existing add-on’s direct `.o3d` export backend with Blender 5.0+ support.

**Architecture:** Add the upstream exporter’s binary, geometry, material, and indexing modules under `o3d_io/o3d_exporter/`. Keep the root add-on as the sole registration owner and route only direct `.o3d` export through the new backend; CFG/SCO export, import, and map workflows remain on their current paths. Reuse and extend `o3d_io/blender_compat.py` for Blender 5 mesh-normal, Principled BSDF, transparency, and evaluated-mesh lifecycle differences.

**Tech Stack:** Python 3.11+, Blender Python API 5.0+, Blender `bpy`/`mathutils`, existing O3D codec in `o3d_io/o3dconvert.py`, background Blender smoke tests.

## Global Constraints

- Target Blender support is Blender 5.0+.
- Preserve existing CFG, SCO, MAP, and import workflows.
- Direct `.o3d` export uses the ported upstream backend.
- Existing `.cfg` and `.sco` export paths remain unchanged; only tightly coupled compatibility fixes may modify them.
- The upstream standalone `__init__.py` is not registered.
- Empty material slots produce a valid neutral fallback material.
- OMSI 1 mode rejects wide indexes with an operator error.
- Evaluated meshes are cleared after conversion, including failure paths.
- Do not add runtime dependencies or commit generated caches, render output, or temporary artifacts.
- Do not revert unrelated pre-existing working-tree changes.

---

### Task 1: Add the upstream exporter core modules

**Files:**
- Create: `o3d_io/o3d_exporter/__init__.py`
- Create: `o3d_io/o3d_exporter/indexdict.py`
- Create: `o3d_io/o3d_exporter/meshio.py`
- Test: `tests/smoke_io.py`

**Interfaces:**
- Consumes: source modules from `.gitignorefolder/Blender-OMSI-Exporter/io_export_o3d/`.
- Produces: importable `o3d_io.o3d_exporter.meshio.Mesh`, `MeshFormatSpec`, `LongIndexesNotSupportedError`, and `IndexDict`.

- [ ] **Step 1: Add a package marker without registration side effects**

Create `o3d_io/o3d_exporter/__init__.py` with only a module docstring and no `bpy.utils.register_class` calls. The package must be safe to import from the root add-on.

- [ ] **Step 2: Port the deterministic index helper**

Copy `IndexDict` into `o3d_io/o3d_exporter/indexdict.py` and retain its `dict` subclass behavior:

```python
class IndexDict(dict[_K, int]):
    def __missing__(self, key: _K) -> int:
        self[key] = len(self)
        return self[key]
```

- [ ] **Step 3: Port the binary mesh model and encoder**

Copy `meshio.py` from the ignored exporter and preserve its public classes and exception names. Keep binary encoding independent of Blender imports so it can be smoke-tested without a running Blender UI.

- [ ] **Step 4: Add codec smoke assertions**

In `tests/smoke_io.py`, add a check that constructs `MeshFormatSpec(7)`, verifies long indexes and equality bits are supported, writes a minimal `Mesh` through `meshio.dump`, and asserts the output begins with the O3D signature bytes.

- [ ] **Step 5: Run the focused codec check**

Run:

```bash
blender --background --factory-startup --python tests/blender_smoke.py
```

Expected: the test reaches the codec assertion without import or registration errors. If Blender is unavailable, run the project’s available Python smoke command and record the missing Blender executable rather than installing an unrelated dependency.

- [ ] **Step 6: Commit the core module port**

```bash
git add o3d_io/o3d_exporter/__init__.py o3d_io/o3d_exporter/indexdict.py o3d_io/o3d_exporter/meshio.py tests/smoke_io.py
git commit -m "feat: add O3D exporter mesh core" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

### Task 2: Port the Blender 5 material-node adapter

**Files:**
- Create: `o3d_io/o3d_exporter/node_shader.py`
- Modify: `o3d_io/blender_compat.py`
- Test: `tests/smoke_materials.py`

**Interfaces:**
- Consumes: `o3d_io.o3d_exporter.meshio` material types and Blender 5 Principled BSDF node trees.
- Produces: `MaterialWrapper` with stable `diffuse`, `emissive`, `specular`, `power`, `texture`, `uv_map`, and UV-deformation access used by `Exporter`.

- [ ] **Step 1: Add failing Blender 5 material coverage**

Add a smoke assertion that creates a Principled BSDF material, assigns base color, alpha, roughness, specular, and an image texture, then verifies the exporter wrapper returns those values and the texture basename.

Use the existing material setup helpers in `tests/smoke_materials.py`; do not add a third-party test framework.

- [ ] **Step 2: Port the node traversal implementation**

Copy `node_shader.py` into `o3d_io/o3d_exporter/` and retain its group-node traversal and named-output behavior. Ensure every socket lookup goes through a compatibility-aware lookup rather than assuming removed or renamed Blender socket identifiers.

- [ ] **Step 3: Add Blender 5 socket compatibility**

Extend `o3d_io/blender_compat.py` with a small helper that returns the first available socket name from an ordered tuple, for example:

```python
def first_socket(node, *names):
    for name in names:
        if name in node.inputs:
            return node.inputs[name]
    return None
```

Use it for specular and emission inputs where Blender 4 and Blender 5 expose different names. Preserve the current fallback values when no compatible socket exists.

- [ ] **Step 4: Preserve transparency semantics**

Route material transparency changes through the existing `set_material_alpha_mode` and `get_material_alpha_mode` helpers. Do not reintroduce direct Blender 3/4-only assignments in the new material module.

- [ ] **Step 5: Run the material smoke checks**

Run:

```bash
blender --background --factory-startup --python tests/blender_smoke.py
```

Expected: material compatibility checks pass on Blender 5.0+ and existing terrain, solid, layered, and bump-map checks remain passing.

- [ ] **Step 6: Commit the material adapter**

```bash
git add o3d_io/o3d_exporter/node_shader.py o3d_io/blender_compat.py tests/smoke_materials.py
git commit -m "feat: port O3D material shader adapter" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

### Task 3: Port geometry conversion and O3D writing

**Files:**
- Create: `o3d_io/o3d_exporter/exporter.py`
- Modify: `o3d_io/blender_compat.py`
- Test: `tests/smoke_io.py`

**Interfaces:**
- Consumes: evaluated `bpy.types.Object` meshes, material slots, vertex groups, and `o3d_exporter.node_shader.MaterialWrapper`.
- Produces: `Exporter(...).export(objects: Iterable[bpy.types.Object], path: pathlib.Path) -> None`.

- [ ] **Step 1: Add failing geometry/export assertions**

Add smoke checks for:

```python
Exporter(weights=False).export([evaluated_object], output_path)
```

Then assert the file exists and can be imported by the existing O3D importer. Add separate cases for UV seams, empty material slots, custom normals, and vertex weights.

- [ ] **Step 2: Port the upstream `Exporter` implementation**

Copy `exporter.py` into the new package. Preserve its public constructor options:

```python
Exporter(
    compatibility=False,
    transforms={'LOC', 'ROT', 'SCA'},
    origin=True,
    weights=False,
    merge_within=True,
    merge_between=True,
    uv_layer='active_render',
    material_output_node_target='ALL',
    material_output_node_name='Export',
)
```

Preserve deterministic object sorting and material merging behavior.

- [ ] **Step 3: Adapt Blender 5 mesh preparation**

Replace direct calls to removed or version-sensitive split-normal APIs with `blender_compat.prepare_export_mesh`. Keep loop-triangle calculation and evaluated-mesh cleanup in the exporter’s `finally` path.

- [ ] **Step 4: Preserve long-index and OMSI 1 behavior**

Use `MeshFormatSpec(1)` for compatibility mode and `MeshFormatSpec(7)` otherwise. Let `LongIndexesNotSupportedError` retain the format version so the operator can report a precise error. Ensure long triangle and skin-weight indexes are included when selecting index width.

- [ ] **Step 5: Run geometry-focused smoke checks**

Run:

```bash
blender --background --factory-startup --python tests/blender_smoke.py
```

Expected: O3D export/reimport, UV seams, material-less meshes, weight export, narrow indexes, wide indexes, and pre-v3 rejection pass.

- [ ] **Step 6: Commit the geometry backend**

```bash
git add o3d_io/o3d_exporter/exporter.py o3d_io/blender_compat.py tests/smoke_io.py
git commit -m "feat: port O3D geometry exporter" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

### Task 4: Integrate direct `.o3d` export into the existing operator

**Files:**
- Modify: `__init__.py:190-395`
- Modify: `o3d_io/__init__.py`
- Test: `tests/blender_smoke.py`
- Test: `tests/smoke_io.py`

**Interfaces:**
- Consumes: `o3d_io.o3d_exporter.exporter.Exporter`, current `ExportModelCFG`, and existing `do_export` CFG/SCO path.
- Produces: unchanged `bpy.ops.export_scene.omsi_model_cfg` registration with `.o3d` routed to the new backend and `.cfg`/`.sco` routed to the existing backend.

- [ ] **Step 1: Add the routing test before changing the operator**

Add a smoke assertion that invokes the existing export operator with an `.o3d` path and verifies one valid output file is created. Add a second assertion that a `.cfg` path still enters the existing CFG export path.

- [ ] **Step 2: Add a narrow integration function**

In `o3d_io/io_o3d_export.py`, add a function with an explicit interface:

```python
def export_direct_o3d(filepath: str, context: bpy.types.Context, use_selection: bool,
                       o3d_version: int = 7, export_custom_normals: bool = True) -> None:
    ...
```

This function must gather selected or scene mesh objects, obtain evaluated objects from the dependency graph, sort them as required by the upstream backend, and call `Exporter(...).export(...)`.

- [ ] **Step 3: Route only the `.o3d` branch**

Update `ExportModelCFG.execute` or its existing dispatch helper so a `.o3d` suffix calls `export_direct_o3d`, while `.cfg` and `.sco` continue to call the existing `do_export` behavior. Preserve current operator properties and error reporting.

- [ ] **Step 4: Translate backend exceptions to operator reports**

Catch `LongIndexesNotSupportedError` and report cancellation for OMSI 1 compatibility. Catch filesystem or mesh conversion errors only where the current operator already reports errors; do not swallow unexpected exceptions that the smoke test should expose.

- [ ] **Step 5: Confirm registration isolation**

Keep the upstream exporter’s operator classes unregistered. Verify `bpy.ops.export_scene.omsi_model_cfg`, `bpy.ops.import_scene.omsi_model_cfg`, and `bpy.ops.import_scene.omsi_tile` remain available after add-on registration.

- [ ] **Step 6: Run the integration smoke test**

Run:

```bash
blender --background --factory-startup --python tests/blender_smoke.py
```

Expected: all existing operator-registration checks pass and direct `.o3d` export produces an importable file.

- [ ] **Step 7: Commit the operator integration**

```bash
git add __init__.py o3d_io/__init__.py o3d_io/io_o3d_export.py tests/blender_smoke.py tests/smoke_io.py
git commit -m "feat: integrate Blender 5 O3D exporter" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

### Task 5: Update user-facing compatibility documentation

**Files:**
- Modify: `README.md`
- Modify: `README-FR.md`
- Modify: `blender_manifest.toml` only if the verified minimum changes

**Interfaces:**
- Consumes: the implemented operator behavior and verified Blender 5 smoke results.
- Produces: documentation that accurately describes the integrated direct O3D exporter and Blender 5.0+ support.

- [ ] **Step 1: Update the English compatibility section**

Document that the direct O3D exporter is based on the integrated upstream backend, supports Blender 5.0+, preserves CFG/SCO/map workflows, and supports OMSI 1 compatibility mode with the documented wide-index limitation.

- [ ] **Step 2: Update the French compatibility section**

Mirror the same factual support and limitation statements in `README-FR.md` without adding claims not verified by the smoke test.

- [ ] **Step 3: Keep manifest metadata consistent**

Leave `blender_manifest.toml` at its current minimum unless Blender 5.0 support is verified and the manifest’s actual target policy requires a change. Do not raise the minimum above 5.0+ for a 5.2-only test result.

- [ ] **Step 4: Run documentation checks**

Run:

```bash
git diff --check -- README.md README-FR.md blender_manifest.toml
```

Expected: no whitespace errors and no version claim contradicts the manifest or smoke-test result.

- [ ] **Step 5: Commit the documentation update**

```bash
git add README.md README-FR.md blender_manifest.toml
git commit -m "docs: document Blender 5 O3D exporter" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

### Task 6: Run final verification and inspect the diff

**Files:**
- Test: `tests/blender_smoke.py`
- Test: `tests/smoke_io.py`
- Test: `tests/smoke_materials.py`
- Inspect: all files changed by this port

**Interfaces:**
- Consumes: all implementation and documentation changes from Tasks 1-5.
- Produces: verified test output and a clean, scoped final diff.

- [ ] **Step 1: Run the full background Blender smoke test**

Run:

```bash
blender --background --factory-startup --python tests/blender_smoke.py
```

Expected: the command exits with status 0 and prints `BLENDER_O3D_IO_SMOKE_OK`.

- [ ] **Step 2: Run repository Python smoke checks if available**

Run:

```bash
python3 tests/smoke_io.py
python3 tests/smoke_materials.py
python3 tests/smoke_paths.py
```

Expected: checks that do not require `bpy` pass; Blender-dependent checks should be run through the background Blender command rather than plain CPython.

- [ ] **Step 3: Check the final diff and working tree**

Run:

```bash
git diff --check
 git status --short
 git diff --stat HEAD~6..HEAD
```

Expected: no whitespace errors, only intended port commits plus pre-existing user changes, and no generated caches or render files added by the port.

- [ ] **Step 4: Verify ignored source remains untouched**

Run:

```bash
git status --short --ignored .gitignorefolder/Blender-OMSI-Exporter/io_export_o3d
```

Expected: the source remains ignored and is not included in the repository diff.

- [ ] **Step 5: Record completion state**

Update the session todo `verify-blender-5-port` only after the smoke command and diff inspection succeed. Report any unavailable Blender executable or failing test explicitly instead of claiming completion.
