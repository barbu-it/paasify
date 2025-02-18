"Manage apps/pods"

import os
import logging
from pprint import pprint
import sh

from pathlib import Path
from types import SimpleNamespace
import json

from superconf.anchors2 import PathAnchor
from mrjk_components.varmgr.lib.store_template import RenderableStoreManager
from mrjk_components.varmgr.lib.store_base import (
    StoreManager,
    Source,
    UndefinedVarError,
)

from paasify_v4.core import (
    AppNode,
    VarMgrNodeMixin,
    WorkingDirNode,
    setup_once,
    requires_setup_node,
    node_registry,
)
from paasify_v4.common import (
    find_file_in_path,
    dict_to_env,
    write_file,
    read_file,
    from_yaml,
    to_yaml,
    to_domain,
    flatten,
    truncate,
)

# from paasify_v4.models.core_catalog import PaasifyCatalog
from paasify_v4.models.core_common import (
    PaasifyAppV1SupportMixin,
    JsonnetTagV1,
    ComposeTagV1,
    Var,
    TagConfigV1,
)

from paasify_v4.engine_docker.compose_app import ComposedApp
import paasify_v4.exception as exc

from paasify_v4.lib.shexec import shexec
from paasify_v4.core_abc import PodManagedMixin


logger = logging.getLogger(__name__)


# Vars management
# ================================================


# Pod classes
# ================================================


class PaasifyPod(PodManagedMixin, VarMgrNodeMixin, PaasifyAppV1SupportMixin, AppNode):
    "Base class for all Paasify pods"

    paasify_type = "pod"
    node__iterate_backend = "_store_vars"
    node__iterate_setupmarker = "setup_vars"

    def __init__(self, ident, parent=None, name=None, raw_config=None, path=None):
        # assert isinstance(parent, PaasifyStack)
        super().__init__(ident, parent)

        self._name = name or ident.split("/", maxsplit=1)[0]

        self._path = PathAnchor(path, name="pod_path", parent=parent.path)
        self.config = self.build_config(raw_config, ident=ident)
        self._app = None
        self._store_vars = {}

        self.setup_node()

    @property
    def ns(self):
        "Return namespace"
        return self.parent.ns

    @property
    def stack(self):
        "Return stack"
        return self.parent

    @property
    def catalog(self):
        "Return catalog"
        return self.parent.catalog

    # Infos
    # --------------------------------

    def get_infos(self):
        "Get infos"
        base = super().get_infos()
        # base["---"] = "---"

        if self.app:
            app_fields = [
                "self",
                # "kind",
                # "name",
                "ident",
                "path",
                "vars",
                # "tags",
                "compose_files",
                "jsonnet_files",
            ]
            app_vars = self.app.get_infos()
            # app_vars1 = {f"app_{key}": val for key, val in app_vars.items()}
            app_vars2 = {
                f"app_{key}": val for key, val in app_vars.items() if key in app_fields
            }
            # base.update(app_vars1)
            base.update(app_vars2)

        return base

    # Vars management
    # --------------------------------

    @setup_once("setup_vars")
    def setup_vars(self):
        "Setup vars"

        app_vars = self.config.get("vars", {}) or {}
        for var_name, var_value in app_vars.items():
            var = Var(var_name, var_value)
            self._store_vars[var_name] = var

        # self._store_vars = self.config.get("vars", {}) or {}

    @requires_setup_node("setup_vars")
    def get_vars(self):  # V2
        "Get vars"
        return {key: val.value for key, val in self._store_vars.items()}

    # @setup_once("setup_node")
    # def get_vars(self): # V1
    #     "Get vars"
    #     return self.config.get("vars", {}) or {}

    # Config build
    # --------------------------------

    def build_config(self, config, ident=None):
        "Build config"
        # if ident:
        #     config = config.get(ident, {})
        out = {
            "ident": ident,
            "directory": None,
            "app": None,
            "name": None,
            "vars": {},
            "tags": [],
        }

        # Check type
        if isinstance(config, str) and config:
            # If not empty string, on it's simplest form, we exect
            # to be the app name
            config = {"app": str(config)}
        elif isinstance(config, dict):
            pass
        elif not config:
            config = {}
        else:
            raise exc.PaasifyConfigError(f"Invalid config type: {type(config)}")

        out.update(config)
        if ident:
            out.update(
                {
                    "directory": ident,
                }
            )

        out["vars"] = out["vars"] or {}
        out["tags"] = out["tags"] or []

        return out

    @setup_once("setup_node")
    def setup_node(self):
        "Setup the pod"
        logger.info("Setup pod: %s", self)
        # self.vars = self.config.get("vars", {}) or {}
        # self.tags = self.config.get("tags", []) or []

    # High level methods
    # --------------------------------

    def get_varmgr(self):
        "Get varmgr"
        varmgr = super().get_varmgr()

        ret = {
            "ns_vars": self.ns.get_vars() if self.ns else {},
            "stack_vars": self.stack.get_vars(),
            "pod_vars": self.get_vars(),
        }

        varmgr.set_layer("ns_vars", ret["ns_vars"])
        varmgr.set_layer("stack_vars", ret["stack_vars"])
        varmgr.set_layer("pod_vars", ret["pod_vars"])

        return varmgr

    # Apps methods
    # --------------------------------

    @property
    @requires_setup_node("setup_app")
    def app(self):
        "Return app"
        return self._app

    @setup_once("setup_app")
    def setup_app(self):
        "Setup app"

        # Resolve app name
        app = None
        app_name = self.config.get("app")
        if app_name:
            app = self._build_resolve_app_name(app_name)

        self._app = app

    # Assembling methods
    # --------------------------------

    def pod_build(self, selector=None):
        "Assemble tests"
        assert selector is None, "Selector not supported for pod"

        print("Build pod", self.name, ~self.path)

        self.assemble()

        # pprint(self._build_filter_tags(["homepage", "traefik-svc"]))

    def _build_resolve_app_name(self, app_name):
        "Resolve app name from catalog"
        app_matches = self.catalog.resolve_app(app_name)
        if len(app_matches) > 1:
            app_idents = [app.ident for app in app_matches]
            msg = f"Multiple apps found for '{app_name}', keeping only the first one: {app_idents}"
            logger.info(msg)
        if len(app_matches) > 0:
            return app_matches[0]
        return None

    # def _build_filter_tags(self, app, tags):
    #     "Filter tags"
    #     # app_name = self.config.get("app")
    #     # app = self._build_resolve_app_name(app_name)

    #     # TODO: This is wrong, all collections should be asked
    #     all_jsonnet_tags = app.parent.get_jsonnet_files()

    #     matches = []
    #     for tag in all_jsonnet_tags:
    #         if tag.name in tags:
    #             matches.append(tag)
    #     return matches

    # @requires_setup_node("setup_app")
    def assemble(self, dry_run=False):
        "Assemble the pod - V1 support"

        app = self.app

        # Fetch app files
        tags = self.config.get("tags", [])
        docker_file_match = app.get_compose_file()
        app_vars = app.get_vars_files()

        new_tags = [TagConfigV1(config="_paasify", parent=self)]
        for tag in tags:
            ret_tag = TagConfigV1(config=tag, parent=self)
            # pprint(ret_tag.__dict__)
            new_tags.append(ret_tag)

        # tags = new_tags
        # pprint(tags)
        # assert False, "WIP"
        # docker_app_tag_files = app.get_extra_docker_files(tags)

        # Resolve tag files
        # jsonnet_app_tag_files =

        # out = self.ns.get_compose_files()
        # pprint(out)
        # assert False, "WIP"

        # Prepare tag database
        tags_db = {
            "jsonnet_collection_tag_files": app.collection.get_jsonnet_files(),
            "jsonnet_ns_tag_files": self.ns.get_jsonnet_files() if self.ns else [],
            "jsonnet_app_tag_files": app.get_jsonnet_files(),
            "jsonnet_local_tag_files": self.get_jsonnet_files(),
            # "docker_ns_tag_files": app.namespace.
            "docker_app_tag_files": app.get_compose_files(),
            "docker_local_tag_files": self.get_compose_files(),  # TODO: Add local tag files
        }

        tags_db_flat = []
        tag_processing_order = [
            "jsonnet_collection_tag_files",
            "jsonnet_ns_tag_files",
            "jsonnet_app_tag_files",
            "jsonnet_local_tag_files",
            "docker_app_tag_files",
            "docker_local_tag_files",
        ]
        for tag_type in tag_processing_order:
            tag_list = tags_db[tag_type]
            tags_db_flat.extend(tag_list)

        # tags_db_flat = flatten([value for value in tags_db.values()])
        tags_db_flat = {x.ident: x for x in tags_db_flat}

        # print("TAG PAYLOAD")
        # pprint(SimpleNamespace(**tags_db))
        # print("TAG PAYLOAD FLAT")
        # pprint(tags_db_flat)

        # Resolve and validatetags processing order
        tags_array = []
        for tag in new_tags:
            if not tag.ident in tags_db_flat:
                logger.warning("Tag %s not found in tags_db_flat", tag)
            else:
                ret = SimpleNamespace(tag=tags_db_flat[tag.ident], conf=tag.config)
                tags_array.append(ret)

        # print("TAG ARRAY")
        # pprint(tags_array)
        jsonnet_tags_array = [x for x in tags_array if isinstance(x.tag, JsonnetTagV1)]
        docker_tags_array = [
            x.tag for x in tags_array if isinstance(x.tag, ComposeTagV1)
        ]

        # print("JSONNET TAG ARRY")
        # pprint(jsonnet_tags_array)

        # Process pod variables
        varmgr = self.get_varmgr()
        vbuild = self.get_build_varmgr(varmgr, app=app, app_vars=app_vars)
        renderer = vbuild.get_renderer("scope_build")
        build_vars = renderer.render_values()

        # Process jsonnet global vars
        jsonnet_vars = dict(build_vars)
        jsonnet_result = {}
        for tag in jsonnet_tags_array:
            out = tag.tag.process_jsonnet_vars(vars=jsonnet_vars)
            final = {}
            final.update(out["def"])
            final.update(out["dyn"])
            jsonnet_vars.update(final)
            jsonnet_result.update(final)
        # pprint(jsonnet_result)
        # jsonnet_vars.update(out)

        # Reparse vars with varmgr once jsonnet tags are parsed
        vbuild.set_layer("build_default_vars", jsonnet_result)
        build_vars = vbuild.get_renderer("scope_build").render_values()

        # pprint(build_vars)

        # assert False, "WIP TAG DB, tag assert"

        # tags_payload ={
        #     "jsonnet_app_tag_files": self._build_filter_tags(app, tags),
        #     "docker_app_tag_files": app.get_extra_docker_files(tags),
        #     "jsonnet_local_tag_files": None,
        #     "docker_local_tag_files": None, # TODO: Add local tag files
        # }
        # print("TAG PAYLOAD")
        # pprint(SimpleNamespace(**tags_payload))
        # # assert False, "WIP"

        # varmgr = self.get_varmgr()
        # vbuild = self.get_build_varmgr(varmgr, ctx)
        # renderer = vbuild.get_renderer("scope_build")
        # build_vars = renderer.render_values()

        # Process .env file content
        dc_project_name = "_".join([self.stack.name, self.name])
        if self.ns:
            dc_project_name = "_".join([self.ns.name, dc_project_name])
        compose_settings = {
            "COMPOSE_PROJECT_NAME": dc_project_name,
            "COMPOSE_FILE": "docker-compose.yml",
            # "COMPOSE_PROFILES": "profile1,profile2",
            # "COMPOSE_CONVERT_WINDOWS_PATHS": "false",
            "COMPOSE_PATH_SEPARATOR": ":",  # ; on windows
            # "COMPOSE_IGNORE_ORPHANS": "false",
            "COMPOSE_REMOVE_ORPHANS": "true",  # False by default
            # "COMPOSE_PARALLEL_LIMIT": "10", # Not set by default
            # "COMPOSE_ANSI": "auto",
            # "COMPOSE_STATUS_STDOUT": "false",
            # COMPOSE_ENV_FILES=.env.envfile1, .env.envfile2
            "COMPOSE_ENV_FILES": ".env .env.secrets",
            # "COMPOSE_MENU": "true",
            # "COMPOSE_EXPERIMENTAL": "true",
        }
        self.write_env_file(
            compose_settings=compose_settings, build_vars=build_vars, dry_run=dry_run
        )

        # tmp = SimpleNamespace(
        #     # compose_files=([docker_file_match] + docker_app_tag_files),
        #     compose_files=([docker_file_match] + ctx.extra_docker_files),
        #     name=dc_project_name,
        #     build_vars=build_vars,
        #     dry_run=dry_run,
        # )
        # pprint(tmp)
        docker_app_tag_files = [+x.path for x in docker_tags_array]
        compose_files = [docker_file_match] + docker_app_tag_files
        # pprint(compose_files)
        # assert False, "WIP"

        # Process docker-compose.yml file
        compose_content = self.gen_compose_file(
            # compose_files=[docker_file_match] + docker_app_tag_files,
            compose_files=compose_files,
            name=dc_project_name,
            build_vars=build_vars,
            output="json",
        )
        compose_content_json = json.loads(compose_content)

        # print("COMPOSE CONTENT")
        # print(compose_content)

        # Process jsonnet plugins instances
        jsonnet_vars = dict(build_vars)
        jsonnet_result = {}
        loop_out = compose_content_json
        for tag in jsonnet_tags_array:
            conf = tag.conf
            tag = tag.tag
            # print("PROCESSING PLUGIN", tag.ident, conf)

            _config = dict(build_vars)
            _config.update(conf)
            out = tag.process_jsonnet_plugin(config=_config, docker_data=loop_out)
            # pprint(out)
            loop_out = out
            # pprint(tag.__dict__)

            # final = {}
            # final.update(out["def"])
            # final.update(out["dyn"])

        # print("FINAL")
        # pprint(loop_out)
        compose_content = to_yaml(loop_out)

        assert compose_content

        if not dry_run:
            docker_file_dest = self.path / "docker-compose.yml"
            logger.info("Write docker-compose.yml file: %s", docker_file_dest)
            write_file(docker_file_dest, compose_content)

    def gen_compose_file(
        self, compose_files=None, name=None, build_vars=None, output="json"
    ):
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

    def write_env_file(self, compose_settings, build_vars=None, dry_run=False):
        "Write .env file"

        env_content = "# File autogenerated by paasify, do not edit\n"
        env_content += "# =====================================\n\n"
        if compose_settings:
            env_content += "\n# Compose settings \n"
            env_content += "# ---------- \n\n"
            env_content += dict_to_env(compose_settings) + "\n"

        if build_vars:
            env_content += "\n# Variables \n"
            env_content += "# ---------- \n\n"
            env_content += (dict_to_env(dict(sorted(build_vars.items())))) + "\n"

        if compose_settings and not build_vars:
            logger.warning("No build vars, skipping env file creation")
            return

        if not dry_run:
            logger.info("Write env file: %s", self.path / ".env")
            write_file(self.path / ".env", env_content)
        else:
            logger.info("Dry run, not writing env file: %s", self.path / ".env")
        return env_content

    def get_build_varmgr(self, varmgr, app=None, app_vars=None):
        "Get build varmgr - V1 support"

        # tags = ctx.tags
        # app_vars = ctx.app_vars
        # app = ctx.app

        varmgr = self.get_varmgr()

        # Create environment file
        default_network = "network"
        default_service = None

        # V1 COMPAT
        stack_dir = +self.path
        default_vars = {
            "app_network_name": "default",
            "app_domain": "TOFIX_app_domain",
            "app_name": app.name,
            # "app_log_level": "DEBUG",
            # "app_log_access": "True",
            # "app_dir_conf": os.path.join(stack_dir, "conf"),
            # "app_dir_data": os.path.join(stack_dir, "data"),
            # "app_dir_logs": os.path.join(stack_dir, "logs"),
            # "app_dir_secrets": os.path.join(stack_dir, "secrets"),
            # "app_puid": 1000,
            # "app_pgid": 1000,
            # "app_tz": "America/Toronto",
            # "net_proxy": "net_proxy",
            # "prj_ns": self.ns.ident,
            # "app_fqdn": "TOFIX_app_fqdn",
            # "app_service": default_service,
            # "app_prot": "http",
            # "app_description": "NO DESCRIPTION",
            # "app_expose_ip": "0.0.0.0",
            # "app_expose_port": 80,
            # "app_expose_proto": "http",
            # "app_expose_host": None,
            # "app_expose_path": None,
            # "app_expose_tls": False,
            # "stack_app_path": self.stack.path.get_path(mode="abs"),
            # "app_ident": app.ident,
        }

        tags = ["DISABLED_TEMP"]

        # print("============================")
        runtime_vars = {
            "paasify_sep": "-",
            "paasify_sep_dir": os.sep,
            # See: https://www.docker.com/blog/announcing-compose-v2-general-availability/
            "paasify_sep_net": "_",
            "_prj_path": +self.path,
            # "_prj_domain": to_domain(self.ns.ident),
            "_prj_stack_path": +self.stack.path,
            # Colon is used here for easier to parsing for later ...
            "_prj_stack_tags": f":{':'.join(tags)}:",
            "_stack_name": self.stack.ident,
            "_stack_path_abs": self.path.get_path(mode="abs"),
            "_stack_path_abs2": self.stack.path.get_path(mode="abs"),
            "_stack_network": default_network,
            "_stack_service": default_service,
            # To report below as well
            "_stack_app_name": None,
            "_stack_app_dir": None,
            "_stack_app_path": None,
            "_stack_collection_app_path": None,
            # App extras
            # "_stack_app_name": os.path.basename(app.app_name),
            # "_stack_app_dir": app.app_name,
            # "_stack_app_path": app.get_app_path(),
            # Project namespace (DEFAULT CAN BE OVERRIDED BY NAMESPACE)
            "_prj_namespace": self.ident,  # deprecated because too long !
            "_prj_ns": self.ident,
        }
        if self.ns:
            runtime_vars.update(
                {
                    "_prj_namespace": self.ns.ident,  # deprecated because too long !
                    "_prj_ns": self.ns.ident,
                }
            )

        # runtime_vars.update(vars_dict)
        # pprint(runtime_vars)

        vbuild = RenderableStoreManager()
        vbuild.add_sources(
            [
                Source("runtime_vars", level=200, help="Runtime variables"),
                Source("pod_vars", level=500, help="Pod variables"),
                Source("stack_vars", level=700, help="Stack variables"),
                Source("ns_vars", level=900, help="Namespace variables"),
                Source("app_vars", level=1000, help="App variables"),
                Source("build_default_vars", level=2000, help="Pod variables"),
                Source("default_vars", level=9999, help="Default variables"),
            ]
        )
        vbuild.set_layer("runtime_vars", runtime_vars)
        vbuild.set_layer("pod_vars", varmgr.get_layer("pod_vars"))
        vbuild.set_layer("stack_vars", varmgr.get_layer("stack_vars"))
        vbuild.set_layer("ns_vars", varmgr.get_layer("ns_vars"))
        vbuild.set_layer("app_vars", app_vars)
        vbuild.set_layer("default_vars", default_vars)

        vbuild.set_scopes(
            {
                # "scope_ns": ["runtime_vars", "ns_vars", "default_vars"],
                # "scope_stack": [
                #     "runtime_vars",
                #     "stack_vars",
                #     "ns_vars",
                #     "default_vars",
                # ],
                "scope_build": [
                    "runtime_vars",
                    "pod_vars",
                    "stack_vars",
                    "ns_vars",
                    "app_vars",
                    "build_default_vars",
                    "default_vars",
                ],
            }
        )

        return vbuild

    # Other methods
    # --------------------------------
