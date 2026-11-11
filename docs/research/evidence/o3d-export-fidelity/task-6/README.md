# Task 6 — material-selected UV and Mapping export

Recorded **2026-11-12, Asia/Hong_Kong**. Source/tests: **`51c914e75fed77d601c4f365a5f21d1a39e80797`**, parent `7014ccb3084132c6068ab7987051994213947788`; reviewed helper-contract follow-up: **`76007bc242d54b16fba09c9e11fd7d64e48380e6`**, parent `51c914e75fed77d601c4f365a5f21d1a39e80797`. Only the [exporter](../../../../../o3d_io/io_o3d_export.py) and [fidelity tests](../../../../../tests/smoke_export_fidelity.py) changed. This is Blender construction/shader evidence, **not native rendering parity**.

## Implemented boundary

- A supported **direct active Principled Base Color image Color output** selects its named UV Map first; otherwise use render-active, active/first, or the no-layer source `(0,0)` default. A missing explicit name diagnoses; no unrelated-map substitution.
- A single static Mapping accepts POINT `T @ R @ S`, TEXTURE inverse point order with shader componentwise safe divide, or VECTOR `R @ S` without the unavailable Location socket. Rotation is XYZ in three dimensions. Apply exactly one existing target V conversion **after** Mapping.
- Resolve material/corner final UV **before deduplication**. Material-specific mappings split shared source corners as needed; every output split retains its source weights.
- Diagnose singular TEXTURE (zero-scale components produce shader zero), unsupported NORMAL, procedural/generated/From Instances sources, linked inputs, animation, and incompatible alpha/specular-mask/emission/bump coordinate streams. Compatible established CFG texture routes stay accepted. Node-tree animation is conservatively refused, not frozen at the export frame.
- Geometry-only readiness also serves unconverted MMD graphs: without the supported active Color-image path it keeps established render/default geometry. This is **not actual-export graph acceptance**: the strict material builder still rejects unsupported/ambiguous active surfaces and unsupported Base Color paths before publication. Eligible UV errors propagate; there is no broad exception fallback.

The normal/rest-space/prepared baked-mesh tuple, helper filtering, weighted source identity, split weights, context restoration, codec and public record shapes remain intact. No production normal/compatibility rewrite, material conversion/importer changes, CFG writer, gamma or env/light/night policy change, dependency, new switch, native research or OMSI launch.

## Independent oracles and TDD

The reviewed [U1/U2 contract](../task-3/README.md#L53) and retained [pinned Blender source/probe report](../task-3/blender-api-research.md#4-mapping-node-point-texture-and-vector) are the shader authority, not reference transform order or its VECTOR exception. The Blender source pin is `a51f293548adba0dda086f5771401e8d8ab66227`.

Before production edits, existing five UV cases were **0/5 PASS, exit1**. Extended final29 were **2 PASS/27 FAIL, exit1** (literal named selection and no-layer baseline already pass). The new mapping/material/diagnostic assertions fail for absent behavior, not setup errors. Successful alpha fixtures deliberately use Base Color's coordinate path; separate fixtures demand explicit conflict refusal.

Tests check the exact plan values: render B `(0.25,0.75)` → `(0.25,0.25)`, named A `(0.1,0.2)` → `(0.1,0.8)`, and POINT source `(0.2,0.3)`, scale `(2,3,1)`, Z rotation `pi/2`, translation `(0.1,0.2,0)` → `(-0.8,0.4)`. Further cases cover full XYZ rotations, negative scale, TEXTURE singular safe divide, per-material maps/transforms, weighted seams and unchanged source UV/node values/links. **Six real CPU Cycles Mapping bakes per build** independently compare decoded O3D UVs against shader output (POINT/TEXTURE/VECTOR, negative POINT/TEXTURE, singular TEXTURE).

The permitted test-only 4.2 generated-normal oracle correction uses a version-aware reset on its disposable evaluated mesh, compares against a fresh mesh with no custom data, and checks known triangle cross-product geometry. It does not call production preparation. The custom-disabled assertion remains active and passes; no new 4.2 production-normal defect was exposed. Historical frozen **4.2 27/28 setup failure vs 5.2 28/28 pass** remains unchanged history.

## Exact-final verification

[Hash-bound verification](verification.json) records full argv, source/parent, imported source hashes, builds, exact collected exits and local log/summary hashes. All final focused runs imported exporter SHA256 **`b27b969aab2ec28805b7e52666cdfa30cccbd83557b1f8731d34e427f2ad8b2e`** and test SHA256 **`a2acdca4e14fd250ac7d92d9c89dda07ec6d3a4a534a5326ec6ae797b79aa48c`**, matching source `76007bc`.

| Runtime / check | Result | Collected job |
| --- | --- | --- |
| Blender 4.2.23 LTS `d0cbe84903e8` focused | **76/76 PASS, exit0** | `bash-a49f2139afac48b0` |
| Blender 5.0.1 `a3db93c5b259` focused | **76/76 PASS, exit0** | same |
| Blender 5.2.4 LTS `cd5dc428cce1` focused | **76/76 PASS, exit0** | same |
| Pure codec/package/support | **30/30 PASS, exit0** | same |
| Existing section-count + readiness regressions, 5.0.1 | **2/2 PASS, exit0** | `bash-c9b7967681f54e31` |
| Existing complete smoke, 5.0.1 | **PASS, exit0**, `BLENDER_O3D_IO_SMOKE_OK 5.0.1`; 33 human checks | same |

Focused76 comprises **UV29 + custom-normal11 + transforms17 + materials19**. The combined jobs explicitly reported each invocation's captured exit, not an inferred success from log silence. Generated O3Ds, images, complete manifests and raw logs remain local scratch, not public dependencies or a duplicated corpus. Reproduce with the committed tests and exact commands in the verification record; the scratch helper simply invokes the two unchanged existing regressions, not a new framework.

### Two diagnosed follow-up regressions, not hidden passes

The first full smoke on `51c914e` exited1: new UV slot lookup ran before the existing >65535 material-count guard, so the existing section-count test's deliberately invalid slot sequence raised AttributeError. The same guard was moved to export entry; no generic slot fallback or weakened assertion.

The guard-only full smoke then exited1 at existing MMD readiness: the geometry helper had acquired strict material rejection. The explicit supported-active-image eligibility boundary above restores the accepted geometry-only caller contract without relaxing actual export. Both roots were traced and approved before repair; original failing logs/exits remain hash-bound in the verification record. Final unchanged regressions and full smoke pass on `76007bc`.

## Remaining gates

Lead owns final integrated full-matrix/board acceptance. No native texture orientation, final GPU/effect shader, color-space or visual-parity claim follows from these Blender tests. Arbitrary graphs, node groups, multiple Mapping nodes, animation evaluation and general procedural-coordinate baking remain unsupported and diagnosed where they affect an eligible image stream. No reference exporter was used as a numerical oracle.
