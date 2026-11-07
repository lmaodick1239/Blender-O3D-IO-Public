# O3D Bone Armature Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Import OMSI O3D bone weights into usable Blender armatures and export independently rigged Blender meshes back to OMSI without baking the current armature pose.

**Architecture:** Keep `o3dconvert.py` as the binary O3D layer and preserve its named bone tuple representation. Add a focused `o3d_armature.py` helper for Blender hierarchy, placement, validation, parenting, and modifier binding; keep import/export orchestration in `io_o3d_import.py` and `io_o3d_export.py`. Export vertex groups after final O3D vertex construction, while obtaining geometry with armature deformation disabled.

**Tech Stack:** Python, Blender `bpy` and `mathutils`, existing `blender_compat.py` helpers, and the repository’s background Blender smoke harness.

## Global Constraints

- Create one Blender armature per imported O3D mesh that contains bones.
- Keep the O3D bone names as Blender vertex-group names.
- Build a canonical human hierarchy because O3D stores no parent relationships.
- Estimate bone placement from weighted vertex centroids, with a normalized human template fallback for missing or degenerate data.
- Add an Armature modifier and parent each imported bone-bearing mesh to its generated armature.
- Export vertex groups as O3D bone weights so independently rigged Blender models can be used in OMSI.
- Export rest/model-space geometry rather than baking the current armature pose.
- Do not implement OMSI procedural human runtime, `[links]` pose generation, or animation clips.
- Support the declared Blender 4.2 through 5.2 range without new dependencies.
- Preserve existing behavior for imports without O3D bones and exports without valid bone groups.
- Do not modify `README.md` or `README-FR.md`.
- Do not serialize Blender armature hierarchy because O3D section `0x54` contains names and weights only.

---

## File Map

- Create `o3d_io/o3d_armature.py`: Blender armature construction, canonical parent map, template placement, and influence normalization.
- Modify `o3d_io/io_o3d_import.py`: validate/import vertex groups and invoke armature construction per bone-bearing mesh.
- Modify `o3d_io/io_o3d_export.py`: preserve source-to-export vertex mapping, collect validated groups, extract rest-space geometry, and choose index width.
- Modify `o3d_io/o3dconvert.py`: make `0x54` bone count/index-width serialization match the documented format and reject unrepresentable values.
- Modify `tests/smoke_io.py`: add synthetic armature, malformed influence, posed export, round-trip, and index-width checks.
- Modify `tests/blender_smoke.py`: register the new smoke checks in the existing suite.

## Verification Commands

Run the complete suite with the Blender executable under test:

```bash
blender --background --factory-startup --python tests/blender_smoke.py
```

The command must print `BLENDER_O3D_IO_SMOKE_OK`. Run it with Blender 4.2, 5.0, and 5.2 where those interpreters are available. Use `git diff --check` after implementation.

### Task 1: Add the armature helper and synthetic coverage

**Files:**
- Create: `o3d_io/o3d_armature.py`
- Modify: `tests/smoke_io.py`
- Modify: `tests/blender_smoke.py`

**Interfaces:**
- Consumes `bpy.types.Object` and `list[tuple[str, list[tuple[int, float]]]]` O3D bone records.
- Produces `create_armature_for_mesh(mesh_object: bpy.types.Object, bones: list[tuple[str, list[tuple[int, float]]]]) -> bpy.types.Object | None`.
- Exposes `CANONICAL_PARENTS` for test inspection.
- Logs invalid influences and returns `None` only when no usable bone names remain.

- [ ] **Step 1: Add a failing synthetic smoke check**

Add `assert_armature_helper(addon)` to `tests/smoke_io.py`. Create the test mesh inline with four non-collinear vertices and call the helper with repeated names and weights:

```python
mesh = bpy.data.meshes.new("O3D Armature Source Mesh")
mesh.from_pydata([(0, 0, 0), (0, 0, 1), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
source = bpy.data.objects.new("O3D Armature Source", mesh)
bpy.context.scene.collection.objects.link(source)
armature = addon.o3d_io.o3d_armature.create_armature_for_mesh(
    source,
    [
        ("Main", [(0, 1.0), (1, 0.5)]),
        ("Hip", [(0, 0.5), (2, 1.0)]),
        ("Head", [(1, 1.0)]),
        ("Hip", [(2, 0.25)]),
    ],
)
assert armature is not None
assert {bone.name for bone in armature.data.bones} == {"Main", "Hip", "Head"}
assert armature.data.bones["Hip"].parent == armature.data.bones["Main"]
assert armature.data.bones["Head"].parent == armature.data.bones["Main"]
assert source.parent is armature
assert source.modifiers[-1].type == "ARMATURE"
assert source.modifiers[-1].object is armature
assert all(bone.length > 0.0 for bone in armature.data.bones)
```

Remove the source object and armature after assertions so the smoke scene stays isolated.

- [ ] **Step 2: Run the smoke test and confirm the new check fails**

Run:

```bash
blender --background --factory-startup --python tests/blender_smoke.py
```

Expected failure: `o3d_io.o3d_armature` is not available or `create_armature_for_mesh` is undefined.

- [ ] **Step 3: Implement explicit hierarchy and influence normalization**

Create `o3d_io/o3d_armature.py` with these exact parent relationships:

```python
CANONICAL_PARENTS = {
    "Hip": "Main",
    "Head": "Main",
    "OA_L": "Main",
    "OA_R": "Main",
    "UA_L": "OA_L",
    "UA_R": "OA_R",
    "Hand_L": "UA_L",
    "Hand_R": "UA_R",
    "OS_L": "Hip",
    "OS_R": "Hip",
    "US_L": "OS_L",
    "US_R": "OS_R",
}
```

Normalize records by name while preserving first-seen bone order. For repeated `(bone_name, vertex_index)` entries, retain the maximum valid weight. Skip and log weights when the index is outside `0 <= index < len(mesh.data.vertices)`, the weight is not finite, or the weight is negative. Keep zero weights out of centroid calculations but permit a named group to exist if its name is non-empty. Do not infer parents from input order. Unknown names remain root bones.

- [ ] **Step 4: Implement centroid, template, and edit-bone creation**

Use mesh-local vertex coordinates. For each bone with usable positive weights, calculate the weighted centroid. Use a normalized human template direction/position for missing or degenerate centroids, scaling the template by the mesh bounding-box diagonal with a minimum scale of `0.001`. Place each head at its centroid or fallback point. Use the child centroid as a tail when a canonical child exists and is distinct; otherwise use a non-zero template direction. Ensure every edit bone has a strictly positive length.

Create an armature data block and object, link the armature to the first collection used by the mesh (or the scene collection if none exists), create all edit bones, assign parent pointers in a second pass, exit edit mode, set `mesh_object.parent = armature_object`, and append an Armature modifier targeting the new object. Catch construction failures, log the mesh name and exception, and return `None` without deleting the mesh or its vertex groups.

- [ ] **Step 5: Run the synthetic check and confirm it passes**

Run the same Blender smoke command. Expected result: the synthetic bones, parent map, non-zero lengths, mesh parenting, and modifier assertions pass.

- [ ] **Step 6: Commit the helper and test**

```bash
git add o3d_io/o3d_armature.py tests/smoke_io.py tests/blender_smoke.py
git commit -m "feat: build armatures from O3D bones"
```

### Task 2: Integrate validated bone import

**Files:**
- Modify: `o3d_io/io_o3d_import.py:17-18,197-202`
- Modify: `tests/smoke_io.py`

**Interfaces:**
- Consumes parsed `o3d[4]` bone records from `load_o3d`.
- Produces named Blender vertex groups and, when records are present, a generated armature per mesh object.

- [ ] **Step 1: Add a failing importer integration check**

Add `assert_imported_bone_armature(addon)` as an isolated importer integration check. Temporarily replace `io_o3d_import.load_o3d` with a test stub returning a synthetic Blender mesh plus `Main`, `Hip`, and `Head` bone tuples, call `do_import` using a temporary placeholder `.o3d` path, then restore the original loader in `finally`. Assert the result contains the mesh and generated armature, the same group names, canonical parent relationships, mesh parenting, and an Armature modifier. Also assert that the existing material-only import path does not create an armature. Do not rely on exporting/re-importing an O3D file here; binary bone round trips depend on the `o3dconvert.py` fixes in Task 5 and are verified in Task 6.

Add an optional stock-human check that reads the asset path from `O3D_HUMAN_ASSET` and explicitly logs/skips when unset or missing. When present, import it and assert the 13 names from the design spec: `Hip`, `Head`, `OA_R`, `UA_L`, `Hand_R`, `OS_R`, `Hand_L`, `US_L`, `OS_L`, `US_R`, `OA_L`, `UA_R`, and `Main`.

- [ ] **Step 2: Run the focused check and confirm it fails**

Run the smoke command. Expected failure: imported groups exist but no armature object is generated.

- [ ] **Step 3: Add import diagnostics and helper invocation**

Import `.o3d_armature`. Before adding each parsed influence, validate its vertex index and weight and log `[O3D_Import]`, source path, bone name, index, and reason for skipped data. Preserve the group name when Blender can represent it; do not silently discard an empty or unknown name. After all groups are created, call:

```python
if o3d[4]:
    o3d_armature.create_armature_for_mesh(blender_obj, o3d[4])
```

If the helper reports construction failure, keep the mesh and groups in the returned object list and log that no armature was created. Do not alter LOD collection selection or the `blender_objs` result contract.

- [ ] **Step 4: Run focused and full import checks**

Run the complete smoke command. Verify generated armatures for bone-bearing sources, no armatures for mesh-only sources, and unchanged material/path/LOD checks.

- [ ] **Step 5: Commit importer integration**

```bash
git add o3d_io/io_o3d_import.py tests/smoke_io.py
git commit -m "feat: attach armatures during O3D import"
```

### Task 3: Add validated export bone collection and source-index mapping

**Files:**
- Modify: `o3d_io/io_o3d_export.py:32-121`
- Modify: `tests/smoke_io.py`

**Interfaces:**
- Add `collect_o3d_bones(blender_obj: bpy.types.Object, source_vertex_count: int, source_to_export: dict[int, list[int]]) -> list[tuple[str, list[tuple[int, float]]]]`.
- The returned indices refer to the final `verts` array, not the original Blender mesh vertex array.

- [ ] **Step 1: Add a failing weight round-trip check**

Create a mesh with a UV seam that causes exported vertex duplication and assign one group to the source vertex shared by both seam vertices. Export and parse the O3D bytes. Assert the group is non-empty and contains each generated export index corresponding to the source vertex. Add a second group with no assignments and assert it is omitted.

- [ ] **Step 2: Run the check and confirm the current exporter fails**

Run the smoke command. Expected failure: the current exporter queries group weights using generated indices, may emit empty groups, and can lose or misassign weights after seam duplication.

- [ ] **Step 3: Implement validated collection**

Build `source_to_export` while constructing `verts`: whenever a source Blender vertex becomes a new exported vertex, append the exported index to that source vertex’s list; when an existing exported vertex is reused, append the index as well. For each vertex group, query weights against the source vertex count, then copy each valid weight to every corresponding exported vertex index. Retain finite weights `>= 0.0`, skip out-of-range source indices, and log object/group/index/reason for invalid data. Omit groups with no retained influences and preserve Blender group order.

- [ ] **Step 4: Replace the broad exception path and run the check**

Call `collect_o3d_bones` from `export_mesh` after final vertex construction and pass its result to `o3dconvert.export_o3d`. Run the smoke command and verify seam weights and empty-group omission.

- [ ] **Step 5: Commit the collector**

```bash
git add o3d_io/io_o3d_export.py tests/smoke_io.py
git commit -m "fix: validate and map exported O3D weights"
```

### Task 4: Export rest-space geometry while preserving other modifiers

**Files:**
- Modify: `o3d_io/io_o3d_export.py:124-215`
- Modify: `tests/smoke_io.py`

**Interfaces:**
- `do_export` continues accepting the existing arguments and returns the existing result.
- `export_mesh` receives a mesh snapshot whose coordinates are rest/model-space when an Armature modifier is present.

- [ ] **Step 1: Add a failing posed-rig export test**

Create a two-bone armature and a mesh with a group bound to the child bone. Record the source rest vertex positions, pose the child bone by a visible rotation, export the mesh, parse the O3D vertices, and assert the current output differs from the recorded rest positions. Then add the intended assertion that output positions match the rest-space expectation; this assertion must fail before the fix.

- [ ] **Step 2: Implement non-destructive armature exclusion**

In `do_export`, inspect the source object’s modifiers before obtaining the evaluated mesh. For objects with an Armature modifier, temporarily disable only those modifiers for viewport/render evaluation, obtain the evaluated mesh, then restore every modifier’s prior state in a `finally` block. Do not mutate the source mesh data, pose, parenting, or modifier order. Keep non-armature modifiers evaluated as before. Continue applying object/world/global transforms to the temporary mesh only.

- [ ] **Step 3: Run posed export verification**

Run the smoke command. Verify a posed mesh exports the rest-space coordinates, while the generated Armature modifier and source pose remain intact after export.

- [ ] **Step 4: Commit rest-space export**

```bash
git add o3d_io/io_o3d_export.py tests/smoke_io.py
git commit -m "fix: export armature meshes from rest space"
```

### Task 5: Correct O3D index-width selection and binary validation

**Files:**
- Modify: `o3d_io/io_o3d_export.py:116-121`
- Modify: `o3d_io/o3dconvert.py:273-352,366-403`
- Modify: `tests/smoke_io.py`

**Interfaces:**
- `o3dconvert.export_o3d` keeps its current arguments and uses `long_triangle_indices` for both triangle indices and `0x54` weight vertex indices.
- Bone count remains serialized as `u16` in section `0x54`, including version 3+.

- [ ] **Step 1: Add failing index-width tests**

Add a direct binary test for a normal version-7 mesh and assert header flag bit 0 is clear when all triangle and bone indices fit in `u16`. Add a synthetic large-index case that requires bit 0 and assert the serialized weight record uses four-byte vertex indices. Add a version-2 case requiring an index above `65535` and assert export raises a clear `ValueError` instead of truncating.

- [ ] **Step 2: Implement one width decision in the exporter**

After final `verts`, triangles, and bones are known, compute `max_triangle_or_weight_index`. Set `long_triangle_indices = max_index > 65535`. Reject `o3d_version < 3 and long_triangle_indices` with an error naming the version and maximum index. Pass the same boolean to `o3dconvert.export_o3d`; do not always pass `False`.

- [ ] **Step 3: Validate serializer bounds**

In `o3dconvert.py`, validate that the bone count and each weight count fit `u16`, names fit the one-byte length-prefixed encoding, indices are non-negative integers, and weights are finite and non-negative. Use `u16` bone counts for the `0x54` section regardless of long headers. Raise `ValueError` with the affected bone or record details when a value cannot be represented.

- [ ] **Step 4: Run binary and regression checks**

Run the smoke command. Verify version/header flags, 16-bit and 32-bit round trips, malformed-value errors, and all existing material/path tests.

- [ ] **Step 5: Commit format-layer changes**

```bash
git add o3d_io/io_o3d_export.py o3d_io/o3dconvert.py tests/smoke_io.py
git commit -m "fix: select O3D bone index width consistently"
```

### Task 6: Add end-to-end pose and re-import verification

**Files:**
- Modify: `tests/smoke_io.py`
- Modify: `tests/blender_smoke.py`

**Interfaces:**
- Uses the completed importer/exporter/helper behavior without adding production APIs.

- [ ] **Step 1: Add visible pose deformation coverage**

Import or construct a mesh with a child-bone group, record a bound vertex coordinate, rotate the child pose bone in pose mode, update the dependency graph, and assert the evaluated mesh coordinate changes by more than `1e-5`. Restore/delete the test objects afterward.

- [ ] **Step 2: Add export/re-import weight verification**

Export the posed rig, parse it with `o3dconvert.import_o3d`, assert the expected named bones are present, assert every weight index is within the parsed vertex count, and assert the expected weights survive within `1e-6`. Delete the source and re-import the file through `do_import`; verify group names and generated armature names.

- [ ] **Step 3: Add explicit malformed-input recovery coverage**

Call the armature helper and exporter collector with duplicate names, duplicate indices, negative values, `float("nan")`, `float("inf")`, and out-of-range indices. Assert valid influences remain, invalid influences do not serialize, empty groups are omitted, and the helper does not fail solely because one influence is malformed.

- [ ] **Step 4: Register checks and run the full suite**

Add the checks to `CHECKS` in `tests/blender_smoke.py` in dependency order after existing low-level guards and before the final broad round trip. Run Blender 4.2, 5.0, and 5.2 where available. The expected terminal marker is `BLENDER_O3D_IO_SMOKE_OK` for every supported interpreter.

- [ ] **Step 5: Commit end-to-end coverage**

```bash
git add tests/smoke_io.py tests/blender_smoke.py
git commit -m "test: cover O3D armature round trips"
```

### Task 7: Final review and compatibility verification

**Files:**
- Inspect all changed files; do not modify README files.

- [ ] **Step 1: Run formatting and repository checks**

Run:

```bash
git diff --check
git status --short
```

Confirm no generated Blender files, smoke logs, temporary O3D files, or `.gitignorefolder` contents were added.

- [ ] **Step 2: Run the complete Blender matrix**

Run `tests/blender_smoke.py` with Blender 4.2, 5.0, and 5.2. Record any unavailable interpreter explicitly; available interpreters must print `BLENDER_O3D_IO_SMOKE_OK`.

- [ ] **Step 3: Verify requirement coverage**

Confirm the final diff covers canonical hierarchy, centroid/template placement, per-mesh armatures including LOD meshes, import diagnostics, validated export groups, rest-space export, index-width consistency, malformed influence recovery, pose deformation, re-import, and unchanged mesh-only behavior.

- [ ] **Step 4: Inspect the final diff for scope**

Run:

```bash
git --no-pager diff --stat
git --no-pager diff -- o3d_io/o3d_armature.py o3d_io/io_o3d_import.py o3d_io/io_o3d_export.py o3d_io/o3dconvert.py tests/smoke_io.py tests/blender_smoke.py
```

Ensure no README changes or unrelated refactors are present.
