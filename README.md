# Blender-O3D-IO

[En Français](README-FR.md) (Merci à [@boingtheboeing](https://github.com/boingtheboeing) pour la traduction)

A Blender add-on for importing and exporting OMSI 2 files: `.map`, `.cfg`, `.sco`, and `.o3d`.

## Blender 4.x and 5.x support

Version 1.3.4 works with Blender 4.0 through Blender 5.2 (tested on Blender 5.2 LTS). It uses the current Blender APIs for custom normals, Principled BSDF materials, material transparency, and multi-file selection, while still working with older files.

Map and tile import builds its materials using the shader setup of whatever Blender version is running, so terrain and map-preview materials work on 4.0 and newer (where the Principled BSDF sockets changed names).

**Installing:**
- **Blender 4.2 – 5.2:** Go to `Edit > Preferences > Get Extensions > Install from Disk` and select the ZIP file itself (not the folder it's in).
- **Blender 4.0 / 4.1:** Use the legacy add-on installer via the repository ZIP.

**Note:** The optional private `o3d_crypto.py` module is not included in this repository. You only need it to open encrypted O3D files — normal importing and exporting works without it.

![Blender-O3D-IO-Screenshot](https://user-images.githubusercontent.com/15130114/208222029-5f9c2eb7-1007-4c38-a06a-0f3214d0a2f6.png)

## Features

The add-on gives you a fast O3D importer/exporter with full support for the format. For complex models, `.cfg` and `.sco` files can also be imported and exported. OMSI map tiles (`.map` files) can be imported too.

### O3D files — fully supported

- Explicit vertex normals
- Long headers (version 3 and up)
- Encryption (needs the private `o3d_crypto.py` module)
- Long triangle indices
- Alternative encryption seed
- Embedded materials
- Bones
- UV coordinates

### CFG/SCO files — many features supported

- LODs
- Advanced material features, both importing and exporting:
  - `[matl]`
  - `[matl_alpha]`
  - `[matl_transmap]`
  - `[matl_envmap]` & `[matl_envmap_mask]`
  - `[matl_bumpmap]` (Blender 2.80 and newer only!)
  - `[matl_nightmap]` & `[matl_lightmap]`
  - ... and more
- Interior lights and spotlights
- Lens flares (`[light_enh]` and `[light_enh_2]`)
- Imports all referenced models (o3d files only) and textures in the CFG/SCO as separate objects
- Imports `.x` files if a compatible importer is installed (https://github.com/Poikilos/io_import_x)

### Map tiles — work in progress

- Imports referenced scenery objects
- Imports terrain tiles and materials
- Imports splines and converts them to meshes

## Installation

1. Download the latest release from the [releases page](https://github.com/space928/Blender-O3D-IO-Public/releases/latest) — it will look like `Blender-O3D-IO-Public-0.2.3.zip`
2. Open Blender and go to `Edit -> Preferences...`
3. Go to the `Add-ons` tab and press `Install...`
4. Select the **zip** file (do NOT unzip it) and press `Install Add-on`
5. You can now import o3d/cfg/sco files from `File -> Import -> OMSI Model Config (*.cfg, *.sco, *.o3d)`
6. Map tiles can be imported from `File -> Import -> OMSI Map Tile (*.map)`
7. You can export o3d/cfg/sco files from `File -> Export -> OMSI Model Config (*.cfg, *.sco, *.o3d)`

### Packaging the extension ZIP

To pack the add-on into a distribution-ready ZIP for Blender 4.2+ extensions:

```bash
./pack.py
```

The script reads `blender_manifest.toml`, filters out tests/docs/temporary files, and creates `dist/blender_o3d_io-<version>.zip` without needing a Blender installation. Run `./pack.py --help` for options (`--output-dir`, `--output-name`, `--dry-run`, `--verbose`, `--quiet`).

### File handling details

- Imported paths (models, configs, textures, splines, terrain) are matched case-insensitively, including on Linux. Exact matches win; regional-codepage fallbacks still work.
- Each O3D material gets its own Blender material slot and face assignments, including repeated texture references. Images load separately, never merged by filename.
- Missing textures keep their own unloaded image reference with the original path for relinking — they never silently fall back to some other texture.
- CFG material settings are matched by texture path and material index.

## Converting MMD characters to OMSI

Open the 3D View sidebar (`N`) and choose **OMSI > OMSI Character Tools**. These tools don't need `mmd_tools`; import your MMD mesh and armature first with whatever importer you prefer.

### 1. Clean up the materials

Select the character mesh. Missing toon textures (like `toon02.bmp`) can make MMD shaders look magenta.

- **Reset MMD Toon Factor** — disables missing toon texture contributions (sphere reset is on by default).
- **Flatten MMD Materials** — replaces MMD shaders with exportable Principled materials, keeping the base texture and UV mapping.
- By default, both tools work on a copy with private materials, select the copy for the next step, and leave your originals untouched. Nothing to change = no copy created.
- Tick **Apply to every material in the file** to edit the original materials in place instead.

### 2. Convert to an OMSI armature

In **Convert to OMSI Armature**, set the source pointers manually if selection can't identify them.

- **Auto from MMD joints** builds the standard OMSI rig; **Copy template** uses a separate copy of an armature you supply.
- Defaults: keep 4 influences per vertex, remove shape keys, keep the source armature, and put the result in `OMSI_Converted`. Weights are merged and normalized.
- **Keep unmapped MMD bones as extras** keeps extra bones under ASCII names, but they stay unbound — you'll need to assign human bindings yourself.
- Conversion selects its output and updates the sidebar pointers.

### 3. Human configuration and export

Compatible `.hum` `[links]` and pivots are required for human animation. **Human Configuration & Export** (after **Mesh LODs**) derives these from supported canonical rest bones and preserved real neck/finger landmarks. Missing points need explicit numeric overrides — not collider positions. Physics, morph animation, and vehicle bindings are outside the scope of these tools.

**Measurements:** Confirm the labeled target, click **Refresh Measurements**, and resolve any missing/stale findings using **Landmark Overrides** or explicit stale-point consent. Voice, mass (kg), seat height, feet distance, and optional height/advanced walking values are saved on that target rig.

**Coordinate rules:**
- Overrides are final scaled file coordinates — don't multiply them by the export scale again.
- Enable **Turn 180°** to turn exported meshes/LODs and measured landmarks around the vertical axis without changing your Blender scene. Paired limb bindings follow their final exported side. Numeric overrides must already match the chosen direction.

**Check Export Readiness** runs strict checks on serialized character limits, CP1252 bone names, weight normalization, helper groups, missing unpacked disk images, remaining shape keys, MMD shaders, and unbound extras. Results appear in Blender reports and the console. The check doesn't change the scene or source pointers.

**Export Human** — pick `character.hum` and the tool writes `model/character.cfg`, O3D files under `model/`, and copies referenced textures into `textures/`, all with matching relative references, CP1252 text, and exactly 22 link values. Generic model export still needs textures arranged separately; **Export Human** packages them for you.

**Texture options:**
- **Max Texture Size:** **Keep Original**, or a longest-edge limit from 64 to 8192 pixels. Reduction keeps aspect ratio and alpha, and never upscales. The largest source texture dimensions are shown in the sidebar and file picker.
- **Texture Format:** **Keep Source Format** (default), **PNG (.png)**, **Targa (.tga)**, or **DDS (.dds)**.
  - Keep Source Format preserves supported PNG, Targa, BMP, and JPEG formats even when resizing. Unchanged supported disk/packed images are copied byte for byte.
  - Targa uses Blender's native writer and keeps alpha.
  - DDS uses `texconv` or ImageMagick's `magick` from PATH (or the executable chosen in **DDS Converter**) for legacy DXT5 output. Resized or edited DDS sources need that encoder to stay DDS; if conversion is unavailable or fails, you get the original/PNG with a warning. Unsupported source formats become PNG with a warning.
- Resolution defaults to unchanged, and all re-encoding uses private image copies. Explicit overwrite consent covers the HUM, model files, and copied textures.

**Arm rest pose and preview:** In **Human Configuration & Export**, opt in with **Normalize Arm Rest Pose** and set **Rest Arm Angle (degrees)**. `0` keeps the existing horizontal normalization, positive angles put the rest arms below horizontal, negative angles put them above. With normalization off, the angle is ignored. The existing walking beta is unchanged and applies as additional game lowering after the chosen rest angle.

Open the child **Diagnostic Arm Preview**, choose **Exported Rest**, **Standing Arms**, **Walking Arms** (with **Walking Cycle Phase**), or **Seated Arms**, and click **Refresh Arm Preview**. **Clear Arm Preview** removes the copies. These viewport copies never export and are cleared on Undo/Redo, save, load, or add-on unregister — click **Refresh Arm Preview** to rebuild them. The diagnostic keeps torso and legs static, uses a fixed seated lowering of 67°, and doesn't guarantee clothing clearance or how the game will look.

### Rules and limitations

- Conversion refuses active object constraints — apply/bake or disable them first.
- Existing target collections must be local, editable, visible in the active scene/view layer, and outside LOD collections.
- Generate LODs in Object mode with a local, unshared source mesh: base level selected, old reduced levels deselected.
- Export paths must be distinct case-insensitively; conflicting or unsafe paths are rejected before any files are written.

## Import diagnostics

After the `Loaded ...` console line, each model import prints a tally of unreadable meshes and missing textures, grouped by filename with occurrence counts and unique-file totals. Repeated references are counted separately, the most frequent failures show first, and counts reset for each imported model or configuration. Existing warnings still appear as files are processed.

## Exporter Tips

OMSI and Blender handle 3D models and materials quite differently, so converting between them isn't always exact — mostly when exporting, where the exporter has to make some assumptions. The exporter tries to re-export an imported cfg file as close to the original as possible. The best way to learn the exporter's behavior is to import some files and see how the importer sets them up in Blender.

### How do I export CFG files instead of just O3D files?

The exporter decides what to export based on the file extension you type:

- Exporting a **single mesh** as `.o3d` produces a single o3d file.
- Exporting **multiple objects** as `.o3d` automatically creates a separate o3d file per object (this can't be changed).
- Exporting as `.cfg` does the same as above, plus writes a cfg file — and the o3d files aren't prefixed with the file name.

For example, with this scene:

```
Scene Collection
| > Body
| > Wheel_H
| > Wheel_VL
| > Wheel_VR
```

Enable the "Export selection" option in the export dialog to control which objects get exported.

With only `Body` selected, exporting as `Body.o3d` gives you one file, `Body.o3d`. Selecting all objects and exporting as `Car.o3d` gives:

```
Car-Body.o3d
Car-Wheel_H.o3d
Car-Wheel_VL.o3d
Car-Wheel_VR.o3d
```

Exporting as `Car.cfg` does the same but without the name prefix, plus a cfg file:

```
Car.cfg
Body.o3d
Wheel_H.o3d
Wheel_VL.o3d
Wheel_VR.o3d
```

### Materials don't look correct in OMSI

Blender's shading system is completely different from OMSI's, so there are some limitations when exporting materials:

- Some material features only work when a cfg file is exported too (transparency, envmaps, lightmaps, etc...).
- If textures aren't showing in OMSI, check:
  - Blender supports image formats OMSI doesn't. If possible, use **DDS files** for textures — they're best optimized for OMSI and load faster. (OMSI only supports DXT compression in DDS files.)
  - Make sure the texture file exists in the right textures directory in OMSI. The exporter converts all texture paths to relative paths, so the texture must be in the correct place relative to the o3d/cfg file.

Only these material fields are exported:

- Base Color / Diffuse Color
- Alpha
- Specular Color / Specular Intensity
- Roughness / Specular Hardness (roughness below 0.1 automatically enables the envmap)
- Emission Color
- Base Color Texture
- Alpha Texture
- Specular Texture
- Normalmap (treated as a bumpmap)
- Emission Texture (exported as `[matl_lightmap]` if emission strength is above 1, otherwise as `[matl_nightmap]`)

Also:

- Animating material properties is not supported.
- With shader nodes (default in Blender 2.80+), the **only** node supported as an input to the *Principled BSDF Node* is the *Image Texture* node.

### How does the importer handle OMSI-specific data?

The importer keeps as much cfg data as possible, including metadata Blender doesn't use (like `[CTC_Texture]`). This data is stored in each object's "Custom Properties" section:

- Scene-specific config items → Scene tab's Custom Properties
- Object config → Object Properties tab
- Mesh/light config → Data Properties tab
- Material config → Material Properties tab

You can add or modify this data and the exporter will write it to the correct place — but it's easy to break. Don't modify it unless you know what you're doing.

### Light flares

Blender doesn't support light flares, so the importer creates EMPTY objects in the right position for `[light_enh_2]` flares. All flare properties are available in the "Custom Properties" section of the object's "Object Properties" tab — except colour, texture, and size, which are on the object data properties (colour is at "Object Properties -> Viewport Display -> Color").

For `[light_enh]` and `[light_enh_2]`, a blank or omitted texture falls back to `licht.bmp`, even when the flare is the last entry in the CFG.

### Lights

All **point lights** export as `[interiorlight]` objects. Only these properties are exported:

- Location
- Light Energy (divided by 10 to use as range) [Blender 2.80+]
- Light Distance [Blender 2.79 and older]
- Light Color
- Light Variable (from "Custom Properties")

All **spotlights** export as `[spotlight]` objects. Only these properties are exported:

- Location
- Rotation (converted to the spot direction vector)
- Light Energy (divided by 10 to use as range) [Blender 2.80+]
- Light Distance [Blender 2.79 and older]
- Light Color
- Light Spot Size
- Light Spot Blend (converted to inner angle)

### How do I prevent objects from being exported?

Two ways:

1. Enable the "Export selection" option in the export dialog (right-hand side of the file picker), then select only the objects you want to export.
2. For each object you want to skip, go to its "Object Properties" tab, and in "Custom Properties" add a property named `skip_export` (property type doesn't matter; the value is ignored).

### Animations

Animations aren't imported. If an imported cfg file contains animations, they should re-export correctly (they're preserved in "Custom Properties"), but there's no way to convert Blender animations to OMSI animations yet. Object pivot points do export correctly — setting these up properly is vital for animations to work in OMSI.

### LODs

LODs export automatically based on collection names (or groups in Blender 2.79). Objects in a collection named `LOD_X` — where `X` is a decimal number for the minimum screen size — are exported in that LOD.
