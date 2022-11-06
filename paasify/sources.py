"""Paasify Source management libray

"""

import os
import logging
from pprint import pprint, pformat

# import yaml
# import anyconfig
# import sh

# import _jsonnet

from urllib.parse import urlparse
from giturlparse import parse as gitparse


# from paasify.common import _exec
from cafram.utils import _exec, first
from cafram.nodes import NodeMap, NodeDict, NodeList

# from paasify.class_model import ClassClassifier
from paasify.framework import PaasifyObj
import paasify.errors as error


log = logging.getLogger(__name__)


# =====================================================================
# Source management
# =====================================================================


class Source(NodeMap, PaasifyObj):
    """A Source instance"""

    conf_default = {
        "remote": None,
        "name": None,
        "prefix": None,
        # "prefix": "https://github.com/%s.git",
    }

    schema_def = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Paasify Source configuration",
        "additionalProperties": False,
        "type": "object",
        "properties": {
            "remote": {
                "type": "string",
            },
            "name": {
                "type": "string",
            },
            "prefix": {
                "type": "string",
            },
            # "alias": {
            #    "type": "array",
            # },
        },
    }

    @property
    def name(self):
        "Return the remote name"
        conf = self.get_value()
        name = conf.get("name")
        if name:
            ret = name
        else:
            ret = self.git_repo_ident()

        assert ret, f"Stack without name or remote ! {self}"
        return ret

    # @property
    def git_repo_ident(self):
        "Return git repo ident"
        remote = self.remote
        if not remote:
            self.log.info(f"Using local collection for source: {self.serialize('raw')}")
            if self.name:
                return self.name

            raise Exception("Missing source name for: {self.serialize('raw')}")

        # Why does this lint fails ?
        # pylint: disable=no-member
        out = gitparse(self.remote)
        ret = f"{out.owner}/{out.repo}"
        return ret

    @property
    def path(self):
        "Return path of git repo installation path"

        actual_path = self.git_repo_ident()
        if not actual_path:
            raise error.InvalidSourceConfig(
                f"Can't find path for source: {self.serialize('raw')}"
            )

        ret = os.path.join(self.collection_dir, actual_path)
        return ret

    @property
    def git_url(self):
        "Return the git URL"
        ret = self.remote
        if self.prefix:
            ret = f"{self.prefix}{self.remote}"
        return ret

    def node_hook_init(self, **kwargs):

        self.obj_prj = self._node_parent._node_parent
        self.collection_dir = self.obj_prj.runtime.project_collection_dir

    def is_git(self):
        "Return true if git repo"
        test_path = os.path.join(self.path, ".git")
        return os.path.isdir(test_path)

    def is_installed(self):
        "Return true if installed"
        return os.path.isdir(self.path)

    def install(self):
        "Install from remote"

        # Check if install dir is already present
        if os.path.isdir(self.path):
            self.log.info("This source is already installed")
            return

        self.log.notice(f"Installing git source: {self.git_url}")

        # Git clone that stuff
        cli_args = ["clone", self.git_url, self.path]
        _exec("git", cli_args, _fg=True)

    def update(self):
        "Update from remote"

        # Check if install dir is already present
        if not os.path.isdir(self.path):
            self.log.info("This source is not installed yet")
            return

        # Git clone that stuff
        self.log.info(f"Updating git repo: {self.git_url}")
        cli_args = [
            "-C",
            self.path,
            "pull",
        ]
        _exec("git", cli_args, _fg=True)


class SourcesManager(NodeList, PaasifyObj):
    "Source manager"

    conf_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Paasify Source configuration",
        "description": "Configure a list of collections to install",
        "oneOf": [
            {
                "type": "null",
                "title": "Unset sources",
                "description": "If null or empty, it does not use any source",
            },
            {
                "title": "List of sources",
                "description": "Each source define a git repository and a name for stack references",
                "type": "array",
                "additionalProperties": False,
                "items": Source.schema_def,
            },
        ],
    }

    conf_children = Source

    def get_all(self):
        "Return the list of all sources"
        return list(self.get_children())

    def list_all_names(self) -> list:
        "Return a list of valid string names"

        sources = self.get_children()
        return [src.name for src in sources]

    def get_source(self, src_name):
        "Get source"
        sources = self.get_children()

        return first([src for src in sources if src.name == src_name])

    def find_app(self, app_path, source_name=None):
        "Find an app across all sources"

        source_names = [source_name] or self.list_all_names()

        for src in source_names:
            src = self.get_source(src)
            assert src.path, f"Source path should not be None: {self.__dict__}"
            test_dir = os.path.join(src.path, app_path)
            if os.path.isdir(test_dir):
                return test_dir
        return None

    def resolve_ref_pattern(self, src_pat):
        "Return a resource from its name or alias"

        for src_name_def in self.list_all_names():

            if f"{src_name_def}:" in src_pat:
                rsplit = src_pat.split(":", 2)
                src_name = rsplit[0]
                src_stack = rsplit[1]

                return src_stack, src_name

        return src_pat, None

    # =========================

    def cmd_ls(self) -> list:
        "List all stacks names"

        sources = self.get_children()
        print(f"{'Name' :<32}   {'Installed' :<14} {'git' :<14} {'URL' :<10}")
        for src in sources:

            is_installed = "True" if src.is_installed() else "False"
            is_git = "True" if src.is_git() else "False"
            print(
                f"  {src.name :<32} {is_installed :<14} {is_git :<14} {src.git_url :<10} {src.path}"
            )

    def cmd_install(self):
        "Ensure all sources are installed"

        sources = self.get_children()
        for src in sources:
            log.notice(f"Installing source: {src.name}")
            src.install()

    def cmd_update(self):
        "Update all source"

        sources = self.get_children()
        for src in sources:
            log.notice(f"Installing source: {src.name}")
            src.update()
