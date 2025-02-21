"Manage pods commands"

import logging
from pprint import pprint

from clak import Argument, Command, Parser
from clak.views import ListView, ShowView

from paasify_v4.common import to_yaml
from paasify_v4.models.core_pod import PaasifyPod

logger = logging.getLogger(__name__)


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
            "app": None,
            # "config": ~pod.config_path,
            # "namespace": pod.ns,
            # "catalog": pod.catalog,
            # "path_mode": pod.path_mode,
            "": "",
        }
        if pod.app:
            app_vars = to_yaml(pod.app.get_vars())
            out["app"] = pod.app
            out["app_path"] = ~pod.app.path
            out["app_vars"] = app_vars
        for key, val in pod.get_vars().items():
            out[f"var:{key}"] = val

        return ShowView(out)


class PodListCmd(Parser):
    "List stack apps"

    def cli_run(self, ctx=None, **_):
        "Main command"

        current = ctx.data["runner"].get_current()
        viewer = current.kind
        out = []
        print(current)
        if isinstance(current, PaasifyPod):
            current = current.stack
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

    info = Command(PodInfoCmd, aliases=["i"])
    ls = Command(PodListCmd, aliases=["list", "l"])
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
