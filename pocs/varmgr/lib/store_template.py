"""Template-based variable store implementation.

This module provides template-based variable resolution capabilities by extending the base 
StoreManager. It allows variables to be defined using string templates (e.g. ${var_name}) 
which are resolved at runtime.

The main components are:

- StringTemplate: Extended Template class with identifier extraction
- StringTemplateEngine: Engine for parsing and rendering templates 
- RenderableStoreManager: Store manager with template rendering capabilities
- RenderingSettings: Configuration for template rendering behavior

The module handles template parsing, variable substitution, error handling and caching of rendered 
values.
"""

from string import Template
from typing import List, Any, Optional
import logging
from pprint import pprint
from dataclasses import dataclass

from .store_base import StoreManager, UndefinedVarError, VarMgrUserError


logger = logging.getLogger(__name__)
# try:
#     old_value = value
#     value = tpl.substitute(**env)
#     if old_value != value:
#         self.log.trace(
#             f"Transformed template var {hint}: {old_value} => {value}"
#         )

# pylint: disable=too-few-public-methods
class StoreTemplateError(VarMgrUserError):
    """Base class for StoreTemplate exceptions."""


# pylint: disable=too-few-public-methods
class TemplateUndefinedVarError(StoreTemplateError):
    """Exception raised when accessing an undefined variable in a template."""


# pylint: disable=too-few-public-methods
class TemplateValueError(StoreTemplateError):
    """Exception raised when accessing an undefined variable in a template."""


# pylint: disable=too-few-public-methods
class TemplateKeyError(StoreTemplateError):
    """Exception raised when accessing an undefined variable in a template."""


# =====================================================================
# Class overrides
# =====================================================================


class StringTemplate(Template):
    """
    String Template class override to support version of python below 3.11

    # pylint: disable=line-too-long
    Source code: Source: https://github.com/python/cpython/commit/dce642f24418c58e67fa31a686575c980c31dd37
    """

    def get_identifiers(self):
        """Returns a list of the valid identifiers in the template, in the order
        they first appear, ignoring any invalid identifiers."""

        ids = []
        # pylint: disable=invalid-name
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

        # pylint: disable=invalid-name
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

    # @classmethod
    # def is_template(cls, data):
    #     "Return true if template contains template variables"
    #     if not isinstance(data, str):
    #         return False
    #     for _ in cls.pattern.finditer(data):
    #         return True
    #     return False


# We override this method only if version of python is below 3.11
if hasattr(Template, "get_identifiers"):
    StringTemplate = Template  # noqa: F811


# =====================================================================
# TemplateEngines class
# =====================================================================


class _TemplateEngines:
    """Class for managing template engines."""


class _TemplateInstances:
    """A class that wraps a template engine instance and provides methods
    for getting variable names and rendering templates."""


# =====================================================================
# TemplateEngines StringTemplate class
# =====================================================================


class StringTemplateEngine(_TemplateEngines):
    """Python StringTemplate template engine."""

    def __init__(self):
        super().__init__()
        self.engine_cls = StringTemplate
        self._engine = None
        self._value = None

    def is_template(self, data):
        "Return true if template contains template variables"

        # Check if data is a string, otherwize we can't template it
        if not isinstance(data, str):
            return False

        # Check in Python sring.Template config if any opening pattern
        # matches in the text
        for _ in self.engine_cls.pattern.finditer(data):
            return True
        return False

    def get_template(self, value):
        "Return a new engine instance"
        return StringTemplateInstance(value, engine_cls=self.engine_cls)


class StringTemplateInstance(_TemplateInstances):
    """A class that wraps a template engine instance and provides methods for
    getting variable names and rendering templates.

    This class encapsulates a template engine (like string.Template) and provides
    a consistent interface for:
    - Getting the variable names/identifiers used in the template
    - Rendering the template by substituting variables with values
    - Handling template rendering errors
    """

    def __init__(self, value, engine_cls):

        assert isinstance(value, str), "value must be a string"
        assert callable(engine_cls), "engine_cls must be a callable"
        self._value = value
        self.engine_cls = engine_cls
        self._engine = engine_cls(value)

    def get_var_names(self):
        """Return a list of the valid identifiers in the template, in the order they first
        appear, ignoring any invalid identifiers.
        """
        return self._engine.get_identifiers()

    def render(self, dict_vars=None, settings=None, report=None):
        """Render a template by substituting variables with their values.

        Args:
            value (str): The template string to render
            dict_vars (dict): Dictionary mapping variable names to their values
            settings (Settings): Settings object containing rendering options
            report (dict, optional): Dictionary to store rendering metadata. Defaults to None.

        Returns:
            tuple: (rendered_value, report_dict) where rendered_value is the template with
                variables substituted and report_dict contains metadata about the rendering
                process

        Raises:
            TemplateValueError: If template value is invalid and settings.on_value_error is
                Exception
            TemplateKeyError: If variable substitution fails and settings.on_key_error is
                Exception
        """
        dict_vars = dict_vars or {}
        engine = self._engine
        report = report or {}
        value = self._value

        assert isinstance(dict_vars, dict), "dict_vars must be a dict"
        assert isinstance(value, str), "value must be a string"

        # Substitute vars
        report["parse_error"] = None
        report["parsed"] = False
        err = None
        try:
            parsed = engine.substitute(dict_vars)
            report["parsed"] = True
        except (ValueError, KeyError) as _err:
            err = _err

        # Handle error
        if err is not None:
            report["parse_error"] = str(err)
            if isinstance(err, ValueError):
                if settings.on_value_error is Exception:
                    raise TemplateValueError(err, value=value, report=report) from err
                parsed = settings.on_value_error

            elif isinstance(err, KeyError):
                if settings.on_key_error is Exception:
                    raise TemplateKeyError(err, value=value, report=report) from err
                parsed = settings.on_key_error
            else:
                # Unmanaged error, raise general exception
                raise err

        # Build report for children
        if settings.debug:
            report["value"] = parsed
            report["raw_value"] = value

        return parsed


# =====================================================================
# Renderer class
# =====================================================================


@dataclass
class RenderingSettings:
    """Class for keeping track of template settings."""

    on_undefined_error: Any = Exception
    on_value_error: Any = Exception
    on_key_error: Any = Exception
    debug: bool = False
    cache: bool = True


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
        # self.tpl_engine = StringTemplate

        self.engine = StringTemplateEngine()

    def render_values(self, **kwargs):
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
        self,
        var_name: str,
        _seen: List[str] = None,
        _lvl=None,
        debug=False,
        cache=True,
        settings=None,
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
            settings: RenderingSettings instance to control error handling and behavior.
                     If None, default settings will be used.

        Returns:
            str: The rendered variable value with all template references resolved.
            If debug=True, returns a tuple of (value, debug_info).

        Raises:
            UndefinedVarError: If the variable or any referenced variables don't exist
                              and settings.on_undefined_error is Exception.
            ValueError: If circular references are detected.
            TemplateUndefinedVarError: If a variable is undefined and
                                      settings.on_undefined_error is Exception.
        """

        # 0. Init vars
        _seen = _seen or []
        _lvl = _lvl or 0

        # 1. Init config
        pprint(settings)
        settings = settings or RenderingSettings(
            on_undefined_error=Exception,
            on_value_error=Exception,
            on_key_error=Exception,
            debug=debug,
            cache=cache,
        )
        assert isinstance(
            settings, RenderingSettings
        ), "settings must be a RenderingSettings instance"
        debug = settings.debug
        cache = settings.cache

        # 2. Init report
        logger.info("Renderer: Rendering var%d: %s", _lvl, var_name)
        _report = {
            "key": var_name,
            "level": _lvl,
            "parsed": False,
            "cache": False,
            "cached": False,
        }

        # 3. Check cache
        if cache and var_name in self._cache:
            out = self._cache[var_name]
            _report["cache"] = True
            if debug:
                return out, _report
            return out

        # 4. Fetch and process variable
        value = self.store.get_value(var_name, scope=self.scope)
        _report["value"] = value
        _report["parsed"] = False

        # 5. Process template variables, if possible/requested
        tpl_engine = self.engine
        if not tpl_engine.is_template(value):
            _report["templated"] = False

        else:
            _report["templated"] = True

            # Inject text into template engine
            template = tpl_engine.get_template(value)

            # Fetch template variable names from string
            # and recursively resolve template variables values
            var_names = template.get_var_names()
            dict_vars = self._render_var_template1(
                var_names=var_names,
                settings=settings,
                seen=_seen,
                lvl=_lvl,
                report=_report,
            )

            # Try to parse value with dict_vars
            value = template.render(
                dict_vars=dict_vars,
                settings=settings,
                report=_report,
            )

        # Save in cache
        if cache:
            self._cache[var_name] = value
            _report["cached"] = True

        # Return value
        if debug:
            return value, _report
        return value

    # pylint: disable=too-many-arguments,too-many-locals
    def _render_var_template1(
        self,
        var_names=None,
        settings=None,
        # Forwarded args
        report=None,
        seen=None,
        lvl=None,
    ):
        """Render a template by resolving all variable references.

        Args:
        """

        report = report or {}
        _lvl = lvl or 0
        seen = seen or []
        debug = settings.debug

        # DATA BUILDER

        # Recursive value names resolver
        _children = {}
        dict_vars = {}
        template_keys = var_names
        for key in template_keys:

            # Check for circular references
            if key in seen:
                circular_ref = " -> ".join(seen + [key])
                msg = f"Circular reference detected: {circular_ref}"
                raise ValueError(msg)
            new_seen = seen + [key]

            # Recursive resolve vars
            try:
                value = self.render_var(
                    key,
                    _seen=new_seen,
                    _lvl=_lvl + 1,
                    # debug=debug,
                    settings=settings,
                )
            except UndefinedVarError as err:
                # pprint(err.__dict__)
                if settings.on_undefined_error is Exception:
                    msg = (
                        f"Renderer: Variable '{key}' not found, "
                        "set on_undefined_error=False to change this behavior"
                    )
                    err_kwargs = {
                        "variable": key,
                        "report": report,
                    }
                    raise TemplateUndefinedVarError(msg, **err_kwargs) from err

                value = settings.on_undefined_error

                if debug:
                    report = err.kwargs.get("report", None)
                    value = [value, report]
                    if report:
                        print("Renderer: Variable not found, skipping")
                        pprint(report)

            # Depack arguments in debug mode
            if debug:
                subreport = value[1]
                value = value[0]
                _children[key] = subreport

            dict_vars[key] = value

        # Build report for children
        if debug:
            report["children"] = _children

        return dict_vars


class RenderableStoreManager(StoreManager):
    """
    A class to manage variables and their sources.
    """

    def __init__(self):
        self._renderer_cache = {}

        super().__init__()

    def get_renderer(self, scope_name: Optional[str] = None) -> Renderer:
        """Get or create a Renderer instance for the given scope.

        Args:
            scope_name (Optional[str], optional): The scope name to get a renderer for.
                If None, uses the default scope. Defaults to None.

        Returns:
            Renderer: A Renderer instance configured for the specified scope.
                The same instance will be returned for subsequent calls with the same scope.
        """

        # scope_name = scope_name or "default"

        # Return from cache
        if scope_name and scope_name in self._renderer_cache:
            return self._renderer_cache[scope_name]

        # Create and save object
        renderer = Renderer(store=self, scope=scope_name)
        self._renderer_cache[scope_name] = renderer
        return renderer
