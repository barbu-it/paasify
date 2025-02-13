"Manage stacks"

# import os
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
from paasify_v4.core_catalog import PaasifyCatalog
from paasify_v4.core_namespace import PaasifyNamespace
import paasify_v4.exception as exc


logger = logging.getLogger(__name__)


# Pod classes
# ================================================


class PaasifyPod(VarMgrNodeMixin, AppNode):
    "Base class for all Paasify pods"

    def __init__(self, ident, parent=None, raw_config=None, path=None):
        assert isinstance(parent, PaasifyStack)
        super().__init__(ident, parent)

        self._path = PathAnchor(path)
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


# Stacks classes
# ================================================


class PaasifyStack(WorkingDirNode):
    "Base class for all Paasify stacks"

    OBJECT_NAME = "Stack"
    ALLOWED_CONF_FILES = [
        "paasify.yml",
        "paasify.yaml",
        "paasify.stack.yml",
        "paasify.stack.yaml",
    ]

    node__iterate_backend = "_store_pods"
    node__iterate_setupmarker = "setup_node"

    def __init__(
        self,
        ident=None,
        parent=None,
        path=None,
        search_up=None,
        namespace=None,
        catalog=None,
    ):
        super().__init__(ident=ident, parent=parent, path=path, search_up=search_up)

        self.config = self.config or {}

        # Register namespace if provided
        if namespace:
            assert isinstance(namespace, PaasifyNamespace)
        self.ns = namespace

        # Register catalog if provided
        if catalog:
            assert isinstance(catalog, PaasifyCatalog)
        self.catalog = catalog

        self.setup_node()

    # Pod mangement
    # --------------------------------

    @setup_once("setup_node")
    def setup_node(self):
        "Setup the stack and it's apps"
        logger.info("Setup stack: %s", self)

        config = self.config or {}

        apps_config = config.get("apps", {}) or {}
        assert isinstance(apps_config, dict)
        out = {}
        for pod_ident, pod_config in apps_config.items():
            pod = PaasifyPod(
                ident=pod_ident,
                parent=self,
                path=pod_ident,
                raw_config=pod_config,
            )
            out[pod_ident] = pod

        self._store_pods = out

    @requires_setup_node("setup_node")
    def get_pods(self):
        "Get all deployments for the stack"
        return list(self._store_pods.values())

    @requires_setup_node("setup_node")
    def get_vars(self):
        "Get vars"
        return self.config.get("vars", {})

    @requires_setup_node("setup_node")
    def get_varmgr(self):
        "Get varmgr"
        varmgr = super().get_varmgr()

        ret = {
            "ns_vars": self.ns.get_vars() if self.ns else {},
            "stack_vars": self.get_vars(),
            # "pod_vars": self.config.get("vars", {}),
        }

        varmgr.set_layer("ns_vars", ret["ns_vars"])
        varmgr.set_layer("stack_vars", ret["stack_vars"])
        # varmgr.set_layer("pod_vars", ret["pod_vars"])

        return varmgr
