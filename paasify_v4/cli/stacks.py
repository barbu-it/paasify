"Manage stacks commands"

import logging

from clak import Argument, Command, Parser
from clak.views import ListView, ShowView

import paasify_v4.exception as exc
from paasify_v4.lib.shexec import shexec

logger = logging.getLogger(__name__)
from pprint import pprint

import sh

# Stack management
# ================================================


class StackTreeCmd(Parser):
    "Show stack tree"

    def cli_run(self, ctx=None, **_):
        "Main command"

        ns = ctx.data["runner"].namespace
        cmd = [
            "tree",
            "-L",
            "3",
            "-P",
            "paasify.yml",
            "--info",
            "--noreport",
            "--prune",
            ~ns.path,
        ]

        # out = shexec(cmd)
        try:
            out = shexec(cmd)
            print(out)
        except AttributeError as err:
            msg = f"Command not found: {err}"
            raise exc.PaasifyCliError(msg) from None
        except Exception as err:
            # pprint(type(err))
            # pprint(type(err).__mro__)
            # pprint(err.__dict__)
            msg = f"Command '{' '.join(cmd)}' returned an error: {err}"
            raise exc.PaasifyCliError(msg) from None


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

    info = Command(StackInfoCmd, aliases=["i"])
    ls = Command(StackListAppsCmd, aliases=["list", "l"])
    tree = Command(StackTreeCmd, aliases=["t"])
    # show = Command(StackShowCmd)
    # devel = Command(CollectionDevelCmd)

    # def cli_group(self, ctx, force=None, debug=False, **_):

    #     collections_paths = ctx.data["paths_collections"]
    #     catalog = PaasifyCatalog(collections_paths=collections_paths)
    #     ctx.data["catalog"] = catalog

    #     stack = find_closest_workdir(path=os.getcwd(), kind=[PaasifyStack])
    #     if stack:
    #         ctx.data["stack"] = stack
