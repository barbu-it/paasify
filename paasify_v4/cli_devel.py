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
from paasify_v4.core_stack import PaasifyStack

logger = logging.getLogger(__name__)


# Pod management
# ================================================
class PodInfoCmd(Parser):
    "Show pod info"

    def cli_run(self, ctx=None, **_):
        "Main command"

        print("PodInfoCmd")

        # stack = ctx.data["stack"]
        # ns = ctx.data["namespace"]
        # catalog = ctx.data["catalog"]


class PodPlaceholderCmd(Parser):
    "Not implemented yet"

    def cli_run(self, ctx=None, **_):
        "Main command"

        print("PodPlaceholderCmd")

        raise NotImplementedError(f"Command for {self.name} is not implemented yet")


class PodGroup(Parser):
    "Manage pods"

    info = Command(PodInfoCmd)
    # list = Command(StackListCmd)
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

    def cli_group(self, ctx, force=None, debug=False, **_):

        collections_paths = ctx.data["paths_collections"]
        catalog = PaasifyCatalog(collections_paths=collections_paths)
        ctx.data["catalog"] = catalog

        # ns = PaasifyNamespace(ident="cli_init", path=os.getcwd(), search_up=True)
        # ctx.data["namespace"] = ns

        # stack = PaasifyStack(ident="cli_init", path=os.getcwd(), search_up=True)
        # ctx.data["stack"] = stack

        stack = find_closest_workdir(path=os.getcwd(), kind=[PaasifyStack])
        if stack:
            ctx.data["stack"] = stack


# Stack management
# ================================================
class StackListAppsCmd(Parser):
    "List stack apps"

    def cli_run(self, ctx=None, **_):
        "Main command"

        # catalog = ctx.data["catalog"]
        stack = ctx.data["stack"]

        # pprint(stack.__dict__)

        out = stack.get_deployments()
        # render = []
        # for item in out.items():
        # pprint(out)
        return ListView(out)


class StackInfoCmd(Parser):
    "Show stack info"

    def cli_run(self, ctx=None, **_):
        "Main command"

        # catalog = ctx.data["catalog"]
        stack = ctx.data["stack"]

        # pprint(stack.__dict__)

        out = stack.get_deployments()
        pprint(out)

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

    def cli_group(self, ctx, force=None, debug=False, **_):

        collections_paths = ctx.data["paths_collections"]
        catalog = PaasifyCatalog(collections_paths=collections_paths)
        ctx.data["catalog"] = catalog

        stack = find_closest_workdir(path=os.getcwd(), kind=[PaasifyStack])
        if stack:
            ctx.data["stack"] = stack


# Namespace management
# ================================================


class NamespaceInfoCmd(Parser):
    "Show namespace info"

    def cli_run(self, ctx=None, **_):
        "Main command"
        ns = ctx.data["namespace"]

        # print(f"Namespace: {ns.name}")
        # pprint(ns.__dict__)

        out = {
            "ident": ns.ident,
            "root_dir": ~ns._path,
            "config_file": ~ns.config_path,
            "config": ns.config["config"],
            "stacks": ns.config["stacks"],
            "collections": ns.config["collections"],
            "": "",
        }

        for key, val in ns.get_vars().items():
            out[f"var:{key}"] = val

        # out = dict(**ns.config)

        # pprint(out)
        return ShowView(out)


class NamespaceGroup(Parser):
    "Manage namespaces"

    info = Command(NamespaceInfoCmd)
    # list = Command(NamespaceListCmd)
    # show = Command(NamespaceShowCmd)
    # devel = Command(CollectionDevelCmd)

    def cli_group(self, ctx, force=None, debug=False, **_):

        ns = PaasifyNamespace(ident="cli_init", path=os.getcwd(), search_up=True)
        ctx.data["namespace"] = ns
