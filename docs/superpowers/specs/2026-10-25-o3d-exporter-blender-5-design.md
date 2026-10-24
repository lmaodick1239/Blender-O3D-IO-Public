# O3D Exporter Blender 5 Port Design

## Scope

Integrate the ignored `Blender-OMSI-Exporter/io_export_o3d` exporter into the existing `Blender-O3D-IO-Public` add-on. The target is Blender 5.0+ while preserving the existing CFG, SCO, MAP, and import workflows.

Direct `.o3d` export is the first integration target. Existing `.cfg` and `.sco` export paths remain unchanged; only tightly coupled compatibility fixes may modify them.

## Architecture

The upstream exporter implementation will be copied into a focused package under `o3d_io/o3d_exporter/`:

- `exporter.py` converts evaluated Blender mesh objects into O3D mesh data.
- `meshio.py` owns O3D binary structures and encoding.
- `node_shader.py` converts Blender shader-node materials into O3D material values.
- `indexdict.py` supplies deterministic insertion-order indexing.

The upstream standalone `__init__.py` will not be copied or registered. The existing root add-on remains the only registration owner.

The existing `ExportModelCFG` operator will route direct `.o3d` output through the ported exporter backend. `.cfg` and `.sco` output will continue to use the current exporter path. The current importer, map importer, map panel, and configuration parser remain in place.

A small compatibility boundary will adapt Blender 5 changes for:

- custom and split normal preparation;
- Principled BSDF socket names and material values;
- material transparency settings;
- evaluated mesh lifecycle and cleanup.

## Data Flow

1. The operator gathers selected mesh objects from the evaluated dependency graph.
2. The backend applies the requested transform flags and converts Blender coordinates to O3D coordinates.
3. Evaluated meshes are triangulated and converted into unique O3D vertices using position, normal, and UV data.
4. Materials are resolved through the Blender 5-compatible shader wrapper. Empty slots use a neutral fallback material.
5. Optional skin weights are mapped from Blender vertex groups to exported vertices.
6. The backend selects O3D version 7 by default, or version 1 for OMSI 1 compatibility.
7. `meshio` writes the binary output and creates parent directories as needed.
8. Evaluated mesh data is cleared in all conversion paths.

Existing filename behavior is preserved: a single mesh can produce one O3D file, multiple selected objects can produce separate files, and CFG/SCO output remains on the current path.

## Error Handling

- O3D 1 exports reject meshes requiring long indexes with a clear operator error.
- Missing materials or empty material slots use a neutral material rather than producing invalid O3D data.
- Unsupported or malformed weights are skipped without aborting otherwise valid geometry.
- Unsupported shader-node links fall back to the wrapper’s available defaults.
- Filesystem errors are surfaced through Blender’s operator reporting and should not leave partially written output where the backend can avoid it.
- No second add-on registration system is introduced.

## Validation

Focused tests will cover:

- backend imports and registration isolation;
- empty material slots;
- UV seam preservation;
- Blender 5 custom normals;
- short and long index output;
- OMSI 1 rejection of wide indexes;
- vertex-weight export;
- Blender 5 Principled BSDF sockets.

The existing background Blender smoke test will also exercise the integrated direct `.o3d` operator and confirm that CFG/SCO/MAP/import operators still register. Exported O3D files will be read back through the existing importer where practical.

Validation will use the available Blender 5 executable and the repository’s existing test commands. Generated caches, render output, and temporary files must remain outside the committed diff.

## Online References

- [Blender 5.0 Python API release notes](https://developer.blender.org/docs/release_notes/5.0/python_api)
- [Blender Python API change log](https://docs.blender.org/api/current/change_log.html)
- [Upstream blender-omsi-exporter repository](https://github.com/Road-hog123/blender-omsi-exporter)
