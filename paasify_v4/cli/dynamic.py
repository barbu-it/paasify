import os
import logging
from pprint import pprint

from clak import Parser, Argument, Command
from clak.views import ListView, ShowView


from paasify_v4.models.core_namespace import PaasifyNamespace
from paasify_v4.models.core_stack import PaasifyStack, PaasifyPod
import paasify_v4.exception as exc

logger = logging.getLogger("paasify_v4.cli.dyn")

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

        # pprint(ctx.args.__dict__)

        item = ctx.data["runner"].get_current()
        logger.info("Working on: %s", item)
        if not item:
            raise exc.PaasifyWorkdirNotFoundError(
                f"Can't find any PaasifyStack or PaasifyNamespace in path: {os.getcwd()}"
            )

        if not isinstance(item, (PaasifyPod)):
            raise NotImplementedError(
                f"Command for {self.name} is not implemented yet for tother things that Pods"
            )

        out = item.assemble()

        return out


class DynVarsCmd(Parser):
    "Show vars"
    app_names = Argument("APP", help="App name", nargs="*")

    def cli_run(self, ctx=None, app_names=None, **_):
        "Main command"

        item = ctx.data["runner"].get_current()

        logger.info("Working on: %s", item)
        if not item:
            # if not isinstance(item, (PaasifyStack, PaasifyNamespace, PaasifyPod)):
            raise exc.PaasifyWorkdirNotFoundError(
                f"Can't find any PaasifyStack or PaasifyNamespace in path: {os.getcwd()}"
            )

        out = item.get_varmgr().get_values()
        ListView(out).render()


class DynListCmd(Parser):
    "List stack apps"

    def cli_run(self, ctx=None, **_):
        "Main command"

        item = ctx.data["runner"].get_current()
        logger.info("Working on: %s", item)
        # if not isinstance(item, (PaasifyStack, PaasifyNamespace)):
        if not item:
            raise exc.PaasifyWorkdirNotFoundError(
                f"Can't find any PaasifyStack or PaasifyNamespace in path: {os.getcwd()}"
            )

        render = []
        # TODO: Fix columns in clak
        columns = ["Name", "Value"]
        print(item)
        for child in item:
            render.append({"Path": ~child.path, "Ident": child.ident, "Object": child})
            # if isinstance(child, PaasifyStack):
            #     render.append([~child.path, child.ident, child])
            # else:
            #     render.append([child.ident, child])
        return ListView(render, columns=columns)


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
