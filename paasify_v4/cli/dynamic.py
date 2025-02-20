import os
import sh
import logging
from pprint import pprint

from clak import Parser, Argument, Command
from clak.views import ListView, ShowView


from paasify_v4.models.core_namespace import PaasifyNamespace
from paasify_v4.models.core_stack import PaasifyStack, PaasifyPod
import paasify_v4.exception as exc
from paasify_v4.lib.shexec import shexec

logger = logging.getLogger("paasify_v4.cli.dyn")

# Dynamic commands
# ================================================


class DynPlaceholderCmd(Parser):
    "Not implemented yet"

    def cli_run(self, ctx=None, **_):
        "Main command"

        print("DynPlaceholderCmd")
        raise NotImplementedError(f"Command for {self.name} is not implemented yet")


class DynBuildCmd(Parser):
    "Build pods"

    app_names = Argument("APP", help="App name", nargs="*")

    def cli_run(self, ctx=None, app_names=None, **_):
        "Main command"

        # Algorithm with ABC class is: V1
        # if app_names is None: - Direct mode
        #   - If pod, just pod.build()
        #   - Get the list of current pod context.
        #     - For ns and stack, get_pods()
        # else app_names is not none: - Arg mode
        #   - If pod, use closest stack
        #   - Get the list of current stack/ns context.
        #     - For ns and stack, .get_pods() and check all app_names exists, or raise error
        #     - For ns and stack, .get_pods()
        #        - For each pod, check if name match, and build it pod.build()

        # Algorithm with ABC class is: V2 ---- THIS ONE
        # if app_names is None: - Direct mode
        #   - If pod, just pod.pod_build()
        #   - Get the list of current pod context.
        #     - For ns or stack, .pod_build()
        # else app_names is not none: - Arg mode
        #   - If pod, use closest pod.stack   # pod.pod_build(selector=NOARGS) or raise error
        #   - Get the list of pods in current stack/ns context:
        #     - stack.pod_build(selector=app_names)

        # So write me an ABC Mixin class with methods:
        # - pod_build(self, selector=None)
        # - get_closest_parent

        # V2
        # item = item.get_closest_parent()
        # item.pod_build(selector=app_names)

        # V3
        # print("APP NAMES", app_names)

        item = ctx.data["runner"].get_current()
        logger.debug(
            "For %s.pod_build(), build pods: %s",
            item,
            ", ".join(app_names or ["All or One"]),
        )

        if app_names:
            ctl = item.get_closest_parent()
            logger.info(
                "Use %s to build selection of pods: %s", ctl, ", ".join(app_names)
            )
            # print("Use ctl", ctl)
            ctl.pod_build(selector=app_names)
        else:
            if item.kind == "pod":
                logger.info("Use %s to build itself", item)
            else:
                logger.info("Use %s to build all children pods", item)
            item.pod_build()


class DynUpCmd(Parser):
    "Up pods"

    app_names = Argument("APP", help="App name", nargs="*")

    def cli_run(self, ctx=None, app_names=None, **_):
        "Main command"

        # pprint(ctx.args.__dict__)

        item = ctx.data["runner"].get_current()
        logger.debug("Working on: %s", item)
        out = item.assemble()
        return out


class DynEditCmd(Parser):
    "Edit config file"

    def cli_run(self, ctx=None, **_):
        "Main command"

        item = ctx.data["runner"].get_current()
        logger.debug("Working on: %s", item)
        # if not isinstance(item, (PaasifyStack, PaasifyNamespace)):
        if isinstance(item, PaasifyPod):
            item = item.stack

        # Start editor with config file
        config_path = ~item.config_path
        cmd_name = os.environ.get("EDITOR", "vim")
        cmd = sh.Command(cmd_name)
        cmd(config_path, _fg=True)

        return config_path


class DynVarsCmd(Parser):
    "Show vars"
    app_names = Argument("APP", help="App name", nargs="*")
    all = Argument("--all", "-a", help="Show all vars", action="store_true")

    def cli_run(self, ctx=None, app_names=None, all=False, **_):
        "Main command"

        item = ctx.data["runner"].get_current()

        logger.debug("Working on: %s", item)
        # out = item.get_varmgr().get_values()
        if all:
            out = item.get_varmgr().get_values()
        else:
            out = item.get_vars()

        ListView(out).render()


class DynListCmd(Parser):
    "List pods"

    def cli_run(self, ctx=None, **_):
        "Main command"

        item = ctx.data["runner"].get_current()
        item = item.get_closest_parent()
        logger.debug("Working on: %s", item)

        render = []
        # TODO: Fix columns in clak
        columns = ["Name", "Value"]
        # print(item)
        for child in item.get_pods():
            # print(type(child), child)
            render.append(
                {
                    # "Path": ~child.path,
                    "Path": ~child.path,
                    # "Ident": child.ident,
                    "Object": child,
                }
            )
            # if isinstance(child, PaasifyStack):
            #     render.append([~child.path, child.ident, child])
            # else:
            #     render.append([child.ident, child])
        return ListView(render, columns=columns)


class DynInfoCmd(Parser):
    "Show info"

    def cli_run(self, ctx=None, **_):
        "Main command"

        item = ctx.data["runner"].get_current()
        logger.debug("Working on: %s", item)
        out = item.get_infos()
        ShowView(out).render()


# class DynListCmd(Parser):
#     "List stack apps"

#     def cli_run(self, ctx=None, **_):
#         "Main command"


#         item = ctx.data["runner"].get_current()
#         logger.debug("For %s.pod_build(), build pods: %s", item, ', '.join(app_names or ["All or One"]))


#             if item.kind == "pod":
#                 logger.info("Use %s to build itself", item)
#             else:
#                 logger.info("Use %s to build all children pods", item)
#             item.get_pods()


# Dynamic Mixin
# ================================================


class DynMixin(Parser):
    "Dynamic commands"

    # Dynamic commands
    build = Command(DynBuildCmd, aliases=["b"])
    up = Command(DynUpCmd)
    list = Command(DynListCmd, aliases=["ls", "l"])
    edit = Command(DynEditCmd, aliases=["e"])

    vars = Command(DynVarsCmd, aliases=["v"])
    info = Command(DynInfoCmd, aliases=["i"])
    # info = Command(DynPlaceholderCmd)
    # build = Command(DynPlaceholderCmd)
    # down = Command(DynPlaceholderCmd)
