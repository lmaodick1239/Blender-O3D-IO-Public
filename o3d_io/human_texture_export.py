"""Private texture staging for human bundles; source image data is never edited."""
from contextlib import contextmanager
import ntpath
import os
import re
import shutil
import struct
import subprocess
import tempfile

import bpy
import numpy as np

from . import blender_compat, o3d_cfg_parser
from .omsi_paths import resolve_case_insensitive_path


_TEXTURE_SLOTS = ('base_color_texture', 'alpha_texture', 'specular_texture',
                  'emission_color_texture')
_IMAGE_FORMATS = {'.bmp': 'BMP', '.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG', '.tga': 'TARGA'}


def human_images(meshes):
    """Collect supported shader images once, in stable mesh/material order."""
    images = {}
    for obj in meshes:
        for slot in obj.material_slots:
            material = slot.material
            if material is None or not material.use_nodes:
                continue
            wrapper = o3d_cfg_parser.o3d_node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=True)
            for key in _TEXTURE_SLOTS:
                texture = getattr(wrapper, key, None)
                if texture is not None and texture.image is not None:
                    images[texture.image] = None
            bump = blender_compat.find_bump_map(wrapper)
            if bump is not None:
                images[bump[0]] = None
    return list(images)


def largest_texture_size(meshes):
    """Dimensions of the texture with the largest edge (then largest area)."""
    images = human_images(meshes)
    _envmap_images(meshes, images, [], [], load_missing=False)
    return max((tuple(image.size) for image in images),
               key=lambda size: (max(size), size[0] * size[1]), default=(0, 0))


def find_dds_converter(filepath=''):
    """Use only a known optional encoder; do not install or download programs."""
    if filepath:
        path = bpy.path.abspath(filepath)
        if not os.path.isfile(path):
            return None
        name = os.path.basename(path).lower()
        if name in {'texconv', 'texconv.exe', 'magick', 'magick.exe'}:
            return path
        return None
    return shutil.which('texconv') or shutil.which('magick')


def _source_path(image):
    if not image.filepath:
        return ''
    path = bpy.path.abspath(image.filepath, library=image.library).replace('\\', os.sep)
    return resolve_case_insensitive_path(os.path.abspath(path))


def _save_image(image, path, size, file_format='PNG'):
    """Copy the current buffer explicitly: Image.copy can discard dirty pixels."""
    width, height = image.size
    if width <= 0 or height <= 0:
        raise ValueError(f'{image.name}: texture has no readable pixels')
    pixels = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    private = bpy.data.images.new('__omsi_texture_export__', width=width, height=height,
                                  alpha=True, float_buffer=image.is_float)
    try:
        private.colorspace_settings.name = image.colorspace_settings.name
        private.alpha_mode = image.alpha_mode
        private.pixels.foreach_set(pixels)
        if size != (width, height):
            private.scale(*size)
        private.filepath_raw = path
        private.file_format = file_format
        private.save()
    finally:
        bpy.data.images.remove(private)


def _compress_dds(converter, source, target):
    if os.path.basename(converter).lower().startswith('texconv'):
        command = [converter, '-nologo', '-y', '-f', 'DXT5', '-o', os.path.dirname(target), source]
    else:
        command = [converter, source, '-define', 'dds:compression=dxt5', target]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            timeout=120, check=False)
    if result.returncode:
        raise ValueError(result.stdout.decode('utf8', errors='replace')[-500:].strip())
    # Texconv derives the output stem from its input, with case varying by version.
    actual = resolve_case_insensitive_path(os.path.join(os.path.dirname(target),
        os.path.splitext(os.path.basename(source))[0] + '.dds'))
    if not os.path.isfile(target) and os.path.isfile(actual):
        shutil.copyfile(actual, target)
    with open(target, 'rb') as stream:
        header = stream.read(128)
    if (len(header) != 128 or header[:4] != b'DDS ' or header[84:88] != b'DXT5'
            or not all(struct.unpack_from('<II', header, 12))):
        raise ValueError('encoder did not produce a legacy DXT5 DDS texture')


def _envmap_images(meshes, images, warnings, owned, *, load_missing=True):
    """Resolve explicit environment maps alongside each material's base image."""
    aliases = {}
    materials = dict.fromkeys(slot.material for obj in meshes for slot in obj.material_slots
                              if slot.material is not None and slot.material.use_nodes)
    for material in materials:
        wrapper = o3d_cfg_parser.o3d_node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=True)
        if wrapper.roughness > .1 or wrapper.specular <= .0001:
            continue
        base = wrapper.base_color_texture
        if base is None or base.image is None:
            continue
        name = str(material.get('envmap_tex', 'envmap.bmp'))
        candidates = [bpy.path.abspath(name)]
        base_path = _source_path(base.image)
        if base_path:
            candidates.append(os.path.join(os.path.dirname(base_path), name.replace('\\', os.sep)))
        image = next((image for image in dict.fromkeys([*images, *bpy.data.images])
                      if image.filepath and (image.filepath == name or
                         os.path.normcase(_source_path(image)) in
                         {os.path.normcase(os.path.abspath(path)) for path in candidates})), None)
        if image is not None and image not in images:
            images.append(image)
        if image is None and load_missing:
            path = next((resolve_case_insensitive_path(path) for path in candidates
                         if os.path.isfile(resolve_case_insensitive_path(path))), None)
            if path is not None:
                image = bpy.data.images.load(path, check_existing=False)
                owned.append(image)
                images.append(image)
        if image is None:
            warnings.append(f'{material.name}: environment map {name!r} unavailable; external reference retained')
        else:
            aliases[(material, 'envmap_tex')] = image
    return aliases


@contextmanager
def staged_textures(meshes, *, max_texture_size=0, compress_textures=False, dds_converter='',
                    texture_format=None):
    """Prepare files in temporary storage before destination overwrite validation.

    texture_format overrides the legacy compress_textures switch when supplied.
    """
    if isinstance(max_texture_size, bool) or not isinstance(max_texture_size, int) or max_texture_size < 0:
        raise ValueError('Maximum texture size must be a nonnegative whole pixel count (0 keeps original)')
    if texture_format is None:
        texture_format = 'DDS' if compress_textures else 'SOURCE'
    if texture_format not in {'SOURCE', 'PNG', 'TGA', 'DDS'}:
        raise ValueError(f'Unknown texture export format: {texture_format!r}')
    images = human_images(meshes)
    warnings, owned = [], []
    converter = find_dds_converter(dds_converter) if texture_format in {'SOURCE', 'DDS'} else None
    try:
        aliases = _envmap_images(meshes, images, warnings, owned)
        largest = max((tuple(image.size) for image in images),
                      key=lambda size: (max(size), size[0] * size[1]), default=(0, 0))
        with tempfile.TemporaryDirectory(prefix='omsi-human-textures-') as temporary:
            names, files, sources, used = {}, [], set(), set()
            for index, image in enumerate(images):
                if image.source not in {'FILE', 'GENERATED'}:
                    raise ValueError(f'{image.name}: human export requires a single file, packed or generated texture')
                source = _source_path(image)
                disk_image = source and os.path.isfile(source)
                if disk_image:
                    sources.add(os.path.realpath(source))
                original_size = tuple(image.size)
                if (not disk_image and not image.packed_file and image.source != 'GENERATED'
                        and not (image.has_data and all(original_size))):
                    raise ValueError(f'{image.name}: missing texture source {image.filepath!r}')
                size = original_size
                if max_texture_size and not all(size):
                    raise ValueError(f'{image.name}: cannot apply a texture size limit without readable dimensions')
                if max_texture_size and max(size) > max_texture_size:
                    ratio = max_texture_size / max(size)
                    size = tuple(max(1, round(edge * ratio)) for edge in size)
                extension = ntpath.splitext(source or image.name)[1].lower()
                source_supported = extension == '.dds' or extension in _IMAGE_FORMATS
                copy_encoding = source_supported and (image.source == 'FILE' or image.packed_file is not None)
                if not copy_encoding:
                    # file_format is a mutable save setting, not the encoding of
                    # existing bytes. Use it only when no stored format is known.
                    native_format = image.file_format if extension != '.dds' else ''
                    if native_format == 'TARGA_RAW':
                        native_format = 'TARGA'
                    source_supported = native_format in _IMAGE_FORMATS.values()
                    extension = next((ext for ext, value in _IMAGE_FORMATS.items()
                                      if value == native_format), '.png')
                if not source_supported and texture_format == 'SOURCE':
                    warnings.append(f'{image.name}: source format is not supported by OMSI; using PNG')
                target_extension = {'PNG': '.png', 'TGA': '.tga'}.get(texture_format, extension)
                unchanged = (copy_encoding and not image.is_dirty and size == original_size
                             and target_extension == extension)
                copy_packed = unchanged and image.packed_file is not None
                copy_original = unchanged and disk_image and not copy_packed
                folder = os.path.join(temporary, str(index))
                os.mkdir(folder)
                # DDS needs the optional encoder whenever its pixels have changed.
                save_extension = target_extension if target_extension != '.dds' and texture_format != 'DDS' else '.png'
                staged = os.path.join(folder, 'texture' + (extension if copy_original or copy_packed else save_extension))
                if copy_packed:
                    with open(staged, 'wb') as stream:
                        stream.write(image.packed_file.data)
                elif copy_original:
                    shutil.copyfile(source, staged)
                else:
                    file_format = _IMAGE_FORMATS[save_extension]
                    if texture_format == 'SOURCE' and save_extension == '.tga' and image.file_format == 'TARGA_RAW':
                        file_format = 'TARGA_RAW'
                    _save_image(image, staged, size, file_format)
                needs_dds = texture_format == 'DDS' or (target_extension == '.dds' and not (copy_original or copy_packed))
                legacy_dds = False
                if needs_dds and (copy_original or copy_packed) and extension == '.dds':
                    with open(staged, 'rb') as stream:
                        header = stream.read(128)
                    legacy_dds = len(header) == 128 and header[:4] == b'DDS ' and header[84:88] in {b'DXT1', b'DXT3', b'DXT5'}
                if needs_dds and not legacy_dds:
                    if converter is None:
                        warnings.append(f'{image.name}: DDS compression unavailable; select texconv or ImageMagick; using original/PNG texture')
                    else:
                        output = os.path.join(folder, 'dds')
                        os.mkdir(output)
                        dds = os.path.join(output, 'texture.dds')
                        try:
                            _compress_dds(converter, staged, dds)
                            staged = dds
                        except (OSError, ValueError, subprocess.SubprocessError) as error:
                            warnings.append(f'{image.name}: DDS compression failed; using original/PNG texture ({error})')
                # ASCII names keep source Unicode/control names out of CP1252 CFG/O3D strings.
                stem = ntpath.splitext(ntpath.basename(image.filepath or image.name))[0]
                stem = re.sub(r'[^A-Za-z0-9._-]+', '_', stem).strip('. ')[:120] or 'texture'
                extension = os.path.splitext(staged)[1]
                name, suffix = stem + extension, 2
                while name.casefold() in used:
                    name = f'{stem}_{suffix}{extension}'
                    suffix += 1
                used.add(name.casefold())
                names[image] = '../textures/' + name
                files.append((staged, 'textures/' + name))
            names.update((key, names[image]) for key, image in aliases.items())
            yield {'names': names, 'files': files, 'sources': sources, 'warnings': warnings,
                   'max_texture_size': largest}
    finally:
        for image in owned:
            bpy.data.images.remove(image)
