"Manage namespaces"
import os
import sys
from pprint import pprint
import logging

from superconf.anchors2 import PathAnchor, FileAnchor
from paasify_v4.common import find_files_down
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

    node__iterate_backend = "_store_stacks"
    node__iterate_setupmarker = "setup_stacks"

    OBJECT_NAME = "Namespace"
    ALLOWED_CONF_FILES = [
        "paasify.ns.yml",
        "paasify.ns.yaml",
        "paasify.namespace.yml",
        "paasify.namespace.yaml",
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._store_stacks = {}

        self.setup_node()
        # pprint(self.__dict__)

    @setup_once("setup_node")
    def setup_node(self):
        "Setup the pod"
        logger.info("Setup namespace: %s", self)

        # Default ns config
        out = {
            "namespace": None,
            "config": self.config.get("config", {}),
            "collections": {},
            "vars": self.config.get("vars", {}),
            "stacks": self.config.get("stacks", []),
        }
        self.config = out

    @requires_setup_node("setup_node")
    @setup_once("setup_stacks")
    def setup_stacks(self):
        "Setup stacks"

        # Frist implementation:
        # - Scan all subdirectories with depth=3 and search for paasify.stack.yml file.
        # - For each files, create a PaasifyStack object and add it to the stacks list.
        # - Return the stacks list.

        # print("SETUP STACKS from", ~self.path)

        # Get auto discovery config
        auto_discovery = self.config.get("config", {}).get("auto_discovery", {})
        max_depth = auto_discovery.get("depth", 3)

        # Find all paasify stack files under namespace path
        file_names = [
            "paasify.stack.yml",
            "paasify.stack.yaml",
            "paasify.yml",
            "paasify.yaml",
        ]

        path_mode = "abs"

        path = self.path.get_path(mode=path_mode)
        stack_files = find_files_down(file_names, path, depth=3)

        stacks_config = {}

        for stack_file in stack_files:

            fanchor = FileAnchor(stack_file, parent=self.path)
            stack_dir = fanchor.get_dir()

            if stack_dir in stacks_config:
                current = stacks_config[stack_dir]

                logger.warning(
                    "Duplicate file config for stack %s, found %s but ignoring extra %s",
                    stack_dir,
                    current.get_path(mode=path_mode),
                    stack_file,
                )
                continue

            logger.debug("Found stack file: %s", stack_file)
            # We import locally PaasifyStack to avoid circular import
            # pylint: disable=import-outside-toplevel
            from paasify_v4.core_stack import PaasifyStack

            stack_ident2 = fanchor.get_dir(
                mode="rel", start=self.path.get_dir(), clean=True
            )
            stack_ident = stack_dir
            print("STACK DIR", stack_ident, "VS", stack_ident2)

            stack_inst = PaasifyStack(ident=stack_ident2, parent=self, path=~fanchor)
            stacks_config[stack_ident] = stack_inst

        # pprint(stacks_config)

        self._store_stacks = stacks_config
        # sys.exit(0)

        # Find all paasify stack files under namespace path
        #
        # stack_files = []
        # for root, dirs, files in os.walk(path):
        #     # Calculate current depth
        #     depth = root[len(path):].count(os.sep)
        #     if depth > max_depth:
        #         # Skip deeper directories
        #         dirs[:] = []
        #         continue

        #     for file in files:
        #         if file in ["paasify.yml", "paasify.yaml"]:
        #             stack_path = os.path.join(root, file)
        #             logger.debug("Found stack file: %s", stack_path)
        #             stack_files.append(stack_path)

        # pprint(stack_files)

        logger.info(
            "Found %d stack files under %s (max depth=%d)",
            len(stack_files),
            path,
            max_depth,
        )

        # ################################

        # pprint(self.__dict__)
        # stacks = self.config.get("stacks", [])
        # for stack in stacks:
        #     print("SETUP STACK", stack)

        #     # stack.setup_node()
        # # self.config["stacks"] = [
        # #     PaasifyStack(path=os.path.join(self._path, stack))
        # #     for stack in self.config.get("stacks", [])
        # # ]

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
