"Manage stacks"

import logging
from pprint import pprint

# import paasify_v4.exception as exc
from paasify_v4.models.core_catalog import PaasifyCatalog
from paasify_v4.models.core_common import PaasifyStackV1Mixin
from paasify_v4.models.core_pod import PaasifyPod
from paasify_v4.nodes_paasify import AppNode, requires_setup_node, setup_once
from paasify_v4.common import to_yaml

# from superconf.anchors import PathAnchor

# from paasify_v4.specs.config_stack import PaasifyStackConfigFile, StackPods
# from paasify_v4.specs2.config_stack import PaasifyStackConfigFile # , StackPods


from paasify_v4.specs.config_stack import PaasifyStackConfigFile, StackPods


logger = logging.getLogger(__name__)


# Stacks classes
# ================================================


class PaasifyStack(PaasifyStackV1Mixin):
    "Base class for all Paasify stacks"

    paasify_type = "stack"

    OBJECT_NAME = "Stack"
    ALLOWED_CONF_FILES = [
        "paasify2.yml",
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
        # print("INIT STACK", ident, parent)
        assert (
            type(parent).__name__ == "PaasifyNamespace"
        ), f"Parent should be a PaasifyNamespace, not {type(parent).__name__}"

        # pprint(self.__dict__)

        self.raw_config = self.config or {}
        self.config = PaasifyStackConfigFile(
            value=self.config, key=f"stack_{self.name}"
        )

        # print("STACK CONFIG", self.config.fname)
        # assert False

        # pprint(self.raw_config)
        # obj  = PaasifyStackConfigFile()
        # obj.load(self.raw_config)

        # print(to_yaml(obj.dump(self.raw_config)))

        # pprint(obj)
        # pprint(obj.__dict__)

        # self.config = obj

        # assert False, "WIP MARSHMALLOW"

        # pprint(self.__dict__)
        # assert False, "WIP, self.config must be superconf.Configuration"

        # self.config = self.config or {}

        # Register namespace if provided
        namespace = namespace or parent
        assert isinstance(namespace, (AppNode, type(None)))
        self.ns = namespace

        # Register catalog if provided
        if catalog:
            assert isinstance(catalog, PaasifyCatalog)
        self.catalog = catalog

        self.setup_node()

    # @property
    # def fname(self):
    #     "Return full name"
    #     part_ns = self.ns.name or "MISSING"
    #     part_stack = self.name or "MISSING"
    #     final1 = "__".join([part_ns, part_stack])
    #     return final1

    def get_infos(self) -> dict:
        "Get infos"
        base = super().get_infos()

        logger.debug("Get stack infos for %s", self)

        sep = base.pop("--", "--") + "-"
        base[sep] = sep

        pods = self.get_pods()
        for pod in pods:
            pod_cfg = {
                "app": pod.app.name,
                "vars": pod.get_vars(),
                # "tags": pod.get_tags(),
            }
            base[f"pod:{pod.name}"] = to_yaml(pod_cfg)

        return base

    # Pod mangement
    # --------------------------------

    @setup_once("setup_node")
    def setup_node(self):
        "Setup the stack and it's apps"
        logger.info("Setup stack: %s", self)

        # config = self.config or {}

        # self.raw_config = config
        # self.config = PaasifyStackConfigFile(value=config)

        config = self.config
        # print("SETUP Stack node")
        # pprint(config)

        # apps_config = config.get("apps", {}) or {}
        apps_config2 = config.get("apps")
        apps_config = config.apps

        assert apps_config2 == apps_config, "apps_config2 != apps_config"
        # print(type(apps_config), apps_config.__class__.__mro__)
        # assert isinstance(apps_config, (dict, StackPods)), f"GoPaasifyPodt: {type(apps_config)}"
        assert isinstance(
            apps_config, StackPods
        ), f"Expected StackPods, got: {type(apps_config)}"

        # toto = apps_config.get_value()
        # pprint(toto)
        # # assert toto, f"WIP, got: {toto}"

        out = {}
        for pod_ident, pod_config in apps_config.items():
            # pprint(pod_config)
            # pprint(pod_config.__class__.__mro__)
            pod = PaasifyPod(
                ident=pod_ident,
                parent=self,
                path=pod_ident,
                config=pod_config,
                # raw_config=pod_config,
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

        logger.debug("Get varmgr from stack for %s", self)
        ret = {
            "ns_vars": self.ns.get_vars() if self.ns else {},
            "stack_vars": self.get_vars(),
            # "pod_vars": self.config.get("vars", {}),
        }

        varmgr.set_layer("ns_vars", ret["ns_vars"])
        varmgr.set_layer("stack_vars", ret["stack_vars"])
        # varmgr.set_layer("pod_vars", ret["pod_vars"])

        return varmgr
