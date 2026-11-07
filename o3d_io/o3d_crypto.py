# ==============================================================================
#  Copyright (c) 2022-2023 Thomas Mathieson.
# ==============================================================================

import math


# O3D Decryption Code
# LCG (PRNG)
def lcg_rand(prev_val, seed1, seed2):
    prod1 = prev_val * seed1
    prod2 = seed1 * seed2

    return (prod1 + prod2) % 8000


def frac(val):
    return val - math.trunc(val)


def init_rand(encryption_header, alt_encryption_seed, version):
    """
    Initialises the random number generator used by the decrypter

    :param encryption_header: model encryption key
    :param alt_encryption_seed: whether to use the alternative encryption seed
    :param version: the file version
    :return: the initial value of next_rand
    """
    encryption_const1 = 1  # AFAIK, this is always 1
    # encryption_const2b = 55
    encryption_const2 = 0  # TODO: Check if this can ever be anything other than 0
    const = encryption_const1 + encryption_const2 * 2 - 1  # ATM doesn't do much, but this just copying what omsi does
    if alt_encryption_seed:
        return (version - 4 + encryption_header + 0x17d) % 65000
    else:
        return (version - 4 + encryption_header) % 65000


def decrypt_vert(vert, encryption_header, alt_encryption_seed, prev_seed, prev_vpos_seed, n_verts):
    """
    Decrypts an O3D vertex given the current state of the random number generator.

    :param vert: encrypted vertex data
    :param encryption_header: model encryption key
    :param alt_encryption_seed: model extended header options
    :param prev_seed: random number generator previous seed value
    :param prev_vpos_seed: random number generator previous vertex position seed
    :param n_verts: number of vertices in the model
    :return: the decrypted vertex, next_rand, and v_pos_seed
    """
    if encryption_header == 0:
        if alt_encryption_seed:
            prev_seed = 0x130
        else:
            prev_seed = 0

    next_rand = lcg_rand(prev_seed, n_verts % 65000, prev_vpos_seed)

    v_pos_seed = math.trunc(abs(frac(vert[0][0]) * frac(vert[0][1]) * frac(vert[0][2]) * 600.0))
    v_pos_seed = (v_pos_seed + (v_pos_seed >> 0x20)) % 0x100

    if next_rand < 1000:
        # Swap xp with yp
        vert[0][0], vert[0][1] = vert[0][1], vert[0][0]
    elif next_rand < 3000:
        # Swap xp with zp
        vert[0][0], vert[0][2] = vert[0][2], vert[0][0]
    elif next_rand > 7000:
        # Swap yp with zp
        vert[0][1], vert[0][2] = vert[0][2], vert[0][1]

    if next_rand & 3 == 0:
        # Flip xn
        vert[1][0] = -vert[1][0]
    if next_rand % 6 == 0:
        # Flip yn
        vert[1][1] = -vert[1][1]
    if next_rand % 7 == 0:
        # Flip zn
        vert[1][2] = -vert[1][2]

    if next_rand < 600:
        # Swap zn with yn
        vert[1][1], vert[1][2] = vert[1][2], vert[1][1]
    elif next_rand <= 4500:
        pass
    else:
        # Swap xn with zyn
        vert[1][0], vert[1][1] = vert[1][1], vert[1][0]

    if next_rand % 5 == 0:
        # Add random to u
        vert[2][0] -= (next_rand % 100) ** 2 / 10000
    if next_rand % 3 == 0:
        # Add random to v
        vert[2][1] -= (next_rand % 50) ** 2 / 2500

    return vert, next_rand, v_pos_seed


def encrypt_vert(vert, encryption_header, alt_encryption_seed, prev_seed, prev_vpos_seed, n_verts):
    """
    Encrypts an O3D vertex given the current state of the random number generator.

    :param vert: unencrypted vertex data
    :param encryption_header: model encryption key
    :param alt_encryption_seed: model extended header options
    :param prev_seed: random number generator previous seed value
    :param prev_vpos_seed: random number generator previous vertex position seed
    :param n_verts: number of vertices in the model
    :return: the decrypted vertex, next_rand, and v_pos_seed
    """
    if encryption_header == 0:
        if alt_encryption_seed:
            prev_seed = 0x130
        else:
            prev_seed = 0

    vert = [*vert]

    next_rand = lcg_rand(prev_seed, n_verts % 65000, prev_vpos_seed)

    v_pos_seed = math.trunc(abs(frac(vert[0]) * frac(vert[1]) * frac(vert[2]) * 600.0))
    v_pos_seed = (v_pos_seed + (v_pos_seed >> 0x20)) % 0x100

    if next_rand < 1000:
        # Swap xp with yp
        vert[0], vert[1] = vert[1], vert[0]
    elif next_rand < 3000:
        # Swap xp with zp
        vert[0], vert[2] = vert[2], vert[0]
    elif next_rand > 7000:
        # Swap yp with zp
        vert[1], vert[2] = vert[2], vert[1]

    if next_rand < 600:
        # Swap zn with yn
        vert[5], vert[4] = vert[4], vert[5]
    elif next_rand <= 4500:
        pass
    else:
        # Swap xn with zn
        vert[4], vert[3] = vert[3], vert[4]

    if next_rand & 3 == 0:
        # Flip xn
        vert[3] = -vert[3]
    if next_rand % 6 == 0:
        # Flip yn
        vert[4] = -vert[4]
    if next_rand % 7 == 0:
        # Flip zn
        vert[5] = -vert[5]

    if next_rand % 5 == 0:
        # Add random to u
        vert[6] += (next_rand % 100) ** 2 / 10000
    if next_rand % 3 == 0:
        # Add random to v
        vert[7] += (next_rand % 50) ** 2 / 2500

    return vert, next_rand, v_pos_seed
