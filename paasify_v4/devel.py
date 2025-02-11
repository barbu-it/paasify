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
import paasify_v4.exception as exc


# from paasify_v4.catalog import PaasifyCatalog

logger = logging.getLogger(__name__)


# Pod classes
# ================================================


class PaasifyPod(WorkingDirNode):
    "Base class for all Paasify pods"

    OBJECT_NAME = "Pod"
    ALLOWED_CONF_FILES = [
        "paasify.pod.yml",
        "paasify.pod.yaml",
    ]


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

    def get_deployments(self):
        "Get all deployments for the stack"
        return self.config.get("apps", [])


# Namespace class
# ================================================


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


# Context helper
# ================================================


def find_closest_workdir(path=None, search_up=True, kind=None):
    "Find the closest workdir"

    # Prepare args
    items = kind or [
        PaasifyStack,
        PaasifyNamespace,
    ]
    items = [items] if not isinstance(kind, list) else kind
    if not path:
        # path = list_parent_dirs(os.getcwd())
        path = os.getcwd()
    items_names = " or ".join([item.__name__ for item in items])

    # Loop over first match
    logger.debug("Searching for %s in path: %s", items_names, path)
    last_error = None
    for item in items:
        try:
            return item(path=path, search_up=search_up)
        except exc.PaasifyWorkdirNotFoundError as err:
            logger.debug("Can't find %s in path '%s': %s", item.__name__, path, err)
            last_error = err

    # msg = f"Can't find any {items_names} in path: {last_error}"
    raise exc.PaasifyWorkdirNotFoundError(last_error)
