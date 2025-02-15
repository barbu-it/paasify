"""
Paasify Catalog Module

This module provides the core catalog functionality for Paasify v4.
Key components include:

- PaasifyApp: Class representing an application in the catalog with metadata handling
- PaasifyCollection: Collection of applications (defined later in file)
- PaasifyCollectionPath: Path containing collections (defined later in file) 
- PaasifyCatalog: Main catalog class managing collections and applications (defined later in file)

The module focuses on organizing and managing applications in a hierarchical catalog structure,
with support for metadata, variables, and collection management.
"""

import os
import logging
from typing import List, Dict
from pprint import pprint

# from pprint import pprint
from pathlib import Path
from difflib import get_close_matches
from superconf.anchors2 import PathAnchor


from paasify_v4.common import (
    find_file_in_path,
    dict_to_env,
    write_file,
    read_file,
    from_yaml,
    to_domain,
    flatten,
    truncate,
)


from paasify_v4.core import AppNode, setup_once, requires_setup_node
from paasify_v4.lib.git_helpers import GitRepo
import paasify_v4.exception as exc

logger = logging.getLogger(__name__)


# Catalog
# ================================================


class PaasifyAppV1SupportMixin():
    "Support for paasify v1 apps"

    def get_var_tags(self):
        "Return var tags"

        # Actually, there is no use case, I never used
        # it .. i think ...
        # app_path = ~self.path
    
        return []



class PaasifyApp(PaasifyAppV1SupportMixin,AppNode):
    "PaasifyApp class"

    paasify_type = "catalog_app"

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def __init__(self, ident, name=None, path=None, parent=None, index=None):
        super().__init__(ident, parent)
        assert isinstance(parent, PaasifyCollection)

        self._path = PathAnchor(path, parent=parent.path)
        self.index = index
        self._name = name

        self._store_vars = {}
        self._store_tags = {}

    # Vars support
    # ------------
    @setup_once("setup_vars")
    def setup_vars(self):
        "Parse app metadata"
        logger.info("Setup app vars: %s", self)
        self._store_vars = self.get_vars_files()

    @requires_setup_node("setup_vars")
    def get_vars(self):
        "Return vars"
        return self._store_vars

    @requires_setup_node("setup_vars")
    def get_description(self):
        "Return description"
        return self._store_vars.get("app_description", "")

    # Structure scan support
    # ------------
    @setup_once("setup_tags")
    def setup_tags(self):
        "Parse app tags"
        logger.info("Setup app tags: %s", self)
        self._store_tags = self.walk_tags()

    def walk_tags(self):
        "Return tags"
        # path = self.get_path()
        path = +self.path
        needle = "docker-compose.*.yml"
        tags = {}

        for match in sorted(Path(path).rglob(needle)):
            tag_parts = match.stem.split(".")
            tag = tag_parts[1:]
            tag = ".".join(tag)
            tags[tag] = {"path": str(match)}

            # Read the tag file
            content = self.read_yaml_file(match)
            if content:
                metadata = content.get("x-meta", {})
                tags[tag]["metadata"] = metadata

                # https://jsonlogic.com/play.html
                rules = content.get("x-rules", {})
                tags[tag]["rules"] = rules

        return tags

    @requires_setup_node("setup_tags")
    def get_tags(self):
        "Return tags"
        return self._store_tags

    # File structure support - Shared code Apps<=>Pods
    # # ------------
    # @setup_once("setup_files")
    # def setup_files(self):
    #     "Parse app files"
    #     # logger.info("Setup app files: %s", self)
    #     # self._store_files = self.walk_files()

    def get_compose_files(self):
        "Return files"

        # Get app path and base docker-compose file
        app_path = ~self.path
        docker_files = ["docker-compose.yml", "docker-compose.yaml"]
        docker_file_matches = find_file_in_path(docker_files, app_path)
        if len(docker_file_matches) == 0:
            raise exc.PaasifyAssembleError(
                f"No docker-compose.yml file found in {app_path}"
            )
        elif len(docker_file_matches) > 1:
            msg = f"Multiple docker-compose.yml files found in {app_path}, keeping the first one only: {docker_file_matches}"
            raise exc.PaasifyAssembleError(msg)
        logger.debug("Docker file matches: %s", docker_file_matches)
        docker_file_match = docker_file_matches[0]

        return docker_file_match

    def get_vars_files(self):
        "Return vars files"
        app_path = ~self.path

        app_vars_files = ["vars.yml", "vars.yaml"]
        app_vars_matches = find_file_in_path(app_vars_files, app_path)
        app_vars = {}
        if len(app_vars_matches) != 0:
            app_vars = from_yaml(read_file(app_vars_matches[0]))

        return app_vars

    def get_extra_docker_files(self, tags):
        "Return extra docker files"

        app_path = ~self.path

        extra_docker_files = []
        for tag in tags:
            tag_paths = app_path / f"docker-compose.{tag}"
            tag_paths = [f"{tag_paths}.{ext}" for ext in ["yml", "yaml"]]
            logger.debug("Tag path: %s", tag_paths)

            match = find_file_in_path(tag_paths, app_path)
            if match:
                # print("Match:", match, tag_paths)
                extra_docker_files.append(match[0])
            else:
                logger.warning("No match for tag %s in %s", tag, tag_paths)

        return extra_docker_files


############################################

class PaasifyCollectionV1SupportMixin():
    "Support for paasify v1 collections"

    def get_jsonnet_files(self):
        "Return var tags"
        collection_path = self.path
        search_path = collection_path / "__paasify__/tags/"
        jsonnet_files = []
        print("Search path:", search_path)
        for match in Path(search_path).rglob("*.jsonnet"):
            jsonnet_files.append(match)
        return jsonnet_files


class PaasifyCollection(PaasifyCollectionV1SupportMixin,AppNode):
    "PaasifyCollection class"

    def __init__(self, ident, name=None, path=None, parent=None, index=None):
        assert isinstance(parent, CollectionsPath)
        super().__init__(ident, parent)

        self._name = name
        self._path = PathAnchor(path)
        self.index = index
        self._store_apps = {}
        self.git = None

    def __repr__(self):
        return f"{self.__class__.__name__}({self.path.get_name() or self.name})"

    # Git support
    # ------------

    @setup_once("init_git")
    def init_git(self):
        "Init git"
        logger.info("Init git: %s", self)
        self.git = GitRepo(~self.path)

    @requires_setup_node("init_git")
    def get_git_remote(self):
        "Get git remote"
        # self.git = GitRepo(self.get_path())

        logger.debug("Get git remotes: %s", self)
        return self.git.remote()

    @requires_setup_node("init_git")
    def get_git_branch(self):
        "Get git branch"
        # self.git = GitRepo(self.get_path())

        logger.debug("Get git branch: %s", self)
        return self.git.branch()

    @requires_setup_node("init_git")
    def is_git_clean_worktree(self):
        "Check if git worktree is clean"
        # self.git = GitRepo(self.get_path())

        logger.debug("Get git dirtyness: %s", self)
        return not self.git.is_dirty()

    @requires_setup_node("init_git")
    def get_git_status(self):
        "Get git status"
        # self.git = GitRepo(self.get_path())

        logger.debug("Get git status: %s", self)
        return self.git.git_status()

    # Apps support
    # ------------
    @requires_setup_node("init_apps")
    def get_apps(self):
        "Return apps"
        logger.debug("Get %s apps", self)
        return list(self._store_apps.values())

    @setup_once("init_apps")
    def init_apps(self):
        "Walk collection and get apps"
        logger.info("Setup collection: %s", self)

        # collection_path = self.get_path()
        collection_path = ~self.path
        self._store_apps = self.walk_apps(collection_path)

    def walk_apps(self, collection_path) -> Dict:
        "Walk collections directories and return scan report"

        ret = {}
        # List recursively on three levels all docker-compose.yml files
        needle = "docker-compose.yml"

        for match in Path(collection_path).rglob(needle):
            # Get relative path from collection root
            rel_path = match.relative_to(collection_path)

            # Remove docker-compose.yml from path
            app_path = rel_path.parent

            # Use path as app identifier
            app_ident = str(app_path)

            app = PaasifyApp(
                ident=f"{self.ident}@{app_ident}",
                name=app_ident,
                path=str(app_path),
                parent=self,
                index=self.index,
            )

            # Store app info
            assert app_ident not in ret
            ret[app_ident] = app

        return ret


##############################################################


class CollectionsPath(AppNode):
    "CollectionsPath class"

    paasify_type = "catalog_path"

    def __repr__(self):
        return (
            f"{self.__class__.__name__}({truncate((+self.path or self.name), max=-12)})"
        )

    # def __repr__(self):
    #     return f"{self.__class__.__name__}({+self.path or self.name})"

    # def __repr__(self):
    #     return f"{self.__class__.__name__}({self.path.get_name() or self.name})"

    def __init__(self, ident, parent=None, path=None, index=None):
        assert isinstance(parent, PaasifyCatalog)
        super().__init__(ident, parent)

        self._path = PathAnchor(path, mode="abs")
        self.index = index
        self._store_collections = {}

        # Auto init
        self.setup_node()
        self._setup_done = True  # TODO: This should be safe to remove now

    @setup_once("setup_node")
    def setup_node(self):
        "Setup collections path"
        logger.info("Setup collections path: %s", self)
        self._store_collections = self.walk_collections(~self._path)

    def walk_collections(self, collections_path) -> Dict:
        "Walk collections directories and return scan report"
        out = {}
        # List all directories names
        if not os.path.exists(collections_path):
            logger.info("Collections path does not exist: %s", collections_path)
        else:
            for dir_path in Path(collections_path).iterdir():
                # Dir_path must be a directory
                if not dir_path.is_dir():
                    continue

                # Fetch the directory name, and skip hidden directories
                dir_name = dir_path.name
                if dir_name.startswith("."):
                    continue

                collection = PaasifyCollection(
                    ident=dir_name,
                    name=dir_name,
                    path=dir_path,
                    parent=self,
                    index=self.index,
                )
                out[dir_name] = collection

                # Future v2
                # # List recursively on three levels all docker-compose.yml files
                # needle = "paasify.collection.yml"
                # for docker_compose_path in Path(collection_path.path).rglob(needle):
                #     print(docker_compose_path)

        return out

    @requires_setup_node("setup_node")
    def get_collections(self, *args):
        "Return collections, from store"
        logger.debug("Get %s collections", self)

        if len(args) == 0:
            return self._store_collections.values()
        if len(args) == 1:
            return self._store_collections.get(args[0], None)
        raise ValueError(f"Invalid arguments: {args}")


class PaasifyCatalog(AppNode):
    "Catalog class, manage list of collections paths"

    paasify_type = "catalog"

    # node__iterate_backend = "_children"
    node__iterate_setupmarker = "setup_node"

    def __init__(self, collections_paths=None):
        super().__init__()

        # Settings attributes
        self.collections_paths = collections_paths

        self._store_paths = []
        self._store_collections = {}
        # self._store_apps = {}

        # Auto init
        self.setup_node()
        # self._setup_done = True

    def __repr__(self):
        return f"{self.__class__.__name__}({len(self.collections_paths) or ''})"

    # =============

    @setup_once("setup_node")
    def setup_node(self, paths=None):
        "Init node"
        # logger.debug("Setup node333 %s", self)
        logger.info("Setup catalog: %s", self)
        paths = paths or self.collections_paths
        self._store_paths = self.walk_collections_paths(paths)

    def walk_collections_paths(self, paths) -> List[Dict]:
        "Walk collections directories and return scan report"

        ret = []
        for index, collection_path in enumerate(paths):
            ident = Path(collection_path).name

            # Build result
            data = CollectionsPath(
                ident=ident,
                parent=self,
                path=collection_path,
                index=index,
                # collection_names=_names,
            )
            ret.append(data)

        return ret

    ########################## Main objects

    @requires_setup_node("setup_node")
    def get_collections_paths(self):
        "Return collections paths"
        return self._store_paths

    @requires_setup_node("setup_node")
    def get_collections(self, *args):
        "Return collections, loop over each colections paths"
        logger.debug("Get %s catalog collections", self)
        ret = []
        for collection_path in self._store_paths:
            if len(args) == 1:
                match = collection_path.get_collections(*args)
                if match is not None:
                    return match
            else:
                for collection in collection_path.get_collections():
                    ret.append(collection)
        return ret

    @requires_setup_node("setup_node")
    def get_apps(self):
        "Return apps"
        ret = []
        for collections_path in self._store_paths:
            for collection in collections_path:
                ret.extend(collection.get_apps())
        return ret

    @requires_setup_node("setup_node")
    def get_app(self, name):
        "Return app"

        out = []
        for collection in self.get_collections():
            for app in collection.get_apps():
                if name in [app.name, app.ident]:
                    out.append(app)

        # Unicity checker
        if len(out) > 1:
            out = " ".join([app.ident for app in out])
            raise ValueError(f"Multiple apps found for '{name}': {out}")
        if len(out) == 0:
            raise ValueError(f"App '{name}' not found")
        return out[0]

    @requires_setup_node("setup_node")
    def resolve_app(self, hint, raise_on_empty=False):
        "Return app by path"

        out = []
        app_list = []
        for collection in self.get_collections():
            for app in collection.get_apps():
                app_list.append(app)
                if hint in [app.name, app.ident]:
                    # print("APP:", app)
                    out.append(app)

        if len(out) > 0 or not raise_on_empty:
            return out

        hints = [app.name for app in app_list] + [app.ident for app in app_list]
        hints = list(set(hints))
        close_matches = " ".join(get_close_matches(hint, hints))
        msg = f"App '{hint}' not found, do you mean: {close_matches} ?"
        raise exc.PaasifyAppNotFoundError(msg, hints=close_matches)
