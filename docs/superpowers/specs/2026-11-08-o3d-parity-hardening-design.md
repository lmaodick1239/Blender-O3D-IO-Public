# O3D Parity Hardening Design

Date: 2026-11-08

## Goal

Bring the Blender O3D IO construction and codec paths into parity with the confirmed OMSI reader/writer behavior documented in:

- `docs/research/2026-11-08-addon-o3d-construction-audit.md`
- `docs/research/2026-11-08-omsi-original-o3d-vs-addon.md`

The implementation will address confirmed addon defects and traced OMSI 2.2.032 runtime constraints. It will not claim unverified native coordinate, texture-directory, or encryption-formula compatibility.

## Decisions

### Shared codec

`o3dconvert` will validate all representability constraints before writing any bytes:

- Accept public O3D versions `1` through `7`. Import rejects bad magic, truncated headers, and unsupported versions. Version `0` is rejected as addon policy because the public UI/API exposes `1..7`; the native trace specifically establishes rejection above `7`.
- Force short triangle indices for versions below `3`, because those versions have no options byte.
- Reject empty vertex or triangle sections. Blender export will therefore reject empty, edge-only, and modifier-empty meshes before opening their destination.
- Encode material and bone names once as CP1252 and reject unencodable or over-255-byte names. Material validation must happen before an existing destination can be truncated.
- Reject encrypted exports below version `4`, encrypted exports using `0xffffffff`, invalid keys, and encrypted requests when the crypto implementation is unavailable. Pass the serialized vertex count to the encryption routine.
- Continue dispatch after an unknown section byte by default, matching the native one-byte continuation behavior. Add a strict import option that raises with the tag and offset for callers that require complete known-section input. Truncated known sections still raise rather than being treated as successful partial imports.

### Blender import

- Initialize material alpha from embedded diffuse alpha before applying CFG overrides.
- Preserve the raw O3D specular exponent and the importer’s baseline Blender roughness in material custom properties. An unchanged imported material exports the original exponent; an edited material uses the documented addon conversion for editable preview values.
- Create vertex groups using the returned Blender object and maintain a file-bone-index mapping. Generate deterministic Blender-safe names for truncation and collisions, and preserve the original names in mesh metadata for diagnostics/lossless tooling. Armature construction uses the mapped names.
- Treat repeated influence records for a single file bone and vertex using the first record, matching the traced native preparation behavior.
- For a singular or near-singular transform, use an identity object frame and axis-only mesh conversion. Do not use `inverted_safe()` or return a singular object matrix while claiming untransformed import.

### Blender export

- Apply the global export transform in the same order to serialized positions and the stored origin frame. The frame composition follows the mesh operation order (`global_matrix @ axis @ matrix_world @ axis`) before the existing transpose/storage conversion.
- Apply traced OMSI skinning limits whenever serialized bones are present, while allowing wide static meshes. This rejects more than `65535` serialized skinned vertices and dominant exported bone indices `>=128`.
- When an armature modifier supplies the deforming armature, serialize only populated groups whose names match armature bones and log omitted helper groups. For meshes without an armature, retain populated groups because arbitrary group names are valid O3D bone names and no safe filter exists.
- Infer smooth-skin metadata from the exact serialized geometry. Generated CFG output adds one `[smoothskin]` directive when any serialized vertex has multiple positive influences, while preserving `[setbone]` and other custom blocks.
- Mark layered materials at construction time and reject them in ordinary O3D export with a clear error, because one O3D material record cannot represent multiple diffuse/splat layers. This prevents silent layer loss.
- Preserve relative texture subpaths when they are available and safe to express relative to the export root; use the existing basename fallback for external/ambiguous paths. Validate the resulting encoded O3D material name and apply the same path choice to CFG material directives.

## Data flow

1. Geometry preparation produces serialized vertices, triangles, filtered bones, and a `smoothskin` boolean derived from those exact records.
2. Material preparation builds and validates O3D material tuples before opening the destination.
3. Codec preflight validates version, sections, names, encryption, and index widths.
4. The writer emits the validated header and sections.
5. CFG generation receives per-object serialized metadata so it does not recompute skinning from a different source mesh.
6. Import applies codec validation, converts geometry, creates materials/groups, then creates an armature from the mapped group records.

Multi-object CFG export remains non-transactional across separate O3D files; validation will happen for each candidate before that candidate is opened, and existing behavior for already-written earlier candidates is documented by tests where relevant.

## Testing

Add focused codec tests for:

- bad magic, truncated headers, unsupported versions, and version `1/2` default index width;
- unknown-section continuation and strict-mode rejection;
- 255-byte material names, overlong/unencodable names, and preservation of existing destinations;
- empty geometry rejection before writes;
- encrypted round trips across versions, keys, alternate seeds, and vertex counts different from the version, plus invalid combinations and missing-crypto rejection.

Extend Blender smoke coverage for:

- embedded alpha-only import/export;
- specular exponent `32` unchanged when untouched;
- long and colliding imported bone names, first-duplicate influence semantics;
- singular-transform geometry/object-frame behavior;
- translated-object export with global scale;
- generic skinned runtime-limit rejection, helper-group handling, and inferred `[smoothskin]`;
- layered-material rejection and relative texture-name handling.

Existing tests for already-fixed version-3 headers, wide bone influence indices, and character conversion limits remain regression coverage and will be updated only where the new generic runtime policy changes an expectation.

## Non-goals

- Establishing OMSI behavior for versions other than the traced build.
- Proving or replacing the current crypto algebra without native encrypted fixtures.
- Adding extra O3D sections or multiple UV/material channels.
- Baking layered materials automatically.
- Declaring the current coordinate, normal, winding, or native texture-directory convention incorrect without new native evidence.
