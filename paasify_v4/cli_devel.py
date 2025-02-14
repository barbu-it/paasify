import os
import logging
from pprint import pprint

from clak import Parser, Argument, Command
from clak.views import ListView, ShowView

from paasify_v4.core_catalog import PaasifyCatalog
from paasify_v4.core_namespace import PaasifyNamespace
from paasify_v4.core_stack import PaasifyStack


logger = logging.getLogger("paasify_v4.cli.devel")


# Pod management
# ================================================
class PodInfoCmd(Parser):
    "Show pod info"

    name = Argument("NAME", help="App name", nargs="?")

    def cli_run(self, ctx=None, name=None, **_):
        "Main command"

        if not name:
            pod = ctx.data["runner"].pod
        else:
            pod = ctx.data["runner"].stack[name]

        out = {
            "ident": pod.ident,
            "name": pod.name,
            "path": ~pod.path,
            # "config": ~pod.config_path,
            # "namespace": pod.ns,
            # "catalog": pod.catalog,
            # "path_mode": pod.path_mode,
            "": "",
        }
        for key, val in pod.get_vars().items():
            out[f"var:{key}"] = val

        return ShowView(out)


class PodListCmd(Parser):
    "List stack apps"

    def cli_run(self, ctx=None, **_):
        "Main command"

        current = ctx.data["runner"].current
        viewer = current.kind
        out = []
        for pod in current.get_pods():
            part1 = {
                "ident": pod.ident,
                "name": pod.name,
                "path": pod.path.get_path(
                    start=~ctx.data["dir_cwd"],
                    # start=os.getcwd(),
                    # mode="rel",
                    mode=ctx.data["dir_mode"],
                ),
            }
            part2 = {}
            if viewer in ["namespace"]:
                part2 = {
                    "stack": pod.stack.ident,
                }

            out.append({**part1, **part2})

        return ListView(out)


class PodPlaceholderCmd(Parser):
    "Not implemented yet"

    def cli_run(self, ctx=None, **_):
        "Main command"

        print("PodPlaceholderCmd")

        raise NotImplementedError(f"Command for {self.name} is not implemented yet")


class PodGroup(Parser):
    "Manage pods"

    info = Command(PodInfoCmd)
    list = Command(PodListCmd)
    # show = Command(StackShowCmd)
    # devel = Command(CollectionDevelCmd)
    up = Command(PodPlaceholderCmd)
    down = Command(PodPlaceholderCmd)
    # start = Command(PodPlaceholderCmd)
    # stop = Command(PodPlaceholderCmd)
    # restart = Command(PodPlaceholderCmd)
    # status = Command(PodPlaceholderCmd)
    # logs = Command(PodPlaceholderCmd)
    # exec = Command(PodPlaceholderCmd)

    # def cli_group(self, ctx, force=None, debug=False, **_):

    #     collections_paths = ctx.data["paths_collections"]
    #     catalog = PaasifyCatalog(collections_paths=collections_paths)
    #     ctx.data["catalog"] = catalog

    #     stack = find_closest_workdir(path=os.getcwd(), kind=[PaasifyStack])
    #     if stack:
    #         ctx.data["stack"] = stack


# Stack management
# ================================================
class StackListAppsCmd(Parser):
    "List stack apps"

    def cli_run(self, ctx=None, **_):
        "Main command"

        namespace = ctx.data["runner"].namespace
        out = []
        for stack in namespace:
            print(stack)
            out.append(
                {
                    "ident": stack.ident,
                    "name": stack.name,
                    "path": ~stack.path,
                }
            )
        return ListView(out)


class StackInfoCmd(Parser):
    "Show stack info"

    name = Argument("NAME", help="App name", nargs="?")

    def cli_run(self, ctx=None, name=None, **_):
        "Main command"

        if not name:
            stack = ctx.data["runner"].stack
        else:
            stack = ctx.data["runner"].stack[name]

        # catalog = ctx.data["catalog"]

        # pprint(stack.__dict__)

        out = {
            "ident": stack.ident,
            "name": stack.name,
            "path": ~stack.path,
            "config": ~stack.config_path,
            "namespace": stack.ns,
            "catalog": stack.catalog,
            "path_mode": stack.path_mode,
            "sub_path": stack.sub_path,
            "": "",
        }

        for pod in stack:
            out[f"pod:{pod.ident}"] = pod.ident

        return ShowView(out)

        # out = stack.get_deployments()
        # pprint(out)

        # print(f"Stack: {stack.ident}")

        # print(to_json(stack.config))

        # print(to_json(ns.config))

        # print(catalog)
        # print(to_yaml(catalog.__dict__))
        # help(catalog)

        # cwd = ctx.data["dir_cwd"]
        # print(" * Working dir:")
        # print(f"    get_path: {cwd.get_path()}")
        # print(f"    get_dir : {cwd.get_dir()}")
        # print(f"    get_dir (abs): {cwd.get_dir(mode='abs')}")
        # print(f"    get_dir (rel): {cwd.get_dir(mode='rel')}")
        # print(" * Collections paths:")

        # for col_path in catalog_mgr.get_collections_paths():
        #     print(f"    {col_path.index}: {col_path.ident}: {col_path.get_path()}")


class StackGroup(Parser):
    "Manage stacks"

    info = Command(StackInfoCmd)
    list = Command(StackListAppsCmd)
    # show = Command(StackShowCmd)
    # devel = Command(CollectionDevelCmd)

    # def cli_group(self, ctx, force=None, debug=False, **_):

    #     collections_paths = ctx.data["paths_collections"]
    #     catalog = PaasifyCatalog(collections_paths=collections_paths)
    #     ctx.data["catalog"] = catalog

    #     stack = find_closest_workdir(path=os.getcwd(), kind=[PaasifyStack])
    #     if stack:
    #         ctx.data["stack"] = stack


# Namespace management
# ================================================


class NamespaceInfoCmd(Parser):
    "Show namespace info"

    def cli_run(self, ctx=None, **_):
        "Main command"
        ns = ctx.data["runner"].namespace
        out = {
            "ident": ns.ident,
            "root_dir": ~ns.path,
            "config_file": ~ns.config_path,
            "config": ns.config["config"],
            "stacks": ns.config["stacks"],
            "collections": ns.config["collections"],
            "": "",
        }

        for key, val in ns.get_vars().items():
            out[f"var:{key}"] = val
        return ShowView(out)


class NamespaceGroup(Parser):
    "Manage namespaces"

    info = Command(NamespaceInfoCmd)
    # list = Command(NamespaceListCmd)
    # show = Command(NamespaceShowCmd)
    # devel = Command(CollectionDevelCmd)
