import logging
from pathlib import Path, PosixPath
from pprint import pprint

from superconf.anchors2 import PathAnchor

from paasify_v4.lib.jsonnet2 import JsonnetError, JsonnetProcessor
from paasify_v4.nodes_paasify import AppNode, requires_setup_node, setup_once

logger = logging.getLogger(__name__)


class PaasifyTagV1(AppNode):
    "Paasify tag class - V1 support"

    def __init__(self, ident=None, path=None, parent=None):
        assert ident is None, f"Can't acccept anything else than none value"
        assert isinstance(path, PosixPath), f"path={path}, expected posixPath"

        ident = path.stem.replace("docker-compose.", "")
        self._path = PathAnchor(path, parent=parent.path, name="source_file")

        assert "docker-compose" not in ident, f"ident={ident}"
        assert "yml" not in ident, f"ident={ident}"
        assert "jsonnet" not in ident, f"ident={ident}"

        super().__init__(ident=ident, parent=parent)

        self.source = parent

    def __repr__(self):
        kind = self.__class__.__name__
        kind_source = self.source.__class__.__name__
        return f"{kind}.{kind_source} ({self.source.ident}.{self.ident})"


#######################################


class JsonnetTagV1(PaasifyTagV1):
    "Jsonnet tag class - V1 support"

    def process_jsonnet_vars(self, vars=None):
        "Process jsonnet vars"
        jsonnet_path = ~self.path
        vars = vars or {}

        jproc = JsonnetProcessor()
        try:
            out = jproc.process_jsonnet_exec(
                jsonnet_path,
                "plugin_vars",
                {
                    "args": vars,
                },
            )
            # print("======== OUT")
            # pprint(out)
            # print("======== OUT")
        except JsonnetError as err:
            # logger.critical(f"Can't parse jsonnet file: {jsonnet_path}")
            msg = f"Can't parse jsonnet file: {jsonnet_path}, got error:\n\n{err}"
            raise exc.PaasifyAssembleError(msg) from None

        return out

    def process_jsonnet_plugin(self, config=None, docker_data=None):
        "Process jsonnet plugin"
        jsonnet_path = ~self.path
        docker_data = docker_data or {}

        jproc = JsonnetProcessor()
        try:
            out = jproc.process_jsonnet_exec(
                jsonnet_path,
                "docker_transform",
                {
                    "args": config,
                    "docker_data": docker_data,
                },
            )
            # print("======== OUT")
            # pprint(out)
            # print("======== OUT")
        except JsonnetError as err:
            # logger.critical(f"Can't parse jsonnet file: {jsonnet_path}")
            msg = f"Can't parse jsonnet file: {jsonnet_path}, got error:\n\n{err}"
            raise exc.PaasifyAssembleError(msg) from None

        return out


class ComposeTagV1(PaasifyTagV1):
    "Compose tag class - V1 support"
