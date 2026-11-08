# ==============================================================================
#  Copyright (c) 2022-2023 Thomas Mathieson.
# ==============================================================================
import os
import ntpath
import re
import unicodedata


def platform_related_path(path):
    """
    Return a string with correct path separators for the current platform
    :param path: the path to convert
    :return: the converted path
    """
    return path.replace("/", os.sep).replace("\\", os.sep)


def join_omsi_path(base, relative):
    """
    Joins a path declared inside an OMSI config file onto the directory it is relative to.

    OMSI writes Windows style paths and frequently prefixes them with a separator even though they are
    relative, which os.path.join would otherwise treat as an absolute path and use on its own.

    :param base: the directory the declared path is relative to
    :param relative: the path as written in the config file
    :return: the joined path using this platform's separators
    """
    return os.path.join(base, platform_related_path(relative).lstrip(os.sep))


def safe_export_path(base, relative):
    """Resolve an OMSI relative output without traversal or Windows drive escapes."""
    relative = str(relative)
    if ntpath.splitdrive(relative)[0] or ".." in relative.replace("\\", "/").split("/"):
        raise ValueError(f"Unsafe OMSI export path: {relative!r}")
    path = join_omsi_path(base, relative)
    resolved_base, resolved_path = os.path.realpath(base), os.path.realpath(path)
    if os.path.commonpath((resolved_base, resolved_path)) != resolved_base:
        raise ValueError(f"Export path escapes selected root: {relative!r}")
    return path


def unique_export_path(source, objects, suffix="converted"):
    """Return a fresh ASCII basename, comparing OMSI paths case-insensitively."""
    original = str(source.get("export_path", source.name + ".o3d"))
    stem = ntpath.splitext(ntpath.basename(original.replace("/", "\\")))[0]
    stem = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode("ascii")
    stem = re.sub(r'[^A-Za-z0-9_-]+', "_", stem).strip("_ .") or "character"
    stem = stem[:100]
    used = {ntpath.normpath(str(obj.get("export_path", obj.name + ".o3d"))).lstrip("\\/").casefold()
            for obj in objects}
    base = f"{stem}_{suffix}"
    candidate, index = base + ".o3d", 1
    while candidate.casefold() in used:
        candidate = f"{base}_{index}.o3d"
        index += 1
    return candidate


# OMSI configs are written in the author's local codepage. A Turkish or Cyrillic filename read as
# cp1252 decodes to a name that does not exist on disk, so retry the other regional codepages.
FALLBACK_ENCODINGS = ("cp1254", "cp1251", "cp1250", "cp1253", "cp1257")


def decode_candidates(text, source_encoding="cp1252"):
    """
    Yields the text as it would read in each regional codepage, starting with the text itself.
    """
    yield text
    if text.isascii():
        return
    try:
        raw = text.encode(source_encoding)
    except UnicodeEncodeError:
        return
    for encoding in FALLBACK_ENCODINGS:
        try:
            decoded = raw.decode(encoding)
        except UnicodeDecodeError:
            continue
        if decoded != text:
            yield decoded


def resolve_case_insensitive_path(path):
    """Return the existing path's casing, or the requested path when no match exists."""
    path = platform_related_path(path)
    if os.path.exists(path):
        return path
    drive, tail = os.path.splitdrive(os.path.abspath(path))
    current = drive + os.sep
    for component in tail.split(os.sep):
        if not component:
            continue
        exact = os.path.join(current, component)
        if os.path.exists(exact):
            current = exact
            continue
        try:
            match = next((name for name in sorted(os.listdir(current))
                          if name.casefold() == component.casefold()), None)
        except OSError:
            return path
        if match is None:
            return path
        current = os.path.join(current, match)
    return current


def resolve_omsi_path(base, relative, source_encoding="cp1252"):
    """
    Resolve a declared OMSI path regardless of filename/directory case or regional codepage.
    Returns the first file that exists, or the plain join when none of them do.
    """
    fallback = None
    for candidate in decode_candidates(relative, source_encoding):
        path = join_omsi_path(base, candidate)
        if fallback is None:
            fallback = path
        path = resolve_case_insensitive_path(path)
        if os.path.isfile(path):
            return path
    return fallback
