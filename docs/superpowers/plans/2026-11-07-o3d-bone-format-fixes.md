# O3D Bone Format Fixes: Handoff

> **For agentic workers:** Use superpowers:test-driven-development. Write each test, run it, and watch it fail before changing production code. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Make exported O3D files load correctly in OMSI 2.2.032 when they contain bones, and warn when `[setbone]` entries no longer match exported bone names.

**State at handoff:** No production or test code has been changed. HEAD is `e5ec06c6157924ae553dfeb1777e9d19de588195`. The nested checkout `.gitignorefolder/Blender-OMSI-Exporter` was already dirty; leave it alone. `docs/research/` is new and untracked; it holds the evidence notes below.

## Evidence

Read these before starting:

- [2026-11-07-omsi-vs-addon-bones.md](../../research/2026-11-07-omsi-vs-addon-bones.md): OMSI vs. add-on comparison.
- [2026-11-07-addon-bones-static-analysis.md](../../research/2026-11-07-addon-bones-static-analysis.md): add-on bone code walkthrough.
- Decompiled OMSI code: `/mnt/Random/users/user/Documents/Ghidra/OMSI/rea-evidence/o3d-bones/decomp/`
  - `func-0056c7b4.c`: O3D reader
  - `func-0056af88.c`: O3D writer
  - `func-005efb98-model-cfg.c`: model CFG parser

All OMSI facts come from static decompilation of `Omsi.exe` 2.2.032 (SHA-256 `c7765877…a33e`). None were confirmed by loading files in OMSI.

### OMSI reader rules (`func-0056c7b4.c`)

| Field | OMSI rule | Reader lines |
| --- | --- | --- |
| Version byte | rejected if `> 7` | 153-158 |
| Options byte | present if `version >= 3`; bit 0 = 32-bit triangle indices, bit 1 = alternate seed | 159-168 |
| Encryption key (`u32`) | present if `version >= 4`; `0xFFFFFFFF` = not encrypted | 170-176 |
| `0x17` vertex count | `u16` if `version < 3`, otherwise `u32` | 601-608 |
| `0x49` triangle count | `u16` if `version < 3`, otherwise `u32` | 473-480 |
| `0x49` triangle indices | `u32` if options bit 0, otherwise `u16` | 507-570 |
| `0x26` material count | always `u16` | 790 |
| `0x54` bone count | always `u16` | 917 |
| `0x54` name | `u8` length + bytes | 935-947 |
| `0x54` influence count | always `u16` | 948 |
| `0x54` influence | **always `u16` index + `f32` weight; bit 0 is ignored** | 970-995 |

OMSI's own writer (`func-0056af88.c:705-826`) also writes bone indices as `u16`.

### `[setbone]` binding (`func-005efb98-model-cfg.c:2313-2395`)

`[setbone]` reads two lines: a bone name and an integer. OMSI compares the name with each bone name loaded from the current mesh's O3D file. On a match it stores the integer as that bone's slot. Names that match nothing are skipped silently. Bone names are not hardcoded in the executable.

## Task 1: Bone influence indices are always `u16`

**Bug:** If any triangle or weighted index is above 65535, [io_o3d_export.py:162-167](../../../o3d_io/io_o3d_export.py#L162-L167) sets `long_triangle_indices`. [o3dconvert.py:310](../../../o3d_io/o3dconvert.py#L310) then writes 8-byte `<If` influence records. OMSI reads 6-byte records, so it misparses the bone section and every section after it. The importer makes the same wrong assumption at [o3dconvert.py:85-86](../../../o3d_io/o3dconvert.py#L85-L86) and [:220](../../../o3d_io/o3dconvert.py#L220). Existing round-trip tests pass only because the add-on's reader and writer agree with each other.

**Files:** `o3d_io/o3dconvert.py`, `o3d_io/io_o3d_export.py`, `tests/smoke_io.py`, `tests/blender_smoke.py`

- [ ] Add a test-only parser to `tests/smoke_io.py` that implements the reader-rules table above. Do not use `o3dconvert.import_o3d`. Return the version, options, counts, and bones `[(name, [(index, weight), ...])]`. Assert that every section is consumed exactly and that parsing ends after `0x79` plus 64 bytes at end of file.
- [ ] Add `assert_wide_mesh_bone_indices_are_u16`. Build a mesh with more than 65535 exported vertices: copy the 25000-triangle unique-UV construction from `assert_wide_index_width` ([smoke_io.py:733-793](../../../tests/smoke_io.py#L733-L793)) into a shared helper. Weight source vertices `[0, 1, 2]`, export as v7, and parse the file with the OMSI parser. Assert that options bit 0 is set, that the bone parses with three influences, and that every index is below 65536.
- [ ] Add `assert_weighted_index_above_u16_rejected`. Use the same wide mesh with weights on its last three vertices, as the current `assert_wide_index_width` does. Expect `ValueError` mentioning `65535` and the group name. OMSI cannot address these vertices from a bone.
- [ ] Change `assert_wide_index_width` to weight low vertices. Otherwise it collides with the new rejection.
- [ ] Register the new checks in `CHECKS` in [blender_smoke.py](../../../tests/blender_smoke.py#L16-L47). Run the tests and confirm they fail for the expected reason.
- [ ] Fix `import_bone` and `import_bone_list`: drop the `long_triangle_indices` parameter, always read `<Hf` (6 bytes), and always read the count as `u16`. Update the call at [o3dconvert.py:220](../../../o3d_io/o3dconvert.py#L220).
- [ ] Fix `export_bone` and `export_bone_list`: always write `<Hf`. Raise `ValueError` if `vertex_index > 65535`, naming the bone, the index, and the limit.
- [ ] In `export_mesh`, base `long_triangle_indices` on triangle indices only. Check weighted indices separately and raise before writing the file. The file is currently opened before validation, so a failed export can leave a partial file. Either validate first or reuse the existing behavior, and document whichever you choose.

## Task 2: Version 3 header

**Bug:** OMSI expects the options byte and `u32` vertex and triangle counts from version 3. The add-on uses `version > 3` for both on export ([o3dconvert.py:411-418](../../../o3d_io/o3dconvert.py#L411-L418)) and on import ([:185-194](../../../o3d_io/o3dconvert.py#L185-L194)). A v3 file from the add-on therefore makes OMSI read the `0x17` tag as the options byte. The export UI allows versions 1-7 ([__init__.py:227-232](../../../__init__.py#L227-L232)). The default, v7, is unaffected.

- [ ] Add `assert_v3_header_layout`. Export a small triangle as v3 and parse it with the OMSI test parser. Assert that byte 3 is the options byte, byte 4 is `0x17`, the vertex count is `u32`, and no key is present. Also round-trip the file through `o3dconvert.import_o3d` and compare vertex and triangle counts.
- [ ] Watch the test fail.
- [ ] Import: read the options byte when `version >= 3`, read the key only when `version >= 4`, and set `l_header = version >= 3`. Keep the default of not encrypted when no key is present.
- [ ] Export: write the options byte when `version >= 3` and the key only when `version >= 4`. Set `long_header = version >= 3`. Encryption needs a key, so warn on `encrypted` only when `version < 4`. `export_mesh` always passes `alt_encryption_seed=True` ([io_o3d_export.py:181](../../../o3d_io/io_o3d_export.py#L181)), so don't warn about the seed below version 4; that warning would fire on every export. Do not change encryption behavior.
- [ ] Leave the pre-v3 guard `o3d_version < 3` at [io_o3d_export.py:170](../../../o3d_io/io_o3d_export.py#L170) as it is. Triangle indices above 65535 need options bit 0, which exists from version 3, so the guard already matches OMSI. Confirm that `assert_pre_v3_wide_index_rejection` still passes after Task 1 changes the index calculation.

## Task 3: Warn about unbound `[setbone]` entries

**Gap:** The add-on does not parse `[setbone]`. The CFG importer stores it as an unknown command, and the CFG exporter writes it back as raw text ([o3d_cfg_parser.py:436-471](../../../o3d_io/o3d_cfg_parser.py#L436-L471)). If a user renames or empties a vertex group in Blender, the preserved `[setbone]` no longer matches any exported bone. OMSI then skips it silently, and that bone stops deforming.

**Decision:** Warn; don't rewrite. There is no reliable mapping from an old name to a new one. Do not warn about bones that lack a `[setbone]` entry; that is valid, for example on `[smoothskin]` meshes.

- [ ] Add `find_unbound_setbone_names(obj)` to `o3d_io/o3d_cfg_parser.py`. Gather `[setbone]` entries from `obj.data["cfg_data"]` and from each material's `"cfg_data"`. The parser attaches a command to the material when it follows a `[matl]` block ([:438-450](../../../o3d_io/o3d_cfg_parser.py#L438-L450)). Each entry has the form `["[setbone]", name, value, ...]`. Return names that do not equal a vertex group with at least one assigned weight above zero. Use exact, case-sensitive comparison.
- [ ] Call it in `write_cfg_mesh` ([:473-486](../../../o3d_io/o3d_cfg_parser.py#L473-L486)) and `log()` one warning per name, including the object name. Keep writing the entry unchanged.
- [ ] Add `assert_unbound_setbone_warning`. Create a mesh with a populated `Main` group and an empty `Empty` group. Store `cfg_data = [["[setbone]", "Main", "-11"], ["[setbone]", "Renamed", "-10"], ["[setbone]", "Empty", "-12"]]` on the mesh data. Assert that the helper returns `{"Renamed", "Empty"}`. Write it first and confirm it fails because the helper doesn't exist yet.
- [ ] First check how Blender stores this list-of-lists IDProperty. Mirror the importer at [io_o3d_import.py:186](../../../o3d_io/io_o3d_import.py#L186) and read entries back with `list(...)`. The parser appends every line after the command, so entries can carry trailing blank lines. Use only elements 1 (name) and 2 (value), stripped.

## Verification

```bash
blender --background --factory-startup --python tests/blender_smoke.py | tee smoke.log
grep -q BLENDER_O3D_IO_SMOKE_OK smoke.log
```

`blender` is at `/usr/local/bin/blender`. CI runs Blender 4.2, 5.0, and 5.2 ([smoke_test.yml](../../../.github/workflows/smoke_test.yml)). Run locally and report the version you used. The full suite builds 75k-vertex meshes several times and is slow.

Before finishing:

- [ ] All checks pass and `BLENDER_O3D_IO_SMOKE_OK` is printed.
- [ ] `git diff --check` is clean.
- [ ] Update [2026-11-07-omsi-vs-addon-bones.md](../../research/2026-11-07-omsi-vs-addon-bones.md) to mark each fixed gap.

## Out of scope

Do not do these in this pass. Mention them to the user if they become relevant.

- Export dedup at [io_o3d_export.py:96-123](../../../o3d_io/io_o3d_export.py#L96-L123) keys on position, normal, and UV only. Coincident vertices with different weights can merge.
- Duplicate-name vertex groups on import ([io_o3d_import.py:206-229](../../../o3d_io/io_o3d_import.py#L206-L229)).
- `[smoothskin]` semantics, `[links]`, procedural pose, and normalization. These were not traced in OMSI.
- Encryption, and the "TODO: encryption is broken" note at [o3dconvert.py:416](../../../o3d_io/o3dconvert.py#L416).

## Open questions

- Whether OMSI compares `[setbone]` names case-sensitively. The compare routine `FUN_00409150` was not traced. If case-insensitive matching is confirmed later, relax the Task 3 comparison.
- None of these fixes has been checked by loading a file in OMSI. If the user can test there, export a weighted mesh above 65535 vertices (expect a clear error) and a v3 file with bones (expect it to load).
