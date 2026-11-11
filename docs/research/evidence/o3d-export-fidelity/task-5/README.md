# Task 5 material conversion checkpoint

Recorded **2026-11-12, Asia/Hong_Kong**. Source/test commit `03b6dea057fa1cd917b94286ebe824fe3eac752d`, parent `9cbbd1b91ef3c1584c285681ea5d04fe44da2fbc`. These are Blender/add-on serialization observations and explicit authoring policies, not native rendering or BRDF equivalence. The [Task 3 material/CFG gates](../task-3/README.md#4-material-question-eleven-floats-through-cfg-to-the-draw) remain the native evidence boundary. No new native investigation, gamma conversion, or env/light/night heuristic redesign occurred.

## Conversion and preservation

- Supported new/edited roughness uses `power = 1000 * (1 - roughness)`. Import preview uses `clamp(1 - power/1000, 0, 1)`. Unchanged finite imported powers, including 0/32/500/1500, retain their original values. Existing `o3d_specular_power` and `o3d_specular_roughness` names remain compatible.
- Supported constant emission exports color times strength, explicitly black at zero. Finite HDR components survive. Blender 4+ specular remains tint RGB times IOR level. No gamma compensation is applied.
- A new direct image **Color** to Base Color uses neutral white RGB and independent alpha. Image **Alpha** to Base Color is diagnosed as unsupported. Unchanged imported nonwhite diffuse, independent alpha, specular, and emission are stored separately and survive unrelated roughness edits. Component baselines include relevant defaults/source sockets/image identity; relevant component edits use the declared authoring conversion. Tests compare actual serialized f32 bytes for unchanged native components.
- Import CFG matching lowercases ASCII A–Z only and counts per-texture occurrences; binary triangle material indices remain absolute. Allcolor's effective power is selected before capturing the final roughness baseline, including env preview ordering. Textureless explicit overrides also reach processing. Raw fourteen-field `[matl_allcolor]`, noZ, and alphascale blocks are retained separately in CFG data. Existing ambient/env/night/light preview heuristics remain previews, not native embedded truth; CFG serialization does not mutate embedded fields.

## Supported graph boundary

The installed wrapper recognizes direct Principled/output pairs, constant input defaults, immediate image inputs and selected image-vector Mapping setup. Its scalar/RGB getters read inactive destination defaults for linked inputs; they do not evaluate RGB, Value, groups, or arithmetic. The exporter now resolves only direct RGB/Value constants in addition to supported unlinked inputs. It diagnoses unsupported group/arithmetic/image-strength paths and active non-Principled surfaces instead of silently exporting their defaults. No generic graph evaluator was added.

Existing CFG alpha/transparency, specular-mask/reflection, emission light/night, and bump paths remain available. Their inactive embedded fallback constants are explicitly diagnosed as **not evaluated graph values**. An image-driven emission color is not multiplied by strength into a guessed baked emission; the existing CFG strength routing remains unchanged. Color versus Alpha source identity is retained in edit baselines. This is bounded compatibility, not a texture/shader visual-equivalence claim.

Legitimate non-node Material constants keep the established wrapper fallback (Material diffuse RGB, alpha1, black tint/emission, new authored power from Material roughness) without creating nodes. This path is exercised on Blender 4.2.23. On 5.0.1 and 5.2.4, assigning `use_nodes=False` leaves it true; those runs explicitly report that the non-node case is unavailable and do not establish non-node coverage there.

## Test evidence

[Verification](verification.json) retains exact commands, exit codes, source hashes before/after, full local-log hashes and bounded line-numbered excerpts. Managed final job `bash-d1fcf98401f64bbf` was collected **exit0**, with identical source hashes throughout. Production/tests were committed before this evidence update; no additional implementation change or test rerun was made for documentation.

| Final check | Result |
| --- | --- |
| Pure unittest discovery | 30 tests, exit0 |
| Blender 5.0.1 `materials`, `custom_normal`, `transforms`, `cfg_materials` | 47 cases pass:17 material,28 geometry,2 CFG; exit0 |
| Complete existing Blender 5.0.1 smoke suite | `BLENDER_O3D_IO_SMOKE_OK`, exit0 |
| Blender 4.2.23 `d0cbe84903e8`, focused materials | 17 cases pass, exit0 |
| Blender 5.2.4 `cd5dc428cce1`, focused materials | 17 cases pass, exit0; non-node case explicitly unavailable |

The strengthened material cases first produced real RED for authored powers, strength3/0 emission, image neutral RGB, native components/previews, direct constants, unsupported paths, CFG image emission treatment, and 4.2 non-node compatibility. Earlier whole-corpus execution retained exactly the five intentionally unresolved UV cases; its earlier runner/source identity is recorded separately and is not represented as final-source verification.

Compatibility corrections are narrow: the emission smoke explicitly sets strength1; duplicate missing-texture CFG selectors now use valid repeat ranks0/1 while retaining absolute face-slot assertions. The embedded material smoke asserts the intended power32 preview roughness.968 and retains raw power/alpha round-trip assertions.

The supplied human scene contains an active unsupported MMD shader group. Its original transient converted mesh now must refuse readiness/export under a write-open guard, with no files and unchanged context/source hash. Positive human export coverage remains: a disposable copy of the converted mesh/data/materials receives explicitly authored Principled constants, preserves geometry/weights/face slots, and exports HUM/CFG/O3D with22finite links. This variant does not claim to flatten the MMD shader. The original material graphs and source fixture remain unchanged.

## Review fix 1 — active material surface

Source/test fix `af362ab3a6103f75a8c099bcff4bd5d2225e9bc5`, parent `1d8951affb0e28489729fac6325bd6107fdd2ab0`. Independent review found that the installed wrapper can choose an inactive direct Principled/output pair while another output is active. Two real two-output cases first failed: active unsupported group plus inactive Principled silently exported; active different Principled exported the inactive constants.

The minimal guard requires one active Material Output with a direct Principled Surface, then requires the wrapper-selected pair to match that active pair. A mismatch is explicitly diagnosed as ambiguous rather than serializing inactive values. This bounded refusal also keeps existing embedded and CFG extraction consistent without rewriting the CFG writer or adding output traversal. The legitimate non-node fallback precedes the guard; normal one-output materials, established CFG links and per-component raw baselines remain covered.

[Fix verification](fix-1-verification.json) retains exact commands, exits, source hashes before/after, log hashes and bounded excerpts. RED job `bash-9050426560bd4140` was collected exit1 for the two new cases. Frozen GREEN job `bash-3a049ac6437c445f` was collected exit0: pure30, focused49 (19 material/28 geometry/2 CFG), complete existing Blender5.0.1 smoke, and focused19 on4.2.23/5.2.4. Both new cases pass; active unsupported and ambiguous inactive selection refuse before publishing output without changing links/active flags. Source hashes remained identical throughout. Non-node coverage remains actual4.2 only, explicitly unavailable on5.x. The prior checkpoint's47/17 counts above remain attributed to its original source commit. No source edits or test reruns were made for this addendum.

## Remaining gates

Task 6 UV selection/Mapping and Task 7 CFG writer repeat indices/policy remain open. Native effect arithmetic, texture/color-space transfer, alpha history, env/light/night behavior and rendered parity remain open under the [canonical capture recipes](../task-3/README.md#6-exact-remaining-load-bearing-gates-and-capture-recipes). Full 4.2/5.2 integration matrices and independent source review belong to lead verification. Geometry, rest/split-weight/helper/context behavior and codec tuple/wire shapes were preserved.
