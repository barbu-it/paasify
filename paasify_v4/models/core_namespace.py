"Manage namespaces"
import logging
from pprint import pprint

from superconf.anchors2 import FileAnchor

from paasify_v4.common import find_files_down
from paasify_v4.models.core_common import PaasifyNamespaceV1Mixin
from paasify_v4.models.core_stack import PaasifyStack
from paasify_v4.nodes_paasify import requires_setup_node, setup_once

# import paasify_v4.exception as exc

logger = logging.getLogger(__name__)


# class PaasifyNoNamespace(PodManagementMixin, AppNode):
#     "No namespace class, just implement dumb methods"

#     paasify_type = "namespace"

#     OBJECT_NAME = "EmptyNamespace"
#     ALLOWED_CONF_FILES = ["paasify.ns.yml"]

#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)


class PaasifyNamespace(PaasifyNamespaceV1Mixin):
    "Namespace class, manage list of stacks"

    paasify_type = "namespace"

    node__iterate_backend = "_store_stacks"
    node__iterate_setupmarker = "setup_stacks"

    OBJECT_NAME = "Namespace"
    ALLOWED_CONF_FILES = [
        "paasify.ns.yml",
        "paasify.ns.yaml",
        "paasify.namespace.yml",
        "paasify.namespace.yaml",
    ]

    def __init__(self, catalog=None, **kwargs):
        super().__init__(**kwargs)

        if not self.ident:
            self.ident = self.path.get_name()

        # pprint(self.__dict__)
        # print(self.path)
        # # help(self.path)
        # print()

        assert self.ident, "Namespace must have an ident"

        self._store_stacks = {}
        # Register catalog if provided
        self.catalog = catalog
        self.setup_node()

    # @property
    # def fname(self):
    #     "Return full name"
    #     return self.name or "MISSING"

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

            fanchor = FileAnchor(stack_file, name="stack_app", parent=self.path)
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
            # from paasify_v4.core_stack import PaasifyStack

            stack_ident2 = fanchor.get_dir(
                mode="rel", start=self.path.get_dir(), clean=True
            )
            stack_ident = stack_dir

            # print("EXEC HERER", self)

            stack_inst = PaasifyStack(
                ident=stack_ident2,
                parent=self,
                path=~fanchor,
                catalog=self.catalog,
            )
            stacks_config[stack_ident] = stack_inst

        self._store_stacks = stacks_config

        logger.info(
            "Found %d stack files under %s (max depth=%d)",
            len(stack_files),
            path,
            max_depth,
        )

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

    @requires_setup_node("setup_node")
    def get_pods(self):
        "Get pods"
        out = []
        for stack in self.get_stacks():
            out.extend(stack.get_pods())
        return out

    @requires_setup_node("setup_node")
    def get_stacks(self):
        "Get stacks"

        out = []
        for stack in self:
            out.append(stack)
        return out
