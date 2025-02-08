"Main app command line interface"

import os
import sys
from pprint import pprint

from pathlib import Path

# from clak import Parser, Argument, Command

from clak import Parser, Argument, Command
from clak.views import ListView, ShowView
from superconf.anchors import PathAnchor

from paasify_v4.devel import AppCatalog


# App management
# ================================================


class AppListCmd(Parser):
    "List apps"


class AppShowCmd(Parser):
    "Show app"


class AppGroup(Parser):
    "Manage collections"

    list = Command(AppListCmd)
    show = Command(AppShowCmd)

    def cli_run(self, force=None, debug=False, **_):
        print(f"Run Command 1: Hello force={force}")
        if debug:
            print("Debug mode enabled")


# Collection management
# ================================================


class CollectionAllAppsCmd(Parser):
    "Show all apps"

    def cli_run(self, ctx=None, **_):
        "Main command"
        catalog_mgr = ctx.data["catalog_mgr"]
        # data = catalog_mgr.get_app("paasify-collection-lscr/jellyfin")

        # GUBBB HERE
        data = [
            catalog_mgr.get_app("paasify-collection-lscr/jellyfin"),
            catalog_mgr.get_app("paasify-collection-infra/netbird"),
        ]

        pprint(data)
        # pprint(data.__dict__)
        # return

        # data = catalog_mgr.get_apps()

        # return

        out = {}
        # for app in data.values():
        for app in data:
            # render.append(app)
            # line = [app["app_path"]]
            # render[app["app_ident"]] = line

            out[app.ident] = {
                "ident": app,
                "test_coll": app.test_coll,
                "Catalog": app.catalog,
                "Collection path": app.collection_path,
                "Collection": str(app.collection),
                # "App": app.name,
                # # "path": app.path,
            }

            # break

        pprint(out)
        # return

        return ListView(out)
        pprint(out)
        # return ListView(out)

        # return ListView(out, headers=["ident", "collection", "path"])


class CollectionShowCmd(Parser):
    "Show collection"

    name = Argument("NAME", help="Collection name")

    def cli_run(self, ctx=None, name=None, **_):
        "Main command"
        catalog_mgr = ctx.data["catalog_mgr"]

        out = catalog_mgr.get_collection_by_name(name)

        pprint(out)

        # return ShowView(out)


class CollectionListCmd(Parser):
    "List collections"

    def cli_run(self, ctx=None, **_):
        "Main command"
        catalog_mgr = ctx.data["catalog_mgr"]

        catalog_mgr = ctx.data["catalog_mgr"]

        # pprint(catalog_mgr.__dict__)
        collections_paths = catalog_mgr.get_collections_paths()

        out = []
        print("Get Catalog")
        for collections_path in collections_paths:
            print(f"  Get Collection path: {collections_path.ident}")
            collections = collections_path.get_collections()
            for collection in collections:
                apps = collection.get_apps()
                print(f"    Get Collection: {collection.ident} ({len(apps)} apps)")
                # pprint(collection.__dict__)

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

        # pprint(catalog_mgr.collections_paths)
        # out = catalog_mgr.walk_collections_paths()

        # # out = list(out.values())
        # return ListView(out)

        # pprint(ctx.data)
        cwd = ctx.data["dir_cwd"]

        print("Working dir:")
        print(f"  get_path: {cwd.get_path()}")
        print(f"  get_dir : {cwd.get_dir()}")
        print(f"  get_dir (abs): {cwd.get_dir(mode='abs')}")
        print(f"  get_dir (rel): {cwd.get_dir(mode='rel')}")
        print("Collections paths:")
        for idx, path in enumerate(catalog_mgr.collections_paths):
            print(f"path: {idx} => {path}")


################# BETA


class CollectionDevelCmd(Parser):
    "Debug collections"

    def cli_run(self, ctx=None, **_):
        "Main command"

        catalog_mgr = ctx.data["catalog_mgr"]

        # pprint(catalog_mgr.__dict__)
        collections_paths = catalog_mgr.get_collections_paths()

        print("Get Catalog")
        for collections_path in collections_paths:
            print(f"  Get Collection path: {collections_path.ident}")
            collections = collections_path.get_collections()
            for collection in collections:
                apps = collection.get_apps()
                print(f"    Get Collection: {collection.ident} ({len(apps)} apps)")
                for app in apps:
                    print(f"      Get App: {app.ident}")

        return


class CollectionGroup(Parser):
    "Manage collections"

    info = Command(CollectionInfoCmd)
    list = Command(CollectionListCmd)
    # show = Command(CollectionShowCmd)
    # apps = Command(CollectionAllAppsCmd)
    devel = Command(CollectionDevelCmd)

    def cli_group(self, ctx, force=None, debug=False, **_):

        # print("\n> Group executed")

        # Create a test catalog
        test_path1 = "/home/jez/volumes/data/prj/mrjk/bench_paasify/python-paasify__work__v4/pocs/v4_collections/SOURCE_v1"
        test_path2 = "/home/jez/volumes/data/prj/mrjk/bench_paasify/python-paasify__work__v4/pocs/v4_collections/SOURCE_v2"
        test_path3 = "/home/jez/volumes/data/prj/mrjk/bench_paasify/python-paasify__work__v4/pocs/v4_collections/SOURCE_v3"
        collections_paths = [
            test_path1,
            test_path2,
            # test_path3,
        ]
        mgr = AppCatalog(collections_paths=collections_paths)
        ctx.data["catalog_mgr"] = mgr

        # print("\n> Command forward")


# Beta
# ================================================


class AppCommand2(Parser):
    "Command 2, with option and positional arguments"
    aliases = Argument("--alias", "-a", action="append", help="Alias")  # (5)!
    name = Argument("NAME", help="Name")

    def cli_run(self, name=None, aliases=None, force=False, config=None, **_):  # (6)!
        print(f"Run command 2 World on: {name} in '{config}' file (force_mode={force})")
        for alias in aliases or []:
            print(f"Map: {alias} -> {name}")


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

        # out = AppCatalog(collections_paths=collections_paths)

        # pprint(out)
        # pprint(out.__dict__)

        # print("======================")
        # o = out.walk_collections_paths()
        # pprint(o)

class DebugCmd(Parser):
    "Debug commands"

    def cli_run(self, ctx=None, **_):
        "Main command"
        print("Debug command executed")
        pprint(ctx.__dict__)



class DemoCmd(Parser):
    "Demo viewers"

    def cli_run(self, ctx=None, **_):
        "Main command"

        # Tests1 - ShowView
        data_item_dict1 = {
            "name": "World",
            "age": 42,
            "city": "Paris",
        }
        data_item_list1 = [
            "World",
            42,
            "Paris",
        ]

        view = ShowView(data_item_dict1)
        view.render()

        view = ShowView(data_item_list1)
        view.render()

        # Tests2 - DictView

        data_item_dict2 = {
            "name": "World2",
            "age": 43,
            "city": "Berlin",
        }
        data_items_dict_of_dicts = {
            "item1": data_item_dict1,
            "item2": data_item_dict2,
        }
        view = ListView(data_items_dict_of_dicts)
        view.render()

        # Tests3 - ListView
        data_items_list_of_dicts = [
            data_item_dict1,
            data_item_dict2,
        ]
        view = ListView(data_items_list_of_dicts)
        view.render()

        return


# Main application
# ================================================


class Hidden(Argument):
    "Hidden argument"
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.hidden = True


HIDDEN = Hidden()
from argparse import SUPPRESS


class AppMain(Parser):
    """Demo application with options and two subcommands."""

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
    app = Command(AppGroup)
    collection = Command(CollectionGroup)

    dev = Command(Devel)
    command2 = Command(AppCommand2)
    demo = Command(DemoCmd)

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
                test_path1,
                test_path2,
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

    app = AppMain()


if __name__ == "__main__":
    run()
