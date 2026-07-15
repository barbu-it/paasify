"Main app command line interface"

# import sys
import logging
import os
from argparse import SUPPRESS
from pprint import pprint

from clak import Argument, Command, LoggingOptMixin, Parser
from clak.views import ListView, ShowView
from superconf.anchors import PathAnchor

import paasify_v4.exception as exc
from paasify_v4.app import PaasifyRunner
from paasify_v4.cli.catalog import AppGroup, CollectionGroup
from paasify_v4.cli.dynamic import DynMixin
from paasify_v4.cli.namespaces import NamespaceGroup
from paasify_v4.cli.pods import PodGroup
from paasify_v4.cli.stacks import StackGroup, StackTreeCmd

# from paasify_v4.cli.devel import StackGroup, PodGroup


logger = logging.getLogger(__name__)


# Beta
# ================================================


class Devel(Parser):
    "Developpement commands"

    # aliases = Argument("--alias", "-a", action="append", help="Alias")  # (5)!
    # name = Argument("NAME", help="Name")

    def cli_run(self, name=None, aliases=None, force=False, config=None, **_):
        print("Devel command executed")


# Main Prod application
# ================================================


class DebugCmd(Parser):
    "Debug commands"

    def cli_run(self, ctx=None, **_):
        "Main command"
        head = "=" * 80

        print(head)
        print("Logging")
        print(head)
        logger.debug("Hello World - App")
        logger.info("Hello World - App")
        logger.warning("Hello World - App")
        logger.error("Hello World - App")
        self.logger.debug("Hello World - Self")
        self.logger.info("Hello World - Self")
        self.logger.warning("Hello World - Self")
        self.logger.error("Hello World - Self")

        print(head)
        print("Arguments")
        print(head)
        ShowView(ctx.args.__dict__).render()

        print(head)
        print("Debug context")
        print(head)
        pprint(ctx.__dict__)

        print(head)
        print("Debug infos")
        print(head)

        cwd = ctx.data["dir_cwd"]
        print("Working dir:")
        print(f"  get_path: {cwd.get_path()}")
        print(f"  get_dir : {cwd.get_dir()}")
        print(f"  get_dir (abs): {cwd.get_dir(mode='abs')}")
        print(f"  get_dir (rel): {cwd.get_dir(mode='rel')}")


# Main application
# ================================================


# from clak.common import get_top_package


class AppMain(LoggingOptMixin, DynMixin, Parser):
    """Paasify, manage your dockerized apps with claass and compose."""

    class Meta:
        "Main app config"
        log_prefix = f"{__name__.split('.', maxsplit=1)[0]}"
        # log_prefix = "paasify_v4"
        known_exceptions = [
            exc.PaasifyError,
        ]

        # log_levels = [
        #     ["paasify_v4.cli"],
        #     [
        #         "paasify_v4.cli",
        #         "paasify_v4.models",
        #         "paasify_v4.engine_docker",
        #         # "paasify_v4",
        #     ],
        #     # [
        #     #     "paasify_v4",
        #     #     # "clak",
        #     # ],
        #     [
        #         "paasify_v4",
        #         "mrjk_components",
        #         "sh.command.process",
        #     ],
        #     [""],
        # ]

        # log_silent = [
        #     "sh.command.process.streamreader",
        #     "sh.command.process.streamwriter",
        #     "sh.stream_bufferer",
        #     "sh.streamreader",
        #     "sh.streamwriter",
        #     "sh.command.process",
        # ]

        log_levels = [
            [
                "INFO|paasify_v4.cli",
                "WARNING|sh.command.process.streamreader",
                "WARNING|sh.command.process.streamwriter",
                "WARNING|sh.stream_bufferer",
                "WARNING|sh.streamreader",
                "WARNING|sh.streamwriter",
                "WARNING|sh.command.process",
            ],
            ["DEBUG|paasify_v4.cli"],
            [
                "INFO|paasify_v4.models",
                "INFO|paasify_v4.engine_docker",
            ],
            [
                "DEBUG|paasify_v4.models",
                "DEBUG|paasify_v4.engine_docker",
            ],
            [
                "INFO|paasify_v4",
                "INFO|mrjk_components",
                "INFO|sh.command.process",
                "INFO|superconf",
            ],
            [
                "DEBUG|paasify_v4",
                "DEBUG|mrjk_components",
                "DEBUG|superconf",
            ],
            ["INFO|"],
            ["DEBUG|"],
        ]

    # Define options
    # ----------------------

    debug = Argument("--debug", action="store_true", help="Enable debug mode")  # (8)!
    config = Argument("--config", "-c", help="Config file path", default="config.yaml")

    work_dir = Argument("--work-dir", "-C", help="Working directory", default=SUPPRESS)
    dir_mode = Argument(
        "--dir-mode",
        "-D",
        help="Directory mode",
        choices=["abs", "rel", "auto"],
        default="auto",
    )

    collections_dirs = Argument(
        "--collections-dirs", "-L", help="Collections directories", default=SUPPRESS
    )

    # Define subcommands
    # ----------------------

    # Component commands
    app = Command(AppGroup, help="==SUPPRESS==", aliases=["a"])
    collection = Command(CollectionGroup, help="==SUPPRESS==", aliases=["c"])
    pod = Command(PodGroup, help="==SUPPRESS==", aliases=["p"])
    stack = Command(StackGroup, help="==SUPPRESS==", aliases=["s"])
    ns = Command(NamespaceGroup, help="==SUPPRESS==", aliases=["n"])

    # Quick commands
    tree = Command(StackTreeCmd, aliases=["t"])

    # Beta commands
    # command2 = Command(AppCommand2)
    # demo = Command(DemoCmd)
    dev = Command(Devel)
    debug = Command(DebugCmd)

    def cli_group(self, ctx, **_):
        "Main group"

        # Fetch arguments
        _dir_mode = ctx.args.dir_mode
        _working_dir = ctx.args.get("work_dir", SUPPRESS)  # TODO: Add tests in clak

        # Prepare paths
        working_dir = _working_dir
        if _working_dir is SUPPRESS:
            working_dir = "."
        dir_mode = _dir_mode
        if dir_mode == "auto":
            dir_mode = "rel"
            if _working_dir and os.path.isabs(_working_dir):
                dir_mode = "abs"
        working_dir = PathAnchor(working_dir, name="working_dir", mode=dir_mode)

        # Register data
        ctx.data["dir_cwd"] = working_dir
        ctx.data["dir_mode"] = dir_mode

        # Generate default collections paths
        collections_paths_default = [
            os.path.expanduser("~/.paasify/collections"),
            "/etc/paasify/collections",
            "/usr/local/share/paasify/collections",
        ]

        # Add command line extra paths
        collections_paths_user = ctx.args.get("collections_dirs", SUPPRESS)
        if collections_paths_user is not SUPPRESS:
            collections_paths_user = collections_paths_user.split(":")
        else:
            collections_paths_user = []

        # Extra temporary collections
        test_path1 = "/home/jez/volumes/data/prj/mrjk/bench_paasify/work__v4/paasify_v4/SOURCE_v1"
        test_path2 = "/home/jez/volumes/data/prj/mrjk/bench_paasify/work__v4/paasify_v4/SOURCE_v2"
        test_path4 = "/home/jez/volumes/data/prj/mrjk/bench_paasify/work__v4/paasify_v4/SOURCE_v4"
        collections_paths_extra = [
            # test_path2,
            # test_path1,
            test_path4,
        ]

        # Merge paths and start runner
        paths_collections = (
            collections_paths_user + collections_paths_extra + collections_paths_default
        )
        ctx.data["runner"] = PaasifyRunner(
            start_path=~working_dir, collections_paths=paths_collections
        )
