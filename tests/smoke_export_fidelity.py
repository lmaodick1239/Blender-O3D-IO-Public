"""Synthetic export fidelity checkpoint; intentionally RED until later repairs.

Standalone owns add-on registration. run_checks never does. No input .blend is
loaded or saved. Raw O3Ds/PNGs/CFGs stay in --output-dir, never in fixtures.
Reference output is comparison evidence, not authority for native rendering.
"""
import argparse
import hashlib
import importlib
import json
import math
from pathlib import Path
import sys
import tempfile
import traceback
from types import ModuleType

import bpy
from bpy_extras import node_shader_utils
from mathutils import Euler, Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from o3d_export_support import oriented_surface, read_export
from smoke_support import load_addon


GROUPS = ('custom_normal', 'transforms', 'materials', 'uv_mapping', 'cfg_materials')
OUTPUT_DIR = Path(__file__).resolve().parents[1] / '.superpowers/sdd/2026-11-10-o3d-export-fidelity/task-2-scratch/baseline'
REFERENCE = None
AXIS = Matrix(((1, 0, 0), (0, 0, 1), (0, 1, 0)))
UVS = ((.13, .21), (.81, .32), (.27, .89))
MAPPING_LOCATION = (.11, -.07, .03)
MAPPING_ROTATION = (.31, -.27, .49)
MAPPING_SCALE = (1.3, .7, 1.1)


def assert_direction(actual, expected):
    assert (Vector(actual) - Vector(expected)).length < 2e-4, (actual, expected)
    assert math.isclose(Vector(actual).length, 1.0, abs_tol=2e-4), actual


def assert_emission_record(material):
    actual = material[7:10]
    expected = (0.6, 0.9, 1.2)
    assert all(math.isclose(a, b, abs_tol=2e-6)
               for a, b in zip(actual, expected)), actual


def _json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')


def _rounded(value):
    if isinstance(value, float):
        return round(value, 5)
    if isinstance(value, (tuple, list)):
        return tuple(_rounded(v) for v in value)
    return value


def _reference_exporter(path):
    root = Path(path).resolve()
    package = root / 'io_export_o3d'
    if not (package / 'exporter.py').is_file():
        raise FileNotFoundError(f'requested reference exporter unavailable: {path} (expected io_export_o3d/exporter.py)')
    # Avoid the reference UI's registration and __init__ side effects entirely.
    name = '_o3d_fidelity_reference'
    module = ModuleType(name)
    module.__path__ = [str(package)]
    sys.modules[name] = module
    return importlib.import_module(name + '.exporter').Exporter


def _mesh(name, vertices=None, faces=None, custom=True):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices or [(0, 0, 0), (2, .1, 0), (.3, 1.4, .2)],
                     [], faces or [(0, 1, 2)])
    mesh.update()
    uv = mesh.uv_layers.new(name='Editing')
    for i, item in enumerate(uv.uv):
        item.vector = UVS[i % 3]
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    if custom:
        normal = Vector((.23, -.41, .88)).normalized()
        mesh.normals_split_custom_set([normal] * len(mesh.loops))
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    return obj


def _material(obj, name='Fidelity', roughness=1., emission=False):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    # Both exporters read the same explicitly named material output.
    material.node_tree.nodes.get('Material Output').name = 'Export'
    wrapper = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=False)
    wrapper.base_color = (.7, .4, .2)
    wrapper.alpha = .65
    wrapper.specular = 0.
    wrapper.roughness = roughness
    wrapper.emission_color = (.2, .3, .4) if emission else (0., 0., 0.)
    wrapper.emission_strength = 3. if emission else 0.
    obj.data.materials.append(material)
    return material, wrapper


def _image(directory):
    # 4x4 arrow/checker, bottom-to-top RGBA; no mirror symmetry in either axis.
    rows = ('RBBB', 'GRBW', 'GGRA', 'YWGY')
    colors = {'R': (1, 0, 0, 1), 'G': (0, 1, 0, .75), 'B': (0, 0, 1, .5),
              'W': (1, 1, 1, 1), 'A': (1, .2, 0, .25), 'Y': (1, 1, 0, 1)}
    image = bpy.data.images.new('arrow-checker.png', width=4, height=4, alpha=True)
    image.pixels = [channel for row in rows for color in row for channel in colors[color]]
    image.filepath_raw = str(directory / 'arrow-checker.png')
    image.file_format = 'PNG'
    image.save()
    return image


def _textured(obj, directory):
    material, wrapper = _material(obj)
    image = _image(directory)
    wrapper.base_color_texture.image = image
    wrapper.alpha_texture.image = image
    return material, wrapper


def _snapshot(obj):
    mesh = obj.data
    mesh.calc_loop_triangles()
    return {
        'vertices': [tuple(v.co) for v in mesh.vertices],
        'faces': [tuple(p.vertices) for p in mesh.polygons],
        'smooth': [p.use_smooth for p in mesh.polygons],
        'corner_normals': [tuple(n.vector) for n in mesh.corner_normals],
        'loop_vertices': [loop.vertex_index for loop in mesh.loops],
        'loop_triangles': [tuple(t.loops) for t in mesh.loop_triangles],
        'uv_layers': [{'name': layer.name, 'active_render': layer.active_render,
                       'uvs': [tuple(uv.vector) for uv in layer.uv]} for layer in mesh.uv_layers],
        'editing_uv': mesh.uv_layers.active.name if mesh.uv_layers.active else None,
        'location': tuple(obj.location), 'scale': tuple(obj.scale),
        'rotation_mode': obj.rotation_mode, 'rotation_euler': tuple(obj.rotation_euler),
        'rotation_quaternion': tuple(obj.rotation_quaternion),
        'matrix_world': [tuple(row) for row in obj.matrix_world],
        'parent_matrix_world': [tuple(row) for row in obj.parent.matrix_world] if obj.parent else None,
        'weights': [[(obj.vertex_groups[g.group].name, g.weight) for g in v.groups] for v in mesh.vertices],
        'modifiers': [(m.name, m.type, m.show_viewport, m.show_render) for m in obj.modifiers],
        'materials': [slot.material.name if slot.material else None for slot in obj.material_slots],
    }


def _make_case(group, name, directory):
    custom = group == 'transforms' or name == 'oblique_triangle'
    vertices = faces = None
    if name in ('flat_wedge', 'smooth_wedge', 'uv_seam'):
        vertices = [(0, 0, 0), (2, 0, 0), (.2, 1.3, 0), (.2, .3, 1.1)]
        faces = [(0, 1, 2), (1, 0, 3)]
    elif name == 'nonplanar_quad':
        vertices, faces = [(0, 0, 0), (2, 0, 0), (2, 1, .35), (0, 1, 0)], [(0, 1, 2, 3)]
    elif name == 'concave_ngon':
        vertices = [(0, 0, 0), (2, 0, 0), (2, 2, 0), (1, .7, 0), (0, 2, 0)]
        faces = [(0, 1, 2, 3, 4)]
    obj = _mesh(name, vertices, faces, custom=custom)
    settings = {'global_scale': 1., 'version': 7, 'local_transforms': ['LOC', 'ROT', 'SCA'],
                'origin': True, 'reference_weights': False, 'export_custom_normals': True}
    if name == 'flat_wedge':
        for p in obj.data.polygons:
            p.use_smooth = False
    if name == 'uv_seam':
        for slot, uv in zip(obj.data.uv_layers.active.uv,
                            ((.1, .2), (.8, .2), (.3, .9), (.9, .8), (.6, .7), (.2, .1))):
            slot.vector = uv
    transforms = {
        'positive_scale': ('scale', (2., 2., 2.)),
        'negative_scale': ('scale', (-1., 1., 1.)),
        'nonuniform_scale': ('scale', (2., .7, 1.4)),
        'translation': ('location', (2., -3., 4.)),
        'euler_rotation': ('rotation_euler', (.31, -.27, .49)),
    }
    if name in transforms:
        setattr(obj, *transforms[name])
    if name == 'quaternion_rotation':
        obj.rotation_mode = 'QUATERNION'
        obj.rotation_quaternion = Euler((.31, -.27, .49), 'XYZ').to_quaternion()
    if name == 'parent_transform':
        parent = bpy.data.objects.new('Fidelity parent', None)
        bpy.context.scene.collection.objects.link(parent)
        parent.location = (2., -3., 4.)
        parent.rotation_euler = (.31, -.27, .49)
        obj.parent = parent
        obj.location = (.4, -.2, .3)
    if name == 'global_scale':
        settings['global_scale'] = 2.
    if name == 'weighted_rest':
        armature = bpy.data.armatures.new('Fidelity rig')
        rig = bpy.data.objects.new('Fidelity rig', armature)
        bpy.context.scene.collection.objects.link(rig)
        bpy.context.view_layer.objects.active = rig
        rig.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bone = armature.edit_bones.new('Main')
        bone.head, bone.tail = (0, 0, 0), (0, 0, 1)
        bpy.ops.object.mode_set(mode='OBJECT')
        rig.pose.bones['Main'].rotation_mode = 'XYZ'
        rig.pose.bones['Main'].rotation_euler = (.5, -.2, .7)
        rig.pose.bones['Main'].location = (1., .5, .3)
        obj.vertex_groups.new(name='Main').add([0, 1, 2], 1., 'REPLACE')
        obj.vertex_groups.new(name='HelperNotABone').add([0, 1, 2], .5, 'REPLACE')
        modifier = obj.modifiers.new('Posed armature', 'ARMATURE')
        modifier.object = rig
        bpy.context.view_layer.objects.active = obj
        settings['pose'] = {'rotation': (.5, -.2, .7), 'location': (1., .5, .3)}
    if group in ('uv_mapping', 'cfg_materials') or name == 'image_alpha':
        material, wrapper = _textured(obj, directory)
    else:
        roughness = {'roughness_0': 0., 'roughness_half': .5, 'roughness_1': 1.}.get(name, 1.)
        material, wrapper = _material(obj, roughness=roughness, emission=name == 'emission')
    settings['shader'] = {'base_color': tuple(wrapper.base_color), 'alpha': wrapper.alpha,
                          'roughness': wrapper.roughness, 'specular': wrapper.specular,
                          'emission_color': tuple(wrapper.emission_color),
                          'emission_strength': wrapper.emission_strength,
                          'image': 'arrow-checker.png' if group in ('uv_mapping', 'cfg_materials') or name == 'image_alpha' else None}
    if group == 'uv_mapping':
        second = obj.data.uv_layers.new(name='Rendering')
        for slot, uv in zip(second.uv, ((.71, .62), (.91, .53), (.67, .98))):
            slot.vector = uv
        second.active_render = True
        obj.data.uv_layers.active_index = 0
        settings['uv_source'] = 'Rendering'
        if name == 'named_uv':
            uv_node = material.node_tree.nodes.new('ShaderNodeUVMap')
            # Named map differs from both editing and render defaults.
            obj.data.uv_layers['Editing'].active_render = True
            uv_node.uv_map = 'Rendering'
            material.node_tree.links.new(uv_node.outputs['UV'], wrapper.base_color_texture.node_image.inputs['Vector'])
            settings['uv_source'] = 'Rendering'
        elif name.startswith('mapping_'):
            nodes, links = material.node_tree.nodes, material.node_tree.links
            mapping = nodes.new('ShaderNodeMapping')
            mode = name.removeprefix('mapping_').upper()
            mapping.vector_type = mode
            if mapping.inputs.get('Location') is not None:
                mapping.inputs['Location'].default_value = MAPPING_LOCATION
            mapping.inputs['Rotation'].default_value = MAPPING_ROTATION
            mapping.inputs['Scale'].default_value = MAPPING_SCALE
            coords = nodes.new('ShaderNodeTexCoord')
            links.new(coords.outputs['UV'], mapping.inputs['Vector'])
            links.new(mapping.outputs['Vector'], wrapper.base_color_texture.node_image.inputs['Vector'])
            settings['mapping'] = {'mode': mode, 'location': MAPPING_LOCATION,
                                   'rotation': MAPPING_ROTATION, 'scale': MAPPING_SCALE}
    if group == 'cfg_materials':
        if name == 'cfg_alpha':
            material['o3d_alpha_mode'] = 'CLIP'
        else:
            material['cfg_data'] = [['[matl_allcolor]', *[str(v) for v in
                (.2, .3, .4, .55, .1, .2, .3, .4, .5, .6, .7, .8, .9, 32.)]]]
    bpy.context.view_layer.update()
    return obj, settings


CASES = {
    'custom_normal': ('oblique_triangle', 'flat_wedge', 'smooth_wedge', 'uv_seam', 'nonplanar_quad', 'concave_ngon'),
    'transforms': ('identity', 'positive_scale', 'negative_scale', 'nonuniform_scale', 'translation',
                   'euler_rotation', 'quaternion_rotation', 'parent_transform', 'global_scale',
                   'weighted_rest', 'empty_preserves_destination'),
    'materials': ('roughness_0', 'roughness_half', 'roughness_1', 'emission', 'image_alpha'),
    'uv_mapping': ('render_active', 'named_uv', 'mapping_point', 'mapping_texture', 'mapping_vector'),
    'cfg_materials': ('cfg_alpha', 'cfg_allcolor'),
}


def _expected_corners(obj, settings, snapshot):
    """Independent Blender corner-domain/math oracle, not production helpers.

    C is the established XZY export basis; this tests construction fidelity,
    not an assertion about native renderer culling or normal-sign consumers.
    """
    matrix = Matrix.Scale(settings['global_scale'], 4) @ AXIS.to_4x4() @ obj.matrix_world
    normals = matrix.to_3x3().inverted().transposed()
    layer = next(layer for layer in snapshot['uv_layers'] if layer['name'] == settings.get('uv_source', 'Editing'))
    result = []
    for li, vi in enumerate(snapshot['loop_vertices']):
        position = matrix @ Vector(snapshot['vertices'][vi])
        normal = (normals @ Vector(snapshot['corner_normals'][li])).normalized()
        uv = Vector((*layer['uvs'][li], 0.))
        mapping = settings.get('mapping')
        if mapping:
            rotation = Euler(mapping['rotation'], 'XYZ').to_matrix()
            if mapping['mode'] == 'TEXTURE':
                uv = rotation.transposed() @ (uv - Vector(mapping['location']))
                uv = Vector(tuple(uv[i] / mapping['scale'][i] for i in range(3)))
            else:
                uv = rotation @ Vector(tuple(uv[i] * mapping['scale'][i] for i in range(3)))
                if mapping['mode'] == 'POINT':
                    uv += Vector(mapping['location'])
        result.append((*position, *normal, uv.x, 1 - uv.y))
    return result


def _assert_corners(records, expected):
    # Compare every emitted face corner, not just the first split vertex.
    actual = [records['vertices'][i] for tri in records['triangles'] for i in tri[:3]]
    assert actual, 'exported no corners'
    for vertex in actual:
        candidates = [v for v in expected if (Vector(v[:3]) - Vector(vertex[:3])).length < 2e-4]
        assert candidates, ('unexpected position', vertex, expected)
        assert any((Vector(v[6:8]) - Vector(vertex[6:8])).length < 2e-4 for v in candidates), ('UV', vertex, candidates)
        matching = [v for v in candidates if (Vector(v[6:8]) - Vector(vertex[6:8])).length < 2e-4]
        assert any((Vector(v[3:6]) - Vector(vertex[3:6])).length < 2e-4 for v in matching), ('normal direction', vertex, matching)
        assert math.isclose(Vector(vertex[3:6]).length, 1., abs_tol=2e-4), vertex
    for corner in expected:
        assert any(max(abs(a-b) for a, b in zip(vertex, corner)) < 2e-4 for vertex in actual), ('lost source corner', corner)


def _record(path):
    data = path.read_bytes()
    records = read_export(data)
    return {'file': path.name, 'sha256': hashlib.sha256(data).hexdigest(), 'size': len(data),
            'records': records, 'oriented_surface': oriented_surface(records),
            'material_texture_identities': records['materials']}


def _empty_regression(addon, directory, manifest):
    obj = _mesh('empty_rejection')
    obj.data.clear_geometry()
    manifest['input'] = _snapshot(obj)
    manifest['settings'] = {'version': 7, 'global_scale': 1., 'export_custom_normals': True,
                            'entry_point': 'export_mesh', 'reference': 'not configured for destination safety regression'}
    sentinel = b'keep existing output\x00\xff'
    # Temporary destination, never any supplied model or baseline asset.
    with tempfile.TemporaryDirectory(prefix='empty-sentinel-', dir=directory) as temporary:
        path = Path(temporary) / 'existing.o3d'
        path.write_bytes(sentinel)
        error = None
        try:
            addon.o3d_io.io_o3d_export.export_mesh(
                str(path), bpy.context, obj, obj.data, [value for row in Matrix.Identity(4) for value in row],
                obj.material_slots, 7, True)
        except ValueError as caught:
            error = str(caught)
        actual = path.read_bytes()
        manifest['sentinel'] = {'before_hex': sentinel.hex(), 'after_hex': actual.hex(), 'error': error}
        _json(directory / 'manifest.json', manifest)
        assert error is not None and 'vertex' in error, ('empty export not rejected', error)
        assert actual == sentinel, ('rejected empty export destroyed existing bytes', actual)


def _run_case(addon, reference, group, name, directory):
    directory.mkdir(parents=True, exist_ok=True)
    manifest = {'group': group, 'case': name, 'blender': bpy.app.version_string,
                'blender_build': bpy.app.build_hash.decode(), 'exporters': {}, 'checks': []}
    # Restore only things this test creates; never clear a caller's scene.
    collections = (bpy.data.objects, bpy.data.meshes, bpy.data.armatures, bpy.data.materials, bpy.data.images)
    before = [set(collection) for collection in collections]
    active = bpy.context.view_layer.objects.active
    selected = list(bpy.context.selected_objects)
    failures = []

    def check(label, assertion):
        try:
            assertion()
        except Exception as error:
            failures.append(f'{group}/{name}: {label}: {type(error).__name__}: {error}')
            manifest['checks'].append({'name': label, 'status': 'FAIL', 'error': str(error)})
        else:
            manifest['checks'].append({'name': label, 'status': 'PASS'})

    try:
        if name == 'empty_preserves_destination':
            check('rejected empty export preserves sentinel', lambda: _empty_regression(addon, directory, manifest))
        else:
            obj, settings = _make_case(group, name, directory)
            snapshot = _snapshot(obj)
            manifest['input'] = snapshot
            manifest['settings'] = settings
            manifest['expected_corners'] = _expected_corners(obj, settings, snapshot)
            image = directory / 'arrow-checker.png'
            if image.exists():
                manifest['texture'] = {'file': image.name, 'sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
                                       'rows_bottom_to_top': ['RBBB', 'GRBW', 'GGRA', 'YWGY']}
            # Complete and save every configured export before any fidelity assertion.
            for label in ('current', 'reference') if reference else ('current',):
                path = directory / f'{label}.o3d'
                entry = manifest['exporters'][label] = {'settings': {
                    'version': 7, 'local_transforms': ['LOC', 'ROT', 'SCA'], 'origin': True,
                    'global_scale': settings['global_scale'] if label == 'current' else 1.,
                    'weights': bool(obj.vertex_groups) if label == 'current' else False}}
                try:
                    target = obj
                    if label == 'current':
                        entry['input_transforms'] = {key: snapshot[key] for key in (
                            'location', 'scale', 'rotation_mode', 'rotation_euler', 'rotation_quaternion',
                            'matrix_world', 'parent_matrix_world')}
                        addon.o3d_io.io_o3d_export.do_export(str(path), bpy.context,
                            Matrix.Scale(settings['global_scale'], 4), True, 7, True, objects=[obj])
                    else:
                        # Reference lacks a global-scale option. Use a disposable object
                        # with the equivalent uniform position scale; never mutate source.
                        if settings['global_scale'] != 1:
                            target = obj.copy()
                            target.data = obj.data.copy()
                            bpy.context.scene.collection.objects.link(target)
                            target.scale *= settings['global_scale']
                            target.location *= settings['global_scale']
                            bpy.context.view_layer.update()
                        reference_input = _snapshot(target)
                        entry['input_transforms'] = {key: reference_input[key] for key in (
                            'location', 'scale', 'rotation_mode', 'rotation_euler', 'rotation_quaternion',
                            'matrix_world', 'parent_matrix_world')}
                        entry['settings']['global_scale_emulation'] = settings['global_scale']
                        reference(compatibility=False, transforms={'LOC', 'ROT', 'SCA'}, origin=True,
                                  weights=False).export([target], path)
                    entry.update(_record(path))
                except Exception as error:
                    entry.update(error=f'{type(error).__name__}: {error}', traceback=traceback.format_exc())
                    failures.append(f'{group}/{name}: {label} export: {error}')
                finally:
                    _json(directory / 'manifest.json', manifest)
            current = manifest['exporters']['current'].get('records')
            ref = manifest['exporters'].get('reference', {}).get('records')
            if current and ref:
                manifest['comparison'] = {
                    'oriented_surface_equal_5dp': _rounded(oriented_surface(current)) == _rounded(oriented_surface(ref)),
                    'materials_equal_5dp': _rounded(current['materials']) == _rounded(ref['materials']),
                    'matrix_equal_5dp': _rounded(current['matrix']) == _rounded(ref['matrix']),
                    'reference_limitations': 'No equality oracle for translation, parents, quaternion, nonuniform normals or skin widths.'}
            # Persist comparisons and raw data even if the first assertion fails.
            _json(directory / 'manifest.json', manifest)
            check('source mesh and modifier state unchanged', lambda: _assert_equal(_snapshot(obj), snapshot))
            if current:
                check('version and unencrypted output', lambda: _assert_equal(current['version'], 7))
                check('every source position/normal/UV corner preserved', lambda: _assert_corners(current, manifest['expected_corners']))
                check('all rest-space positions preserved', lambda: _assert_positions(current, manifest['expected_corners']))
                check('oriented triangles under established export basis', lambda: _assert_winding(current, snapshot, manifest['expected_corners'], obj, settings))
                check('triangle count', lambda: _assert_equal(len(current['triangles']), len(snapshot['loop_triangles'])))
                check('stored origin frame', lambda: _assert_matrix(current['matrix'], obj, settings['global_scale']))
                if group == 'transforms':
                    check('finite unit normal directions', lambda: _assert_unit_normals(current))
                    check('one source direction across equivalent corners', lambda: _assert_one_direction(current))
                if name == 'translation':
                    control = obj.copy()
                    bpy.context.scene.collection.objects.link(control)
                    control.location = (0., 0., 0.)
                    bpy.context.view_layer.update()
                    path = directory / 'translation-control.o3d'
                    addon.o3d_io.io_o3d_export.do_export(str(path), bpy.context, Matrix.Identity(4), True, 7, True, objects=[control])
                    manifest['translation_control'] = _record(path)
                    check('translation cannot enter normal direction', lambda: _assert_translation_invariant(
                        current, manifest['translation_control']['records']))
                if name == 'weighted_rest':
                    check('rest weights, filtered helpers and modifier restoration', lambda: _assert_rest(current, obj))
                if name == 'emission':
                    check('emission color times strength', lambda: assert_emission_record(current['materials'][0]))
                if name.startswith('roughness_'):
                    manifest['authoring_policy_comparison'] = {
                        'current_exponent': current['materials'][0][10],
                        'reference_linear_1000_exponent': 1000 * (1 - settings['shader']['roughness']),
                        'status': 'observation only; PBR-to-O3D exponent policy not a native fact'}
                if group == 'cfg_materials':
                    check('CFG material command/embedded separation', lambda: _cfg_check(addon, obj, directory, name, manifest))
                # Only use reference equality on bounded, compatible construction cases.
                if ref and group == 'custom_normal':
                    check('oriented reference surface including winding', lambda: _assert_equal(
                        _rounded(oriented_surface(current)), _rounded(oriented_surface(ref))))
    except Exception as error:
        failures.append(f'{group}/{name}: setup: {type(error).__name__}: {error}')
        manifest['setup_error'] = traceback.format_exc()
    finally:
        manifest['failures'] = failures
        manifest['status'] = 'FAIL' if failures else 'PASS'
        _json(directory / 'manifest.json', manifest)
        if bpy.context.object and bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        for collection, existing in zip(collections, before):
            for item in set(collection) - existing:
                collection.remove(item, do_unlink=True)
        bpy.ops.object.select_all(action='DESELECT')
        for obj in selected:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = active
    return manifest


def _assert_equal(actual, expected):
    assert actual == expected, (actual, expected)


def _assert_positions(records, expected):
    for vertex in records['vertices']:
        assert any((Vector(vertex[:3]) - Vector(v[:3])).length < 2e-4 for v in expected), vertex
    for v in expected:
        assert any((Vector(vertex[:3]) - Vector(v[:3])).length < 2e-4 for vertex in records['vertices']), v


def _assert_winding(records, snapshot, expected, obj, settings):
    def cyclic(indices):
        return min(indices[i:] + indices[:i] for i in range(3))
    mapping = {}
    for i, vertex in enumerate(records['vertices']):
        loop = min(range(len(expected)), key=lambda li: (Vector(vertex[:3]) - Vector(expected[li][:3])).length)
        mapping[i] = snapshot['loop_vertices'][loop]
    mirrored = (Matrix.Scale(settings['global_scale'], 3) @ AXIS @ obj.matrix_world.to_3x3()).determinant() < 0
    want = []
    for loops in snapshot['loop_triangles']:
        indices = tuple(snapshot['loop_vertices'][li] for li in loops)
        want.append(cyclic(indices[::-1] if mirrored else indices))
    actual = [cyclic(tuple(mapping[i] for i in triangle[:3])) for triangle in records['triangles']]
    assert sorted(actual) == sorted(want), (actual, want)


def _assert_unit_normals(records):
    for vertex in records['vertices']:
        assert all(math.isfinite(value) for value in vertex), vertex
        assert math.isclose(Vector(vertex[3:6]).length, 1., abs_tol=2e-4), vertex


def _assert_translation_invariant(translated, control):
    # UV labels identify corresponding corners without relying on index order.
    for vertex in translated['vertices']:
        source = next(v for v in control['vertices'] if v[6:8] == vertex[6:8])
        assert_direction(vertex[3:6], source[3:6])


def _assert_one_direction(records):
    first = records['vertices'][0][3:6]
    for vertex in records['vertices']:
        assert_direction(vertex[3:6], first)


def _assert_matrix(actual, obj, scale):
    axis = AXIS.to_4x4()
    expected = (axis @ Matrix.Scale(scale, 4) @ obj.matrix_world @ axis).transposed()
    assert max(abs(actual[i][j] - expected[i][j]) for i in range(4) for j in range(4)) < 2e-4, (actual, expected)


def _assert_rest(records, obj):
    assert [name for name, _ in records['bones']] == ['Main'], records['bones']
    assert records['bones'][0][1] == [(i, 1.) for i in range(len(records['vertices']))], records['bones']
    assert obj.modifiers[0].show_viewport and obj.modifiers[0].show_render


def _cfg_check(addon, obj, directory, name, manifest):
    path = directory / 'current.cfg'
    obj['export_path'] = 'cfg-mesh.o3d'
    addon.o3d_io.io_o3d_export.do_export(str(path), bpy.context, Matrix.Identity(4), True, 7, True, objects=[obj])
    text = path.read_text(encoding='cp1252')
    manifest['cfg'] = {'file': path.name, 'text': text,
                       'records': read_export((directory / 'cfg-mesh.o3d').read_bytes()),
                       'evidence_class': 'Blender CFG serialization only; not native precedence'}
    _json(directory / 'manifest.json', manifest)
    assert '[matl]\narrow-checker.png\n0' in text, text
    if name == 'cfg_alpha':
        assert '[matl_alpha]\n1' in text, text
    else:
        assert '[matl_allcolor]' in text and '32.0' in text, text
    assert manifest['cfg']['records']['materials'] == manifest['exporters']['current']['records']['materials']


def run_checks(addon, names: list[str] | None = None) -> None:
    """All requested cases run and save diagnostics before an aggregate failure."""
    names = list(GROUPS) if names is None else names
    unknown = set(names) - set(GROUPS)
    if unknown:
        raise ValueError(f'unknown fidelity case groups: {sorted(unknown)}; choose {GROUPS}')
    reference = _reference_exporter(REFERENCE) if REFERENCE is not None else None
    output = Path(OUTPUT_DIR).resolve()
    output.mkdir(parents=True, exist_ok=True)
    manifests = []
    for group in names:
        for name in CASES[group]:
            manifest = _run_case(addon, reference, group, name, output / group / name)
            manifests.append(manifest)
            print(f'FIDELITY {group}/{name}: {manifest["status"]}')
    source = Path(addon.__file__).resolve().parent
    current_files = [source / 'o3d_io' / name for name in ('io_o3d_export.py', 'blender_compat.py', 'o3dconvert.py')]
    reference_files = [Path(REFERENCE) / 'io_export_o3d' / name for name in ('exporter.py', 'node_shader.py', 'meshio.py')] if REFERENCE else []
    summary = {'blender': bpy.app.version_string, 'blender_build': bpy.app.build_hash.decode(),
               'source_sha256': {str(path.relative_to(source)) if path.is_relative_to(source) else str(path):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in current_files + reference_files},
               'reference_requested': str(REFERENCE) if REFERENCE is not None else None,
               'groups': names, 'cases': [{'group': m['group'], 'case': m['case'], 'status': m['status'],
                                          'failures': m['failures'],
                                          'manifest': f'{m["group"]}/{m["case"]}/manifest.json'} for m in manifests]}
    _json(output / 'summary.json', summary)
    failures = [failure for m in manifests for failure in m['failures']]
    assert not failures, '\n'.join(failures) + f'\nAll configured case manifests saved in {output}'
    print('BLENDER_O3D_EXPORT_FIDELITY_OK', bpy.app.version_string)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', action='append', choices=GROUPS)
    parser.add_argument('--compare-reference', type=Path)
    parser.add_argument('--output-dir', type=Path, default=OUTPUT_DIR)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    OUTPUT_DIR, REFERENCE = args.output_dir, args.compare_reference
    # Validate requested external input before touching registration/scene state.
    if REFERENCE is not None:
        _reference_exporter(REFERENCE)
    addon = load_addon()
    addon.register()
    try:
        run_checks(addon, args.case)
    finally:
        addon.unregister()
