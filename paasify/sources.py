# -*- coding: utf-8 -*-
"""Paasify Source management libray

"""

import os
import logging
from pprint import pprint, pformat  # noqa: F401

from giturlparse import parse as gitparse

from cafram.utils import _exec, first
from cafram.nodes import NodeMap, NodeList

from paasify.common import get_paasify_pkg_dir
from paasify.framework import PaasifyObj, FileReference
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
        "dir": None,
        "install": None,
        # "prefix": "https://github.com/%s.git",
    }

    schema_def = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Paasify Source configuration",
        "oneOf": [
            {
                "type": "string",
            },
            {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {
                        "type": "string",
                    },
                    "remote": {
                        "type": "string",
                    },
                    "ref": {
                        "type": "string",
                    },
                    "prefix": {
                        "type": "string",
                    },
                    "aliases": {
                        "type": "array",
                    },
                },
            },
        ],
    }

    def extract_short(self, short):
        "Guess data from source short forms"
        ret = None

        # Try if remote
        remote = self.remote or short
        if remote:
            out = gitparse(remote)
            if hasattr(out, "url"):
                # Guess from valid URL
                ret = {
                    "remote": out.url,
                    "name": out.repo,
                    "dir": f"{out.owner}-{out.repo}",
                    "install": "clone",
                    "guess": f"a git repo: {out.url}",
                }
            else:
                self.log.trace(f"Source is not a git repo: {self._node_conf_raw}")

        # Try if dir
        value_ = self.dir or self.remote or self.name or short
        if not ret and value_:
            # So is it a path? Relative, absolute?
            install_ = self.install or "none"

            # Look for direct path
            path = FileReference(value_, root=self.runtime.root_path, keep=True)
            if os.path.isdir(path.path()):
                path_ = path.path()
                ret = {
                    "remote": None,
                    "name": str(self.name or os.path.basename(path.path_abs())),
                    "path": path_,
                    "install": install_,
                    "guess": f"path: {path_}",
                }
            else:
                self.log.trace(
                    f"Source is not found in path '{path}' for {self._node_conf_raw}"
                )

            # Look into <prj>.paasify/collections
            if not ret:
                path_ = FileReference(
                    value_, self.runtime.project_collection_dir, keep=True
                ).path()
                if os.path.isdir(path_):
                    ret = {
                        "remote": None,
                        "name": str(self.name or os.path.basename(path_)),
                        "path": path_,
                        "install": install_,
                        "guess": f"inside the stack: {path_}",
                    }
                else:
                    self.log.trace(
                        f"Source is not found in collection dir '{path}' for {self._node_conf_raw}"
                    )

        # Try default gh repo
        value_ = self.dir or self.remote or short
        if not ret and value_:
            # Last change to guess from pattern
            owner = None
            repo = value_
            if "/" in value_:
                parts = short.split("/", 2)
                owner = parts[0]
                repo = parts[1]

            if not owner:
                owner = "paasify"

            remote_ = f"https://github.com/{owner}/{repo}.git"
            ret = {
                "remote": remote_,
                "name": f"{owner}/{repo}",
                "dir": f"{owner}/{repo}",
                "install": "clone",
                "guess": "Refer to github repository ({remote_})",
            }

        if not ret:
            msg = f"Invalid configuration for source: {self._node_conf_raw}"
            raise error.InvalidSourceConfig(msg)

        assert ret["install"]
        return ret

    def node_hook_init(self, **kwargs):
        "Setup object vars from parents"
        self.obj_prj = self._node_parent._node_parent
        self.collection_dir = self.obj_prj.runtime.project_collection_dir

    def node_hook_transform(self, payload):
        "Transform short form into dict"

        if isinstance(payload, str):
            payload = {"short": payload}
        return payload

    def node_hook_final(self):
        "Init source correctly from available elements"

        self.runtime = self._node_parent._node_parent.runtime
        self.relative = self.runtime.relative

        # TODO: this is very awful
        self.short = getattr(self, "short", None)
        self.name = getattr(self, "name", None)
        self.dir = getattr(self, "dir", None)
        self.aliases = getattr(self, "aliases", [])
        self.remote = getattr(self, "remote", None)
        self.install = getattr(self, "install", None)
        self.path = None

        extracted = None
        extracted = self.extract_short(self.short)
        for key, value in extracted.items():
            setattr(self, key, getattr(self, key, None) or value)
        self.log.debug(f"Source '{self.name}' is {extracted['guess']}")

        # The actual thing we all want !
        if not self.path:
            self.path = FileReference(
                self.dir, self.runtime.project_collection_dir, keep=True
            ).path()

        assert self.name
        assert self.path

    def is_git(self):
        "Return true if git repo"
        test_path = os.path.join(self.path, ".git")
        return os.path.isdir(test_path)

    def is_installed(self):
        "Return true if installed"
        return os.path.isdir(self.path)

    def cmd_install(self):
        "Install from remote"

        # Check if install dir is already present
        remote = self.remote
        install = self.install

        # Skip non installable sources
        if install == "none":
            self.log.notice(f"Source '{self.name}' is a path, no need to install")
            return

        # Ensure parent directory exists before install
        dest = os.path.join(self.collection_dir, self.dir)
        parent_dir = os.path.dirname(dest)
        if not os.path.isdir(parent_dir):
            self.log.info(f"Creating parent directories: {parent_dir}")
            os.makedirs(parent_dir)

        # Install source
        if install.startswith("symlink"):
            self.log.notice(f"Installing '{self.name}' via {install}: {remote}")

            # Ensure nothing exists first
            if os.path.exists(dest):

                if not os.path.exists(os.readlink(dest)):
                    self.log.notice(f"Removing broken link in: {dest}")
                    os.unlink(dest)
                else:
                    assert False, "Found a bug !"

            # Create the symlink
            self.log.notice(f"Collection symlinked in: {dest}")
            os.symlink(remote, dest)

        elif install == "clone":
            # Git clone that stuff
            if os.path.isdir(self.path):
                self.log.notice(
                    f"Source '{self.name}' is already installed in {self.path}"
                )
                return
            self.log.notice(f"Installing '{self.name}' git: {remote} in {self.path}")
            cli_args = ["clone", remote, self.path]
            _exec("git", cli_args, _fg=True)
        else:
            raise Exception(f"Unsupported methods: {install}")

    def cmd_update(self):
        "Update from remote"

        # Check if install dir is already present
        if not os.path.isdir(self.path):
            self.log.info("This source is not installed yet")
            return

        # Git clone that stuff
        git_url = self.git_url()
        self.log.info(f"Updating git repo: {git_url}")
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
                "items": Source.schema_def,
            },
        ],
    }

    conf_children = Source

    def node_hook_transform(self, payload):

        module_path = os.path.dirname(error.__file__)
        module_path2 = get_paasify_pkg_dir()
        assert module_path == module_path2, "TODO: Validate this"
        paasify_collection = os.path.join(
            module_path, "assets", "collections", "paasify"
        )

        # Always inject the paasify core source at first
        payload = payload or []
        payload.insert(
            0,
            {
                "name": "paasify",
                "dir": paasify_collection,
            },
        )

        return payload

    def node_hook_final(self):
        "Prepare sources"

        # Look for duplicate names
        known_names = []
        for src in self.get_children():

            if src.name in known_names:
                dups = [dup._node_conf_raw for dup in self.find_by_name_alias(src.name)]
                dups = ", ".join(dups)
                msg = f"Two stacks have the same name: {dups}"
                raise error.DuplicateSourceName(msg)
            known_names.append(src.name)

            for alias in src.aliases:
                if alias in known_names:
                    dups = [
                        dup._node_conf_raw for dup in self.find_by_name_alias(alias)
                    ]
                    dups = ", ".join(dups)
                    msg = f"An alias have duplicate assignments: {dups}"
                    raise error.DuplicateSourceName(msg)
                known_names.append(alias)

        # Assign a default node:
        default = self.find_by_name_alias("default")
        if len(default) < 1:
            first_node = first(self.get_children())
            if first_node:
                first_node.aliases.append("default")
                self.log.info(
                    f"First source has been set as default: {first_node.name}"
                )
            else:
                self.log.info("No source found for this project")

    def get_all(self):
        "Return the list of all sources"
        return list(self.get_children())

    def list_all_names(self) -> list:
        "Return a list of valid string names"

        sources = self.get_children()
        return [src.name for src in sources]

    def get_app_source(self, app_name, source=None):
        "Return the source of an app_name"

        if source:
            sources = self.find_by_name_alias(source)
        else:
            sources = self.get_all()

        checked_dirs = []
        for src in sources:
            check_dir = os.path.join(src.path, app_name)
            if os.path.isdir(check_dir):
                return src
            checked_dirs.append(check_dir)

        # Fail and explain why
        sources = [src.name for src in self.get_all()]
        src_str = ",".join(sources)
        msg_dirs = " ".join(checked_dirs)
        msg = f"Impossible to find app '{app_name}' in sources '{src_str}' in paths: {msg_dirs}"

        if len(sources) != checked_dirs:
            hint = "Are you sure you have installed sources before? If not, run: paasify src install"
            self.log.warning(hint)
        raise error.MissingApp(msg)

    def get_search_paths(self):
        "Get search paths"

        return [{"path": src.path, "src": src} for src in self.get_children()]

    def find_by_name_alias(self, string, name=None, alias=None):
        "Return all src that match name or alias"

        name = name or string
        alias = alias or string

        sources = self.get_children()
        return [src for src in sources if name == src.name or alias in src.aliases]

    # Commands
    # ======================

    def cmd_tree(self) -> list:
        "Show a tree of all sources"

        print("Not implemented yet")

    def cmd_ls(self, explain=False) -> list:
        "List all stacks names"

        sources = self.get_children()
        for src in [None] + sources:

            if not src:
                remote = "REMOTE"
                name = "NAME"
                is_installed = "INSTALLED"
                is_git = "GIT"
                path = "PATH"
            else:
                is_installed = "True" if src.is_installed() else "False"
                is_git = "True" if src.is_git() else "False"
                remote = src.remote or ""
                name = src.name
                path = src.path

            print(
                f"  {name :<20} {is_installed :<10} {is_git :<8} {remote :<50} {path}"
            )

    def cmd_install(self):
        "Ensure all sources are installed"

        sources = self.get_children()
        for src in sources:
            log.notice(f"Installing source: {src.name}")
            src.cmd_install()

    def cmd_update(self):
        "Update all source"

        sources = self.get_children()
        for src in sources:
            log.notice(f"Installing source: {src.name}")
            src.cmd_update()
