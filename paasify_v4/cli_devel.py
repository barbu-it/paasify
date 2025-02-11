

import os
import logging
from pprint import pprint

from clak import Parser, Argument, Command
from clak.views import ListView, ShowView

from paasify_v4.common import read_file, from_yaml, find_file_up, list_parent_dirs, to_json, to_yaml
from paasify_v4.catalog import PaasifyCatalog

from paasify_v4.devel import PaasifyNamespace, PaasifyStack

logger = logging.getLogger(__name__)



# Stack management
# ================================================


class StackInfoCmd(Parser):
    "Show stack info"

    def cli_run(self, ctx=None, **_):
        "Main command"

        stack = ctx.data["stack"]
        ns = ctx.data["namespace"]
        catalog = ctx.data["catalog"]

        print(f"Stack: {stack.name}")


        print(to_json(stack.config))

        print(to_json(ns.config))

        print(catalog)
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
    # list = Command(StackListCmd)
    # show = Command(StackShowCmd)
    # devel = Command(CollectionDevelCmd)

    def cli_group(self, ctx, force=None, debug=False, **_):

        collections_paths = ctx.data["paths_collections"]
        catalog = PaasifyCatalog(collections_paths=collections_paths)
        ctx.data["catalog"] = catalog

        ns = PaasifyNamespace(ident="cli_init", search_up=os.getcwd())
        ctx.data["namespace"] = ns

        stack = PaasifyStack(ident="cli_init", search_up=os.getcwd())
        ctx.data["stack"] = stack


# Namespace management
# ================================================

class NamespaceInfoCmd(Parser):
    "Show namespace info"

    def cli_run(self, ctx=None, **_):
        "Main command"
        ns = ctx.data["namespace"]

        print(f"Namespace: {ns.name}")

        # cwd = ctx.data["dir_cwd"]
        # print(" * Working dir:")
        # print(f"    get_path: {cwd.get_path()}")
        # print(f"    get_dir : {cwd.get_dir()}")
        # print(f"    get_dir (abs): {cwd.get_dir(mode='abs')}")
        # print(f"    get_dir (rel): {cwd.get_dir(mode='rel')}")
        # print(" * Collections paths:")

        # for col_path in catalog_mgr.get_collections_paths():
        #     print(f"    {col_path.index}: {col_path.ident}: {col_path.get_path()}")





class NamespaceGroup(Parser):
    "Manage namespaces"

    info = Command(NamespaceInfoCmd)
    # list = Command(NamespaceListCmd)
    # show = Command(NamespaceShowCmd)
    # devel = Command(CollectionDevelCmd)

    def cli_group(self, ctx, force=None, debug=False, **_):

        # collections_paths = ctx.data["paths_collections"]
        # mgr = PaasifyCatalog(collections_paths=collections_paths)
        # ctx.data["catalog_mgr"] = mgr


        ns = PaasifyNamespace(ident="cli_init", search_up=os.getcwd())
        ctx.data["namespace"] = ns

        # namespace.setup_node()
