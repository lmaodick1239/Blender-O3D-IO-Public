# Blender O3D IO: current bone implementation, static analysis

Date: 2026-11-07. Repository HEAD at inspection: `e5ec06c6157924ae553dfeb1777e9d19de588195`.

## Scope and evidence

Read-only analysis of the current addon source, its Blender smoke tests, and the bone design/implementation documents. This report is the only file created by this analysis. No Blender, OMSI, smoke tests, binary fixtures, or decompiled executable were run or inspected. The existing dirty nested exporter checkout was excluded from implementation claims; the production paths examined are the root addon and its `o3d_io` package.

Claims below describe what this addon reads/writes and does in Blender. They do **not** establish what the OMSI executable requires, recognizes, or does at runtime. Source links are repository-relative and include line ranges. Design documents establish intent only; executable source takes precedence.

## Main findings

1. The implemented O3D bone payload is a list of **names and vertex influences**, not a serialized skeleton: there are no parent indices, per-bone bind/rest transforms, joint positions, rotation limits, or animation channels in the implemented bone reader/writer. The only matrix section implemented here is one mesh/object transform. [Binary reader](../../o3d_io/o3dconvert.py#L74-L88), [bone-list reader](../../o3d_io/o3dconvert.py#L149-L175), [section dispatch](../../o3d_io/o3dconvert.py#L201-L236), [bone writer](../../o3d_io/o3dconvert.py#L273-L310), [list/matrix writer](../../o3d_io/o3dconvert.py#L372-L399).
2. Bone names are **not restricted to the 13 human names**. All nonempty names flow into vertex-group creation and generated edit bones. Human names have hardcoded parent/template metadata; unknown names remain unparented unless the caller subsequently edits them. Export serializes every populated vertex group, without requiring a same-name Blender bone or even an armature. [Importer](../../o3d_io/io_o3d_import.py#L197-L237), [helper input/creation](../../o3d_io/o3d_armature.py#L49-L100), [parenting](../../o3d_io/o3d_armature.py#L117-L145), [export collector](../../o3d_io/io_o3d_export.py#L32-L70).
3. The generated Blender rig is an **estimate**: head positions come from weighted mesh-local centroids or a template; tails and parents are inferred from the canonical map. Blender hierarchy and edit-bone geometry are not read back for export. [Placement](../../o3d_io/o3d_armature.py#L74-L100), [bone construction](../../o3d_io/o3d_armature.py#L117-L145), [export collector](../../o3d_io/io_o3d_export.py#L32-L70).
4. Export disables Armature modifiers while extracting geometry, restores their prior flags in `finally`, and writes names/weights. It does not serialize a pose, keyframes, or Blender actions. Unknown CFG commands have a separate text-preservation path, which must not be confused with executing or converting animation. [Evaluation/restoration](../../o3d_io/io_o3d_export.py#L225-L255), [export/finally](../../o3d_io/io_o3d_export.py#L301-L319), [CFG preservation](../../o3d_io/o3d_cfg_parser.py#L436-L467).

## 1. Binary parse/write contract

All `struct` formats use `<`, i.e. little-endian with explicit standard sizes. The implemented section layout is:

| Field | Encoding and behavior | Evidence |
| --- | --- | --- |
| Bone section identifier | One byte `0x54`; writer omits the entire section if the list is empty | [reader dispatch](../../o3d_io/o3dconvert.py#L219-L223), [writer](../../o3d_io/o3dconvert.py#L372-L385) |
| Bone count | `u16` in the actual top-level reader and writer, even for long-header files | [reader forces `l_header=False`](../../o3d_io/o3dconvert.py#L219-L220), [list reader](../../o3d_io/o3dconvert.py#L149-L155), [writer](../../o3d_io/o3dconvert.py#L376-L385) |
| Per-bone name | One-byte length followed by that many CP1252 bytes, decoded/encoded through a Python Pascal-string format; not a null-terminated name | [reader](../../o3d_io/o3dconvert.py#L75-L79), [writer](../../o3d_io/o3dconvert.py#L273-L284) |
| Per-bone influence count | `u16` | [reader](../../o3d_io/o3dconvert.py#L81-L84), [writer](../../o3d_io/o3dconvert.py#L286-L293) |
| Influence | `(u16 vertex index, float32 weight)` = 6 bytes, or `(u32 vertex index, float32 weight)` = 8 bytes | [reader](../../o3d_io/o3dconvert.py#L84-L86), [writer](../../o3d_io/o3dconvert.py#L295-L310) |
| Index-width selector | Extended-header option bit 0 selects both triangle indices and bone weight indices; this is separate from long section-count headers | [header parsing](../../o3d_io/o3dconvert.py#L178-L194), [dispatch](../../o3d_io/o3dconvert.py#L213-L220), [header writing](../../o3d_io/o3dconvert.py#L409-L418) |
| Object transform | Separate `0x79` section with sixteen float32 values, not a per-bone transform | [reader](../../o3d_io/o3dconvert.py#L166-L175), [dispatch](../../o3d_io/o3dconvert.py#L222-L223), [writer](../../o3d_io/o3dconvert.py#L391-L399) |

The parsed in-memory representation is `(name, [(vertex_index, weight), ...])`; the top-level return puts the bone list at tuple position 4 and the transform at position 5. Repeated records are returned as records; the binary layer does not deduplicate or normalize them. [Reader](../../o3d_io/o3dconvert.py#L74-L88), [list construction](../../o3d_io/o3dconvert.py#L157-L163), [return](../../o3d_io/o3dconvert.py#L236).

### Limits and validation

- Writer limits: at most **65,535 bone records**, **65,535 influences per bone**, and **255 CP1252-encoded name bytes**. CP1252 encoding is strict on export; an unencodable Blender name raises an encoding exception rather than using a fallback encoding. [Name/influence checks](../../o3d_io/o3dconvert.py#L276-L293), [bone count check](../../o3d_io/o3dconvert.py#L376-L385).
- The writer accepts nonnegative integer indices and finite nonnegative numeric weights. It does **not** enforce weights `<= 1`, normalize across bones, cap bones affecting a vertex, verify indices against the vertex-list length, or explicitly check the upper bound for the chosen index width. The eventual `<Hf`/`<If` packing provides representation bounds, not a custom upper-bound diagnostic. [Validation/writing](../../o3d_io/o3dconvert.py#L295-L310), [packing callback](../../o3d_io/o3dconvert.py#L405-L407).
- The parser uses counts and `unpack_from` directly; the bone functions have no explicit truncation, index-range, finite-weight, duplicate-name, or duplicate-index checks. Blender import performs some influence validation later. Unknown section identifiers log and stop the top-level parse rather than being preserved. [Bone parser](../../o3d_io/o3dconvert.py#L74-L88), [list parser](../../o3d_io/o3dconvert.py#L149-L163), [unknown-section handling](../../o3d_io/o3dconvert.py#L206-L226), [Blender validation](../../o3d_io/io_o3d_import.py#L211-L229).
- Public-release encryption support is conditional: without the private crypto module, vertex decryption/encryption functions are pass-through stubs and a warning is printed. Encrypted mesh positions, and thus centroid placement derived from them, cannot be assumed correct in that configuration. [Fallback functions](../../o3d_io/o3dconvert.py#L13-L29), [vertex decryption call](../../o3d_io/o3dconvert.py#L100-L110).

### Version boundary discrepancy

The Blender exporter selects wide indices when the maximum final triangle or bone index exceeds 65,535, but rejects them only for `o3d_version < 3`. The binary header writer and reader expose the option bit only for `version > 3`. Consequently, the **version-3 wide-index path has a static inconsistency**: the writer can emit wide records without an extended-header bit that its own reader uses to recognize them. This is an internal source finding, not a claim about OMSI's official version specification. The UI permits versions 1–7, default 7. [Width selection and guard](../../o3d_io/io_o3d_export.py#L161-L182), [header writer](../../o3d_io/o3dconvert.py#L409-L426), [header reader](../../o3d_io/o3dconvert.py#L178-L194), [UI](../../__init__.py#L227-L239).

## 2. Blender import and synthesized skeleton

### Mesh transforms first

The importer creates the mesh, swaps Y and Z using a matrix `C`, transposes the stored object matrix, computes `M = C @ stored_matrix_transposed @ C`, and applies `M.inverted() @ C` to mesh geometry (using `inverted_safe()` for determinant zero). It assigns `M` to the mesh object's `matrix_basis`. Bone/group generation happens afterward, so centroids use the already transformed **mesh-local** coordinates. [Mesh construction/transforms](../../o3d_io/io_o3d_import.py#L407-L457), [object basis](../../o3d_io/io_o3d_import.py#L165-L178), [bone generation ordering](../../o3d_io/io_o3d_import.py#L195-L237).

### Groups and influence handling

For each parsed nonempty name, the importer requests a new Blender vertex group, skips indices outside the mesh's range, skips weights that are nonnumeric, nonfinite, or negative, and adds surviving assignments using `REPLACE`. Zero weights pass the explicit validation. There is no sum-to-one pass or explicit `<= 1` check. The code delegates actual group storage behavior to Blender. [Group import](../../o3d_io/io_o3d_import.py#L197-L229).

The helper separately merges records by exact name; for repeated `(name, index)` entries it retains the **maximum** valid weight. This dictionary is used to estimate bone locations; it is not written back into the mesh's vertex groups. Empty names are skipped. Nonempty names with zero/all-invalid influences still enter the dictionary and can produce fallback bones. [Normalization](../../o3d_io/o3d_armature.py#L49-L72), [centroid/fallback](../../o3d_io/o3d_armature.py#L84-L100).

**Preservation caveat:** duplicate source names take two different paths. Group import calls `vertex_groups.new(name=...)` for every record but then fetches `vertex_groups[bone_name]` to assign weights; it neither uses the returned group nor implements the helper's max merge. Thus duplicate group-name disambiguation and assignment can diverge from the helper's single synthesized bone per exact name. No source-level reconciliation or original-name/byte mapping exists in these paths. Long-name truncation, Blender name disambiguation, undefined CP1252-byte `backslashreplace` decoding, or later Blender renaming therefore preclude a blanket byte-for-byte name-preservation claim. Exact runtime effects were not tested. [Group creation/lookup](../../o3d_io/io_o3d_import.py#L198-L229), [helper deduplication](../../o3d_io/o3d_armature.py#L49-L69), [decode fallback](../../o3d_io/o3dconvert.py#L75-L79), [export takes group name](../../o3d_io/io_o3d_export.py#L66-L68). The smoke source itself notes Blender's name-length limitation but does not test imported 255-byte names: [validation test](../../tests/smoke_io.py#L850-L880).

### Hardcoded names versus arbitrary names

The exact hardcoded parent map is:

| Child | Parent |
| --- | --- |
| `Hip`, `Head`, `OA_L`, `OA_R` | `Main` |
| `UA_L` / `UA_R` | `OA_L` / `OA_R` |
| `Hand_L` / `Hand_R` | `UA_L` / `UA_R` |
| `OS_L`, `OS_R` | `Hip` |
| `US_L` / `US_R` | `OS_L` / `OS_R` |

`Main` has no assigned parent. A parent relationship is applied only when both names exist. No missing canonical bones are inserted, and input order is not interpreted as hierarchy. Unknown names receive bones but no parent from this map. The same 13 names have hardcoded normalized template positions; unknown names use `(0, 0, 0.5)`. [Map/template](../../o3d_io/o3d_armature.py#L8-L37), [fallback](../../o3d_io/o3d_armature.py#L95-L100), [all-name creation and conditional parents](../../o3d_io/o3d_armature.py#L117-L141).

### Placement, binding, and limits

- Mesh scale is the bounding-box diagonal, clamped to `0.001`; fallback positions are `bounds_center + template * scale`. Heads otherwise use the centroid of positive-weight influences. The helper's variable named `normalized` denotes deduplication/validation, not cross-bone weight normalization. [Bounds and centroids](../../o3d_io/o3d_armature.py#L49-L100).
- A tail uses the first eligible canonical child with a positive-weight centroid distinct from the head. Otherwise it follows the template direction at length `max(scale * 0.1, 0.001)`; a final guard ensures nonzero length. This is inferred editor geometry, not recovered bind-pose data. [Tail selection](../../o3d_io/o3d_armature.py#L117-L136).
- One armature object is created per helper call, linked to the mesh's first collection, then set as mesh parent and Armature-modifier target. No pose constraints, joint limits, IK, custom roll, explicit bone connectivity, or animation data are configured in the constructor. It also does not explicitly copy the mesh object's basis/world transform to the armature or set a parent-inverse matrix. Correct deformation for nonidentity object transforms therefore needs runtime verification rather than assumption. [Creation/binding](../../o3d_io/o3d_armature.py#L102-L146).
- Construction failures are caught and logged; the helper removes the created armature object/data and returns `None`. The importer has already retained the mesh and groups, logs the lack of an armature, and returns generated armatures alongside meshes on success. [Cleanup](../../o3d_io/o3d_armature.py#L147-L155), [caller](../../o3d_io/io_o3d_import.py#L165-L169), [result append](../../o3d_io/io_o3d_import.py#L231-L237), [return](../../o3d_io/io_o3d_import.py#L263-L277).

## 3. Blender export

The exporter builds final O3D vertices from triangle loops, using `(position, normal, UV)` as the deduplication key. It records each source vertex's corresponding final indices and replicates the source group weight onto every mapped index. Vertices not visited by triangles do not acquire a final index and therefore have no exported influence. Empty groups, or groups with no mapped surviving influences, are omitted. [Final-vertex map](../../o3d_io/io_o3d_export.py#L84-L126), [collector](../../o3d_io/io_o3d_export.py#L44-L70), [call](../../o3d_io/io_o3d_export.py#L158-L159).

**Weight-preservation caveat:** weights and source vertex identity are absent from the deduplication key. Distinct source vertices with identical position/normal/UV can map to the same output vertex even if their bone memberships differ. The collector can then produce repeated `(bone, output index)` records or combine different groups on that shared vertex; it does not reconcile or prevent the collision. This follows from the code paths and is not a reproduced runtime failure. The seam test covers one source vertex splitting into two outputs, not distinct differently weighted source vertices merging into one. [Deduplication](../../o3d_io/io_o3d_export.py#L96-L123), [weight copying](../../o3d_io/io_o3d_export.py#L45-L68), [seam test](../../tests/smoke_io.py#L355-L441).

Every populated vertex group is eligible, including groups used for purposes other than armature deformation. Armature hierarchy, bone rest matrices, bone names that have no group, constraints, and pose channels are not consulted by the collector. Weights are filtered for finite/nonnegative values and copied without explicit normalization. [Collector](../../o3d_io/io_o3d_export.py#L32-L70).

For mesh extraction, only Armature modifiers are disabled; other modifiers remain evaluated. The exporter obtains an evaluated object/mesh, applies object-world and Y/Z conversion transforms, applies the supplied global matrix through BMesh, triangulates, then writes the evaluated object's groups against the resulting mesh vertex count. There is no explicit original-index remapping for topology-changing modifiers beyond the final loop map; correct weights for such modifiers require separate verification. [Modifier exclusion/evaluation](../../o3d_io/io_o3d_export.py#L225-L255), [transforms/triangulation](../../o3d_io/io_o3d_export.py#L261-L287), [evaluated-group export](../../o3d_io/io_o3d_export.py#L301-L305).

The object matrix serialized is `(C @ ob.matrix_world @ C).transposed()`, flattened to sixteen values; the global export matrix is applied to temporary geometry separately. Despite the stale identity/TODO comment in `export_transform`, the function does serialize the supplied transform, using identity only when passed `None`. No per-bone matrix is emitted. [Object transform](../../o3d_io/io_o3d_export.py#L262-L282), [flattened argument](../../o3d_io/io_o3d_export.py#L304-L305), [serializer](../../o3d_io/o3dconvert.py#L391-L399).

Modifier flags are restored even through the outer `finally`, and successful temporary mesh creation is paired with `to_mesh_clear()` in a nested `finally`. CFG writing has no ARMATURE-object branch, so armatures themselves are not represented as skeleton blocks in CFG. [Cleanup/restoration](../../o3d_io/io_o3d_export.py#L306-L319), [CFG object dispatch](../../o3d_io/o3d_cfg_parser.py#L643-L654).

## 4. Animation and configuration support

No animation payload exists in the implemented bone binary functions. The armature constructor provides a Blender binding suitable for posing, but does not import OMSI procedural motion, `[links]`, clips, constraints, or keyframes; export intentionally excludes armature pose deformation. This boundary matches the design's explicit exclusion of procedural human runtime, `[links]` pose generation, and animation clips. [Binary record](../../o3d_io/o3dconvert.py#L74-L88), [constructor](../../o3d_io/o3d_armature.py#L102-L155), [rest export](../../o3d_io/io_o3d_export.py#L225-L255), [design scope](../superpowers/specs/2026-10-24-o3d-bone-armature-design.md#L13-L26).

The generic CFG parser stores unrecognized command blocks under material, mesh, or LOD/global `cfg_data` according to the current parse context. The importer attaches mesh/global data to custom properties, and CFG export writes those stored blocks back. This can preserve animation-related text through that generic mechanism, but it neither understands those commands nor creates Blender animation from them. It is not a byte-for-byte CFG preservation guarantee: parsing strips trailing whitespace and writing reconstructs lines/context. [Read stripping](../../o3d_io/o3d_cfg_parser.py#L104-L112), [unknown blocks](../../o3d_io/o3d_cfg_parser.py#L436-L457), [custom-property attachment](../../o3d_io/io_o3d_import.py#L185-L190), [global attachment](../../o3d_io/io_o3d_import.py#L251-L253), [block writer/mesh path](../../o3d_io/o3d_cfg_parser.py#L462-L486), [global writer](../../o3d_io/o3d_cfg_parser.py#L692-L693).

The README likewise says animation is not imported, imported CFG animation is expected to survive as custom properties, and there is no Blender-to-OMSI animation conversion. This is consistent with source scope, but the stated CFG round-trip expectation was not runtime-validated here. [README animation section](../../README.md#L173-L177).

## 5. Test coverage and its limits

These are assertions present in source, **not passing results from this analysis**. The smoke entry point registers the bone checks, and CI declares Blender 4.2, 5.0, and 5.2 jobs. Neither registration nor CI configuration proves a particular run passed. [Registered checks](../../tests/blender_smoke.py#L16-L47), [runner](../../tests/blender_smoke.py#L50-L66), [CI matrix/command](../../.github/workflows/smoke_test.yml#L9-L14), [CI smoke command](../../.github/workflows/smoke_test.yml#L49-L53).

| Present source coverage | Important qualification |
| --- | --- |
| Helper creates `Main`, `Hip`, `Head`, parents, binding and nonzero lengths: [helper check](../../tests/smoke_io.py#L18-L42) | Repeated `Hip` input is supplied, but centroid/max-weight correctness is not directly asserted. |
| Importer creates groups, armature, parents, modifier; no-bone import stays mesh-only: [integration check](../../tests/smoke_io.py#L236-L329) | The loader is stubbed with identity object transform; this does not validate binary decoding or nonidentity bone-space behavior. |
| Optional real human import: [asset check](../../tests/smoke_io.py#L331-L352) | Only runs if `O3D_HUMAN_ASSET` names an existing file, and checks expected vertex-group names when a mesh exists; it does not assert stock-human pose fidelity. |
| Seam duplication copies weights and omits an empty group: [seam check](../../tests/smoke_io.py#L355-L443) | Raw parsing locates `0x54` with `data.find` and loops to a `0x79` byte rather than using the parsed bone count; this is fixture-specific, not a robust general binary validator. |
| Posed export matches rest coordinates and retains pose; modifier flags restored on success/failure: [rest check](../../tests/smoke_io.py#L446-L553), [restoration checks](../../tests/smoke_io.py#L556-L649) | Synthetic rigs and simple modifiers; no assertion of OMSI deformation equivalence. |
| Narrow/wide flag selection and version-2 rejection: [width checks](../../tests/smoke_io.py#L698-L847) | Width tests assert header flags, not actual wide bone-record contents/round-trip. Version 3 is not exercised. |
| Name validation: [validation check](../../tests/smoke_io.py#L850-L882) | Despite its docstring, this test only exports a normal 63-character name and asserts the file exists; it does not directly test overlong/CP1252-incompatible names, count overflow, invalid raw indices, or invalid raw weights. |
| Visible deformation: [pose check](../../tests/smoke_io.py#L885-L950) | Uses a manually constructed two-bone rig, not the helper-generated skeleton or an OMSI animation. |
| Names/weights export, parse, and reimport with canonical parent: [round-trip check](../../tests/smoke_io.py#L953-L1112) | Uses `Main`/`Hip` and simple weights. Reimport weight checks iterate existing assignments; not every missing expected assignment would necessarily fail. It does not check original arbitrary hierarchy/rest matrices because they are not serialized. |
| Malformed influences and empty groups: [recovery check](../../tests/smoke_io.py#L1115-L1274) | Some helper assertions are conditional on a non-`None` result; all-invalid records may legitimately produce fallback bones. The exporter portion supplies valid Blender assignments plus an empty group rather than injecting malformed raw weights. |

No dedicated source test was identified in the inspected smoke suite for duplicate imported names/group disambiguation, arbitrary hierarchy preservation, differently weighted coincident-vertex merging, >1/sum-not-one weight semantics, nonidentity generated-rig transforms, topology-changing modifier weight remapping, exact byte-name preservation, joint limits, or animation conversion. The relevant production paths and narrower assertions above delimit what is currently evidenced.

## 6. Boundaries for the separate OMSI comparison

Use these addon facts as comparison inputs, not assumptions about the engine:

- Verify whether OMSI's actual reader agrees with the addon's fixed `u16` bone/influence counts and option-bit-controlled index width, especially the version-3 boundary. [Implemented contract](../../o3d_io/o3dconvert.py#L178-L223), [writer](../../o3d_io/o3dconvert.py#L372-L418).
- Determine separately how OMSI maps names to runtime bones, handles unknown names, and supplies hierarchy/pivots/rest transforms. The addon preserves usable group names but injects its own canonical editor hierarchy/template. [Name handling](../../o3d_io/io_o3d_import.py#L197-L237), [canonical data](../../o3d_io/o3d_armature.py#L8-L37).
- Determine engine weight normalization, duplicate influence behavior, per-vertex influence limits, and handling of weights outside `[0,1]`; the addon has no explicit cross-bone normalization or per-vertex cap. [Group import](../../o3d_io/io_o3d_import.py#L211-L229), [collection](../../o3d_io/io_o3d_export.py#L44-L68), [serializer checks](../../o3d_io/o3dconvert.py#L295-L310).
- Establish OMSI procedural human animation, `[links]`, bone transform composition, and any runtime joint limits from engine evidence. This addon does not implement them, so its Blender rig is not evidence of equivalent engine kinematics. [Constructor scope](../../o3d_io/o3d_armature.py#L102-L155), [design exclusions](../superpowers/specs/2026-10-24-o3d-bone-armature-design.md#L24-L26).

No implementation changes or runtime compatibility conclusions are proposed by this report.
