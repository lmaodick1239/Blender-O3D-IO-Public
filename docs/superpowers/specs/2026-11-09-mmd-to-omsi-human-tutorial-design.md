# MMD to OMSI Human Tutorial Design

## Purpose

Create a beginner-facing Markdown tutorial for converting an MMD character imported into Blender with `mmd_tools` into an OMSI human asset using the add-on's current `OMSI > Character Tools` panel, then authoring the required `.hum` configuration from a shipped OMSI example.

## Audience and Assumptions

The reader is new to OMSI human assets and Blender export workflows. They have Blender 5.0.1 or a compatible supported version, the add-on enabled, an MMD character and armature imported through `mmd_tools`, and access to an OMSI 2 installation. The tutorial must explain terminology before asking the reader to use it.

## Tutorial Flow

1. Explain the output files and the division of responsibility:
   - Blender produces the converted mesh, `.o3d` files, and `.cfg` bindings.
   - The `.hum` file supplies the human model reference, body dimensions, procedural joint pivots, walking defaults, voice, and mass.
2. Prepare the MMD source, including applying scale, selecting the mesh, and checking the armature modifier.
3. Use the MMD material tools to reset missing toon inputs and flatten materials to an exportable Principled setup.
4. Use the conversion panel with beginner-safe defaults, explaining automatic versus template rig mode, maximum influences, shape-key removal, extra bones, and source preservation.
5. Generate optional LODs and explain that LOD factors are screen-size values.
6. Run readiness checks and resolve CP1252 bone names, helper groups, missing images, shape keys, weight normalization, and runtime-limit errors.
7. Export a selected converted character to a safe relative output directory and verify the `.cfg` references every `.o3d` file.
8. Create a `.hum` by copying the shipped `Humans/aXYZ/man03.hum` pattern. Explain exact relative path syntax and the following sections:
   - `[model]`
   - `[seatheight]`
   - `[humangeom]`
   - `[links]` with 22 scalar values and the shipped comments explaining omitted X inputs
   - `[walk_param]`
   - `[voice]`
   - `[mass]`
9. Explain that the shipped `model/man03.cfg` repeats the 13 canonical `[setbone]` bindings for each LOD and that these names must match the O3D bone groups exactly.
10. Install the asset under an OMSI Humans-style directory and troubleshoot path, encoding, missing texture, model, skeleton, and proportions problems.

## Source-Grounded Values

Use the supplied OMSI files as primary examples:

- `Humans/aXYZ/man03.hum` for the complete human configuration and 22-value `[links]` block.
- `Humans/aXYZ/model/man03.cfg` for two LOD entries and the canonical bindings `OS_L -2`, `OS_R -3`, `US_L -4`, `US_R -5`, `OA_L -6`, `OA_R -7`, `UA_L -8`, `UA_R -9`, `Hip -10`, `Main -11`, `Head -12`, `Hand_L -13`, and `Hand_R -14`.
- `Humans/bcoy_driver/man05.hum` and `model/man05.cfg` as a comparison showing that human `.hum` and CFG section order can vary while the same binding pattern remains.

Explain that `.hum` files in the supplied installation use a Windows-compatible legacy text encoding; recommend preserving the encoding of the copied template and using OMSI-style backslashes for relative paths. Do not claim that Blender bones or `.o3d` files provide the procedural human pivots; the `[links]` section remains a manual `.hum` concern.

## Explicit Limitations

The tutorial must state that the panel does not write `.hum` files, convert MMD physics/morph animation, or guarantee in-game animation from a Blender action. The generated CFG/O3D path is verified with the repository's Blender 5.0.1 smoke workflow; OMSI in-game appearance and animation require user testing.

## Verification

Before presenting the tutorial, check every command, filename, section name, numeric binding, and path example against the source notes and shipped files. Ensure the Markdown has no placeholders, no unsupported claims, and includes a concise final checklist.
