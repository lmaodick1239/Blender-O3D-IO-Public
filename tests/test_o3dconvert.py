import io
import struct
import unittest

from o3d_io import o3dconvert


VERTICES = [
    [0.25, 0.5, 0.75, 0.0, 0.0, 1.0, 0.2, 0.3],
    [1.25, 0.5, 0.75, 0.0, 0.0, 1.0, 0.4, 0.5],
    [0.25, 1.5, 0.75, 0.0, 0.0, 1.0, 0.6, 0.7],
]
TRIANGLES = [(0, 1, 2, 0)]
MATERIALS = [(1.0, 1.0, 1.0, 1.0, 0.1, 0.2, 0.3,
              0.0, 0.0, 0.0, 4.0, "")]


def encode(*, version=7, vertices=None, triangles=None, materials=None, **kwargs):
    target = io.BytesIO()
    o3dconvert.export_o3d(
        target,
        VERTICES if vertices is None else vertices,
        TRIANGLES if triangles is None else triangles,
        MATERIALS if materials is None else materials,
        [],
        None,
        version=version,
        **kwargs,
    )
    return target.getvalue()


def find_section(data, tag):
    offset = 3
    version = data[2]
    if version >= 3:
        offset += 1
    if version >= 4:
        offset += 4
    while offset < len(data):
        section_offset = offset
        section = data[offset]
        offset += 1
        if section == tag:
            return section_offset, offset
        if section == 0x17:
            count_size = 4 if version >= 3 else 2
            count = struct.unpack_from("<I" if count_size == 4 else "<H", data, offset)[0]
            offset += count_size + count * 32
        elif section == 0x49:
            count_size = 4 if version >= 3 else 2
            count = struct.unpack_from("<I" if count_size == 4 else "<H", data, offset)[0]
            offset += count_size
            stride = 14 if version >= 3 and data[3] & 1 else 8
            offset += count * stride
        elif section == 0x26:
            count = struct.unpack_from("<H", data, offset)[0]
            offset += 2
            for _ in range(count):
                offset += 44
                offset += data[offset] + 1
        elif section == 0x54:
            count = struct.unpack_from("<H", data, offset)[0]
            offset += 2
            for _ in range(count):
                name_len = data[offset]
                offset += name_len + 1
                influences = struct.unpack_from("<H", data, offset)[0]
                offset += 2 + influences * 6
        elif section == 0x79:
            offset += 64
        else:
            offset += 1
    raise AssertionError(f"section {tag:#x} not found")


def material_power(data):
    _, offset = find_section(data, 0x26)
    count = struct.unpack_from("<H", data, offset)[0]
    assert count >= 1
    return struct.unpack_from("<f", data, offset + 2 + 10 * 4)[0]


class O3DCodecParityTests(unittest.TestCase):
    def test_import_rejects_bad_or_truncated_headers(self):
        for payload in (b"\x00\x19\x07", b"\x84\x19", b"\x84\x19\x08"):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    o3dconvert.import_o3d(payload)

    def test_export_rejects_unsupported_versions_before_writing(self):
        for version in (0, 8, 255, -1):
            target = io.BytesIO(b"keep")
            with self.subTest(version=version):
                with self.assertRaises(ValueError):
                    o3dconvert.export_o3d(
                        target, VERTICES, TRIANGLES, MATERIALS, [], None,
                        version=version,
                    )
                self.assertEqual(target.getvalue(), b"keep")

    def test_pre_v3_defaults_to_short_triangle_indices(self):
        for version in (1, 2):
            data = encode(version=version)
            section_offset, payload_offset = find_section(data, 0x49)
            count = struct.unpack_from("<H", data, payload_offset)[0]
            self.assertEqual(count, 1)
            triangle = struct.unpack_from("<HHHH", data, payload_offset + 2)
            self.assertEqual(triangle, (0, 1, 2, 0))
            self.assertEqual(data[section_offset], 0x49)

    def test_unknown_section_continues_native_dispatch_by_default(self):
        data = bytearray(encode())
        triangle_section_offset, _ = find_section(data, 0x49)
        data[triangle_section_offset:triangle_section_offset] = b"\x00"
        parsed = o3dconvert.import_o3d(bytes(data))
        self.assertEqual(len(parsed[1]), 3)
        self.assertEqual(len(parsed[2]), 1)
        self.assertEqual(len(parsed[3]), 1)
        self.assertEqual(parsed[5][0][0], 1.0)

        with self.assertRaises(ValueError):
            o3dconvert.import_o3d(bytes(data), strict=True)

    def test_trailing_unknown_section_is_consumed(self):
        parsed = o3dconvert.import_o3d(encode() + b"\x00")
        self.assertEqual(len(parsed[2]), 1)

    def test_export_rejects_empty_geometry_before_writing(self):
        for vertices, triangles in (([], []), (VERTICES, []), ([], TRIANGLES)):
            target = io.BytesIO(b"keep")
            with self.subTest(vertices=len(vertices), triangles=len(triangles)):
                with self.assertRaises(ValueError):
                    o3dconvert.export_o3d(
                        target, vertices, triangles, MATERIALS, [], None,
                    )
                self.assertEqual(target.getvalue(), b"keep")

    def test_export_rejects_overlong_material_names_before_writing(self):
        for name in ("a" * 256, "漢"):
            target = io.BytesIO(b"keep")
            materials = [(*MATERIALS[0][:-1], name)]
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    o3dconvert.export_o3d(
                        target, VERTICES, TRIANGLES, materials, [], None,
                    )
                self.assertEqual(target.getvalue(), b"keep")

    def test_255_byte_material_name_is_exactly_aligned(self):
        name = "a" * 255
        data = encode(materials=[(*MATERIALS[0][:-1], name)])
        _, offset = find_section(data, 0x26)
        self.assertEqual(data[offset + 2 + 44], 255)
        parsed = o3dconvert.import_o3d(data)
        self.assertEqual(parsed[3][0][-1], name)

    def test_encrypted_round_trip_uses_vertex_count_not_version(self):
        for key in (0, 1):
            for alternate in (False, True):
                with self.subTest(key=key, alternate=alternate):
                    data = encode(
                        encrypted=True,
                        encryption_key=key,
                        alt_encryption_seed=alternate,
                    )
                    parsed = o3dconvert.import_o3d(data)
                    self.assertTrue(parsed[-1])
                    for actual, expected in zip(parsed[1], VERTICES):
                        for actual_component, expected_component in zip(
                            (*actual[0], *actual[1], *actual[2]), expected
                        ):
                            self.assertAlmostEqual(
                                actual_component, expected_component, places=5
                            )

    def test_encryption_rejects_unsupported_combinations(self):
        for version, key in ((3, 1), (4, 0xffffffff)):
            target = io.BytesIO(b"keep")
            with self.subTest(version=version, key=key):
                with self.assertRaises(ValueError):
                    o3dconvert.export_o3d(
                        target, VERTICES, TRIANGLES, MATERIALS, [], None,
                        version=version, encrypted=True, encryption_key=key,
                    )
                self.assertEqual(target.getvalue(), b"keep")

    def test_unavailable_crypto_rejects_encrypted_export(self):
        original = o3dconvert._CRYPTO_AVAILABLE
        o3dconvert._CRYPTO_AVAILABLE = False
        try:
            with self.assertRaises(RuntimeError):
                encode(version=4, encrypted=True, encryption_key=1)
        finally:
            o3dconvert._CRYPTO_AVAILABLE = original

    def test_import_preserves_raw_specular_power(self):
        materials = [(*MATERIALS[0][:10], 32.0, "")]
        data = encode(materials=materials)
        self.assertAlmostEqual(material_power(data), 32.0, places=5)
        parsed = o3dconvert.import_o3d(data)
        self.assertAlmostEqual(parsed[3][0][3], 32.0, places=5)


if __name__ == "__main__":
    unittest.main()
