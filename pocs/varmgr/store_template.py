from string import Template
from typing import List, Dict, Any, Union, Optional, Iterator, TypeVar
import logging
from pprint import pprint
from dataclasses import dataclass

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


class TemplateValueError(StoreTemplateError):
    """Exception raised when accessing an undefined variable in a template."""

class TemplateKeyError(StoreTemplateError):
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




# TemplateEngines class
# =====================================================================

class TemplateEngines:
    """Class for managing template engines."""

    def __init__(self):
        self.engines = {}


class PythonTemplateEngine(TemplateEngines):
    """Python template engine."""

    def __init__(self):
        super().__init__()
        self.engine_cls = StringTemplate
        self.engine = None
        self.value = None

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
    

    # Inited object only!!!!


    def init_engine(self, value):
        "Return a new engine instance"
        assert self.engine is not  None, "Engine is not inited yet!"
        self.engine = self.engine_cls(value)
        self.value = value

        return self.engine

    def get_var_names(self):
        "Return a list of the valid identifiers in the template, in the order they first appear, ignoring any invalid identifiers."
        assert self.engine is not  None, "Engine is not inited yet!"
        return self.engine.get_identifiers()


    def _render_var_template2(self, parent,
            # var_name=None,
            value=None,
            dict_vars=None, 
            settings=None,
            engine=None, 
            report=None,
        ):  

        assert self.engine is not  None, "Engine is not inited yet!"

        #### RESOLVER
        report = report or {}
        debug = settings.debug
        # engine = self.engine


        # Substitute vars
        try:
            parsed = engine.substitute(dict_vars)
            report["parsed"] = True
        except ValueError as e:
            parsed = value

            if settings.on_value_error is Exception:
                msg = (
                    f"Renderer: Error parsing template value '{value}'"
                    "set on_value_error='<default_value>' to change this behavior"
                )
                raise TemplateValueError(msg, value=value, report=report) from e

            parsed = settings.on_value_error

            # Happens with bad template value:
            #  - "test'$'test"
            logger.warning("Error substituting '%s' vars: %s", value, e)
            report["parsed"] = str(e)

        except KeyError:

            if settings.on_parse_error is Exception:
                msg = (
                    f"Renderer: Error parsing template value '{value}'"
                    "set on_parse_error='<default_value>' to change this behavior"
                )
                raise TemplateKeyError(msg, value=value, report=report) from e


            assert False, "Notimplemented"


        # Build report for children
        if debug:
            report["value"] = parsed
            report["raw_value"] = value
            report["templated"] = True

        return parsed, report




# Renderer class
# =====================================================================


@dataclass
class RenderingSettings:
    """Class for keeping track of an item in inventory."""

    on_undefined_error: Any = Exception
    on_value_error: Any = Exception
    on_parse_error: Any = Exception
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
        self.tpl_engine = StringTemplate

        self.engine = PythonTemplateEngine()

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
        debug=False, 
        cache=True,
        # on_undefined_error: Any = Exception,
        # on_value_error: Any = Exception,
        # on_parse_error: Any = Exception,
        # on_undefined_error: Any = Exception, 
        # on_value_error: Any = Exception, 
        # on_parse_error: Any = Exception,
        settings = None,
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

        settings = settings or RenderingSettings(
            on_undefined_error=Exception,
            on_value_error=Exception,
            on_parse_error=Exception,
            debug=debug,
            cache=cache,
        )
        assert isinstance(settings, RenderingSettings), "settings must be a RenderingSettings instance"

        # Init report
        _report = {}
        _report["key"] = var_name
        _report["level"] = _lvl
        _report["parsed"] = False
        logger.info("Renderer: Rendering var%d: %s", _lvl, var_name)

        # Check cache
        if settings.cache and var_name in self._cache:
            out = self._cache[var_name]
            _report["cache"] = True
            if debug:
                return out, _report
            return out
        _report["cache"] = False

        # Fetch and process variable
        value = self.store.get_value(var_name, scope=self.scope)
        _report["value"] = value
        _report["parsed"] = False

        # Process template variables
        # if not self.tpl_engine.is_template(value):
        if not self.engine.is_template(value):
            _report["templated"] = False

        else:
            _report["templated"] = True

            # Inject text into template engine
            # engine = self.tpl_engine(value)
            engine = self.engine.init_engine(value)

            # Fetch template variable names from string
            # var_names = engine.get_identifiers()
            var_names = self.engine.get_var_names()

            # Recursive resolve template variables values
            dict_vars, _report = self._render_var_template1(
                var_names=var_names,
                settings=settings,

                seen=_seen,
                lvl=_lvl,

                report=_report,
            )


            # Try to parse value with dict_vars
            try:
                # value, _report = self._render_var_template2(
                value, _report = self.engine._render_var_template2(
                    self,
                    value=value,
                    dict_vars=dict_vars,
                    settings=settings,

                    engine=engine, 
                    report=_report,
                )
            except (TemplateValueError,  TemplateKeyError) as err:
                msg=f"Renderer: Error parsing template '{var_name}' with value '{value}': {err}"
                raise err(msg=msg, var_name=var_name) from err



        # Save in cache
        cached = False
        if settings.cache:
            self._cache[var_name] = value
            cached = True
        _report["cached"] = cached

        # Return value
        if debug:
            return value, _report
        return value






    def _render_var_template1(self,
                        var_names=None,
                        settings=None,

                        
                        # Forwarded args
                        report=None,
                        seen=None, 
                        lvl=None, 
                        # debug=False, 
                        # cache=True, 
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
                    key, _seen=new_seen, _lvl=_lvl + 1, debug=debug,
                )
            except UndefinedVarError as err :
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

        return dict_vars, report


  


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
