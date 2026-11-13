"""Public import-normal checks using native synthetic O3Ds, without registration.

blender --background --threads 2 --factory-startup --disable-autoexec
--python-exit-code 1 --python tests/smoke_import_normals.py [-- --check custom]
"""
import argparse
from collections import Counter
from contextlib import contextmanager
import math
from pathlib import Path
import sys
import tempfile

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from smoke_support import load_addon


PIVOTS = {
    'identity': Matrix.Identity(4),
    'half_turn': Matrix.Rotation(math.pi, 4, 'Y'),
    'reflected': Matrix.Diagonal((-1, 1, 1, 1)),
    'translated': Matrix.Translation((3, -2, 1)),
    'nonuniform_shear': Matrix(((2, .3, 0, 0), (0, .75, .2, 0),
                               (0, 0, 1.5, 0), (0, 0, 0, 1))),
    'singular_fallback': Matrix.Diagonal((0, 1, 1, 1)),
}
MATERIALS = [(1., 1., 1., 1., 0., 0., 0., 0., 0., 0., 0., '')] * 2


def _native_geometry():
    mesh = bpy.data.meshes.new('O3D Import Normals Fixture')
    bm = bmesh.new()
    try:
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1)
        bm.to_mesh(mesh)
        vertices = []
        for vertex in mesh.vertices:
            x, y, z = vertex.co
            normal = Vector((x + .23 * z, .8 * y + .17 * x, 1.2 * z)).normalized()
            record = (*vertex.co, *normal, (x + 1) / 2, (y + 1) / 2)
            vertices.append(record)
        triangles = [(*face.vertices, face.index % 2) for face in mesh.polygons]
        assert len(vertices) == 42 and len(triangles) == 80
        return vertices, triangles
    finally:
        bm.free()
        bpy.data.meshes.remove(mesh)


@contextmanager
def _fixture(addon, *, zero_normal=False):
    vertices, triangles = _native_geometry()
    if zero_normal:
        vertices[0] = (*vertices[0][:3], 0., 0., 0., *vertices[0][6:8])
    with tempfile.TemporaryDirectory(prefix='o3d-import-normals-') as temporary:
        paths = {}
        for case_name, pivot in PIVOTS.items():
            path = Path(temporary) / (case_name + '.o3d')
            serialized_pivot = [value for row in pivot.transposed() for value in row]
            with path.open('wb') as file:
                addon.o3d_io.o3dconvert.export_o3d(
                    file, vertices, triangles, MATERIALS, [], serialized_pivot,
                )
            paths[case_name] = path
        yield vertices, triangles, paths


@contextmanager
def _imported(addon, path, custom):
    source_bytes = path.read_bytes()
    result = addon.o3d_io.io_o3d_import.load_o3d(str(path.parent), str(path), custom)
    mesh = result[2]
    try:
        assert mesh is not None
        yield result
    finally:
        if mesh is not None:
            bpy.data.meshes.remove(mesh)
        assert path.read_bytes() == source_bytes, 'import changed the source O3D'


def _close(actual, expected, label):
    assert (Vector(actual) - Vector(expected)).length < 2e-5, (label, tuple(actual), tuple(expected))


def _angle(actual, expected):
    assert all(math.isfinite(value) for value in (*actual, *expected)), (actual, expected)
    assert actual.length > 0 and expected.length > 0, (actual, expected)
    return math.degrees(math.acos(max(-1.0, min(1.0, actual.normalized().dot(expected.normalized())))))


def _assert_geometry(result, vertices, triangles, case_name):
    materials, material_ids, mesh, decoded, frame = result
    assert len(mesh.vertices) == len(vertices) == 42
    assert len(mesh.polygons) == len(triangles) == 80
    assert len(materials) == 2
    assert material_ids == [triangle[3] for triangle in triangles]
    assert [face.material_index for face in mesh.polygons] == material_ids
    for vertex, record, raw in zip(mesh.vertices, vertices, decoded[1]):
        x, y, z = record[:3]
        _close(frame @ vertex.co, (x, z, y), (case_name, 'position', vertex.index))
        _close(raw[1], record[3:6], (case_name, 'raw normal', vertex.index))
    for loop in mesh.loops:
        u, v = vertices[loop.vertex_index][6:8]
        _close(mesh.uv_layers[0].data[loop.index].uv, (u, 1 - v), (case_name, 'UV', loop.index))
    for face, triangle in zip(mesh.polygons, triangles):
        source = [Vector(vertices[index][:3]) for index in triangle[:3]]
        source_normal = (source[1] - source[0]).cross(source[2] - source[0]).normalized()
        nx, ny, nz = source_normal
        expected = Vector((nx, nz, ny))
        # World cross products include the preserved object frame's handedness.
        if frame.is_negative:
            expected.negate()
        world = [frame @ mesh.vertices[index].co for index in face.vertices]
        actual = (world[1] - world[0]).cross(world[2] - world[0]).normalized()
        assert actual.dot(expected) > .99999, (case_name, 'winding', face.index, actual.dot(expected))


def _assert_custom_directions(mesh, frame, vertices, case_name):
    assert mesh.has_custom_normals, case_name
    normal_to_world = frame.to_3x3().inverted().transposed()
    maximum = 0.
    for loop in mesh.loops:
        record = vertices[loop.vertex_index]
        nx, ny, nz = record[3:6]
        expected = Vector((nx, nz, ny)).normalized()
        actual = (normal_to_world @ mesh.corner_normals[loop.index].vector).normalized()
        assert all(math.isfinite(value) for value in actual) and actual.length > .99, (case_name, loop.index)
        if expected.length == 0:
            continue  # Blender supplies the generated direction for a zero record.
        angle = _angle(actual, expected)
        assert angle < 1.0, (case_name, loop.index, angle)
        maximum = max(maximum, angle)
    return maximum


def assert_import_custom_normals(addon):
    """Authored directions survive import transforms and winding correction."""
    with _fixture(addon) as (vertices, triangles, paths):
        for case_name, path in paths.items():
            with _imported(addon, path, True) as result:
                _assert_geometry(result, vertices, triangles, case_name)
                maximum = _assert_custom_directions(result[2], result[4], vertices, case_name)
                print('IMPORT_CUSTOM_NORMALS_OK', case_name, 'max_angle_degrees', maximum)


def _assert_generated_directions(mesh, case_name, *, vertex_index=None):
    checked = 0
    for face in mesh.polygons:
        for loop_index in face.loop_indices:
            if vertex_index is not None and mesh.loops[loop_index].vertex_index != vertex_index:
                continue
            normal = mesh.corner_normals[loop_index].vector
            assert all(math.isfinite(value) for value in normal) and normal.length > .99, (case_name, loop_index)
            assert normal.dot(face.normal) > 0, (case_name, 'generated orientation', loop_index)
            checked += 1
    assert checked > 0


def assert_import_generated_normals(addon):
    """Opt-out keeps generated shading; zero authored directions fall back safely."""
    for zero_normal in (False, True):
        with _fixture(addon, zero_normal=zero_normal) as (vertices, triangles, paths):
            for case_name, path in paths.items():
                with _imported(addon, path, zero_normal) as result:
                    mesh, frame = result[2], result[4]
                    _assert_geometry(result, vertices, triangles, case_name)
                    if zero_normal:
                        _assert_custom_directions(mesh, frame, vertices, case_name)
                        _assert_generated_directions(mesh, case_name, vertex_index=0)
                        print('IMPORT_ZERO_NORMAL_OK', case_name)
                    else:
                        assert not mesh.has_custom_normals, case_name
                        _assert_generated_directions(mesh, case_name)
                        print('IMPORT_GENERATED_NORMALS_OK', case_name)


def _assert_exported_records(decoded, vertices, triangles, label):
    assert len(decoded[2]) == len(triangles) == 80
    assert len(decoded[3]) == 2
    assert not decoded[4], (label, 'unexpected bones')
    assert Counter(triangle[1] for triangle in decoded[2]) == Counter(triangle[3] for triangle in triangles)
    matched = set()
    maximum = 0.
    for index, (position, normal, uv) in enumerate(decoded[1]):
        candidates = [i for i, record in enumerate(vertices)
                      if (Vector(position) - Vector(record[:3])).length < 2e-5]
        assert len(candidates) == 1, (label, 'position match', index, position, candidates)
        source_index = candidates[0]
        matched.add(source_index)
        source = vertices[source_index]
        angle = _angle(Vector(normal), Vector(source[3:6]))
        assert angle < 1.0, (label, 'exported normal', index, angle)
        _close(uv, source[6:8], (label, 'exported UV', index))
        maximum = max(maximum, angle)
    assert matched == set(range(len(vertices))), (label, 'missing positions')
    return maximum


def assert_import_normal_roundtrip(addon):
    """Two real export/reimport cycles preserve native records despite vertex splits."""
    with _fixture(addon) as (vertices, triangles, paths):
        materials = []
        try:
            for index in range(2):
                material = bpy.data.materials.new('O3D Import Normals Neutral ' + str(index))
                materials.append(material)
                addon.o3d_io.blender_compat.enable_material_nodes(material)
            for case_name, source_path in paths.items():
                path = source_path
                for cycle in (1, 2):
                    with _imported(addon, path, True) as result:
                        mesh, decoded, frame = result[2:5]
                        records = [(*position, *normal, *uv) for position, normal, uv in decoded[1]]
                        _assert_custom_directions(mesh, frame, records, (case_name, cycle))
                        obj = bpy.data.objects.new('O3D Import Normals Roundtrip', mesh)
                        parent = bpy.data.objects.new('O3D Import Normals Frame', None)
                        try:
                            bpy.context.scene.collection.objects.link(parent)
                            bpy.context.scene.collection.objects.link(obj)
                            # Parent-inverse storage preserves shear through depsgraph
                            # updates; a direct matrix_world assignment loses it to TRS.
                            obj.parent = parent
                            obj.matrix_parent_inverse = frame
                            bpy.context.view_layer.update()
                            for actual, expected in zip(obj.matrix_world, frame):
                                _close(actual, expected, (case_name, cycle, 'object frame'))
                            for material in materials:
                                mesh.materials.append(material)
                            exported_path = source_path.with_name(case_name + '-cycle-' + str(cycle) + '.o3d')
                            addon.o3d_io.io_o3d_export.do_export(
                                str(exported_path), bpy.context, Matrix.Identity(4), True, 7, True,
                                objects=[obj],
                            )
                            exported = addon.o3d_io.o3dconvert.import_o3d(exported_path.read_bytes())
                            maximum = _assert_exported_records(exported, vertices, triangles, (case_name, cycle))
                            print('IMPORT_NORMAL_ROUNDTRIP_OK', case_name, 'cycle', cycle,
                                  'vertices', len(exported[1]), 'max_angle_degrees', maximum)
                        finally:
                            bpy.data.objects.remove(obj, do_unlink=True)
                            bpy.data.objects.remove(parent, do_unlink=True)
                    path = exported_path
                # Reimport the final output too, not only the input to each export.
                with _imported(addon, path, True) as result:
                    records = [(*position, *normal, *uv) for position, normal, uv in result[3][1]]
                    _assert_custom_directions(result[2], result[4], records, (case_name, 'final'))
        finally:
            for material in materials:
                bpy.data.materials.remove(material)


CHECKS = [assert_import_custom_normals, assert_import_generated_normals, assert_import_normal_roundtrip]


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', choices=('custom', 'generated', 'roundtrip'))
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    addon = load_addon()
    checks = dict(zip(('custom', 'generated', 'roundtrip'), CHECKS))
    for check in ([checks[args.check]] if args.check else CHECKS):
        check(addon)
        print('IMPORT_NORMAL_CHECK_OK', check.__name__)
    print('IMPORT_NORMALS_SMOKE_OK', bpy.app.version_string)


if __name__ == '__main__':
    run()
