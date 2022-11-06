#!/usr/bin/env python3
"""Paasify CLI interface

This API provides a similar experience as the CLI, but in Python.

Example:
``` py title="test.py"
from paasify.cli import app

paasify = app()
paasify.info()
paasify.apply()
```

"""

# pylint: disable=logging-fstring-interpolation

# Run like this:
#   python3 python_cli.py -vvvv demo
# Author: mrjk

import os
import sys
from enum import Enum

import traceback

from typing import Optional


from pprint import pprint
from pathlib import Path
import yaml

import sh
import typer

from cafram.utils import get_logger
from cafram.base import CaframException

import paasify.errors as error
from paasify.version import __version__
from paasify.common import OutputFormat, SchemaTarget
from paasify.app2 import PaasifyApp

# from rich.console import Console
# from rich.syntax import Syntax

# import paasify.app as Paasify


# from paasify.app import DirectoryItem, Namespace
# from paasify.app2 import Project

# from paasify.app import App

# import os
# import os.path

# import logging
# log = logging.getLogger("paasify")

log = get_logger(logger_name="paasify.cli")


cli_app = typer.Typer(
    help="Paasify, build your compose-files",
    invoke_without_command=True,
    no_args_is_help=True,
)


@cli_app.callback()
def main(
    ctx: typer.Context,
    verbose: int = typer.Option(1, "--verbose", "-v", count=True, min=0, max=5),
    working_dir: str = typer.Option(
        # os.getcwd(),  # For absolute paths
        # ".",          # For relative paths
        None,  # For automagic
        "-c",
        "--config",
        help="Path of paasify.yml configuration file.",
        envvar="PAASIFY_PROJECT_DIR",
    ),
    # collections_dir: Path = typer.Option(
    #     f"$HOME/.config/paasify/collections",
    #     "-l",
    #     "--collections_dir",
    #     help="Path of paasify collections directory.",
    #     envvar="PAASIFY_COLLECTIONS_DIR",
    # ),
    version: bool = typer.Option(
        False,
        "--version",
        help="Show version info",
    ),
):
    """
    Prepare Paasify App instance.
    """

    # 50: Crit
    # 40: Err
    # 30: Warn
    #   25: Notice
    # 20: Info
    #   15: Exec
    # 10: Debug
    #   5: Trace
    # 0: Not set

    verbose = 30 - (verbose * 5)
    verbose = verbose if verbose > 0 else 0
    log.setLevel(level=verbose)

    # log.critical("SHOW CRITICAL")
    # log.error("SHOW ERROR")
    # log.warning("SHOW WARNING")

    # log.notice("SHOW NOTICE")
    # log.info("SHOW INFO")
    # log.exec("SHOW EXEC")
    # log.debug("SHOW DEBUG")
    # log.trace("SHOW TRACE")

    # Init paasify
    app_conf = {
        "config": {
            "default_source": "default",
            "cwd": os.getcwd(),
            "root_hint": working_dir,
            # "collections_dir": collections_dir,
        }
    }

    if version:
        print(__version__)
        return

    paasify = PaasifyApp(payload=app_conf)

    ctx.obj = {
        "paasify": paasify,
    }


# Generic commands
# ==============================
@cli_app.command("info")
def cli_info(
    ctx: typer.Context,
):
    """Show context infos"""
    psf = ctx.obj["paasify"]
    psf.info(autoload=True)


@cli_app.command("explain")
def cli_explain(
    ctx: typer.Context,
    mode: Optional[str] = typer.Option(
        None,
        help="If a path, generate the doc, if none, report stdout",
    ),
    stack: Optional[str] = typer.Argument(
        None,
        help="Stack to target, current cirectory or all",
    ),
):
    """Show project plugins"""
    psf = ctx.obj["paasify"]
    prj = psf.load_project()
    prj.stacks.cmd_stack_explain(stack_names=stack, mode=mode)


@cli_app.command("ls")
def cli_ls(
    ctx: typer.Context,
):
    """List all stacks"""
    paasify = ctx.obj["paasify"]
    prj = paasify.load_project()
    prj.stacks.cmd_stack_ls()


# pylint: disable=redefined-builtin
@cli_app.command("schema")
def cli_schema(
    ctx: typer.Context,
    format: OutputFormat = typer.Option(
        OutputFormat.yaml.value,
        help="Output format",
    ),
    target: SchemaTarget = typer.Argument(
        SchemaTarget.prj.value,
        help="Select object schema",
    ),
):
    """Show paasify configurations schema format"""
    psf = ctx.obj["paasify"]
    out = psf.cmd_config_schema(format=format, target=target)
    print(out)


# @cli_app.command("init")
# def cli_init(
#     ctx: typer.Context,
#     name: Optional[str] = typer.Argument(
#         None,
#         help="Name of reference project to create",
#     ),
# ):
#     """Create new project/namespace"""
#     paasify = ctx.obj["paasify"]
#     paasify.init_project(name)


@cli_app.command("help")
def cli_help(
    ctx: typer.Context,
):
    """Show this help message"""
    print(ctx.parent.get_help())


# Source commands
# ==============================
# TODO: Fix source commands


@cli_app.command()
def src_ls(
    ctx: typer.Context,
):
    """List sources"""
    paasify = ctx.obj["paasify"]
    prj = paasify.load_project()
    prj.sources.cmd_ls()


@cli_app.command()
def src_install(
    ctx: typer.Context,
):
    """Install sources"""
    paasify = ctx.obj["paasify"]
    prj = paasify.load_project()
    prj.sources.cmd_install()


@cli_app.command()
def src_update(
    ctx: typer.Context,
):
    """Update sources"""
    paasify = ctx.obj["paasify"]
    prj = paasify.load_project()
    prj.sources.cmd_update()


@cli_app.command()
def src_tree(
    ctx: typer.Context,
):
    """Show source tree"""
    paasify = ctx.obj["paasify"]
    prj = paasify.load_project()
    prj.cmd_src_tree()


# Stack commands (Base)
# ==============================


@cli_app.command("build")
def cli_assemble(
    ctx: typer.Context,
    stack: Optional[str] = typer.Argument(
        None,
        help="Stack to target, current cirectory or all",
    ),
):
    """Build docker-files"""

    paasify = ctx.obj["paasify"]
    prj = paasify.load_project()
    prj.stacks.cmd_stack_assemble(stack_names=stack)


@cli_app.command("up")
def cli_up(
    ctx: typer.Context,
    logs: bool = typer.Option(
        False, "--logs", "-l", help="Show running logs after action"
    ),
    stack: Optional[str] = typer.Argument(
        None,
        help="Stack to target, current cirectory or all",
    ),
):
    """Start docker stack"""
    paasify = ctx.obj["paasify"]
    prj = paasify.load_project()
    prj.stacks.cmd_stack_up(stack_names=stack)

    if logs:
        prj.stacks.cmd_stack_logs(stack_names=stack, follow=True)


@cli_app.command("down")
def cli_down(
    ctx: typer.Context,
    stack: Optional[str] = typer.Argument(
        None,
        help="Stack to target, current cirectory or all",
    ),
):
    """Stop docker stack"""
    paasify = ctx.obj["paasify"]
    prj = paasify.load_project()
    prj.stacks.cmd_stack_down(stack_names=stack)


@cli_app.command("ps")
def cli_ps(
    ctx: typer.Context,
    stack: Optional[str] = typer.Argument(
        None,
        help="Stack to target, current cirectory or all",
    ),
):
    """Show docker stack instances"""
    paasify = ctx.obj["paasify"]
    prj = paasify.load_project()
    prj.stacks.cmd_stack_ps(stack_names=stack)


@cli_app.command("logs")
def cli_logs(
    ctx: typer.Context,
    follow: bool = typer.Option(False, "--follow", "-f"),
    stack: Optional[str] = typer.Argument(
        None,
        help="Stack to target, current cirectory or all",
    ),
):
    """Show stack logs"""
    paasify = ctx.obj["paasify"]
    prj = paasify.load_project()
    prj.stacks.cmd_stack_logs(stack_names=stack, follow=follow)


# Stack commands (Helpers)
# ==============================


@cli_app.command("apply")
def cli_apply(
    ctx: typer.Context,
    logs: bool = typer.Option(
        False, "--logs", "-l", help="Show running logs after action"
    ),
    stack: Optional[str] = typer.Argument(
        None,
        help="Stack to target, current cirectory or all",
    ),
):
    """Build and apply stack"""
    paasify = ctx.obj["paasify"]
    prj = paasify.load_project()
    prj.stacks.cmd_stack_apply(stack_names=stack)

    if logs:
        prj.stacks.cmd_stack_logs(stack_names=stack, follow=True)


@cli_app.command("recreate")
def cli_recreate(
    ctx: typer.Context,
    logs: bool = typer.Option(
        False, "--logs", "-l", help="Show running logs after action"
    ),
    stack: Optional[str] = typer.Argument(
        None,
        help="Stack to target, current cirectory or all",
    ),
):
    """Stop, rebuild and create stack"""
    paasify = ctx.obj["paasify"]
    prj = paasify.load_project()
    prj.stacks.cmd_stack_recreate(stack_names=stack)

    if logs:
        prj.stacks.cmd_stack_logs(stack_names=stack, follow=True)


# Top levels helpers
# ==============================


def clean_terminate(err):
    "Terminate nicely the program depending the exception"

    # log.error(traceback.format_exc())

    oserrors = [
        PermissionError,
        FileExistsError,
        FileNotFoundError,
        InterruptedError,
        IsADirectoryError,
        NotADirectoryError,
        TimeoutError,
    ]

    # Choose dead end way
    if isinstance(err, error.PaasifyError):
        err_name = err.__class__.__name__
        if isinstance(err.advice, str):
            log.warning(err.advice)

        log.error(err)
        log.critical(f"Paasify exited with: error {err.rc}: {err_name}")
        sys.exit(err.rc)

    if isinstance(err, yaml.scanner.ScannerError):
        log.critical(err)
        log.critical("Paasify exited with: YAML Scanner error (file syntax)")
        sys.exit(error.YAMLError.rc)

    if isinstance(err, yaml.composer.ComposerError):
        log.critical(err)
        log.critical("Paasify exited with: YAML Composer error (file syntax)")
        sys.exit(error.YAMLError.rc)

    if isinstance(err, yaml.parser.ParserError):
        log.critical(err)
        log.critical("Paasify exited with: YAML Parser error (file format)")
        sys.exit(error.YAMLError.rc)

    if isinstance(err, sh.ErrorReturnCode):
        log.critical(err)
        log.critical(f"Paasify exited with: failed command returned {err.exit_code}")
        sys.exit(error.ShellCommandFailed.rc)

    if isinstance(err, CaframException):
        log.critical(err)
        log.critical("Paasify exited with backend error.")
        sys.exit(error.ConfigBackendError.rc)

    if err.__class__ in oserrors:

        # Decode OS errors
        # errno = os.strerror(err.errno)
        # errint = str(err.errno)

        log.critical(f"Paasify exited with OS error: {err}")
        sys.exit(err.errno)


def app():
    "Return a Paasify App instance"

    try:
        return cli_app()

    # pylint: disable=broad-except
    except Exception as err:

        clean_terminate(err)

        # Developper catchall
        log.error(traceback.format_exc())
        log.critical(f"Uncatched error {err.__class__}; this may be a bug!")
        log.critical("Exit 1 with bugs")
        sys.exit(1)


if __name__ == "__main__":
    app()
