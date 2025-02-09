"Main app command line interface"

import os

# import sys
import logging
from pprint import pprint

from argparse import SUPPRESS
from clak import Parser, Argument, Command, LoggingOptMixin
from clak.views import ListView, ShowView
from superconf.anchors import PathAnchor

from paasify_v4.catalog import PaasifyCatalog
from paasify_v4.common import truncate


logger = logging.getLogger(__name__)
# Never grab root, this break loggingMixin
# logger_root = logging.getLogger()


# App management
# ================================================


class AppListCmd(Parser):
    "List apps"

    def cli_run(self, ctx=None, **_):
        "Main command"

        catalog_mgr = ctx.data["catalog_mgr"]
        logger.info("Get apps")

        apps = catalog_mgr.get_apps()

        assert apps, f"No apps found: {apps}"

        # pprint(out)
        out = []
        for app in apps:
            # print(f"  {app.ident}: {app.get_path()}")
            out.append(
                {
                    "ident": app.ident,
                    "description": truncate(app.get_description()),
                    "name": app.name,
                    # "ident": app.name,
                    # "path": app.get_path(),
                    "collection": app.parent.name,
                    # "collection_path": app.collection_path,
                }
            )

        return ListView(out)


class AppShowCmd(Parser):
    "Show app"

    name = Argument("NAME", help="App name")

    def cli_run(self, ctx=None, name=None, **_):
        "Main command"
        catalog_mgr = ctx.data["catalog_mgr"]

        logger.info("Show app: %s", name)
        app = catalog_mgr.get_app(name)
        # print("===========")
        app = catalog_mgr.get_app(name)
        assert app, f"App {name} not found"
        # app = catalog_mgr[name]
        # assert app, f"App {name} not found"

        # tmp = f"UNSET: {type(app)}"
        # if app:
        #     tmp = "YEAHHH"
        # assert app, f"App {name} not found: {app} {tmp}"

        # print("===========")

        app_vars = app.get_vars()
        extra = {
            # "Infos": "",
            "ident": app.ident,
            "name": app.name,
            "source": app.parent.name,
            "index": app.index,
            # "apps_count": len(app.get_apps()),
            "path": app.get_path(),
            # "Vars:": "",
        }
        ShowView(extra).render()
        logger.info("Show app metadata: %s", name)
        # extra.update(app_vars)
        return ShowView(app_vars)


class AppGroup(Parser):
    "Manage collections"

    list = Command(AppListCmd)
    show = Command(AppShowCmd)

    def cli_group(self, ctx, **_):

        collections_paths = ctx.data["paths_collections"]
        mgr = PaasifyCatalog(collections_paths=collections_paths)
        ctx.data["catalog_mgr"] = mgr


# Collection management
# ================================================


class CollectionShowCmd(Parser):
    "Show collection"

    name = Argument("NAME", help="Collection name")

    def cli_run(self, ctx=None, name=None, **_):
        "Main command"
        catalog_mgr = ctx.data["catalog_mgr"]
        collection = catalog_mgr.get_collections(name)
        assert collection, f"Collection {name} not found"
        logger.info("Show collection %s", name)

        is_clean = collection.is_git_clean_worktree()
        extra = {
            "ident": collection.ident,
            "source": collection.parent,
            "index": collection.index,
            "apps_count": len(collection.get_apps()),
            "path": collection.get_path(),
            # "reference": f"{collection.get_git_remote()}#{collection.get_git_branch()}",
            "remote": collection.get_git_remote(),
            "branch": collection.get_git_branch(),
            "clean": is_clean,
            # "status": collection.get_git_status(),
        }
        if not is_clean:
            extra["status"] = collection.get_git_status()
            # extra["status"] = ellipsize(collection.get_git_status(), 100)
            # extra["status"] = truncate(collection.get_git_status())
        
        # pprint(extra)
        return ShowView(extra)


class CollectionListCmd(Parser):
    "List collections"

    def cli_run(self, ctx=None, **_):
        "Main command"
        catalog_mgr = ctx.data["catalog_mgr"]

        collections_paths = catalog_mgr.get_collections_paths()
        print = lambda x: x

        out = []
        print("Get Catalog")
        for collections_path in collections_paths:
            print(f"  Get Collection path: {collections_path.ident}")
            collections = collections_path.get_collections()
            for collection in collections:
                apps = collection.get_apps()
                print(f"    Get Collection: {collection.ident} ({len(apps)} apps)")

                out.append(
                    {
                        "collection": collection.ident,
                        "apps": len(apps),
                        "source": collections_path.ident,
                        "collection_path": collection.sub_path,
                    }
                )

        return ListView(out)


class CollectionInfoCmd(Parser):
    "Show collection info"

    def cli_run(self, ctx=None, **_):
        "Main command"
        catalog_mgr = ctx.data["catalog_mgr"]

        cwd = ctx.data["dir_cwd"]
        print(" * Working dir:")
        print(f"    get_path: {cwd.get_path()}")
        print(f"    get_dir : {cwd.get_dir()}")
        print(f"    get_dir (abs): {cwd.get_dir(mode='abs')}")
        print(f"    get_dir (rel): {cwd.get_dir(mode='rel')}")
        print(" * Collections paths:")

        for col_path in catalog_mgr.get_collections_paths():
            print(f"    {col_path.index}: {col_path.ident}: {col_path.get_path()}")


################# BETA


class CollectionDevelCmd(Parser):
    "Debug collections"

    def cli_run(self, ctx=None, **_):
        "Main command"

        catalog_mgr = ctx.data["catalog_mgr"]

        collections_paths = catalog_mgr.get_collections_paths()
        # print("Get Catalog")
        # for collections_path in collections_paths:
        #     print(f"  Get Collection path: {collections_path.ident}")
        #     collections = collections_path.get_collections()
        #     for collection in collections:
        #         apps = collection.get_apps()
        #         print(f"    Get Collection: {collection.ident} ({len(apps)} apps)")
        #         for app in apps:
        #             print(f"      Get App: {app.ident}")

        # print("Test2")
        collections_paths = catalog_mgr.get_collections_paths()
        print("Get Catalog")
        for collections_path in collections_paths:
            for collection in collections_path:
                print(f"  {collection.ident}")
                # for app in collection:
                #     print(f"    {app.ident}")

        print("Test3")
        for app in catalog_mgr.get_apps():
            print(f"  {app.ident}: {app.get_path()}")

        return


class CollectionGroup(Parser):
    "Manage collections"

    info = Command(CollectionInfoCmd)
    list = Command(CollectionListCmd)
    show = Command(CollectionShowCmd)
    # devel = Command(CollectionDevelCmd)

    def cli_group(self, ctx, force=None, debug=False, **_):

        collections_paths = ctx.data["paths_collections"]
        mgr = PaasifyCatalog(collections_paths=collections_paths)
        ctx.data["catalog_mgr"] = mgr


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


class AppMain(LoggingOptMixin, Parser):
    """Demo application with options and two subcommands."""

    class Meta:
        "Main app config"
        log_prefix = f"{__name__.split('.', maxsplit=1)[0]}"

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
    app = Command(AppGroup, help="==SUPPRESS==")
    collection = Command(CollectionGroup, help="==SUPPRESS==")

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
