import logging
from pprint import pprint
from typing import List, Dict
from dataclasses import dataclass
from types import SimpleNamespace

from pathlib import Path

from superconf.anchors import PathAnchor


logger = logging.getLogger(__name__)


class Node:
    "Node class"

    ident = None
    parent = None
    _children = None

    def __init__(self, ident=None, parent=None):
        self.ident = ident
        self.parent = parent
        self._children = {}

        # Make the node relationship
        if parent is not None:
            assert isinstance(parent, Node)
            parent._children[self.ident] = self

    def __repr__(self):
        return f"{self.__class__.__name__}({self.ident or ''})"


@staticmethod
def requires_setup_node(func):
    "Decorator to ensure init_node is called only once before method execution"

    def wrapper(self, *args, **kwargs):
        # print("WRAPPED DECORATOR CALL", self, func, args, kwargs)
        # pprint(self.__dict__)
        if not hasattr(self, "_setup_done"):
            # print("DECORATOR INIT NODE")
            self.setup_node()
            self._setup_done = True
        return func(self, *args, **kwargs)

    return wrapper


# @dataclass
class DataProtocol:
    "DataProtocol class, generic data protocols for inter class communication"

    ident: str


class AppNode(Node):
    "AppNode class"

    @property
    def name(self):
        "Return collection ident"
        name = self.ident
        if "/" in name:
            name = name.split("/")[-1]
        return name

    @property
    def path2(self):
        "Return source"

        if hasattr(self, "sub_path"):
            return self.sub_path
        if hasattr(self, "_path"):
            return self._path
        return "NO PATH"


# Catalog
# ================================================


class ApplicationObj(AppNode):
    "ApplicationObj class"

    def __init__(self, ident, path=None, parent=None, index=None):
        super().__init__(ident, parent)
        assert isinstance(parent, CollectionObj)

        self.sub_path = path
        self.index = index

class CollectionObj(AppNode):
    "CollectionObj class"

    def __init__(self, ident, sub_path=None, parent=None, index=None):
        assert isinstance(parent, CollectionsPath)
        super().__init__(ident, parent)

        self.sub_path = sub_path
        self.index = index
        self._store_apps = {}

    @requires_setup_node
    def get_apps(self):
        "Return apps"
        return list(self._store_apps.values())

    def setup_node(self):
        path = self.sub_path
        self._store_apps = self.walk_apps(path)

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

            app = SimpleNamespace(
                ident=app_ident,
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
        assert isinstance(parent, AppCatalog)
        super().__init__(ident, parent)
        # assert isinstance(parent, (type(None), CollectionObj))

        self.path = path
        self.index = index
        self._store_collections = {}

        # Auto init
        self.setup_node()
        self._setup_done = True

    def setup_node(self):
        path = self.path
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

            # collection = CollectionObj(
            collection = CollectionObj(
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

    @requires_setup_node
    def get_collections(self, *args):
        "Return collections, from store"
        logger.info("Get collections from %s", self)

        if len(args) == 0:
            return self._store_collections.values()
        if len(args) == 1:
            return self._store_collections.get(args[0], None)
        raise ValueError(f"Invalid arguments: {args}")


class AppCatalog(AppNode):
    "Catalog class, manage list of collections paths"

    def __init__(self, collections_paths=None):
        super().__init__()

        # Settings attributes
        self.collections_paths = collections_paths

        self._store_paths = []
        self._store_collections = {}
        # self._store_apps = {}

    # =============
    @requires_setup_node
    def get_collections_paths(self):
        "Return collections paths"
        return self._store_paths

    # =============

    def setup_node(self, paths=None):
        "Init node"
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

    @requires_setup_node
    def get_collections(self, *args):
        "Return collections, loop over each colections paths"
        logger.info("Get collections from %s", self)
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
