#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

import os
import sys
import traceback
import logging
from enum import Enum
from typing import Optional
from pathlib import Path
from pprint import pprint  # noqa: F401

import yaml
import sh
import typer

from cafram.utils import get_logger, to_yaml, to_json
from cafram.base import CaframException

from paasify import __version__
import paasify.errors as error
from paasify.common import to_bool, OutputFormat
from paasify.app import PaasifyApp

# from rich.console import Console
# from rich.syntax import Syntax


# log = logging.getLogger()
log = logging.getLogger("paasify")

NOTTY = to_bool(os.environ.get("PAASIFY_NOTTY", os.environ.get("NOTTY", "False")))
PAASIFY_TRACE = to_bool(os.environ.get("PAASIFY_TRACE", False))
EDITOR = os.environ.get("EDITOR", "nano")


# CLI documenation
# ==============================

HELP_PROJECT_CMD = ""
HELP_STACKS_CMD = "Stacks Commands"
HELP_DOC_CMD = "Document Commands"
HELP_STACKS_HELPERS = "Stacks Commands"
HELP_SRC_CMD = "Sources Commands"

HELP_HEADER = f"""
Paasify - build your compose-files with ease

version: {__version__}

Paasify is a tool that build and deploy [bold]docker-compose.yml[/bold] files from a central
configuration file called [bold]paasify.yml[/bold]. In this file, define collections sources
and select your app. Then deploy your stacks, test, review and commit your
changes (and reiterate).

Full documentation: [italic green][bold]https://barbu-it.github.io/paasify/[/bold][/italic green]

🧭 Quickstart:

    To start a new project call [bold]my_prj[/bold]:
        paasify init my_prj

    Then add sources and stacks:
        {EDITOR} my_prj/paasify.yml

    Once you're ready, deploy your stacks:
        paasify -c my_prj apply


💡 Getting help:

    For more detailed information on each commands, please use the [bold]--help[/bold] flag
    Some commands provide an [bold]--explain[/bold] flag
    Extra logging is available, use [bold]-v[/bold] flags to increase verbosity


📢 Community:

    Project website:                [italic]https://github.com/barbu-it/paasify[/italic]
    Ask questions or report a bug:  [italic]https://github.com/barbu-it/paasify/issues[/italic]
    Original author: mrjk           [italic]https://github.com/mrjk[/italic]
    License: GPLv3

"""

# Exception handling
# ==============================


def test_logging():
    "Function to test logging"

    log.critical("SHOW CRITICAL")
    log.error("SHOW ERROR")
    log.warning("SHOW WARNING")
    log.notice("SHOW NOTICE")
    log.info("SHOW INFO")
    log.exec("SHOW EXEC")
    log.debug("SHOW DEBUG")
    log.trace("SHOW TRACE")


def clean_terminate(err):
    "Terminate nicely the program depending the exception"

    if PAASIFY_TRACE:
        log.error(traceback.format_exc())

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
        log.critical(f"Paasify exited with backend error. {type(err)}")
        sys.exit(error.ConfigBackendError.rc)

    if err.__class__ in oserrors:

        # Decode OS errors
        # errno = os.strerror(err.errno)
        # errint = str(err.errno)

        log.critical(f"Paasify exited with OS error: {err}")
        sys.exit(err.errno)


class CatchErrors(typer.core.TyperGroup):
    "Class to catch program exceptions and make a nice shutdown"

    def __call__(self, *args, **kwargs):
        "Used to catch program exceptions"

        try:
            return self.main(*args, **kwargs)
        except Exception as exc:
            clean_terminate(exc)

            # If we reached here, then let's go fo a good old Exception
            raise


# Main application
# ==============================

cli_app = typer.Typer(
    cls=CatchErrors,
    help=HELP_HEADER,
    rich_markup_mode="rich",
    invoke_without_command=True,
    no_args_is_help=True,
)


# Generic commands
# ==============================
help_args = {"help_option_names": ["-h", "--help"]}


@cli_app.callback(invoke_without_command=True, context_settings=help_args)
def main(
    ctx: typer.Context,
    verbose: int = typer.Option(
        0, "--verbose", "-v", count=True, min=0, max=5, help="Increase verbosity"
    ),
    working_dir: Optional[Path] = typer.Option(
        # os.getcwd(),  # For absolute paths
        # ".",          # For relative paths
        None,  # For automagic
        "-c",
        "--config",
        help="Path of paasify.yml configuration file.",
        envvar="PAASIFY_PROJECT_DIR",
    ),
    version: bool = typer.Option(
        False,
        "-V",
        "--version",
        help="Show version info",
    ),
    trace: bool = typer.Option(
        False,
        "--trace",
        help="Show traces",
    ),
):
    """

    Prepare Paasify App instance.
    """

    # pylint: disable=global-statement,invalid-name
    global log
    global PAASIFY_TRACE
    PAASIFY_TRACE = trace

    # 50: Crit
    # 40: Err
    # 30: Warn
    #   25: Notice
    # 20: Info
    #   15: Exec
    # 10: Debug
    #   5: Trace
    # 0: Not set

    # Detect extra logging
    dump_payload_log = False
    if verbose > 4:
        verbose -= 1
        dump_payload_log = True

    # Calculate log level
    verbose += 1
    verbose = 30 - (verbose * 5)
    verbose = verbose if verbose > 0 else 0

    # Logger format
    fmt = {
        0: "default",
        2: "struct",
        3: "precise",
        4: "time",
    }
    sformat = "default"
    if trace:
        sformat = fmt[2]

    # Get logger level
    log = get_logger(logger_name="paasify.cli", sformat=sformat)
    log.setLevel(level=verbose)
    # test_logging()

    # Report logging state
    if dump_payload_log:
        log.trace("Exta verbose mode enabled: data will be dumped into logs")
    else:
        log.trace("Trace mode enabled")

    if version:
        print(__version__)
        return

    app_conf = {
        "config": {
            "default_source": "default",
            "cwd": os.getcwd(),
            "root_hint": working_dir,
            "dump_payload_log": dump_payload_log,
            "no_tty": NOTTY,
            # "collections_dir": collections_dir,
        }
    }

    # Init paasify
    paasify = PaasifyApp(payload=app_conf)
    log.debug("Paasify app has been started")

    ctx.obj = {
        "paasify": paasify,
    }


# Generic commands
# ==============================


@cli_app.command("info", rich_help_panel=HELP_PROJECT_CMD)
def cli_info(
    ctx: typer.Context,
):
    """Show context infos"""
    psf = ctx.obj["paasify"]
    psf.info(autoload=True)


@cli_app.command("new", rich_help_panel=HELP_PROJECT_CMD)
def cli_new(
    ctx: typer.Context,
    source: Optional[str] = typer.Option(
        None,
        "--from",
        help="Use another project as source",
    ),
    path: Optional[str] = typer.Argument(
        ".", help="Directory of the project to create"
    ),
):
    """Create a new paasify project"""
    psf = ctx.obj["paasify"]
    psf.new_project(path, source=source)


@cli_app.command("help")
def cli_help(
    ctx: typer.Context,
):
    """Show this help message"""
    print(ctx.parent.get_help())


# Document commands
# ==============================


# pylint: disable=redefined-builtin
@cli_app.command("document_conf", rich_help_panel=HELP_DOC_CMD)
def cli_doc_conf(
    ctx: typer.Context,
    out: Optional[Path] = typer.Option(
        None,
        "-o",
        "--out",
        help="Out directory, where all files are generated",
    ),
    format_: OutputFormat = typer.Option(
        OutputFormat.json,
        "-t",
        "--format",
        help="Output format for stdout",
    ),
):
    """Build configuration schema documentation"""
    psf = ctx.obj["paasify"]
    ret = psf.cmd_config_schema(dest_dir=out)
    if not out:
        if format_ == OutputFormat.yaml:
            ret = to_yaml(ret)
        elif format_ == OutputFormat.json:
            ret = to_json(ret)
        print(ret)


@cli_app.command("document_collection", rich_help_panel=HELP_DOC_CMD)
def cli_doc_collection(
    ctx: typer.Context,
    out: Optional[Path] = typer.Option(
        None,
        "-o",
        "--out",
        help="Out directory, where all files are generated",
    ),
    mkdocs_config: Optional[Path] = typer.Option(
        None,
        "-m",
        "--mkdocs_config",
        help="Directory where to create mkdocs config, omited if empty",
    ),
    path: Optional[str] = typer.Argument(
        ".", help="Directory of the project to create"
    ),
):
    """Build collection documentation"""
    psf = ctx.obj["paasify"]
    assert isinstance(path, str), f"Got: {path}"
    psf.cmd_document(path=path, dest_dir=out, mkdocs_config=mkdocs_config)


# Does not work ????
class DocSubCmd(str, Enum):
    "Source sub commands"
    COLLECTION = "collection"
    CONF = "conf"


@cli_app.command(
    "document",
    hidden=True,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def cli_document(
    ctx: typer.Context,
    cmd: DocSubCmd,
):
    """Command sources"""
    sub = {
        "collection": cli_doc_collection,
        "conf": cli_doc_conf,
    }
    func = sub.get(cmd)
    func(ctx, *ctx.args)


# Source commands
# ==============================


@cli_app.command("src ls", rich_help_panel=HELP_SRC_CMD)
def src_ls(
    ctx: typer.Context,
    explain: bool = typer.Option(
        False, "--explain", "-X", help="Show collection and apps"
    ),
):
    """List sources"""
    paasify = ctx.obj["paasify"]
    prj = paasify.load_project()
    prj.sources.cmd_ls(explain=explain)


@cli_app.command("src install", rich_help_panel=HELP_SRC_CMD)
def src_install(
    ctx: typer.Context,
):
    """Install sources"""
    paasify = ctx.obj["paasify"]
    prj = paasify.load_project()
    prj.sources.cmd_install()


@cli_app.command("src update", rich_help_panel=HELP_SRC_CMD)
def src_update(
    ctx: typer.Context,
):
    """Update sources"""
    paasify = ctx.obj["paasify"]
    prj = paasify.load_project()
    prj.sources.cmd_update()


@cli_app.command("src tree", rich_help_panel=HELP_SRC_CMD)
def src_tree(
    ctx: typer.Context,
):
    """Show source tree"""
    paasify = ctx.obj["paasify"]
    prj = paasify.load_project()
    prj.sources.cmd_tree()


class SrcSubCmd(str, Enum):
    "Source sub commands"

    LS = "ls"
    UPDATE = "update"
    TREE = "tree"
    INSTALL = "install"


@cli_app.command(
    "src",
    hidden=True,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def cli_src(
    ctx: typer.Context,
    cmd: SrcSubCmd,
):
    """Command sources"""
    sub = {
        "ls": src_ls,
        "update": src_update,
        "tree": src_tree,
        "install": src_install,
    }
    func = sub.get(cmd)
    return ctx.invoke(func, ctx)


# Stack commands (Base)
# ==============================


@cli_app.command("ls", rich_help_panel=HELP_STACKS_CMD)
def cli_ls(
    ctx: typer.Context,
    explain: bool = typer.Option(
        False, "--explain", "-X", help="Show stacks structure"
    ),
    stack: Optional[str] = typer.Argument(
        None,
        help="Stack to target, current directory or all, only when explain is enabled",
    ),
):
    """List all stacks"""
    paasify = ctx.obj["paasify"]
    prj = paasify.load_project()
    if explain:
        prj.stacks.cmd_stack_explain(stack_names=stack)
    else:
        prj.stacks.cmd_stack_ls()


@cli_app.command("build", rich_help_panel=HELP_STACKS_CMD)
def cli_assemble(
    ctx: typer.Context,
    explain: bool = typer.Option(
        False, "--explain", "-X", help="Show diff between modifications"
    ),
    stack: Optional[str] = typer.Argument(
        None,
        help="Stack to target, current directory or all",
    ),
):
    """Build docker-files"""

    paasify = ctx.obj["paasify"]
    prj = paasify.load_project()
    prj.stacks.cmd_stack_assemble(stack_names=stack, explain=explain)


@cli_app.command("up", rich_help_panel=HELP_STACKS_CMD)
def cli_up(
    ctx: typer.Context,
    logs: bool = typer.Option(
        False, "--logs", "-l", help="Show running logs after action"
    ),
    stack: Optional[str] = typer.Argument(
        None,
        help="Stack to target, current directory or all",
    ),
):
    """Start docker stack"""
    paasify = ctx.obj["paasify"]
    prj = paasify.load_project()
    prj.stacks.cmd_stack_up(stack_names=stack)

    if logs:
        prj.stacks.cmd_stack_logs(stack_names=stack, follow=True)


@cli_app.command("down", rich_help_panel=HELP_STACKS_CMD)
def cli_down(
    ctx: typer.Context,
    stack: Optional[str] = typer.Argument(
        None,
        help="Stack to target, current directory or all",
    ),
):
    """Stop docker stack"""
    paasify = ctx.obj["paasify"]
    prj = paasify.load_project()
    prj.stacks.cmd_stack_down(stack_names=stack)


@cli_app.command("ps", rich_help_panel=HELP_STACKS_CMD)
def cli_ps(
    ctx: typer.Context,
    stack: Optional[str] = typer.Argument(
        None,
        help="Stack to target, current directory or all",
    ),
):
    """Show docker stack instances"""
    paasify = ctx.obj["paasify"]
    prj = paasify.load_project()
    prj.stacks.cmd_stack_ps(stack_names=stack)


@cli_app.command("logs", rich_help_panel=HELP_STACKS_CMD)
def cli_logs(
    ctx: typer.Context,
    follow: bool = typer.Option(False, "--follow", "-f"),
    stack: Optional[str] = typer.Argument(
        None,
        help="Stack to target, current directory or all",
    ),
):
    """Show stack logs"""
    paasify = ctx.obj["paasify"]
    prj = paasify.load_project()
    prj.stacks.cmd_stack_logs(stack_names=stack, follow=follow)


@cli_app.command("vars", rich_help_panel=HELP_STACKS_CMD)
def cli_vars(
    ctx: typer.Context,
    vars: Optional[str] = typer.Option(
        None,
        help="List of vars comma separated to show only",
    ),
    explain: bool = typer.Option(
        False, "--explain", "-X", help="Show running logs after action"
    ),
    stack: Optional[str] = typer.Argument(
        None,
        help="Stack to target, current directory or all",
    ),
):
    """Dump stack variables"""
    paasify = ctx.obj["paasify"]
    prj = paasify.load_project()
    vars = vars.split(",") if vars else True
    prj.stacks.cmd_stack_vars(stack_names=stack, vars_=vars, explain=explain)


# Stack commands (Helpers)
# ==============================


@cli_app.command("apply", rich_help_panel=HELP_STACKS_HELPERS)
def cli_apply(
    ctx: typer.Context,
    logs: bool = typer.Option(
        False, "--logs", "-l", help="Show running logs after action"
    ),
    stack: Optional[str] = typer.Argument(
        None,
        help="Stack to target, current directory or all",
    ),
):
    """Build and apply stack"""
    paasify = ctx.obj["paasify"]
    prj = paasify.load_project()
    prj.stacks.cmd_stack_apply(stack_names=stack)

    if logs:
        prj.stacks.cmd_stack_logs(stack_names=stack, follow=True)


@cli_app.command("recreate", rich_help_panel=HELP_STACKS_HELPERS)
def cli_recreate(
    ctx: typer.Context,
    logs: bool = typer.Option(
        False, "--logs", "-l", help="Show running logs after action"
    ),
    stack: Optional[str] = typer.Argument(
        None,
        help="Stack to target, current directory or all",
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


def app():
    "Return a Paasify App instance"

    try:
        return cli_app()

    # pylint: disable=broad-except
    except Exception as err:

        # Developper catchall
        log.error(traceback.format_exc())
        log.critical(f"Uncatched error {err.__class__}; this may be a bug!")
        log.critical("Exit 1 with bugs")
        sys.exit(1)


if __name__ == "__main__":
    app()
