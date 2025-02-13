# import os
import logging
from pprint import pprint

# from typing import List, Dict
# from dataclasses import dataclass
# from types import SimpleNamespace
import os.path

# from superconf.anchors import PathAnchor

from superconf.anchors2 import PathAnchor


# from paasify_v4.common import (
#     read_file,
#     from_yaml,
#     find_file_up,
#     list_parent_dirs,
#     to_json,
# )
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

# from mrjk_components.varmgr.lib import RenderableStoreManager,

# from store import StoreManager, Source



# from mrjk_components.varmgr.lib.store_template import RenderableStoreManager

# from paasify_v4.catalog import PaasifyCatalog

logger = logging.getLogger(__name__)


# Pod classes
# ================================================


class PaasifyPod(VarMgrNodeMixin, AppNode):
    "Base class for all Paasify pods"

    def __init__(self, ident, parent=None, raw_config=None, path=None):
        assert isinstance(parent, PaasifyStack)
        super().__init__(ident, parent)

        # self.stack = parent
        # self.ns = parent.ns
        self._path = PathAnchor(path)

        # print("Pod init:", self)
        # self.raw_config = raw_config
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
        pprint(ret)
        pprint(self.ns)

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

    # def __init__(self, ident=None, parent=None, path=None,search_up=None):
    #     super().__init__(ident=ident, parent=parent)

    def __init__(
        self, ident=None, parent=None, path=None, search_up=None, 
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
        # if isinstance(self.catalog, str):
        #     paths = catalog.split(":")
        #     self.catalog = PaasifyCatalog(collections_paths=paths)



        # if self.catalog is None:
        #     # collections_paths = [
        #     #     ,
        #     #     os.path.join(self._path.get_path(mode="abs"), CATALOG_PREFIX),
        #     # ]


        #     CATALOG_PREFIX = ".paasify/collections"
        #     stack_catalog_path = None
        #     if self.ns:
        #         stack_catalog_path = os.path.join(self.ns._path.get_path(mode="abs"), CATALOG_PREFIX)
        #     # ns_catalog_path = None
        #     # if self.ns:
        #     ns_catalog_path = os.path.join(self._path.get_path(mode="abs"), CATALOG_PREFIX)
                
        #     user_catalog_path = os.path.expanduser("~/.paasify/collections")
        #     etc_catalog_path = "/etc/paasify/collections"
        #     sys_catalog_path = "/usr/local/share/paasify/collections"

        #     collections_paths = [
        #         stack_catalog_path,
        #         ns_catalog_path,
        #         user_catalog_path,
        #         etc_catalog_path,
        #         sys_catalog_path,
        #     ]
        #     collections_paths = [x for x in collections_paths if x]




        #     # pprint(collections_paths)
        #     # assert False, "WIP - Catalog"
        #     logger.debug(
        #         "No catalog provided, searching for in parents of: %s", ~self._path
        #     )
        #     self.catalog = PaasifyCatalog(collections_paths=collections_paths)

        self.setup_node()

    # Stack intialization
    # --------------------------------

    # def find_namespace(self):
    #     "Find the closest namespace above the stack"

    #     ret = None
    #     try:
    #         path = self._path.get_path(mode="abs")
    #         match = find_closest_workdir(
    #             path=path, search_up=True, kind=[PaasifyNamespace]
    #         )
    #         if match:
    #             ret = match
    #     except exc.PaasifyWorkdirNotFoundError as err:
    #         logger.debug("No namespace found in %s: %s", path, err)

    #     return ret

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
        # return self.config.get("apps", [])

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


# Context helper
# ================================================


# def find_closest_workdir(path=None, search_up=True, kind=None):
#     "Find the closest workdir"

#     # Prepare args
#     items = kind or [
#         PaasifyStack,
#         PaasifyNamespace,
#     ]
#     items = [items] if not isinstance(items, list) else items
#     if not path:
#         # path = list_parent_dirs(os.getcwd())
#         path = os.getcwd()
#     items_names = " or ".join([getattr(x, "__name__", str(x)) for x in items])

#     # Loop over first match
#     logger.debug("Searching for %s in path: %s", items_names, path)
#     errors = []
#     for item in items:
#         assert isinstance(item, type), f"Item must be a type, not {type(item)}"
#         try:
#             out = item(path=path, search_up=search_up)
#             logger.info("Found item: %s in %s", out, ~out.path)
#             if item is PaasifyStack:
#                 # print("GOT STACK:", out)
#                 # pprint(out.__dict__)
#                 if out.sub_path:
#                     logger.info("%s detected, looking for app %s", item, out.sub_path)
#                     # print("SUB PATH:", out.sub_path)
#                     out = out[out.sub_path]
#                 # assert False, "WIP"
#             return out
#         except exc.PaasifyWorkdirNotFoundError as err:
#             logger.debug("Can't find %s in path '%s': %s", item.__name__, path, err)
#             errors.append(err)

#     # msg = f"Can't find any {items_names} in path: {last_error}"
#     errors = "\n  - ".join([str(x) for x in errors])
#     search = "in parent directories" if search_up else "in paths"
#     errors = f"Can't find any {items_names} {search}:\n  - {errors}"
#     raise exc.PaasifyWorkdirNotFoundError(errors)
