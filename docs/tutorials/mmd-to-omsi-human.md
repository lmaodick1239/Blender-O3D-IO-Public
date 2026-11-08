# Convert an MMD Character to an OMSI Human

This tutorial takes an MMD character imported into Blender and turns it into an OMSI human asset. It uses the current `OMSI > OMSI Character Tools` panel for the Blender part, then uses a copied shipped OMSI human as the starting point for the manual `.hum` file.

The workflow produces three different kinds of files:

- `.o3d` files contain exported meshes, vertex groups, and weights.
- `.cfg` is the model configuration written by Blender. It lists the `.o3d` meshes, LODs, materials, and `[setbone]` bindings.
- `.hum` is the human configuration edited separately. It points to the model `.cfg` and supplies human geometry, procedural joint pivots, walking defaults, voice, and mass.

The Character Tools panel does **not** write `.hum` files. Blender generates the `.o3d` and `.cfg`; you author the `.hum` from a shipped example.

## Before you start

You need:

- Blender **5.0.1** for the verified workflow in this repository. The add-on supports a wider Blender range, but this tutorial's smoke workflow was verified on 5.0.1.
- A current Blender-O3D-IO add-on installation, enabled in Blender.
- An MMD character and armature imported with `mmd_tools` or another MMD importer. `mmd_tools` is not required by the panel itself, but it is the expected source format for this walkthrough.
- OMSI 2, including an accessible `Humans` directory and a way to test the result in game.
- The character's image textures, in formats OMSI can load.

Make a separate working copy of the MMD source, its textures, and any reference OMSI human files before you begin. The default panel operations preserve the source, but a backup makes it possible to compare or repeat the conversion.

### The two jobs in this workflow

**Blender job:** prepare materials, convert the MMD armature and weights, optionally generate LODs, run readiness checks, and export a selected `.cfg` with its `.o3d` files.

**Manual OMSI job:** copy a shipped `.hum`, change its model path and human measurements, and make sure every exported LOD has the canonical human bindings in its CFG.

An exported armature does not serialize a Blender hierarchy, rest matrices, animation clips, or human joint pivots. OMSI obtains the human's procedural pivots from `[links]` in the `.hum` file.

## Part 1: Prepare the Blender source

1. Start Blender and import the MMD mesh and its armature.
2. Select the character mesh and inspect its Armature modifier. Confirm that it points to the imported MMD armature.
3. Apply the intended object scale before conversion. A character with unapplied or incorrect scale can produce proportions that do not match its measurements in the `.hum` file.
4. Check that the base images are available. Missing MMD toon images such as `toon02.bmp` can make a correct character appear magenta in Blender.
5. Keep the original MMD mesh and armature in the scene until the converted output has passed export and in-game checks.

## Part 2: Open Character Tools

Open the 3D View sidebar with `N`, then choose **OMSI > OMSI Character Tools**. If selection does not fill the source fields, set **Source Mesh** and **Source Armature** explicitly in the panel.

### Repair the materials first

With the character mesh selected:

1. Click **Reset MMD Toon Factor**. This sets the MMD toon contribution to zero; the default sphere reset is enabled as well. This prevents a missing toon image from contributing magenta shading.
2. Click **Flatten MMD Materials**. The panel creates exportable Principled materials while retaining the base image and UV mapping.
3. Leave **Apply to every material in the file** disabled unless you deliberately want to edit materials outside this character. The normal action creates private working copies and preserves the originals.
4. Confirm that the working mesh has a Principled BSDF with the intended base image. The exporter does not export arbitrary MMD shader graphs as OMSI materials.

Repeating a material operation after there is nothing left to change should not create another working copy. Do not assume that a packed image is automatically an installable OMSI texture; arrange real texture files in the final package yourself.

### Convert the rig

In **Convert to OMSI Armature**:

1. Set **Source Mesh** and **Source Armature** to the MMD character.
2. Choose **Auto from MMD joints** for a normal first conversion. This builds the canonical OMSI human rig from the source joint positions.
3. Choose **Copy template** only when you already have an OMSI-compatible template armature selected. In template mode, the panel copies the template's bone set and rest geometry; it does not turn arbitrary extra bones into human transform slots.
4. Keep **Max Influences** at its default of `4` for this beginner workflow. The panel merges mapped weights and normalizes them.
5. Leave **Remove shape keys** enabled when you intend to generate LODs. Shape keys prevent the decimation operation used for reduced LODs. Removing them is done on the converted working data, not the preserved source.
6. Leave **Keep unmapped MMD bones as extras** disabled for the first conversion. Enable it only when you understand that extra bones receive ASCII names but remain unbound in a human CFG unless you add suitable bindings yourself.
7. Leave **Delete the source MMD armature** disabled. Preserve the source until the complete package works.
8. Keep the default target collection, `OMSI_Converted`, unless your project has an established alternative.
9. Click **Convert to OMSI Armature** and inspect the selected output. The source and the converted mesh should remain separate.

The conversion ignores MMD bookkeeping groups such as `mmd_edge_scale` and `mmd_vertex_order`, maps supported MMD names to canonical OMSI names, merges unmapped weights by proximity when extras are disabled, and normalizes the resulting weights. It does not convert MMD physics, IK, morph targets, or animation actions.

### Generate LODs (optional)

In **Mesh LODs**, the defaults are:

- **LOD Count:** `3` total levels, including the full-detail source.
- **Reduced Ratios:** `0.5 / 0.25`.
- **LOD Factors:** `0.2 / 0.1 / 0`.

LOD factors are minimum screen-size values, not distances in metres. They must descend strictly and end in zero. Each generated mesh belongs to its matching collection, such as `LOD_0.2`, `LOD_0.1`, or `LOD_0`.

For a simpler first test, use one level with factor `0`; there is no requirement to invent a middle level. For two levels, use factors `0.2 / 0` and one reduced ratio. Select the converted character, keep old reduced levels deselected, and click **Generate LODs**. The source remains the full-detail level.

## Part 3: Check readiness and export

Click **Check Export Readiness** before exporting. Readiness checks are read-only, but they are a gate: fix every reported `ERROR` before export. Resolve warnings that describe content you did not intentionally choose.

Typical findings include:

- bone names that cannot be encoded in CP1252 or exceed OMSI's name limits;
- MMD helper groups still present;
- weights that do not sum to 1.0;
- missing unpacked image files;
- remaining shape keys;
- MMD shader nodes that were not flattened;
- unbound arbitrary extra bones;
- too many serialized skinned vertices or an unsafe dominant bone index;
- unsafe or colliding export paths.

Then:

1. Select the converted mesh, or the complete generated LOD family.
2. Choose **File > Export > OMSI Model Config**.
3. Export to a new package's `model` directory as a `.cfg` file.
4. Enable **Selection Only**. This prevents preserved MMD sources and intermediate working copies from entering the export.
5. Confirm that the generated CFG references every intended `.o3d` and that each file exists beside it.

Blender's export success proves that the files were serialized. It does not prove that OMSI will animate or display the character correctly; that requires the installation and in-game checks later in this tutorial.

## Part 4: Create the `.hum` file manually

Start from the shipped pedestrian example:

```text
OMSI 2\Humans\aXYZ\man03.hum
```

Copy it into your own package and preserve the copied file's legacy Windows-compatible encoding. The supplied file was read successfully as CP1252; that is a safe choice for this shipped template, not a claim that every OMSI text file has one universal encoding. ASCII names and values are the safest choices for new content.

Use OMSI-style backslashes in relative paths. Do not change `model\...` to a filesystem path with a drive letter, and do not add a leading slash. The `[model]` path is relative to the directory containing the `.hum`.

The following is a compact working template based on `Humans/aXYZ/man03.hum`. It uses the concrete working names `mmd_human.cfg`, `mmd_human.o3d`, and `mmd_human_low.o3d`; make those names match the files you actually exported. Keep only the real numeric blocks below. The explanatory labels that appear before the real values in the shipped file are comments/templates, not extra input lines.

```text
[model]
model\mmd_human.cfg

[seatheight]
0.90

[humangeom]
0.04
1.78

[links]
0.09
0.00
0.92
0.09
-0.03
0.53
0.02
1.17
0.18
-0.05
1.43
0.44
-0.04
1.41
-0.02
1.55
0.69
-0.03
1.43
0.90
-0.03
1.43

[walk_param]
1.4
80
1.0
1.0
0.0

[voice]
M2

[mass]
0.07
```

### What to change in the template

- `[model]`: change `model\mmd_human.cfg` to the relative path of your exported model CFG.
- `[seatheight]`: begin with the shipped `0.90` value. It is used by seated-pose construction; do not treat it as a vehicle seat coordinate or assume it rescales all other geometry.
- `[humangeom]`: the two values are `feetdist` (`0.04` in the shipped example) and height (`1.78`). Start with measurements appropriate to the converted character and verify them in OMSI.
- `[walk_param]`: the shipped values are `1.4`, `80`, `1.0`, `1.0`, `0.0`, in the order shown. The shipped explanatory comment gives `66` as the default for `upper_arm_beta`, but the actual example is `80`; preserve that distinction.
- `[voice]`: `M2` is the voice token used by the shipped pedestrian example. The inspected files establish `M2` and `M4` as examples, not a complete voice catalogue.
- `[mass]`: the value is mass in tonnes. `0.07` means 70 kg; a shipped 90 kg comparison human uses `0.09`.

### The 22-value `[links]` block

`[links]` contains exactly **22 scalar values** in this order:

| Positions | Field labels in the shipped template |
| --- | --- |
| 1-3 | `x_hip`, `y_hip`, `z_hip` |
| 4-6 | `x_knee`, `y_knee`, `z_knee` |
| 7-8 | `y_waist`, `z_waist` |
| 9-11 | `x_shoulder`, `y_shoulder`, `z_shoulder` |
| 12-14 | `x_elbow`, `y_elbow`, `z_elbow` |
| 15-16 | `y_neck`, `z_neck` |
| 17-19 | `x_hand (carpus)`, `y_hand (carpus)`, `z_hand (carpus)` |
| 20-22 | `x_finger`, `y_finger`, `z_finger` |

The count is `3 + 3 + 2 + 3 + 3 + 2 + 3 + 3 = 22`. Waist and neck intentionally have **no X input line**. Do not insert one: doing so shifts every later value and corrupts the configuration. Do not add values for finger joints or turn this block into a list of the 13 bone names.

The values are procedural joint/pivot geometry used by OMSI's human pose code. They are not Blender bone serialization, animation keyframes, or a replacement for CFG `[setbone]` bindings. The engine stores an internal coordinate layout, but the input file order remains the labeled `x, y, z` order above; do not swap Y and Z because of that implementation detail.

For a first pass, use the shipped values and test the character. To adapt them, measure corresponding hip, knee, waist, shoulder, elbow, neck, carpus, and finger locations in the converted character using a consistent coordinate convention, then change only the documented positions. There is no verified automatic conversion from arbitrary Blender joint coordinates to these 22 values, and changing `[humangeom]` height alone is not established as a universal rescale for `[links]`.

The shipped `man03.hum` places `[voice]` before `[walk_param]`; the inspected driver comparison places those two blocks in the opposite order. Keep the complete blocks and their values together. Do not infer that every `.hum` must use one global section order beyond the concrete shipped pattern you copied.

## Part 5: Check the model CFG bindings

The human CFG binds exported group names to OMSI's 13 human transform slots. Names are case-sensitive. For the standard human rig, use this exact table:

| O3D bone/group name | CFG integer |
| --- | ---: |
| `OS_L` | `-2` |
| `OS_R` | `-3` |
| `US_L` | `-4` |
| `US_R` | `-5` |
| `OA_L` | `-6` |
| `OA_R` | `-7` |
| `UA_L` | `-8` |
| `UA_R` | `-9` |
| `Hip` | `-10` |
| `Main` | `-11` |
| `Head` | `-12` |
| `Hand_L` | `-13` |
| `Hand_R` | `-14` |

A binding is written as two lines after `[setbone]`, for example:

```text
[setbone]
OS_L
-2
```

The shipped `model\man03.cfg` has two LOD blocks:

```text
[LOD]
0.2

[mesh]
man03.o3d

...the 13 [setbone] blocks...

[LOD]
0

[mesh]
man03_low.o3d

...the same 13 [setbone] blocks again...
```

Repeat the bindings for **every exported LOD**, not only the first mesh. Replace the mesh filenames with the names in your generated CFG, but keep each binding name and integer exact. A bone/group renamed from `Hand_L` to `hand_l`, or a binding copied into only one LOD, can leave that part of the human unbound. The panel emits bindings for canonical names present in the final rig; a human intended to use all 13 slots should retain all 13 canonical groups through conversion and export.

Do not invent `[setbone]` integers for arbitrary extra MMD bones. Extra bones can exist in an O3D, but they do not acquire a human transform slot merely because they have a Blender parent. Human motion still depends on the canonical CFG slots and the `.hum` pivots.

## Part 6: Install the package

Use a separate directory under OMSI's `Humans` folder. For example:

```text
OMSI 2\Humans\mmd_to_omsi\
  mmd_to_omsi.hum
  model\
    mmd_human.cfg
    mmd_human.o3d
    mmd_human_low.o3d
  texture\
    mmd_body.bmp
    mmd_face.tga
```

The relationship is:

```text
mmd_to_omsi.hum
  [model] model\mmd_human.cfg
    [mesh] mmd_human.o3d       -> model\mmd_human.o3d
    [mesh] mmd_human_low.o3d   -> model\mmd_human_low.o3d
    texture references          -> texture\...
```

The CFG mesh filenames are relative to the `model` directory. Texture assets used by the CFG are placed in the package's sibling `texture` tree, with paths and case matching the references. Copy the `.hum`, CFG, every referenced `.o3d`, and every required texture together. Do not overwrite the shipped source human while learning.

Start OMSI and test the installed human in a controlled situation. Check the standing appearance, walking pose, seated pose, hands, joints, textures, and each LOD. Blender validation and a successful file export are necessary but are not in-game verification.

## Troubleshooting

| Symptom | Checks and fixes |
| --- | --- |
| `model` or `.o3d` file is missing | Open the `.hum` and CFG as text. Confirm `[model]` points to `model\mmd_human.cfg`, each `[mesh]` filename exists under `model`, and the spelling/case matches. Re-export with Selection Only if a file was never written. |
| OMSI cannot find the model after moving the package | Use package-relative OMSI backslashes. Remove drive letters, absolute paths, and leading slashes. Keep the `.hum` beside `model` and `texture`. |
| CP1252 or bone-name export error | Run **Check Export Readiness**. Rename non-CP1252 MMD groups to stable ASCII names or let conversion map them to canonical names. Do not leave Japanese or other unsupported names in the final bound groups. Preserve the copied `.hum` encoding. |
| Magenta or missing textures | Reset the MMD toon factor, flatten MMD materials, verify the base image, and copy the real image file into the package's `texture` directory. A packed/generated Blender image still needs an installable OMSI file. |
| A limb does not move or moves rigidly | Compare the exported group name and CFG binding character-for-character with the canonical table. Confirm that the binding is repeated in every LOD block. Run readiness checks for unbound extras. |
| Character is too tall, short, or distorted | Apply Blender object scale before conversion. Recheck `[humangeom]` height and the measured `[links]` positions together. Do not assume height alone rescales the pivot geometry; verify standing and seated poses in OMSI. |
| LOD disappears or switches incorrectly | Confirm factors descend to a final `0`, each factor is a screen-size value, each `[mesh]` exists, and each LOD repeats all required bindings. A two-level `0.2 / 0` setup is valid; do not add an arbitrary middle level. |
| Blender export passes but OMSI animation is wrong | Separate the two validation stages. Blender checks serialization and panel limits; OMSI must still resolve the `.hum`, load the CFG and textures, construct procedural pivots, and animate the human. Inspect all poses and LODs in game. |

## Limitations

- The Character Tools panel does not generate `.hum` files.
- The panel does not convert MMD physics, IK, morph targets, or morph animation.
- The panel does not guarantee that a Blender action or animation clip becomes OMSI human animation. The `.hum` procedural settings and OMSI runtime provide the human motion path.
- Blender armature parenting, bone hierarchy, rest geometry, and exported O3D data do not supply the human `[links]` pivots.
- The exact `[links]` conversion for arbitrary Blender proportions is not automated or established by this tutorial. The supplied pivots are a practical starting point that must be tested.
- `M2` and `M4` are observed voice identifiers, not a complete voice catalogue or a guarantee that every identifier is available in every installation.
- The inspected pedestrian and driver examples show concrete section orders and values; they do not prove a universal grammar, universal optionality, all repaint semantics, or a complete driver-registration workflow.
- Runtime evidence and the generated CFG/O3D path were verified with Blender 5.0.1. OMSI in-game appearance and animation require user testing.

## Final checklist

- [ ] The MMD source and textures are backed up.
- [ ] Blender scale is applied and the mesh has the intended Armature modifier.
- [ ] MMD toon input is reset and materials are flattened to exportable Principled materials.
- [ ] Conversion uses the intended auto or template rig mode, with normalized weights and no unresolved readiness errors.
- [ ] LOD factors descend to zero, and every intended LOD has a real `.o3d` file.
- [ ] Bone names are CP1252-safe and the 13 canonical names use the exact case shown above.
- [ ] The `.hum` uses a preserved legacy encoding, OMSI backslashes, all required sections, and exactly 22 `[links]` values.
- [ ] `[model]` points to the installed CFG, and CFG `[mesh]` paths point to existing files.
- [ ] Every LOD repeats the canonical `[setbone]` bindings.
- [ ] The `.hum`, CFG, O3Ds, and textures are copied into one OMSI Humans-style package.
- [ ] OMSI has been tested for textures, standing/walking/seated poses, hands, joints, and all LODs.
