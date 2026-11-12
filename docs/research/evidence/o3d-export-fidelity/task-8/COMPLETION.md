# Local completion follow-up — 2026-11-12

This addendum follows the task-report audit of the automated exporter repair. It closes the two optional-reference harness findings while preserving the distinction between serialized-value tests and native observations.

## Scope

The follow-up changes the test harness only: reference surface equality is required only for explicitly comparable fixtures; transformed-normal deltas remain recorded observations. Current-export source/context checks execute before reference setup, and a global-scale reference copy and its mesh are removed in an owned `finally` block with strict reference-context restoration. Product serialization and the unmodified reference exporter are unchanged.

The [historical validation report](<README.md>) remains attributed to its original source and logs. The [historical whole-branch review](<FINAL-REVIEW.md>) is not represented as a review of later harness changes.

## Frozen follow-up verification

Harness commit `1bacc2a180cb6106614e33b22fb838f858198b4e` changes only `tests/smoke_export_fidelity.py`, SHA-256 `35a540588e375e2e90a60ed85f2ac591db4b66bfdef1e5fedd7895f17550c876`. [Exact commands, process exits, source inventories and log identities](<completion-verification.json>) retain the following observed outcomes:

- Real focused RED: all three affected cases fail before changes. Focused GREEN: all three pass. The same reference-enabled cases also pass on Blender 4.2.23 and 5.2.4 after the fix.
- Final Blender 5.0.1 optional-reference refresh: **81 PASS / one reference VECTOR error, actual exit 1**. The incompatible-equality and global-scale context failures are gone. Raw reference deltas remain available; the known reference exception is not recast as success.
- Eight live controls meet their expectations, including six intentional negative scenarios: compatible reference-normal corruption, current selection/active/mode mutation and current/reference injected errors remain detectable; owned reference IDs/context are restored on failure.
- Final-source pre-merge public matrix: **30 pure tests**, **82 standalone fidelity cases per build**, and **121 root + 82 fidelity + 31 synthetic-human integrated checks per build** on **4.2.23 `d0cbe84903e8` / 5.0.1 `a3db93c5b259` / 5.2.4 `cd5dc428cce1`**, all exit 0. Strict caller-restoration checks pass and all 42 source/config/test hashes remain unchanged during the matrix.
- Retained evidence verification and its corruption regression pass with original captured script/JSON hashes. The extension archive still matches every current production byte; no product change requires repackaging. The earlier native comparison package retains its original source provenance rather than being falsely attributed to this later harness commit.

The final-source matrix began before the harness commit was recorded; its explicit before/after byte inventory matches that committed harness exactly. The earlier interrupted matrix/review was superseded after a late permanent cleanup assertion changed the source; no result from the earlier source is presented as final-byte validation.

## Independent follow-up review

A fresh independent reviewer inspected the complete frozen incremental harness diff, binding requirements, live final source, worker RED/GREEN and mutation controls, all nine final pre-merge run logs, focused reference checks on 4.2/5.2 and the full 42-file source inventory. **Spec compliance PASS; task quality PASS; no Critical, P1, P2 or P3 code findings.** The review applies to automated follow-up commit `1bacc2a`; it preserves the existing native/reference limits and does not claim runtime rendering or an already executed merge. The earlier drift-interrupted review was not used as an approval.

## Completed local integration

The original checkout's local `blender-5.2-support` was fast-forwarded from `23c7ef6396b451fb77f6f7841b17d24e5cc45d37` to `f313eddbf7679f2a7c16b6785869cee5ca93e064` using `git merge --ff-only fix/o3d-export-fidelity`. No remote pull/push occurred.

Tests then ran from that **merged original checkout**, rather than the feature worktree: pure30, retained-evidence validation/corruption regression and integrated121root+82fidelity+31synthetic-human checks on each exact4.2.23/5.0.1/5.2.4 build all exit0, strict caller restoration passes and all42 inventoried source/config/test hashes remain unchanged. [Postmerge receipts](<completion-verification.json>) retain exact commands, log hashes and the tested commit. The final receipt-only commit documents these observed outcomes; it changes no tested product/harness bytes. The feature worktree and branch remain as local evidence storage.

## Evidence boundaries retained

The unmodified reference's VECTOR Mapping export reads an unavailable `Location` socket. Its full comparison command must continue to record the actual nonzero exit; the exception is not hidden or called a successful comparison. All independent current-export checks remain mandatory.

The research-only [derived-math helper](<../task-3/check-derived-math.py>) regenerates its JSON despite its historical read-only module description. It is itself hash-bound retained evidence. The README explains the actual behavior; the script and its original capture hashes remain unchanged.

No usable authorized OMSI installation has been established. The synthetic package remains **NOT RENDERED**, with loader roots unobserved and origin/skin cases lacking executable host wiring. Native culling/normalization/effect, texture/color-space/alpha-history, dynamic-map, origin-animation and skin-driver gates remain open. The original motivating appearance asset was not supplied, and the newer optional private blend remains unreadable by Blender 4.2. No native launch, installation, new Wine prefix or graphics change is part of this local merge.

Local raw verification outputs and generated archives remain in the evidence-bearing worktree. They are gitignored, so this worktree is preserved rather than destructively cleaned up after integration. Committed summaries preserve provenance without pretending that raw artifacts are included in a clean public checkout.
