"""Independent strict reader; no production or reference codec imports.

Disk widths: retained native func-0056c7b4.c, lines 147-176 (header),
472-609 (counts/triangles), 652-675 (8-float vertex), 789-908 (material),
916-1029 (fixed Hf skin and matrix). CP1252 is the add-on's text policy.
Unknown/duplicate tags are rejected here so leftover bytes cannot mask drift.
"""
import struct


def read_export(data: bytes) -> dict:
    offset = 0

    def take(fmt):
        nonlocal offset
        size = struct.calcsize(fmt)
        if size > len(data) - offset:
            raise ValueError(f'truncated O3D at byte {offset}: need {size}, have {len(data)-offset}')
        result = struct.unpack_from(fmt, data, offset)
        offset += size
        return result

    def text():
        length, = take('<B')
        return take(f'<{length}s')[0].decode('cp1252')

    magic, version = take('<HB')
    if magic != 0x1984:
        raise ValueError('invalid O3D magic')
    if not 1 <= version <= 7:
        raise ValueError(f'unsupported O3D version {version}')
    options = take('<B')[0] if version >= 3 else 0
    if version >= 4 and take('<I')[0] != 0xffffffff:
        raise ValueError('encrypted O3D is not supported by the fidelity decoder')
    records = {'version': version, 'options': options, 'vertices': [], 'triangles': [],
               'materials': [], 'bones': [],
               'matrix': [(1., 0., 0., 0.), (0., 1., 0., 0.),
                          (0., 0., 1., 0.), (0., 0., 0., 1.)]}
    count_fmt = '<I' if version >= 3 else '<H'
    seen = set()
    while offset < len(data):
        section_offset = offset
        tag, = take('<B')
        if tag not in (0x17, 0x49, 0x26, 0x54, 0x79):
            raise ValueError(f'unknown O3D tag 0x{tag:02x} at byte {section_offset}')
        if tag in seen:
            raise ValueError(f'duplicate O3D tag 0x{tag:02x} at byte {section_offset}')
        seen.add(tag)
        if tag == 0x79:
            records['matrix'] = [take('<4f') for _ in range(4)]
            continue
        count, = take(count_fmt if tag in (0x17, 0x49) else '<H')
        if tag == 0x17:
            records['vertices'] = [take('<8f') for _ in range(count)]
        elif tag == 0x49:
            fmt = '<IIIH' if options & 1 else '<4H'
            records['triangles'] = [take(fmt) for _ in range(count)]
        elif tag == 0x26:
            records['materials'] = [(*take('<11f'), text()) for _ in range(count)]
        else:
            for _ in range(count):
                name = text()
                influences, = take('<H')
                records['bones'].append((name, [take('<Hf') for _ in range(influences)]))
    return records


def oriented_surface(records: dict) -> list:
    """Material + exact corners, sorted by face and cyclic rotation only.

    Callers may round a *copy* for a tolerance-based comparison; the decoder
    and this representation never discard raw record precision or winding.
    """
    result = []
    for a, b, c, material in records['triangles']:
        corners = tuple(tuple(records['vertices'][index]) for index in (a, b, c))
        cyclic = min(corners[i:] + corners[:i] for i in range(3))
        result.append((tuple(records['materials'][material]), cyclic))
    return sorted(result)
