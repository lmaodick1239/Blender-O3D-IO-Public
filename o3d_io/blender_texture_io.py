# ==============================================================================
#  Copyright (c) 2022-2023 Thomas Mathieson.
# ==============================================================================

import os
import bpy
import numpy as np
from .dds_loader.dds_loader import DDSTexture, FormatNotValid, FormatNotSupported


def log(*args):
    print("[O3D_Texture_Import]", *args)


class TextureSlotWrapper:
    """
    Wrapper around old texture slot type
    """

    class TextureWrapper:
        """
        Wrapper around old texture type
        """

        def __init__(self, image):
            self.image = image

    def __init__(self, image):
        self.texture = TextureSlotWrapper.TextureWrapper(image)


def find_image_path(base_file_path, texture_path, abs_path=False, find_cfg=False):
    if base_file_path[-3:] == "sco":
        tex_file = os.path.join(os.path.dirname(base_file_path), "texture", texture_path.lower())
    elif base_file_path[-3:] == "map":
        tex_file = os.path.join(os.path.dirname(base_file_path), "..", "..", texture_path.lower())
    else:
        tex_file = os.path.join(os.path.dirname(base_file_path), "..", "texture", texture_path.lower())

    if abs_path:
        tex_file = texture_path.lower()

    pre, ext = os.path.splitext(tex_file)
    if os.path.isfile(pre + ".dds"):
        tex_file = pre + ".dds"

    # Attempt a manual search for the file if we couldn't find it
    if not os.path.isfile(tex_file):
        tex_dir = os.path.dirname(base_file_path)
        while True:
            tex_file = os.path.join(tex_dir, texture_path.lower())
            if os.path.isfile(tex_file):
                break
            tex_file = os.path.join(tex_dir, "texture", texture_path.lower())
            if os.path.isfile(tex_file):
                break

            last_dir = tex_dir
            tex_dir = os.path.dirname(tex_dir)
            # Exit case if no texture was found
            if os.path.ismount(tex_dir) or last_dir == tex_dir:
                break

    if find_cfg:
        tex_file += ".cfg"

    if os.path.isfile(tex_file):
        return tex_file
    else:
        return None


def decode_alpha_8_dds(dds, tex_file):
    """
    Rebuilds an ALPHA_8_UNORM DDS surface as a packed Blender image, since Blender can't load them itself.
    """
    surf = dds.surfaces[0]
    alpha = np.frombuffer(bytes(surf.data), dtype=np.uint8)
    expected = surf.width * surf.height
    if alpha.size < expected:
        raise ValueError("surface holds {0} of {1} expected pixels".format(alpha.size, expected))

    image = bpy.data.images.new(tex_file, surf.width, surf.height, alpha=dds.header.ddspf.dwABitMask != 0)
    # Keep the source path so exporting the material writes the real texture name back out
    image.filepath = tex_file
    image.pixels.foreach_set(np.repeat(alpha[:expected].astype(np.float32) / 255.0, 4))
    # Pack the image into .blend so it gets saved with it
    image.pack()
    return image


def load_image(base_file_path, texture_path, abs_path=False):
    tex_file = find_image_path(base_file_path, texture_path, abs_path, False)

    if tex_file is not None and os.path.isfile(tex_file):
        # TODO: Alpha_8_UNORM DDS files are not supported by Blender
        image = bpy.data.images.load(tex_file,
                                     check_existing=True)

        is_dds = tex_file[-3:].lower() == "dds"

        if not image.has_data and is_dds:
            # image.has_data doesn't necessarily mean Blender can't load it (sometimes it's deferred), but there's a
            # good chance it failed.
            # Try loading the DDS file ourselves
            dds = DDSTexture()
            try:
                dds.load(tex_file)
            except FormatNotValid as e:
                log("DDS format not valid: " + str(e))
                dds = None
            except FormatNotSupported as e:
                log("DDS format not supported: " + str(e))
                dds = None

            if dds and dds.dxgi_format == 65:
                # For now, we only support ALPHA_8_UNORM DDS files as they are uncompressed, and so far have been the
                # only dds format encountered which isn't supported by Blender
                try:
                    image = decode_alpha_8_dds(dds, tex_file)
                except Exception as e:
                    log("WARNING: Couldn't decode DDS file {0}: {1}".format(tex_file, e))

        return image
    else:
        log("WARNING: Couldn't find texture: {0}".format(texture_path))
        return None


def load_texture_into_new_slot(base_file_path, texture_path, mat, abs_path=False):
    image = load_image(base_file_path, texture_path, abs_path)

    if image is not None:
        # Wrapper around old texture type
        return TextureSlotWrapper(image)
    return None
