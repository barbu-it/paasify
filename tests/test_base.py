#!/usr/bin/env pytest
# -*- coding: utf-8 -*-

import os
from pprint import pprint  # noqa: F401
import logging
import importlib

import pytest

from typer.testing import CliRunner

from paasify.cli import cli_app
from paasify.app import PaasifyApp
import paasify.errors as error

from paasify.common import get_paasify_pkg_dir

common = importlib.import_module("common_lib")

# Test cli
# ------------------------
cwd = os.path.realpath(os.path.dirname(get_paasify_pkg_dir()))
runner = CliRunner()


def test_cli_info_without_project():
    result = runner.invoke(
        cli_app, ["-vvvvv", "--config", cwd + "/tests/examples", "info"]
    )
    out = result.stdout_bytes.decode("utf-8")
    print(out)
    assert result.exit_code != 0
    # assert "Impossible to find" in out


def test_cli_info_with_project():

    prj_dir = cwd + "/tests/examples/minimal"
    result = runner.invoke(cli_app, ["--config", prj_dir, "info"])

    # out = result.stdout_bytes.decode("utf-8")
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
            "stack_config": stack.serialize(mode="raw"),
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
    common.recursive_replace(root_prj, root_prj, os.path.relpath(root_prj))
    results = common.load_yaml_file_hierarchy(root_prj)
    data_regression.check(results)


# Main run
# ------------------------
if __name__ == "__main__":

    pytest.main([__file__])

    # unittest.main()
