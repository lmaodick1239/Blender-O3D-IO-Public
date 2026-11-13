"""Opt-in CPU comparison renders of the actual human arm preview copies.

Run in background Blender with --disable-autoexec --python-exit-code 1, then
--python tests/render_arm_rest_preview.py -- --private-blend PATH --rig NAME
--meshes LOD0 LOD1 LOD2 --output-dir EMPTY_DIRECTORY. No private fixture is
selected by default. The input blend is opened with scripts disabled and never
saved; only PNG comparisons and a JSON manifest are written to the destination.
"""
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import sys


ANGLES = (-10, 0, 10)
POSES = ('REST', 'STANDING', 'WALKING', 'SEATED')


def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--private-blend', required=True, type=Path)
    parser.add_argument('--rig', required=True, help='Exact converted canonical OMSI armature name')
    parser.add_argument('--meshes', required=True, nargs='+', help='Exact converted mesh/LOD names; no helpers')
    parser.add_argument('--output-dir', required=True, type=Path, help='New or empty private evidence directory')
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    args = parser.parse_args(argv)
    args.private_blend = args.private_blend.expanduser().resolve()
    args.output_dir = args.output_dir.expanduser().resolve()
    if not args.private_blend.is_file() or args.private_blend.suffix.lower() != '.blend':
        parser.error('private blend must be an existing .blend file')
    if args.output_dir.exists() and (not args.output_dir.is_dir() or any(args.output_dir.iterdir())):
        parser.error('output directory must be absent or empty (existing evidence is never overwritten)')
    if len(set(args.meshes)) != len(args.meshes):
        parser.error('mesh/LOD names must be distinct')
    try:
        import bpy
    except ImportError:
        parser.error('Run this utility in background Blender with --disable-autoexec')
    if not bpy.app.background:
        parser.error('Run this utility in background Blender with --disable-autoexec')
    return args


def content_center(frame, panel_width):
    """Center the figure within the bands reserved for captions and caveats."""
    return ((frame['left'] + frame['right']) / 2,
            (frame['top'] + frame['bottom']) / 2 + .095 * panel_width)


def main():
    args = arguments()
    import bpy
    from mathutils import Matrix, Vector

    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / 'tests'))
    from smoke_support import load_addon
    source_paths = [root / '__init__.py', *sorted((root / 'o3d_io').rglob('*.py'))]
    source_hashes = {str(path.relative_to(root)): sha256(path) for path in source_paths}
    blend_hash = sha256(args.private_blend)
    addon = load_addon()
    addon.register()
    preview = importlib.import_module(addon.__name__ + '.o3d_io.human_arm_preview')
    exporter = importlib.import_module(addon.__name__ + '.o3d_io.io_o3d_export')
    original_prepare = exporter.prepare_o3d_geometry
    captured = []

    def capture(*positional, **keywords):
        geometry = original_prepare(*positional, **keywords)
        captured.append((positional[0].original.name, geometry))
        return geometry

    try:
        bpy.context.preferences.filepaths.use_scripts_auto_execute = False
        bpy.ops.wm.open_mainfile(filepath=str(args.private_blend), use_scripts=False)
        assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
        source_scene = bpy.context.scene
        rig = source_scene.objects.get(args.rig)
        meshes = [source_scene.objects.get(name) for name in args.meshes]
        if rig is None or rig.type != 'ARMATURE':
            raise ValueError('Expected explicit converted OMSI armature: ' + args.rig)
        required_bones = set(addon.o3d_io.mmd_rig.CANONICAL_NAMES)
        if not required_bones.issubset(rig.data.bones.keys()):
            raise ValueError('Explicit armature does not contain the canonical OMSI bones')
        if any(obj is None or obj.type != 'MESH' for obj in meshes):
            raise ValueError('Every explicit mesh/LOD must be a mesh in the opened scene')
        # Validate binding/scope before creating any evidence directory or render IDs.
        addon.o3d_io.omsi_human._human_candidates(bpy.context, rig, meshes)
        scene = bpy.data.scenes.new('Disposable arm preview comparison')
        scene.render.engine = 'CYCLES'
        scene.cycles.device = 'CPU'
        scene.cycles.samples = 8
        scene.cycles.seed = 0
        scene.cycles.use_denoising = False
        scene.render.threads_mode, scene.render.threads = 'FIXED', 4
        scene.render.resolution_x = 2400
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = 'PNG'
        scene.render.image_settings.color_mode = 'RGB'
        scene.render.image_settings.color_depth = '8'
        scene.render.film_transparent = False
        scene.view_settings.view_transform = 'Standard'
        scene.view_settings.look = 'None'
        scene.view_settings.exposure, scene.view_settings.gamma = 0, 1
        world = bpy.data.worlds.new('Neutral diagnostic studio')
        world.use_nodes = True
        world.node_tree.nodes['Background'].inputs['Color'].default_value = (.08, .08, .08, 1)
        world.node_tree.nodes['Background'].inputs['Strength'].default_value = .7
        scene.world = world
        camera_data = bpy.data.cameras.new('Comparison camera')
        camera = bpy.data.objects.new('Comparison camera', camera_data)
        scene.collection.objects.link(camera)
        camera_data.type = 'ORTHO'
        scene.camera = camera
        light_data = bpy.data.lights.new('Diagnostic key', 'AREA')
        light_data.energy, light_data.shape, light_data.size = 500, 'DISK', 4
        light = bpy.data.objects.new('Diagnostic key', light_data)
        scene.collection.objects.link(light)
        light.location = (-2, 4, 4)
        light.rotation_euler = (Vector((0, 0, 1.1)) - light.location).to_track_quat('-Z', 'Y').to_euler()
        materials = []
        palette = (('Main', (.35, .37, .40, 1)), ('L', (.22, .48, .85, 1)), ('R', (.85, .31, .18, 1)))
        for name, color in palette:
            material = bpy.data.materials.new('Diagnostic ' + name)
            material.diffuse_color = color
            material.use_nodes = True
            shader = material.node_tree.nodes['Principled BSDF']
            shader.inputs['Base Color'].default_value = color
            shader.inputs['Roughness'].default_value = .75
            materials.append(material)
        ink = bpy.data.materials.new('Unlit readable labels')
        ink.use_nodes = True
        ink.node_tree.nodes.clear()
        emission = ink.node_tree.nodes.new('ShaderNodeEmission')
        emission.inputs['Color'].default_value = (.95, .95, .95, 1)
        output = ink.node_tree.nodes.new('ShaderNodeOutputMaterial')
        ink.node_tree.links.new(emission.outputs[0], output.inputs['Surface'])
        variants = []
        for pose in POSES:
            for angle in ANGLES:
                captured.clear()
                exporter.prepare_o3d_geometry = capture
                try:
                    result = preview.refresh_preview(bpy.context, rig, meshes, normalize_arms=True,
                        arm_rest_angle=angle, scale=1.0, turn_180=True, pose=pose, phase=.25, beta=80)
                finally:
                    exporter.prepare_o3d_geometry = original_prepare
                assert len(result['objects']) == len(captured) > 0
                # Evaluate the new side-by-side location BEFORE copying matrix_world.
                bpy.context.view_layer.update()
                parts = []
                for obj, (source_name, geometry) in zip(result['objects'], captured):
                    data = obj.data.copy()
                    # ID.copy carries preview tags: transfer this independent
                    # mesh to the renderer before Clear releases preview IDs.
                    data.pop(preview._OWNER_KEY, None)
                    data.materials.clear()
                    for material in materials:
                        data.materials.append(material)
                    weights = [{} for _ in geometry['verts']]
                    for name, entries in geometry['bones']:
                        for index, weight in entries:
                            if weight > 0:
                                weights[index][name] = weight
                    for polygon in data.polygons:
                        binding = weights[polygon.vertices[0]]
                        bone = max(binding, key=binding.get) if binding else ''
                        polygon.material_index = 1 if bone.endswith('_L') else 2 if bone.endswith('_R') else 0
                    clone = bpy.data.objects.new(f'Rendered {pose} {angle:+d}', data)
                    scene.collection.objects.link(clone)
                    base = obj.matrix_world.copy()
                    base.translation -= Vector(result['offset'])
                    clone.matrix_world = base
                    points = [base @ vertex.co for vertex in data.vertices]
                    arms = [point for point, binding in zip(points, weights)
                            if any(name.startswith(('OA_', 'UA_', 'Hand_')) for name in binding)]
                    if not arms:
                        raise ValueError('No serialized arm weights in the selected primary mesh')
                    stream = {key: geometry[key] for key in ('verts', 'tris', 'bones', 'smoothskin')}
                    parts.append({'object': clone, 'base': base, 'points': points, 'arms': arms,
                                  'source_mesh': source_name,
                                  'vertices': len(data.vertices), 'triangles': len(data.polygons),
                                  'serialized_geometry_sha256': hashlib.sha256(json.dumps(stream).encode()).hexdigest(),
                                  'preview_points_sha256': hashlib.sha256(json.dumps([list(p) for p in points]).encode()).hexdigest()})
                variants.append({'pose': pose, 'angle': angle, 'parts': parts})
                preview.clear_preview()
                for variant in variants:
                    for part in variant['parts']:
                        assert len(part['object'].data.vertices) == part['vertices'], 'Clear removed renderer-owned geometry'
                        assert preview._OWNER_KEY not in part['object'].data

        views = {'front': Vector((0, 8, 0)), 'front-three-quarter': Vector((3, 8, 0))}
        rotations = {name: (-direction).to_track_quat('-Z', 'Y') for name, direction in views.items()}
        # Fit all columns/states at one scale; crop below the lowest diagnostic arm.
        frames = {}
        for name, rotation in rotations.items():
            inverse = rotation.inverted()
            points = [inverse @ point for variant in variants for part in variant['parts'] for point in part['points']]
            arms = [inverse @ point for variant in variants for part in variant['parts'] for point in part['arms']]
            height = max(p.y for p in points) - min(p.y for p in points)
            frames[name] = {'left': min(p.x for p in points), 'right': max(p.x for p in points),
                            'bottom': min(p.y for p in arms) - .06 * height,
                            'top': max(p.y for p in points) + .03 * height}
        panel_width = max(frame['right'] - frame['left'] for frame in frames.values()) * 1.08
        content_height = max(frame['top'] - frame['bottom'] for frame in frames.values())
        frame_height = content_height + .49 * panel_width
        frame_width = 3 * panel_width
        scene.render.resolution_y = round(2400 * frame_height / frame_width)
        camera_data.ortho_scale = frame_width
        manifest = {
            'actual_new_preview_geometry': True, 'private_blend': str(args.private_blend),
            'source_blend_sha256_before': blend_hash, 'rig': rig.name, 'rig_bones': len(rig.data.bones),
            'explicit_mesh_lods': args.meshes, 'utility_sha256': sha256(__file__), 'source_sha256': source_hashes,
            'blender_version': bpy.app.version_string, 'blender_build_hash': bpy.app.build_hash.decode(),
            'settings': {'normalize_arms': True, 'rest_angles_degrees': list(ANGLES), 'scale': 1.0,
                         'turn_180': True, 'turn_180_basis': 'Prior installed-output inference; not recovered saved UI state',
                         'beta_degrees': 80, 'beta_basis': 'Explicit in-memory diagnostic argument; source walk_params unchanged',
                         'walking_phase': .25, 'walking_amplitude_degrees': 18, 'seated_lowering_degrees': 67,
                         'additional_game_lowering_degrees': {'REST': 0, 'STANDING': 80, 'WALKING': 77, 'SEATED': 67}},
            'render': {'engine': 'CYCLES', 'device': 'CPU', 'samples': 8, 'seed': 0, 'denoising': False,
                       'threads': 4, 'resolution': [scene.render.resolution_x, scene.render.resolution_y],
                       'format': 'PNG RGB 8-bit', 'view_transform': 'Standard', 'look': 'None', 'exposure': 0, 'gamma': 1,
                       'projection': 'ORTHO', 'ortho_scale': frame_width, 'panel_width': panel_width,
                       'frame_height': frame_height, 'view_directions': {k: list(v) for k, v in views.items()},
                       'frames': frames, 'content_centers': {k: list(content_center(v, panel_width)) for k, v in frames.items()},
                       'world_color': [.08, .08, .08], 'world_strength': .7,
                       'area_light': {'location': list(light.location), 'energy': 500, 'size': 4, 'shape': 'DISK'},
                       'material_palette': {name: list(color) for name, color in palette}},
            'limitations': ['Static torso and legs', 'Neutral diagnostic materials, not game shaders',
                            'Not full-body/game animation or a collision guarantee', 'No independent private T-pose reference'],
            'variants': [{'pose': v['pose'], 'rest_angle_degrees': v['angle'],
                          'parts': [{k: p[k] for k in ('source_mesh', 'vertices', 'triangles', 'serialized_geometry_sha256', 'preview_points_sha256')}
                                    for p in v['parts']]} for v in variants], 'images': [],
        }
        labels = []

        def label(text, x, y, size, rotation):
            font = bpy.data.curves.new('Comparison label', 'FONT')
            font.body, font.align_x, font.size = text, 'CENTER', size
            caption = bpy.data.objects.new('Comparison label', font)
            scene.collection.objects.link(caption)
            font.materials.append(ink)
            caption.location = rotation @ Vector((x, y, 2))
            caption.rotation_euler = rotation.to_euler()
            labels.append(caption)

        args.output_dir.mkdir(parents=True, exist_ok=True)
        for pose in POSES:
            for view in ('front', 'front-three-quarter') if pose == 'SEATED' else ('front',):
                for caption in labels:
                    font = caption.data
                    bpy.data.objects.remove(caption, do_unlink=True)
                    bpy.data.curves.remove(font)
                labels.clear()
                rotation, frame = rotations[view], frames[view]
                camera.location = rotation @ Vector((0, 0, 8))
                camera.rotation_euler = rotation.to_euler()
                center_x, center_y = content_center(frame, panel_width)
                for variant in variants:
                    for part in variant['parts']:
                        obj = part['object']
                        obj.hide_render = variant['pose'] != pose
                        column = ANGLES.index(variant['angle']) - 1
                        shift = rotation @ Vector((column * panel_width - center_x, -center_y, 0))
                        obj.matrix_world = Matrix.Translation(shift) @ part['base']
                title = {'REST': 'Exported Rest', 'STANDING': 'Standing', 'WALKING': 'Walking phase 0.25',
                         'SEATED': 'Seated fixed 67°'}[pose] + ' | ' + view
                top, bottom = frame_height / 2, -frame_height / 2
                label(title, 0, top - .065 * panel_width, .045 * panel_width, rotation)
                label('Actual prepared preview copies | same scale across angles and states',
                      0, top - .125 * panel_width, .03 * panel_width, rotation)
                lowering = {'REST': 'none (rest)', 'STANDING': '80° (beta80)',
                            'WALKING': '77° (beta80 - 3°)', 'SEATED': '67° (fixed)'}[pose]
                for column, angle in enumerate(ANGLES):
                    x = (column - 1) * panel_width
                    label(f'Rest {angle:+d}°', x, top - .215 * panel_width, .048 * panel_width, rotation)
                    label('Additional game lowering: ' + lowering, x, top - .275 * panel_width,
                          .028 * panel_width, rotation)
                label('Static torso + legs | neutral diagnostic | L blue / R orange | no game or collision guarantee',
                      0, bottom + .085 * panel_width, .028 * panel_width, rotation)
                label('Turn180: prior inference | beta80: memory only | seated lowering fixed at 67°',
                      0, bottom + .035 * panel_width, .028 * panel_width, rotation)
                filename = pose.lower() + '-' + view + '-comparison.png'
                scene.render.filepath = str(args.output_dir / filename)
                bpy.ops.render.render(write_still=True, scene=scene.name)
                manifest['images'].append({'pose': pose, 'view': view, 'path': filename,
                                           'sha256': sha256(scene.render.filepath)})
        manifest['source_blend_sha256_after'] = sha256(args.private_blend)
        manifest['source_blend_preserved'] = manifest['source_blend_sha256_after'] == blend_hash
        manifest['modules_preserved'] = all(sha256(root / path) == digest for path, digest in source_hashes.items())
        assert manifest['source_blend_preserved'] and manifest['modules_preserved']
        (args.output_dir / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
        print('ARM_REST_PREVIEW_RENDER_OK', str(args.output_dir), '5 labeled comparisons; input preserved')
    finally:
        exporter.prepare_o3d_geometry = original_prepare
        preview.clear_preview()
        addon.unregister()


if __name__ == '__main__':
    main()
