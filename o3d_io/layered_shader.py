# ==============================================================================
#  Copyright (c) 2023 Thomas Mathieson.
# ==============================================================================
import inspect

from . import blender_compat

_shader_utils = blender_compat.shader_utils()
_BASE_TAKES_USE_NODES = "use_nodes" in inspect.signature(
    _shader_utils.PrincipledBSDFWrapper.__init__
).parameters


class LayeredBSDFWrapper(_shader_utils.PrincipledBSDFWrapper):
    """
    Hard coded shader setup, based in Principled BSDF but with automatic layering of diffuse textures.
    Should cover most common cases on import, and gives a basic nodal shaders support for export.
    Supports basic: diffuse/spec/reflect/transparency/normal, with texturing.
    """

    def __init__(self, material, is_readonly=True, use_nodes=True):
        if _BASE_TAKES_USE_NODES:
            super().__init__(material, is_readonly, use_nodes)
        else:
            super().__init__(material, is_readonly)

        self._base_color_textures = []
        material["o3d_layered_material"] = True
        self._mix_node_links = [self.node_principled_bsdf]

    def base_color_texture_get(self):
        return None

    base_color_texture = property(base_color_texture_get)

    def base_color_textures_get(self):
        if not getattr(self, "use_nodes", True) or self.node_principled_bsdf is None:
            return None
        return tuple(self._base_color_textures)

    """Tuple of ShaderImageTextureWrappers"""
    base_color_textures = property(base_color_textures_get)

    def _append_splat_map_to_previous(self):
        if not self._base_color_textures:
            return
        col_image = self._base_color_textures[-1][0]
        node_mix = self._mix_node_links[-1]
        self._base_color_textures[-1] = (
            col_image,
            _shader_utils.ShaderImageTextureWrapper(
                self, node_mix,
                node_mix.inputs["Fac"],
                grid_row_diff=2,
            )
        )

    def _remove_excess_textures(self, tree, n):
        for _ in range(len(self._base_color_textures) - 1, n - 1, -1):
            tree.nodes.remove(self._mix_node_links[-1])
            color_texture, splat_texture = self._base_color_textures[-1]
            tree.nodes.remove(color_texture.node_image)
            # The final layer has no splat map, so it may be missing
            if splat_texture is not None:
                tree.nodes.remove(splat_texture.node_image)
            del self._base_color_textures[-1]
            del self._mix_node_links[-1]

    def _add_texture_layer(self, tree, is_last):
        node_mix = tree.nodes.new(type='ShaderNodeMixRGB')
        self._grid_to_location(-2, 0, dst_node=node_mix, ref_node=self._mix_node_links[-1])

        tree.links.new(node_mix.outputs["Color"],
                       self._mix_node_links[-1].inputs["Color1" if len(self._mix_node_links) > 1 else
                                                       "Base Color"])
        node_mix.inputs["Fac"].default_value = 1

        self._base_color_textures.append((
            _shader_utils.ShaderImageTextureWrapper(
                self, node_mix,
                node_mix.inputs["Color2"],
                grid_row_diff=1,
            ),
            None if is_last else _shader_utils.ShaderImageTextureWrapper(
                self, node_mix,
                node_mix.inputs["Fac"],
                grid_row_diff=2,
            )
        ))

        self._mix_node_links.append(node_mix)

    def base_color_n_textures_set(self, n):
        tree = self.material.node_tree
        if n < len(self._base_color_textures):
            self._remove_excess_textures(tree, n)
            return

        self._append_splat_map_to_previous()
        for x in range(len(self._base_color_textures), n):
            self._add_texture_layer(tree, is_last=x == n - 1)

    base_color_n_textures = property(lambda self: len(self.base_color_textures_get()), base_color_n_textures_set)
