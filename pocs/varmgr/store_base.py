from pprint import pprint

# from types import SimpleNamespace
# from collections import OrderedDict
from typing import List, Dict, Any, Union, Optional, Iterator, TypeVar

DEFAULT_LEVEL = 500

T = TypeVar("T")


def flatten2(array: List[Any]) -> List[Any]:
    """Flatten any nested arrays while preserving inner values but not ordering.

    Args:
        array: A list that may contain nested lists at any depth.

    Returns:
        List[Any]: A flattened list containing all elements from input arrays.

    Example:
        >>> flatten2([[1, 2], [3, 4]])
        [1, 2, 3, 4]
    """
    if array == []:
        return array
    if isinstance(array[0], list):
        return flatten(array[0]) + flatten(array[1:])
    return array[:1] + flatten(array[1:])


def flatten(nested: Any, depth: int = 0) -> Iterator[Any]:
    """Flatten nested iterables while preserving ordering.

    Args:
        nested: Any potentially nested iterable structure.
        depth: Current recursion depth, used internally for debugging.

    Returns:
        Iterator[Any]: A generator yielding flattened elements in order.

    Example:
        >>> list(flatten([[1, 2], [3, 4]]))
        [1, 2, 3, 4]
    """
    try:
        # print("{}Iterate on {}".format('  '*depth, nested))
        for sublist in nested:
            for element in flatten(sublist, depth + 1):
                # print("{}got back {}".format('  '*depth, element))
                yield element
    except TypeError:
        # print('{}not iterable - return {}'.format('  '*depth, nested))
        yield nested


class VarMgrError(Exception):
    """Base class for all VarMgr exceptions.

    This class serves as the root of the VarMgr exception hierarchy.
    """

    def __init__(self, msg: str, **kwargs: Any):
        self.msg = msg
        self.kwargs = kwargs

    def __str__(self) -> str:
        prefix = f"{self.msg}"
        if self.kwargs:
            # kwargs_str = ", ".join([f"{k}={v}" for k, v in self.kwargs.items()])
            kwargs_str = ", ".join([f"{k}" for k, _ in self.kwargs.items()])
            return f"{prefix} ({kwargs_str})"
        return prefix


class VarMgrAppError(VarMgrError):
    """Base class for Application-level VarMgr exceptions.

    These exceptions indicate errors in the application's configuration or setup.
    """


class AlreadyExistingSourceError(VarMgrAppError):
    """Exception raised when attempting to add a source that already exists.

    This error occurs when trying to register a source with a name that is already in use.
    """


class ReferenceToMissingSourceError(VarMgrAppError):
    """Exception raised when referencing a non-existent source.

    This error occurs when trying to use a source that hasn't been registered.
    """


class VarMgrUserError(VarMgrError):
    """Base class for User-level VarMgr exceptions.

    These exceptions indicate errors in user input or usage.
    """


class UndefinedVarError(VarMgrUserError):
    """Exception raised when accessing an undefined variable.

    This error occurs when trying to access a variable that doesn't exist in any layer.
    """


class Source:
    """Represents a named source with optional level and help text.

    A Source is a fundamental unit in the variable management system that
    represents where variables come from. Sources can be ordered by level
    for precedence handling.

    Args:
        name: Unique identifier for the source.
        level: Optional priority level for source ordering (lower numbers have higher priority).
        help: Optional help text describing the source's purpose.
    """

    # pylint: disable=redefined-builtin
    def __init__(
        self, name: str, level: Optional[int] = None, help: Optional[str] = None
    ):
        self.name = name
        self.level = level
        self.help = help

    def __repr__(self) -> str:
        return f"Source({self.name}, {self.level})"

    def get_help(self) -> str:
        if not self.help:
            return f"Source {self.name}"
        return self.help


class Scope:
    """Represents a named collection of sources.

    A Scope groups related sources together and can be used to limit
    variable resolution to a specific set of sources.

    Args:
        name: Unique identifier for the scope.
    """

    def __init__(self, name: str):
        self.name = name

    def __repr__(self) -> str:
        return f"Scope({self.name})"


class Layer:
    """Represents a data layer containing variables from a specific source.

    A Layer combines a source with its actual data (payload) and metadata.
    It serves as a container for variables from a particular source.

    Args:
        source: The Source object this layer is associated with.
        payload: Dictionary containing the actual variables and their values.
        meta: Dictionary containing metadata about this layer.
    """

    def __init__(self, source: Source, payload: Dict[str, Any], meta: Dict[str, Any]):
        self.source = source
        self.payload = payload
        self.meta = meta

    def __repr__(self) -> str:
        return f"Layer({self.source.name})"


class StoreManager:
    """
    A class to manage variables and their sources.
    """

    middle_level = DEFAULT_LEVEL

    def __init__(self):

        self.layered_store: Dict[str, Layer] = {}
        self.store: Dict[str, Any] = {}
        self.order: List[str] = []
        self._sources: Dict[str, Source] = {}
        self._scopes: Dict[str, List[Source]] = {}

    # SourcesScopes managements
    # ====================

    def add_sources(self, args: Union[List[Source], Source], force: bool = False) -> None:
        """Register one or more sources with the variable manager.

        Args:
            args: Either a single Source object or a list of Source objects to register.

        Raises:
            ValueError: If the arguments are not of the expected type.
            AlreadyExistingSourceError: If a source with the same name already exists.
        """

        if isinstance(args, list):
            for source in args:
                assert isinstance(source, Source)
                self._sources[source.name] = source
        elif isinstance(args, Source):
            if args.name in self._sources and not force:
                raise AlreadyExistingSourceError(
                    f"Source {args.name} already exists, use force to override",
                    name = args.name,
                    arg = args
                    )
            self._sources[args.name] = args
        else:
            raise ValueError(f"Invalid number of arguments: {len(args)}")

    def set_scopes(self, *args: Union[Dict[str, List[str]], str, List[str]]) -> None:
        """Define scopes for variable resolution.

        Args:
            *args: Either a dict mapping scope names to source lists,
                  or a scope name and its source list as separate arguments.

        Raises:
            ValueError: If the number or type of arguments is invalid.
            VarMgrAppError: If referenced sources don't exist or if there are circular references.
        """

        # Process arguments
        obj_scopes = dict(self._scopes)
        if len(args) == 1:
            scopes = args[0]
            assert isinstance(scopes, dict)
            obj_scopes.update(scopes)
        elif len(args) == 2:
            name, scope = args
            assert isinstance(scope, list)
            obj_scopes[name] = scope
        else:
            raise ValueError(f"Invalid number of arguments: {len(args)}")

        # recursive scope solver
        def scope_solver(scope_name, scope_items, scopes, sources, _seen=None):
            """Resolve scopes recursively."""
            # print(f"scope_solver({scope_name}, {scope_items}, SEEN={_seen})")
            assert isinstance(scope_items, list)

            _seen = _seen or []

            out = []
            for item_ref in scope_items:
                if item_ref in sources:
                    # This is a source, direct resolve instead of recursivity
                    source = sources[item_ref]
                    assert isinstance(source, Source)
                    out.append(source)

                elif item_ref in scopes:
                    # Check for recursion loops
                    if item_ref in _seen:
                        stack = " -> ".join([scope_name] + _seen)
                        raise VarMgrAppError(
                            f"Scope '{scope_name}' is recursive: {stack}",
                            scope_name = scope_name,
                            stack = list([scope_name] + _seen),
                        )
                    _seen.append(item_ref)

                    # Register children
                    # out.append(Scope(item_ref))
                    out.append(
                        scope_solver(item_ref, scopes[item_ref], scopes, sources, _seen)
                    )

                else:
                    raise VarMgrAppError(
                        f"Item '{item_ref}' not found in sources or scopes",
                        item_ref = item_ref,
                        scope_name = scope_name,
                    )

            return out

        # Register scopes
        _out = {}
        for scope_name, items_list in obj_scopes.items():
            _out[scope_name] = list(
                flatten(scope_solver(scope_name, items_list, scopes, self._sources))
            )

        self._scopes = _out

    def get_ordered_sources(self, scope: Optional[str] = None) -> List[Source]:
        """Retrieve sources in priority order, optionally filtered by scope.

        Args:
            scope: Optional scope name to filter sources.

        Returns:
            List of Source objects ordered by their level (or middle_level if not specified).
            If scope is provided, returns only sources in that scope.

        Raises:
            KeyError: If the specified scope doesn't exist.
        """

        def lvl_sorter(item):
            lvl = item.level
            if lvl is None:
                lvl = self.middle_level
            return lvl

        if scope is None:
            ret = sorted(self._sources.values(), key=lvl_sorter)
            return ret

        # Return names only
        return self._scopes[scope]

    def get_source_names(self, scope: Optional[str] = None) -> List[str]:
        """Get names of all sources, optionally filtered by scope.

        Args:
            scope: Optional scope name to filter sources.

        Returns:
            List of source names in priority order.

        Raises:
            KeyError: If the specified scope doesn't exist.
        """
        return [x.name for x in self.get_ordered_sources(scope)]

    # Sources management
    # ====================

    # AKA set_layer
    def set_layer(
        self, source_name: str, dataset: Dict[str, Any], **kwargs: Any
    ) -> None:
        """Import a dataset as a new layer for a specific source.

        Args:
            source_name: Name of the source to import data for.
            dataset: Dictionary containing the variables and their values.
            **kwargs: Additional metadata to store with the layer.

        Raises:
            VarMgrAppError: If the specified source doesn't exist.
        """

        source = self._sources.get(source_name, None)
        if source is None:
            raise VarMgrAppError(f"Source {source_name} not found", 
                                 source_name=source_name)

        self.layered_store[source_name] = Layer(
            # "level": source.level,
            source=source,
            payload=dataset,
            meta=kwargs,
        )

    def get_ordered_layers(self, scope: Optional[str] = None) -> List[Layer]:
        """Retrieve layers in priority order, optionally filtered by scope.

        Args:
            scope: Optional scope name to filter layers.

        Returns:
            List of Layer objects ordered by their source's priority.

        Raises:
            KeyError: If the specified scope doesn't exist.
        """

        accepted_sources = self.get_ordered_sources(scope=scope)

        out = []
        for source in accepted_sources:
            if source.name in self.layered_store:
                out.append(self.layered_store[source.name])

        return out

    def show_sources_help(self, scope: Optional[str] = None) -> None:
        """Display help information for all sources, optionally filtered by scope.

        Args:
            scope: Optional scope name to filter sources.

        Raises:
            KeyError: If the specified scope doesn't exist.
        """

        scope_name = scope or "default"
        print(f"Sources for '{scope_name}':")
        for idx, source in enumerate(self.get_ordered_sources(scope=scope)):
            print(f"  {idx:3d}. {source.get_help()}")

    # Vars managements
    # ====================

    def get_var_names(self, scope: Optional[str] = None) -> List[str]:
        """Get names of all variables, optionally filtered by scope.

        Args:
            scope: Optional scope name to filter variables.

        Returns:
            List of variable names.
        """
        _out = []
        for layer in self.get_ordered_layers(scope=scope):
            _out.extend(list(layer.payload.keys()))

        _out = list(set(_out))
        return _out

    def get_var(
        self, name: str, scope: Optional[str] = None, debug: bool = False
    ) -> Union[Layer, List[Layer]]:
        """Retrieve variable information from the first (or all) layers containing it.

        Args:
            name: Name of the variable to look up.
            scope: Optional scope name to limit the search.
            debug: If True, return all layers containing the variable instead of just the first.

        Returns:
            If debug is False, returns the first Layer containing the variable.
            If debug is True, returns a list of all Layers containing the variable.

        Raises:
            UndefinedVarError: If the variable is not found in any layer.
            KeyError: If the specified scope doesn't exist.
        """
        _out = []
        for layer in self.get_ordered_layers(scope=scope):
            payload = layer.payload
            if name in payload:
                _out.append(layer)
                if not debug:
                    return layer

        if not _out:
            raise UndefinedVarError(f"Variable '{name}' not found", variable=name)

        return _out

    def inspect_var(self, name: str, scope: Optional[str] = None) -> List[Layer]:
        """Inspect all layers containing a specific variable.

        Args:
            name: Name of the variable to inspect.
            scope: Optional scope name to limit the search.

        Returns:
            List of all layers containing the variable, in priority order.

        Raises:
            UndefinedVarError: If the variable is not found in any layer.
            KeyError: If the specified scope doesn't exist.
        """
        return self.get_var(name, scope=scope, debug=True)

    def get_value(self, name: str, scope: Optional[str] = None) -> Any:
        """Get the value of a variable from the highest priority layer.

        Args:
            name: Name of the variable to retrieve.
            scope: Optional scope name to limit the search.

        Returns:
            The value of the variable from the highest priority layer.

        Raises:
            UndefinedVarError: If the variable is not found in any layer.
            KeyError: If the specified scope doesn't exist.
        """
        return self.get_var(name, scope=scope).payload[name]

    def get_values(self, scope: Optional[str] = None) -> Dict[str, Any]:
        """Get all variables and their values, respecting layer priority.

        Args:
            scope: Optional scope name to limit the search.

        Returns:
            Dictionary mapping variable names to their values from the highest priority layer.

        Raises:
            KeyError: If the specified scope doesn't exist.
        """
        out = {}
        order = self.get_ordered_layers(scope=scope)
        for layer in order:
            for key, val in layer.payload.items():
                if key not in out:
                    out[key] = val
                    # out[key] = self.get_value(key, scope=scope)
                    # print(f"WARNING: {key} already exists in {layer.source.name}")
        return out
