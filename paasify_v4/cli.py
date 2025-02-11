"Main app command line interface"

import os

# import sys
import logging
from pprint import pprint

from argparse import SUPPRESS
from clak import Parser, Argument, Command, LoggingOptMixin
from clak.views import ListView, ShowView
from superconf.anchors2 import PathAnchor

from paasify_v4.core_catalog import PaasifyCatalog
from paasify_v4.common import truncate, to_yaml


from paasify_v4.core_catalog_cli import AppGroup, CollectionGroup
from paasify_v4.cli_devel import StackGroup, NamespaceGroup, PodGroup
from paasify_v4.cli_dyn import DynMixin, DynUpCmd
import paasify_v4.exception as exc


logger = logging.getLogger(__name__)
# Never grab root, this break loggingMixin
# logger_root = logging.getLogger()


# Beta
# ================================================


# class AppCommand2(Parser):
#     "Command 2, with option and positional arguments"
#     aliases = Argument("--alias", "-a", action="append", help="Alias")  # (5)!
#     name = Argument("NAME", help="Name")

#     def cli_run(self, name=None, aliases=None, force=False, config=None, **_):  # (6)!
#         print(f"Run command 2 World on: {name} in '{config}' file (force_mode={force})")
#         for alias in aliases or []:
#             print(f"Map: {alias} -> {name}")


class Devel(Parser):
    "Developpement commands"
    # aliases = Argument("--alias", "-a", action="append", help="Alias")  # (5)!
    # name = Argument("NAME", help="Name")

    def cli_run(self, name=None, aliases=None, force=False, config=None, **_):
        print("Devel command executed")

        # test_path1 = "/home/jez/volumes/data/prj/mrjk/bench_paasify/python-paasify__work__v4/pocs/v4_collections/SOURCE_v1"
        # test_path2 = "/home/jez/volumes/data/prj/mrjk/bench_paasify/python-paasify__work__v4/pocs/v4_collections/SOURCE_v2"
        # collections_paths = [
        #     # test_path1,
        #     # test_path2,
        # ]

        # out = PaasifyCatalog(collections_paths=collections_paths)

        # pprint(out)
        # pprint(out.__dict__)

        # print("======================")
        # o = out.walk_collections_paths()
        # pprint(o)


# class DemoCmd(Parser):
#     "Demo viewers"

#     def cli_run(self, ctx=None, **_):
#         "Main command"

#         # Tests1 - ShowView
#         data_item_dict1 = {
#             "name": "World",
#             "age": 42,
#             "city": "Paris",
#         }
#         data_item_list1 = [
#             "World",
#             42,
#             "Paris",
#         ]

#         view = ShowView(data_item_dict1)
#         view.render()

#         view = ShowView(data_item_list1)
#         view.render()

#         # Tests2 - DictView

#         data_item_dict2 = {
#             "name": "World2",
#             "age": 43,
#             "city": "Berlin",
#         }
#         data_items_dict_of_dicts = {
#             "item1": data_item_dict1,
#             "item2": data_item_dict2,
#         }
#         view = ListView(data_items_dict_of_dicts)
#         view.render()

#         # Tests3 - ListView
#         data_items_list_of_dicts = [
#             data_item_dict1,
#             data_item_dict2,
#         ]
#         view = ListView(data_items_list_of_dicts)
#         view.render()

#         return


# Main Prod application
# ================================================


class DebugCmd(Parser):
    "Debug commands"

    def cli_run(self, ctx=None, **_):
        "Main command"
        head = lambda: print("=" * 80)

        head()
        print("Logging")
        head()
        logger.debug("Hello World - App")
        logger.info("Hello World - App")
        logger.warning("Hello World - App")
        logger.error("Hello World - App")
        self.logger.debug("Hello World - Self")
        self.logger.info("Hello World - Self")
        self.logger.warning("Hello World - Self")
        self.logger.error("Hello World - Self")
        # logger_root.warning("Hello World - Root")

        head()
        print("Arguments")
        head()
        ShowView(ctx.args.__dict__).render()

        head()
        print("Debug context")
        head()
        pprint(ctx.__dict__)
        # ListView(ctx.__dict__).render()

        head()
        print("Debug infos")
        head()

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
    """Demo application with options and two subcommands."""

    class Meta:
        "Main app config"
        log_prefix = f"{__name__.split('.', maxsplit=1)[0]}"
        # log_prefix = "paasify_v4"
        known_exceptions = [
            exc.PaasifyError,
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
    collection = Command(CollectionGroup, help="==SUPPRESS==")
    pod = Command(PodGroup)  # , help="==SUPPRESS==")
    stack = Command(StackGroup)  # , help="==SUPPRESS==")
    ns = Command(NamespaceGroup)  # , help="==SUPPRESS==")



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

        # Create Path Anchors
        working_dir = PathAnchor(working_dir, name="working_dir", mode=dir_mode)

        # Prepare paths_collections
        collections_dirs = ctx.args.get("collections_dirs", SUPPRESS)
        if collections_dirs is not SUPPRESS:
            paths_collections = collections_dirs.split(":")
        else:
            # Create a test catalog
            test_path1 = "/home/jez/volumes/data/prj/mrjk/bench_paasify/python-paasify__work__v4/pocs/v4_collections/SOURCE_v1"
            test_path2 = "/home/jez/volumes/data/prj/mrjk/bench_paasify/python-paasify__work__v4/pocs/v4_collections/SOURCE_v2"
            # test_path3 = "/home/jez/volumes/data/prj/mrjk/bench_paasify/python-paasify__work__v4/pocs/v4_collections/SOURCE_v3"
            paths_collections = [
                test_path2,
                test_path1,
                # test_path3,
            ]

        # Register data
        ctx.data["dir_cwd"] = working_dir
        ctx.data["dir_mode"] = dir_mode
        ctx.data["paths_collections"] = paths_collections

# stacks:
#   - list
#   - show
# application:
#   - list
#   - show
# collection:
#   - list
#   - show
#   - apps


def run():
    "Return a Paasify App instance"

    _ = AppMain()


if __name__ == "__main__":
    run()
