import logging
from pathlib import Path, PosixPath
from pprint import pprint

from superconf.anchors2 import PathAnchor

import paasify_v4.exception as exc
from paasify_v4.common import (
    dict_to_env,
    find_file_in_path,
    flatten,
    from_yaml,
    read_file,
    to_domain,
    to_yaml,
    truncate,
    write_file,
)
from paasify_v4.engine_docker.compose_app import ComposedApp
from paasify_v4.nodes_paasify import AppNode, requires_setup_node, setup_once
from paasify_v4.specs.config_app import AppMainConfig

logger = logging.getLogger(__name__)


class Var:
    "Represent a variable"

    def __init__(self, name, value, **kwargs):
        self.ident = name
        self._name = name
        self._value = value
        self.kwargs = kwargs
        self.path = "nopath"

    def __repr__(self):
        keyval = f"{self.name}={self.value}"
        return f"Var({truncate(keyval, max=24)})"

    def __str__(self):
        "Return string representation - Required for var templating"
        return f"{self.value}"

    @property
    def value(self):
        "Return value"
        return self._value

    @property
    def name(self):
        "Return name"
        return self._name
