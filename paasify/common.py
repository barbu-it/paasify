# -*- coding: utf-8 -*-
"""Paasify common library

Holds common pieces of code

"""

import os
import logging
from enum import Enum
from string import Template

# from pprint import pprint

# =====================================================================
# Init
# =====================================================================
log = logging.getLogger()


class OutputFormat(str, Enum):
    "Available paasify format outputs"

    # pylint: disable=invalid-name

    yaml = "yaml"
    json = "json"
    # toml = "toml"


class SchemaTarget(str, Enum):
    "Available schema items"

    app = "app"
    prj = "prj"
    prj_config = "prj_config"
    prj_stacks = "prj_stacks"
    prj_sources = "prj_sources"


# =====================================================================
# Misc functions
# =====================================================================


def uniq(seq):
    """Remove duplicate duplicates items in a list while preserving order"""
    return list(dict.fromkeys(seq))


def update_dict(dict1, dict2, strict=False):
    """Update dict1 keys with null value from dict2"""
    result = dict1.copy()
    for key, new_value in dict2.items():
        value = result.get(key)
        if not strict and not value:
            result[key] = new_value
        elif strict and value is None:
            result[key] = new_value

    return result


def list_parent_dirs(path):
    """
    Return a list of the parents paths
    path treated as strings, must be absolute path
    """
    result = [path]
    val = path
    while val and val != os.sep:
        val = os.path.split(val)[0]
        result.append(val)
    return result


def find_file_up(names, paths):
    """
    Find every files names in names list in
    every listed paths
    """
    assert isinstance(names, list), f"Names must be array, not: {type(names)}"
    assert isinstance(paths, list), f"Paths must be array, not: {type(names)}"

    result = []
    for path in paths:
        for name in names:
            file_path = os.path.join(path, name)
            if os.access(file_path, os.R_OK):
                result.append(file_path)

    return result


def filter_existing_files(root_path, candidates):
    """Return only existing files"""
    result = [
        os.path.join(root_path, cand)
        for cand in candidates
        if os.path.isfile(os.path.join(root_path, cand))
    ]
    return list(set(result))


def cast_docker_compose(var):
    "Convert any types to strings"

    if var is None:
        result = ""
    elif isinstance(var, (bool)):
        result = "true" if var else "false"
    elif isinstance(var, (str, int)):
        result = str(var)
    elif isinstance(var, list):
        result = ",".join(var)
    elif isinstance(var, dict):
        result = ",".join([f"{key}={str(val)}" for key, val in var.items()])
    else:
        raise Exception(f"Impossible to cast value: {var}")

    return result


def to_bool(string):
    "Return a boolean"
    if isinstance(string, bool):
        return string
    return string.lower() in ["true", "1", "t", "y", "yes"]


def merge_env_vars(obj):
    "Transform all keys of a dict starting by _ to their equivalent wihtout _"

    override_keys = [key.lstrip("_") for key in obj.keys() if key.startswith("_")]
    for key in override_keys:
        old_key = "_" + key
        obj[key] = obj[old_key]
        obj.pop(old_key)

    return obj, override_keys


def get_paasify_pkg_dir():
    """Return the dir where the actual paasify source code lives"""

    # pylint: disable=import-outside-toplevel
    import paasify as _

    return os.path.dirname(_.__file__)


def ensure_dir_exists(path):
    """Ensure directories exist for a given path"""
    if not os.path.isdir(path):
        log.info(f"Create directory: {path}")
        os.makedirs(path)
        return True
    return False


def ensure_parent_dir_exists(path):
    """Ensure parent directories exist for a given path"""
    parent = os.path.dirname(os.path.normpath(path))
    return ensure_dir_exists(parent)


# =====================================================================
# Class overrides
# =====================================================================


class StringTemplate(Template):
    """
    String Template class override to support version of python below 3.11

    Source code: Source: https://github.com/python/cpython/commit/dce642f24418c58e67fa31a686575c980c31dd37
    """

    def get_identifiers(self):
        """Returns a list of the valid identifiers in the template, in the order
        they first appear, ignoring any invalid identifiers."""

        ids = []
        for mo in self.pattern.finditer(self.template):
            named = mo.group("named") or mo.group("braced")
            if named is not None and named not in ids:
                # add a named group only the first time it appears
                ids.append(named)
            elif (
                named is None
                and mo.group("invalid") is None
                and mo.group("escaped") is None
            ):
                # If all the groups are None, there must be
                # another group we're not expecting
                raise ValueError("Unrecognized named group in pattern", self.pattern)
        return ids

    def is_valid(self):
        """Returns false if the template has invalid placeholders that will cause
        :meth:`substitute` to raise :exc:`ValueError`.
        """

        for mo in self.pattern.finditer(self.template):
            if mo.group("invalid") is not None:
                return False
            if (
                mo.group("named") is None
                and mo.group("braced") is None
                and mo.group("escaped") is None
            ):
                # If all the groups are None, there must be
                # another group we're not expecting
                raise ValueError("Unrecognized named group in pattern", self.pattern)
        return True


# We override this method only if version of python is below 3.11
if hasattr(Template, "get_identifiers"):
    StringTemplate = Template  # noqa: F811
