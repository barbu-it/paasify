"""
Paasify Application library

This library provides a convenient paasify user friendly API.

Example:
``` py title="test.py"
from paasify.app2 import PaasifyApp

app = PaasifyApp()

print (app.info())
prj = app.load_project()
prj.dump()
```

"""

from pprint import pprint

from cafram.utils import (
    to_yaml,
    to_json,
)
from cafram.nodes import NodeMap

import paasify.errors as error
from paasify.common import OutputFormat
from paasify.framework import PaasifyObj
from paasify.projects import PaasifyProject, PaasifyProjectConfig
from paasify.stacks2 import PaasifyStackManager
from paasify.sources import SourcesManager


class PaasifyApp(NodeMap, PaasifyObj):
    "Paasify Main application Instance"

    ident = "Paasify App"

    conf_default = {
        "config": {},
        "project": {},
    }

    conf_children = [
        {
            "key": "project",
            "cls": PaasifyProject,
            "action": "unset",
        },
    ]

    conf_schema = {
        # "$defs": {
        #     "AppProject": PaasifyProject.conf_schema,
        # },
        # "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "title": "Paasify App",
        "description": "Paasify app implementation",
        "additionalProperties": False,
        # "required": [
        #     "stacks"
        # ],
        "default": {},
        "properties": {
            "project": {
                "title": "Project configuration",
                "description": "See: schema prj",
                # "oneOf": [
                #     {
                #         "$ref": "#/$defs/AppProject",
                #         "description": "Instanciate project",
                #         "type": "object",
                #     },
                #     {
                #         "description": "Config file or path",
                #         "type": "string",
                #     },
                #     {
                #         "description": "Do not instanciate project",
                #         "type": "null",
                #     },
                # ],
            },
            "config": {
                "title": "Application configuration",
                "type": "object",
                "additionalProperties": True,
                # TODO: Add schema for appp
            },
        },
    }

    def info(self, autoload=None):
        """Report app config"""

        print("Paasify App Info:")
        print("==================")
        for key, val in self.config.items():
            print(f"  {key}: {val}")

        print("\nPaasify Project Info:")
        print("==================")

        # Autoload default project
        msg = ""
        if autoload is None or bool(autoload):
            try:
                if not self.project:
                    self.log.notice("Info is autoloading project")
                    self.load_project()
            except error.ProjectNotFound as err:
                msg = err
                if autoload is True:
                    raise error.ProjectNotFound(err) from err

        if self.project:
            # Report with active project if available
            for key, val in self.project.runtime.get_value(lvl=-1).items():
                print(f"  {key}: {val}")
        else:
            print(f"  {msg}")

    # pylint: disable=redefined-builtin
    def cmd_config_schema(self, format=None, target=None):
        """Returns the configuration json schema

        Args:
            format (_type_, optional): _description_. Defaults to None.

        Returns:
            _type_: _description_
        """

        target = target or "project"
        # mode = mode or "stdout"

        # assert mode in ["doc", "single", "stdout", "file"], f"Invalid mode: {mode}"

        # Select target to document
        if target == "app":
            out = self.conf_schema
        elif target == "prj":
            out = PaasifyProject.conf_schema
        elif target == "prj_config":
            out = PaasifyProjectConfig.conf_schema
        elif target == "prj_sources":
            out = SourcesManager.conf_schema
        elif target == "prj_stacks":
            out = PaasifyStackManager.conf_schema
        else:
            raise NotImplementedError(f"Target '{target}' is not supported")

        if format == OutputFormat.yaml:
            out = to_yaml(out)
        elif format == OutputFormat.json:
            out = to_json(out, nice=True)

        return out

    def load_project(self, path=None):
        "Return closest project"

        if self.project is not None:
            return self.project

        payload = path or {
            "_runtime": self.config,
        }

        prj = PaasifyProject(
            parent=self,
            payload=payload,  # Only string or nested runtime dict
        )

        self.add_child("project", prj)
        return prj
