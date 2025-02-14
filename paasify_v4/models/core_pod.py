"Manage apps/pods"

import logging
from pprint import pprint

from superconf.anchors2 import PathAnchor
from paasify_v4.core import (
    AppNode,
    VarMgrNodeMixin,
    WorkingDirNode,
    setup_once,
    requires_setup_node,
)
from paasify_v4.models.core_catalog import PaasifyCatalog
import paasify_v4.exception as exc


logger = logging.getLogger(__name__)


# Pod classes
# ================================================


class PaasifyPod(VarMgrNodeMixin, AppNode):
    "Base class for all Paasify pods"

    paasify_type = "pod"

    def __init__(self, ident, parent=None, name=None, raw_config=None, path=None):
        # assert isinstance(parent, PaasifyStack)
        super().__init__(ident, parent)

        self._name = name or ident.split("/", maxsplit=1)[0]

        self._path = PathAnchor(path, parent=parent.path)
        self.config = self.build_config(raw_config, ident=ident)

        self.setup_node()

    @property
    def ns(self):
        "Return namespace"
        return self.parent.ns

    @property
    def stack(self):
        "Return stack"
        return self.parent

    # Config build
    # --------------------------------

    def build_config(self, config, ident=None):
        "Build config"
        # if ident:
        #     config = config.get(ident, {})
        out = {
            "ident": ident,
            "directory": None,
            "app": None,
            "name": None,
            "vars": {},
            "tags": [],
        }

        # Check type
        if isinstance(config, str) and config:
            # If not empty string, on it's simplest form, we exect
            # to be the app name
            config = {"app": str(config)}
        elif isinstance(config, dict):
            pass
        elif not config:
            config = {}
        else:
            raise exc.PaasifyConfigError(f"Invalid config type: {type(config)}")

        out.update(config)
        if ident:
            out.update(
                {
                    "directory": ident,
                }
            )

        out["vars"] = out["vars"] or {}
        out["tags"] = out["tags"] or []

        return out

    @setup_once("setup_node")
    def setup_node(self):
        "Setup the pod"
        logger.info("Setup pod: %s", self)
        # self.vars = self.config.get("vars", {}) or {}
        # self.tags = self.config.get("tags", []) or []

    # @setup_once("setup_node")
    def get_vars(self):
        "Get vars"
        return self.config.get("vars", {}) or {}

    # High level methods
    # --------------------------------

    def get_varmgr(self):
        "Get varmgr"
        varmgr = super().get_varmgr()

        ret = {
            "ns_vars": self.ns.get_vars() if self.ns else {},
            "stack_vars": self.stack.get_vars(),
            "pod_vars": self.get_vars(),
        }

        varmgr.set_layer("ns_vars", ret["ns_vars"])
        varmgr.set_layer("stack_vars", ret["stack_vars"])
        varmgr.set_layer("pod_vars", ret["pod_vars"])

        return varmgr

    def assemble(self):
        "Assemble the pod"
        print("ASSEMBLE POD:", self)

        print("Get vars")
        varmgr = self.get_varmgr()
        print("Vars:")
        vars_dict = varmgr.get_values()
        pprint(vars_dict)

        print("Get App name")
        app_name = self.config.get("app")
        print("App name:", app_name)

        print("Get Tags")
        tags = self.config.get("tags", [])
        print("Tags:", tags)

        # Get the name from the Catalog App directory, and get the app object
        # instance from the Catalog

        assert False, "WIP pre-up, TODO: Resolve app from catalog"
