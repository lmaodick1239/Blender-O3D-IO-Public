"""Hand-packed native grammar checks; never import an add-on/reference codec."""
import copy
import struct
import unittest

from o3d_export_support import oriented_surface, read_export


VERTICES = [(0., 0., 0., .25, -.5, .75, .125, .875),
            (2., 0., 0., .5, .25, -.75, .625, .25),
            (0., 3., 1., -.25, .75, .5, .875, .5)]
MATERIAL = (.25, .5, .75, .5, .125, .25, .5, .625, .875, 1.25, 32., "flèche.png")
MATRIX = [(1., 0., 0., 0.), (0., 1., 0., 0.),
          (0., 0., 1., 0.), (2., -3., 4., 1.)]


def hand_packed(version=7, wide=True, matrix_first=False, matrix=True):
    """Literal widths from retained 0056c7b4; skin stays Hf even with IIIH."""
    header = struct.pack('<HB', 0x1984, version)
    if version >= 3:
        header += struct.pack('<B', int(wide) | 2)
    if version >= 4:
        header += struct.pack('<I', 0xffffffff)
    count = '<I' if version >= 3 else '<H'
    vertices = b'\x17' + struct.pack(count, 3)
    vertices += b''.join(struct.pack('<8f', *v) for v in VERTICES)
    triangles = b'\x49' + struct.pack(count, 1)
    triangles += struct.pack('<IIIH' if wide and version >= 3 else '<4H', 0, 2, 1, 0)
    texture = MATERIAL[-1].encode('cp1252')
    materials = b'\x26\x01\x00' + struct.pack('<11f', *MATERIAL[:11])
    materials += bytes([len(texture)]) + texture
    bones = b'\x54\x01\x00\x04Main\x02\x00'
    bones += struct.pack('<HfHf', 0, .25, 2, .75)
    frame = b'\x79' + struct.pack('<16f', *(v for row in MATRIX for v in row)) if matrix else b''
    return header + vertices + triangles + materials + (frame + bones if matrix_first else bones + frame)


class DecoderTests(unittest.TestCase):
    def test_complete_v7_values_and_both_section_orders(self):
        for matrix_first in (False, True):
            with self.subTest(matrix_first=matrix_first):
                records = read_export(hand_packed(matrix_first=matrix_first))
                self.assertEqual(set(records), {'version', 'options', 'vertices', 'triangles',
                                                'materials', 'bones', 'matrix'})
                self.assertEqual(records['version'], 7)
                self.assertEqual(records['options'], 3)
                self.assertEqual(records['vertices'], VERTICES)
                self.assertEqual(records['triangles'], [(0, 2, 1, 0)])
                self.assertEqual(records['materials'], [MATERIAL])
                self.assertEqual(records['bones'], [('Main', [(0, .25), (2, .75)])])
                self.assertEqual(records['matrix'], MATRIX)

    def test_legacy_v1_counts_short_triangles_and_values(self):
        records = read_export(hand_packed(version=1))
        self.assertEqual(records['version'], 1)
        self.assertEqual(records['options'], 0)
        self.assertEqual(records['vertices'], VERTICES)
        self.assertEqual(records['triangles'], [(0, 2, 1, 0)])
        self.assertEqual(records['materials'], [MATERIAL])
        self.assertEqual(records['bones'], [('Main', [(0, .25), (2, .75)])])
        self.assertEqual(records['matrix'], MATRIX)

    def test_versions_and_triangle_width_do_not_widen_skin(self):
        for version in range(1, 8):
            for wide in (False, True):
                with self.subTest(version=version, wide=wide):
                    records = read_export(hand_packed(version=version, wide=wide))
                    self.assertEqual(records['triangles'], [(0, 2, 1, 0)])
                    self.assertEqual(records['bones'], [('Main', [(0, .25), (2, .75)])])

    def test_absent_matrix_defaults_to_identity(self):
        self.assertEqual(read_export(hand_packed(matrix=False))['matrix'],
                         [(1., 0., 0., 0.), (0., 1., 0., 0.),
                          (0., 0., 1., 0.), (0., 0., 0., 1.)])

    def test_truncation_at_each_record_and_string_boundary(self):
        # Every strict prefix except the five valid section boundaries must fail.
        for version, boundaries in ((1, {3, 102, 113, 171, 193}), (7, {8, 109, 128, 186, 208})):
            data = hand_packed(version=version)
            for end in range(len(data)):
                if end in boundaries:
                    continue
                with self.subTest(version=version, end=end), self.assertRaisesRegex(ValueError, 'truncated'):
                    read_export(data[:end])

    def test_exact_eof_unknown_tag_and_duplicate_section(self):
        data = hand_packed()
        for suffix in (b'\x00', b'\xffgarbage', b'\x79' + bytes(64)):
            with self.subTest(suffix=suffix[:1]), self.assertRaises(ValueError):
                read_export(data + suffix)

    def test_rejects_encryption_magic_and_unsupported_version(self):
        data = hand_packed()
        with self.assertRaisesRegex(ValueError, 'encrypt'):
            read_export(data[:4] + struct.pack('<I', 0) + data[8:])
        for header in (b'\x00\x00\x07', b'\x84\x19\x00', b'\x84\x19\x08'):
            with self.subTest(header=header), self.assertRaises(ValueError):
                read_export(header)

    def test_oriented_surface_ignores_numbering_and_cyclic_rotation_not_reversal(self):
        original = {'vertices': VERTICES, 'triangles': [(0, 1, 2, 0)], 'materials': [MATERIAL]}
        renumbered = {'vertices': [VERTICES[2], VERTICES[0], VERTICES[1]],
                      'triangles': [(2, 0, 1, 0)], 'materials': [MATERIAL]}
        self.assertEqual(oriented_surface(original), oriented_surface(renumbered))
        reversed_records = copy.deepcopy(original)
        reversed_records['triangles'] = [(2, 1, 0, 0)]
        self.assertNotEqual(oriented_surface(original), oriented_surface(reversed_records))
        changed_material = copy.deepcopy(original)
        changed_material['materials'] = [(*MATERIAL[:10], 16., MATERIAL[-1])]
        self.assertNotEqual(oriented_surface(original), oriented_surface(changed_material))
        changed_uv = copy.deepcopy(original)
        changed_uv['vertices'][0] = (*VERTICES[0][:6], .5, .5)
        self.assertNotEqual(oriented_surface(original), oriented_surface(changed_uv))

    def test_polygon_tessellation_deltas_remain_observable(self):
        # Equal source corners do not imply equal oriented triangle surfaces.
        # Polygon fixtures use Blender's tessellation as their invariant; the
        # reference may choose another diagonal, which must stay visible as data.
        vertices = [(0., 0., 0., 0., 0., 1., 0., 0.),
                    (2., 0., 0., 0., 0., 1., 1., 0.),
                    (2., 1., .35, 0., 0., 1., 1., 1.),
                    (0., 1., 0., 0., 0., 1., 0., 1.)]
        first = {'vertices': vertices, 'triangles': [(0, 1, 2, 0), (0, 2, 3, 0)],
                 'materials': [MATERIAL]}
        other_diagonal = {'vertices': vertices, 'triangles': [(0, 1, 3, 0), (1, 2, 3, 0)],
                          'materials': [MATERIAL]}
        self.assertNotEqual(oriented_surface(first), oriented_surface(other_diagonal))
        reversed_face = copy.deepcopy(first)
        reversed_face['triangles'][0] = (2, 1, 0, 0)
        self.assertNotEqual(oriented_surface(first), oriented_surface(reversed_face))

    def test_oriented_surface_uses_material_identity_not_slot_index(self):
        records = {'vertices': VERTICES, 'triangles': [(0, 1, 2, 0)], 'materials': [MATERIAL]}
        swapped = {'vertices': VERTICES, 'triangles': [(1, 2, 0, 1)],
                   'materials': [(*MATERIAL[:11], 'other.png'), MATERIAL]}
        self.assertEqual(oriented_surface(records), oriented_surface(swapped))


if __name__ == '__main__':
    unittest.main()
