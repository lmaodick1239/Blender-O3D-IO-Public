# Task 7 — CFG selector and controlled comparisons

2026-11-12, Asia/Hong_Kong. Base `bf40ad09d66bf5fe97d92c14fc6d8f0ae2060c7d`. Production/test checkpoints:

- `3b38c8468d45d9d71b63f054355984d6b0503c97` (parent base): native repeat selector and initial RED/GREEN tests.
- `985f35ef4fad9ce6d14619147befd8249c025e3d` (parent `3b38c84`): four controlled CFG conditions.
- `897507f93a3a81a39048f4a2eb43e629c5fc272a` (parent `985f35e`): selector edges, exact imported overrides and actual shared entrypoints. Source/tests committed before this evidence.

## Demonstrated fix

The [native C1 contract](<../task-3/README.md#L90-L105>) selects a zero-based **matching-texture occurrence**, lowercasing ASCII A–Z only. The [writer](<../../../../../o3d_io/o3d_cfg_parser.py#L672-L699>) now reuses the existing helper and counts serialized texture identities in slot order, including empty identities contributed by None/untextured slots. `[A,B,A]` emits ranks **0,0,1**, not **0,1,2**. `[matl_change]` uses the same ordinal. Binary triangle slots remain absolute; no importer/exporter/codec/geometry/UV conversion changed.

Before production edits, actual export with decoded names `[A.PNG,B.PNG,A.PNG]` and triangle slots `[0,1,2]` failed the independent selector assertion: writer ranks were `[0,1,2]`. Collected job `bash-d5bc4e02cd7a4296`, **exit1**. After the minimal parser-only fix, the same focused suite passed **3/3, exit0**, job `bash-b3b64212290f4755`. Both exits are tool-collected, not inferred from log text. [Verification identities](<verification.json>) bind RED and exact-final source hashes.

The [tests](<../../../../../tests/smoke_export_fidelity.py#L1191-L1435>) use an independent ordered command reader and native selector oracle over independently decoded O3D material records. Coverage includes nonadjacent/same-material duplicates, None/untextured/empty-filename slots, ASCII case, CP1252 Ä/ä and Straße/STRASSE distinctions, actual shared filename conversion, conditional materials and UV splits. The 13-slot fixture preserves 13 absolute face slots and 39 serialized split vertices. Exact assertions cover all 14 ordered `[matl_allcolor]` values, including retained raw overrides, ambient, HDR emission and Power1500; explicit supported setters remain after inferred setters. CFG generation does not mutate embedded material records.

## Four controlled conditions — native rendering pending

One material/mesh generates these assets under the requested test output directory, in `cfg_materials/cfg_four_conditions/`:

| Condition | Controlled difference |
| --- | --- |
| Embedded minimal | Only a matching mesh declaration; embedded data without material CFG settings. |
| Normal generated | Actual normal generated CFG, including inferred and explicit blocks. |
| No inferred environment | Remove only the single inferred env block; exact explicit suffix survives. |
| No inferred light/night | Remove only the inferred light-map block; explicit light/night/env/alpha/bump/allcolor blocks survive. |

All four point to the **same O3D**. Direct embedded and CFG-produced decoded O3Ds compare equal. Filtering is test-only, narrowly scoped to the known generated prefix; no public export switch or generic CFG transformation was added. Hashes are retained in [verification.json](<verification.json>); rerunning the synthetic test regenerates the assets without private inputs. **These are controlled serialization/pending-native comparisons, not observed appearance or native visual parity.**

Inspected and retained: roughness `<=.1` env inference, `sqrt(specular)` reflection factor, emission Strength `>1` light versus `<=1` night routing, alpha/CLIP choice and bump factor rounding. The fixture checks reflection≈.6, bump .4, inferred alpha1, explicit alpha2 precedence, and the light/night branch. No isolated native mismatch authorizes changing those policies. First fixture input `.1` stored above `.1` in float32; changing its test input to `.01` corrected setup, not production policy. The separate `.1001` test still asserts no inferred env.

## Actual shared entrypoints

The synthetic existing human fixture exports through O3D-only, CFG, SCO and HUM. Their complete decoded binary records are equal; all four generated O3Ds have SHA256 `6c6ab48f401a01adf0802f21af7cd8aebbec04e1683efc075dd11eb2c0c64828` on the recorded 5.0.1 run. Material names `[A,B,A]`, selectors and absolute face slots `[0,2]` agree. Source helper weights must not generate `[smoothskin]` after filtering; genuine serialized Main/Hip blending must generate it exactly once. HUM bindings use serialized bone names with established native slots Main=-11/Hip=-10. Source mesh/shaders/modifiers and selection/context compare unchanged.

This is bounded synthetic shared-path coverage, not proof for every material-changing modifier. No speculative Geometry Nodes fixture, architecture change or new metadata API was added. Existing imported raw/rest/helper/UV/wire-format behavior remains under the covering suites.

## Collected exact-final verification

| Check | Result | Executor build / managed job |
| --- | --- | --- |
| All fidelity | **82/82 PASS, exit0** | 5.0.1 `a3db93c5b259`, `bash-3ebe553419024257` |
| Pure tests | **30/30 PASS, exit0** | python3, same job |
| Existing full smoke | **PASS, exit0**, final smoke marker and 33 human checks | 5.0.1, same job |
| Focused CFG | **6/6 PASS, exit0** | 4.2.23 `d0cbe84903e8`, `bash-daf9b8c460494ab6` |
| Focused CFG | **6/6 PASS, exit0** | 5.2.4 `cd5dc428cce1`, same job |

Both final jobs and every intermediate own job were collected. All final fidelity summaries bind the same committed source/test hashes; a bounded post-collection check verified those hashes, case statuses/counts and log identities. No full historical matrix was rerun here. Two intermediate fixture-only failures remain attributed as failures: `.1` float storage (job `bash-049aed57ac784b40`, exit1) and incorrect test-only HUM slots0/1 (job `bash-01220d69debc4f07`, exit1); neither changed production policy.

Reproduce using the executors/common arguments and exact command forms in [verification.json](<verification.json>). Local logs/summaries are hash-bound provenance, not public fixture dependencies. No executable/private/reference/history data, new package, configuration, native launch or giant corpus/verifier is included.

**Remaining gates:** lead review/final integrated matrix; [Task 3 named native capture gates](<../task-3/README.md#L107-L120>) for appearance, effect arithmetic, alpha history, dynamic maps, texture orientation and color space. Serialization success does not close them.
