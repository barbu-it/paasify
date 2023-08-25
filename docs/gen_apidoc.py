#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# flake8: noqa

# Usual way to call this script: ./gen_apidoc.py src/

# from pprint import pprint
import sys
import os
from distutils.dir_util import copy_tree
import logging
import re

import sh
import click

log = logging.getLogger("mkdocs")
if __name__ == "__main__":
    log = logging.getLogger("gen_apidoc")

#
# Environment conf
# =============================================

# Parse the fast option
from_env = os.environ.get("FAST")
FAST = False
if from_env == "t":
    FAST = True

#
# Constants
# =============================================

PATH = "./src"
BUILD_DIR_SCHEMA = f"{PATH}/jsonschemas"
BUILD_DIR_DOC = f"{PATH}/refs/config"
BUILD_DIR_RAW = f"{PATH}/refs/raw"
BUILD_DIR_SCHEMA = BUILD_DIR_RAW
ENV = os.environ.copy()
ENV.update(
    {
        "COLUMNS": "82",
    }
)

CLI_USAGE = """
Generate all artifacts for mkdocs after the building. This
script can be both called manually or via the mkdocs-simple-hooks
plugin.

Example:
```
./gen_apidoc.py src/
```

Config definition in `mkdocs.yml`:
```
plugins:
  - mkdocs-simple-hooks:
      hooks:
        #on_post_build: "docs.hooks:copy_logos"
        on_files: "docs.hooks:install_files"
```

The same command is called each time mkdocs is built.

Note: If you edit this script and generate new files, don't forget
      to update .gitignore as well.
"""

#
# Helpers
# =============================================


def get_paasify_pkg_dir():
    """Return the dir where the actual paasify source code lives"""

    # pylint: disable=import-outside-toplevel
    import paasify as _

    return os.path.dirname(_.__file__)


#
# mkdoc API
# =============================================


def copy_logos(*args, **kwargs):
    "Insert logo into the site"

    log.info("Copy logos into project root")
    copy_tree("../logo/", "src/logo", update=True)


def gen_cli_usage(*args, **kwargs):
    "Generate cli usage"
    dest = f"{BUILD_DIR_RAW}/cli_usage.txt"
    log.info(f"Generate paasify help output in {dest}")
    log.info(f"cmd: paasify help")

    out = sh.paasify("help", _tty_out=False, _env=ENV)
    out = out.stdout.decode("utf-8")
    out = re.sub(r" +\n", "\n", out)
    with open(dest, "w") as file_:
        file_.write(out)


def install_jupyter(*args, **kwargs):
    "Install jupyter bash kernel module"
    log.info("Installing jupyter bash kernel")
    log.info(f"cmd: python -m bash_kernel.install")
    sh.python("-m", "bash_kernel.install")

    # At least, I tried ... lol
    # import bash_kernel
    # bash_kernel.install


def gen_internal_collection(*args, **kwargs):
    "Generate internal collection doc"

    col_path = os.path.join(get_paasify_pkg_dir(), "assets", "collections", "paasify")
    log.info(f"Generate internal collection: {col_path}")
    sh.paasify(
        "document_collection",
        col_path,
        "--out",
        "src/plugins_apidoc",
    )

    return


def gen_schemas(*args, **kwargs):
    "Generate jsonschema"
    log.info("Generate jsonschemas")

    sh.paasify(
        "document_conf",
        "--out",
        "src/paasify_apidoc",
    )

    return

#
# Entrypoints
# =============================================

def require_restart():
    "Return true if never executed before"
    return not os.path.isdir("src/logo")

# Main hook
def on_files_hook(*args, **kwargs):
    "Pre hook to install everything"
    global FAST

    restart = require_restart()
    if FAST and not restart:
        log.info("Skip generate scripts, only run at startup!")
        return

    copy_logos()
    gen_cli_usage()
    install_jupyter()
    gen_schemas()
    gen_internal_collection()
    FAST = True

    log.info("Pre-hooks are all done :)")

    if restart and "serve" in sys.argv:
        log.error(f"The build command was not run, please run again: {' '.join(sys.argv)}")
        sys.exit(1)


# Cli interface
@click.command(help=CLI_USAGE)
@click.argument("path", type=click.Path(exists=True))
def main(path):
    """
    Script to generate extra documentation bits
    """

    if not path:
        raise

    PATH = path
    BUILD_DIR_SCHEMA = f"{PATH}/jsonschemas"
    BUILD_DIR_DOC = f"{PATH}/refs/config"
    BUILD_DIR_RAW = f"{PATH}/refs/raw"
    BUILD_DIR_SCHEMA = BUILD_DIR_RAW

    log = logging.basicConfig(level=logging.INFO)

    click.echo("This script will copy assets into mkdocs dir")
    on_files_hook()
    click.echo("Done!")


if __name__ == "__main__":
    main()
