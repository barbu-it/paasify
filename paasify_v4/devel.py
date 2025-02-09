import os
import logging
from pprint import pprint
from typing import List, Dict
from dataclasses import dataclass
from types import SimpleNamespace

from pathlib import Path

from superconf.anchors import PathAnchor

from paasify_v4.common import read_file, from_yaml
from paasify_v4.core import AppNode, setup_once, requires_setup_node

logger = logging.getLogger(__name__)



# Catalog
# ================================================


class PaasifyApp(AppNode):
    "PaasifyApp class"

    def __init__(self, ident, name=None, path=None, parent=None, index=None):
        super().__init__(ident, parent)
        assert isinstance(parent, PaasifyCollection)

        self.sub_path = path
        self.index = index
        self._name = name

        self._store_vars = {}

    # @setup_once("setup_node")
    # def setup_node(self):
    #     "Parse app metadata"
    #     logger.info("Setup app vars: %s", self)

    #     self._store_vars = self.read_vars()

    @setup_once("setup_vars")
    def setup_vars(self):
        "Parse app metadata"
        logger.info("Setup app vars: %s", self)
        self._store_vars = self.read_vars()

    def read_vars(self, filename="vars.yml"):
        "Read vars.yml file"
        vars_file = os.path.join(self.get_path(), filename)
        if os.path.exists(vars_file):
            data = read_file(vars_file)
            data = from_yaml(data)
            return data
        return {}

    @requires_setup_node("setup_vars")
    def get_vars(self):
        "Return vars"
        return self._store_vars

    @requires_setup_node("setup_vars")
    def get_description(self):
        "Return description"
        return self._store_vars.get("app_description", "")


class PaasifyCollection(AppNode):
    "PaasifyCollection class"

    def __init__(self, ident, sub_path=None, parent=None, index=None):
        assert isinstance(parent, CollectionsPath)
        super().__init__(ident, parent)

        self.sub_path = sub_path
        self.index = index
        self._store_apps = {}

    @requires_setup_node("setup_node")
    def get_apps(self):
        "Return apps"
        logger.debug("Get %s apps", self)
        return list(self._store_apps.values())

    @setup_once("setup_node")
    def setup_node(self):
        "Walk collection and get apps"
        logger.info("Setup collection: %s", self)

        # collection_path = os.path.join(self.get_path(), self.sub_path)
        collection_path = self.get_path()
        self._store_apps = self.walk_apps(collection_path)

    def walk_apps(self, collection_path) -> Dict:
        "Walk collections directories and return scan report"

        ret = {}
        # List recursively on three levels all docker-compose.yml files
        needle = "docker-compose.yml"

        for match in Path(collection_path).rglob(needle):
            # print("MATCH", match)
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

    def __init__(self, ident, parent=None, path=None, index=None):
        assert isinstance(parent, PaasifyCatalog)
        super().__init__(ident, parent)
        # assert isinstance(parent, (type(None), PaasifyCollection))

        self._path = path
        self.index = index
        self._store_collections = {}

        # Auto init
        self.setup_node()
        self._setup_done = True

    @setup_once("setup_node")
    def setup_node(self):
        logger.info("Setup collections path: %s", self)
        path = self._path
        self._store_collections = self.walk_collections(path)

    def walk_collections(self, collections_path) -> Dict:
        "Walk collections directories and return scan report"
        out = {}
        # List all directories names
        for dir_path in Path(collections_path).iterdir():
            # Dir_path must be a directory
            if not dir_path.is_dir():
                continue

            # Fetch the directory name, and skip hidden directories
            dir_name = dir_path.name
            if dir_name.startswith("."):
                continue

            # collection = PaasifyCollection(
            collection = PaasifyCollection(
                ident=dir_name,
                sub_path=dir_name,
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

    def walk_applications(self) -> Dict:
        "Walk collections directories and return scan report"

        print("YO APPS")
        for ident, collection in self._store_collections.items():
            collection.setup_node()

        return "WIP"

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
