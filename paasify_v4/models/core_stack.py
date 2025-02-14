"Manage stacks"

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
from paasify_v4.models.core_pod import PaasifyPod
import paasify_v4.exception as exc


logger = logging.getLogger(__name__)


# Stacks classes
# ================================================


class PaasifyStack(WorkingDirNode):
    "Base class for all Paasify stacks"

    paasify_type = "stack"

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
            assert isinstance(namespace, AppNode)
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
