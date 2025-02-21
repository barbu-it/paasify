import logging
import os
# pylint: disable=unused-import
from pprint import pprint
from typing import Optional

from mrjk_components.varmgr.lib.store_base import (Source, StoreManager,
                                                   UndefinedVarError)
from mrjk_components.varmgr.lib.store_template import RenderableStoreManager
from superconf.anchors2 import FileAnchor, PathAnchor

import paasify_v4.exception as exc
from paasify_v4.common import (find_file_up, from_yaml, list_parent_dirs,
                               read_file, to_json)

logger = logging.getLogger(__name__)


# Node registry class
# ================================================
class NodeRegistry:
    "Node registry class"

    def __init__(self):
        self.nodes = []

    def register_node(self, node):
        "Register a node"
        self.nodes.append(node)

    def get_node(self, ident):
        "Get a node"
        for node in self.nodes:
            if node.ident == ident:
                return node
        return None


node_registry = NodeRegistry()

# Parent Node class
# ================================================


# pylint: disable=too-few-public-methods
class Node:
    "Node class"

    ident = None
    parent = None
    _children = None

    def __init__(self, ident=None, parent=None):
        self.ident = ident
        self.parent = parent
        self._children = {}

        # Register the node (Temp?)
        node_registry.register_node(self)

        # Make the node relationship
        if parent is not None:
            assert isinstance(parent, Node)
            parent._children[self.ident] = self

    def __repr__(self):
        return f"{self.__class__.__name__}({self.ident or ''})"

    def iter_parents(self, include_self=False):
        "Iterate over parents"
        if include_self:
            yield self
        parent = self.parent
        while parent:
            yield parent
            parent = parent.parent


# VarMgr mixin
# ================================================


class VarMgrNodeMixin:
    "VarMgr mixin class"

    def get_varmgr(self):
        "Get varmgr"
        logger.info("Prepare varmgr for: %s", self)

        # Goal:
        # - Show vars from the stack
        # - Show vars from the namespace
        # - Show vars from the pod
        # ret = {
        #     "ns_vars": self.ns.get_vars(),
        #     "stack_vars": self.stack.get_vars(),
        #     "pod_vars": self.config.get("vars", {}),
        # }

        # varmgr = StoreManager()
        varmgr = RenderableStoreManager()
        varmgr.add_sources(
            [
                Source("runtime_vars", level=1000, help="Runtime variables"),
                Source("pod_vars", level=500, help="Pod variables"),
                Source("stack_vars", level=700, help="Stack variables"),
                Source("ns_vars", level=900, help="Namespace variables"),
                Source("app_vars", level=1000, help="App variables"),
                Source("default_vars", level=9999, help="Default variables"),
            ]
        )
        varmgr.set_scopes(
            {
                "scope_ns": ["runtime_vars", "ns_vars", "default_vars"],
                "scope_stack": [
                    "runtime_vars",
                    "stack_vars",
                    "ns_vars",
                    "default_vars",
                ],
                "scope_pod": [
                    "runtime_vars",
                    "pod_vars",
                    "stack_vars",
                    "ns_vars",
                    "app_vars",
                    "default_vars",
                ],
            }
        )

        return varmgr
