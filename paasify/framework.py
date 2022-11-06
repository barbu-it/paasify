"Paasify Framework Libary"


# pylint: disable=logging-fstring-interpolation

import os
import logging


from pprint import pprint


from cafram.nodes import NodeList, NodeMap, NodeDict
from cafram.base import MixInLog, Base

from cafram.utils import (
    # to_domain,
    # to_yaml,
    merge_dicts,
    # flatten,
    # duplicates,
    # write_file,
    # to_json,
    # to_dict,
    # from_yaml,
    # serialize,
    # json_validate,
)

import paasify.errors as error

# from paasify.common import lookup_candidates  # serialize, , json_validate, duplicates
# from paasify.engines import bin2utf8


_log = logging.getLogger()


class PaasifyObj(Base, MixInLog):
    "Default Paasify base object"

    module = "paasify.api"
    conf_logger = "paasify"
    log = _log

    def __init__(self, *args, **kwargs):

        # Manually load classe
        Base.__init__(self, *args, **kwargs)
        MixInLog.__init__(self, *args, **kwargs)

        # Other things
        # super().__init__(*args, **kwargs)

        # print ("INIT PaasifyObj", self, '->'.join([ x.__name__ for x in self.__class__.__mro__]), args, kwargs)
        # #print ("INIT PaasifyObj", self, '->'.join([ x.__name__ for x in self.__class__.__mro__]), args, kwargs)
        # if hasattr(self, "get_parents"):
        #     print (self.get_parents())


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
                "oneOf": [
                    {"title": "As string", "type": "string"},
                    {"title": "As boolean", "type": "boolean"},
                    {"title": "As integer", "type": "integer"},
                    {
                        "title": "As null",
                        "description": "If set to null, this will remove variable",
                        "type": "null",
                    },
                ],
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

    def node_hook_final(self):
        "Ensure the logger is loaded early"

        # Start logger
        self.set_logger("paasify.cli.ConfigVar")


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
                #     ".*": { "properties": PaasifyConfigVar.conf_schema, }
                # }
                "propertyNames": {"pattern": "^[A-Za-z_][A-Za-z0-9_]*$"},
                "additionalProperties": PaasifyConfigVar.conf_schema,
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

        # print (f"INIT NEW VARSSSS: {type(payload)} {result} VS {payload}")
        return result

    def node_hook_final(self):
        "Ensure the logger is loaded early"

        # Start logger
        self.set_logger("paasify.cli.ConfigVarsManager")

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
