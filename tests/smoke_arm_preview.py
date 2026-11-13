"""Public synthetic arm preview checks; no private scene or game assets.

blender --background --factory-startup --disable-autoexec --python-exit-code 1
--python tests/smoke_arm_preview.py [-- --check geometry]
"""
import argparse
import importlib
import math
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import warnings

import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from smoke_support import load_addon
from smoke_arm_normalization import (arm_fixture, bundle_fixture, close, matrix_close,
    mesh_state, preserve_context, rig_state, runtime_arm_matrices, runtime_cases)
from smoke_human import RecordingHumanLayout, cancel_native, select_only
from o3d_export_support import read_export


def modules(addon):
    return tuple(importlib.import_module(addon.__name__ + '.o3d_io.' + name)
                 for name in ('human_arm_preview', 'omsi_human', 'omsi_character_panel'))


def ids():
    return tuple(frozenset(item.as_pointer() for item in group) for group in
                 (bpy.data.objects, bpy.data.meshes, bpy.data.collections, bpy.data.materials))


def source_state(rig, meshes):
    state = rig_state(rig)
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=DeprecationWarning,
                                message=r"^'Material\.use_nodes' is expected to be removed in Blender 6\.0$")
        materials = tuple((m.as_pointer(), repr(dict(m.items())), tuple(m.diffuse_color), m.use_nodes)
                          for m in bpy.data.materials)
    return (state[:4], state[5:], repr([mesh_state(obj) for obj in meshes]),
            tuple((obj.hide_get(), obj.hide_viewport, obj.hide_render, obj.hide_select,
                   obj.parent, repr(dict(obj.items()))) for obj in (rig, *meshes)), materials)


def displayed(point):
    return Vector((point[0], point[2], point[1]))


def file_joints(links, points, turn_180):
    # Decode the final symmetric HUM links, never raw asymmetric bone heads.
    landmarks = {'OA': links[8:11], 'UA': links[11:14], 'Hand': links[16:19]}
    result = {}
    for side in ('L', 'R'):
        sign = -1 if points['OA_' + side].x * (-1 if turn_180 else 1) < 0 else 1
        for stem, (x, y, z) in landmarks.items():
            result[stem + '_' + side] = Vector((sign * x, z, y))
    return result


def assert_display(obj, records, matrices=None, *, smoothskin=True):
    # Decoded float32 O3D geometry/skin is independent of preview preparation.
    weights = [[] for _ in records['vertices']]
    for name, entries in records['bones']:
        for index, weight in entries:
            if math.isfinite(weight) and weight > 0:
                weights[index].append((name, weight))
    # Verify transport before Blender's short2 custom-normal encoding. Near
    # degenerate deformed fans can quantize by ~.003 on Blender 5.0.1.
    preview = next(module for name, module in sys.modules.items() if name.endswith('.o3d_io.human_arm_preview'))
    _, transported = preview._display_geometry(dict(verts=records['vertices'], bones=records['bones'],
                                                   smoothskin=smoothskin), matrices or {})
    for i, (vertex, raw) in enumerate(zip(obj.data.vertices, records['vertices'])):
        point, normal = Vector(raw[:3]), Vector(raw[3:6])
        if matrices is not None and weights[i]:
            binding = weights[i] if smoothskin else [max(weights[i], key=lambda entry: entry[1])]
            mass = sum(weight for _, weight in binding)
            point = sum((weight / mass * (matrices.get(name, Matrix.Identity(4)) @ point)
                         for name, weight in binding), Vector())
            normal = sum((weight / mass * (matrices.get(name, Matrix.Identity(4)).to_3x3() @ normal)
                          for name, weight in binding), Vector()).normalized()
        close(vertex.co, displayed(point))
        assert (Vector(transported[i]) - displayed(normal)).length < 2e-5
        for loop in (loop for loop in obj.data.loops if loop.vertex_index == i):
            close(obj.data.uv_layers.active.uv[loop.index].vector, (raw[6], 1 - raw[7]))
            # Native short2 storage; precise math is checked above independently.
            assert (obj.data.corner_normals[loop.index].vector - displayed(normal)).length < .004, (
                i, loop.index, tuple(normal), tuple(obj.data.corner_normals[loop.index].vector), weights[i])
    assert len(obj.data.vertices) == len(records['vertices'])
    assert [tuple(p.vertices) for p in obj.data.polygons] == [tuple(t[:3][::-1]) for t in records['triangles']]
    assert [p.material_index for p in obj.data.polygons] == [t[3] for t in records['triangles']]
    assert obj.parent is None and not obj.modifiers
    assert obj.hide_select and obj.hide_render and 'skip_export' in obj
    assert not obj.select_get()


def assert_arm_preview_controls(addon):
    # Catches missing/scene-global angle, lost forwarding, gait mutation,
    # expensive draw-time preview builds, and phase falsely invalidating readiness.
    panel = importlib.import_module(addon.__name__ + '.o3d_io.omsi_character_panel')
    assert 'arm_rest_angle' in panel.OMSIHumanSettings.bl_rna.properties, 'per-rig arm_rest_angle is missing'
    preview, human, panel = modules(addon)
    props = bpy.context.scene.omsi_character_data
    pointers = props.source_mesh, props.source_armature
    try:
        with preserve_context(), bundle_fixture(addon) as (rig, meshes, _, _, _), arm_fixture(addon) as (other, _):
            props.source_mesh, props.source_armature = meshes[0], rig
            select_only(rig)
            settings = rig.omsi_human_settings
            assert settings.arm_rest_angle == other.omsi_human_settings.arm_rest_angle == 0
            walk = settings.walk_params[:]
            settings.normalize_arms = True
            settings.arm_rest_angle = 15
            assert other.omsi_human_settings.arm_rest_angle == 0
            assert settings.walk_params[:] == walk
            plan, export, refresh = panel.normalization.build_arm_transforms, human.export_human, preview.refresh_preview
            plans, calls, previews = [], [], []
            def observed_plan(target, **kwargs):
                plans.append(kwargs)
                return plan(target, **kwargs)
            def observed_export(*args, **kwargs):
                calls.append((args, kwargs))
                return export(*args, **kwargs)
            def observed_preview(*args, **kwargs):
                previews.append((args, kwargs))
                return refresh(*args, **kwargs)
            panel.normalization.build_arm_transforms = observed_plan
            human.export_human, preview.refresh_preview = observed_export, observed_preview
            try:
                before = source_state(rig, meshes)
                assert bpy.ops.omsi.refresh_human_measurements() == {'FINISHED'}
                assert plans[-1]['rest_angle_degrees'] == 15
                assert bpy.ops.omsi.human_preflight() == {'FINISHED'}
                assert calls[-1][1]['arm_rest_angle'] == 15
                with tempfile.TemporaryDirectory(prefix='arm-preview-export-') as root:
                    assert bpy.ops.omsi.export_human(filepath=str(Path(root) / 'human.hum')) == {'FINISHED'}
                    assert calls[-1][1]['arm_rest_angle'] == 15
                assert source_state(rig, meshes) == before
                assert bpy.ops.omsi.preview_human_arms() == {'FINISHED'}
                assert previews[-1][0][1] is rig and previews[-1][0][2] == meshes
                assert previews[-1][1]['arm_rest_angle'] == 15
                assert preview.is_preview_active(rig) and not preview.is_preview_active(other)
                status = settings.status
                settings.arm_preview_pose = 'WALKING'
                settings.arm_preview_phase = .5
                assert settings.status == status
                assert previews[-1][1]['pose'] == 'WALKING' and previews[-1][1]['phase'] == .5
                count = len(previews)
                other.omsi_human_settings.arm_rest_angle = -15
                assert len(previews) == count
                settings.arm_rest_angle = -15
                assert len(previews) == count + 1 and previews[-1][1]['arm_rest_angle'] == -15
                assert settings.status == 'Settings changed; refresh/check again'
                assert settings.walk_params[:] == walk
                assert source_state(rig, meshes) == before
                for enabled in (False, True):
                    settings.normalize_arms = enabled
                    before, count = source_state(rig, meshes), len(previews)
                    layout = RecordingHumanLayout()
                    panel.VIEW3D_PT_omsi_character_human.draw(SimpleNamespace(layout=layout), bpy.context)
                    panel.VIEW3D_PT_omsi_character_arm_preview.draw(SimpleNamespace(layout=layout), bpy.context)
                    names = [name for kind, name, _ in layout.records if kind == 'prop']
                    assert ('arm_rest_angle' in names) is enabled
                    assert 'arm_preview_pose' in names and 'arm_preview_phase' in names
                    assert len(previews) == count and source_state(rig, meshes) == before
                    labels = ' '.join(name for kind, name, _ in layout.records if kind == 'label').lower()
                    assert 'diagnostic' in labels and 'static' in labels and '67' in labels
                preview.clear_preview()
                # Clear is drawn/enabled even if target resolution refuses.
                props.source_mesh, props.source_armature = None, None
                select_only()
                layout = RecordingHumanLayout()
                panel.VIEW3D_PT_omsi_character_human.draw(SimpleNamespace(layout=layout), bpy.context)
                panel.VIEW3D_PT_omsi_character_arm_preview.draw(SimpleNamespace(layout=layout), bpy.context)
                assert ('operator', 'omsi.clear_human_arm_preview', True) in layout.records
                assert bpy.ops.omsi.clear_human_arm_preview() == {'FINISHED'}
            finally:
                panel.normalization.build_arm_transforms = plan
                human.export_human, preview.refresh_preview = export, refresh
                preview.clear_preview()
    finally:
        props.source_mesh, props.source_armature = pointers


def assert_arm_preview_matrices(addon):
    # Wrong axes, side convention, hand multiplication order or seated beta
    # coupling breaks agreement with the pre-existing independent runtime oracle.
    preview, _, _ = modules(addon)
    for left_sign in (-1, 1):
        joints = {stem + '_' + side: Vector((sign * x, z, y))
                  for side, sign in (('L', left_sign), ('R', -left_sign))
                  for stem, x, y, z in (('OA', .2, .01, 1.4), ('UA', .49, .03, 1.3), ('Hand', .73, .02, 1.2))}
        for beta in (45, 80):
            for state, phase in runtime_cases():
                expected = runtime_arm_matrices(joints, state, phase, beta=beta)
                actual = preview.arm_pose_matrices(joints, state.upper(), phase, beta=beta)
                for name, matrix in expected.items():
                    matrix_close(actual[name], matrix)
                for name in ('Hip', 'Head', 'OS_L', 'US_R'):
                    matrix_close(actual[name], Matrix.Identity(4))
            assert all(matrix == Matrix.Identity(4) for matrix in preview.arm_pose_matrices(joints, 'REST').values())


def assert_arm_preview_skin_modes(addon):
    # Runtime admission comes from the serialized stream. This isolates absent
    # mass, finite positive admission, normalized blends and first-bone tie order.
    preview, _, _ = modules(addon)
    geometry = {'verts': [[1, 2, 3, 0, 1, 0, 0, 0]] * 4,
                'bones': [('OA_L', [(0, .4), (1, .1), (2, 0), (3, float('nan'))]),
                          ('UA_L', [(0, .4), (1, .8), (2, -.2)]),
                          ('Extra', [(1, .1)])], 'smoothskin': True}
    matrices = {'OA_L': Matrix.Translation((2, 0, 0)), 'UA_L': Matrix.Translation((10, 0, 0))}
    points, normals = preview._display_geometry(geometry, matrices)
    for point, expected in zip(points, ((7, 3, 2), (9.2, 3, 2), (1, 3, 2), (1, 3, 2))):
        close(point, expected)
    geometry['smoothskin'] = False
    points, normals = preview._display_geometry(geometry, matrices)
    for point, expected in zip(points, ((3, 3, 2), (11, 3, 2), (1, 3, 2), (1, 3, 2))):
        close(point, expected)
    assert all(tuple(normal) == (0, 0, 1) for normal in normals)


def assert_arm_preview_geometry(addon):
    # Rest is checked against real disk output; runtime against decoded weights
    # and final symmetric HUM pivots, including explicit coordinate overrides.
    preview, human, _ = modules(addon)
    with preserve_context():
        for form, custom, target in (('active', True, 15), ('parent', False, -15), ('disabled', True, 0)):
            with bundle_fixture(addon, extra=True, custom=custom, binding_form=form) as (rig, meshes, points, _, _):
                meshes[1].hide_set(True)
                meshes[0].data.materials.append(None)
                for index, polygon in enumerate(meshes[0].data.polygons):
                    polygon.material_index = index % 2
                select_only(rig)
                if form == 'active':
                    # A small admitted asymmetry must still use HUM's symmetric
                    # runtime pivots, rather than the two raw side bone heads.
                    bpy.ops.object.mode_set(mode='EDIT')
                    for stem in ('OA', 'UA', 'Hand'):
                        bone = rig.data.edit_bones[stem + '_R']
                        bone.head.y += .004
                        bone.tail.y += .004
                    bpy.ops.object.mode_set(mode='OBJECT')
                baseline_ids = ids()
                before = source_state(rig, meshes)
                try:
                    for turn in (False, True):
                        for normalize in (False, True):
                            options = dict(normalize_arms=normalize, arm_rest_angle=target, scale=1.3,
                                           turn_180=turn, export_custom_normals=target != 0, confirm_stale=True)
                            # Overrides deliberately differ from raw transformed heads.
                            overrides = {'elbow': (.59, .04, 1.63), 'hand': (.88, .06, 1.54)}
                            with tempfile.TemporaryDirectory(prefix='arm-preview-geometry-') as root:
                                result = human.export_human(str(Path(root) / 'human.hum'), bpy.context, rig, meshes,
                                                            overrides=overrides, **options)
                                records = read_export(Path(result['mesh_paths'][0]).read_bytes())
                                lines = Path(result['hum_path']).read_text(encoding='cp1252').splitlines()
                                start, end = lines.index('[links]') + 1, lines.index('[walk_param]')
                                links = [float(v) for v in lines[start:end] if v.strip()]
                            shown = preview.refresh_preview(bpy.context, rig, meshes, overrides=overrides, **options)
                            assert len(shown['objects']) == 1, 'only highest detail is displayed'
                            obj = shown['objects'][0]
                            assert_display(obj, records)
                            assert list(obj.data.materials) == list(meshes[0].data.materials), [
                                (m.name, m.as_pointer(), m.original.as_pointer()) for m in obj.data.materials]
                            bpy.context.view_layer.update()
                            evaluated = meshes[0].evaluated_get(bpy.context.evaluated_depsgraph_get())
                            source_max = max((evaluated.matrix_world @ v.co).x for v in evaluated.data.vertices)
                            assert abs(min((obj.matrix_world @ v.co).x for v in obj.data.vertices)
                                       - source_max - .25) < 2e-5
                            assert obj.location.y == obj.location.z == 0
                            offset = obj.location.copy()
                            for state, phase in runtime_cases():
                                shown = preview.refresh_preview(bpy.context, rig, meshes, pose=state.upper(), phase=phase,
                                                                beta=45, overrides=overrides, **options)
                                matrix = runtime_arm_matrices(file_joints(links, points, turn), state, phase, beta=45)
                                assert_display(shown['objects'][0], records, matrix)
                                close(shown['objects'][0].location, offset)
                            assert source_state(rig, meshes) == before
                            assert human.human_meshes(bpy.context, rig, selection_only=False) == meshes
                            # Generic CFG export also obeys the skip_export marker.
                            exporter = importlib.import_module(addon.__name__ + '.o3d_io.io_o3d_export')
                            with tempfile.TemporaryDirectory(prefix='arm-preview-generic-') as root:
                                exporter.do_export(str(Path(root) / 'scene.cfg'), bpy.context, Matrix.Identity(4), False, 7)
                                assert not any('Preview' in p.name for p in Path(root).rglob('*.o3d'))
                            preview.clear_preview()
                            assert ids() == baseline_ids and source_state(rig, meshes) == before
                finally:
                    preview.clear_preview()


def assert_arm_preview_placement(addon):
    # Raw base bounds miss active keys/modifiers; export-rest bounds also miss
    # the restored source pose. Check the actual evaluated world-space REST gap.
    preview, _, _ = modules(addon)
    with preserve_context():
        for kind in ('shape_key', 'screw', 'generated_empty'):
            with bundle_fixture(addon) as (rig, meshes, _, _, _):
                source = meshes[0]
                generated = nodes = None
                try:
                    if kind == 'shape_key':
                        meshes[1]['omsi_lod_level'] = 0  # common offset for two primaries
                        key = source.shape_key_add(name='Active +1 X')
                        for point in key.data:
                            point.co.x += 1
                        key.value = 1
                    elif kind == 'screw':
                        modifier = source.modifiers.new('Extend visible X', 'SCREW')
                        modifier.axis, modifier.angle, modifier.screw_offset = 'X', 0, 1.25
                        modifier.steps = modifier.render_steps = 1
                        source.location.x = .37
                        source.scale = (1.2, 1.2, 1.2)
                        # Ensure restored armature evaluation differs from export rest.
                        rig.pose.bones['OA_R'].rotation_mode = 'XYZ'
                        rig.pose.bones['OA_R'].rotation_euler.z = .6
                    else:
                        data = bpy.data.meshes.new('Empty generated source')
                        generated = bpy.data.objects.new('Generated primary', data)
                        bpy.context.scene.collection.objects.link(generated)
                        generated.parent = rig
                        generated.location.x = 2.5
                        generated['export_path'] = 'generated_primary.o3d'
                        # Make the only primary's base empty: modifiers own all geometry.
                        source['omsi_lod_level'] = 1
                        source = generated
                        nodes = bpy.data.node_groups.new('Generated preview fixture', 'GeometryNodeTree')
                        nodes.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
                        cube = nodes.nodes.new('GeometryNodeMeshCube')
                        output = nodes.nodes.new('NodeGroupOutput')
                        nodes.links.new(cube.outputs['Mesh'], output.inputs['Geometry'])
                        modifier = generated.modifiers.new('Generated cube', 'NODES')
                        modifier.node_group = nodes
                    inputs = [*meshes, generated] if generated else meshes
                    select_only(rig, meshes[1])
                    bpy.context.view_layer.update()
                    before, baseline_ids = source_state(rig, meshes), ids()
                    generated_before = ((tuple(source.matrix_world), source.parent, source.hide_get(),
                                         source.hide_viewport, source.hide_render, source.hide_select,
                                         len(source.data.vertices), modifier.node_group, modifier.show_viewport,
                                         modifier.show_render) if generated else None)
                    for turn, scale in ((False, 1.), (True, 1.3)):
                        for normalize in (False, True):
                            options = dict(turn_180=turn, scale=scale, normalize_arms=normalize, arm_rest_angle=15)
                            shown = preview.refresh_preview(bpy.context, rig, inputs, **options)
                            bpy.context.view_layer.update()
                            depsgraph = bpy.context.evaluated_depsgraph_get()
                            evaluated = source.evaluated_get(depsgraph)
                            source_max = max((evaluated.matrix_world @ v.co).x for v in evaluated.data.vertices)
                            preview_min = min((obj.matrix_world @ v.co).x
                                              for obj in shown['objects'] for v in obj.data.vertices)
                            gap = preview_min - source_max
                            print('ARM_PREVIEW_PLACEMENT', kind, turn, scale, normalize,
                                  {'evaluated_source_max_x': source_max, 'preview_min_x': preview_min, 'gap': gap})
                            assert abs(gap - .25) < 2e-5, (kind, turn, scale, normalize, source_max, preview_min, gap)
                            offset = shown['offset']
                            for obj in shown['objects']:
                                close(obj.location, offset)
                            for pose in ('STANDING', 'WALKING', 'SEATED'):
                                posed = preview.refresh_preview(bpy.context, rig, inputs, pose=pose, phase=.75, **options)
                                close(posed['offset'], offset)
                                for obj in posed['objects']:
                                    close(obj.location, offset)
                                assert source_state(rig, meshes) == before
                            preview.clear_preview()
                            assert ids() == baseline_ids and source_state(rig, meshes) == before
                            if generated:
                                assert not source.data.vertices
                                assert (tuple(source.matrix_world), source.parent, source.hide_get(),
                                        source.hide_viewport, source.hide_render, source.hide_select,
                                        len(source.data.vertices), modifier.node_group, modifier.show_viewport,
                                        modifier.show_render) == generated_before
                finally:
                    preview.clear_preview()
                    if generated:
                        data = generated.data
                        bpy.data.objects.remove(generated, do_unlink=True)
                        bpy.data.meshes.remove(data)
                    if nodes:
                        bpy.data.node_groups.remove(nodes)


def assert_arm_preview_ownership(addon):
    # Staged failure must keep prior session and leak no IDs; external removal,
    # pending Edit Mode and registration cleanup must be safe and idempotent.
    preview, human, _ = modules(addon)
    with preserve_context(), bundle_fixture(addon) as (rig, meshes, _, _, _):
        select_only(rig)
        meshes[1]['omsi_lod_level'] = 0  # two primaries: fail after one copy is built
        before, baseline_ids = source_state(rig, meshes), ids()
        first = preview.refresh_preview(bpy.context, rig, meshes)
        active_ids = ids()
        exporter = importlib.import_module(addon.__name__ + '.o3d_io.io_o3d_export')
        prepare = exporter.prepare_o3d_geometry
        build_count = 0
        def fail(*args, **kwargs):
            nonlocal build_count
            build_count += 1
            if build_count == 2:
                raise RuntimeError('injected preview build failure after one copy')
            return prepare(*args, **kwargs)
        exporter.prepare_o3d_geometry = fail
        try:
            try:
                preview.refresh_preview(bpy.context, rig, meshes)
            except RuntimeError as error:
                assert 'injected' in str(error)
            else:
                raise AssertionError('injected failure was swallowed')
            assert ids() == active_ids and preview.is_preview_active(rig)
            assert first['objects'][0].name in bpy.data.objects
        finally:
            exporter.prepare_o3d_geometry = prepare
        for angle in (False, True, float('nan'), -90, 90):
            try:
                preview.refresh_preview(bpy.context, rig, meshes, normalize_arms=True, arm_rest_angle=angle)
            except ValueError as error:
                assert 'angle' in str(error).lower()
            else:
                raise AssertionError('invalid enabled rest angle accepted: ' + repr(angle))
            assert ids() == active_ids and preview.is_preview_active(rig)
        bpy.ops.object.mode_set(mode='EDIT')
        cancel, edit_ids = rig_state(rig), ids()
        try:
            try:
                preview.refresh_preview(bpy.context, rig, meshes)
            except ValueError as error:
                assert 'Object Mode' in str(error)
            else:
                raise AssertionError('pending edits accepted')
            # IDPropertyGroup wrappers have identity equality, even for the
            # same unchanged nested landmark metadata; compare their contents.
            after = rig_state(rig)
            assert after[:4] == cancel[:4] and after[5:] == cancel[5:]
            assert repr(after[4]) == repr(cancel[4])
            assert ids() == edit_ids, 'refusal leaked IDs'
        finally:
            bpy.ops.object.mode_set(mode='OBJECT')
        import bmesh
        select_only(meshes[0])
        bpy.ops.object.mode_set(mode='EDIT')
        pending = bmesh.from_edit_mesh(meshes[0].data)
        pending.verts.ensure_lookup_table()
        original = pending.verts[0].co.copy()
        pending.verts[0].co.z += .123
        pending_point, edit_ids = pending.verts[0].co.copy(), ids()
        try:
            try:
                preview.refresh_preview(bpy.context, rig, meshes)
            except ValueError as error:
                assert 'Object Mode' in str(error)
            else:
                raise AssertionError('pending mesh edits accepted')
            assert meshes[0].mode == 'EDIT' and pending.verts[0].co == pending_point
            assert ids() == edit_ids
        finally:
            pending.verts[0].co = original
            bpy.ops.object.mode_set(mode='OBJECT')
            select_only(rig)
        bpy.data.objects.remove(first['objects'][0], do_unlink=True)
        preview.clear_preview()
        preview.clear_preview()
        assert ids() == baseline_ids and source_state(rig, meshes) == before
        preview.register()
        preview.register()
        assert bpy.app.handlers.save_pre.count(preview._clear_on_file_change) == 1
        assert bpy.app.handlers.load_pre.count(preview._clear_on_file_change) == 1
        assert not any(getattr(f, '__module__', '') == preview.__name__ for f in bpy.app.handlers.depsgraph_update_post)
        preview.refresh_preview(bpy.context, rig, meshes)
        preview.unregister()
        assert ids() == baseline_ids and source_state(rig, meshes) == before
        assert preview._clear_on_file_change not in bpy.app.handlers.save_pre
        preview.register()


def assert_arm_preview_primary_scope(addon):
    preview, _, _ = modules(addon)
    with preserve_context(), bundle_fixture(addon) as (rig, meshes, _, _, _):
        second = meshes[0].copy()
        second.data = meshes[0].data.copy()
        second['export_path'] = 'second_primary.o3d'
        bpy.context.scene.collection.objects.link(second)
        collections = [bpy.data.collections.new('LOD_' + factor) for factor in ('.2', '.1', '0')]
        try:
            for collection, mesh in zip(collections, meshes):
                bpy.context.scene.collection.children.link(collection)
                del mesh['omsi_lod_level']
                for old in list(mesh.users_collection):
                    old.objects.unlink(mesh)
                collection.objects.link(mesh)
            collections[0].objects.link(second)
            meshes[0].hide_set(True)
            select_only(rig)
            before = source_state(rig, [*meshes, second])
            result = preview.refresh_preview(bpy.context, rig, [*meshes, second])
            assert len(result['objects']) == 2, 'all highest-detail body/material meshes are needed'
            assert source_state(rig, [*meshes, second]) == before
        finally:
            preview.clear_preview()
            data = second.data
            bpy.data.objects.remove(second, do_unlink=True)
            bpy.data.meshes.remove(data)
            for collection in collections:
                bpy.data.collections.remove(collection)


def _persistence(addon):
    # Run only in a disposable child: caller root fixtures must survive.
    preview, _, _ = modules(addon)
    with tempfile.TemporaryDirectory(prefix='arm-preview-persistence-') as root:
        path = str(Path(root) / 'preview.blend')
        with bundle_fixture(addon) as (rig, meshes, _, _, _), arm_fixture(addon) as (other, _):
            first, second = rig.omsi_human_settings, other.omsi_human_settings
            first.normalize_arms, first.arm_rest_angle = True, -15
            first.arm_preview_pose, first.arm_preview_phase = 'WALKING', .75
            select_only(rig)
            names = rig.name, other.name
            before = source_state(rig, meshes)
            preview.refresh_preview(bpy.context, rig, meshes)
            bpy.ops.wm.save_as_mainfile(filepath=path)
            assert not preview.is_preview_active() and source_state(rig, meshes) == before
        bpy.ops.wm.open_mainfile(filepath=path, use_scripts=False)
        first, second = (bpy.data.objects[name].omsi_human_settings for name in names)
        assert first.arm_rest_angle == -15 and second.arm_rest_angle == 0
        assert first.arm_preview_pose == 'WALKING' and first.arm_preview_phase == .75
        assert not preview.is_preview_active() and not any('skip_export' in obj for obj in bpy.data.objects)
        rig = bpy.data.objects[names[0]]
        human = modules(addon)[1]
        preview.refresh_preview(bpy.context, rig, human.human_meshes(bpy.context, rig, selection_only=False))
        bpy.ops.wm.open_mainfile(filepath=path, use_scripts=False)
        assert not preview.is_preview_active()
        rig = bpy.data.objects[names[0]]
        meshes = human.human_meshes(bpy.context, rig, selection_only=False)
        preview.refresh_preview(bpy.context, rig, meshes)
        bpy.data.objects.remove(rig, do_unlink=True)
        assert bpy.ops.omsi.clear_human_arm_preview() == {'FINISHED'}
        assert not preview.is_preview_active()
    print('ARM_PREVIEW_PERSISTENCE_OK', bpy.app.version_string)


def assert_arm_preview_persistence(addon):
    expression = (f'import sys; sys.path.insert(0, {str(HERE)!r}); '
                  'import smoke_arm_preview as t; a=t.load_addon(); a.register(); '
                  't._persistence(a); a.unregister()')
    result = subprocess.run([bpy.app.binary_path, '--background', '--factory-startup', '--disable-autoexec',
                             '--python-exit-code', '1', '--python-expr', expression],
                            capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'ARM_PREVIEW_PERSISTENCE_OK' in result.stdout, result.stdout
    print('ARM_PREVIEW_PERSISTENCE_OK isolated subprocess')


PUBLIC_CHECKS = {'controls': assert_arm_preview_controls, 'matrices': assert_arm_preview_matrices,
                 'skin': assert_arm_preview_skin_modes,
                 'geometry': assert_arm_preview_geometry, 'placement': assert_arm_preview_placement,
                 'ownership': assert_arm_preview_ownership,
                 'scope': assert_arm_preview_primary_scope, 'persistence': assert_arm_preview_persistence}
CHECKS = list(PUBLIC_CHECKS.values())


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', choices=['all', *PUBLIC_CHECKS], default='all')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    addon = load_addon()
    addon.register()
    try:
        for check in CHECKS if args.check == 'all' else [PUBLIC_CHECKS[args.check]]:
            check(addon)
            print('ARM_PREVIEW_CHECK_OK', check.__name__)
    finally:
        addon.unregister()
    print('ARM_PREVIEW_SMOKE_OK', bpy.app.version_string, bpy.app.build_hash)


if __name__ == '__main__':
    run()
