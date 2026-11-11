"""Synthetic export fidelity checkpoint; geometry/materials repaired, UV cases still RED.

Standalone owns add-on registration. run_checks never does. No input .blend is
loaded or saved. Raw O3Ds/PNGs/CFGs stay in --output-dir, never in fixtures.
Reference output is comparison evidence, not authority for native rendering.
"""
import argparse
import hashlib
import contextlib
import io
import importlib
import json
import math
import struct
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
        normal = Vector((.3, .4, math.sqrt(.75)))
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


def _snapshot(obj, mesh=None):
    mesh = mesh if mesh is not None else obj.data
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
        'pose': [(m.object.name, m.object.data.pose_position,
                  [(b.name, tuple(b.location), tuple(b.rotation_euler), tuple(b.rotation_quaternion), tuple(b.scale))
                   for b in m.object.pose.bones])
                 for m in obj.modifiers if m.type == 'ARMATURE' and m.object],
        'materials': [slot.material.name if slot.material else None for slot in obj.material_slots],
    }


def _evaluated_rest_snapshot(obj, custom=True):
    # Independent oracle: Blender evaluation, never production preparation.
    states = [(m, m.show_viewport, m.show_render) for m in obj.modifiers if m.type == 'ARMATURE']
    evaluated = mesh = None
    try:
        for modifier, _, _ in states:
            modifier.show_viewport = modifier.show_render = False
        depsgraph = bpy.context.evaluated_depsgraph_get()
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
        if not custom and mesh.has_custom_normals:
            mesh.attributes.remove(mesh.attributes['custom_normal'])
        return _snapshot(obj, mesh)
    finally:
        if mesh is not None:
            evaluated.to_mesh_clear()
        for modifier, viewport, render in states:
            modifier.show_viewport, modifier.show_render = viewport, render


def _assert_prepared_space(addon, obj, settings, snapshot):
    matrix = Matrix.Scale(settings['global_scale'], 4) @ AXIS.to_4x4() @ obj.matrix_world
    expected = [matrix @ Vector(co) for co in snapshot['vertices']]
    with addon.o3d_io.io_o3d_export.prepared_export_mesh(
            obj, bpy.context, Matrix.Scale(settings['global_scale'], 4)) as prepared:
        assert len(prepared) == 3
        evaluated, mesh, frame = prepared
        assert evaluated.original == obj and len(frame) == 16
        assert len(mesh.vertices) == len(expected)
        for vertex, position in zip(mesh.vertices, expected):
            assert (vertex.co - position).length < 2e-4, (vertex.co[:], position[:])
        # Human height reads this mesh directly: export Y must be baked height.
        assert math.isclose(max(v.co.y for v in mesh.vertices) - min(v.co.y for v in mesh.vertices),
                            max(v.y for v in expected) - min(v.y for v in expected), abs_tol=2e-4)


def _context_snapshot():
    return (bpy.context.view_layer.objects.active, set(bpy.context.selected_objects),
            bpy.context.object.mode if bpy.context.object else None)


def _restoration_regression(addon, obj, directory, snapshot):
    exporter = addon.o3d_io.io_o3d_export
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    context = _context_snapshot()
    sentinel = b'codec failure must not truncate\x00\xff'
    path = directory / 'failure-sentinel.o3d'
    path.write_bytes(sentinel)
    codec = exporter.o3dconvert.export_o3d
    try:
        exporter.do_export(str(directory / 'edit-success.o3d'), bpy.context, Matrix.Identity(4), True, 7)
        assert _context_snapshot() == context
        # Packing failure after successful real codec validation/writes must
        # still happen before the existing destination is opened.
        def fail_after_codec(*args, **kwargs):
            codec(*args, **kwargs)
            raise RuntimeError('induced codec failure')
        exporter.o3dconvert.export_o3d = fail_after_codec
        try:
            exporter.do_export(str(path), bpy.context, Matrix.Identity(4), True, 7)
        except RuntimeError as error:
            assert str(error) == 'induced codec failure'
        else:
            raise AssertionError('expected induced codec failure')
        assert _context_snapshot() == context
        assert path.read_bytes() == sentinel, 'induced codec failure truncated destination'
    finally:
        exporter.o3dconvert.export_o3d = codec
        bpy.ops.object.mode_set(mode='OBJECT')
    _assert_equal(_snapshot(obj), snapshot)


def _make_case(group, name, directory):
    custom = group == 'transforms' or name in ('oblique_triangle', 'custom_quad', 'custom_ngon')
    vertices = faces = None
    if name in ('flat_wedge', 'smooth_wedge', 'flat_transform', 'smooth_transform',
                'uv_seam', 'weighted_rest', 'evaluated_weights'):
        vertices = [(0, 0, 0), (2, 0, 0), (.2, 1.3, 0), (.2, .3, 1.1)]
        faces = [(0, 1, 2), (1, 0, 3)]
    elif name in ('nonplanar_quad', 'custom_quad'):
        vertices, faces = [(0, 0, 0), (2, 0, 0), (2, 1, .35), (0, 1, 0)], [(0, 1, 2, 3)]
    elif name == 'degenerate_face':
        vertices, faces = [(0, 0, 0), (1, 0, 0), (2, 0, 0)], [(0, 1, 2)]
    elif name in ('concave_ngon', 'custom_ngon'):
        vertices = [(0, 0, 0), (2, 0, 0), (2, 2, 0), (1, .7, 0), (0, 2, 0)]
        faces = [(0, 1, 2, 3, 4)]
    obj = _mesh(name, vertices, faces, custom=custom)
    settings = {'global_scale': 1., 'version': 7, 'local_transforms': ['LOC', 'ROT', 'SCA'],
                'origin': True, 'reference_weights': False, 'export_custom_normals': True}
    if name in ('custom_quad', 'custom_ngon'):
        obj.data.normals_split_custom_set([Vector((.15 + i * .07, .4, 1)).normalized()
                                          for i in range(len(obj.data.loops))])
    if name in ('flat_wedge', 'flat_transform'):
        for p in obj.data.polygons:
            p.use_smooth = False
    if name in ('flat_transform', 'smooth_transform', 'custom_quad', 'custom_ngon'):
        obj.scale = (-2., .7, 1.4)
        obj.rotation_euler = (.31, -.27, .49)
    if name in ('uv_seam', 'weighted_rest', 'evaluated_weights'):
        for slot, uv in zip(obj.data.uv_layers.active.uv,
                            ((.1, .2), (.8, .2), (.3, .9), (.9, .8), (.6, .7), (.2, .1))):
            slot.vector = uv
    transforms = {
        'positive_scale': ('scale', (2., 2., 2.)),
        'negative_scale': ('scale', (-1., 1., 1.)),
        'nonuniform_scale': ('scale', (2., .7, 1.4)),
        'translation': ('location', (2., -3., 4.)),
        'zero_scale': ('scale', (0., 1., 1.)),
        'singular_line': ('scale', (0., 0., 1.)),
        'singular_point': ('scale', (0., 0., 0.)),
        'near_singular': ('scale', (1e-8, .7, 1.4)),
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
    if name in ('weighted_rest', 'evaluated_weights'):
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
        obj.vertex_groups.new(name='Main').add(list(range(len(obj.data.vertices))), 1., 'REPLACE')
        obj.vertex_groups.new(name='HelperNotABone').add(list(range(len(obj.data.vertices))), .5, 'REPLACE')
        modifier = obj.modifiers.new('Posed armature', 'ARMATURE')
        modifier.object = rig
        bpy.context.view_layer.objects.active = obj
        if name == 'evaluated_weights':
            mirror = obj.modifiers.new('Evaluated topology', 'MIRROR')
            mirror.use_mirror_merge = False
            for index in range(len(obj.data.vertices)):
                obj.vertex_groups['Main'].add([index], .25 + .15 * index, 'REPLACE')
            obj.location = (.4, -.2, .3)
            obj.rotation_euler = (.31, -.27, .49)
            obj.scale = (-2., .7, 1.4)
        settings['pose'] = {'rotation': (.5, -.2, .7), 'location': (1., .5, .3)}
    if name == 'custom_disabled':
        settings['export_custom_normals'] = False
    if group in ('uv_mapping', 'cfg_materials') or name == 'image_alpha':
        material, wrapper = _textured(obj, directory)
    else:
        roughness = {'roughness_0': 0., 'roughness_quarter': .25, 'roughness_half': .5, 'roughness_1': 1.}.get(name, 1.)
        material, wrapper = _material(obj, roughness=roughness, emission=name in ('emission', 'emission_zero'))
    if name == 'emission_zero':
        wrapper.emission_strength = 0.
    if name == 'image_alpha':
        wrapper.base_color = (.8, .8, .8)
        wrapper.alpha = .25
        socket = wrapper.node_principled_bsdf.inputs['Alpha']
        for link in list(socket.links):
            material.node_tree.links.remove(link)
        wrapper.base_color_texture.image.pixels = [1.] * len(wrapper.base_color_texture.image.pixels)
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
    'custom_normal': ('oblique_triangle', 'flat_wedge', 'smooth_wedge', 'uv_seam', 'nonplanar_quad', 'concave_ngon',
                      'custom_quad', 'custom_ngon', 'flat_transform', 'smooth_transform', 'degenerate_face'),
    'transforms': ('identity', 'positive_scale', 'negative_scale', 'nonuniform_scale', 'translation',
                   'euler_rotation', 'quaternion_rotation', 'parent_transform', 'global_scale',
                   'weighted_rest', 'evaluated_weights', 'custom_disabled', 'zero_scale',
                   'singular_line', 'singular_point', 'near_singular', 'empty_preserves_destination'),
    'materials': ('roughness_0', 'roughness_quarter', 'roughness_half', 'roughness_1', 'emission', 'emission_zero', 'image_alpha',
                  'native_power_0', 'native_power_32', 'native_power_500', 'native_power_1500',
                  'native_components', 'native_cfg_overrides', 'constant_nodes', 'non_node_constants',
                  'active_unsupported_output', 'active_supported_output', 'unsupported_paths', 'cfg_image_paths'),
    'uv_mapping': ('render_active', 'named_uv', 'mapping_point', 'mapping_texture', 'mapping_vector'),
    'cfg_materials': ('cfg_alpha', 'cfg_allcolor'),
}


def _expected_corners(obj, settings, snapshot):
    """Independent Blender corner-domain/math oracle, not production helpers.

    C is the established XZY export basis; this tests construction fidelity,
    not an assertion about native renderer culling or normal-sign consumers.
    """
    matrix = Matrix.Scale(settings['global_scale'], 4) @ AXIS.to_4x4() @ obj.matrix_world
    linear = matrix.to_3x3()
    # At singular transforms no authored inverse-transpose direction exists.
    # Zero explicitly represents undefined, not a guessed unit axis.
    normals = linear.inverted().transposed() if linear.determinant() else Matrix(((0.,) * 3,) * 3)
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
        assert math.isclose(Vector(vertex[3:6]).length, Vector(matching[0][3:6]).length, abs_tol=2e-4), vertex
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


def _material_regression(addon, name, directory):
    exporter = addon.o3d_io.io_o3d_export
    importer = addon.o3d_io.io_o3d_import
    parser = addon.o3d_io.o3d_cfg_parser
    obj = _mesh(name)

    def export():
        path = directory / 'roundtrip.o3d'
        exporter.do_export(str(path), bpy.context, Matrix.Identity(4), True, 7, True, objects=[obj])
        return read_export(path.read_bytes())['materials']

    if name == 'non_node_constants':
        material = bpy.data.materials.new('Non-node constant fixture')
        material.use_nodes = False
        if material.use_nodes:
            assert bpy.app.version >= (5, 0), bpy.app.version_string
            print('NON_NODE_UNAVAILABLE_ON_BUILD', bpy.app.version_string)
            return
        material.diffuse_color = (.2, .3, .4, .25)
        material.roughness = .25
        material.specular_intensity = .4
        obj.data.materials.append(material)
        tree = material.node_tree
        nodes = list(tree.nodes) if tree else []
        _assert_close(export()[0][:11], (.2,.3,.4,1.,0.,0.,0.,0.,0.,0.,750.))
        assert not material.use_nodes and material.node_tree == tree
        assert (list(tree.nodes) if tree else []) == nodes
        return

    if name.startswith('native_'):
        power = float(name.rsplit('_', 1)[1]) if name.startswith('native_power_') else 32.
        raw = (.2, .4, .6, .25, 1.2, .3, .7, 2., .9, 1.2, power, 'MISSING.PNG')
        cfg = {}
        records = [raw]
        if name == 'native_cfg_overrides':
            # Nonadjacent duplicates, ASCII-only normalization, no slash folding.
            records = [raw, (*raw[:11], 'OTHER.PNG'), (*raw[:11], 'missing.png'),
                       (*raw[:11], 'Ä.PNG'), (*raw[:11], 'ä.png'), (*raw[:11], '')]
            block = ['.1', '.2', '.3', '.4', '.5', '.6', '.7', '.8', '.9', '1', '2', '3', '4', '1500']
            path = directory / 'input.cfg'
            _image(directory)
            path.write_text('[mesh]\ninput.o3d\n[matl]\nOTHER.PNG\n0\n[matl_envmap]\nenv.bmp\n.7\n[matl_alpha]\n2\n[matl_nightmap]\narrow-checker.png\n[matl]\nmissing.png\n1\n[matl_envmap]\nenv.bmp\n.6\n[matl_allcolor]\n' + '\n'.join(block) +
                            '\n[matl_noZwrite]\n[matl_noZcheck]\n[alphascale]\nalpha_var\n[matl]\nä.png\n0\n[matl_allcolor]\n' + '\n'.join(block) +
                            '\n[matl]\n\n0\n[matl_allcolor]\n' + '\n'.join(block) + '\n', encoding='cp1252')
            cfg = parser.read_cfg(str(path), '')[0][-1]['meshes']['input.o3d']['matls']
        # Exercise the real binary codec on input, not a hand-built parser tuple.
        binary = io.BytesIO()
        addon.o3d_io.o3dconvert.export_o3d(binary, [(0,0,0,0,0,1,0,0), (1,0,0,0,0,1,1,0), (0,1,0,0,0,1,0,1)],
                                           [(0,1,2,0)], records, [], None)
        decoded = addon.o3d_io.o3dconvert.import_o3d(binary.getvalue())[3]
        importer.generate_materials(cfg, str(directory / 'input.cfg'), 0, decoded, obj.data)
        material = obj.data.materials[0]
        wrapper = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=False)
        _assert_close((wrapper.roughness,), ({0.: 1., 32.: .968, 500.: .5, 1500.: 0.}[power],))
        _assert_close(wrapper.emission_color[:3], (2., .9, 1.2))
        assert wrapper.emission_strength == 1.
        first = export()
        for index, (actual, expected) in enumerate(zip(first, records)):
            expected = expected[:11] if name != 'native_cfg_overrides' or index not in (2, 4, 5) else (*expected[:10], 1500.)
            assert struct.pack('<11f', *actual[:11]) == struct.pack('<11f', *expected), (index, actual, expected)
        wrapper.roughness = .25
        edited = export()[0]
        _assert_close(edited[:10], raw[:10])
        assert edited[10] == 750.
        if name == 'native_components':
            wrapper.alpha = .75
            alpha_edit = export()[0]
            _assert_close(alpha_edit[:4], (.2, .4, .6, .75))
            _assert_close(alpha_edit[4:10], raw[4:10])
            wrapper.emission_strength = 0.
            _assert_close(export()[0][7:10], (0., 0., 0.))
            wrapper.specular = .5
            _assert_close(export()[0][4:7], (.5, .125, 7 / 24))
            # Changing image identity is a relevant diffuse edit, unlike roughness.
            wrapper.base_color_texture.image = _image(directory)
            _assert_close(export()[0][:4], (1., 1., 1., .75))
        if name == 'native_cfg_overrides':
            env = obj.data.materials[1]
            env_preview = node_shader_utils.PrincipledBSDFWrapper(env, is_readonly=True)
            _assert_close((env_preview.roughness, env['o3d_specular_roughness']), (.01, .01))
            assert env['o3d_specular_power'] == 32.
            assert env_preview.emission_color_texture.image is not None
            for index in (2, 4, 5):
                mat = obj.data.materials[index]
                preview = node_shader_utils.PrincipledBSDFWrapper(mat, is_readonly=True)
                assert mat['o3d_specular_power'] == 1500.
                assert preview.roughness == mat['o3d_specular_roughness'] == 0.
                assert any(list(b) == ['[matl_allcolor]', *block] for b in mat['cfg_data'])
            assert obj.data.materials[3]['o3d_specular_power'] == 32.
            assert any(list(b) == ['[matl_noZwrite]'] for b in obj.data.materials[2]['cfg_data'])
            assert any(list(b) == ['[alphascale]', 'alpha_var'] for b in obj.data.materials[2]['cfg_data'])
            before = export()
            stream = io.StringIO()
            parser.write_cfg_materials(stream, obj, str(directory / 'output.cfg'))
            assert '[matl_allcolor]' in stream.getvalue()
            assert export() == before, 'CFG writer mutated embedded components'
        return

    material, wrapper = _material(obj)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = wrapper.node_principled_bsdf
    if name.startswith('active_'):
        inactive = nodes.get('Export')
        active = nodes.new('ShaderNodeOutputMaterial')
        active.is_active_output = True
        assert active.is_active_output and not inactive.is_active_output
        if name == 'active_unsupported_output':
            tree = bpy.data.node_groups.new('Unsupported Active Surface', 'ShaderNodeTree')
            tree.interface.new_socket(name='Shader', in_out='OUTPUT', socket_type='NodeSocketShader')
            group = nodes.new('ShaderNodeGroup')
            group.node_tree = tree
            links.new(group.outputs['Shader'], active.inputs['Surface'])
        else:
            supported = nodes.new('ShaderNodeBsdfPrincipled')
            supported.inputs['Base Color'].default_value = (.1, .2, .3, 1.)
            supported.inputs['Alpha'].default_value = .25
            supported.inputs['Roughness'].default_value = .25
            supported.inputs['Specular IOR Level'].default_value = 0.
            links.new(supported.outputs['BSDF'], active.inputs['Surface'])
        before = [(link.from_socket, link.to_socket) for link in links]
        try:
            actual = export()[0]
        except ValueError as error:
            assert 'material' in str(error).lower(), str(error)
            assert ('unsupported' if name == 'active_unsupported_output' else 'ambiguous') in str(error).lower(), str(error)
            assert not (directory / 'roundtrip.o3d').exists(), 'refusal published output'
        else:
            assert name == 'active_supported_output', 'active unsupported surface silently exported inactive Principled'
            _assert_close(actual[:4], (.1, .2, .3, .25))
            assert actual[10] == 750., actual
        assert active.is_active_output and not inactive.is_active_output
        assert [(link.from_socket, link.to_socket) for link in links] == before
    elif name == 'constant_nodes':
        rgb = nodes.new('ShaderNodeRGB')
        rgb.outputs[0].default_value = (.2, .3, .4, 1.)
        value = nodes.new('ShaderNodeValue')
        value.outputs[0].default_value = .25
        strength = nodes.new('ShaderNodeValue')
        strength.outputs[0].default_value = 3.
        for socket in ('Base Color', 'Emission Color', 'Specular Tint'):
            links.new(rgb.outputs[0], shader.inputs[socket])
        for socket in ('Alpha', 'Roughness', 'Specular IOR Level'):
            links.new(value.outputs[0], shader.inputs[socket])
        links.new(strength.outputs[0], shader.inputs['Emission Strength'])
        _assert_close(export()[0][:11], (.2,.3,.4,.25,.05,.075,.1,.6,.9,1.2,750.))
    elif name == 'unsupported_paths':
        for kind in ('alpha_base', 'strength_image', 'math', 'group', 'surface'):
            test = material.copy()
            obj.data.materials[0] = test
            graph = test.node_tree
            principled = graph.nodes.get('Principled BSDF')
            image = graph.nodes.new('ShaderNodeTexImage')
            image.image = _image(directory)
            if kind == 'alpha_base':
                graph.links.new(image.outputs['Alpha'], principled.inputs['Base Color'])
            elif kind == 'strength_image':
                graph.links.new(image.outputs['Color'], principled.inputs['Emission Strength'])
            elif kind == 'math':
                math_node = graph.nodes.new('ShaderNodeMath')
                graph.links.new(math_node.outputs[0], principled.inputs['Roughness'])
            elif kind == 'group':
                group = graph.nodes.new('ShaderNodeGroup')
                tree = bpy.data.node_groups.new('Unsupported', 'ShaderNodeTree')
                tree.interface.new_socket(name='Color', in_out='OUTPUT', socket_type='NodeSocketColor')
                group.node_tree = tree
                graph.links.new(group.outputs[0], principled.inputs['Base Color'])
            else:
                graph.links.new(graph.nodes.new('ShaderNodeEmission').outputs[0], graph.nodes.get('Export').inputs['Surface'])
            try:
                export()
            except ValueError as error:
                assert 'material' in str(error).lower() and ('unsupported' in str(error).lower() or 'cannot' in str(error).lower()), str(error)
            else:
                raise AssertionError(f'unsupported {kind} silently exported destination defaults')
        obj.data.materials[0] = material
    elif name == 'cfg_image_paths':
        wrapper.base_color_texture.image = _image(directory)
        wrapper.alpha = .25
        wrapper.specular = .4
        wrapper.specular_tint = (.2, .3, .4)
        wrapper.roughness = .01
        wrapper.emission_color = (.2, .3, .4)
        wrapper.emission_strength = 3.
        wrapper.alpha_texture.image = wrapper.base_color_texture.image
        wrapper.specular_texture.image = wrapper.base_color_texture.image
        wrapper.emission_color_texture.image = wrapper.base_color_texture.image
        addon.o3d_io.blender_compat.apply_bump_map(wrapper, wrapper.base_color_texture.image, .4)
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            actual = export()[0]
        _assert_close(actual[:10], (1,1,1,.25,.08,.12,.16,.2,.3,.4))
        assert 'fallback' in stdout.getvalue().lower() and 'not evaluated' in stdout.getvalue().lower(), stdout.getvalue()
        stream = io.StringIO()
        parser.write_cfg_materials(stream, obj, str(directory / 'output.cfg'))
        for command in ('[matl_alpha]', '[matl_envmap]', '[matl_envmap_mask]', '[matl_bumpmap]', '[matl_lightmap]'):
            assert command in stream.getvalue(), (command, stream.getvalue())
        wrapper.emission_strength = .5
        stream = io.StringIO()
        parser.write_cfg_materials(stream, obj, str(directory / 'output.cfg'))
        assert '[matl_nightmap]' in stream.getvalue()


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
        if name.startswith(('native_', 'active_')) or name in ('constant_nodes', 'non_node_constants', 'unsupported_paths', 'cfg_image_paths'):
            check('material import/export contract', lambda: _material_regression(addon, name, directory))
        elif name == 'empty_preserves_destination':
            check('rejected empty export preserves sentinel', lambda: _empty_regression(addon, directory, manifest))
        else:
            obj, settings = _make_case(group, name, directory)
            snapshot = _snapshot(obj)
            manifest['input'] = snapshot
            manifest['settings'] = settings
            expected_snapshot = _evaluated_rest_snapshot(obj, settings['export_custom_normals'])
            manifest['evaluated_rest'] = expected_snapshot
            manifest['expected_corners'] = _expected_corners(obj, settings, expected_snapshot)
            image = directory / 'arrow-checker.png'
            if image.exists():
                manifest['texture'] = {'file': image.name, 'sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
                                       'rows_bottom_to_top': ['RBBB', 'GRBW', 'GGRA', 'YWGY']}
            initial_context = _context_snapshot()
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
                            Matrix.Scale(settings['global_scale'], 4), True, 7, settings['export_custom_normals'], objects=[obj])
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
                    'reference_limitations': 'No equality oracle for polygon tessellation, translation, parents, quaternion, nonuniform normals or skin widths.'}
            # Persist comparisons and raw data even if the first assertion fails.
            _json(directory / 'manifest.json', manifest)
            check('source mesh and modifier state unchanged', lambda: _assert_equal(_snapshot(obj), snapshot))
            check('selection mode and active object unchanged', lambda: _assert_equal(_context_snapshot(), initial_context))
            if group in ('custom_normal', 'transforms'):
                check('prepared tuple and directly consumed GCM baked mesh',
                      lambda: _assert_prepared_space(addon, obj, settings, expected_snapshot))
            if name in ('identity', 'oblique_triangle') and current:
                check('literal oblique XZY normal contract', lambda: [assert_direction(v[3:6], (.3, math.sqrt(.75), .4))
                                                                     for v in current['vertices']])
            if current:
                check('version and unencrypted output', lambda: _assert_equal(current['version'], 7))
                check('every source position/normal/UV corner preserved', lambda: _assert_corners(current, manifest['expected_corners']))
                check('all rest-space positions preserved', lambda: _assert_positions(current, manifest['expected_corners']))
                check('oriented triangles under established export basis', lambda: _assert_winding(current, expected_snapshot, manifest['expected_corners'], obj, settings))
                check('triangle count', lambda: _assert_equal(len(current['triangles']), len(expected_snapshot['loop_triangles'])))
                check('stored origin frame', lambda: _assert_matrix(current['matrix'], obj, settings['global_scale']))
                if group == 'transforms':
                    check('finite unit normal directions', lambda: _assert_unit_normals(current, singular=not obj.matrix_world.determinant()))
                    if (settings['export_custom_normals'] and obj.matrix_world.determinant()
                            and name != 'evaluated_weights'):
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
                if name in ('weighted_rest', 'evaluated_weights'):
                    check('rest weights, filtered helpers and modifier restoration', lambda: _assert_rest(current, obj, expected_snapshot, manifest['expected_corners']))
                    check('success and induced failure restore context/pose/source',
                          lambda: _restoration_regression(addon, obj, directory, snapshot))
                if name == 'emission':
                    check('emission color times strength', lambda: assert_emission_record(current['materials'][0]))
                if name == 'emission_zero':
                    check('zero strength emits black', lambda: _assert_equal(current['materials'][0][7:10], (0., 0., 0.)))
                if name == 'image_alpha':
                    check('neutral image RGB and independent alpha', lambda: _assert_close(current['materials'][0][:4], (1., 1., 1., .25)))
                if name.startswith('roughness_'):
                    powers = {'roughness_0': 1000., 'roughness_quarter': 750., 'roughness_half': 500., 'roughness_1': 0.}
                    check('authored exponent policy', lambda: _assert_equal(current['materials'][0][10], powers[name]))
                    manifest['authoring_policy_comparison'] = {
                        'current_exponent': current['materials'][0][10],
                        'reference_linear_1000_exponent': 1000 * (1 - settings['shader']['roughness']),
                        'status': 'observation only; PBR-to-O3D exponent policy not a native fact'}
                if group == 'cfg_materials':
                    check('CFG material command/embedded separation', lambda: _cfg_check(addon, obj, directory, name, manifest))
                # Already-triangulated fixtures have compatible construction.
                # Polygon reference deltas remain observations above; source
                # corners and Blender's own loop triangles are their invariants.
                if ref and group == 'custom_normal' and all(len(face) == 3 for face in snapshot['faces']):
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


def _assert_close(actual, expected):
    assert len(actual) == len(expected) and all(math.isclose(a, b, abs_tol=2e-6) for a, b in zip(actual, expected)), (actual, expected)


def _assert_equal(actual, expected):
    assert actual == expected, (actual, expected)


def _assert_positions(records, expected):
    for vertex in records['vertices']:
        assert any((Vector(vertex[:3]) - Vector(v[:3])).length < 2e-4 for v in expected), vertex
    for v in expected:
        assert any((Vector(vertex[:3]) - Vector(v[:3])).length < 2e-4 for vertex in records['vertices']), v


def _assert_winding(records, snapshot, expected, obj, settings):
    # Ordered positions establish winding independently of shading normals.
    # UV labels only disambiguate coincident/collapsed corners, not direction.
    def label(vertex):
        return (*vertex[:3], *vertex[6:8]) if determinant == 0 else vertex[:3]
    determinant = (Matrix.Scale(settings['global_scale'], 3) @ AXIS @ obj.matrix_world.to_3x3()).determinant()
    want = []
    for loops in snapshot['loop_triangles']:
        corners = [label(expected[li]) for li in loops]
        want.append(corners[::-1] if determinant <= 0 else corners)
    for triangle in records['triangles']:
        actual = [label(records['vertices'][index]) for index in triangle[:3]]
        matches = [i for i, corners in enumerate(want) if any(
            all(max(abs(a-b) for a, b in zip(actual[j], corners[(j+offset) % 3])) < 2e-4
                for j in range(3)) for offset in range(3))]
        assert matches, ('unexpected oriented triangle', actual, want)
        want.pop(matches[0])
    assert not want, ('missing oriented triangles', want)


def _assert_unit_normals(records, singular=False):
    for vertex in records['vertices']:
        assert all(math.isfinite(value) for value in vertex), vertex
        assert math.isclose(Vector(vertex[3:6]).length, 0. if singular else 1., abs_tol=2e-4), vertex


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


def _assert_rest(records, obj, snapshot, expected):
    assert [name for name, _ in records['bones']] == ['Main'], records['bones']
    actual = dict(records['bones'][0][1])
    assert set(actual) == set(range(len(records['vertices']))), records['bones']
    for index, vertex in enumerate(records['vertices']):
        loops = [li for li, corner in enumerate(expected)
                 if max(abs(a-b) for a, b in zip(vertex, corner)) < 2e-4]
        weights = [dict(snapshot['weights'][snapshot['loop_vertices'][li]])['Main'] for li in loops]
        assert weights and any(math.isclose(actual[index], weight, abs_tol=2e-6) for weight in weights), (vertex, weights)
    assert len(records['vertices']) > len(snapshot['vertices']), 'UV seam lost its weighted splits'
    if any(m.type == 'MIRROR' for m in obj.modifiers):
        assert len(snapshot['vertices']) > len(obj.data.vertices), 'evaluated topology not exercised'
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
    current_files = [source / 'o3d_io' / name for name in ('io_o3d_export.py', 'io_o3d_import.py', 'o3d_cfg_parser.py', 'blender_compat.py', 'o3dconvert.py')]
    current_files.append(Path(__file__).resolve())
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
