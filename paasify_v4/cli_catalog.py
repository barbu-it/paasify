"Paasify catalog CLI commands"


import logging
from pprint import pprint

from clak import Parser, Argument, Command
from clak.views import ListView, ShowView

from paasify_v4.common import truncate, to_yaml
from paasify_v4.catalog import PaasifyCatalog


logger = logging.getLogger(__name__)


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

        print("===========")
        tag_config = app.get_tags()
        tags = list(tag_config.keys())
        pprint(tag_config)

        app_vars = app.get_vars()
        app_vars = {f"var: {k}": v for k, v in app_vars.items()}
        extra = {
            # "Infos": "",
            "ident": app.ident,
            "name": app.name,
            "source": app.parent.name,
            "index": app.index,
            # "apps_count": len(app.get_apps()),
            "path": app.get_path(),
            "tags": " ".join(tags),
            "": "",
        }
        # ShowView(extra).render()
        # logger.info("Show app metadata: %s", name)
        extra.update(app_vars)
        return ShowView(extra)


class AppTagsCmd(Parser):
    "Show app tags"

    name = Argument("NAME", help="App name")

    def cli_run(self, ctx=None, name=None, **_):
        "Main command"
        catalog_mgr = ctx.data["catalog_mgr"]
        app = catalog_mgr.get_app(name)
        assert app, f"App {name} not found"

        tags = app.get_tags()
        pprint(tags)
        out = []
        for tag_name, tag in tags.items():
            # line = f"{tag_name}: {tag['path']}"
            line = {
                "tag": tag_name,
                # "path": tag["path"],
                # "metadata2": tag["metadata"],
                "metadata": to_yaml(tag["metadata"], strip_last=True),
                "rules": to_yaml(tag["rules"], strip_last=True),
            }
            out.append(line)
        return ListView(out)


class AppGroup(Parser):
    "Manage collections"

    list = Command(AppListCmd)
    show = Command(AppShowCmd)
    tags = Command(AppTagsCmd)

    # def cli_group(self, ctx, **_):

    #     collections_paths = ctx.data["paths_collections"]
    #     mgr = PaasifyCatalog(collections_paths=collections_paths)
    #     ctx.data["catalog_mgr"] = mgr


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
                        "remote": collection.get_git_remote(),
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


# class CollectionDevelCmd(Parser):
#     "Debug collections"

#     def cli_run(self, ctx=None, **_):
#         "Main command"

#         catalog_mgr = ctx.data["catalog_mgr"]

#         collections_paths = catalog_mgr.get_collections_paths()
#         # print("Get Catalog")
#         # for collections_path in collections_paths:
#         #     print(f"  Get Collection path: {collections_path.ident}")
#         #     collections = collections_path.get_collections()
#         #     for collection in collections:
#         #         apps = collection.get_apps()
#         #         print(f"    Get Collection: {collection.ident} ({len(apps)} apps)")
#         #         for app in apps:
#         #             print(f"      Get App: {app.ident}")

#         # print("Test2")
#         collections_paths = catalog_mgr.get_collections_paths()
#         print("Get Catalog")
#         for collections_path in collections_paths:
#             for collection in collections_path:
#                 print(f"  {collection.ident}")
#                 # for app in collection:
#                 #     print(f"    {app.ident}")

#         print("Test3")
#         for app in catalog_mgr.get_apps():
#             print(f"  {app.ident}: {app.get_path()}")

#         return


class CollectionGroup(Parser):
    "Manage collections"

    info = Command(CollectionInfoCmd)
    list = Command(CollectionListCmd)
    show = Command(CollectionShowCmd)
    # devel = Command(CollectionDevelCmd)
    app = Command(AppGroup)

    def cli_group(self, ctx, force=None, debug=False, **_):

        collections_paths = ctx.data["paths_collections"]
        mgr = PaasifyCatalog(collections_paths=collections_paths)
        ctx.data["catalog_mgr"] = mgr


