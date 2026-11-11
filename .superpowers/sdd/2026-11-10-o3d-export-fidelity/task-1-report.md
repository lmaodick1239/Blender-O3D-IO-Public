# Task 1 report: export-fidelity research checkpoint

**Status:** DONE_WITH_CONCERNS, pending lead review. Task 1 is research-only; follow-on implementation is not included. Execution date: 2026-11-11, Asia/Hong_Kong. Base commit: `23c7ef6396b451fb77f6f7841b17d24e5cc45d37`; branch: `fix/o3d-export-fidelity`. This report is included in the same investigation checkpoint as the ledger/evidence. The exact resulting commit hash is reported to the lead and final response after committing; no self-referential hash is fabricated here.

## Implemented items

- Read the [isolated Task 1 brief](task-1-brief.md) first, then its updated controller context and [binding constraints](global-constraints.md). Did not read the full approved plan, other task briefs, progress tracker, or unrelated workspaces.
- Loaded research/execution/verification/review skills. This delegated session cannot spawn another agent; primary-source research and self-review were performed directly. The updated brief explicitly assigns shared-board control to the lead; the child neither discovers nor mutates board state. Leave task `task-1` in_progress for lead review.
- Created the [current-status ledger](../../../docs/research/2026-11-10-o3d-export-fidelity.md) with one bounded claim per table row: question, old evidence, current source, observation, evidence class, dependency, repair/test task.
- Reconciled alpha, imported exponent, scaled origin, safe long-name mapping, helper filtering, runtime skinning limits, headers, fixed bone widths, rest-space evaluation, source-aware split weights, context/modifier restoration, path validation, smoothskin CFG generation and additional historical codec findings. Implemented behaviors are preservation requirements, not new Task 1 fixes.
- Traced all direct callers of the four requested helpers, recorded exact tuple/dictionary contracts, human measurement/readiness/export dependencies, validator wrappers, raw-bone versus name-only metadata, and the dynamic panel-test monkeypatch.
- Created the five-question evidence table, explicitly separating static normals from native skinned-clone normal recomputation. Static/source, Blender observations, native runtime absence, mathematical identities, authoring policy and unresolved dependencies remain separate. No native visual parity is claimed.
- Recorded bounded executable/reference/Blender/fixture identities and retained-primary-export hashes. Read-only executable hash matches the historical build; mismatches are an explicit address-reuse gate.
- Inspected each existing `.blend` in isolated background, factory-startup, automatic-script-disabled Blender processes, with bounded detailed inventory and all-object aggregates. All fixture hashes remain unchanged.
- Ran fresh in-memory Blender probes and the existing pure suite; did not edit production or tests, add dependencies, change the reference checkout, launch OMSI/Wine, invoke Ghidra, or alter its original project.

## Changed paths (explicit staging only)

1. [Research ledger](../../../docs/research/2026-11-10-o3d-export-fidelity.md).
2. [Evidence readme](../../../docs/research/evidence/o3d-export-fidelity/README.md).
3. [Identity record](../../../docs/research/evidence/o3d-export-fidelity/identities.json).
4. [Caller inventory](../../../docs/research/evidence/o3d-export-fidelity/caller-contracts.json).
5. [Fixture inventory](../../../docs/research/evidence/o3d-export-fidelity/fixture-inventory.json).
6. [Checkpoint probes](../../../docs/research/evidence/o3d-export-fidelity/checkpoint-probes.json).
7. This [Task 1 report](task-1-report.md).

Research paths are ignored by default and must be force-added by exact path. No copied historical report/evidence, brief, baseline log, constraints file or progress tracker is staged.

## Commands and output

Identity commands:

```sh
pwd
git rev-parse HEAD
git status --short
blender --version
sha256sum /mnt/Random/users/user/Documents/Ghidra/OMSI/Omsi.exe
sha256sum .gitignorefolder/Blender-OMSI-Exporter/io_export_o3d/exporter.py .gitignorefolder/Blender-OMSI-Exporter/io_export_o3d/node_shader.py .gitignorefolder/Blender-OMSI-Exporter/io_export_o3d/meshio.py
```

Observed:

```text
cwd: /mnt/Random/users/user/Documents/GitHub/Blender-O3D-IO-Public/.worktrees/o3d-export-fidelity
HEAD: 23c7ef6396b451fb77f6f7841b17d24e5cc45d37
initial git status --short: empty
Blender: 5.0.1; build a3db93c5b259
Omsi.exe: c7765877620816dd4de4cceb21dce1996c8789c89ee550c1fb58440ee689a33e
exporter.py: a51396f9c0360a728dc224fcbd7b78602375edc1d50c1013a2134060fedeb340
node_shader.py: 64776f9b6fbfe6b76a8b49f647cab4598b59bcea3077d5b10d69ff5b07f57f07
meshio.py: 205da29f652a7c439c9dfde348cf8eedbefb05c7e58fe3f0e23a4778e54bc526
```

The full Blender version output, binary hash, reference symlink target and exact identity command arrays are retained in the JSON record. No broad hash/tree dump was taken. An early environment probe attempted `python`, which was absent; this was diagnosed immediately, `/bin/python3` resolved, and subsequent scripts used `python3`. No failed research result was treated as evidence.

Fixture/process commands (full argument arrays and expressions retained in fixture JSON):

```text
blender --background --factory-startup --disable-autoexec <one existing tests/Untitled*.blend> --python-exit-code 1 --python-expr <read-only inventory>
Three detailed + three aggregate processes: exit 0 each
Fixture SHA-256 equality before/after: 3/3
Object counts: Untitled=167; Untitled1=7; Untitled2=92
Weighted meshes: 0; 2; 1
Armatures: none; 13 and 574 bones; 319 bones
```

Targeted probe command (full Blender expression/output retained in probe JSON):

```text
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --python-expr <in-memory add-on probes>
Exit 0
Embedded alpha: 0.25 -> 0.25
Imported power: 32 -> 32
Emission color (0.2,0.4,0.6), strength 3: serialized color only (float32 approximations recorded)
Active EditUV (0.1,0.2), render-active RenderUV (0.7,0.8): serialized UV (0.1,0.8)
Empty export: ValueError 'O3D export requires at least one vertex'; existing output 13 bytes -> 0 bytes
```

The last assertion intentionally detects a current failure; successful probe execution is not a production fix.

Fresh pure suite:

```sh
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
```

```text
12 codec tests + 8 packaging tests: all ok
Ran 20 tests in 0.054s
OK
```

Expected diagnostic lines report unknown `0x0` sections in two malformed/padding fixtures. They are not test failures. Lead's full Blender baseline is separately retained in [baseline log](baseline-blender.log), lines 725–726: `BLENDER_O3D_IO_SMOKE_OK 5.0.1`, build `a3db93c5b259`; it was inspected, not rerun or reattributed as this child's own smoke run.

Fresh self-review/verification script results before staging:

```text
JSON_OK: four evidence JSON records
HASH_RECHECK_OK: 13 bounded files (executable, reference3, Blender, fixtures3, retained exports5)
LOCAL_LINKS_OK: ledger and evidence readme
PRODUCTION_TESTS_DIFF_EMPTY
git diff --check: no output
Current HEAD: unchanged base
```

The explicit seven-file staged allowlist, final JSON/local-link/13-hash checks and `git diff --cached --check` all passed before committing: `FINAL_SELF_REVIEW_OK`. No unstaged/source/test changes were present. Postcommit identity and committed-path checks are reported to the lead/final response after the commit exists.

## Self-review and concerns

- Checked every Task 1 checkbox against an actual ledger section/evidence record, rather than assuming old findings still apply.
- Reviewed source anchors and local links, helper shapes and caller counts (6 prepared contexts, 3 geometry calls, 2 material-builder calls, 59 do_export calls). Corrected a relative external-evidence link during review.
- Inspected reference `meshio` and documented its wide `If` bone records as a trap not to copy. Retained native reader keeps fixed `Hf`; no top-four limit or parent/quaternion restrictions introduced.
- Kept imported power/name-preservation caveats explicit. Long-name import safety does not establish original-name byte-for-byte export; stored metadata is not automatically used by the collector.
- **Current reproducible concern:** outer `export_mesh` truncates existing output before empty-geometry codec refusal. The pure codec rejection test does not cover outer file publication. Reported to lead early; left unfixed because this is a research-only checkpoint.
- **Authoring-policy concerns:** emission strength is ignored in current builder and edit-active UV wins over render-active/material graph. Reference differences are not native correctness proofs.
- Existing files are not certified native fixtures; missing unpacked texture paths gate appearance comparisons. Only Blender 5.0.1 was executed; 4.2.0 remains the minimum requirement. Existing version metadata/smoke assertion still advertises 4.0.0 and was not modified.
- No independent reviewer was spawned because delegation depth is exhausted. Self-review is complete; lead review remains required. No shared board task was marked complete by this child.

## Unresolved gates

1. Native static normals/winding, cull/lighting state and vertex-buffer normal construction.
2. Native `0x79` matrix use in draw/animation-origin composition; general noncommuting global transforms.
3. Native embedded material/texture modulation and CFG override field precedence.
4. Explicit Blender shader/UV authoring subset and conversion policy, preserving imported fields.
5. Controlled byte/math fixtures, Blender 4.2/5.2 verification and separately authorized native runtime evidence.
6. Scope a later repair/test for existing-output protection on empty geometry.

Task 1 completion means the investigation checkpoint is ready for lead review, not that these later gates are solved. Keep board task `task-1` in_progress and do not edit the progress tracker.
