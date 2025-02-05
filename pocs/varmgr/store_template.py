from string import Template
from typing import List, Dict, Any, Union, Optional, Iterator, TypeVar
import logging
from pprint import pprint

from store_base import StoreManager, Source, UndefinedVarError, VarMgrUserError


logger = logging.getLogger(__name__)
# try:
#     old_value = value
#     value = tpl.substitute(**env)
#     if old_value != value:
#         self.log.trace(
#             f"Transformed template var {hint}: {old_value} => {value}"
#         )

class StoreTemplateError(VarMgrUserError):
    """Base class for StoreTemplate exceptions."""


class TemplateUndefinedVarError(StoreTemplateError):
    """Exception raised when accessing an undefined variable in a template."""


# =====================================================================
# Class overrides
# =====================================================================


class StringTemplate(Template):
    """
    String Template class override to support version of python below 3.11

    Source code: Source: https://github.com/python/cpython/commit/dce642f24418c58e67fa31a686575c980c31dd37
    """

    def get_identifiers(self):
        """Returns a list of the valid identifiers in the template, in the order
        they first appear, ignoring any invalid identifiers."""

        ids = []
        for mo in self.pattern.finditer(self.template):
            named = mo.group("named") or mo.group("braced")
            if named is not None and named not in ids:
                # add a named group only the first time it appears
                ids.append(named)
            elif (
                named is None
                and mo.group("invalid") is None
                and mo.group("escaped") is None
            ):
                # If all the groups are None, there must be
                # another group we're not expecting
                raise ValueError("Unrecognized named group in pattern", self.pattern)
        return ids

    def is_valid(self):
        """Returns false if the template has invalid placeholders that will cause
        :meth:`substitute` to raise :exc:`ValueError`.
        """

        for mo in self.pattern.finditer(self.template):
            if mo.group("invalid") is not None:
                return False
            if (
                mo.group("named") is None
                and mo.group("braced") is None
                and mo.group("escaped") is None
            ):
                # If all the groups are None, there must be
                # another group we're not expecting
                raise ValueError("Unrecognized named group in pattern", self.pattern)
        return True

    @classmethod
    def is_template(cls, data):
        "Return true if template contains template variables"
        if not isinstance(data, str):
            return False
        for _ in cls.pattern.finditer(data):
            return True
        return False


# We override this method only if version of python is below 3.11
if hasattr(Template, "get_identifiers"):
    StringTemplate = Template  # noqa: F811


class Renderer:
    """A class that renders template variables by resolving references.

    The Renderer class handles resolving template variables in a given scope,
    processing any nested references and caching results for efficiency.

    Args:
        store: The variable store containing the values to render.
        scope: The scope name to limit variable resolution.
    """

    def __init__(self, store, scope: str):
        self.store = store
        self.scope = scope
        self._cache = {}

        self.sources = store.get_ordered_sources(scope=scope)
        self.tpl_engine = StringTemplate

    def render_values(self, debug=False, **kwargs):
        """Get all variables and their rendered values.

        This method retrieves all variables in the current scope and renders their values,
        resolving any template references. The rendered values can be cached to avoid
        redundant processing.

        Args:
            cache: Whether to cache rendered values for reuse. Defaults to True.

        Returns:
            Dict[str, Any]: Dictionary mapping variable names to their rendered values.
        """

        _out = {}
        for var_name in self.store.get_var_names(scope=self.scope):
            _out[var_name] = self.render_var(var_name, **kwargs)

        return _out

    def render_var(
        self, var_name: str, _seen: List[str] = None, _lvl=None, 
        debug=False, cache=True,
        value_on_undefined: Any = Exception,
        value_on_parse: Any = Exception,
    ) -> str:
        """Render a variable value, resolving any template references.

        This method retrieves the value of a variable and processes any template
        references (variables enclosed in curly braces) within it. It handles nested
        references recursively and can cache results for better performance.

        Args:
            var_name: Name of the variable to render.
            _seen: List of variables seen during recursive resolution to detect cycles.
            _lvl: Current recursion level for debugging.
            debug: Whether to return additional debug information.
            cache: Whether to cache rendered values for reuse.

        Returns:
            str: The rendered variable value with all template references resolved.
            If debug=True, returns a tuple of (value, debug_info).

        Raises:
            UndefinedVarError: If the variable or any referenced variables don't exist.
            ValueError: If circular references are detected.
        """

        # Init vars
        _seen = _seen or []
        _lvl = _lvl or 0

        # Init report
        if debug:
            _report = {}
            _report["key"] = var_name
            _report["level"] = _lvl
            _report["parsed"] = False

        logger.info("Renderer: Rendering var%d: %s", _lvl, var_name)

        # Check cache
        if cache and var_name in self._cache:
            out = self._cache[var_name]
            if debug:
                _report["cache"] = True
                return out, _report
            return out
        if debug:
            _report["cache"] = False

        # Fetch and process variable
        value = self.store.get_value(var_name, scope=self.scope)

        # Process template variables
        if not self.tpl_engine.is_template(value):
            if debug:
                _report["templated"] = False
                _report["value"] = value

        else:

            _children = {}
            engine = self.tpl_engine(value)

            # Recursive value names resolver
            dict_vars = {}
            template_keys = engine.get_identifiers()
            for key in template_keys:

                # Check for circular references
                if key in _seen:
                    circular_ref = " -> ".join(_seen + [key])
                    msg = f"Circular reference detected: {circular_ref}"
                    raise ValueError(msg)
                new_seen = _seen + [key]

                # Recursive resolve vars
                try:    
                    value = self.render_var(
                        key, _seen=new_seen, _lvl=_lvl + 1, debug=debug, cache=cache
                    )
                except UndefinedVarError as err :
                    # pprint(err.__dict__)
                    if value_on_undefined is Exception:
                        msg = (
                            f"Renderer: Variable '{key}' not found, "
                            "set value_on_undefined=False to change this behavior"
                        )
                        err_kwargs = {
                            "variable": key,
                            "report": _report if debug else None,
                        }
                        raise TemplateUndefinedVarError(msg, **err_kwargs) from err

                    value = value_on_undefined

                    if debug:
                        report = err.kwargs.get("report", None)
                        value = [value, report]
                        if report:
                            print("Renderer: Variable not found, skipping")
                            pprint(report)
                        

                # Build report for children
                if debug:
                    subreport = value[1]
                    value = value[0]
                    _children[key] = subreport

                dict_vars[key] = value

            # Substitute vars
            try:
                parsed = engine.substitute(dict_vars)
                if debug:
                    _report["parsed"] = True
            except ValueError as e:
                if value_on_parse is Exception:
                    msg = (
                        f"Renderer: Error parsing template '{var_name}' with value '{value}'"
                    )
                    raise ValueError(msg) from e

                parsed = value_on_parse


                # Happens with bad template value:
                #  - "test'$'test"
                logger.warning("Error substituting %s='%s' vars: %s", var_name, value, e)
                if debug:
                    _report["parsed"] = str(e)
                parsed = value

            # Build report for children
            if debug:
                _report["children"] = _children
                _report["value"] = parsed
                _report["raw_value"] = value
                _report["templated"] = True

            value = parsed

        # Save in cache
        cached = False
        if cache:
            self._cache[var_name] = value
            cached = True

        # Return value
        if debug:
            _report["cached"] = cached
            return value, _report
        return value


class RenderableStoreManager(StoreManager):
    """
    A class to manage variables and their sources.
    """

    def __init__(self):
        self._renderer_cache = {}

        super().__init__()

    def get_renderer(self, scope_name: Optional[str] = None) -> Renderer:

        # scope_name = scope_name or "default"

        # Return from cache
        if scope_name and scope_name in self._renderer_cache:
            return self._renderer_cache[scope_name]

        # Create and save object
        renderer = Renderer(store=self, scope=scope_name)
        self._renderer_cache[scope_name] = renderer
        return renderer
