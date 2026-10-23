# O3D Bone Armature Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Import OMSI O3D bone weights into usable Blender armatures and export rest-space Blender rigs back to OMSI bone sections.

**Architecture:** Keep `o3dconvert.py` as the O3D format layer and add a focused Blender armature helper that consumes the existing named weight tuples. Wire that helper into O3D import, and make export collect validated vertex groups while disabling armature deformation for geometry extraction. Blender hierarchy is editor metadata; O3D names and weights remain the portable contract.

**Tech Stack:** Python, Blender 4.2–5.2 Python API, `bpy`, `mathutils`, existing Blender smoke harness.

## Global Constraints

- Create one Blender armature per imported O3D mesh that contains bones.
- Keep the O3D bone names as Blender vertex-group names.
- Build a canonical human hierarchy because O3D stores no parent relationships.
- Estimate bone placement from weighted vertex centroids, with a normalized template fallback for missing or degenerate data.
- Add an Armature modifier and parent each imported bone-bearing mesh to its generated armature.
- Export vertex groups as O3D bone weights so independently rigged Blender models can be used in OMSI.
- Export rest/model-space geometry rather than baking the current armature pose.
- Do not implement OMSI's procedural human runtime, `[links]` pose generation, or animation clips.
- Support the declared Blender 4.2 through 5.2 range without new dependencies.
- Preserve existing behavior for imports without O3D bones and exports without bone groups.

---

### Task 1: Build the reusable armature-construction helper

**Files:**
- Create: `o3d_io/o3d_armature.py`
- Test: `tests/smoke_io.py`

**Interfaces:**
- Consumes: `bpy.types.Object`, mesh vertex coordinates, and O3D bone tuples of type `list[tuple[str, list[tuple[int, float]]]]`.
- Produces: `create_armature_for_mesh(mesh_object: bpy.types.Object, bones: list[tuple[str, list[tuple[int, float]]]]) -> bpy.types.Object | None`.
- Produces: explicit module constants for the canonical parent map and template bone directions so tests can inspect stable behavior without depending on O3D file order.

- [ ] **Step 1: Add a failing helper test using a synthetic mesh and named weights**

Add a smoke assertion that creates a small mesh with `Main`, `Hip`, and `Head`
vertex groups, calls `create_armature_for_mesh`, and checks:

```python
armature = addon.o3d_io.o3d_armature.create_armature_for_mesh(
    source,
    [
        ("Main", [(0, 1.0), (1, 0.5)]),
        ("Hip", [(0, 0.5), (2, 1.0)]),
        ("Head", [(1, 1.0)]),
    ],
)
assert armature is not None
assert {bone.name for bone in armature.data.bones} == {"Main", "Hip", "Head"}
assert armature.data.bones["Hip"].parent == armature.data.bones["Main"]
assert armature.data.bones["Head"].parent == armature.data.bones["Main"]
assert source.parent is armature
assert source.modifiers[-1].type == "ARMATURE"
assert source.modifiers[-1].object is armature
```

- [ ] **Step 2: Run the focused smoke test and verify it fails**

Run the repository’s Blender smoke command used by CI, targeting the updated
`smoke_io.py` entry point. Expected result: failure because
`o3d_io.o3d_armature` does not exist.

- [ ] **Step 3: Implement canonical hierarchy and robust influence collection**

In `o3d_io/o3d_armature.py`, define:

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

Merge repeated names by maximum weight for a given vertex, ignore only
out-of-range, non-finite, or negative influences with an explicit log message,
and retain unknown names as root bones. Use weighted centroids for heads and
derive tails from the child centroid or a non-zero template direction. Ensure
every edit bone has a non-zero length even when its group has no usable
vertices.

- [ ] **Step 4: Implement armature creation and binding**

Create an armature data block and object, link it to the mesh’s collection,
create edit bones, assign explicit parents after all bones exist, exit edit
mode, parent the mesh to the armature, and add an Armature modifier pointing
to the armature. Return the armature object. Return `None` only when the input
contains no usable bone names, and log construction failures rather than
silently swallowing them.

- [ ] **Step 5: Run the focused smoke test and verify it passes**

Run the same Blender smoke selector. Expected result: the synthetic armature,
canonical parents, parenting, and modifier assertions pass.

- [ ] **Step 6: Commit the helper**

```bash
git add o3d_io/o3d_armature.py tests/smoke_io.py
git commit -m "feat: build armatures from O3D bones"
```

### Task 2: Wire armatures into O3D import

**Files:**
- Modify: `o3d_io/io_o3d_import.py:197-202` and import setup near the module imports
- Test: `tests/smoke_io.py`

**Interfaces:**
- Consumes: `o3d_armature.create_armature_for_mesh` from Task 1 and the parsed
  `o3d[4]` bone tuples returned by `load_o3d`.
- Produces: bone-bearing imported O3D objects with generated armatures, while
  mesh-only O3D objects retain their existing behavior.

- [ ] **Step 1: Add a failing real-asset import assertion**

Add a smoke test that imports
`/mnt/More_Games/openOMSI-0.1.78-linux-x64/Humans/aXYZ/model/man01.o3d`
with `do_import`, locates the new mesh object and its armature, and asserts the
13 expected names:

```python
expected = {
    "Hip", "Head", "OA_R", "UA_L", "Hand_R", "OS_R", "Hand_L",
    "US_L", "OS_L", "US_R", "OA_L", "UA_R", "Main",
}
assert {bone.name for bone in armature.data.bones} == expected
assert {group.name for group in mesh_object.vertex_groups} == expected
```

Also assert that importing a known mesh without bones still returns only its
mesh object and does not create an armature.

- [ ] **Step 2: Run the focused test and verify it fails**

Run the Blender smoke selector for the new assertion. Expected result: the
imported mesh has vertex groups but no generated armature.

- [ ] **Step 3: Wire the helper after vertex groups are populated**

Import `o3d_armature` and call:

```python
if o3d[4]:
    o3d_armature.create_armature_for_mesh(blender_obj, o3d[4])
```

Call it after all vertex groups are created and before the object is selected
for the completed import result. Preserve the existing returned object list and
LOD collection logic.

- [ ] **Step 4: Add explicit import diagnostics**

Ensure invalid influences are logged with the O3D path, bone name, vertex index,
and reason. If armature construction fails, leave the imported mesh and groups
available, log the failure, and do not report that an armature was created.

- [ ] **Step 5: Run focused import tests and the existing smoke suite**

Run the real-asset bone test and then the complete configured Blender smoke
suite. Expected result: generated armatures pass and all existing import,
material, path, and regression checks remain green.

- [ ] **Step 6: Commit importer integration**

```bash
git add o3d_io/io_o3d_import.py tests/smoke_io.py
git commit -m "feat: attach armatures during O3D import"
```

### Task 3: Make bone export rest-space and validation aware

**Files:**
- Modify: `o3d_io/io_o3d_export.py:20-120`
- Test: `tests/smoke_io.py`

**Interfaces:**
- Consumes: Blender mesh objects with vertex groups and optional Armature
  modifiers.
- Produces: validated `list[tuple[str, list[tuple[int, float]]]]` passed to
  `o3dconvert.export_o3d`, with rest-space geometry and correct index width.

- [ ] **Step 1: Add a failing export test for a posed rig**

Create a triangle mesh with a `Main` vertex group and an armature modifier,
pose the armature by rotating its edit/pose bone, export it, parse the written
O3D, and compare the exported vertex positions against the unposed source
mesh. Also assert that the parsed bone list contains `Main` and its weights.

Add a second test with a mesh that has no material and no bone groups to ensure
the existing default-material path remains unchanged.

- [ ] **Step 2: Run the focused export test and verify it fails**

Run the Blender smoke selector. Expected result: the current exporter evaluates
the armature modifier and exports posed geometry.

- [ ] **Step 3: Separate rest-space geometry from source vertex groups**

In `do_export`, detect Armature modifiers and create the export mesh without
their deformation applied. Keep the existing evaluated path for non-armature
modifiers and preserve object/world/global transforms. Do not mutate the
original Blender mesh or permanently disable modifiers.

- [ ] **Step 4: Validate and collect export influences**

Replace the broad exception around `v_group.weight(index)` with an explicit
collector that:

```python
def collect_o3d_bones(
    blender_obj: bpy.types.Object,
    vertex_count: int,
) -> list[tuple[str, list[tuple[int, float]]]]:
    ...
```

For each group, retain finite weights greater than or equal to zero, reject
out-of-range indices, omit empty groups, and log the object/group/reason for
skipped data. Preserve the existing group order for stable output.

- [ ] **Step 5: Select long indices consistently**

Before serialization, ensure a version-3-or-later export uses long indices when
the mesh or any bone influence needs an index above `65535`. Reject the
combination of version below 3 and indices above `65535` with an explicit
export error rather than truncating. Pass the same choice to triangle and bone
serialization.

- [ ] **Step 6: Run focused export tests and the existing smoke suite**

Verify that posed armatures export rest geometry, re-imported bones preserve
names and weights, invalid influences are diagnosed, and existing round-trip
tests remain green.

- [ ] **Step 7: Commit export support**

```bash
git add o3d_io/io_o3d_export.py tests/smoke_io.py
git commit -m "feat: export validated rest-space O3D bones"
```

### Task 4: Document and run final compatibility verification

**Files:**
- Modify: `README.md` bone/feature documentation section
- Modify: `README-FR.md` corresponding bone/feature documentation section
- Test: `tests/smoke_io.py`

**Interfaces:**
- Consumes: completed importer and exporter behavior from Tasks 1–3.
- Produces: user-facing instructions for importing, posing, and exporting
  bone-bearing models plus final verified behavior.

- [ ] **Step 1: Document the user workflow**

Explain that imported bone-bearing O3D meshes receive per-mesh armatures,
Blender hierarchy is inferred for editing, O3D export serializes named vertex
groups rather than hierarchy, and exports use rest/model-space geometry.
Mention that independently rigged models export when their vertex groups use
the intended OMSI bone names.

- [ ] **Step 2: Run the complete supported smoke matrix**

Run the repository’s configured smoke command against Blender 4.2, 5.0, and
5.2 when those interpreters are available. The expected result is a passing
baseline with the new real-human import, pose, rest-export, re-import, and
malformed-influence assertions.

- [ ] **Step 3: Inspect the final diff**

Run:

```bash
git --no-pager diff --check HEAD~3..HEAD
git --no-pager status --short
```

Confirm that only the planned armature helper, importer/exporter changes,
tests, and directly related documentation are present.

- [ ] **Step 4: Commit documentation and final tests**

```bash
git add README.md README-FR.md tests/smoke_io.py
git commit -m "docs: describe OMSI bone rig workflow"
```
