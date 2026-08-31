# ==============================================================================
#  Copyright (c) 2022-2023 Thomas Mathieson.
# ==============================================================================
import os


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
