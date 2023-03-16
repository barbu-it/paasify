# -*- coding: utf-8 -*-
"""
Stack components class

"""

import os
from pprint import pprint, pformat  # noqa: F401

import json
import _jsonnet
import anyconfig

from cafram.nodes import NodeList, NodeMap
from cafram.utils import (
    to_json,
    to_yaml,
    write_file,
    first,
    _exec,
)

from paasify.framework import PaasifyObj
import paasify.errors as error


# =======================================================================================
# Stack Assembler
# =======================================================================================


class StackDumper(PaasifyObj):
    "StackDumper for dumping data into files for troubleshooting purpose"

    def __init__(self, path, enabled=True):

        self.out_dir = path
        self.enabled = enabled

        if self.enabled:
            self.cleanup()

    def cleanup(self):
        "Cleanup target directory"
        path = self.out_dir

        if not os.path.exists(path):
            self.log.info(f"StackDumper created directory: {path}")
            os.makedirs(path)
        for file_ in os.listdir(path):
            rm_file = os.path.join(path, file_)
            self.log.notice(f"StackDumper removed file: {rm_file}")
            os.remove(rm_file)

    def dump(self, file_name, content, fmt=None):
        "Dump any data"

        if not self.enabled:
            return

        dest = os.path.join(self.out_dir, file_name)

        if fmt == "json":
            content = to_json(content)
        elif fmt in ["yml", "yaml"]:
            content = to_yaml(content)
        elif fmt in ["pprint", "pformat"]:
            content = pformat(content) + "\n"

        if not isinstance(content, str):
            content = str(content)

        self.log.info(f"Dumping data into: {dest}")
        write_file(dest, content)

    def show_diff(self):
        "Show a colored diff outpout between files"

        if not self.enabled:
            return

        print("==== Dump differential jsonnet output")
        path = os.path.realpath(self.out_dir)
        prev = os.path.join(path, "1-docker-compose.yml")
        print(_exec("tail", cli_args=["-n", "9999", prev]))
        for file_ in sorted(os.listdir(path)):
            if file_.startswith("2-") and file_.endswith("out.yml"):
                file_ = os.path.join(path, file_)
                opts = [
                    "--color=always",
                    "-u",
                    prev,
                    file_,
                ]
                out = _exec("diff", cli_args=opts, _ok_code=[0, 1])
                print(out)
                prev = file_


# =======================================================================================
# Stack Assembler
# =======================================================================================


class StackAssembler(PaasifyObj):
    "Object to manage stack assemblage"

    # Internal object:
    # all_tags
    # engine

    # Docker processors
    # ===========================
    def _get_docker_files(self, all_tags):
        "Retrieve the list of tags docker-files"

        # TODO: Deprecated this, this has already been done before somewhere in the process !

        docker_files = []
        for cand in all_tags:
            docker_file = cand.get("docker_file")
            if docker_file:
                docker_files.append(docker_file)
                self.log.info(f"Insert docker-compose: {docker_file}")

        return docker_files

    def assemble_docker_compose(
        self, all_tags, engine, env=None, dump_payload_log=False
    ):
        "Generate the docker-compose file"

        docker_files = self._get_docker_files(all_tags)

        # Report to user
        env = env or {}
        assert isinstance(env, dict), f"Got: {env}"

        if dump_payload_log:
            self.log.trace("Docker vars:")
            for key, val in sorted(env.items()):
                self.log.trace(f"  {key}: {val}")

        out = engine.assemble(docker_files, env=env)
        # Exception is too wide !
        # try:
        #    out = engine.assemble(docker_files, env=env)
        # except Exception as err:
        # # TOTEST => except sh.ErrorReturnCode as err:
        #    err = bin2utf8(err)
        #    # pylint: disable=no-member
        #    self.log.critical(err.txterr)
        #    raise error.DockerBuildConfig(
        #        f"Impossible to build docker-compose files: {err}"
        #    ) from err

        # Fetch output
        docker_run_content = out.stdout.decode("utf-8")
        docker_run_payload = anyconfig.loads(docker_run_content, ac_parser="yaml")
        return docker_run_payload

    # Vars processors
    # ===========================

    def process_jsonnet_exec(self, file, action, data, import_dirs=None):
        "Process jsonnet file"

        # Developper init
        import_dirs = import_dirs or []
        data = data or {}
        assert isinstance(data, dict), f"Data must be dict, got: {data}"
        # assert len(import_dirs) > 2, f"Missing import dirs, got: {import_dirs}"

        # TODO: Enforce jsonnet API
        # assert action in [
        #     "metadata",
        #     "vars_default",
        #     "vars_override",
        #     "process_globals", # Testing WIP
        #     "process_transform", # Testing WIPP
        #     "docker_override",
        # ], f"Action not supported: {action}"

        # Prepare input variables
        mod_ident = os.path.splitext(os.path.basename(file))[0]
        ext_vars = {
            "parent": json.dumps(mod_ident),
            "action": json.dumps(action),
        }
        for key, val in data.items():
            ext_vars[key] = json.dumps(val)

        def try_path(dir_, rel):
            "Helper function to load a jsonnet file into memory for _jsonnet"

            if not rel:
                return None, None
                # raise RuntimeError("Got invalid filename (empty string).")

            if rel[0] == "/":
                full_path = rel
            else:
                full_path = os.path.join(dir_, rel)

            if full_path[-1] == "/":
                return None, None
                # raise RuntimeError("Attempted to import a directory")

            if not os.path.isfile(full_path):
                return full_path, None
            with open(
                full_path,
                encoding="utf-8",
            ) as file_:
                return full_path, file_.read()

        # Jsonnet import callback
        def import_callback(dir_, rel):
            "Helper function to load a jsonnet libraries in lookup paths"

            test_dirs = [dir_] + import_dirs
            for test_dir in test_dirs:
                full_path, content = try_path(test_dir, rel)
                self.log.trace(f"Load '{rel}' jsonnet from: {full_path}")
                if content:
                    return full_path, content.encode()

            test_dirs = " ".join(test_dirs)
            raise RuntimeError(
                f"Jsonnet file not found '{rel}' in any of these paths: {test_dirs}"
            )

        # Process jsonnet tag
        self.log.trace(f"Process jsonnet: {file} (action={action})")
        try:
            # pylint: disable=c-extension-no-member
            result = _jsonnet.evaluate_file(
                file,
                ext_vars=ext_vars,
                import_callback=import_callback,
            )
        except RuntimeError as err:
            self.log.critical(f"Can't parse jsonnet file: {file}")
            raise error.JsonnetBuildFailed(err)

        # Return python object from json output
        result = json.loads(result)
        return result


# =======================================================================================
# Stack Apps
# =======================================================================================


class StackApp(NodeMap, PaasifyObj):
    "Stack Applicationk Object"

    # conf_logger = "paasify.cli.stack_app"

    conf_default = {
        "app": None,
        "app_source": None,
        "app_path": None,
        "app_name": None,
    }

    @property
    def name(self):
        "App name attribute"
        return self.app_name

    # def node_hook_init(self, **kwargs):
    def node_hook_init(self):

        # Future: let's propagate from the top instead ...
        # parents = self.get_parents()
        # stack = parents[1]
        # prj = parents[3]
        self.stack = self._node_parent
        self.prj = self.stack._node_parent._node_parent
        self.sources = self.prj.sources

        self.app_dir = None

    def node_hook_transform(self, payload):

        if isinstance(payload, str):
            payload = {"app": payload}

        app_def = payload.get("app")
        app_path = payload.get("app_path")
        app_source = payload.get("app_source")
        app_name = payload.get("app_name")

        app_split = app_def.split(":", 2)

        if len(app_split) == 2:
            app_source = app_source or app_split[0] or "default"
            app_path = app_path or app_split[1]
        else:
            # Get from default namespace
            app_name = app_source or app_split[0] or "default"
            app_source = "default"
            app_path = app_name
        app_def = f"{app_source}:{app_path}"

        if not app_name:
            app_name = os.path.split(app_path)[-1]

        result = {
            "app": app_def,
            "app_path": app_path,
            "app_source": app_source,
            "app_name": app_name,
        }

        return result

    def get_app_source(self):
        "Return app source"

        app_source = self._node_conf_parsed["app_source"] or None
        target = self._node_conf_parsed["app_path"] or self._node_conf_parsed["app_name"]
        src = self.prj.sources.get_app_source(target, source=app_source)
        return src

    def get_app_path(self):
        "Return app path"

        src = self.get_app_source()
        target = self._node_conf_parsed["app_path"] or self._node_conf_parsed["app_name"]
        ret = os.path.join(src.path, target)
        return ret


# =======================================================================================
# Stack Tag schemas
# =======================================================================================

stack_name_pattern = {
    "title": "Short form",
    "description": (
        "Just pass the tag you want to apply as string."
        " This form does not allow jsonnet ovar override"
    ),
    "type": "string",
    "oneOf": [
        {
            "title": "Reference collection app",
            "description": (
                "Reference a tag from a specific collection."
                " This form does not allow jsonnet ovar override"
            ),
            "pattern": "^.*:.*$",
        },
        {
            "title": "Direct or absolute app path",
            "description": ("Reference a tag from a specific collection."),
            "pattern": ".*/[^:]*",
        },
        {
            "title": "Tag",
            "description": ("Will find the best matvhing tag."),
            "pattern": "^.*$",
        },
    ],
}


stack_ref_kind_defs = [
    {
        "title": "With value",
        "description": "Pass extra vars for during jsonet tag processing.",
        "type": "object",
    },
    {
        "title": "Without value",
        "description": ("No vars are added for this jsonnet tag processing."),
        "type": "null",
    },
]
stack_ref_defs = {
    "[~].*": {
        "title": "Disabled Tag: ~$tag_name",
        "description": (
            "Completely disable a tag from the processing list, whatever how many instances there are."
        ),
        "oneOf": stack_ref_kind_defs,
        "default": {},
    },
    "^.*:.*$": {
        "title": "Collection tag: $collection_name:$tag_name",
        "description": (
            "Reference a tag from a specific collection."
            "See: Specific tag documentation for further informations."
        ),
        "oneOf": stack_ref_kind_defs,
        "default": {},
    },
    # ".*/[^:]*": {
    #     "title": "Absolute tag: $tag_path",
    #     "description": (
    #         "Reference a tag from a absolute app path."
    #     ),
    # },
    ".*": {
        "title": "Tag name: $tag_name",
        "description": (
            "Will find the best matching tag."
            "See: Specific tag documentation for further informations."
        ),
        "oneOf": stack_ref_kind_defs,
        "default": {},
    },
}


class StackTag(NodeMap, PaasifyObj):
    """Paasify Stack object"""

    conf_schema = {
        # "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "StackTag configuration",
        "description": (
            "Tag definition. It support two formats at the same time: as string or dict."
            " If the name is prefixed with a `!`, then it is removed from the"
            " processing list (both vars, docker-file and jsonnet processing)."
        ),
        "oneOf": [
            {
                "title": "As string",
                "description": (
                    "Just pass the tag you want to apply as string."
                    " This form does not allow jsonnet ovar override"
                ),
                "type": "string",
                "default": "",
                "examples": [
                    {
                        "tags": [
                            "my_tagg",
                            "~my_prefix_tag",
                            "my_collection:my_prefix_tag",
                        ],
                    },
                ],
                "oneOf": [
                    {
                        "title": stack["title"],
                        "description": stack["description"],
                        "pattern": stack_pattern,
                    }
                    for stack_pattern, stack in stack_ref_defs.items()
                ],
            },
            {
                "title": "As object",
                "description": (
                    "Define a tag. The key represent the name of the"
                    " tag, while it's value is passed as vars during"
                    " jsonnet processing. This form allow jsonnet ovar override"
                ),
                "type": "object",
                "default": {},
                "examples": [
                    {
                        "tags": [
                            {
                                "other_tag": {
                                    "specific_conf": "val1",
                                }
                            },
                            {"my_collection:another_tag": None},
                            {
                                "~ignore_this_tag": {
                                    "specific_conf": "val1",
                                }
                            },
                        ],
                    },
                ],
                "minProperties": 1,
                "maxProperties": 1,
                # "additionalProperties": False,
                "patternProperties": stack_ref_defs,
            },
        ],
    }

    conf_ident = "{self.name}={self.vars}"

    conf_children = [
        {
            "key": "name",
            "cls": str,
        },
        {
            "key": "vars",
        },
    ]

    # Place to store list of candidates
    jsonnet_candidates = None
    docker_candidates = None

    # Object shortcuts
    stack = None
    prj = None
    app = None

    def node_hook_transform(self, payload):

        # Init parent objects
        self.stack = self.get_parent().get_parent()
        self.prj = self.stack.get_parent().get_parent()
        self.app = self.prj.get_parents()

        # Transform input
        result = {
            "name": None,
            "vars": {},
        }
        if isinstance(payload, str):
            result["name"] = payload

        elif isinstance(payload, dict):

            keys = list(payload.keys())
            if len(keys) == 1:
                # TODO: replace this by a common function !
                for key, val in payload.items():
                    result["name"] = key
                    result["vars"] = val
            elif len(keys) == 0:
                raise Exception(f"Missing tag name: {payload}")
            else:
                result.update(payload)

        else:
            raise Exception(f"Not supported type: {payload}")

        assert result["name"]
        return result


class StackTagMgr(NodeList, PaasifyObj):
    "Manage Stack Tags"

    conf_schema = {
        # "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Paasify Stack Tags configuration",
        "description": "Determine a list of tags to apply",
        "oneOf": [
            {
                "title": "List of tags",
                "description": (
                    "Define a list of tags. You can interact in few ways with"
                    " tags. Tags can support boths syntaxes at the same time."
                ),
                "type": "array",
                "default": [],
                "additionalProperties": StackTag.conf_schema,
                # "items": StackTag.conf_schema,
                "examples": [
                    {
                        "tags": [
                            "my_tagg",
                            "~my_prefix_tag",
                            "my_collection:my_prefix_tag",
                            {
                                "other_tag": {
                                    "specific_conf": "val1",
                                }
                            },
                            {"my_collection:another_tag": None},
                            {
                                "~ignore_this_tag": {
                                    "specific_conf": "val1",
                                }
                            },
                        ],
                    },
                ],
            },
            {
                "title": "Unset",
                "description": "Do not declare any tags",
                "type": "null",
                "default": None,
                "examples": [
                    {
                        "tags": None,
                    },
                ],
            },
        ],
    }

    conf_children = StackTag
    module = "paasify.cli"

    def node_hook_transform(self, payload):

        # Fetch tag lists
        tag_stack_list = payload["raw"]
        tag_prefix = payload["tag_prefix"]
        tag_suffix = payload["tag_suffix"]

        # Process keys (before parsing :/ )
        tag_stack_keys = [tag for tag in tag_stack_list if isinstance(tag, str)]
        tag_stack_keys = tag_stack_keys + [
            first(tag.keys()) for tag in tag_stack_list if isinstance(tag, dict)
        ]

        # Remove duplicates tags
        tag_items = []
        for item in tag_prefix:
            if item not in tag_stack_keys:
                tag_items.append(item)
        tag_items.extend(tag_stack_list)
        for item in tag_suffix:
            if item not in tag_stack_keys:
                tag_items.append(item)

        return tag_items

    def node_hook_final(self):
        "Remove disabled tags"

        markers = "^"
        excluded_tags = [
            tag.name for tag in self._nodes if tag.name.startswith(markers)
        ]
        if excluded_tags:
            self.log.debug(f"Disabling tags: {excluded_tags}")
        for excluded in excluded_tags:
            clean = excluded[1:]
            xclude = [excluded, clean]
            self._nodes = [tag for tag in self._nodes if tag.name not in xclude]
