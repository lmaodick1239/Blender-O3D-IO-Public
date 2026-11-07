# OMSI 2.2.032 bones vs. Blender O3D IO: static comparison

Date: 2026-11-07. Target: `Omsi.exe`, FileVersion 2.2.032, SHA-256 `c7765877620816dd4de4cceb21dce1996c8789c89ee550c1fb58440ee689a33e`.

Method: Ghidra 12.1.4 headless decompilation of the existing project `/mnt/Random/users/user/Documents/Ghidra/OMSI` opened read-only, plus raw byte searches of `Omsi.exe`. No runtime test. Decompiled output and the trace scripts are saved in `/mnt/Random/users/user/Documents/Ghidra/OMSI/rea-evidence/o3d-bones/decomp/`. The add-on side is detailed in [2026-11-07-addon-bones-static-analysis.md](2026-11-07-addon-bones-static-analysis.md).

## OMSI functions

| Address | Role | How identified |
| --- | --- | --- |
| `0x0056c7b4` | O3D reader | Compares the header word to `0x1984` and dispatches tags `0x17/0x49/0x26/0x54/0x79`; references the "o3d reading failed" string |
| `0x0056af88` | O3D writer | Writes `0x1984`, then the same sections |
| `0x005efb98` | Model CFG parser | The only references to `[setbone]` and `[smoothskin]` |

## OMSI bone format (`0x54`)

Reader `func-0056c7b4.c:916-1004` and writer `func-0056af88.c:705-826` agree:

```text
u8  0x54
u16 bone_count
repeat bone_count:
  u8  name_len, name_len bytes        (Delphi AnsiString)
  u16 influence_count
  repeat influence_count:
    u16 vertex_index                  (always 2 bytes)
    f32 weight
```

The in-memory record is 12 bytes: name, a `u16` index array, and a `f32` weight array. It has no parent, bind matrix, or animation data.

The header flag bit 0 (`(opt & 1) == 1`, reader lines 164-169) affects only `0x49` triangle indices (lines 507-570). The `0x54` index stays `u16` regardless of that flag.

The options byte is read when `version >= 3` (reader lines 159-168). The 4-byte key is read when `version >= 4` (line 170 onward). Versions above 7 are rejected.

## Are bone names hardcoded?

**In OMSI: no.** The engine reads names from the file and binds them through `[setbone]`:

- `[setbone]` (`func-005efb98-model-cfg.c:2313-2395`) reads two lines: a name and an integer. It loops over the mesh's loaded bone-name list (`+0x188`), compares each entry with the CFG name using the Delphi string-compare routine `FUN_00409150`, and on a match stores `StrToInt(value)` in the parallel slot array (`+0x1b8`). Unmatched names are skipped.
- The engine fixes the meaning of the **numeric slot IDs** (for example the human IDs `-2`…`-14`). It does not fix the names.
- Byte search: `Hand_L`, `Hand_R`, and `US_L` appear nowhere in the executable, in ANSI or UTF-16. `OS_L`, `OS_R`, `OA_L`, and `UA_L` appear only as parts of Delphi RTTI field names such as `OS_L_Vec` and `UA_L_Vec` (human joint vectors next to `anim_walk_upper_arm_beta`). `Hip` appears only in the UI labels `Hip Alpha:` and `Hip Gamma:`. `Head` and `Main` match only unrelated UI and VCL strings.
- I did not verify whether `FUN_00409150` compares case-sensitively. It is the same routine used to match CFG keywords such as `[setbone]`.

**In the add-on:** names pass through unchanged on import and export. [o3d_armature.py:8-37](../../o3d_io/o3d_armature.py#L8-L37) hardcodes the 13 human names only to choose Blender parenting and fallback head positions. Other names still become bones, unparented. Export writes every populated vertex group by name.

## Comparison

| Item | OMSI 2.2.032 | Add-on | Result |
| --- | --- | --- | --- |
| Bone count | `u16` | `u16` ([o3dconvert.py:385](../../o3d_io/o3dconvert.py#L385), [:220](../../o3d_io/o3dconvert.py#L220)) | Match |
| Name | `u8` length + bytes | `u8` length + CP1252, max 255 ([:276-284](../../o3d_io/o3dconvert.py#L276-L284)) | Match |
| Influence count | `u16` | `u16` ([:293](../../o3d_io/o3dconvert.py#L293)) | Match |
| Influence vertex index | **always `u16`** | `u32` when header bit 0 is set ([:85-86](../../o3d_io/o3dconvert.py#L85-L86), [:310](../../o3d_io/o3dconvert.py#L310)) | **Fixed 2026-11-07: always `u16`** |
| Weight | `f32` | `f32` | Match |
| Options byte present | `version >= 3` | `version > 3` ([:185](../../o3d_io/o3dconvert.py#L185), [:412](../../o3d_io/o3dconvert.py#L412)) | **Fixed 2026-11-07: `version >= 3`** |
| Hierarchy, bind pose | None in file | Inferred for Blender only, not exported | Compatible |
| Name binding | `[setbone]` name → integer slot | Not parsed or written | **Fixed 2026-11-07: warn on unbound names** |

### 1. Wide bone indices (real incompatibility) — fixed 2026-11-07

[io_o3d_export.py:162-167](../../o3d_io/io_o3d_export.py#L162-L167) sets `long_triangle_indices` when any index is above 65535. [o3dconvert.py:310](../../o3d_io/o3dconvert.py#L310) then writes 8-byte influences. OMSI reads 6-byte influences, so it loses alignment after the first record and misparses the rest of the bone section and everything after it. The importer has the same mirrored assumption ([:85-86](../../o3d_io/o3dconvert.py#L85-L86)), so it also misreads OMSI-written files that set bit 0 and contain bones.

Because OMSI stores bone indices as `u16`, it cannot address vertices above 65535 with bones at all. The correct behavior is to always use `<Hf` for `0x54`, and to reject export when a weighted vertex index exceeds 65535. The existing round-trip tests pass because the add-on's reader and writer share the same wrong assumption.

**Fixed:** the bone reader/writer now always uses `<Hf` and a `u16` influence count, `export_mesh` derives `long_triangle_indices` from triangle indices only, and export raises a `ValueError` naming the group when a weighted vertex index exceeds 65535. Tests: `assert_wide_mesh_bone_indices_are_u16`, `assert_weighted_index_above_u16_rejected`.

### 2. Version 3 header — fixed 2026-11-07

For `version == 3` the add-on writes no options byte. OMSI reads the next byte, the `0x17` tag, as options, which sets bit 0 and the alternate-seed bit, and then misreads the stream. The export UI allows versions 1-7 ([__init__.py:227-232](../../__init__.py#L227-L232)). The default of 7 is unaffected. The wide-index guard at [io_o3d_export.py:170](../../o3d_io/io_o3d_export.py#L170) uses `< 3` while the writer uses `> 3`, which compounds the problem. This finding comes from the decompiled code only and has not been reproduced in OMSI.

**Fixed:** the reader and writer now treat the options byte as present for `version >= 3` and the encryption key as present only for `version >= 4`. Test: `assert_v3_header_layout`.

### 3. `[setbone]` not handled — warn-only fix 2026-11-07

OMSI deforms only bones whose names match a `[setbone]` entry. The add-on neither reads nor writes `[setbone]`/`[smoothskin]` ([o3d_cfg_parser.py](../../o3d_io/o3d_cfg_parser.py) has no match), so renaming a vertex group in Blender silently drops it from OMSI skinning unless the CFG is edited too.

**Fixed (warn, don't rewrite):** `find_unbound_setbone_names` reports `[setbone]` names (from the mesh and each material's preserved `cfg_data`) that no longer equal a vertex group with at least one weight above zero; CFG export logs one warning per name. There is no reliable old-name → new-name mapping, so the entries are still written unchanged. Test: `assert_unbound_setbone_warning`.

## Not established

- What OMSI does with unmatched bones after `[setbone]` (default slot value) and in the `[smoothskin]` path. I located `[smoothskin]` at `func-005efb98-model-cfg.c:2407` but did not trace its body.
- Case sensitivity of the name match.
- Normalization or per-vertex influence limits applied at skinning time. These live outside the loader and were not traced.
