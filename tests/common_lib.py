#!/usr/bin/env pytest
# -*- coding: utf-8 -*-

import os
import pytest
import yaml
from paasify.common import get_paasify_pkg_dir


# Test cli
# ------------------------
cwd = os.path.realpath(os.path.dirname(get_paasify_pkg_dir()))


# Test stacks docker-file search
# ------------------------


def read_file(file):
    "Read file content"
    with open(file, encoding="utf-8") as _file:
        return "".join(_file.readlines())


def write_file(file, content):
    "Write content to file"

    file_folder = os.path.dirname(file)
    if not os.path.exists(file_folder):
        os.makedirs(file_folder)

    with open(file, "w", encoding="utf-8") as _file:
        _file.write(content)


def exclude_file_pattern(path):
    excludes = [".swp", "/_dumps/"]
    skip = False
    for exclude in excludes:
        if exclude in path:
            print(f"SKIP PATH: {path}")
            skip = True

    return skip


def recursive_replace(dir, old, new):
    "Replace all old occurence by new recursively in directory dir"

    if old == new:
        return

    for (dirpath, dirnames, filenames) in os.walk(dir):
        for file in filenames:

            path = os.path.join(dirpath, file)
            if exclude_file_pattern(path):
                print("SKIP", path)
                continue

            data = read_file(path)
            data = data.replace(old, new)
            write_file(path, data)


def load_yaml_file_hierarchy(dir):
    "Load a hierarchy of yaml file and put them in a dict for regression testing"

    # Read project files
    files = []

    for (dirpath, dirnames, filenames) in os.walk(dir):
        for file in filenames:
            path = os.path.join(dirpath, file)
            if exclude_file_pattern(path):
                continue
            files.append(path)

    # Load yaml files
    results = {}
    for file in files:

        with open(file, encoding="utf-8") as _file:
            try:
                payload = yaml.safe_load(_file)
            except yaml.scanner.ScannerError:
                payload = _file.read()

        # if abs_path != dir:
        #     # Trigger abspath dir replacement
        #     # We need to do that as docker compose config transform
        #     # generate absolute path for its volumes.

        #     str_payload = json.dumps(payload)
        #     str_payload = str_payload.replace(abs_path, dir)
        #     payload = json.loads(str_payload)

        path = os.path.relpath(file)
        results[path] = payload

    return results
