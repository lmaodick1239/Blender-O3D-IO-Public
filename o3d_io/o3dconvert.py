# ==============================================================================
#  Copyright (c) 2022-2023 Thomas Mathieson.
# ==============================================================================

import struct
import math


def log(*args):
    print("[O3DConvert]", *args)


# Try to import o3d cryptography module (not available in public plugin release)
try:
    from .o3d_crypto import init_rand, decrypt_vert, encrypt_vert
    _CRYPTO_AVAILABLE = True
except ImportError:
    _CRYPTO_AVAILABLE = False
    log("[WARNING] o3d_crypto.py could not be loaded! O3D encryption and decryption will not work correctly.")


    def init_rand(encryption_header, alt_encryption_seed, version):
        return 0


    def decrypt_vert(vert, encryption_header, alt_encryption_seed, prev_seed, prev_vpos_seed, n_verts):
        return vert, 0, 0


    def encrypt_vert(vert, encryption_header, alt_encryption_seed, prev_seed, prev_vpos_seed, n_verts):
        return vert, 0, 0


# Takes an o3d vertex and returns (((pos), (nrm), (uv)), bewOffset)
def import_vertex(buff, offset):
    v = struct.unpack_from("<ffffffff", buff, offset=offset)  # xp,yp,zp,xn,yn,zn,u,v
    return [[list(v[0:3]), list(v[3:6]), list(v[6:8])], offset + 8 * 4]


# Takes an o3d triangle struct and returns ((indices, matIndex), newOffset)
def import_triangle(buff, offset, long_triangle_indices, invert_normals=False):
    if long_triangle_indices:
        t = struct.unpack_from("<IIIH", buff, offset=offset)
        offset += 4 * 3 + 2
    else:
        t = struct.unpack_from("<HHHH", buff, offset=offset)
        offset += 2 * 4

    if invert_normals:
        return (t[0:3], t[3]), offset
    else:
        return (t[0:3][::-1], t[3]), offset


# Takes an o3d material struct and returns:
#      ((diffuse_r, diffuse_g, diffuse_b, diffuse_a),
#       (specular_r, specular_g, specular_b),
#       (emission_r, emission_g, emission_b),
#       specular_power, texture_name)
# is set to None if one isn't specified in the file
def import_material(buff, offset):
    m = struct.unpack_from("<fffffffffffB", buff, offset=offset)
    offset += 11 * 4
    # Extract texture path length
    path_len = m[-1] + 1  # Path length
    m_name = None
    if path_len + 1 > 0:
        try:
            m_name = struct.unpack_from("<{0}p".format(str(path_len)), buff, offset=offset)[0].decode("cp1252")
        except:
            m_name = ""
        offset += path_len
    return (m[0:4], m[4:7], m[7:10], m[10], m_name), offset


# Takes an o3d bone struct and returns ((name, weights), newOffset)
def import_bone(buff, offset):
    h = struct.unpack_from("<B", buff, offset=offset)  # Name length
    b_name = struct.unpack_from("<{0}p".format(str(h[0] + 1)), buff, offset=offset)[0].decode("cp1252",
                                                                                              errors="backslashreplace")
    offset += h[0] + 1

    n_weights = struct.unpack_from("<H", buff, offset=offset)
    offset += 2
    weights = []
    for w in range(n_weights[0]):
        # OMSI always stores bone influence indices as u16, regardless of the
        # header options bit that widens triangle indices.
        weights.append(struct.unpack_from("<Hf", buff, offset=offset))
        offset += 6

    return (b_name, weights), offset


# Imports a list of o3d vertices and returns (vertices, newOffset)
def import_vertex_list(buff, offset, l_header, encrypted, alt_encryption_seed, encryption_header, version):
    if l_header:
        header = struct.unpack_from("<I", buff, offset=offset)[0]
        offset += 4
    else:
        header = struct.unpack_from("<H", buff, offset=offset)[0]
        offset += 2

    verts = []
    prev_vpos_seed = 0
    prev_seed = init_rand(encryption_header, alt_encryption_seed, version)
    for v in range(header):
        nv = import_vertex(buff, offset)
        if encrypted:
            nv[0], prev_seed, prev_vpos_seed = decrypt_vert(nv[0], encryption_header, alt_encryption_seed, prev_seed,
                                                            prev_vpos_seed, header)

        verts.append(nv[0])
        offset = nv[1]

    return verts, offset


# Imports a list of o3d triangles and returns (triangles, newOffset)
def import_triangle_list(buff, offset, l_header, long_triangle_indices):
    if l_header:
        header = struct.unpack_from("<I", buff, offset=offset)[0]
        offset += 4
    else:
        header = struct.unpack_from("<H", buff, offset=offset)[0]
        offset += 2

    tris = []
    for t in range(header):
        nt = import_triangle(buff, offset, long_triangle_indices, True)
        tris.append(nt[0])
        offset = nt[1]

    return tris, offset


# Imports a list of o3d materials and returns (materials, newOffset)
def import_material_list(buff, offset, l_header):
    # IDK why but materials don't get the long header...
    header = struct.unpack_from("<H", buff, offset=offset)[0]
    offset += 2

    mats = []
    for m in range(header):
        nm = import_material(buff, offset)
        mats.append(nm[0])
        offset = nm[1]

    return mats, offset


# Imports a list of o3d bones and returns (bones, newOffset)
def import_bone_list(buff, offset):
    # OMSI always writes the bone count as u16, even in long-header files.
    header = struct.unpack_from("<H", buff, offset=offset)[0]
    offset += 2

    bones = []
    for b in range(header):
        nb = import_bone(buff, offset)
        bones.append(nb[0])
        offset = nb[1]

    return bones, offset


# Imports an o3d transform struct and returns (transform, newOffset)
def import_transform(buff, offset):
    m = struct.unpack_from("<ffffffffffffffff", buff, offset=offset)
    offset += 16 * 4
    return (
               (m[0], m[1], m[2], m[3]),
               (m[4], m[5], m[6], m[7]),
               (m[8], m[9], m[10], m[11]),
               (m[12], m[13], m[14], m[15])
           ), offset



_SUPPORTED_VERSIONS = range(1, 8)


def _validate_version(version):
    if type(version) is not int or version not in _SUPPORTED_VERSIONS:
        raise ValueError(f"O3D version must be an integer from 1 through 7, got {version!r}")


def _encode_name(value, field):
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    try:
        encoded = value.encode("cp1252")
    except UnicodeEncodeError as error:
        raise ValueError(f"{field} is not CP1252 encodable") from error
    if len(encoded) > 255:
        raise ValueError(f"{field} exceeds 255 CP1252 bytes")
    return encoded


def _validate_material(material):
    if len(material) != 12:
        raise ValueError("O3D materials must contain 11 floats and a texture name")
    _encode_name(material[-1], "material texture name")
    for value in material[:-1]:
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"invalid O3D material value {value!r}")


def _validate_export_inputs(vertex_list, triangle_list, material_list, bone_list,
                            version, long_triangle_indices, encrypted,
                            encryption_key):
    _validate_version(version)
    if not vertex_list:
        raise ValueError("O3D export requires at least one vertex")
    if not triangle_list:
        raise ValueError("O3D export requires at least one triangle")
    if version < 3:
        long_triangle_indices = False
        if len(vertex_list) > 65535 or len(triangle_list) > 65535:
            raise ValueError(f"O3D version {version} supports at most 65535 vertices and triangles")
    if any(
        not isinstance(index, int) or index < 0 or index >= len(vertex_list)
        for triangle in triangle_list for index in triangle[:3]
    ):
        raise ValueError("triangle index is outside the serialized vertex range")
    if any(
        not isinstance(triangle[3], int) or not 0 <= triangle[3] <= 65535
        for triangle in triangle_list
    ):
        raise ValueError("triangle material index must fit in an unsigned 16-bit value")
    if not long_triangle_indices and any(index > 65535 for triangle in triangle_list for index in triangle[:3]):
        raise ValueError("16-bit triangle indices cannot exceed 65535")
    if len(material_list) > 65535:
        raise ValueError("O3D supports at most 65535 materials")
    for material in material_list:
        _validate_material(material)
    if len(bone_list) > 65535:
        raise ValueError("O3D supports at most 65535 bones")
    for bone_name, influences in bone_list:
        _encode_name(bone_name, f"bone name {bone_name!r}")
        if len(influences) > 65535:
            raise ValueError(f"bone {bone_name!r} has more than 65535 influences")
        for vertex_index, weight in influences:
            if not isinstance(vertex_index, int) or not 0 <= vertex_index <= 65535:
                raise ValueError(f"bone {bone_name!r} has an invalid u16 vertex index {vertex_index!r}")
            if vertex_index >= len(vertex_list):
                raise ValueError(f"bone {bone_name!r} references vertex {vertex_index} outside the serialized mesh")
            if not isinstance(weight, (int, float)) or not math.isfinite(weight) or weight < 0:
                raise ValueError(f"bone {bone_name!r} has invalid weight {weight!r}")
    if encrypted:
        if version < 4:
            raise ValueError("O3D encryption requires version 4 or newer")
        if not isinstance(encryption_key, int) or not 0 <= encryption_key <= 0xffffffff:
            raise ValueError("encryption key must be an unsigned 32-bit integer")
        if encryption_key == 0xffffffff:
            raise ValueError("0xffffffff is the unencrypted sentinel, not an encryption key")
        if not _CRYPTO_AVAILABLE:
            raise RuntimeError("O3D encryption support is unavailable")
    return long_triangle_indices


def import_o3d(packed_bytes, *, strict=False):
    if len(packed_bytes) < 3:
        raise ValueError("O3D header is truncated")
    header = struct.unpack_from("<BBB", packed_bytes, offset=0)
    if header[0:2] != (0x84, 0x19):
        raise ValueError(f"invalid O3D magic {header[0:2]!r}; expected (0x84, 0x19)")
    _validate_version(header[2])

    off = 3
    l_header = header[2] >= 3
    encrypted = False
    bonus_header = [0, 0xffffffff]
    if l_header:
        if len(packed_bytes) < off + 1:
            raise ValueError("O3D options header is truncated")
        bonus_header[0] = struct.unpack_from("<B", packed_bytes, offset=off)[0]
        off += 1
        if header[2] >= 4:
            if len(packed_bytes) < off + 4:
                raise ValueError("O3D encryption header is truncated")
            bonus_header[1] = struct.unpack_from("<I", packed_bytes, offset=off)[0]
            off += 4
            encrypted = bonus_header[1] != 0xffffffff
            if encrypted and not _CRYPTO_AVAILABLE:
                raise RuntimeError("O3D encryption support is unavailable")

    vertex_list = []
    triangle_list = []
    material_list = []
    bone_list = []
    transform = ((1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1))
    while off < len(packed_bytes):
        section_offset = off
        section = packed_bytes[off]
        off += 1
        if section == 0x17:
            vertex_list, off = import_vertex_list(
                packed_bytes, off, l_header, encrypted, bonus_header[0] & 2 == 2,
                bonus_header[1], header[2]
            )
            if not vertex_list:
                raise ValueError("O3D vertex section cannot be empty")
        elif section == 0x49:
            triangle_list, off = import_triangle_list(
                packed_bytes, off, l_header, bonus_header[0] & 1 == 1
            )
            if not triangle_list:
                raise ValueError("O3D triangle section cannot be empty")
        elif section == 0x26:
            material_list, off = import_material_list(packed_bytes, off, l_header)
        elif section == 0x54:
            bone_list, off = import_bone_list(packed_bytes, off)
        elif section == 0x79:
            transform, off = import_transform(packed_bytes, off)
        else:
            message = f"unexpected O3D section {section:#x} at offset {section_offset:#x}"
            if strict:
                raise ValueError(message)
            log(message)

    return header, vertex_list, triangle_list, material_list, bone_list, transform, encrypted


def export_vertex(write, vertex):
    """
    Exports an O3D vertex
    :param write: the file writer function
    :param vertex: the vertex to export as a tuple in the form: xp, yp, zp, xn, yn, zn, u, v
    """
    write("<ffffffff", *vertex)  # xp,yp,zp,xn,yn,zn,u,v


def export_triangle(write, triangle, long_triangle_indices, invert_normals=False):
    """
    Exports an O3D triangle
    :param write: the file writer function
    :param triangle: the triangle to export as a tuple in the form: a, b, c, mat_index
    :param long_triangle_indices: whether long triangle indices (32 bit) are used
    :param invert_normals: whether to invert the triangle winding
    """
    write("<IIIH" if long_triangle_indices else "<HHHH",
          *(triangle[0:3][::-1] if invert_normals else triangle[0:3]), triangle[3])


def export_material(write, material):
    """
    Exports an O3D material
    :param write: the file writer function
    :param material: the material to export as a tuple in the form:
    (diffuse_r, diffuse_g, diffuse_b, diffuse_a, specular_r, specular_g, specular_b, emission_r, emission_g, emission_b,
    specular_power, texture_name)
    """
    encoded_name = _encode_name(material[-1], "material texture name")
    write("<fffffffffff", *material[:-1])
    write("<B", len(encoded_name))
    if encoded_name:
        write(f"<{len(encoded_name)}s", encoded_name)


def export_bone(write, bone):
    bone_name, influences = bone

    encoded_name = _encode_name(bone_name, f"bone name {bone_name!r}")
    write("<B", len(encoded_name))
    if encoded_name:
        write(f"<{len(encoded_name)}s", encoded_name)

    # Validate influence count fits in u16
    if len(influences) > 65535:
        raise ValueError(
            f"Bone '{bone_name}' has {len(influences)} influences, "
            f"but the O3D format supports at most 65535 influences per bone."
        )

    write("<H", len(influences))

    for vertex_index, weight in influences:
        # Validate vertex index is a non-negative integer
        if not isinstance(vertex_index, int) or vertex_index < 0:
            raise ValueError(
                f"Bone '{bone_name}' has invalid vertex index {vertex_index}. "
                f"Index must be a non-negative integer."
            )

        # OMSI addresses bone influences with a 16-bit index, so weighted
        # vertices must fit in a u16 regardless of the triangle index width.
        if vertex_index > 65535:
            raise ValueError(
                f"Bone '{bone_name}' has vertex index {vertex_index} above 65535. "
                f"OMSI stores bone influence indices as 16-bit values, so weighted "
                f"vertices must have an index of at most 65535."
            )

        # Validate weight is finite and non-negative
        if not (isinstance(weight, (int, float)) and math.isfinite(weight) and weight >= 0.0):
            raise ValueError(
                f"Bone '{bone_name}' has invalid weight {weight} for vertex {vertex_index}. "
                f"Weight must be a finite non-negative number."
            )

        write("<Hf", vertex_index, weight)


def export_vertex_list(write, vertex_list, encrypted, encryption_key, long_header, alt_encryption_seed, version):
    """
    Exports a list of vertices to an O3D file
    :param write: the file writer function
    :param vertex_list: the vertex list to export
    :param encrypted: whether the vertex list should be encrypted
    :param encryption_key: the encryption key to encrypt with
    :param long_header: whether the file uses long headers
    :param alt_encryption_seed: whether the alternative encryption seed is used
    :param version: the o3d file version
    """
    write("<B", 0x17)
    if long_header:
        write("<I", len(vertex_list))
    else:
        write("<H", len(vertex_list))

    prev_vpos_seed = 0
    prev_seed = init_rand(encryption_key, alt_encryption_seed, version)
    for v in vertex_list:
        if encrypted:
            v, prev_seed, prev_vpos_seed = encrypt_vert(v, encryption_key, alt_encryption_seed, prev_seed,
                                                        prev_vpos_seed, len(vertex_list))
        export_vertex(write, v)


def export_triangle_list(write, triangle_list, long_triangle_indices, long_header, invert_triangle_winding=False):
    """
    Exports a list of triangles to an O3D file
    :param write: the file writer function
    :param triangle_list: the list of triangles to export
    :param long_triangle_indices: whether the triangle indices are 32 bit
    :param long_header: whether the file uses long headers
    """
    write("<B", 0x49)
    if long_header:
        write("<I", len(triangle_list))
    else:
        write("<H", len(triangle_list))

    for t in triangle_list:
        export_triangle(write, t, long_triangle_indices, invert_triangle_winding)


def export_material_list(write, material_list, long_header):
    if len(material_list) == 0:
        return

    write("<B", 0x26)
    # No long headers for materials
    # if long_header:
    #     write("<I", len(material_list))
    # else:
    write("<H", len(material_list))

    for m in material_list:
        export_material(write, m)


def export_bone_list(write, bone_list):
    if len(bone_list) == 0:
        return

    # Validate bone count fits in u16
    if len(bone_list) > 65535:
        raise ValueError(
            f"O3D bone section supports at most 65535 bones, "
            f"but this mesh has {len(bone_list)} bones."
        )

    write("<B", 0x54)
    # Always write bone count as u16, regardless of long_header
    write("<H", len(bone_list))

    for bone in bone_list:
        export_bone(write, bone)


def export_transform(write, transform):
    # For now this just exports an identity matrix
    # TODO: Export correct transform matrix
    if transform is None:
        transform = (1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)

    write("<B", 0x79)
    m = transform
    write("<ffffffffffffffff", *m)


def export_o3d(file, vertex_list, triangle_list, material_list, bone_list, transform, encrypted=False,
               encryption_key=0xffffffff, version=7, long_triangle_indices=True, alt_encryption_seed=True,
               invert_triangle_winding=False):
    long_triangle_indices = _validate_export_inputs(
        vertex_list, triangle_list, material_list, bone_list, version,
        long_triangle_indices, encrypted, encryption_key,
    )

    # Convenience function to pack and write bytes
    def write(fmt, *args):
        file.write(struct.pack(fmt, *args))

    write("<BBB", 0x84, 0x19, version)
    long_header = version >= 3
    if version >= 3:
        options_byte = (1 if long_triangle_indices else 0) | (2 if alt_encryption_seed else 0)
        if not encrypted:
            encryption_key = 0xffffffff
        if version >= 4:
            write("<BI", options_byte, encryption_key)
        else:
            write("<B", options_byte)

    export_vertex_list(
        write, vertex_list, encrypted, encryption_key, long_header,
        alt_encryption_seed, version,
    )
    export_triangle_list(
        write, triangle_list, long_triangle_indices, long_header,
        invert_triangle_winding,
    )
    export_material_list(write, material_list, long_header)
    export_bone_list(write, bone_list)
    export_transform(write, transform)
