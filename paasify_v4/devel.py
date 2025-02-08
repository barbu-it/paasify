from pprint import pprint
from typing import List, Dict
from dataclasses import dataclass
from types import SimpleNamespace

from pathlib import Path

from superconf.anchors import PathAnchor


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

        # self.test_coll = id(parent)

        # # self.collection_dir = parent
        # self.collection = parent
        # self.collection_path = self.collection.parent
        # self.catalog = self.collection_path.parent


#     def get_info(self):
#         "Return application info"


#     @property
#     def path(self):
#         "Return collection ident"
#         # return str(self.sub_path)
#         return str(Path(self.collection.sub_path , self.sub_path))


class CollectionObj(AppNode):
    "CollectionObj class"

    def __init__(self, ident, path=None, parent=None, index=None):
        assert isinstance(parent, CollectionsPath)
        super().__init__(ident, parent)

        self.sub_path = path
        self.index = index
        self._store_apps = {}

        # self.collection_path = parent

    #     # def __repr__(self):
    #     #     return f"{self.__class__.__name__}({self.ident}.{self.index})"

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
        # collection_path = self.sub_path

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


#     def setup_node(self, paths=None):
#         "Init node"
#         # print ("WALK COLLECTION NODE", self)

#         self._store_apps = self.walk_apps()
#         # print ("WALK COLLECTION NODE", self)
#         # pprint(self._store_apps)

#     @requires_setup_node
#     def dump(self):
#         "Dump collection"
#         print(f"Dump of {self}:")
#         pprint(self.__dict__)


#     @requires_setup_node
#     def get_apps(self, name=None):
#         "Return apps"
#         if name is None:
#             return self._store_apps or {}
#         return self._store_apps.get(name, None)


##############################################################


class CollectionsPath(AppNode):
    "CollectionsPath class"

    def __init__(self, ident, parent=None, path=None, index=None):
        assert isinstance(parent, AppCatalog)
        super().__init__(ident, parent)
        # assert isinstance(parent, (type(None), CollectionObj))

        self.path = path
        self.index = index
        # self.catalog = parent
        self._store_collections = {}

    @requires_setup_node
    def get_collections(self):
        "Return collections"
        return self._store_collections.values()

    def setup_node(self):
        path = self.path
        self._store_collections = self.walk_collections(path)

    def walk_collections(self, collections_path) -> Dict:
        "Walk collections directories and return scan report"

        # print("WALK COLLECTIONS DIRECTORY FOR APPS", collections_path)

        out = {}
        # List all directories names
        for dir_path in Path(collections_path).iterdir():
            # Dir_path must be a directory
            # print("T1", dir_path)
            if not dir_path.is_dir():
                continue
            # Fetch the directory name
            dir_name = dir_path.name

            # print("T2", dir_name)

            # collection = CollectionObj(
            collection = CollectionObj(
                ident=dir_name,
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


class AppCatalog(AppNode):
    "Catalog class, manage list of collections paths"

    def __init__(self, collections_paths=None):
        super().__init__()

        # Settings attributes
        self.collections_paths = collections_paths

        # Caching attributes
        # self._cached_collections_paths = None

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
        print("INIT NODE STARTED WALK", paths)

        self._store_paths = self.walk_collections_paths(paths)
        # self._store_collections = self.walk_collections(self._store_paths)

        # self._store_apps =
        # self.walk_applications()

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

    ##########################

    @requires_setup_node
    def dump(self):

        print(f"Dump of {self}:")
        pprint(self.__dict__)

        print("Dump of collections")
        for _, collection in self._store_collections.items():
            collection.dump()

    @requires_setup_node
    def get_app(self, ident):

        for collection in self._store_collections.values():
            app = collection.get_apps(ident)
            if app is not None:
                return app
        return None

    @requires_setup_node
    def get_apps(self):
        "Dump apps"
        print("Dump of apps")
        # pprint(self._store_apps)

        out = {}
        out2 = {}
        out3 = []
        for collection in self._store_collections.values():
            print("COLLECTION", collection)
            # return collection.get_apps()
            # out.update(collection.get_apps())
            # out2[collection.ident]= collection #collection.get_apps()
            out2[collection.ident] = []

            for app in collection.get_apps().values():
                print("APP", app)
                out2[collection.ident].append(app.ident)
                out[app.ident] = app.collection
                out3.append(app)

        return out3

    # @requires_setup_node
    # def get_collections_names(self):
    #     "Return list of collections names"
    #     ret = []
    #     for collection in self._db:
    #         ret.extend(collection.get_app_names())
    #     return ret

    # @requires_setup_node
    # def get_collection_by_name(self, name):
    #     "Return collection by name"
    #     print(f"Show collection name: {name}")
    #     for collection in self._db:
    #         if name in collection.get_app_names():
    #             return collection
    #     return None

    # @requires_setup_node
    # def show_applications(self):
    #     "Show applications"
    #     for collection_path in self.collections_paths:
    #         print(f"Collection: {collection_path}")

    #         # List all directories containing a docker-compose.yml file
    #         for dir_path in Path(collection_path).rglob("docker-compose.yml"):
    #             print(f"Application: {dir_path}")
