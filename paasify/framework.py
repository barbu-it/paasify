# -*- coding: utf-8 -*-
"Paasify Framework Libary"


# pylint: disable=logging-fstring-interpolation

import os
import logging


from pprint import pprint  # noqa: F401


from cafram.nodes import NodeList, NodeMap, NodeDict
from cafram.base import MixInLog, Base

from cafram.utils import (
    # to_domain,
    first,
    merge_dicts,
)

import paasify.errors as error
from paasify.common import filter_existing_files

_log = logging.getLogger()
_first = first


class PaasifyObj(Base, MixInLog):
    "Default Paasify base object"

    module = "paasify.cli"
    conf_logger = None
    log = _log

    def __init__(self, *args, **kwargs):

        # Manually load classe
        Base.__init__(self, *args, **kwargs)
        MixInLog.__init__(self, *args, **kwargs)

        # Other things
        # super().__init__(*args, **kwargs)


class PaasifySimpleDict(NodeMap, PaasifyObj):
    "Simple Paaisfy Configuration Dict"

    conf_default = {}


class PaasifyConfigVar(NodeMap, PaasifyObj):
    "Simple Paaisfy Configuration Var Dict"

    conf_ident = "{self.name}={self.value}"
    conf_default = {
        "name": None,
        "value": None,
    }

    # conf_logger = "paasify.cli.ConfigVar"

    conf_schema = {
        "title": "Variable definition as key/value",
        "description": "Simple key value variable declaration, under the form of: {KEY: VALUE}. This does preserve value type.",
        "type": "object",
        "propertyNames": {"pattern": "^[A-Za-z_][A-Za-z0-9_]*$"},
        "minProperties": 1,
        "maxProperties": 1,
        # "additionalProperties": False,
        "patternProperties": {
            "^[A-Za-z_][A-Za-z0-9_]*$": {
                # ".*": {
                "title": "Environment Key value",
                "description": "Value must be serializable type",
                # "oneOf": [
                #    {"title": "As string", "type": "string"},
                #    {"title": "As boolean", "type": "boolean"},
                #    {"title": "As integer", "type": "integer"},
                #    {
                #        "title": "As null",
                #        "description": "If set to null, this will remove variable",
                #        "type": "null",
                #    },
                # ],
            }
        },
    }

    def node_hook_transform(self, payload):

        result = None
        if isinstance(payload, str):
            value = payload.split("=", 2)
            result = {
                "name": value[0],
                "value": value[1],
            }
        if isinstance(payload, dict):
            if "name" in payload and "value" in payload and len(payload.keys()) == 2:
                result = {
                    "name": payload["name"],
                    "value": payload["value"],
                }

            elif len(payload.keys()) == 1:
                for key, value in payload.items():
                    result = {
                        "name": key,
                        "value": value,
                    }

        if result is None:
            raise Exception(f"Unsupported type {type(payload)}: {payload}")

        return result


vardef_schema_complex = {
    "description": "Environment configuration. Paasify leave two choices for the configuration, either use the native dict configuration or use the docker-compatible format",
    "oneOf": [
        merge_dicts(
            PaasifyConfigVar.conf_schema,
            {
                "examples": [
                    {
                        "env": [
                            {"MYSQL_ADMIN_USER": "MyUser"},
                            {"MYSQL_ADMIN_DB": "MyDB"},
                        ]
                    },
                ],
            },
        ),
        {
            "title": "Variable definition as string (Compat)",
            "description": "Value must be a string, under the form of: KEY=VALUE. This does not preserve value type.",
            "type": "string",
            "pattern": "^[A-Za-z_][A-Za-z0-9_]*=.*$",
            "examples": [
                {
                    "env": [
                        "MYSQL_ADMIN_USER=MyUser",
                        "MYSQL_ADMIN_DB=MyDB",
                    ]
                },
            ],
        },
    ],
}


class PaasifyConfigVars(NodeList, PaasifyObj):
    "Paasify Project configuration object"

    conf_children = PaasifyConfigVar

    conf_schema = {
        # "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Environment configuration",
        "description": (
            "Environment configuration. Paasify leave two choices for the "
            "configuration, either use the native dict configuration or use the "
            "docker-compatible format"
        ),
        "oneOf": [
            {
                "title": "Env configuration as list",
                "description": (
                    "Configure variables as a list. This is the recommended way as"
                    "it preserves the variable parsing order, useful for templating. This format "
                    "allow multiple configuration format."
                ),
                "type": "array",
                "default": [],
                "additionalProperties": vardef_schema_complex,
                "examples": [
                    {
                        "env": [
                            # "MYSQL_ADMIN_DB=MyDB",
                            {"MYSQL_ADMIN_USER": "MyUser"},
                            {"MYSQL_ADMIN_DB": "MyDB"},
                            {"MYSQL_ENABLE_BACKUP": True},
                            {"MYSQL_BACKUPS_NODES": 3},
                            {"MYSQL_NODE_REPLICA": None},
                            "MYSQL_WELCOME_STRING=Is alway a string",
                        ],
                    },
                ],
            },
            {
                "title": "Env configuration as dict (Compat)",
                "description": (
                    "Configure variables as a dict. This option is only proposed for "
                    "compatibility reasons. It does not preserve the order of the variables."
                ),
                "type": "object",
                "default": {},
                # "patternProperties": {
                #    #".*": { "properties": PaasifyConfigVar.conf_schema, }
                #    ".*": { "properties": vardef_schema_complex , }
                # },
                "propertyNames": {"pattern": "^[A-Za-z_][A-Za-z0-9_]*$"},
                # "additionalProperties": PaasifyConfigVar.conf_schema,
                "examples": [
                    {
                        "env": {
                            "MYSQL_ADMIN_USER": "MyUser",
                            "MYSQL_ADMIN_DB": "MyDB",
                            "MYSQL_ENABLE_BACKUP": True,
                            "MYSQL_BACKUPS_NODES": 3,
                            "MYSQL_NODE_REPLICA": None,
                        }
                    },
                ],
            },
            {
                "title": "Unset",
                "description": ("Do not define any vars"),
                "type": "null",
                "default": None,
                "examples": [
                    {
                        "env": None,
                    },
                    {
                        "env": [],
                    },
                    {
                        "env": {},
                    },
                ],
            },
        ],
    }

    def node_hook_transform(self, payload):

        result = []
        if not payload:
            pass
        elif isinstance(payload, dict):
            for key, value in payload.items():
                var_def = {key: value}
                result.append(var_def)
        elif isinstance(payload, list):
            result = payload

        # elif isinstance(payload, str):
        #         value = payload.split("=", 2)
        #         result = {
        #             "name": value[0],
        #             "value": value[1],
        #         }
        else:
            raise error.InvalidConfig(f"Unsupported type: {payload}")

        return result

    def get_vars(self, current=None):
        "Parse vars and interpolate strings"

        result = dict(current or {})

        for var in self._nodes:
            value = var.value
            result[var.name] = value
        return result

    def get_vars_list(self, current=None):
        "Parse vars and interpolate strings"

        assert isinstance(current, list) or current is None

        result = list(current or [])
        for var in self._nodes:
            result.append(var)
        return result


class PaasifySource(NodeDict, PaasifyObj):
    "Paasify source configuration"

    def install(self, update=False):
        "Install a source if not updated"

        # Check if the source if installed or install latest

        prj = self.get_parent().get_parent()
        coll_dir = prj.runtime.project_collection_dir
        src_dir = os.path.join(coll_dir, self.ident)
        git_dir = os.path.join(src_dir, ".git")

        if os.path.isdir(git_dir) and not update:
            self.log.debug(
                f"Collection '{self.ident}' is already installed in: {git_dir}"
            )
            return

        self.log.info(f"Install source '{self.ident}' in: {git_dir}")
        raise NotImplementedError


class PaasifySources(NodeDict, PaasifyObj):
    "Sources manager"
    conf_children = PaasifySource


class FileReference:
    """A FileReference Object

    Useful for managing project paths

    The path, once created is immutable, you choose how it behave one time
    and done forever. They act a immutable local variable.


    path: The path you want to manage
    root: The root of your project, CWD else
    keep: Returned path will be returned as absolute
        True: Return default path from origin abs/rel
        False: Return default path from root_path abs/rel

    """

    def __init__(self, path, root=None, keep=False):

        assert isinstance(path, str), f"Got: {type(path)}"
        root = root or os.getcwd()
        self.raw = path
        self.root = root
        self.keep = keep

    def __str__(self):
        return self.path()

    def is_abs(self):
        "Return true if the path is absolute"
        return os.path.isabs(self.raw)

    def is_root_abs(self):
        "Return true if the root path is absolute"
        return os.path.isabs(self.root)

    def path(self, start=None):
        "Return the absolute or relative path from root depending if root is absolute or not"

        if self.keep:
            if self.is_abs():
                return self.path_abs(start=start)
            return self.path_rel(start=start)
        else:
            if self.is_root_abs():
                return self.path_abs(start=start)
            return self.path_rel(start=start)

    def path_abs(self, start=None):
        "Return the absolute path from root"

        if self.is_abs():
            result = self.raw
        else:
            start = start or self.root
            real_path = os.path.join(start, self.raw)
            result = os.path.abspath(real_path) or "."
        return result

    def path_rel(self, start=None):
        "Return the relative path from root"

        if self.is_abs():
            start = start or self.root
            result = os.path.relpath(self.raw, start=start)
        else:
            start = start or self.root
            real_path = os.path.join(start, self.raw)
            result = os.path.relpath(real_path) or "."
        return result


class FileLookup(PaasifyObj):
    """A FileLookup Object

    Useful for identifing available files in differents hierachies"""

    def __init__(self, path=None, pattern=None, **kwargs):
        self._lookups = []
        self.log = logging.getLogger("paasify.cli.FileLookup")

        if path and pattern:
            self.insert(path, pattern, **kwargs)

    def _parse(self, path, pattern, **kwargs):
        "Ensure lookup is correctly formed"
        data = dict(kwargs)
        data.update(
            {
                "path": path,
                "pattern": pattern if isinstance(pattern, list) else [pattern],
            }
        )
        return data

    def insert(self, path, pattern, **kwargs):
        "Insert first a path/pattern to the lookup object"
        data = self._parse(path, pattern, **kwargs)
        self._lookups.insert(0, data)

    def append(self, path, pattern, **kwargs):
        "Append a path/pattern to the lookup object"
        data = self._parse(path, pattern, **kwargs)
        self._lookups.append(data)

    def get_lookups(self):
        "Return object lookups"
        return self._lookups

    def lookup_candidates(self):
        "List all available candidates of files for given folders, low level"

        result = []
        for lookup in self._lookups:
            path = lookup["path"]
            cand = filter_existing_files(path, lookup["pattern"])
            lookup["matches"] = cand
            result.append(lookup)
        return result

    def paths(self, first=False):
        "All matched files"

        vars_cand = self.lookup_candidates()
        ret = []
        for cand in vars_cand:
            for match in cand["matches"]:
                ret.append(match)

        if first:
            return _first(ret) if len(ret) > 0 else None
        return ret

    def match(self, fail_on_missing=False, first=False):
        "Match all candidates, and built a list result with object inside"

        vars_cand = self.lookup_candidates()
        result = []
        missing = []
        for cand in vars_cand:
            matches = cand["matches"]
            for match in matches:
                payload = dict(cand)
                payload.update({"match": match})
                result.append(payload)
            if len(matches) == 0:
                # Still add unlucky candidates
                missing.append(cand)

        # Report errors if missing
        if fail_on_missing and len(missing) > 0:
            missing_paths = [
                os.path.join(lookup["path"], _first(lookup["pattern"]))
                for lookup in missing
            ]
            for missed in missing_paths:
                self.log.info(f"Missing file: {missed}")
            missed_str = ",".join(missing_paths)
            raise error.MissingFile(
                f"Can't load {len(missing_paths)} vars files: {missed_str}"
            )

        if first:
            return _first(result) if len(result) > 0 else None

        return result
