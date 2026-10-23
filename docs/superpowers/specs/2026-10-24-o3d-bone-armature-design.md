# O3D Bone Armature Design

## Goal

Add Blender armature support for OMSI O3D bone-bearing meshes while preserving
the existing O3D bone-weight format and making newly rigged Blender meshes
exportable back to OMSI.

The first implementation targets the human assets under
`Humans/aXYZ/model`, but the format-facing behavior must also support other
models that use named O3D bone weights.

## Scope

- Create one Blender armature per imported O3D mesh that contains bones.
- Keep the O3D bone names as Blender vertex-group names.
- Build a canonical human hierarchy because O3D stores no parent relationships.
- Estimate bone placement from weighted vertex centroids, with a normalized
  template fallback for missing or degenerate data.
- Add an Armature modifier and parent each imported bone-bearing mesh to its
  generated armature.
- Export vertex groups as O3D bone weights so independently rigged Blender
  models can be used in OMSI.
- Export rest/model-space geometry rather than baking the current armature pose.
- Do not implement OMSI's procedural human runtime, `[links]` pose generation,
  or animation clips.

CFG LOD behavior remains unchanged: each imported LOD mesh receives its own
armature.

## Architecture

O3D parsing remains in `o3d_io/o3dconvert.py`. Its existing bone representation,
`(name, [(vertex_index, weight), ...])`, is the source of truth for imported
weights.

The importer continues to create the mesh and vertex groups, then delegates
armature construction to a focused helper module. The helper:

1. De-duplicates bone names while retaining all valid weights.
2. Creates one armature object and one edit bone per distinct valid name.
3. Applies the canonical parent map for known human names.
4. Places bones from weighted-vertex centroids.
5. Uses a normalized human template scaled to mesh bounds when centroids are
   unavailable or degenerate.
6. Adds an Armature modifier and parents the mesh to the armature.

Unknown bone names remain usable as root or flat bones; they are never inferred
to have a hierarchy from O3D record order.

## Canonical hierarchy

The inferred hierarchy is editor metadata only. It is not serialized to O3D.
The known human relationships are:

- `Main` is the root.
- `Hip` and `Head` are children of `Main`.
- `OA_L` and `OA_R` (upper arms) descend from `Main`.
- `UA_L` and `UA_R` (forearms) descend from the corresponding upper arms.
- `Hand_L` and `Hand_R` descend from the corresponding forearms.
- `OS_L` and `OS_R` (thighs) descend from `Hip`.
- `US_L` and `US_R` (lower legs) descend from the corresponding thighs.

The implementation must make the exact parent map explicit in code and test it;
it must not rely on dictionary or file order.

## Export contract

The exporter treats Blender vertex groups as the portable representation of O3D
bones. A newly rigged model is exportable when its intended bone names are
represented by vertex groups, regardless of whether its armature hierarchy was
inferred by this add-on.

Export behavior:

- Collect non-empty vertex groups as named O3D bones.
- Preserve the vertex-group indices and weights.
- Validate indices and weights before serialization.
- Reject or explicitly report non-finite and negative weights.
- Omit empty groups.
- Select 16-bit or 32-bit weight indices consistently with the O3D header.
- Do not serialize Blender parent relationships because the O3D `0x54`
  section has no hierarchy fields.
- Obtain geometry with armature deformation disabled so a current pose is not
  baked into the exported rest/model-space vertices.
- Preserve the existing rigid-object path for meshes without bone groups.

## Error handling

Malformed bone sections and invalid influences must produce explicit
diagnostics. Safe per-influence recovery is preferred: invalid or out-of-range
influences may be skipped while preserving the rest of the mesh, but the
affected file and reason must be logged. Empty or unsupported names must not be
silently discarded when Blender can represent them.

Armature construction failure must not silently produce a success-shaped
result. The importer should retain the mesh and vertex groups when possible and
report the armature failure clearly.

## Compatibility

Use the repository's existing Blender compatibility helpers and support the
declared Blender 4.2 through 5.2 range. Do not add dependencies.

Imports without O3D bones and exports without bone groups must retain existing
behavior. Bone-bearing imports will additionally create armature objects and
deformation bindings.

## Verification

Extend the Blender smoke coverage with:

1. Import of a stock human O3D from the supplied `aXYZ` assets.
2. Verification of expected named vertex groups and generated bones.
3. Verification of canonical parent relationships.
4. Verification of the Armature modifier and mesh parenting.
5. A pose change that visibly changes the bound mesh.
6. Export of a newly created/rigged mesh and re-import of its O3D bone names
   and weights.
7. Rest-space export while the armature is posed, proving pose geometry is not
   baked into the O3D vertices.
8. Explicit handling of malformed and out-of-range influences.

The existing smoke suite remains the regression baseline.
