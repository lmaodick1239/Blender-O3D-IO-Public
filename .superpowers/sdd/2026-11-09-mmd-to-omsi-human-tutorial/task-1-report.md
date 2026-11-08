# Task 1 Report

## Status

DONE_WITH_CONCERNS

## Scope

Created the beginner-facing MMD-to-OMSI human tutorial from the approved design and supplied source notes. The tutorial covers the current Character Tools workflow, source preservation, material preparation, automatic/template rig choices, LODs, readiness gating, manual `.hum` authoring, canonical CFG bindings, installation, troubleshooting, limitations, and a final checklist. No production code was changed.

## Files Changed

- `docs/tutorials/mmd-to-omsi-human.md`
  - Added prerequisites and the verified Blender 5.0.1 workflow.
  - Documents the current panel labels, defaults, optional extras, LOD screen-size factors, readiness errors, and Selection Only export.
  - Includes a compact `aXYZ/man03.hum`-based template with the exact shipped values, all required sections, and exactly 22 `[links]` scalars.
  - Includes the exact 13 canonical `[setbone]` name/integer pairs and explains repeating them for every LOD.
  - Includes the relative `Humans` package layout, troubleshooting table, explicit limitations, and final checklist.
- `.superpowers/sdd/2026-11-09-mmd-to-omsi-human-tutorial/task-1-report.md`
  - Records this implementation and validation evidence.

## Source Fidelity Checks

- `[humangeom]`: `0.04`, `1.78`.
- `[seatheight]`: `0.90`.
- `[links]`: `0.09, 0.00, 0.92, 0.09, -0.03, 0.53, 0.02, 1.17, 0.18, -0.05, 1.43, 0.44, -0.04, 1.41, -0.02, 1.55, 0.69, -0.03, 1.43, 0.90, -0.03, 1.43`.
- `[walk_param]`: `1.4`, `80`, `1.0`, `1.0`, `0.0`.
- `[voice]`: `M2`.
- `[mass]`: `0.07` tonnes.
- CFG bindings: `OS_L -2`, `OS_R -3`, `US_L -4`, `US_R -5`, `OA_L -6`, `OA_R -7`, `UA_L -8`, `UA_R -9`, `Hip -10`, `Main -11`, `Head -12`, `Hand_L -13`, `Hand_R -14`.

## Validation

Commands/checks:

```bash
git diff --cached --check
```

Result: no whitespace errors.

The tutorial was also checked against:

- `docs/superpowers/specs/2026-11-09-mmd-to-omsi-human-tutorial-design.md`
- `.superpowers/sdd/human-tutorial-source-notes.md`
- `o3d_io/omsi_character_panel.py`
- `README.md` Character Tools workflow notes

The document contains all required sections, exact binding values, the 22-value links ordering, and no unresolved TODO/TBD placeholders. Production tests were not required because this task changes documentation only.

## Concerns

- The supplied `aXYZ/man03.hum` was read as CP1252 during source research. The tutorial recommends preserving the copied legacy encoding but does not claim that CP1252 is universal for every OMSI text file.
- OMSI in-game appearance, animation, seated pose, textures, and LOD switching still require user verification; no OMSI runtime test was performed for this documentation task.
- The tutorial intentionally uses shipped `man03` values as a tested starting point. Arbitrary Blender-to-`.hum` `[links]` conversion remains a manual measurement task.
