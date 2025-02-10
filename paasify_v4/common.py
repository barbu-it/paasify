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

# import os

import yaml

log = logging.getLogger(__name__)


# pylint: disable=redefined-builtin
def truncate(data, max=72, txt=" ..."):
    "Truncate a text to max lenght and replace by txt"
    data = str(data)
    if max < 0:
        return data
    if len(data) > max:
        return data[: max + len(txt)] + txt
    return data


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


def read_file(file):
    "Read file content"
    with open(file, encoding="utf-8") as _file:
        return "".join(_file.readlines())
