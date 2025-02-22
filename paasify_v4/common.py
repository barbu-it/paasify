"""
Common utility functions for Paasify

This module provides common utility functions used throughout Paasify:

- truncate: Truncate text to a maximum length
- from_json: Parse JSON string into Python dict
- to_json: Convert Python object to JSON string
- from_yaml: Parse YAML string into Python dict  
- to_yaml: Convert Python object to YAML string
"""

import json
import logging
import os
import re
from pathlib import Path

import yaml

# import os


log = logging.getLogger(__name__)

# String utils
# ================================================


# pylint: disable=redefined-builtin
def truncate(data, max=72, txt="..."):
    """Truncate a text to a maximum length.

    Args:
        data: The text to truncate
        max: Maximum length of the output text. If positive, truncates from end.
             If negative, truncates from start. If 0, returns original text.
        txt: Text to append/prepend to indicate truncation

    Returns:
        The truncated text string with txt added to indicate truncation
    """
    data = str(data)
    if max == 0:
        return data
    if len(data) > max:
        if max > 0:
            return data[: max + len(txt)] + txt
        return txt + data[(max - len(txt)) :]
    return data


# TODO: Add tests on this one
def to_domain(string, sep=".", alt="-"):
    "Transform any string to valid domain name"

    assert isinstance(string, str), f"String must be a string, not: {type(string)}"

    domain = string.split(sep)
    result = []
    for part in domain:
        part = re.sub("[^a-zA-Z0-9]", alt, part)
        part.strip(alt)
        result.append(part)

    return ".".join(result)


# Python types helpers
# ================================================


def flatten(array):
    "Flatten any arrays nested arrays"
    if array == []:
        return array
    if isinstance(array[0], list):
        return flatten(array[0]) + flatten(array[1:])
    return array[:1] + flatten(array[1:])


# Data utils
# ================================================


def from_json(string):
    "Transform JSON string to python dict"
    return json.loads(string)


def to_json(obj, nice=True):
    "Transform JSON string to python dict"
    if nice:
        return json.dumps(obj, indent=2)
    return json.dumps(obj)


def from_yaml(string, strip_last=False):
    "Transform YAML string to python dict"
    data = yaml.safe_load(string)
    if strip_last:
        return data.rstrip()
    return data


def to_yaml(obj, strip_last=False):
    "Transform obj to YAML"
    data = yaml.dump(obj)
    if strip_last:
        return data.rstrip()
    return data

    # # Ruamel support
    # options = {}
    # string_stream = StringIO()

    # if isinstance(obj, str):
    #     obj = json.loads(obj)

    # yaml.dump(obj, string_stream, **options)
    # output_str = string_stream.getvalue()
    # string_stream.close()
    # if not headers:
    #     output_str = output_str.split("\n", 2)[2]
    # return output_str


def dict_to_env(dict):
    "Convert dict to env"
    return "\n".join([f"{k}={v}" for k, v in dict.items()])


def read_file(file):
    "Read file content, accept pathlib objects"
    file = str(file) if isinstance(file, Path) else file
    with open(file, encoding="utf-8") as _file:
        return "".join(_file.readlines())


def write_file(file, content):
    "Write content to file, accept pathlib objects"

    file = str(file) if isinstance(file, Path) else file
    file_folder = os.path.dirname(file)
    if not os.path.exists(file_folder):
        os.makedirs(file_folder)

    with open(file, "w", encoding="utf-8") as _file:
        _file.write(content)


# File utils
# ================================================


def find_file_in_path(names, path):
    """
    Find every files that exists in a path
    """
    assert isinstance(names, list), f"Names must be array, not: {type(names)}"

    result = []
    for name in names:
        file_path = os.path.join(path, name)
        if os.access(file_path, os.R_OK):
            result.append(file_path)

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
    every listed paths. To be used with ouput of: list_parent_dirs
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


def find_files_down(names, path, depth=3, ignore_dirs=None):
    "Find files in path and subdirectories down to depth"
    result = []
    ignore_dirs = ignore_dirs or [
        ".git",
        "node_modules",
        "__pycache__",
    ]  # Default ignored dirs

    def scan_dir(current_path, current_depth):

        if current_depth > depth:
            log.debug(
                "Skip directory %s at depth %s/%s", current_path, current_depth, depth
            )
            return
        try:
            log.debug("Scanning %s at depth %s/%s", current_path, current_depth, depth)
            with os.scandir(current_path) as entries:
                for entry in entries:
                    if entry.is_file() and entry.name in names:
                        result.append(entry.path)
                    elif entry.is_dir() and entry.name not in ignore_dirs:
                        scan_dir(entry.path, current_depth + 1)
        except PermissionError as error:
            log.debug("Skip %s because of permission error: %s", current_path, error)

    scan_dir(path, 0)
    return result
