import logging
from pathlib import Path
from pprint import pprint
import paasify_v4.exception as exc
from paasify_v4.lib.jsonnet2 import JsonnetProcessor, JsonnetError
from paasify_v4.core import AppNode, setup_once, requires_setup_node
from superconf.anchors2 import PathAnchor

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


#######################################


class PaasifyTagV1(AppNode):
    "Paasify tag class - V1 support"

    def __init__(self, ident=None, path=None, parent=None):
        assert "docker-compose" not in ident, f"ident={ident}"
        assert "yml" not in ident, f"ident={ident}"
        assert "jsonnet" not in ident, f"ident={ident}"
        self.source = parent

        super().__init__(ident=ident, parent=parent)

        # print("CREATE PATHANCHOR", f"{self.source}/{self}", f"{+parent.path} + {path}")
        self._path = PathAnchor(path, name="tag_path", parent=parent.path)

    def __repr__(self):
        kind = self.__class__.__name__
        kind_source = self.source.__class__.__name__
        return f"{kind}.{kind_source} ({self.source.ident}.{self.ident})"


#######################################


class JsonnetTagV1(PaasifyTagV1):
    "Jsonnet tag class - V1 support"

    # def __init__(self, ident=None, path=None, parent=None):
    #     super().__init__(ident=ident, parent=parent)
    #     self._path = PathAnchor(path, parent=parent.path)
    #     self.source = parent

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
                    # "args": {
                    #     "app_name": self.source.ident,
                    #     "app_service": self.source.ident,
                    #     "app_description": self.source.ident,
                    #     "app_product": self.source.ident,
                    #     "app_prot": "http",
                    #     "app_fqdn": "localhost",
                    # }
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

        # jsonnet_file = jsonnet_path.read_text()
        # jsonnet_vars = jsonnet.evaluate_file(jsonnet_file)
        # return jsonnet_vars


class ComposeTagV1(PaasifyTagV1):
    "Compose tag class - V1 support"

    # def __init__(self, ident=None, path=None, parent=None):
    #     super().__init__(ident=ident, parent=parent)
    #     self._path = PathAnchor(path, parent=parent.path)
    #     self.source = parent


class PaasifyAppV1SupportMixin:
    def get_var_tags(self):
        "Return var tags"

        return []

    def get_jsonnet_files(self):
        "Return jsonnet files"

        app_path = ~self.path
        needle = "*.jsonnet"
        ret = []
        # print("GET JSONNET FILES FOR", self, app_path, needle)
        for match in Path(app_path).rglob(needle):
            jsonnet_file = JsonnetTagV1(ident=match.stem, path=match, parent=self)
            ret.append(jsonnet_file)
        return ret

    def get_compose_files(self):
        "Return files"

        # Get app path and base docker-compose file
        app_path = ~self.path

        needle = "docker-compose.*.yml"
        # print("GET COMPOSE FILES FOR", self, app_path, needle)

        ret = []
        # print(f"Search ({self}) docker compose  in app path:", app_path)
        for match in Path(app_path).rglob(needle):
            ident = match.stem.replace("docker-compose.", "")
            assert "docker-compose" not in ident, f"ident={ident}"

            # print("CREATE COMPOSE TAG", self,  +self.path, ident, app_path,  match)
            compose_file = ComposeTagV1(ident=ident, path=str(match), parent=self)
            ret.append(compose_file)

        return ret


class PaasifyCollectionV1SupportMixin:
    "Support for paasify v1 collections"

    def get_jsonnet_files(self):
        "Return var tags - V1 support"
        collection_path = self.path
        search_path = collection_path / "__paasify__/tags/"
        jsonnet_files = []
        # print("Search path JSONNET:", search_path)
        tags = []
        for match in Path(search_path).rglob("*.jsonnet"):
            jsonnet_files.append(match)

            tag = JsonnetTagV1(ident=match.stem, path=match, parent=self)
            tags.append(tag)
        return tags

    def get_compose_files(self):
        "Return compose files - V1 support"
        namespace_path = self.path
        search_path = namespace_path / "__paasify__/tags/"
        compose_files = []
        for match in Path(search_path).rglob("docker-compose.*.yml"):
            ident = match.stem.replace("docker-compose.", "")
            # ident = f"{self.ident} YOOOO222"
            # assert False, f"ident={ident}"
            assert "docker-compose" not in ident, f"ident={ident}"
            compose_file = ComposeTagV1(ident=ident, path=match, parent=self)
            compose_files.append(compose_file)

        return compose_files
