from pprint import pprint
import logging

from paasify_v4.core import AppNode, WorkingDirNode, setup_once, requires_setup_node
import paasify_v4.exception as exc

logger = logging.getLogger(__name__)


class PaasifyNoNamespace(AppNode):
    "No namespace class, just implement dumb methods"

    OBJECT_NAME = "EmptyNamespace"
    ALLOWED_CONF_FILES = ["paasify.ns.yml"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class PaasifyNamespace(WorkingDirNode):
    "Namespace class, manage list of stacks"

    # node__iterate_backend = "_children"
    # node__iterate_setupmarker = "setup_node"

    OBJECT_NAME = "Namespace"
    ALLOWED_CONF_FILES = [
        "paasify.ns.yml",
        "paasify.ns.yaml",
        "paasify.namespace.yml",
        "paasify.namespace.yaml",
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.setup_node()

    @setup_once("setup_node")
    def setup_node(self):
        "Setup the pod"
        logger.info("Setup namespace: %s", self)

        # Default ns config
        out = {
            "namespace": None,
            "config": {},
            "collections": {},
            "vars": self.config.get("vars", {}),
            "stacks": [],
        }
        self.config = out

    @requires_setup_node("setup_node")
    def get_vars(self):
        "Get vars"
        return self.config.get("vars", {})

    def get_varmgr(self):
        "Get varmgr"
        varmgr = super().get_varmgr()

        ret = {
            "ns_vars": self.get_vars(),
            # "stack_vars": self.stack.get_vars(),
            # "pod_vars": self.config.get("vars", {}),
        }

        varmgr.set_layer("ns_vars", ret["ns_vars"])
        # varmgr.set_layer("stack_vars", ret["stack_vars"])
        # varmgr.set_layer("pod_vars", ret["pod_vars"])

        return varmgr
