#!/usr/bin/env pytest

import sys
import os
from pprint import pprint
import logging
import json

import unittest
import pytest

import yaml
from typer.testing import CliRunner

from paasify.cli import cli_app
from paasify.app2 import PaasifyApp
import paasify.errors as error

from paasify.common import get_paasify_pkg_dir






# Test cli
# ------------------------
#cwd = os.getcwd()
cwd = os.path.realpath(os.path.dirname(get_paasify_pkg_dir()))
runner = CliRunner()

def test_cli_info_without_project():
    result = runner.invoke(cli_app, ["-vvvvv", "--config", cwd + "/tests/examples", "info"])
    out = result.stdout_bytes.decode("utf-8")
    print (out)
    assert result.exit_code != 0
    #assert "Impossible to find" in out

def test_cli_info_with_project():

    prj_dir = cwd + "/tests/examples/minimal"
    result = runner.invoke(cli_app, ["--config", prj_dir, "info"])
    
    out = result.stdout_bytes.decode("utf-8")
    assert result.exit_code == 0
    




# Test stacks basics
# ------------------------

def test_stacks_resolution(data_regression):
    "Ensure name, app path and direct string config works correctly"

    # Load project
    app_conf = {
        "config": {
            "root_hint": cwd + "/tests/examples/unit_stacks_idents",
        }
    }
    psf = PaasifyApp(payload=app_conf)
    prj = psf.load_project()

    results = []
    for stack in prj.stacks.get_children():
        result = {
            "stack_config": stack.serialize(mode='raw'),
            "stack_name": stack.stack_name,
            # TOFIX: THIS
            "stack_dir": stack.stack_dir,
            "stack_app": stack.app.serialize() if stack.app else None,
        }
        results.append(result)
        
    data_regression.check(results)


def test_stacks_resolution_fail_on_duplicates(data_regression):
    "Ensure things fails when duplicates tasks"

    # Load project
    app_conf = {
        "config": {
            "root_hint": cwd + "/tests/examples/unit_stacks_idents_dup_fail",
        }
    }
    psf = PaasifyApp(payload=app_conf)
    
    # Test the load fails
    try:
        psf.load_project()
        assert False, "Duplicate configuration should have raised an error!"
    except error.ProjectInvalidConfig:
        pass




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


def recursive_replace(dir, old, new):
    "Replace all old occurence by new recursively in directory dir"

    if old == new:
        return

    for (dirpath, dirnames, filenames) in os.walk(dir):
        for file in filenames:
            
            path = os.path.join(dirpath, file)
            data = read_file(path)
            data = data.replace(old, new)
            write_file(path, data)



def load_yaml_file_hierarchy(dir):
    "Load a hierarchy of yaml file and put them in a dict for regression testing"

    # Read project files
    files = []

    for (dirpath, dirnames, filenames) in os.walk(dir):
        for file in filenames:
            files.append(os.path.join(dirpath, file))
            #files.append([dirpath, file])

    pprint(files)
    # Load yaml files
    results = {}
    for file in files:
        # dir = file[0]
        # fname = file[1]
        # path = os.path.join(dir, fname)
        
        with open(file, encoding="utf-8") as _file:
            payload = yaml.safe_load(_file)

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


# Test stacks vars scenarios
# ------------------------
def test_stacks_vars(caplog, data_regression) -> None:
    "Ensure name, app path and direct string config works correctly"

    caplog.set_level(logging.INFO, logger="paasify.cli")

    

    # Load project
    root_prj = cwd + "/tests/examples/var_merge"
    app_conf = {
        "config": {
            "root_hint": root_prj,
        }
    }
    psf = PaasifyApp(payload=app_conf)

    prj = psf.load_project()
    prj.stacks.cmd_stack_assemble()

    # Check results
    recursive_replace(root_prj, root_prj, os.path.relpath(root_prj))
    results = load_yaml_file_hierarchy(root_prj)
    data_regression.check(results)





# Main run
# ------------------------

if __name__ == "__main__":
    
    pytest.main([__file__])


    
    #unittest.main()


