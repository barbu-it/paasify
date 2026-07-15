import logging
from pathlib import Path, PosixPath
from pprint import pprint
import yaml

from superconf.anchors import PathAnchor
from superconf.exceptions import ConfigurationException
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
from paasify_v4.models.comp_tags import ComposeTagV1, JsonnetTagV1
from paasify_v4.nodes_paasify import AppNode, requires_setup_node, setup_once
from paasify_v4.specs.config_app import AppMainConfig

logger = logging.getLogger(__name__)


##########################################
class PaasifyV1SupportMixin:
    "General API supprot for v1"

    def scan_children_files(
        self,
        needles: list[str] | str,
        path: str | PosixPath = None,
    ) -> list[PosixPath]:
        """
        Scan children files for one or more needles
        Output is a list of PosixPath sorted by name
        """
        app_path = path or ~self.path
        needles = needles or ["docker-compose.*.yml"]
        if not isinstance(needles, list):
            needles = [needles]
        ret = []
        upath = Path(app_path)
        for needle in needles:
            for match in upath.rglob(needle):
                ret.append(match)
        return list(sorted(ret))


class PaasifyCollectionV1SupportMixin(PaasifyV1SupportMixin):
    "Support for paasify v1 collections"

    def get_jsonnet_plugin_tags(self) -> list[JsonnetTagV1]:
        "Return var tags - V1 support"

        # search_path = ~self.path +
        search_path = "__paasify__/tags/*.jsonnet"
        tags = []
        jsonnet_paths = self.scan_children_files(search_path)
        for match in jsonnet_paths:
            tag = JsonnetTagV1(path=match, parent=self)
            tags.append(tag)
        return tags

    def get_compose_feat_tags(self) -> list[ComposeTagV1]:
        "Return compose files for collections - V1 support"

        search_path = "__paasify__/tags/docker-compose.*.jsonnet"
        compose_files = []
        jsonnet_paths = self.scan_children_files(search_path)
        for match in jsonnet_paths:
            compose_file = ComposeTagV1(path=match, parent=self)
            compose_files.append(compose_file)
        return compose_files


class PaasifyAppV1SupportMixin(PaasifyV1SupportMixin):
    "App v1 support"

    def get_infos(self) -> dict:
        "Get infos"
        logger.debug("Get app_v1 infos for %s", self)
        out = {
            "self": self,
            "kind": self.kind,
            "name": self.name,
            "ident": self.ident,
            "path": ~self.path,
            "vars": to_yaml(self.get_vars(), strip_last=True),
            "tags_files": to_yaml(self.get_tags(), strip_last=True),

            "ZZZ_WIP": "YOOOO"
            # "compose_files": to_yaml(
            #     [
            #         str(x.name)
            #         for x in sorted(self.scan_children_files("docker-compose.*.yml"))
            #     ],
            #     strip_last=True,
            # ),
            # "jsonnet_files": to_yaml(
            #     [str(x.name) for x in sorted(self.scan_children_files("*.jsonnet"))],
            #     strip_last=True,
            # ),
        }
        return out

        # base["app_ident"] = app.ident
        # base["app_name"] = app.name
        # base["app_path"] = ~app.path
        # app_vars = to_yaml(app.get_vars())
        # base["app_vars"] = app_vars

    # Manage paasify.app.yml file
    # --------------------------------
    def get_paasify_app_cfg_file(self) -> str:
        "Return paasify app cfg file"
        matches = self.scan_children_files("paasify.app.yml")
        if matches:
            return matches[0]
        return None

    def parse_paasify_config(self, config_file=None) -> dict:
        "Parse paasify config"

        config_file = config_file or self.get_paasify_app_cfg_file()
        if not config_file:
            return {}


        # Try to parse config file
        try:
            raw_config = from_yaml(read_file(config_file))
        except yaml.YAMLError as err:
            msg = f"Error parsing paasify config file '{config_file}': {err}"
            raise exc.PaasifyYamlError(msg) from None

        # assert not hasattr(self, "config"), "config already set"
        # assert False, "To fix, replace by superconf.Configuration"
        # self.config = AppMainConfig(value=raw_config, key=f"app.{self.name}")


        # pprint(self.config.meta)
        # pprint(self.config.meta.__dict__)


        # assert False, "WIPPP"
        try:
            self.config = AppMainConfig(value=raw_config, key=f"app.{self.name}")
        except ConfigurationException as err:
            msg = f"{type(err).__name__} error when reading '{self.name}' app config: {err} in {config_file}"
            raise exc.PaasifyConfigError(msg) from None

        # pprint(self.config.meta.get_value())

        # print("YOOOO")
        # # pprint(app_cctl.features.__dict__)
        # pprint(app_cctl.features.parse_features())
        # app_cctl.app_tag_mgr.get_tags("features")

        # # help(app_cctl.__class__)
        # assert False, "WIP"

        # return raw_config

    def get_var_tags(self) -> list:
        "Return var tags"

        return []

    def get_vars_files(self) -> dict[str, None]:
        "Return app vars from vars.yml"
        # app_path = ~self.path

        # app_vars_matches = find_file_in_path(app_vars_files, app_path)
        app_vars_matches = self.scan_children_files(["vars.yml", "vars.yaml"])
        app_vars = {}
        if len(app_vars_matches) != 0:
            app_vars = from_yaml(read_file(app_vars_matches[0]))

        return app_vars

    def get_jsonnet_plugin_tags(self) -> list[JsonnetTagV1]:
        "Return list of JsonnetTagV1 from *.jsonnet files"

        jsonnet_paths = self.scan_children_files("*.jsonnet")
        ret = []
        for match in jsonnet_paths:
            jsonnet_file = JsonnetTagV1(path=match, parent=self)
            ret.append(jsonnet_file)
        return ret

    def get_compose_feat_tags(self) -> list[ComposeTagV1]:
        "Return list of ComposeTagV1 from: docker-compose.*.yml"

        docker_files = self.scan_children_files("docker-compose.*.yml")
        ret = []
        for match in docker_files:
            compose_file = ComposeTagV1(path=match, parent=self)
            ret.append(compose_file)
        return ret

    def get_compose_infos(self, compose_files=None, vars=None) -> dict:
        "Return compose infos"

        # docker_file_match = self.get_compose_file()
        # vars = vars or {}
        name = "testbuild"

        compose_files = compose_files or [self.get_compose_file()]
        assert compose_files, "Missing compose files"
        comp_app = ComposedApp(
            name=name, project_dir=self.path.get_path(), compose_files=compose_files
        )

        out = {
            "services": comp_app.get_services(),
            # "profiles": comp_app.get_profiles(),
            # "volumes": comp_app.get_volumes(),
            # "images": comp_app.get_images(),
            "variables": comp_app.get_variables(),
        }
        # out6 = comp_app.get_variables2()

        return out

    def gen_compose_file(
        self, compose_files=None, name=None, build_vars=None, output="json"
    ) -> str:
        "Write docker-compose.yml file"

        # Process docker-compose.yml file
        compose_files = compose_files or []
        assert compose_files, "Missing compose files"
        comp_app = ComposedApp(
            name=name, project_dir=self.path.get_path(), compose_files=compose_files
        )

        # TODO: To set back interpolate to false, there is an issue on
        # volumes names VS binds
        compose_content = comp_app.assemble(
            interpolate=True, normalize=False, output="json"
        )
        # compose_content = comp_app.assemble(interpolate=False, normalize=False)
        for varname in comp_app.get_variables2():
            if not varname in build_vars:
                logger.error("Missing variable: %s", varname)
                # logger.error("  %s", conf)

        return compose_content
