"Manage apps/pods"

import os
import logging
from pprint import pprint
import sh

from types import SimpleNamespace

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
    to_domain,
    flatten,
)
from paasify_v4.models.core_catalog import PaasifyCatalog

from paasify_v4.engine_docker.compose_app import ComposedApp
import paasify_v4.exception as exc

from paasify_v4.lib.shexec import shexec

logger = logging.getLogger(__name__)


# Pod classes
# ================================================


class PaasifyPod(VarMgrNodeMixin, AppNode):
    "Base class for all Paasify pods"

    paasify_type = "pod"

    def __init__(self, ident, parent=None, name=None, raw_config=None, path=None):
        # assert isinstance(parent, PaasifyStack)
        super().__init__(ident, parent)

        self._name = name or ident.split("/", maxsplit=1)[0]

        self._path = PathAnchor(path, parent=parent.path)
        self.config = self.build_config(raw_config, ident=ident)
        self._app = None

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

    # @setup_once("setup_node")
    def get_vars(self):
        "Get vars"
        return self.config.get("vars", {}) or {}

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


    # Assembling methods
    # --------------------------------

    # @requires_setup_node("setup_app")
    def assemble(self, dry_run=False):
        "Assemble the pod"

        # Resolve app name
        app_name = self.config.get("app")
        app_matches = self.catalog.resolve_app(app_name)
        if len(app_matches) > 1:
            app_idents = [app.ident for app in app_matches]
            msg = f"Multiple apps found for '{app_name}', keeping only the first one: {app_idents}"
            logger.info(msg)
        app = app_matches[0]

        # Fetch app files
        tags = self.config.get("tags", [])
        docker_file_match = app.get_compose_files()
        app_vars = app.get_vars_files()
        extra_docker_files = app.get_extra_docker_files(tags)

        # Process variables
        ctx = SimpleNamespace(
            tags=tags,
            app_vars=app_vars,
            extra_docker_files=extra_docker_files,
            app=app,
        )
        varmgr = self.get_varmgr()
        vbuild = self.get_build_varmgr(varmgr, ctx)
        renderer = vbuild.get_renderer("scope_build")
        build_vars = renderer.render_values()

        # Process .env file content
        dc_project_name = "_".join([self.ns.name, self.stack.name, self.name])
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
            compose_settings=compose_settings, 
            build_vars=build_vars, dry_run=dry_run)

        # Process docker-compose.yml file
        self.write_compose_file(
            compose_files=[docker_file_match] + extra_docker_files, 
            name=dc_project_name, 
            build_vars=build_vars, 
            dry_run=dry_run)


    def write_compose_file(self, compose_files=None, name=None, build_vars=None, dry_run=False):
        "Write docker-compose.yml file"

        compose_files = compose_files or []

        # Process docker-compose.yml file
        docker_file_dest = self.path / "docker-compose.yml"

        comp_app = ComposedApp(
            name=name,
            project_dir=self.path.get_path(),
            compose_files=compose_files
        )

        # TODO: To set back interpolate to false, there is an issue on
        # volumes names VS binds
        compose_content = comp_app.assemble(interpolate=True, normalize=False) 
        # compose_content = comp_app.assemble(interpolate=False, normalize=False)
        for varname in comp_app.get_variables2():
            if not varname in build_vars:
                logger.error("Missing variable: %s", varname)
                # logger.error("  %s", conf)


        if not dry_run:
            logger.info(
                "Write docker-compose.yml file: %s", self.path / "docker-compose.yml"
            )
            write_file(docker_file_dest, compose_content)


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




    def get_build_varmgr(self, varmgr, ctx):
        "Get build varmgr"

        tags = ctx.tags
        app_vars = ctx.app_vars
        app = ctx.app

        varmgr = self.get_varmgr()

        # Create environment file
        default_network = "network"
        default_service = None

        # V1 COMPAT
        stack_dir = +self.path
        default_vars = {
            "app_network_name": "default",
            "app_log_level": "DEBUG",
            "app_log_access": "True",
            "app_dir_conf": os.path.join(stack_dir, "conf"),
            "app_dir_data": os.path.join(stack_dir, "data"),
            "app_dir_logs": os.path.join(stack_dir, "logs"),
            "app_dir_secrets": os.path.join(stack_dir, "secrets"),
            "app_puid": 1000,
            "app_pgid": 1000,
            "app_tz": "America/Toronto",
            "net_proxy": "net_proxy",
            "prj_ns": self.ns.ident,
            "app_fqdn": "TOFIX_app_fqdn",
            "app_domain": "TOFIX_app_domain",
            "app_expose_ip": "0.0.0.0",
            "app_expose_port": 80,
            "app_expose_proto": "http",
            "app_expose_host": None,
            "app_expose_path": None,
            "app_expose_tls": False,
            "stack_app_path": self.stack.path.get_path(mode="abs"),

            "app_name": app.name,
            "app_ident": app.ident,
        }

        # print("============================")
        runtime_vars = {
            "paasify_sep": "-",
            "paasify_sep_dir": os.sep,
            # See: https://www.docker.com/blog/announcing-compose-v2-general-availability/
            "paasify_sep_net": "_",
            "_prj_path": +self.path,
            "_prj_namespace": self.ns.ident,  # deprecated because too long !
            "_prj_ns": self.ns.ident,
            # "_prj_domain": to_domain(self.ns.ident),
            "_prj_stack_path": +self.stack.path,
            # Colon is used here for easier to parsing for later ...
            "_prj_stack_tags": f":{':'.join(tags)}:",
            "_stack_name": self.stack.ident,
            "_stack_path_abs": self.stack.path.get_path(mode="abs"),
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
        }
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
                    "default_vars",
                ],
            }
        )

        return vbuild
    

    # Other methods
    # --------------------------------