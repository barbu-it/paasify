"""Paasify common library

Holds common pieces of code

"""

import os
from enum import Enum
from string import Template

from pprint import pprint

# from pathlib import Path
# from jsonschema import Draft202012Validator, validators
# import paasify.errors as error

import shlex
import re

# =====================================================================
# Init
# =====================================================================


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


def lookup_candidates(lookup_config):
    "List all available candidates of files for given folders"

    result = []
    for lookup in lookup_config:
        path = lookup["path"]
        if path:
            cand = filter_existing_files(path, lookup["pattern"])

            lookup["matches"] = cand
            result.append(lookup)

    return result


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
    StringTemplate = Template


# =====================================================================
# Beta libs (DEPRECATED)
# =====================================================================


def parse_vars(match):
    "Deprecated"

    match = match.groupdict()

    name = match.get("name1", None) or match.get("name2", None)

    # Detect assignment method
    mode = match["mode"]
    if mode == "-":
        mode = "unset_alt"
    elif mode == ":-":
        mode = "empty_alt"
    elif mode == "?":
        mode = "unset_err"
    elif mode == ":?":
        mode = "empty_err"
    else:
        mode = "simple"

    result = {"name": name, "mode": mode, "arg": match["arg"] or None}
    return result


# Broken
# SHELL_REGEX =r'[^$]((\$(?P<name1>[0-9A-Z_]+))|(\${(?P<name2>[0-9A-Z_]+)((?P<mode>:?[?-]?)(?P<arg>(?R)))}))'


# Test complex only v1
# SHELL_REGEX =r'[^$](\${(?P<name2>[0-9A-Z_]+)((?P<mode>:?[?-]?)(?P<arg>.*))?})'


# Test complex only v2
# SHELL_REGEX =r'[^$](\${(?P<name2>[0-9A-Z_]+)((?P<mode>:?[?-]?)(?P<arg>.*(?R)?.*))?})'


#### WIPPP

# OKK simple: v1 SHELL_REGEX =r'[^$]((\${(?P<name1>[0-9A-Z_]+)((?P<mode>:?[?-]?)(?P<arg>[^}]*))})|(\$(?P<name2>[0-9A-Z_]+)))'
SHELL_REGEX = r"[^$]((\${(?P<name1>[0-9A-Z_]+)((?P<mode>:?[?-]?)(?P<arg>.*))})|(\$(?P<name2>[0-9A-Z_]+)))"


# V2 testing
SHELL_REGEX = r"[^$]((\${(?P<name1>[0-9A-Z_]+)((?P<mode>:?[?-]?)(?P<arg>.*))})|(\$(?P<name2>[0-9A-Z_]+)))"


SHELL_REGEX = re.compile(SHELL_REGEX)  # , flags=regex.DEBUG)


def extract_shell_vars(file):
    "Extract all shell variables call in a file"

    print(f"FILE MATCH: {file}")

    # Open file
    with open(file, encoding="uft-8") as _file:
        lines = _file.readlines()

    content = "".join(lines)

    ### LEXER APPROACH

    # lexer = shlex.shlex(content)
    print(shlex.split(content))
    # for token in lexer:
    #     print ( repr(token))

    #### REGEX APPROACH

    # Parse shell vars, first round
    results = []
    for match in re.finditer(SHELL_REGEX, content):

        result = parse_vars(match)
        print("  NEW MATCH 1: ", result)
        results.append(result)

    # PArse shell vars second round
    found = True
    while found is True:

        cand = [x["arg"] for x in results if isinstance(x["arg"], str)]
        cand = "\n".join(cand)

        # print (cand)
        found = False
        for match in re.finditer(SHELL_REGEX, cand):

            result = parse_vars(match)
            # print ("  NEW MATCH", match.groupdict())
            print("  NEW MATCH 2: ", result)
            var_name = result["name"]
            if len([x for x in results if x["name"] == var_name]) == 0:
                found = True
                results.append(result)

        # TEMP
        # found = False

    print("FINAL RESULT ============================")
    pprint(results)
    return results
