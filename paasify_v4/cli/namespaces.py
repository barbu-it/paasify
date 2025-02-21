"Manage namespaces commands"

import logging

from clak import Argument, Command, Parser
from clak.views import ShowView

logger = logging.getLogger(__name__)


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

    info = Command(NamespaceInfoCmd, aliases=["i"])
    # list = Command(NamespaceListCmd)
    # show = Command(NamespaceShowCmd)
    # devel = Command(CollectionDevelCmd)
