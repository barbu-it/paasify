
from pprint import pprint
from types import SimpleNamespace

DEFAULT_LEVEL = 500



class VarMgrError(Exception):
    """Base class for all VarMgr errors."""

class VarMgrAppError(VarMgrError):
    """Base class for Application VarMgr errors."""


class AlreadyExistingSourceError(VarMgrAppError):
    """Error raised when a source already exists."""

class VarMgrUserError(VarMgrError):
    """Base class for User VarMgr errors."""

class UndefinedVarError(VarMgrUserError):
    """Error raised when a variable is not found."""


class Source:

    def __init__(self, name: str, level: int=None):
        self.name = name
        self.level = level



class Varmgr:

    middle_level = DEFAULT_LEVEL

    def __init__(self):


        self.layered_store = {}
        self.store = {}
        self.order = []


    def set_order(self, order):
        """Define source order.
        
        The order is a list of Source objects.
        """
        assert isinstance(order, list)

        names = []
        out = []
        for idx, item in enumerate(order):
            assert isinstance(item, Source)
            level = item.level
            if not isinstance(level, int):
                item.level = self.middle_level + idx
            out.append(item)

            name = item.name
            if name in names:
                raise AlreadyExistingSourceError(f"Source {name} already exists")
            names.append(name)

        # Then order the out list by level
        self.order = sorted(out, key=lambda x: x.level)


        pprint(self.order)


    def _get_source_by_name(self, name):
        for item in self.order:
            if item.name == name:
                return item
        return None


    def import_source(self, name, dataset, **kwargs):
        """Import a source into the layered store.
        
        The source is identified by its name.
        """

        source = self._get_source_by_name(name)
        if source is None:
            raise VarMgrAppError(f"Source {name} not found")
        
        self.layered_store[source.name] = SimpleNamespace(
            # "level": source.level,
            source=source,
            payload=dataset,
            meta=kwargs,
            )
        

    # alias for __contains__
    def get_all_var_names(self):
        """Get all variable names."""
        all_names = list()
        for item in self._iter_items():
            # pprint(item)
            all_names.extend(list(item.payload.keys()))
        return list(sorted(set(all_names)))
    

    def _iter_items(self):
        """Iterate over items in order of level."""
        return sorted(self.layered_store.values(), key=lambda x: x.source.level)

    def get_value(self, name):
        """Get the value of a variable.
        
        If the variable is not found, raise an UndefinedVarError.
        """

        # TODO: Add meta data to the variable
        # pprint(list(self._iter_items()))

        for item in self._iter_items():
            if name in item.payload:
                return item.payload[name]
            
        raise UndefinedVarError(f"Variable {name} not found")


    def dump(self):
        return self.layered_store
