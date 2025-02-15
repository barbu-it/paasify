"""
Core module for Paasify v4.

This module provides base classes and decorators for node-based hierarchical structures.
Key components include:

- Node: Base class for hierarchical node structures with parent-child relationships
- setup_once: Decorator to ensure setup methods are called only once
- SETUP_PREFIX: Prefix used for setup method markers

The module focuses on providing a foundation for building tree-like data structures
with controlled initialization patterns.
"""

import os
import logging
from typing import Optional

# pylint: disable=unused-import
from pprint import pprint

from mrjk_components.varmgr.lib.store_template import RenderableStoreManager
from mrjk_components.varmgr.lib.store_base import (
    StoreManager,
    Source,
    UndefinedVarError,
)


import paasify_v4.exception as exc


from superconf.anchors2 import PathAnchor, FileAnchor


from paasify_v4.common import (
    read_file,
    from_yaml,
    find_file_up,
    list_parent_dirs,
    to_json,
)

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


SETUP_PREFIX = "__node__setup__"


@staticmethod
def setup_once(name="setup_node"):
    "Decorator to ensure setup method is called only once, with optional force parameter"

    def decorator(func):
        setup_marker = f"{SETUP_PREFIX}{name}"

        def wrapper(self, *args, force=False, **kwargs):
            if not hasattr(self, setup_marker) or force:
                logger.debug(
                    "Trigger lazy loader for '%s' via: <%s>.%s()",
                    name,
                    self,
                    func.__name__,
                )
                result = func(self, *args, **kwargs)
                setattr(self, setup_marker, True)
                return result
            return None

        return wrapper

    return decorator


@staticmethod
def requires_setup_node(name="setup_node"):
    "Decorator to ensure setup method is called only once before method execution"
    setup_marker = f"{SETUP_PREFIX}{name}"

    def decorator(func):
        def wrapper(self, *args, **kwargs):
            if not hasattr(self, setup_marker):
                logger.debug("Setup mode '%s' init: %s", name, func.__name__)
                setup_method = getattr(self, name)
                setup_method()
                setattr(self, setup_marker, True)
            logger.debug("Setup mode '%s' forward: %s", name, func.__name__)
            return func(self, *args, **kwargs)

        return wrapper

    return decorator


# Paasify AppNode class
# ================================================

class HelperMethodsMixin:
    "Common helper methods"

    def read_yaml_file(self, filename):
        "Read vars.yml file"
        vars_file = os.path.join(~self.path, filename)
        if os.path.exists(vars_file):
            data = read_file(vars_file)
            data = from_yaml(data)
            return data
        return {}


class AppNode(HelperMethodsMixin, Node):
    "AppNode class"

    # Default type
    paasify_type = "internal"

    # Default config
    # node__iterate_backend = "_children"
    # node__iterate_setupmarker = "setup_node"

    # Prefered config
    node__iterate_backend = "_children"
    node__iterate_setupmarker = None

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name or ''})"

    @property
    def kind(self):
        "Return kind"
        return self.paasify_type

    @property
    def name(self):
        "Return collection ident"
        if hasattr(self, "_name"):
            return self._name
        name = self.ident
        return name

    @property
    def path(self):
        "Return source"

        # if hasattr(self, "sub_path"):
        #     return self.sub_path
        if hasattr(self, "_path"):
            return self._path
        return "NO PATH"

    # def get_path(self):
    #     "Return path"

    #     # If path is hardcoded, return it
    #     if hasattr(self, "_path"):
    #         return self._path

    #     if hasattr(self, "sub_path"):
    #         sub_path = self.sub_path

    #         # If there is no path, then look recurisveley in each parent
    #         # until we find a path attribute
    #         if self.parent is not None:
    #             return os.path.join(self.parent.get_path(), sub_path)
    #     return "NO PATH"

    # Special methods
    def _get_store_attr(self):
        "Get store attribute"

        backend_store_name = self.node__iterate_backend

        # Check if store is inited
        backend_setup_marker_name = self.node__iterate_setupmarker
        if backend_setup_marker_name is None:
            logger.info(
                "Store: Store: %s.%s: does not specify setup marker",
                self,
                backend_store_name,
            )
        else:
            backend_setup_marker_attr = f"{SETUP_PREFIX}{backend_setup_marker_name}"
            backend_setup_status = getattr(self, backend_setup_marker_attr, None)

            if backend_setup_status:
                logger.info(
                    "Store: %s.%s: setup has already been done, no need to run it again",
                    self,
                    backend_store_name,
                )
            else:
                func = getattr(self, backend_setup_marker_name, None)
                if not callable(func):
                    assert False, f"Setup marker is not callable: {func}"

                logger.info(
                    "Store: %s.%s: setup object with: %s",
                    self,
                    backend_store_name,
                    func,
                )
                func()

        # Then fetch the store name
        backend_store_attr = f"{backend_store_name}"
        backend_store = getattr(self, backend_store_attr, None)
        if backend_store_name != "_children":
            backend_store_name = f"store_{backend_store_name}"
        logger.info(
            "Store: %s.%s: Fetching dynamic store: %s",
            self,
            backend_store_name,
            backend_store_attr,
        )

        # Return always a list of things
        if isinstance(backend_store, dict):
            return list(backend_store.values())
        assert isinstance(backend_store, list), f"Store is not a list: {backend_store}"
        return backend_store

    def __iter__(self):
        "Iterate over children"
        logger.debug("Iterate over children: %s", self)
        return iter(self._get_store_attr())

    def __len__(self):
        "Return length"
        return len(self._get_store_attr())

    def __getitem__(self, key):
        "Get item"
        logger.debug("Get item: %s.%s", self, key)

        store = self._get_store_attr()
        for item in store:
            if item.ident == key:
                return item
        return None

    def __contains__(self, key):
        "Check if item is in store"
        return key in self._get_store_attr()

    def __bool__(self):
        "Check if node is empty"
        return True


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


# Working Directory class
# ================================================


class WorkingDirNode(VarMgrNodeMixin, AppNode):
    "Working directory mixin class"

    ALLOWED_CONF_FILES = []
    OBJECT_NAME = "working_dir"

    def __init__(self, ident=None, parent=None, path=None, search_up=None):
        super().__init__(ident=ident, parent=parent)

        self.path_mode = "abs" if os.path.isabs(path) else "rel"

        _root_path, _config_file, _sub_path = self.find_workdir(
            path=path, search_up=search_up
        )

        root_path = PathAnchor(_root_path, mode=self.path_mode)
        root_config_path = FileAnchor(path=_config_file, parent=root_path)
        self._path = root_path
        self.config_path = root_config_path
        self.sub_path = _sub_path

        logger.debug("Workdir %s config file: %s", self.OBJECT_NAME, ~root_config_path)
        self.config = self.load_config(~root_config_path) or {}

        if not self.ident:
            self._name = self._path.get_name()

        # TODO: Remove absolute path in logs
        logger.info(
            "Initilize %s from: %s", self.OBJECT_NAME, self._path.get_path(mode="abs")
        )

    def __repr__(self):
        return f"{self.__class__.__name__}({self.path.get_path(mode='rel') or ''})"

    def load_config(self, config: Optional[str] = None):
        "Load the namespace config from a file"

        _conf = ~self.config_path if not config else config
        if os.path.isfile(_conf):
            return from_yaml(read_file(_conf))

        return {}

    def find_workdir(self, path=None, search_up=None):
        "Find the namespace path and config file"

        path = os.path.abspath(path) if path else None

        # Prepare discovery method
        # ------------------------
        config_files = None
        root_path = None
        if search_up and path:
            logger.debug("Workdir %s search up from: %s", self.OBJECT_NAME, path)
            paths = list_parent_dirs(path)
            config_files = find_file_up(self.ALLOWED_CONF_FILES, paths)
        elif path:
            if os.path.isfile(path):
                logger.debug("Workdir %s file fetch from: %s", self.OBJECT_NAME, path)
                config_files = [path]
                root_path = os.path.dirname(config_files[0])
            else:
                logger.debug(
                    "Workdir %s directory fetch from: %s", self.OBJECT_NAME, path
                )
                root_path = path
                config_files = find_file_up(self.ALLOWED_CONF_FILES, [path])
        else:
            raise exc.PaasifyError(
                f"No path or search_up provided to start {self.OBJECT_NAME}"
            )

        # Load configuration file
        # ------------------------
        # Actually, we should have a list of zero or one config file.
        if len(config_files) > 1:
            msg = f"Multiple config files found: {config_files}, we use only first one"
            logger.warning(msg)

        config_file = self.ALLOWED_CONF_FILES[0]
        if len(config_files) > 0:
            # The first item should always exists and be an existing file since we scanned
            # the directory above.
            config_file = config_files[0]
            if not root_path:
                root_path = os.path.dirname(config_file)

        # Final checks
        if not root_path:
            target = self.ALLOWED_CONF_FILES[0]
            msg = f"Can't find file '{target}' for {self.OBJECT_NAME} in path: {path}"
            if search_up:
                msg = f"Can't find file '{target}' for {self.OBJECT_NAME} in or above: {path}"

            raise exc.PaasifyWorkdirNotFoundError(msg)
        assert config_file

        sub_path = ""
        if path:
            sub_path = path.replace(root_path, "")
            # Remove leading slash
            sub_path = sub_path.lstrip("/")

        # Create anchored paths
        # ------------------------
        return (root_path, config_file, sub_path)
