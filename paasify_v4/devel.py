# import os
import logging
from pprint import pprint

# from typing import List, Dict
# from dataclasses import dataclass
# from types import SimpleNamespace
import os.path
from pathlib import Path
from typing import List, Optional, Union

# from superconf.anchors import PathAnchor

from paasify_v4.common import (
    read_file,
    from_yaml,
    find_file_up,
    list_parent_dirs,
    to_json,
)
from paasify_v4.core import AppNode, setup_once, requires_setup_node
import paasify_v4.exception as exc

from superconf.anchors2 import PathAnchor, FileAnchor

# from paasify_v4.catalog import PaasifyCatalog

logger = logging.getLogger(__name__)


# Directory Common classes
# ================================================


class _WorkingDir(AppNode):
    "Working directory mixin class"

    # node__iterate_backend = "_children"
    # node__iterate_setupmarker = "setup_node"

    ALLOWED_CONF_FILES = []
    OBJECT_NAME = "working_dir"

    def __init__(self, ident=None, parent=None, path=None, search_up=None):
        super().__init__(ident=ident, parent=parent)

        _root_path, _config_file = self.find_workdir(path=path, search_up=search_up)

        root_path = PathAnchor(_root_path, mode="rel")
        root_config_path = FileAnchor(path=_config_file, parent=root_path)
        self._path = root_path
        self.config_path = root_config_path

        logger.debug("Workdir %s config file: %s", self.OBJECT_NAME, ~root_config_path)
        self.config = self.load_config(~root_config_path)

        # TODO: Remove absolute path in logs
        logger.info(
            "Initilize %s from: %s", self.OBJECT_NAME, self._path.get_path(mode="abs")
        )

    def load_config(self, config: Optional[str] = None):
        "Load the namespace config from a file"

        _conf = ~self.config_path if not config else config
        if os.path.isfile(_conf):
            return from_yaml(read_file(_conf))

        return {}

    def find_workdir(self, path=None, search_up=None):
        "Find the namespace path and config file"

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
                msg = f"Can't find file '{target}' for {self.OBJECT_NAME} in hierarchy of: {path}"

            raise exc.PaasifyWorkdirNotFoundError(msg)
        assert config_file

        # Create anchored paths
        # ------------------------
        return (root_path, config_file)


# Pod classes
# ================================================


class PaasifyPod(_WorkingDir):
    "Base class for all Paasify pods"

    OBJECT_NAME = "Pod"
    ALLOWED_CONF_FILES = [
        "paasify.pod.yml",
        "paasify.pod.yaml",
    ]


# Stacks classes
# ================================================


class PaasifyStack(_WorkingDir):
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


class PaasifyNamespace(_WorkingDir):
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
