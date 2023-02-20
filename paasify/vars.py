# -*- coding: utf-8 -*-
"Paasify Vars Libary"

# pylint: disable=logging-fstring-interpolation

import os
import logging
import graphlib


from pprint import pprint  # noqa: F401

import anyconfig

import paasify.errors as error
from paasify.common import StringTemplate, uniq
from paasify.framework import PaasifyObj

_log = logging.getLogger()


class Variable(PaasifyObj):
    "A simple variable with metadata"

    def __init__(self, parent=None, ident=None, payload=None):

        # Mandatory
        self.name = payload["name"]
        self.value = payload["value"]

        # Required
        self.index = payload["index"]
        self.file = payload["file"]
        self.scope = payload["scope"]
        self.parse_order = payload["parse_order"]

        # WIP
        self.source = payload.get("source")
        self.kind = payload.get("kind")
        self.owner = payload.get("owner")

        # Call parents
        self.ident = (
            f"{self.name}={self.value} ({self.index},{self.kind},{self.source})"
        )
        PaasifyObj.__init__(self, parent, ident)

    # def get_value(self):
    #    return {
    #            "name": None,
    #            }


class VarMgr(PaasifyObj):
    """
    This class manage a list of variables (PaasifyConfigVar), but it keep
    the adding order.

    Args:
        PaasifyObj (_type_): _description_

    Raises:
        error.ProjectInvalidConfig: _description_

    Returns:
        _type_: _description_
    """

    _vars = []

    def __init__(self, *arsg, **kwargs):

        self._vars = []
        super().__init__(*arsg, **kwargs)
        # self.set_logger("paasify.cli.vars")
        self.index = 0

        self.list_index = []
        self.list_parse_order = []

    def add_vars(self, payload, range_parse, **kwargs):
        "Add any kind of variables to the stack"

        # TODO: Sanity avoid duplicate piorities, should not be done this way, if still required
        prio = kwargs.get("parse_order")
        if prio:
            known_prios = uniq([var.parse_order for var in self._vars])
            if prio in known_prios:
                pprint([var for var in self._vars if var.parse_order == prio])
                assert False, f"Got duplicate priority: {prio}, found: {known_prios}"

        index = range_parse
        if isinstance(payload, dict):
            for name, var in payload.items():
                index += 1
                self.add_var(name, var, parse_order=index, **kwargs)

        elif isinstance(payload, list):
            for var in payload:
                index += 1
                self.add_var(var, parse_order=index, **kwargs)
        else:
            assert (
                False
            ), f"Object is not supported, expected dict or list, got: {payload}"

        return index

    def add_var(self, key, value=None, **kwargs):
        """Add a list/dict of vars into varmanager. You can override source/file/owner/kind.

        object can be: Variable (as key or value)
        object can be: key value
        """

        # Fetch object
        obj = None
        if isinstance(key, Variable):
            obj = key
        elif isinstance(value, Variable):
            obj = value

        # Assign overrides from parameters
        if obj:
            for name, val in kwargs.items():
                try:
                    getattr(obj, name)
                except AttributeError:
                    assert False, "BUG HERE !!!"
                setattr(obj, name, val)
        else:
            self.index += 1
            payload = dict(kwargs)
            payload.update(
                {
                    "name": key,
                    "value": value,
                    "index": self.index,
                }
            )
            obj = Variable(parent=self, ident="StackVar", payload=payload)

        # Sanity checks
        assert (
            obj.index not in self.list_index
        ), f"Duplicate index: {obj.index} for {obj}"
        assert (
            obj.parse_order not in self.list_parse_order
        ), f"Duplicate parse_order: {obj.parse_order} for {obj}"
        self.list_index.append(obj.index)
        self.list_parse_order.append(obj.parse_order)

        self._vars.append(obj)

    def add_vars_from_lookup(
        self, lookup, parse_order, fail_on_missing=False, **override
    ):
        """Process yml vars from a tag_list"""

        vars_cand = lookup.match(fail_on_missing=fail_on_missing)
        for cand in vars_cand:

            # Parse file
            cand_file = cand["match"]
            ac_parser = "yaml"
            if cand_file.endswith("json"):
                ac_parser = "json"
            elif cand_file.endswith("toml"):
                ac_parser = "toml"
            self.log.info(f"Process {ac_parser} var file: {cand_file}")
            conf = anyconfig.load(cand_file, ac_parser=ac_parser)
            assert isinstance(conf, dict)

            config = {
                "kind": cand["kind"] + f"_{ac_parser}",
                "source": "core",
                "file": cand_file,
                "owner": cand["owner"],
            }
            config.update(override)

            # Append to config
            parse_order = self.add_vars(conf, range_parse=parse_order, **config)
            # parse_order += 100

    # Vars selector
    # ===========================

    def select(self, func):
        "Allow to select vars on any attributes with a function"
        assert callable(func), f"Wrong argument type, expected a callable, got: {func}"
        result = [var for var in self._vars if func(var)]
        return result

    # Templating processors
    # ===========================

    # TODO: This should be a simple function, not a staticmethod
    @staticmethod
    def _render_env_sorter(var):
        "Helper function to sort vars per parse_order"
        return var.parse_order

    def render_env(
        self, parse=False, parse_vars=None, select=None, hint=None, skip_undefined=False
    ):
        """Return environment context, with eventually parsed variables"""

        # Prepare args
        parse_vars = parse_vars or {}
        selection = []
        if select:
            selection = list(self.select(select))
        else:
            selection = list(self._vars)

        # Prepare unparsed result
        out = {
            var.name: var.value
            for var in sorted(selection, key=self._render_env_sorter)
        }
        if not parse:
            self.log.debug(f"Fetch vars: {hint}")
            return out

        # Parse results
        parsing_env = dict(out)
        parsing_env.update(parse_vars)

        # Generate variables dependency tree
        deptree = {}
        for var in sorted(selection, key=self._render_env_sorter):
            deps = []
            tpl = self.get_value_templater(var.value)
            if tpl:
                deps = tpl.get_identifiers()
            if len(deps) > 0:

                # Missing vars checkup
                delkeys = []
                for dep in deps:
                    if dep == var.name:
                        delkeys.append(dep)
                    if dep not in parsing_env:
                        if skip_undefined:
                            continue
                        else:
                            msg = f"Variable '{dep}' is not defined in statement '{var.name}={var.value}' in {hint}"
                            raise error.UndeclaredVariable(msg) from KeyError

                # CLean uneeded keys
                for name in delkeys:
                    deps.remove(name)
                    self.log.trace(f"Delete recursive resolution for var: {name}")

                deptree[var.name] = deps

        # Generate var topological sorting
        self.log.debug(f"Parse {len(deptree)} var(s), {hint}")
        self.log.trace(f"Vars: {','.join(deptree.keys())}")
        if len(deptree) > 0:

            # Get var dependency parsing order
            ts = graphlib.TopologicalSorter(deptree)
            try:
                ret = tuple(ts.static_order())
            except graphlib.CycleError as err:
                msg2, var = err.args
                msg = f"Variable dependency cycle error for: {','.join(var)} ({msg2})"
                raise error.UndeclaredVariable(msg) from KeyError

            # Parse each vars
            dyn_vars = {}
            for var_name in ret:
                value = parsing_env[var_name]
                value = self.template_value(
                    value, parsing_env, hint=var_name, skip_undefined=skip_undefined
                )
                parsing_env[var_name] = value
                dyn_vars[var_name] = value
            out.update(dyn_vars)

        return out

    def resolve_dyn_vars(self, tpl, env, hint=None):
        "Resolver environment and secret vars"

        env = dict(env)
        var_list = tpl.get_identifiers()
        line = tpl.template

        for var in var_list:
            if var.startswith("_env_"):
                name = var[5:]
                value = os.environ.get(name)
                msg = f"Fetching environment value for: {hint}: {line} ({name}={value})"
                self.log.info(msg)
                env[var] = value
            elif var.startswith("_secret_"):
                msg = f"Support for secrets is not implemented yet: {hint}: {line}"
                self.log.warning(msg)
                env[var] = var
                # raise NotImplementedError(msg)

        return env

    def get_value_templater(self, value):
        """Return the stringTemplater for a given value"""

        if not isinstance(value, str):
            return None

        return StringTemplate(value)

    def template_value(self, value, env, hint=None, skip_undefined=False):
        "Render a string with template engine"

        tpl = self.get_value_templater(value)
        if not tpl:
            return value, "string_simple"

        # Resolve dynamic vars
        # env = self.resolve_dyn_vars(tpl, env, hint=hint)

        try:
            old_value = value
            value = tpl.substitute(**env)
            if old_value != value:
                self.log.trace(
                    f"Transformed template var {hint}: {old_value} => {value}"
                )

        except KeyError as err:
            if not skip_undefined:
                pprint(env)
                raise Exception("You found a bug!")
                msg = f"Variable {err} is not defined in variable '{hint}': '{value}'"
                raise error.UndeclaredVariable(msg) from KeyError

        except ValueError:
            self.log.debug(
                f"Could not parse variable: {hint}='{value}', forwarding to docker compose"
            )

        return value

    # Debug and troubleshoot
    # ===========================

    def dump(self, *args, **kwargs):
        """
        Dump and explain the current variable stack
        """
        super().dump(*args, **kwargs)
        print("  Vars:")
        print("  -----------------")
        filter_vars = kwargs.get("filter_vars")
        filter_vars = None if filter_vars is True else filter_vars
        self.explain()

    def explain(self, scope=None, as_string=False, filter_vars=None):
        """
        Explain the current variable stack
        """

        # header
        payload = {
            "name": "NAME",
            "value": "VALUE",
            "kind": "KIND",
            "source": "SOURCE",
            "file": "FILE",
            "scope": "SCOPE",
            "owner": "OWNER",
            "index": "INDEX",
            "parse_order": "PARSE_ORDER",
        }
        header = [Variable(payload=payload)]

        # Prepare args
        selection = []
        if scope:
            selection = list(self.select(scope))
        else:
            selection = list(self._vars)

        # Loop over all vars
        ellipsis = "..."
        max_ = 60
        result = []
        if not isinstance(filter_vars, list):
            filter_vars = None
        for var in header + sorted(selection, key=self._render_env_sorter):

            if filter_vars and var.name not in filter_vars:
                continue

            # TODO: There is a lib for that !
            ell = ellipsis if len(str(var.value)) > max_ else ""
            value = str(var.value)[: max_ - len(ell)] + ell
            while len(value) < max_:
                add = max_ - len(value)
                add = " " * add
                value += add

            # txt = f"{var.parse_order:<6}{var.name:40}: {value} {var.scope:20} {var.file}"
            # txt = f"{var.parse_order:<6}{var.name:30}: {value:52} {var.scope:20}{var.owner:20}{var.kind:20}"

            # What user want to see
            txt = f"{var.parse_order:<6}{var.name:30}: {value:52} {var.scope:20}  {var.file}"
            result.append(txt)

        result = "\n".join(result)
        if as_string:
            return result

        print(result)
