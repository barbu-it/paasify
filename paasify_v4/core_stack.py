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
from paasify_v4.core import AppNode, WorkingDirNode, setup_once, requires_setup_node
from paasify_v4.core_namespace import PaasifyNamespace
import paasify_v4.exception as exc



# from paasify_v4.catalog import PaasifyCatalog

logger = logging.getLogger(__name__)


# Pod classes
# ================================================


class PaasifyPod(AppNode):
    "Base class for all Paasify pods"


    def __init__(self, ident, parent=None, config=None):
        assert isinstance(parent, PaasifyStack)
        super().__init__(ident, parent)

        self.config = config or {}



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

    # def __init__(self, ident=None, parent=None, path=None,search_up=None):
    #     super().__init__(ident=ident, parent=parent)

    def __init__(
        self, ident=None, parent=None, path=None, search_up=None, namespace=None
    ):
        super().__init__(ident=ident, parent=parent, path=path, search_up=search_up)

        self.ns = namespace
        if self.ns is None:
            logger.debug(
                "No namespace provided, searching for in parents of: %s", ~self._path
            )
            self.ns = self.find_namespace()

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
                config=pod_config,
            )
            out[pod_ident] = pod

        self._store_pods = out

    @requires_setup_node("setup_node")
    def get_pods(self):
        "Get all deployments for the stack"
        return list(self._store_pods.values())
        # return self.config.get("apps", [])




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
        assert isinstance(item, type), f"Item must be a type, not {type(item)}"
        try:
            return item(path=path, search_up=search_up)
        except exc.PaasifyWorkdirNotFoundError as err:
            logger.debug("Can't find %s in path '%s': %s", item.__name__, path, err)
            errors.append(err)

    # msg = f"Can't find any {items_names} in path: {last_error}"
    errors = '\n  - '.join([str(x) for x in errors])
    search = 'in parent directories' if search_up else 'in paths'
    errors = f"Can't find any {items_names} {search}:\n  - {errors}"
    raise exc.PaasifyWorkdirNotFoundError(errors)
