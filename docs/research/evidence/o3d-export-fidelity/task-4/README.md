# Task 4 geometry/export fidelity evidence

Recorded **2026-11-12, Asia/Hong_Kong** after production checkpoint commit `07c7b18680e25a00c11094f8df4d93b40204b8c1`, parent `b585e514038309f380ae519c9f05f2956c3206a5`. This is a bounded Blender/add-on evidence record, not native renderer parity. Production and focused-test sources were frozen before this evidence commit; no source edits or test reruns were made for documentation.

## Current collected verification

Finalizer-owned managed job `bash-ebd4031859d244fd` completed **exit 0**. The exact commands, argv, timestamps, source SHA-256 values before/after, log hashes and retained summary are in [`verification.json`](verification.json).

| Command | Result | Retained log |
| --- | --- | --- |
| `blender --background --factory-startup --python-exit-code 1 --python tests/smoke_export_fidelity.py -- --case custom_normal --case transforms` | **28/28 cases PASS** (11 custom-normal, 17 transform) | `task-4-finalizer-geometry.log` |
| `python3 -B -m unittest discover -s tests -p 'test_*.py' -v` | **30 tests OK** | `task-4-finalizer-pure.log` |
| `blender --background --factory-startup --python-exit-code 1 --python tests/blender_smoke.py` | **full smoke PASS**; `BLENDER_O3D_IO_SMOKE_OK 5.0.1` | `task-4-finalizer-smoke.log` |

All three runs used Blender **5.0.1**, build `a3db93c5b259`. The verification record shows unchanged hashes for the exporter, compatibility helper, focused runner, codec and full-smoke runner across the collected job.

## Bounded repair evidence

- Evaluated corner normals and loop-triangle loop indices are captured before position baking. Corner identity carries positions, UVs, material indices and evaluated weights through Blender tessellation; destructive BMesh triangulation is no longer used.
- Exactly one owner applies `normalize(A^-T n)` to directions for the actual baked linear GCM transform. Translation is excluded. Winding compensation is a separate whole-corner ordering operation and remains distinct from shading-normal direction.
- Position baking remains sequential **M, C, G**. This preserves finite geometry under the existing extreme-scale human preflight case; composing first in Blender float32 overflowed that case.
- Singular transforms do not invoke a raw inverse and do not invent a normal axis: undefined inverse-transpose directions serialize as finite zero vectors. Near-singular transforms retain their real finite inverse-transpose directions. Collapsed geometry remains exportable under the established behavior.
- The prepared tuple remains `(evaluated, mesh, flattened_frame)`, with temporary geometry fully baked to GCM/export space. Source mesh, modifiers, pose, selection, active object and mode are covered by the focused fixture restoration checks.
- Codec packing is performed into `BytesIO` before opening the destination. Empty-geometry rejection and an induced post-codec failure therefore preserve an existing sentinel destination; this is not a general filesystem transaction or disk-write atomicity claim.

## Historical RED and remaining gates

The prior baseline RED remains attributed to the inherited implementer run: its harness executed the parent-commit exporter/compatibility modules in memory and recorded authored-normal/tessellation, singular, and destructive-open failures. It is retained locally in the Task 4 scratch logs and is not represented as a fresh current run. The inherited all-group summary had 34 PASS / 6 intentional remaining failures (emission and five UV-policy cases); those belong to later material/UV policy scope and were not changed here.

This checkpoint does not establish native normal sign, culling, shader/material transfer, dynamic skinning, special origin paths or native visual parity. Blender 4.2/5.2 coverage, Task 5/6/7 work and lead review remain open. No native launch/install/configuration or importer change was made.

Evidence classes: current runs are **observed runtime (Blender/add-on only)**; geometry formulas are **derived mathematics**; material/UV exclusions are **scope policy**; native renderer behavior remains **unresolved**.
