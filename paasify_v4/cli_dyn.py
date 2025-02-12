import os
import logging
from pprint import pprint

from clak import Parser, Argument, Command
from clak.views import ListView, ShowView

from paasify_v4.common import (
    read_file,
    from_yaml,
    find_file_up,
    list_parent_dirs,
    to_json,
    to_yaml,
)
from paasify_v4.core_catalog import PaasifyCatalog

from paasify_v4.core_namespace import PaasifyNamespace
from paasify_v4.core_stack import PaasifyStack, PaasifyPod, find_closest_workdir
import paasify_v4.exception as exc

# logger = logging.getLogger(__name__)
logger = logging.getLogger("paasify_v4.cli.dyn")


# # Pod management
# # ================================================
# class PodInfoCmd(Parser):
#     "Show pod info"

#     def cli_run(self, ctx=None, **_):
#         "Main command"

#         print("PodInfoCmd")

#         # stack = ctx.data["stack"]
#         # ns = ctx.data["namespace"]
#         # catalog = ctx.data["catalog"]


# class PodPlaceholderCmd(Parser):
#     "Show pod placeholder"

#     def cli_run(self, ctx=None, **_):
#         "Main command"

#         print("PodPlaceholderCmd")

#         raise NotImplementedError(f"Command for {self.name} is not implemented yet")


# class PodGroup(Parser):
#     "Manage pods"

#     info = Command(PodInfoCmd)
#     # list = Command(StackListCmd)
#     # show = Command(StackShowCmd)
#     # devel = Command(CollectionDevelCmd)
#     up = Command(PodPlaceholderCmd)
#     down = Command(PodPlaceholderCmd)
#     # start = Command(PodPlaceholderCmd)
#     # stop = Command(PodPlaceholderCmd)
#     # restart = Command(PodPlaceholderCmd)
#     # status = Command(PodPlaceholderCmd)
#     # logs = Command(PodPlaceholderCmd)
#     # exec = Command(PodPlaceholderCmd)

#     def cli_group(self, ctx, force=None, debug=False, **_):

#         collections_paths = ctx.data["paths_collections"]
#         catalog = PaasifyCatalog(collections_paths=collections_paths)
#         ctx.data["catalog"] = catalog

#         # ns = PaasifyNamespace(ident="cli_init", path=os.getcwd(), search_up=True)
#         # ctx.data["namespace"] = ns

#         # stack = PaasifyStack(ident="cli_init", path=os.getcwd(), search_up=True)
#         # ctx.data["stack"] = stack

#         stack = find_closest_workdir(path=os.getcwd(), kind=[PaasifyStack])
#         if stack:
#             ctx.data["stack"] = stack


# # Stack management
# # ================================================
# class StackListAppsCmd(Parser):
#     "List stack apps"

#     def cli_run(self, ctx=None, **_):
#         "Main command"

#         # catalog = ctx.data["catalog"]
#         stack = ctx.data["stack"]

#         # pprint(stack.__dict__)

#         out = stack.get_deployments()
#         # render = []
#         # for item in out.items():
#         # pprint(out)
#         return ListView(out)


# class StackInfoCmd(Parser):
#     "Show stack info"

#     def cli_run(self, ctx=None, **_):
#         "Main command"

#         # catalog = ctx.data["catalog"]
#         stack = ctx.data["stack"]

#         pprint(stack.__dict__)

#         out = stack.get_deployments()
#         pprint(out)

#         # print(f"Stack: {stack.ident}")

#         # print(to_json(stack.config))

#         # print(to_json(ns.config))

#         # print(catalog)
#         # print(to_yaml(catalog.__dict__))
#         # help(catalog)

#         # cwd = ctx.data["dir_cwd"]
#         # print(" * Working dir:")
#         # print(f"    get_path: {cwd.get_path()}")
#         # print(f"    get_dir : {cwd.get_dir()}")
#         # print(f"    get_dir (abs): {cwd.get_dir(mode='abs')}")
#         # print(f"    get_dir (rel): {cwd.get_dir(mode='rel')}")
#         # print(" * Collections paths:")

#         # for col_path in catalog_mgr.get_collections_paths():
#         #     print(f"    {col_path.index}: {col_path.ident}: {col_path.get_path()}")


# class StackGroup(Parser):
#     "Manage stacks"

#     info = Command(StackInfoCmd)
#     list = Command(StackListAppsCmd)
#     # show = Command(StackShowCmd)
#     # devel = Command(CollectionDevelCmd)

#     def cli_group(self, ctx, force=None, debug=False, **_):

#         collections_paths = ctx.data["paths_collections"]
#         catalog = PaasifyCatalog(collections_paths=collections_paths)
#         ctx.data["catalog"] = catalog

#         stack = find_closest_workdir(path=os.getcwd(), kind=[PaasifyStack])
#         if stack:
#             ctx.data["stack"] = stack


# Dynamic commands
# ================================================


class DynPlaceholderCmd(Parser):
    "Not implemented yet"

    def cli_run(self, ctx=None, **_):
        "Main command"

        print("DynPlaceholderCmd")

        raise NotImplementedError(f"Command for {self.name} is not implemented yet")


class DynUpCmd(Parser):
    "Show dynamic up"

    app_names = Argument("APP", help="App name", nargs="*")

    def cli_run(self, ctx=None, app_names=None, **_):
        "Main command"

        print("DynUpCmd called")

        item = find_closest_workdir(path=os.getcwd())

        # Temp failsafe
        logger.info("Working on: %s", item)
        # if not isinstance(item, (PaasifyStack, PaasifyNamespace, PaasifyPod)):
        if not isinstance(item, (PaasifyStack)):
            raise exc.PaasifyWorkdirNotFoundError(
                f"Can't find any PaasifyStack or PaasifyNamespace in path: {os.getcwd()}"
            )

        stack = item

        for app in stack:
            # print (app.ident, app)

            if app_names and app.ident not in app_names:
                continue

            logger.info("Processing %s", app)

            # pprint(app.__dict__)
            app.process_vars()


class DynVarsCmd(Parser):
    "Show vars"
    app_names = Argument("APP", help="App name", nargs="*")

    def cli_run(self, ctx=None, app_names=None, **_):
        "Main command"

        item = find_closest_workdir(path=os.getcwd())

        # Temp failsafe
        logger.info("Working on: %s", item)
        # if not isinstance(item, (PaasifyStack, PaasifyNamespace, PaasifyPod)):
        if not isinstance(item, (PaasifyStack, PaasifyNamespace)):
            raise exc.PaasifyWorkdirNotFoundError(
                f"Can't find any PaasifyStack or PaasifyNamespace in path: {os.getcwd()}"
            )

        if isinstance(item, PaasifyStack):
            stack = item
            out = item.get_varmgr().get_values()

            ListView(out).render()

            # for app in stack:

            #     if app_names and app.ident not in app_names:
            #         continue

            #     app_vars = app.get_varmgr()

            #     # Render vars
            #     logger.info("Rendering vars for %s", app.ident)
            #     out = []
            #     for scope in ["scope_ns", "scope_stack", "scope_pod"]:
            #         out.append(
            #             {
            #                 "key": f"[{scope}]",
            #                 "value": "",
            #             }
            #         )
            #         for key, value in app_vars.get_values(scope=scope).items():
            #             # out.append([scope, key, value])
            #             out.append(
            #                 {
            #                     "key": key,
            #                     "value": value,
            #                 }
            #             )
            #         out.append(
            #             {
            #                 "key": "",
            #                 "value": "",
            #             }
            #         )

            #     ListView(out).render()

        if isinstance(item, PaasifyNamespace):
            print("Namespace vars")
            pprint(item.get_varmgr().get_values())


class DynListCmd(Parser):
    "List stack apps"

    def cli_run(self, ctx=None, **_):
        "Main command"

        # Temporary
        stack = find_closest_workdir(path=os.getcwd())
        logger.info("Working on: %s", stack)
        if not isinstance(stack, (PaasifyStack, PaasifyNamespace)):
            raise exc.PaasifyWorkdirNotFoundError(
                f"Can't find any PaasifyStack or PaasifyNamespace in path: {os.getcwd()}"
            )

        print("GOT STACK:", stack)

        render = []
        for app in stack:
            render.append([app.ident, app])
        return ListView(render)


# Dynamic Mixin
# ================================================


class DynMixin(Parser):
    "Dynamic commands"

    # Dynamic commands
    up = Command(DynUpCmd)
    ls = Command(DynListCmd)
    vars = Command(DynVarsCmd)
    # info = Command(DynPlaceholderCmd)
    # build = Command(DynPlaceholderCmd)
    # down = Command(DynPlaceholderCmd)

    def cli_group(self, ctx, force=None, debug=False, **_):
        "Never called when mixin inherited"

        print("DynMixin")
