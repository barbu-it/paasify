# -*- coding: utf-8 -*-
"""
Paasify Application library

This library provides a convenient paasify user friendly API.

Example:
``` py title="test.py"
from paasify.app import PaasifyApp

app = PaasifyApp()

print (app.info())
prj = app.load_project()
prj.dump()
```

"""

# Imports
# =====================================================================

import os
from pprint import pprint  # noqa: F401

from cafram.utils import (
    to_json,
    _exec,
    write_file,
)
from cafram.nodes import NodeMap

import paasify.errors as error
from paasify import __version__ as paasify_version
from paasify.common import ensure_dir_exists, get_paasify_pkg_dir
from paasify.framework import PaasifyObj, FileLookup
from paasify.projects import PaasifyProject, PaasifyProjectConfig
from paasify.stacks import StackManager
from paasify.sources import SourcesManager
from paasify.collections import CollectionDocumator, gen_schema_doc


# Main Application class
# =====================================================================

README_TEMPLATE = """<p align='center'>
<img src="https://github.com/barbu-it/paasify/raw/main/logo/paasify_project.svg" alt="Paasify Project">
</p>

# Paasify Project: {name}

This project deploys:

    * APP1
    * APP2

APP_DESC

## Quickstart

To deploy this project, your must first checkout the project with git and go into the directory:
```
git clone GIT_REPO {name}
cd {name}
```

Download project sources:
```
paasify src install
```

Deploy stack:
```
paasify apply
```

## Project

### Requirements

The following requirements must be installed for this project:

* docker

To modify this project:

* paasify v{version}
* git

### Paasify documentation

Quicklinks:

* [Paasify Documentation](https://barbu-it.github.io/paasify/)
* [Paasify Sources](https://github.com/barbu-it/paasify)
* [Paasify Gitter](https://gitter.im/barbu-it/paasify)


## Project Informations

Paasify project maintened by:

* Author: AUTHOR, EMAIL
* License: GPLv3
* Repository: GIT_REPO

"""


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

    # Project management
    # ======================

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

    def new_project(self, path, source=None):
        """Create a new project"""

        assets_dir = get_paasify_pkg_dir()
        changed = False
        created = ensure_dir_exists(path)
        prj_name = os.path.basename(os.path.abspath(path))
        print("NAME", prj_name)

        # Prepare configs
        build_conf = {
            "paasify": {
                "dest": os.path.join(path, "paasify.yml"),
            },
            "gitignore": {
                "dest": os.path.join(path, ".gitignore"),
            },
        }
        lookups = {
            "paasify": {
                "path": os.path.join(assets_dir, "assets"),
                "pattern": ["paasify.yml", "paasify.yaml"],
            },
            "gitignore": {
                "path": os.path.join(assets_dir, "assets"),
                "pattern": "gitignore",
            },
        }
        templates = {
            "requirements": {
                "content": "paasify>={version}\n",
                "dest": os.path.join(path, "requirements.txt"),
            },
            "readme": {
                "content": README_TEMPLATE,
                "dest": os.path.join(path, "README.md"),
            },
        }

        # Add source if requested
        if source:
            sources = {
                "paasify": {"path": source, "pattern": ["paasify.yml", "paasify.yaml"]},
                "gitignore": {
                    "path": source,
                    "pattern": ".gitignore",
                },
            }

        # Generate files
        for name, template in templates.items():
            dest = template["dest"]
            if not os.path.exists(dest):
                self.log.notice(f"Create: '{dest}'")
                content = template["content"].format(
                    name=prj_name, version=paasify_version
                )
                write_file(dest, content)
                changed = True
            else:
                self.log.info(f"Skip: '{dest}' as it already exists")

        # Build each assets
        for name, conf in lookups.items():
            lookup = FileLookup()
            if source:
                lookup.append(sources[name]["path"], sources[name]["pattern"])
            lookup.append(conf["path"], conf["pattern"])
            match = lookup.match(first=True)
            if not match:
                continue

            # Copy files
            src = match["match"]
            dest = build_conf[name]["dest"]
            if not os.path.exists(dest):
                self.log.notice(f"Create: '{dest}' from '{src}'")
                _exec("cp", cli_args=[src, dest])
                changed = True
            else:
                self.log.info(f"Skip: '{dest}' as it already exists")

        # Init git directory
        git_dir = os.path.join(path, ".git")
        if not os.path.exists(git_dir):
            self.log.notice(f"Create git repo in '{path}'")
            files = [
                file
                for file in os.listdir(path)
                if os.path.isfile(os.path.join(path, file))
            ]
            _exec("git", ["init", path])
            _exec("git", ["-C", path, "add"] + files)
            changed = True
        else:
            self.log.info(f"Directory is alrayd a git repository:{path}")

        # Report actions
        msg = "No changes in existing project"
        if created:
            if source:
                msg = f"New project created in: {path} from {source}"
            else:
                msg = f"New project created in: {path}"
        elif changed:
            if source:
                msg = f"New project updated in: {path} from {source}"
            else:
                msg = f"New project updated in: {path}"
        self.log.notice(msg)

    # App commands
    # ======================

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

    def cmd_document(self, path=None, dest_dir=None, mkdocs_config=None):
        "Generate documentation"

        documator = CollectionDocumator(
            parent=self, path=path, dest_dir=dest_dir, mkdocs_config=mkdocs_config
        )
        documator.generate(
            mkdocs_config=None,
        )

    # pylint: disable=redefined-builtin
    def cmd_config_schema(self, format=None, dest_dir=None):
        """Returns the configuration json schema

        Args:
            dest_dir (str, optional): Destination directory

        """

        config = dict(
            minify=False,
            deprecated_from_description=True,
            default_from_description=False,
            expand_buttons=False,
            link_to_reused_ref=False,
            copy_css=True,
            copy_js=True,
            # config=config_file,
            # config_parameters=config,
        )
        # config = {}
        self.log.info("TEST 1")

        # Ensure that dest dir exists
        if dest_dir:
            self.log.notice(f"Documentation directory: {dest_dir}")
            if not os.path.isdir(dest_dir):
                self.log.notice(f"Create parent directories: {dest_dir}")
                os.makedirs(dest_dir)

        targets = ["app", "prj", "prj_config", "prj_sources", "prj_stacks"]
        ret = {}
        for target in targets:

            # Select target to document
            if target == "app":
                schema = self.conf_schema
            elif target == "prj":
                schema = PaasifyProject.conf_schema
            elif target == "prj_config":
                schema = PaasifyProjectConfig.conf_schema
            elif target == "prj_sources":
                schema = SourcesManager.conf_schema
            elif target == "prj_stacks":
                schema = StackManager.conf_schema
            else:
                raise NotImplementedError(f"Target '{target}' is not supported")

            ret[target] = schema
            if not schema:
                assert False, "You found a bug!"

            if not dest_dir:
                continue

            slug = f"conf_{target}"
            json_file = os.path.join(dest_dir, f"{slug}.json")

            write_file(json_file, to_json(schema))
            self.log.info(f"Generate '{slug}.html' from: {json_file}")
            gen_schema_doc(json_file, dest_dir, f"{slug}.html", config=config)

        return ret
