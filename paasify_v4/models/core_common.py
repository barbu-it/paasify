import logging

# from pathlib import Path, PosixPath
from pprint import pprint

import paasify_v4.exception as exc
from paasify_v4.lib_paasify.api_abc import PodManagedMixin, PodManagementMixin
from paasify_v4.models.comp_apps import (
    PaasifyAppV1SupportMixin,
    PaasifyCollectionV1SupportMixin,
)

# from paasify_v4.specs.config_app import AppMainConfig
# from paasify_v4.models.comp_tags import JsonnetTagV1, ComposeTagV1
from paasify_v4.nodes import VarMgrNodeMixin

# from paasify_v4.common import (dict_to_env, find_file_in_path, flatten,
#                                from_yaml, read_file, to_domain, to_yaml,
#                                truncate, write_file)
# from paasify_v4.engine_docker.compose_app import ComposedApp
from paasify_v4.nodes_paasify import (  # , requires_setup_node, setup_once
    AppNode,
    WorkingDirNode,
)

# from superconf.anchors import PathAnchor


logger = logging.getLogger(__name__)


class TagConfigV1(AppNode):
    "Stack tag config class - V1 support - DEPRECATED< REPLACE BY SEUPR CONFIG"

    def __init__(self, ident=None, config=None, parent=None):

        tag_config = {}
        tag_ident = None
        if config:
            if isinstance(config, str):
                tag_ident = config
                tag_config = {}
            elif isinstance(config, dict):
                conf_keys = list(config.keys())
                assert len(conf_keys) == 1, f"Expected 1 key, got {len(conf_keys)}"
                tag_ident = conf_keys[0]
                tag_config = config[tag_ident]
                if not isinstance(tag_config, dict):
                    msg = f"Invalid tag config type for {parent}/{tag_ident}, expected dict, got {type(tag_config)}: {tag_config}"
                    raise exc.PaasifyConfigError(msg)
            else:
                msg = f"Invalid tag config type for {parent}/{tag_ident}, expected dict or string, got {type(config)}: {config}"
                raise exc.PaasifyConfigError(msg)

        assert tag_ident
        self.config = tag_config
        assert isinstance(self.config, dict)

        super().__init__(ident=tag_ident, parent=parent)


######


class PaasifyPodV1Mixin(
    PodManagedMixin, VarMgrNodeMixin, PaasifyAppV1SupportMixin, AppNode
):
    "Pod v1 support"

    # def get_infos(self) -> dict:
    #     "Get infos"
    #     return {}


class PaasifyStackV1Mixin(PodManagementMixin, VarMgrNodeMixin, WorkingDirNode):
    "Stack v1 support"

    # def get_infos(self) -> dict:
    #     "Get infos"
    #     return {}


class PaasifyNamespaceV1Mixin(
    PaasifyCollectionV1SupportMixin, PodManagementMixin, VarMgrNodeMixin, WorkingDirNode
):
    "Namespace v1 support"

    # def get_infos(self) -> dict:
    #     "Get infos"
    #     return {}


class PaasifyCatalogV1Mixin(AppNode):
    "Catalog v1 support"

    # def get_infos(self) -> dict:
    #     "Get infos"
    #     return {}


class PaasifyCollectionV1Mixin(PaasifyCollectionV1SupportMixin, AppNode):
    "Collection v1 support"

    # def get_infos(self) -> dict:
    #     "Get infos"
    #     return {}


class PaasifyAppV1Mixin(PaasifyAppV1SupportMixin, AppNode):
    "App v1 support"

    # def get_infos(self) -> dict:
    #     "Get infos"
    #     return {}
