"""
Project library

This handle the project entity.

This library provides two classes:

* PaasifyProjectConfig: A project config
* PaasifyProject: A project instance


Example:
``` py title="test.py"
from paasify.projects import PaasifyProject

prj = PaasifyProject.discover_project()
prj.dump()
```
"""

# pylint: disable=logging-fstring-interpolation


import os

from pprint import pprint
import anyconfig

from cafram.nodes import NodeMap

import paasify.errors as error
from paasify.engines import EngineDetect
from paasify.sources import SourcesManager
from paasify.framework import (
    PaasifyObj,
    PaasifyConfigVars,
)
from paasify.common import list_parent_dirs, find_file_up, get_paasify_pkg_dir

from paasify.stacks2 import PaasifyStackTagManager, PaasifyStackManager


ALLOW_CONF_JUNK = False


class PaasifyProjectConfig(NodeMap, PaasifyObj):
    "Paasify Project Configuration"

    conf_default = {
        "namespace": None,
        "vars": {},
        "tags": [],
        "tags_suffix": [],
        "tags_prefix": [],
    }

    conf_children = [
        {
            "key": "namespace",
        },
        {
            "key": "vars",
            "cls": PaasifyConfigVars,
        },
        # {
        #     "key": "tags",
        #     "cls": list,
        #     #"cls": PaasifyStackTagManager,
        # },
        # {
        #     "key": "tags_prefix",
        #     "cls": list,
        #     #"cls": PaasifyStackTagManager,
        # },
        # {
        #     "key": "tags_suffix",
        #     "cls": list,
        #    # "cls": PaasifyStackTagManager,
        # },
    ]

    conf_schema = {
        # "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Paasify Project settings",
        "description": (
            "Configure main project settings. It provides global settings"
            " but also defaults vars and tags for all stacks."
        ),
        "oneOf": [
            {
                "type": "object",
                "additionalProperties": ALLOW_CONF_JUNK,
                "title": "Project configuration",
                "description": (
                    "Configure project as a dict value. "
                    "Most of these settings are overridable via environment vars."
                ),
                "default": {},
                "properties": {
                    "namespace": {
                        "title": "Project namespace",
                        "description": (
                            "Name of the project namespace. If not"
                            " set, defaulted to directory name"
                        ),
                        "oneOf": [
                            {
                                "title": "None",
                                "description": "Defaulted by the project dir name",
                                "type": "null",
                            },
                            {
                                "title": "String",
                                "description": "Custom namespace name string",
                                "type": "string",
                            },
                        ],
                    },
                    "vars": PaasifyConfigVars.conf_schema,
                    "tags": PaasifyStackTagManager.conf_schema,
                    "tags_suffix": PaasifyStackTagManager.conf_schema,
                    "tags_prefix": PaasifyStackTagManager.conf_schema,
                },
                "examples": [
                    {
                        "config": {
                            "namespace": "my_ns1",
                            "vars": [{"my_var1": "my_value1"}],
                            "tags": ["tag1", "tag2"],
                        },
                    }
                ],
            },
            {
                "type": "null",
                "title": "Empty",
                "description": "Use automatic conf if not set. You can still override conf values with environment vars.",
                "default": None,
                "examples": [
                    {
                        "config": None,
                    },
                    {
                        "config": {},
                    },
                ],
            },
        ],
    }


class PaasifyProjectRuntime(NodeMap, PaasifyObj):
    "Paasify Runtime Object (deprecated)"

    conf_schema = {
        # TODO: "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "title": "Paasify Project settings",
        "additionalProperties": False,
        "properties": {
            "default_source": {
                "title": "",
                "description": "",
                "type": "string",
            },
            "cwd": {
                "title": "",
                "description": "",
                "type": "string",
            },
            "working_dir": {
                "title": "",
                "description": "",
                "oneOf": [
                    {"type": "string"},
                    {"type": "null"},
                ],
            },
            "engine": {
                "title": "Docker backend engine",
                "oneOf": [
                    {
                        "description": "Docker engine",
                        "type": "string",
                    },
                    {
                        "description": "Automatic",
                        "type": "null",
                    },
                ],
            },
            "filenames": {
                "oneOf": [
                    {
                        "title": "List of file to lookup",
                        "description": "List of string file names to lookup paasify.yaml files",
                        "type": "array",
                        "items": {
                            "type": "string",
                        },
                    },
                ],
            },
        },
    }

    conf_default = {
        "load_file": None,
        "root_hint": None,
        # TO CONFIRM
        "default_source": "default",
        "cwd": os.getcwd(),
        # "working_dir": os.getcwd(),
        # "working_dir": ".",
        "working_dir": None,
        "engine": None,
        "filenames": ["paasify.yml", "paasify.yaml"],
        "relative": None,
    }

    def node_hook_transform(self, payload):
        """Init PassifyRuntime"""

        # Allow config as string !
        if isinstance(payload, str):
            root_hint = payload
            payload = {
                "root_hint": root_hint,
                "load_file": True,
            }

        # Create default config
        result = {}
        result = dict(self.conf_default)
        result.update(payload)

        # The payload is a dir or a config file
        root_hint = result.get("root_hint")
        filenames = result.get("filenames")
        _payload1 = self.get_ctx(root_hint, config_files=filenames)
        result.update(_payload1)

        # Build default runtime from root path
        root_path = result["root_path"]

        paasify_source_dir = get_paasify_pkg_dir()
        paasify_plugins_dir = os.path.join(paasify_source_dir, "assets", "plugins")
        private_dir = os.path.join(root_path, ".paasify")
        collection_dir = os.path.join(private_dir, "collections")
        jsonnet_dir = os.path.join(private_dir, "plugins")

        _payload2 = {
            "paasify_source_dir": paasify_source_dir,
            "paasify_plugins_dir": paasify_plugins_dir,
            "project_private_dir": private_dir,
            "project_collection_dir": collection_dir,
            "project_jsonnet_dir": jsonnet_dir,
        }
        result.update(_payload2)

        # Allow user to override parts
        result.update(payload)
        return result

    @classmethod
    def get_project_path2(cls, path, filenames=None):
        "Find the closest paasify config file"

        # if not path.startswith('/'):

        filenames = filenames or cls.filenames
        # filenames = self._node_root.config.filenames

        paths = list_parent_dirs(path)
        result = find_file_up(filenames, paths)

        return result

    @staticmethod
    def get_ctx(project_hint, config_files=None, cwd=None, relative=None):
        "Return a list of directory context"

        config_files = config_files or ["paasify.yml", "paasify.yaml"]
        cwd = cwd or os.getcwd()

        # Autofind config file in parents if None
        if project_hint is None:
            # Show relative by default when project_hint is None
            relative = True if relative is None else relative

            try:
                project_hint = PaasifyProjectRuntime.get_project_path2(
                    cwd, filenames=config_files
                )[0]
            except IndexError as err:
                config_files = "' or '".join(config_files)
                msg = f"Impossible to find any '{config_files}' in '{cwd}', or in above directories."
                raise error.ProjectNotFound(msg) from err

        # Check the project root:
        if os.path.isdir(project_hint):
            root_path = project_hint
            # TODO: Lookup for candidates instead taking the first
            config_file_name = config_files[0]

        elif os.path.isfile(project_hint):
            root_path = os.path.dirname(project_hint)
            config_file_name = os.path.basename(project_hint)
        else:
            msg = f"Impossible to find paasify project in: {project_hint}"
            raise error.ProjectNotFound(msg)

        assert root_path

        # Get more context
        if relative is None:
            relative = not os.path.isabs(project_hint)
        project_rel = os.path.relpath(root_path, start=cwd)
        project_abs = os.path.abspath(root_path)

        # Check if cwd inside
        sub_dir = None
        if project_abs != cwd and project_abs in cwd:
            sub_dir = cwd.replace(project_abs, "").strip("/")
        # elif project_abs != cwd:
        #     relative = False

        # Convert root_path
        root_path = project_rel if relative else project_abs

        result = {
            "namespace": os.path.basename(project_abs),
            "root_path": root_path,
            "config_file": config_file_name,
            "config_file_path": os.path.join(root_path, config_file_name),
            "relative": relative,
            "cwd": cwd,
            "sub_dir": sub_dir,
        }
        return result


class PaasifyProject(NodeMap, PaasifyObj):
    "Paasify Project instance"

    conf_default = {
        "_runtime": {},
        "config": {},
        "sources": [],
        "stacks": [],
    }

    conf_children = [
        {
            "key": "config",
            "cls": PaasifyProjectConfig,
        },
        {
            "key": "sources",
            "cls": SourcesManager,
        },
        {
            "key": "stacks",
            "cls": PaasifyStackManager,
        },
    ]

    conf_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "title": "Paasify",
        "description": "Main paasify project settings. This defines the format of `paasify.yml`.",
        "additionalProperties": ALLOW_CONF_JUNK,
        "examples": [
            {
                "config": {
                    "tags_prefix": ["_paasify"],
                    "vars": {
                        "app_domain": "devbox.192.168.186.129.nip.io",
                        "app_expose_ip": "192.168.186.129",
                        "app_tz": "Europe/Paris",
                        "top_var1": "My value",
                        "top_var2": "TOP VAR1=> ${top_var1}",
                    },
                },
                "sources": [
                    {"default": {"url": "https://github.com/user/docker-compose.git"}}
                ],
                "stacks": [
                    {
                        "app": "default:traefik",
                        "path": "traefik",
                        "tags": [
                            "ep_http",
                            "expose_admin",
                            "debug",
                            {
                                "traefik-svc": {
                                    "traefik_net_external": False,
                                    "traefik_svc_port": "8080",
                                }
                            },
                        ],
                    },
                    {
                        "app": "default:minio",
                        "env": [
                            {"app_admin_passwd": "MY_PASS"},
                            {"app_image": "quay.io/minio/minio:latest"},
                        ],
                        "tags": [
                            {
                                "traefik-svc": {
                                    "traefik_svc_name": "minio-api",
                                    "traefik_svc_port": 9000,
                                }
                            },
                            {
                                "traefik-svc": {
                                    "traefik_svc_name": "minio-console",
                                    "traefik_svc_port": 9001,
                                }
                            },
                        ],
                    },
                    {"app": "default:authelia", "tags": ["traefik-svc"]},
                    {"app": "default:librespeed", "tags": ["traefik-svc"]},
                ],
            },
        ],
        "default": {},
        "properties": {
            "config": {
                "type": "object",
                "description": "See: schema prj_config",
            },
            "sources": {
                "type": "object",
                "description": "See: schema prj_sources",
            },
            "stacks": {
                "type": "array",
                "description": "See: schema prj_stacks",
            },
            "_runtime": {
                "title": "Project runtime variables",
                "type": "object",
                "description": "Internal object to pass context variables, internal use only or for troubleshooting purpose",
            },
        },
    }

    ident = "PaasifyProject"
    engine_cls = None
    runtime = None

    def node_hook_transform(self, payload):
        "Init configuration Project"

        # Create runtime instance child
        _runtime = payload.get("_runtime") or payload
        self.runtime = PaasifyProjectRuntime(
            parent=self, payload=_runtime, ident="ProjectRuntime"
        )

        # Inject payload
        if self.runtime.load_file is not False:
            self.log.debug(f"Load file: {self.runtime.config_file_path}")
            _payload = anyconfig.load(self.runtime.config_file_path)
            payload.update(_payload)

        # Create engine
        if not self.engine_cls:
            engine_name = self.runtime.engine or None
            self.engine_cls = EngineDetect().detect(engine=engine_name)

        return payload
