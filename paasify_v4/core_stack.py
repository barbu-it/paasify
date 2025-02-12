# import os
import logging
from pprint import pprint

# from typing import List, Dict
# from dataclasses import dataclass
# from types import SimpleNamespace
import os.path

# from superconf.anchors import PathAnchor

from paasify_v4.common import (
    read_file,
    from_yaml,
    find_file_up,
    list_parent_dirs,
    to_json,
)
from paasify_v4.core import (
    AppNode,
    VarMgrNodeMixin,
    WorkingDirNode,
    setup_once,
    requires_setup_node,
)
from paasify_v4.core_namespace import PaasifyNamespace
import paasify_v4.exception as exc

# from mrjk_components.varmgr.lib import RenderableStoreManager,

# from store import StoreManager, Source


from mrjk_components.varmgr.lib.store_base import (
    StoreManager,
    Source,
    UndefinedVarError,
)
from mrjk_components.varmgr.lib.store_template import RenderableStoreManager

# from paasify_v4.catalog import PaasifyCatalog

logger = logging.getLogger(__name__)


# Pod classes
# ================================================


class PaasifyPod(VarMgrNodeMixin, AppNode):
    "Base class for all Paasify pods"

    def __init__(self, ident, parent=None, raw_config=None):
        assert isinstance(parent, PaasifyStack)
        super().__init__(ident, parent)

        self.stack = parent
        self.ns = parent.ns

        # print("Pod init:", self)
        # self.raw_config = raw_config
        self.config = self.build_config(raw_config, ident=ident)

        self.setup_node()

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

        return out

    @setup_once("setup_node")
    def setup_node(self):
        "Setup the pod"
        logger.info("Setup pod: %s", self)
        # self.vars = self.config.get("vars", {}) or {}
        # self.tags = self.config.get("tags", []) or []

    @setup_once("setup_node")
    def get_vars(self):
        "Get vars"
        return self.config.get("vars", {})

    # High level methods
    # --------------------------------

    def get_varmgr(self):
        "Get varmgr"
        varmgr = super().get_varmgr()

        ret = {
            "ns_vars": self.ns.get_vars(),
            "stack_vars": self.stack.get_vars(),
            "pod_vars": self.config.get("vars", {}),
        }

        varmgr.set_layer("ns_vars", ret["ns_vars"])
        varmgr.set_layer("stack_vars", ret["stack_vars"])
        varmgr.set_layer("pod_vars", ret["pod_vars"])

        return varmgr

    # def get_varmgr(self):
    #     "Get varmgr"
    #     logger.info("Process vars: %s", self)

    #     # Goal:
    #     # - Show vars from the stack
    #     # - Show vars from the namespace
    #     # - Show vars from the pod
    #     ret = {
    #         "ns_vars": self.ns.get_vars(),
    #         "stack_vars": self.stack.get_vars(),
    #         "pod_vars": self.config.get("vars", {}),
    #     }

    #     # varmgr = StoreManager()
    #     varmgr = RenderableStoreManager()
    #     varmgr.add_sources(
    #         [
    #             Source("ns_vars", level=900, help="Namespace variables"),
    #             Source("stack_vars", level=700, help="Stack variables"),
    #             Source("pod_vars", level=500, help="Pod variables"),
    #         ]
    #     )
    #     varmgr.set_scopes(
    #         {
    #             "scope_ns": ["ns_vars"],
    #             "scope_stack": ["stack_vars", "ns_vars"],
    #             "scope_pod": ["pod_vars", "stack_vars", "ns_vars"],
    #         }
    #     )

    #     # Configure layers ...

    #     # Set layers
    #     varmgr.set_layer("ns_vars", ret["ns_vars"])
    #     varmgr.set_layer("stack_vars", ret["stack_vars"])
    #     varmgr.set_layer("pod_vars", ret["pod_vars"])

    #     return varmgr


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

    # def __init__(self, ident=None, parent=None, path=None,search_up=None):
    #     super().__init__(ident=ident, parent=parent)

    def __init__(
        self, ident=None, parent=None, path=None, search_up=None, namespace=None
    ):
        super().__init__(ident=ident, parent=parent, path=path, search_up=search_up)

        # Auto init namespace if not provided (when None, by default), unless
        # namespace is set to False
        self.ns = namespace
        if self.ns is None:
            logger.debug(
                "No namespace provided, searching for in parents of: %s", ~self._path
            )
            self.ns = self.find_namespace()
        if self.ns:
            assert isinstance(self.ns, PaasifyNamespace)

        self.setup_node()

    # Stack intialization
    # --------------------------------

    def find_namespace(self):
        "Find the closest namespace above the stack"

        ret = None
        try:
            path = self._path.get_path(mode="abs")
            match = find_closest_workdir(
                path=path, search_up=True, kind=[PaasifyNamespace]
            )
            if match:
                ret = match
        except exc.PaasifyWorkdirNotFoundError as err:
            logger.debug("No namespace found in %s: %s", path, err)

        return ret

    # Pod mangement
    # --------------------------------

    @setup_once("setup_node")
    def setup_node(self):
        "Setup the stack and it's apps"
        logger.info("Setup stack: %s", self)

        apps_config = self.config.get("apps", {}) or {}
        assert isinstance(apps_config, dict)
        out = {}
        for pod_ident, pod_config in apps_config.items():
            pod = PaasifyPod(
                ident=pod_ident,
                parent=self,
                raw_config=pod_config,
            )
            out[pod_ident] = pod

        self._store_pods = out

    @requires_setup_node("setup_node")
    def get_pods(self):
        "Get all deployments for the stack"
        return list(self._store_pods.values())
        # return self.config.get("apps", [])

    @requires_setup_node("setup_node")
    def get_vars(self):
        "Get vars"
        return self.config.get("vars", {})

    def get_varmgr(self):
        "Get varmgr"
        varmgr = super().get_varmgr()

        ret = {
            "ns_vars": self.ns.get_vars(),
            "stack_vars": self.get_vars(),
            # "pod_vars": self.config.get("vars", {}),
        }

        varmgr.set_layer("ns_vars", ret["ns_vars"])
        varmgr.set_layer("stack_vars", ret["stack_vars"])
        # varmgr.set_layer("pod_vars", ret["pod_vars"])

        return varmgr


# Context helper
# ================================================


def find_closest_workdir(path=None, search_up=True, kind=None):
    "Find the closest workdir"

    # Prepare args
    items = kind or [
        PaasifyStack,
        PaasifyNamespace,
    ]
    items = [items] if not isinstance(items, list) else items
    if not path:
        # path = list_parent_dirs(os.getcwd())
        path = os.getcwd()
    items_names = " or ".join([getattr(x, "__name__", str(x)) for x in items])

    # Loop over first match
    logger.debug("Searching for %s in path: %s", items_names, path)
    errors = []
    for item in items:
        print("Trying path:", path)
        assert isinstance(item, type), f"Item must be a type, not {type(item)}"
        try:
            out = item(path=path, search_up=search_up)
            logger.info("Found item: %s in %s", out, ~out.path)
            if item is PaasifyStack:
                print("GOT STACK:", out)
                pprint(out.__dict__)
                assert False, "WIP"
            return out
        except exc.PaasifyWorkdirNotFoundError as err:
            logger.debug("Can't find %s in path '%s': %s", item.__name__, path, err)
            errors.append(err)

    # msg = f"Can't find any {items_names} in path: {last_error}"
    errors = "\n  - ".join([str(x) for x in errors])
    search = "in parent directories" if search_up else "in paths"
    errors = f"Can't find any {items_names} {search}:\n  - {errors}"
    raise exc.PaasifyWorkdirNotFoundError(errors)
