"""Public asset bundle checks: blender -b --factory-startup --disable-autoexec
--python-exit-code 1 --python tests/smoke_human_textures.py
"""
import importlib
import os
from pathlib import Path
import shutil
import struct
import sys
import tempfile
from unittest.mock import patch

import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from smoke_support import load_addon
from smoke_human import (REQUIRED_OVERRIDES, disk_snapshot, export_fixture,
                         refuses, source_snapshot)


def material_image(mesh, image):
    material = bpy.data.materials.new('Bundled ' + image.name)
    material.use_nodes = True
    node = material.node_tree.nodes.new('ShaderNodeTexImage')
    node.image = image
    shader = material.node_tree.nodes.get('Principled BSDF')
    material.node_tree.links.new(node.outputs['Color'], shader.inputs['Base Color'])
    material.node_tree.links.new(node.outputs['Alpha'], shader.inputs['Alpha'])
    mesh.data.materials.append(material)
    return material, shader


def file_image(path, color=(.2, .4, .8, .5), size=(8, 4), file_format='PNG'):
    path.parent.mkdir(parents=True, exist_ok=True)
    image = bpy.data.images.new(path.stem, width=size[0], height=size[1], alpha=True)
    image.pixels[:] = list(color) * (size[0] * size[1])
    image.filepath_raw = str(path)
    image.file_format = file_format
    image.save()
    return image


def export(human, root, rig, mesh, **kwargs):
    return human.export_human(str(root / 'person.hum'), bpy.context, rig, [mesh],
                              overrides=REQUIRED_OVERRIDES, **kwargs)


def assert_asset_layout(addon, human):
    # Catches missing copies, same-basename overwrites, stale binary/CFG paths,
    # and duplicate copies when materials share an image.
    with export_fixture(addon) as (rig, mesh, _), tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        first = file_image(root / 'source1' / 'body.png')
        second = file_image(root / 'source2' / 'BODY.png', color=(.8, .1, .2, .25))
        material_image(mesh, first)
        material, shader = material_image(mesh, second)
        node = material.node_tree.nodes.new('ShaderNodeTexImage')
        node.image = first
        material.node_tree.links.new(node.outputs['Color'], shader.inputs['Emission Color'])
        mesh.data.polygons[1].material_index = 1
        mesh['export_path'] = 'model\\body.o3d'
        bpy.context.view_layer.update()
        before = source_snapshot()
        result = export(human, root / 'out', rig, mesh)
        assert source_snapshot() == before
        output = root / 'out'
        assert Path(result['cfg_path']) == output / 'model' / 'person.cfg', result
        assert result['mesh_paths'] == [str(output / 'model' / 'body.o3d')], result
        assert (output / 'person.hum').read_bytes().startswith(b'[model]\r\nmodel\\person.cfg\r\n')
        copies = list((output / 'textures').iterdir())
        assert len(copies) == 2 and len({p.name.casefold() for p in copies}) == 2, copies
        assert {p.read_bytes() for p in copies} == {Path(first.filepath).read_bytes(), Path(second.filepath).read_bytes()}
        cfg = Path(result['cfg_path']).read_text(encoding='cp1252')
        parsed = addon.o3d_io.o3dconvert.import_o3d(Path(result['mesh_paths'][0]).read_bytes())
        for material in parsed[3]:
            name = material[-1].replace('\\', '/')
            assert name.startswith('../textures/'), name
            assert (output / 'model' / name).is_file(), name
            assert name in cfg.replace('\\', '/'), cfg
        assert len(result['texture_paths']) == 2
        saved = disk_snapshot(output)
        refuses(lambda: export(human, output, rig, mesh), 'overwrite')
        assert disk_snapshot(output) == saved


def assert_resize_and_generated(addon, human):
    # Catches upscaling, aspect ratio loss, dropped alpha, lost dirty pixels,
    # source mutation, and preflight creating destination files.
    with export_fixture(addon) as (rig, mesh, _), tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        image = file_image(root / 'original.png')
        image.pack()
        image.filepath = '//missing/original.png'
        image.pixels[:] = [.75, .25, .5, .375] * 32
        material_image(mesh, image)
        snapshot = (source_snapshot(), tuple(image.pixels), image.filepath, tuple(image.size))
        output = root / 'out'
        result = export(human, output, rig, mesh, max_texture_size=4, preflight_only=True)
        assert not output.exists(), list(root.iterdir())
        assert snapshot == (source_snapshot(), tuple(image.pixels), image.filepath, tuple(image.size))
        assert result['max_texture_size'] == (8, 4), result
        result = export(human, output, rig, mesh, max_texture_size=4)
        resized = bpy.data.images.load(result['texture_paths'][0], check_existing=False)
        try:
            assert tuple(resized.size) == (4, 2), tuple(resized.size)
            assert abs(resized.pixels[3] - .375) < .01, list(resized.pixels[:4])
            assert abs(resized.pixels[0] - .75) < .02, list(resized.pixels[:4])
        finally:
            bpy.data.images.remove(resized)
        assert snapshot == (source_snapshot(), tuple(image.pixels), image.filepath, tuple(image.size))
        result = export(human, root / 'unchanged', rig, mesh, max_texture_size=64)
        full = bpy.data.images.load(result['texture_paths'][0], check_existing=False)
        try:
            assert tuple(full.size) == (8, 4)
        finally:
            bpy.data.images.remove(full)
        refuses(lambda: export(human, root / 'invalid', rig, mesh, max_texture_size=-1))


def assert_dds_and_fallback(addon, human):
    with export_fixture(addon) as (rig, mesh, _), tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        image = file_image(root / 'body.png')
        material_image(mesh, image)
        textures = importlib.import_module(addon.__name__ + '.o3d_io.human_texture_export')
        with patch.object(textures, 'find_dds_converter', return_value=None):
            result = export(human, root / 'fallback', rig, mesh, compress_textures=True, max_texture_size=4)
        assert any('DDS' in warning for warning in result['warnings']), result
        assert Path(result['texture_paths'][0]).suffix == '.png', result
        parsed = addon.o3d_io.o3dconvert.import_o3d(Path(result['mesh_paths'][0]).read_bytes())
        assert parsed[3][0][-1].endswith('.png'), parsed[3]
        if shutil.which('magick') or shutil.which('texconv'):
            before = source_snapshot()
            result = export(human, root / 'dds', rig, mesh, compress_textures=True, max_texture_size=4)
            assert source_snapshot() == before
            path = Path(result['texture_paths'][0])
            assert path.suffix == '.dds', result
            header = path.read_bytes()[:128]
            assert header[:4] == b'DDS ' and header[84:88] == b'DXT5', header
            assert struct.unpack_from('<II', header, 12) == (2, 4), header
            loaded = bpy.data.images.load(str(path), check_existing=False)
            try:
                assert tuple(loaded.size) == (4, 2)
                assert abs(loaded.pixels[3] - .5) < .04, list(loaded.pixels[:4])
            finally:
                bpy.data.images.remove(loaded)
            dds_source = bpy.data.images.load(str(path), check_existing=False)
            dds_source.pack()
            mesh.data.materials.clear()
            material_image(mesh, dds_source)
            original_bytes = path.read_bytes()
            result = export(human, root / 'source_dds', rig, mesh, texture_format='SOURCE', max_texture_size=2)
            preserved = Path(result['texture_paths'][0])
            assert preserved.suffix == '.dds', result
            assert preserved.read_bytes()[84:88] == b'DXT5'
            assert struct.unpack_from('<II', preserved.read_bytes(), 12) == (1, 2)
            assert path.read_bytes() == original_bytes and tuple(dds_source.size) == (4, 2)
            with patch.object(textures, 'find_dds_converter', return_value=None):
                result = export(human, root / 'source_dds_fallback', rig, mesh,
                                texture_format='SOURCE', max_texture_size=2)
            assert Path(result['texture_paths'][0]).suffix == '.png' and result['warnings'], result
        else:
            print('HUMAN_DDS_ENCODER_NOT_INSTALLED: fallback verified')


def assert_texture_destination_safety(addon, human):
    with export_fixture(addon) as (rig, mesh, _), tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        image = file_image(root / 'source' / 'body.png')
        material_image(mesh, image)
        output = root / 'out'
        (output / 'textures').mkdir(parents=True)
        (output / 'textures' / 'BODY.PNG').write_bytes(b'keep existing')
        before = disk_snapshot(root)
        refuses(lambda: export(human, output, rig, mesh), 'overwrite')
        assert disk_snapshot(root) == before
        # Consent must not clobber case variants or the source image itself.
        result = export(human, output, rig, mesh, overwrite=True)
        assert len(list((output / 'textures').iterdir())) == 1, result
        source_root = root / 'source_bundle'
        image.filepath = str(source_root / 'textures' / 'body.png')
        Path(image.filepath).parent.mkdir(parents=True)
        shutil.copyfile(root / 'source' / 'body.png', image.filepath)
        before = disk_snapshot(source_root)
        refuses(lambda: export(human, source_root, rig, mesh, overwrite=True), 'source')
        assert disk_snapshot(source_root) == before
        if os.name != 'nt':
            hardlinked = root / 'hardlinked'
            (hardlinked / 'textures').mkdir(parents=True)
            os.link(image.filepath, hardlinked / 'textures' / 'body.png')
            before = disk_snapshot(root)
            refuses(lambda: export(human, hardlinked, rig, mesh, overwrite=True, max_texture_size=4), 'source')
            assert disk_snapshot(root) == before
            escape = root / 'outside'
            escape.mkdir()
            linked = root / 'linked'
            linked.mkdir()
            (linked / 'textures').symlink_to(escape, target_is_directory=True)
            refuses(lambda: export(human, linked, rig, mesh), 'escapes')
            assert not list(escape.iterdir())


def assert_generated_alpha_map(addon, human):
    # Distinct generated images commonly both have empty filepath values.
    with export_fixture(addon) as (rig, mesh, _), tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        base = bpy.data.images.new('base', width=8, height=4, alpha=True)
        mask = bpy.data.images.new('mask', width=8, height=4, alpha=True)
        base.pixels[:] = [.25, .5, .75, 1] * 32
        mask.pixels[:] = [.5, .5, .5, 1] * 32
        material, shader = material_image(mesh, base)
        node = material.node_tree.nodes.new('ShaderNodeTexImage')
        node.image = mask
        material.node_tree.links.new(node.outputs['Color'], shader.inputs['Alpha'])
        bpy.context.view_layer.update()
        result = export(human, root, rig, mesh)
        cfg = Path(result['cfg_path']).read_text(encoding='cp1252').replace('\\', '/')
        assert '[matl_transmap]\n../textures/mask.png\n' in cfg, cfg
        assert len(result['texture_paths']) == 2
        assert not base.filepath and not mask.filepath


def assert_texture_alias_collisions(addon, human):
    if os.name == 'nt':
        return  # Case-distinct source files require a case-sensitive filesystem.
    with export_fixture(addon) as (rig, mesh, _), tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        first = file_image(root / 'sources' / 'A.png')
        second = file_image(root / 'sources' / 'a.png', color=(.8, .2, .1, .5))
        material_image(mesh, first)
        material_image(mesh, second)
        output = root / 'out'
        (output / 'textures').mkdir(parents=True)
        os.link(first.filepath, output / 'textures' / 'A.png')
        before = disk_snapshot(root)
        refuses(lambda: export(human, output, rig, mesh, overwrite=True, max_texture_size=4), 'source')
        assert disk_snapshot(root) == before
    with export_fixture(addon) as (rig, mesh, _), tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        first = file_image(root / 'sources' / 'one.png')
        second = file_image(root / 'sources' / 'two.png', color=(.8, .2, .1, .5))
        material_image(mesh, first)
        material_image(mesh, second)
        output = root / 'out'
        (output / 'textures').mkdir(parents=True)
        (output / 'textures' / 'one.png').write_bytes(b'preserve linked outputs')
        os.link(output / 'textures' / 'one.png', output / 'textures' / 'two.png')
        before = disk_snapshot(root)
        refuses(lambda: export(human, output, rig, mesh, overwrite=True), 'collid')
        assert disk_snapshot(root) == before


def assert_dirty_missing_source(addon, human):
    with export_fixture(addon) as (rig, mesh, _), tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        image = file_image(root / 'source.png')
        image.pixels[:] = [.75, .25, .5, .375] * 32
        Path(image.filepath).unlink()
        material_image(mesh, image)
        before = (source_snapshot(), tuple(image.pixels))
        result = export(human, root / 'out', rig, mesh, max_texture_size=4)
        loaded = bpy.data.images.load(result['texture_paths'][0], check_existing=False)
        try:
            assert tuple(loaded.size) == (4, 2)
            assert abs(loaded.pixels[0] - .75) < .02
            assert abs(loaded.pixels[3] - .375) < .01
        finally:
            bpy.data.images.remove(loaded)
        assert (source_snapshot(), tuple(image.pixels)) == before


def assert_environment_map_buffer(addon, human):
    with export_fixture(addon) as (rig, mesh, _), tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        base = file_image(root / 'source' / 'body.png')
        environment = file_image(root / 'source' / 'env.png')
        environment.pack()
        environment.pixels[:] = [.9, .1, .1, .5] * 32
        material, shader = material_image(mesh, base)
        material['envmap_tex'] = environment.filepath
        shader.inputs['Roughness'].default_value = .05
        bpy.context.view_layer.update()
        before = (source_snapshot(), tuple(environment.pixels))
        result = export(human, root / 'out', rig, mesh)
        cfg = Path(result['cfg_path']).read_text(encoding='cp1252')
        assert '[matl_envmap]\n../textures/env.png\n' in cfg, cfg
        environment_path = next(path for path in result['texture_paths'] if Path(path).name == 'env.png')
        loaded = bpy.data.images.load(environment_path, check_existing=False)
        try:
            assert abs(loaded.pixels[0] - .9) < .02, list(loaded.pixels[:4])
        finally:
            bpy.data.images.remove(loaded)
        assert (source_snapshot(), tuple(environment.pixels)) == before


def assert_unreadable_dds_limit(addon, human):
    with export_fixture(addon) as (rig, mesh, _), tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        # Valid DX10 A8_UNORM; this is unsupported by Blender's native DDS loader.
        header = bytearray(128)
        header[:4] = b'DDS '
        struct.pack_into('<7I', header, 4, 124, 0x100F, 4, 8, 8, 0, 1)
        struct.pack_into('<II4s', header, 76, 32, 4, b'DX10')
        struct.pack_into('<I', header, 108, 0x1000)
        path = root / 'alpha.dds'
        path.write_bytes(header + struct.pack('<5I', 65, 3, 0, 1, 0) + b'\x80' * 32)
        image = bpy.data.images.load(str(path), check_existing=False)
        if tuple(image.size) != (0, 0):
            return  # A Blender version with a decoder can resize this normally.
        material_image(mesh, image)
        refuses(lambda: export(human, root / 'out', rig, mesh, max_texture_size=4), 'readable')
        assert not (root / 'out').exists()
        result = export(human, root / 'compressed', rig, mesh, compress_textures=True)
        header = Path(result['texture_paths'][0]).read_bytes()[:128]
        assert header[84:88] in (b'DXT1', b'DXT3', b'DXT5') or any('DDS' in warning for warning in result['warnings']), result


def assert_texture_format_selection(addon, human):
    # Selected format must control actual encoding and both binary/CFG references.
    with export_fixture(addon) as (rig, mesh, _), tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        image = file_image(root / 'body.png')
        image.file_format = 'TARGA'  # Changing the save setting does not change source PNG bytes.
        material_image(mesh, image)
        before = (source_snapshot(), image.file_format, tuple(image.pixels), Path(image.filepath).read_bytes())
        same_size = export(human, root / 'unscaled_targa', rig, mesh, texture_format='TGA')
        header = Path(same_size['texture_paths'][0]).read_bytes()[:18]
        assert header[2] in (2, 10) and struct.unpack_from('<HH', header, 12) == (8, 4), header
        for texture_format, extension in (('TGA', '.tga'), ('PNG', '.png'), ('SOURCE', '.png')):
            result = export(human, root / texture_format, rig, mesh,
                            texture_format=texture_format, max_texture_size=4)
            path = Path(result['texture_paths'][0])
            assert path.suffix == extension, result
            if extension == '.tga':
                header = path.read_bytes()[:18]
                assert header[2] in (2, 10) and header[16] == 32, header
                assert struct.unpack_from('<HH', header, 12) == (4, 2), header
            else:
                assert path.read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
            loaded = bpy.data.images.load(str(path), check_existing=False)
            try:
                assert tuple(loaded.size) == (4, 2)
                assert abs(loaded.pixels[3] - .5) < .01, list(loaded.pixels[:4])
            finally:
                bpy.data.images.remove(loaded)
            expected = '../textures/body' + extension
            parsed = addon.o3d_io.o3dconvert.import_o3d(Path(result['mesh_paths'][0]).read_bytes())
            assert parsed[3][0][-1] == expected, parsed[3]
            assert expected in Path(result['cfg_path']).read_text(encoding='cp1252')
        assert before == (source_snapshot(), image.file_format, tuple(image.pixels), Path(image.filepath).read_bytes())
        refuses(lambda: export(human, root / 'invalid', rig, mesh, texture_format='INVALID'), 'format')
        assert not (root / 'invalid').exists()


def assert_keep_source_formats(addon, human):
    # Source format must survive resizing, including packed source-only images.
    for extension, file_format in (('.tga', 'TARGA'), ('.bmp', 'BMP'), ('.jpg', 'JPEG'), ('.png', 'PNG')):
        with export_fixture(addon) as (rig, mesh, _), tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            image = file_image(root / ('source' + extension), file_format=file_format)
            original = Path(image.filepath).read_bytes()
            material_image(mesh, image)
            result = export(human, root / 'copy', rig, mesh, texture_format='SOURCE')
            assert Path(result['texture_paths'][0]).suffix == extension, result
            assert Path(result['texture_paths'][0]).read_bytes() == original
            image.pack()
            Path(image.filepath).unlink()
            image.file_format = 'PNG' if file_format == 'TARGA' else 'TARGA'
            before = (source_snapshot(), image.filepath, image.file_format, tuple(image.pixels))
            result = export(human, root / 'packed', rig, mesh, texture_format='SOURCE')
            assert Path(result['texture_paths'][0]).suffix == extension, result
            assert Path(result['texture_paths'][0]).read_bytes() == original
            result = export(human, root / 'resized', rig, mesh, texture_format='SOURCE', max_texture_size=4)
            assert Path(result['texture_paths'][0]).suffix == extension, result
            loaded = bpy.data.images.load(result['texture_paths'][0], check_existing=False)
            try:
                assert tuple(loaded.size) == (4, 2)
                if extension in ('.tga', '.png'):
                    assert abs(loaded.pixels[3] - .5) < .01, list(loaded.pixels[:4])
            finally:
                bpy.data.images.remove(loaded)
            assert before == (source_snapshot(), image.filepath, image.file_format, tuple(image.pixels))


def assert_native_texture_options(addon, human):
    # Catches export ignoring rig-owned resolution/compression controls, and
    # panel drawing that loses the largest texture dimensions or edits sources.
    from smoke_human import select_only
    with export_fixture(addon) as (rig, mesh, source), tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        human.capture_landmarks(source, rig)
        image = file_image(root / 'source.png', size=(128, 64))
        material_image(mesh, image)
        character = bpy.context.scene.omsi_character_data
        character.source_mesh, character.source_armature = mesh, rig
        select_only(rig)
        settings = rig.omsi_human_settings
        settings.max_texture_size = '64'
        settings.texture_format = 'DDS'
        panel = importlib.import_module(addon.__name__ + '.o3d_io.omsi_character_panel')
        textures = importlib.import_module(addon.__name__ + '.o3d_io.human_texture_export')

        class Layout:
            def __init__(self):
                self.labels, self.properties = [], []
            def label(self, *, text, **kwargs):
                self.labels.append(text)
            def prop(self, owner, name):
                self.properties.append(name)

        layout = Layout()
        before = source_snapshot()
        with patch.object(textures, 'find_dds_converter', return_value=None):
            panel._draw_human_textures(layout, settings, [mesh])
            assert any('128 × 64' in label for label in layout.labels), layout.labels
            assert any('Max source edge: 128 px' == label for label in layout.labels), layout.labels
            assert {'max_texture_size', 'texture_format', 'dds_converter'} <= set(layout.properties)
            assert source_snapshot() == before
            assert bpy.ops.omsi.human_preflight() == {'FINISHED'}, settings.errors
            assert 'DDS' in settings.warnings, settings.warnings
            assert bpy.ops.omsi.export_human(filepath=str(root / 'out' / 'person.hum')) == {'FINISHED'}, settings.errors
        paths = list((root / 'out' / 'textures').iterdir())
        assert len(paths) == 1 and paths[0].suffix == '.png'
        resized = bpy.data.images.load(str(paths[0]), check_existing=False)
        try:
            assert tuple(resized.size) == (64, 32), tuple(resized.size)
        finally:
            bpy.data.images.remove(resized)
        settings.texture_format = 'TGA'
        with patch.object(textures, 'find_dds_converter', side_effect=AssertionError('Targa needs no DDS encoder')):
            assert bpy.ops.omsi.human_preflight() == {'FINISHED'}, settings.errors
            assert bpy.ops.omsi.export_human(filepath=str(root / 'targa' / 'person.hum')) == {'FINISHED'}, settings.errors
        paths = list((root / 'targa' / 'textures').iterdir())
        assert len(paths) == 1 and paths[0].suffix == '.tga'
        assert struct.unpack_from('<HH', paths[0].read_bytes(), 12) == (64, 32)


def run():
    addon = load_addon()
    human = importlib.import_module(addon.__name__ + '.o3d_io.omsi_human')
    addon.register()
    try:
        for check in (assert_asset_layout, assert_resize_and_generated, assert_dds_and_fallback,
                      assert_texture_destination_safety, assert_generated_alpha_map,
                      assert_texture_alias_collisions, assert_dirty_missing_source,
                      assert_environment_map_buffer, assert_unreadable_dds_limit,
                      assert_texture_format_selection, assert_keep_source_formats, assert_native_texture_options):
            check(addon, human)
            print('HUMAN_TEXTURE_CHECK_OK', check.__name__)
    finally:
        addon.unregister()
    print('BLENDER_HUMAN_TEXTURE_SMOKE_OK', bpy.app.version_string)


if __name__ == '__main__':
    run()
