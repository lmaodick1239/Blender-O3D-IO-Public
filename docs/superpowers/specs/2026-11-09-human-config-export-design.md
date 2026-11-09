# Rig-Derived OMSI Human Configuration Export

## Status and Goal

Design direction approved on 2026-11-09: add opt-in human configuration generation to armature-backed model export. Derive geometry from rest-space skeletal landmarks, keep non-geometric human settings editable, and treat MMD physics as optional diagnostic evidence rather than anatomical pivots.

The written specification requires user review before implementation planning. No exporter behavior changes are included in this documentation step.

## Scope

Add a **Human Configuration & Export** section directly to the existing **OMSI > OMSI Character Tools** sidebar panel. It contains the measurement controls, editable human settings, readiness feedback, and an **Export Human** button producing a `.hum` file, a model `.cfg`, and its `.o3d` meshes. This is a panel-led workflow, not a feature hidden behind a File > Export checkbox. Normal CFG/SCO/O3D export remains unchanged; the generic file-browser operator does not need a new human-generation toggle.

The first version supports one canonical OMSI human armature and its mesh/LOD family per export. It does not automatically convert an arbitrary MMD rig during export. Users convert the source with Character Tools first, inspect measurements, then export the converted character.

Non-goals: exporting Bullet/MMD physics, adding procedural hair or cloth behavior, baking Blender actions into OMSI animation, inventing slots for extra bones, estimating human mass from collider masses, or adding a generalized configuration-template framework.

## Existing Integration Points

- `__init__.py::ExportModelCFG` remains the existing generic file-browser exporter; the new panel action reuses its backend rather than requiring changes to that operator's UI.
- `o3d_io/io_o3d_export.py::do_export` resolves output meshes, validates destinations, exports evaluated rest geometry, and passes serialized metadata to the existing CFG writer.
- `o3d_io/o3d_cfg_parser.py` already writes mesh/material/LOD blocks and `[smoothskin]` metadata.
- `o3d_io/mmd_rig.py::reconcile_character_bindings` establishes the 13 canonical `[setbone]` bindings during conversion.
- `o3d_io/mmd_rig.py::_canonical_points` simplifies source joints into a 13-bone rig. This can discard a distinct neck landmark and replace the real hand/finger extent with a synthesized tail.
- `o3d_io/omsi_character_panel.py` is the existing home for conversion, readiness checks, and character-specific controls.

Reuse these paths. Add one focused human-measurement/configuration module rather than another geometry exporter or a parallel model CFG implementation.

## Evidence From the Supplied Scene

`tests/Untitled2.blend` was opened read-only with Blender 5.0.1 and auto-execution disabled. The inspected scene contains one 319-bone MMD armature, one character mesh with 11,937 vertices, 51 rigid bodies, and 34 rigid-body constraints.

- The 34 constraints are 19 skirt joints, 14 hair joints, and one accessory joint. None is a hip, knee, shoulder, elbow, wrist, or neck constraint.
- Anatomical collider objects contain native `CHILD_OF` constraints targeting named armature bones. These associations can be inspected without loading `mmd_tools`.
- Collider centers are offset from bone joints. For example, the left upper-arm collider center is approximately `(0.21732, 0.05468, 1.48654)`, while the left upper-arm bone head is `(0.10794, 0.06090, 1.48773)`.
- Rigid-body masses sum to 613 in Blender's mass values; several hair colliders individually use 30. These are simulation settings, not a suitable human mass estimate.
- The source includes separate neck and finger landmarks: `首`, `手首.L/R`, and finger roots such as `中指１.L/R`. Preserve useful source landmarks before conversion simplifies the rig.
- The character mesh world-space bounds are approximately `(-0.76754, -0.28629, 0.00686)` to `(0.76754, 0.42234, 1.86217)`. Physics helpers must not contribute to measured body bounds.

The sample is an integration fixture, not a requirement that every model contain physics or use these object names. Tests must not modify or resave it.

## User Workflow and Output Paths

1. Convert an MMD source using Character Tools, or select an existing compatible OMSI rig in the panel's existing source fields.
2. Open **Human Configuration & Export**, placed after **Mesh LODs** in the same sidebar. Display the target armature clearly so the user can see which character owns the settings.
3. Click **Refresh Measurements**, inspect the derived geometry, and resolve missing/ambiguous landmark feedback with numeric overrides. Refreshing must not overwrite user overrides.
4. Edit voice, mass in kilograms, seat height, feet distance, and height override in the section. Keep detailed landmark overrides and walking parameters in collapsible advanced groups rather than displaying all 22 numbers by default.
5. Run **Check Export Readiness** from this section, then click **Export Human**. The button opens a destination picker for a `.hum` file and invokes the shared geometry/CFG backend with the panel's human settings.
6. Inspect the generated file references, then perform the OMSI installation and in-game checks. No separate File > Export visit is required.

Use a dedicated panel export operator accepting `.hum` destinations; this does not turn ordinary `.o3d` or `.sco` exports into human exports. Reuse the existing backend for mesh serialization, model CFG writing, safe paths, and scale handling rather than duplicating those implementations.

For a chosen destination `character.hum`, write the sibling `character.cfg` and its referenced meshes in the same directory; the HUM uses `character.cfg` as its relative `[model]` reference. This deterministic sibling layout avoids guessing whether the chosen directory is a package root or a `model` directory. Explain that the generated files must be kept together when installing this layout. A separate package-layout wizard is outside scope.

Panel drawing must not perform conversion, mutate measurements, or repeatedly evaluate export geometry. Refresh/readiness/export actions perform that work explicitly and display their findings. Disable Export Human when no compatible target is available, and repeat full validation when the operator executes rather than relying only on disabled UI state.

When Selection Only is enabled, explicitly selected character meshes retain the existing selection scope. If only the canonical armature is selected, include the exportable meshes bound to that armature. Never expand selection to unrelated scene meshes or a preserved source rig. Reject empty character exports and multiple distinct character armatures rather than guessing which human to configure.

## Measurement Data and Ownership

Store human export settings and override values on the converted armature, not as one global scene-level character. They must survive saving/reopening the `.blend` and remain associated with the correct rig and LOD family.

In automatic MMD conversion, preserve source anatomical landmarks as compact, versioned armature-local rest-space metadata expressed relative to the resulting rig. Capture the source neck joint and actual finger-root points before the source can be deleted. In Copy Template mode, copy compatible landmark metadata from the target template; do not transplant raw source neck/finger coordinates into a different target rest shape. If the template lacks those points, require explicit overrides. Landmark metadata is measurements, not a copy of the source rig or a live dependency on it.

Use canonical rest bones for points directly represented by the converted rig. Use preserved source landmarks for geometry that the 13-bone rig does not faithfully retain. Numeric user overrides take precedence. Do not continue consulting the original source rig after conversion, and do not silently use arbitrary bone tails for missing anatomy.

For existing canonical rigs without preserved metadata, derive the unambiguous canonical joints and identify exactly which measurements require explicit overrides. Missing essential inputs may be reported as warnings during inspection, but must block human file generation until resolved. Generic mesh export remains available.

Changing the rig after measurement capture must make source-derived measurements visibly stale. **Refresh Measurements** re-reads available rest bones; source-only points that can no longer be refreshed require confirmation or replacement as overrides. Do not silently promise that old captured coordinates track later armature edits.

## Geometry Contract

Measure in rest space, independent of the current pose, animation frame, or physics simulation. Transform bone points and preserved landmarks into the same final model coordinate frame as the exported mesh, including object transforms and export scale exactly once. Blender display-unit settings are not an additional multiplier when the existing mesh exporter does not apply them.

Keep the `.hum` file's documented input ordering separate from the O3D/native internal axis layout. The measurement adapter must have a golden fixture establishing its coordinate correspondence with final exported model geometry; do not copy the O3D Y/Z swap blindly into `[links]` serialization. This is a required implementation verification step, not permission to choose an unverified sign or axis convention.

Support finite, nonsingular, uniformly scaled character transforms that preserve the human frame: upright, facing the expected model forward direction, with the anatomical centerline on X = 0. Validate that alignment against rest landmarks; object transform values alone are not proof of correct alignment. Reject incompatible alignment and mirrored, sheared, or nonuniformly scaled human transforms with an actionable message in the first version. Do not impose these new restrictions on ordinary export.

Do not reposition, apply transforms to, or otherwise mutate source meshes or rigs during export. Warn about a character whose feet are not near its intended ground plane; do not silently translate it to the ground.

### Landmark Sources

| Human landmark | Preferred rest-space source |
| --- | --- |
| Hip pair | `OS_L` and `OS_R` heads |
| Knee pair | `US_L` and `US_R` heads |
| Waist | Canonical `Main` root/pivot, with explicit override available |
| Shoulder pair | `OA_L` and `OA_R` heads |
| Elbow pair | `UA_L` and `UA_R` heads |
| Neck | Preserved source neck landmark or explicit override; do not assume an arbitrary `Head` head is the neck |
| Carpus/hand pair | `Hand_L` and `Hand_R` heads |
| Finger pair | Preserved middle-finger root landmarks or explicit overrides; never the synthesized hand tail |

The source mapping must distinguish real anatomical MMD bones from dummy, shadow, twist, IK, and collider helper bones. Reuse existing naming rules where they identify the correct joint, but do not let a broader helper-name match win merely because it appears first.

OMSI's human links describe a mirrored pair rather than independently configurable left/right anatomy. Produce each paired point from mean absolute X distance and mean Y/Z of the two measured sides in the shared human frame. Check that the pair lies on opposite sides of the centerline. Report a symmetry warning if the mirrored discrepancy exceeds the greater of 0.01 model metres or 1% of measured height, and display that export uses a symmetric approximation. Waist and neck supply only Y and Z; report off-center source points rather than silently pretending the file can preserve their X coordinates.

Determine height from evaluated rest geometry of the primary full-detail character meshes, excluding colliders, constraints, unrelated objects, and duplicate reduced LODs. Report the measured height and let the user override it. Do not infer feet distance or seated posture merely from character height.

## Human File Format and Editable Defaults

Write Windows-compatible CP1252 text with CRLF line endings and finite locale-independent numeric values. Validate encodability before creating outputs. Use relative OMSI-style paths; do not write absolute installation paths.

Emit the following blocks in this deterministic order:

1. `[model]`: the exported sibling CFG filename.
2. `[seatheight]`: editable default `0.90`.
3. `[humangeom]`: editable feet distance default `0.04`, followed by measured/overridden height.
4. `[links]`: exactly 22 measured/overridden scalar values.
5. `[walk_param]`: editable defaults `1.4`, `80`, `1.0`, `1.0`, `0.0`.
6. `[voice]`: editable default `M2`, without claiming this is a complete voice catalogue.
7. `[mass]`: expose mass as kilograms in the UI, default 70; serialize tonnes, default `0.07`.

These non-geometric defaults come from the shipped `man03.hum` example documented in `docs/tutorials/mmd-to-omsi-human.md`. They are explicit starting values, not predictions from the mesh or physics simulation.

The 22 link values are, in order:

- Hip: X, Y, Z.
- Knee: X, Y, Z.
- Waist: Y, Z.
- Shoulder: X, Y, Z.
- Elbow: X, Y, Z.
- Neck: Y, Z.
- Carpus/hand: X, Y, Z.
- Finger: X, Y, Z.

No extra X values for waist or neck, and no additional values for individual finger joints. Generated comments must not resemble active configuration blocks or become numeric input lines.

## Model CFG and Physics Handling

Reuse the existing CFG writer and serialized bone/smoothskin metadata. Every exported human mesh/LOD must have canonical bindings for its actually serialized canonical bone names and the correct `[smoothskin]` state. Preserve unrelated mesh/material commands. Do not permanently mutate source ID properties or create duplicate conflicting bindings during export.

Exclude objects with a rigid body or rigid-body constraint from the human model candidate set, including selection expansion, bounds measurement, and human-mode CFG writing. Report excluded selected helpers clearly. Generic export remains unaffected so an intentionally exported rigid-body mesh is not globally prohibited.

Physics diagnostics are optional and read-only:

- Resolve explicit native constraint targets or equivalent available MMD bone metadata to report a collider's associated bone.
- Do not require `mmd_tools` to be installed.
- Do not infer an anatomical pivot from a collider center, capsule endpoint, nearest object, or arbitrary hair/skirt joint.
- Do not export collider shapes, springs, collision groups, damping, or mass into the human configuration.
- Missing physics is normal and must not produce an export failure.

## Validation and Failure Behavior

Preflight the complete human export before opening output files: one supported rig, nonempty intended mesh set, usable landmarks/overrides, finite geometry/settings, supported transforms/alignment, encodable text, safe destinations, and matching serialized skin bindings. Require positive height and mass, nonnegative seat height and feet distance, and a nonempty single-line voice token. Reject control characters and configuration-line injection in user-supplied string/path fields. Walk settings remain editable numeric values; do not invent undocumented engine ranges.

Validate every generated path through the existing safe-path logic. Detect case-insensitive and resolved-path collisions among HUM, CFG, and O3D destinations. Existing outputs require explicit overwrite consent covering the generated file set, not just Blender's confirmation for the selected HUM destination. Without consent, cancel before overwriting any member of the export.

Generate and validate human text before mesh serialization, then write the HUM only after successful model CFG/O3D export. A failed model export must not publish a new HUM pointing at failed output. Do not claim an all-or-nothing multi-file transaction; existing exporter write failures can still leave model files that need retrying. Error messages must distinguish preflight refusal from an I/O failure and identify the affected path.

No automatic zero-valued placeholders, copied stock joint geometry, hidden collider-based fallbacks, or changes to the user's original pose/selection/physics state.

## Verification and Acceptance Criteria

Use the existing assertion-based test and Blender smoke-test conventions; do not add a new testing framework or runtime dependency.

Required checks:

- The existing generic CFG/SCO/O3D operator retains its behavior and smoke checks; human generation is reached from the Character Tools panel without a new generic export toggle.
- The Human Configuration & Export child panel displays settings and readiness feedback, invokes the dedicated Export Human action, and performs no measurement/export work merely by drawing.
- A synthetic canonical rig with known anatomical metadata produces the expected 22-value link block and relative model reference.
- A golden coordinate fixture compares human landmark output with corresponding exported rest-geometry coordinates, including nonzero Y/Z and nonidentity supported transforms.
- Export scale applies once; display units do not introduce a second scale factor; current pose/frame does not change the result.
- Source conversion preserves real neck/finger landmarks even when source deletion is enabled; metadata/settings survive save/reload.
- Missing landmarks are identified and block human generation unless overridden; stale and asymmetric measurements are visible.
- Multiple rigs, singular/mirrored/sheared/nonuniform transforms, invalid numbers, unsafe/colliding paths, and unencodable text fail before output creation.
- Every generated mesh/LOD references an existing O3D and receives matching canonical bindings and smoothskin state without persistent source-property mutation.
- Rigid bodies and joint helpers are excluded from human meshes/CFG/bounds, while a physics-free character works normally.
- A read-only integration probe of `tests/Untitled2.blend` recognizes explicit collider-to-bone links and classifies its 34 secondary joints without treating them as anatomical pivots or resaving the fixture.
- Sidecar overwrite refusal preserves existing files, and model export failure does not write a new HUM.
- UI registration/unregistration remains clean; a cancelled/failed export restores normal UI cursor and temporary export state.

Update the human tutorial and README only when the feature is implemented and verified, replacing the current manual-only explanation with the opt-in workflow and its limitations.

Static and Blender checks establish configuration structure and coordinate consistency, not in-game animation correctness. OMSI loading, standing/walking/seated poses, turn behavior, and LOD transitions remain an explicit manual acceptance checklist. Do not describe the generated character as in-game validated until those checks have actually been performed.
