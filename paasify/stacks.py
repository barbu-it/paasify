# -*- coding: utf-8 -*-
"""
Paasify Stack management

This library provides two classes:

* StackManager: Manage a list of stacks
* Stack: A stack instance
"""

# pylint: disable=logging-fstring-interpolation


import os

import re
from pprint import pprint, pformat  # noqa: F401
from functools import wraps

import anyconfig


from cafram.nodes import NodeList, NodeMap
from cafram.utils import (
    to_domain,
    to_yaml,
    first,
    write_file,
    to_json,
)

import paasify.errors as error
from paasify.common import uniq
from paasify.vars import VarMgr
from paasify.framework import (
    PaasifyObj,
    PaasifyConfigVars,
    FileLookup,
    FileReference,
)
from paasify.stack_components import (
    StackTagMgr,
    StackApp,
    StackAssembler,
    StackDumper,
)


# Try to load json schema if present
ENABLE_JSON_SCHEMA = False
try:
    from json_schema_for_humans.generate import generate_from_filename
    from json_schema_for_humans.generation_configuration import GenerationConfiguration

    ENABLE_JSON_SCHEMA = True
except ImportError:
    ENABLE_JSON_SCHEMA = False


class Stack(NodeMap, PaasifyObj):
    "Paasify Stack Instance"

    conf_default = {
        "dir": None,
        "name": None,
        "app": None,
        "tags": [],
        "tags_suffix": [],
        "tags_prefix": [],
        "vars": [],
    }

    conf_children = [
        {
            "key": "app",
            "cls": StackApp,
            "action": "unset",
            "hook": "node_hook_app_load",
        },
        {
            "key": "vars",
            "cls": PaasifyConfigVars,
        },
    ]

    conf_schema = {
        # TODO: Bug: We want a way in stacks to have random/useless values, because
        # while doing trial/errors, the parser becomes annoying. Ie, if extra key
        # starts with a `_`, then simply skip the parser error. This could be a switch
        # like `--develop`
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Paasify Stack configuration",
        "default": conf_default,
        "oneOf": [
            {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {
                        "type": "string",
                        "minLength": 2,
                        "title": "Name of the stack",
                        "description": "This is a stack ident, it should not be changed. If not set, it comes from the app name, and from the dir if no apps. Should not contains any special char, except - (or _). This is used to name the app (docker, dns, etc ...)",
                    },
                    "dir": {
                        "type": "string",
                        "title": "Directory where live the stack",
                        "description": "Directory where the docker-compose.run.yml file is generated. Can be used to move stack directories (cold move). Default comes from the name.",
                        "default": "$name",
                    },
                    "app": {
                        "type": "string",
                        "title": "Application call",
                        "description": "Shortcut to use an application without modifying it's default parameters. First optional part is module collection, and after the ':', it's the name/path to the aplication inside the module",
                    },
                    "tags": StackTagMgr.conf_schema,
                    "tags_prefix": StackTagMgr.conf_schema,
                    "tags_suffix": StackTagMgr.conf_schema,
                    "vars": PaasifyConfigVars.conf_schema,
                },
            },
            {
                "type": "string",
                "title": "Direct application call",
                "description": "Shortcut to use an application without modifying it's default parameters. First optional part is module collection, and after the ':', it's the name/path to the aplication inside the module",
                "pattern": "^([^:]+:)?(.*)$",
            },
        ],
    }

    # Children objects
    tag_manager = None
    engine = None
    prj = None

    # Stack vars
    stack_dir = None
    stack_name = None
    prj_dir = None
    prj_ns = None

    # Vars scopes
    var_scopes = {
        "global": ["default_conf", "extra_vars_yaml", "global_conf"],
        "stack": [
            "default_conf",
            "app_yaml",
            "stack_yaml",
            "extra_vars_yaml",
            "global_conf",
            "tag_def",
            "tag_dyn",
            "stack_conf",
        ],
    }

    # CaFram functions
    # ---------------------

    def node_hook_init(self):
        "Create instance attributes"

        self._cache = {}

        # Internal attributes
        self.prj = self.get_parent().get_parent()
        self.runtime = self.prj.runtime
        assert (
            self.prj.__class__.__name__ == "PaasifyProject"
        ), f"Expected PaasifyProject, got: {self.prj}"

    def node_hook_transform(self, payload):

        if isinstance(payload, str):
            key = "app" if ":" in payload else "name"
            payload = {
                key: payload,
            }

        assert isinstance(payload, dict)
        return payload

    def node_hook_app_load(self):
        "Modify stack depending app"

        # Assert name,dir,app
        stack_name = self.name
        stack_dir = self.dir
        stack_app = self.app

        # Check name first
        if not stack_name:

            # Fetch from app
            if stack_app:
                stack_name = stack_app.app_name

            # Fetch from dir
            elif stack_dir:
                # stack_name = os.path.split(stack_dir)[-1]
                stack_name = "_".join(stack_dir.split(os.path.sep))

            if not stack_name:
                assert False, f"Missing name, or app or path for stack: {self}"

        if not stack_dir:
            stack_dir = stack_name

        if "/" in stack_name:
            # TODO: Workaround, this should be handled before ...
            stack_name = stack_name.replace("/", "-")

        # Register required vars
        self.stack_name = stack_name
        self.stack_dir = stack_dir
        self.prj_ns = self.prj.config.namespace or self.prj.runtime.namespace
        self.prj_path = self.prj.runtime.root_path
        self.stack_path = os.path.join(self.prj.runtime.root_path, stack_dir)
        self.stack_dump_path = os.path.join(
            self.runtime.project_private_dir, "dumps", stack_dir
        )
        self.ident = self.stack_name
        self.stack_path_abs = os.path.abspath(self.stack_path)

        # Check
        assert self.stack_name, f"Bug here, should not be empty, got: {self.stack_name}"
        assert re.search("^[a-zA-Z0-9_].*$", self.stack_name), f"Got: {self.stack_name}"
        assert re.search("^[a-zA-Z0-9_/].*$", self.stack_dir), f"Got: {self.stack_dir}"

    def node_hook_final(self):
        "Enable CLI debugging"

        # Create engine instance
        payload = {
            "stack_name": f"{self.prj_ns}_{self.stack_name}",
            "stack_path": self.stack_path,
            # os.path.join(self.stack_dir, "docker-compose.run.yml"),
            "docker_file": "docker-compose.run.yml",
        }
        self.engine = self.prj.engine_cls(parent=self, payload=payload)

        # Prepare stack lists
        tag_config = {
            "raw": self.tags or self.prj.config.tags,
            "tag_prefix": ["_paasify"]
            + (self.tags_prefix or self.prj.config.tags_prefix),
            "tag_suffix": self.tags_suffix or self.prj.config.tags_suffix,
        }

        # Start managers
        self.tag_manager = StackTagMgr(
            parent=self, ident=self.stack_name, payload=tag_config
        )
        self.var_manager = None

        self.log.info(f"Stack config: {self.stack_name} in {self.stack_path}")

        # Set sh default args
        self.default_sh_args = {"_fg": True}
        if self.prj.runtime.no_tty:
            self.default_sh_args = {"_in": False}

    # Local functions
    # ---------------------

    def docker_candidates(self) -> list:
        """Return all docker-files candidates: local, app and tags

        Search docker-compose files in the following dirs:

          * Main docker-compose:
            * <local>/docker-compose.y?ml
            * <app>/docker-compose.y?ml
          * Additional docker-composes:
            * <local>/docker-compose.<tag>.y?ml
            * <app>/docker-compose.<tag>.y?ml

        Return the list of candidates for the stack
        """

        # 0. Check cache
        _key_cache = "docker_candidates"
        results = self._cache.get(_key_cache)
        if results:
            return results

        # 1. Init
        app = self.app or None
        pattern = ["docker-compose.yml", "docker-compose.yaml"]

        # 2. Lookup stack docker-compose files
        lookup_app = FileLookup()
        lookup_app.append(self.stack_path, pattern)

        # 3. Lookup app docker-compose files
        if app:
            app_path = app.get_app_path()
            lookup_app.append(app_path, pattern)

        # 4. Assemble results
        matches = lookup_app.match()
        results = [match["match"] for match in matches]

        # 5. Sanity check
        for file in results:
            assert isinstance(file, str), f"Got: {file}"

        # 6. Filter result
        if len(results) < 1:
            paths = [look["path"] for look in lookup_app.get_lookups()]
            paths = ", ".join(paths)
            msg = f"Can't find 'docker-compose.yml' for stack '{self._node_conf_raw}' in: {paths}"
            raise error.StackMissingDockerComposeFile(msg)

        # TODO: Test ideas: test if local_cand and app_cand are properly setup depending the pattern

        # Set in cache and return value
        self._cache[_key_cache] = results
        return results

    def get_tag_plan(self) -> list:
        """
        Resolve all files associated to tags

        Return the list of tags with files
        """

        # 0. Init
        # Objects:
        app = self.app or None
        # Vars:
        stack_dir = self.stack_path
        project_jsonnet_dir = self.prj.runtime.project_jsonnet_dir
        docker_candidates = self.docker_candidates()

        # 1. Generate default tag (docker compose files only)
        tag_base = {
            "tag": None,
            "jsonnet_file": None,
            "docker_file": first(docker_candidates),
        }

        # 2. Forward to StackTagManager: Generate directory lookup for tags

        # Get jsonnet search paths
        dirs_docker = [stack_dir]
        if app:
            src = app.get_app_path()
            assert src
            dirs_docker.append(src)
        dirs_jsonnet = [
            self.prj.runtime.paasify_plugins_dir,
            stack_dir,
            project_jsonnet_dir,
        ]
        for src in self.prj.sources.get_all():
            dirs_jsonnet.append(os.path.join(src.path, ".paasify", "plugins"))

        # Build tag list
        tags = self.tag_manager.get_children()

        tag_list = []
        for tag in tags:

            # Docker lookup
            pattern = [
                f"docker-compose.{tag.name}.yml",
                f"docker-compose.{tag.name}.yaml",
            ]
            lookup = FileLookup()
            for dir_ in dirs_docker:
                lookup.append(dir_, pattern)
            docker_cand = lookup.match()

            docker_file = None
            if len(docker_cand) > 0:
                docker_file = first(docker_cand)["match"]

            # Jsonnet lookup
            pattern = [f"{tag.name}.jsonnet"]
            lookup = FileLookup()
            jsonnet_file = None
            for dir_ in dirs_jsonnet:
                lookup.append(dir_, pattern)
                jsonnet_cand = lookup.match()
                if len(jsonnet_cand) > 0:
                    jsonnet_file = first(jsonnet_cand)["match"]

            ret = {
                "tag": tag,
                "jsonnet_file": jsonnet_file,
                "docker_file": docker_file,
            }
            tag_list.append(ret)

            # Report error to user on missing tags
            if not docker_file and not jsonnet_file:
                msg = f"Can't find '{tag.name}' for '{self.stack_name}' stack"
                raise error.MissingTag(msg)

        # 3. Return result list
        results = []
        results.append(tag_base)
        results.extend(tag_list)
        return results, dirs_jsonnet

    def _gen_conveniant_vars(self, docker_file, tag_names=None) -> dict:
        "Generate default core variables"

        # Extract stack config
        tag_names = tag_names or []
        dfile = anyconfig.load(docker_file, ac_ordered=True, ac_parser="yaml")
        default_service = first(dfile.get("services", ["default"]))
        default_network = first(dfile.get("networks", ["default"]))

        assert isinstance(self.prj_ns, str)
        assert isinstance(self.prj_path, str)
        assert isinstance(self.stack_name, str)
        assert isinstance(self.prj_path, str)
        assert isinstance(self.prj_path, str)
        assert self.stack_path_abs.startswith("/")

        # Build default (only primitives)
        result = {
            "paasify_sep": "-",
            "paasify_sep_dir": os.sep,
            # See: https://www.docker.com/blog/announcing-compose-v2-general-availability/
            "paasify_sep_net": "_",
            "_prj_path": self.prj_path,
            "_prj_namespace": self.prj_ns,  # deprecated because too long !
            "_prj_ns": self.prj_ns,
            "_prj_domain": to_domain(self.prj_ns),
            "_prj_stack_path": self.stack_path,
            # Colon is used here for easier to parsing for later ...
            "_prj_stack_tags": f":{':'.join(tag_names)}:",
            "_stack_name": self.stack_name,
            "_stack_path_abs": self.stack_path_abs,
            "_stack_network": default_network,
            "_stack_service": default_service,
            # To report below as well
            "_stack_app_name": None,
            "_stack_app_dir": None,
            "_stack_app_path": None,
            "_stack_collection_app_path": None,
        }

        app = self.app
        if app:
            extra = {
                "_stack_app_name": os.path.basename(app.app_name),
                "_stack_app_dir": app.app_name,
                "_stack_app_path": app.get_app_path(),
                # TODO: Broken ... use app.src instead ?
                # "_stack_collection_app_path": self.app.collection_dir,
            }
            result.update(extra)
        return result

    @property
    def docker_vars_lookup(self) -> list:
        "Return the lookup configuration for vars.yml location"

        # Lookup config
        fl_stack = {
            "path": self.stack_path,
            "pattern": ["vars.yml", "vars.yaml"],
            "kind": "stack",
            "owner": "user",
        }
        lookup = FileLookup()
        lookup.append(**fl_stack)

        if self.app:
            app_dir = self.app.get_app_path()
            assert app_dir, "Missing app name!"
            fl_app = {
                "path": app_dir,
                "pattern": ["vars.yml", "vars.yaml"],
                "kind": "app",
                "owner": "app",
            }
            lookup.insert(**fl_app)

        return lookup

    @property
    def extra_vars_lookups(self) -> list:
        "Return the lookup configuration for extra_vars location"

        prj_config = self.get_parents()[-2].config
        runtime = self.prj.runtime

        extra_vars = prj_config.extra_vars.get_value()
        extra_vars = extra_vars if isinstance(extra_vars, list) else [extra_vars]

        extra_vars_lookups = FileLookup()
        for ref in extra_vars:
            ref = FileReference(ref, root=runtime.root_path)
            dir_, file_ = os.path.split(ref.path())
            xtra = {
                "kind": "extra_vars",
                "owner": "user",
            }
            extra_vars_lookups.append(dir_, [file_], **xtra)
        return extra_vars_lookups

    def render_vars(
        self,
        hint=None,
        parse=True,
        skip_undefined=False,
        scope=None,
        parse_vars=None,
        varmgr=None,
    ):
        "Return parsed vars for a given scope"

        assert hint, f"Missing valid hint for render_vars call for {self} ..."

        # Detect selector
        parse_vars = parse_vars or {}
        func = None
        scopes = None
        varmgr = varmgr or self.var_manager
        assert varmgr, "Var manager is not initialized or provided !"
        if isinstance(scope, str):
            scopes = scope.split(",")
        elif isinstance(scope, list):
            scopes = scope

        # Attribute function
        def _func(var):
            return var.scope in scopes

        func = _func if scopes else scope

        # Parse the result
        msg = f"Environment rendering asked for scope: parse={parse}, hint={hint}"
        self.log.trace(msg)
        result = varmgr.render_env(
            parse=parse,
            parse_vars=parse_vars,
            skip_undefined=skip_undefined,
            select=func,
            hint=hint,
        )
        return result

    def get_stack_vars(self, sta, all_tags, jsonnet_lookup_dirs, extra_user_vars=None):

        # 0. Get ojects we need to query
        varmgr = VarMgr(parent=self, ident=f"{self.stack_name}")

        globvars = self.prj.config.vars
        localvars = self.vars
        extra_user_vars = extra_user_vars or {}

        # 1. Generate data structures
        docker_file = all_tags[0]["docker_file"]
        tag_names = uniq([tag["tag"].name for tag in all_tags if tag["tag"]])

        vars_default = self._gen_conveniant_vars(
            docker_file=docker_file, tag_names=tag_names
        )
        stack_name = vars_default["_stack_name"]

        vars_global = {var.name: var.value for var in globvars.get_vars_list()}
        vars_user = {var.name: var.value for var in localvars.get_vars_list()}

        # 2. Create a varmgr VarMgr and inject configs

        # Order matters here:
        #   - Add core vars, the one starting with _
        #   - Add extra_vars, from external files
        #   - Add vars from app/vars.yml, then stack/vars.yml
        #   - Add global conf vars from paasify.yml
        #   - Add stack conf vars from paasify.yml
        varmgr.add_vars(
            vars_default,
            scope="global",
            kind="default_conf",
            source="core",
            file="paasify.py",
            owner="paasify",
            parse_order=1000,
        )
        varmgr.add_vars_from_lookup(
            self.extra_vars_lookups, 4000, fail_on_missing=True, scope="global"
        )
        varmgr.add_vars_from_lookup(self.docker_vars_lookup, 5000, scope="stack")
        varmgr.add_vars(
            vars_global,
            scope="global",
            kind="global_conf",
            source="core",
            file="paasify.yml:config.vars",
            owner="user",
            parse_order=7000,
        )
        varmgr.add_vars(
            vars_user,
            scope="stack",
            kind="stack_conf",
            source="core",
            file=f"paasify.yml:stacks[{stack_name}]vars",
            owner="user",
            parse_order=8000,
        )

        # 4. Add config for tags as well
        cand_index = -2  # TODO: we sould remove -2 if app or -1 if not
        tag_instances = []
        prio_index = 0
        for cand in all_tags:
            cand_index += 1
            prio_index += 1

            # Fetch the tag
            # --------------------
            tag = cand.get("tag")
            if not tag:
                continue
            tag_vars = tag.vars or {}
            tag_name = tag.name

            jsonnet_file = cand.get("jsonnet_file")
            if not jsonnet_file:
                # Throw a user warning about wrong config
                if len(tag_vars) > 0:
                    msg = f"Tag vars are only supported for jsonnet tags: {tag_name}: {tag_vars}"
                    self.log.warning(msg)
                continue

            # Prepare loop metadata
            # --------------------
            tag_index = 0
            tag_inst = f"{tag_name}{tag_index}"
            while tag_inst in tag_instances:
                tag_index += 1
                tag_inst = f"{tag_name}{tag_index}"
            tag_instances.append(tag_inst)

            # Assemble context and conf
            # --------------------
            loop_vars = {}
            loop_vars.update(tag_vars)

            varmgr.add_vars(
                loop_vars,
                # scope="tag",
                scope=f"tag_{tag_inst}",
                kind="tag_conf",
                source=tag_inst,
                file=f"paasify.yml:stacks[{stack_name}]tags[{tag_inst}]",
                owner="user",
                parse_order=9000 + prio_index,
            )

            # 3.2 Execute jsonnet plugin var calls
            # --------------------
            if tag_index > 0:
                # We only process ONE time the filter of each kind
                continue

            ctx = self.render_vars(
                scope="global,stack",
                parse=False,
                hint=f"jsonnet scoped vars: {tag_name}",
                varmgr=varmgr,
            )

            tmp2 = sta.process_jsonnet_exec(
                jsonnet_file,
                "plugin_vars",
                {"args": ctx},
                import_dirs=jsonnet_lookup_dirs,
            )
            try:
                var_def = tmp2["def"]
                var_dyn = tmp2["dyn"]
            except KeyError as err:
                self.log.error(
                    f"Could not execute plugin '{jsonnet_file}', please check the plugin is working as expected, especially ensure variable 'metadata.ident' is correctly set to the plugin name"
                )
                self.log.debug(f"Plugin returned: {tmp2}")
                raise error.JsonnetBuildFailed(err)

            varmgr.add_vars(
                var_def,
                scope="stack",
                owner=tag_name,
                kind="tag_def",
                source=tag_name,
                file=jsonnet_file,
                parse_order=2000 + prio_index,
            )
            varmgr.add_vars(
                var_dyn,
                scope="stack",
                owner=tag_name,
                kind="tag_dyn",
                source=tag_name,
                file=jsonnet_file,
                parse_order=3000 + prio_index,
            )

        return varmgr

    def log_extra_payloads(self, payload, msg):
        "Dump to log large chunks of data"

        if not self.dump_data_log:
            return

        self.log.trace("= {msg}")
        self.log.trace("=" * 60)
        self.log.trace("{pformat(payload)}")
        self.log.trace("=" * 60)

    def dump_diff_stage1(self, dumper, varmgr, glob_vars, stack_vars, all_tags):
        "Report build diff stage1"

        txt = []
        txt.append("==== Global Scope: Vars")
        txt.append(
            varmgr.explain(scope=lambda var: var.scope in ["global"], as_string=True)
        )
        txt.append("\n==== Global Scope: Parsed")
        txt.append(to_yaml(glob_vars))
        txt = "\n".join(txt)
        dumper.dump("0-glob-env.txt", txt)

        txt = []
        txt.append("==== Stack Scope: Tags")
        txt.append(pformat(all_tags))
        txt.append("\n==== Stack Scope: Vars")
        txt.append(
            varmgr.explain(
                scope=lambda var: var.scope in ["global", "stack"], as_string=True
            )
        )
        txt.append("\n==== Stack Scope: Parsed")
        txt.append(to_yaml(stack_vars))
        txt = "\n".join(txt)
        dumper.dump("0-stack-env.txt", txt)

    def dump_diff_stage2(
        self, dumper, varmgr, loop_vars, scope_filter, tag_inst, cand_index
    ):
        "Report build diff stage2"
        txt = []
        txt.append("==== Jsonnet Scope: Explain")
        txt.append(varmgr.explain(scope=scope_filter, as_string=True))
        txt.append("\n==== Jsonnet Scope: Vars")
        txt.append(to_yaml(loop_vars))
        txt = "\n".join(txt)

        dumper.dump(f"2-{cand_index:02d}-{tag_inst}-env.txt", txt)

    def assemble(self, vars_only=False, dump_payloads=False, explain=False):
        """Generate docker-compose.run.yml and parse it with jsonnet

        vars_only: If False, do nothing, if True or non empty list, just dump the variables
        explain: Show the explainer and/or build diff

        """

        # 1. Prepare assemble context
        # -------------------
        sta = StackAssembler(parent=self, ident=f"{self.stack_name}")
        all_tags, jsonnet_lookup_dirs = self.get_tag_plan()
        self.var_manager = self.get_stack_vars(sta, all_tags, jsonnet_lookup_dirs)

        # 2. Prepare debugging tools
        # -------------------
        dump_payload_log = self.runtime.dump_payload_log
        self.dump_data_log = dump_payloads
        if explain and not vars_only:
            dumper = StackDumper(self.stack_dump_path, enabled=True)

        # 3. Prepare scopes
        # -------------------
        glob_vars = self.render_vars(scope="global", hint="global scoped variables")
        stack_vars = self.render_vars(
            scope="global,stack",
            parse=True,
            parse_vars=glob_vars,
            hint="stack scoped variables",
        )

        # 4. Intermediate debugging tools
        # -------------------
        self.log_extra_payloads(stack_vars, "Dump of docker environment vars")

        if explain and not vars_only:
            self.dump_diff_stage1(
                dumper, self.var_manager, glob_vars, stack_vars, all_tags
            )

        if vars_only:
            if explain:
                self.var_manager.explain(filter_vars=vars_only)

            out = dict(stack_vars)
            if isinstance(vars_only, list):
                out = {key: stack_vars.get(key) for key in vars_only}
            return out

        # 2. Build docker-compose
        # -------------------
        docker_run_payload = sta.assemble_docker_compose(
            all_tags,
            self.engine,
            env=stack_vars,
            dump_payload_log=dump_payload_log,
        )

        if explain:
            dumper.dump("1-docker-compose.yml", docker_run_payload, fmt="yaml")

        # 3. Assemble jsonnet tags
        # -------------------
        cand_index = (
            -2
        )  # We start at minus 2 here, because there is the 2 firsts tags are hidden
        tag_instances = []
        tag_names = []

        # Loop over each tags
        for cand in all_tags:
            cand_index += 1

            # 3.0 Init loop
            # --------------------

            # Check tag infos
            tag = cand.get("tag")
            tag_name = tag.name if tag else "_paasify"

            # Check conditions
            jsonnet_file = cand.get("jsonnet_file")
            if not jsonnet_file:
                continue

            # 3.1 Reload var context if overriden
            # --------------------
            tag_index = 0
            tag_inst = f"{tag_name}{tag_index}"
            while tag_inst in tag_instances:
                tag_index += 1
                tag_inst = f"{tag_name}{tag_index}"
            tag_instances.append(tag_inst)
            if tag_name not in tag_names:
                tag_names.append(tag_name)

            tag_suffix = f"{tag_index}" if tag_index != 0 else ""
            self.log.info(f"Apply jsonnet tag '{tag_inst}': {jsonnet_file}")

            # 3.2 Generate loop vars
            # --------------------
            scope = f"global,stack,tag_{tag_inst}"

            def scope_filter(var):
                # pylint: disable=cell-var-from-loop
                return var.scope in scope.split(",") and var.owner != tag_name

            loop_vars = self.render_vars(
                scope=scope_filter,
                parse=True,
                parse_vars=stack_vars,
                hint=f"jsonnet transform vars: {tag_inst}",
            )

            loop_vars.update(
                {
                    "tag_cand": cand_index,
                    "tag_index": tag_index,
                    "tag_instance": tag_inst,
                    "tag_suffix": tag_suffix,
                }
            )

            # Logging
            self.log_extra_payloads(
                loop_vars, f"Dump of vars before '{tag_inst}' jsonnet execution"
            )
            if explain:
                self.dump_diff_stage2(
                    dumper,
                    self.var_manager,
                    loop_vars,
                    scope_filter,
                    tag_inst,
                    cand_index,
                )

            # 3.3 Prepare jsonnet call
            # --------------------
            params = {
                "args": loop_vars,
                "docker_data": docker_run_payload,
            }
            docker_run_payload = sta.process_jsonnet_exec(
                jsonnet_file,
                "docker_transform",
                params,
                import_dirs=jsonnet_lookup_dirs,
            )
            if explain:
                dumper.dump(
                    f"2-{cand_index:02d}-{tag_inst}-out.yml",
                    docker_run_payload,
                    fmt="yml",
                )

        # 4. Write output file
        # -------------------

        if explain:
            dumper.dump("3-docker.yml", docker_run_payload, fmt="yml")

        # Prepare docker-file output directory
        if not os.path.isdir(self.stack_path):
            self.log.info(f"Create missing directory: {self.stack_path}")
            os.makedirs(self.stack_path)

        # Save the final docker-compose.run.yml file
        outfile = os.path.join(self.stack_path, "docker-compose.run.yml")
        self.log.info(f"Writing docker-compose file: {outfile}")
        output = to_yaml(docker_run_payload)
        write_file(outfile, output)

        if explain:
            dumper.show_diff()

        # 5. Prepare environment
        # -------------------
        # This is a first a basic implementation of apps volumes with permissions
        # TOFIX: Permission change will apply the same permissions on all volumes in a blind way
        # Ie: Permission for mysql containers is not the same as the app itself.
        volumes = docker_run_payload.get("volumes", {})
        uid = int(stack_vars.get("app_puid", "-1"))
        gid = int(stack_vars.get("app_pgid", "-1"))
        for vol_name, vol_def in volumes.items():
            driver = vol_def.get("driver")
            driver_opts = vol_def.get("driver_opts")
            if driver == "local" and driver_opts:
                device = driver_opts.get("device")
                if device and not os.path.exists(device):
                    self.log.info(
                        f"Create volume directory '{vol_name}' with owner '{uid}:{gid}': {device}"
                    )
                    os.makedirs(device)
                    os.chown(device, uid, gid)

    def explain_tags(self):
        "Explain hos tags are processed on stack"

        print(f"  Scanning stack plugins: {self.ident}")
        matches, jsonnet_lookup_dirs = self.get_tag_plan()

        # 0. Internal functions
        def list_items(items):
            "List items"
            _first = "*"
            # list_items(items)
            for cand in items:
                print(f"          {_first} {cand}")
                _first = "-"

        def list_jsonnet_files(items):
            "List jsonnet files"
            for match in items:

                tag = match.get("tag")
                if tag:
                    cand = match.get("jsonnet_file")
                    if cand:
                        print(f"        - {tag.name}")

        # 1. Show all match combinations
        for match in matches:

            tag = match.get("tag")

            if not tag:
                print("    Default config:")
                list_items(self.docker_candidates())
                print("    Tag config:")
                continue

            print(f"      tag: {tag.name}")

            if tag.docker_candidates:
                print("        Docker tags:")
                list_items(tag.docker_candidates)

            if tag.jsonnet_candidates:
                print("        Jsonnet tags:")
                list_items(tag.jsonnet_candidates)

        # 2. Show actual loading
        print("\n    Tag Loading Order:")

        # 2.1 Var loading
        print("      Loading vars:")
        list_jsonnet_files(matches)

        # 2.2 Tag loading
        print("      Loading Tags:")
        for match in matches:

            tag = match.get("tag")

            if not tag:
                cand = match.get("docker_file")
                print(f"        * base: {cand}")
                continue

            cand = match.get("docker_file")
            if cand:
                print(f"        - {tag.name}")

        # 2.3 Jsonnet loading
        print("      Loading jsonnet:")
        list_jsonnet_files(matches)

    def gen_doc(self, output_dir=None):
        "Generate documentation"

        matches, jsonnet_lookup_dirs = self.get_tag_plan()

        # 3. Show jsonschema
        print("\n    Plugins jsonschema:")
        for match in matches:

            tag = match.get("tag")
            if not tag:
                continue

            file = match.get("jsonnet_file")
            if not file:
                continue

            # Create output dir
            dest_dir = os.path.join(output_dir, tag.name)
            if not os.path.isdir(dest_dir):
                os.makedirs(dest_dir)

            print(f"        # {tag.name}: {file}")
            out = self.process_jsonnet(file, "metadata", None)
            tag_meta = out["metadata"]
            tag_schema = tag_meta.get("jsonschema")
            # pprint (tag_meta)
            if "jsonschema" in tag_meta:
                del tag_meta["jsonschema"]

            dest_schema = os.path.join(dest_dir, "jsonschema")
            if tag_schema:
                print(f"Generated jsonschema files in: {dest_schema}.[json|yml]")
                write_file(dest_schema + ".json", to_json(tag_schema))
                write_file(dest_schema + ".yml", to_yaml(tag_schema))

            # Create HTML documentation
            if ENABLE_JSON_SCHEMA:

                fname = "web.html"
                dest_html = os.path.join(dest_dir, fname)
                print(f"Generated HTML doc in: {dest_html}")
                config = GenerationConfiguration(
                    copy_css=True,
                    description_is_markdown=True,
                    examples_as_yaml=True,
                    footer_show_time=False,
                    expand_buttons=True,
                    show_breadcrumbs=False,
                )
                generate_from_filename(dest_schema + ".json", dest_html, config=config)

                # /schema_doc/paasify_yml_schema.html
                # /plugin_api_doc/{tag.name}/web.html
                markdown_doc = f"""
# {tag.name}

Documentationfor tag: `{tag.name}`

## Informations

``` yaml
{to_yaml(tag_meta)}
```

## Tag documentation

<iframe scrolling="yes" src="/plugins_apidoc/{tag.name}/{fname}" style="width: 100vw; height: 70vh; overflow: auto; border: 0px;">
</iframe>


                """
                dest_md = os.path.join(dest_dir, "markdown.md")
                write_file(dest_md, markdown_doc)
                print(f"Generated Markdown doc in: {dest_md}")


def stack_target(fn):
    "Decorator to magically find the correct stack to apply"

    @wraps(fn)
    def wrapper(self, *args, stacks=None, stack_names=None, **kwargs):
        "Decorator to magically find the correct stack to apply"

        # Inteligently guess wich stack to use
        if not stacks:
            stacks = []

            if isinstance(stack_names, str):
                stack_names = [name.strip("/") for name in stack_names.split(",")]

            sub_dir = self.get_parent().runtime.sub_dir
            if not stack_names:

                if sub_dir:

                    # Use current dir stacks if in subdir
                    stack_path = sub_dir.split(os.path.sep)[0]
                    stacks = [
                        stack
                        for stack in self.get_children()
                        if stack_path == stack.stack_dir
                    ]
                    if stacks:
                        self.log.debug(
                            f"Use stack {stack_path} from current working directory"
                        )

                else:
                    # Use all stacks is set to None
                    self.log.debug("Use all stacks")
                    stacks = self.get_children()

            else:
                # Loop over specified list of tasks
                assert isinstance(stack_names, list), f"Got: {stack_names}"
                stack_names = [name for name in stack_names if name]
                stacks = [
                    stack
                    for stack in self.get_children()
                    if stack.stack_name in stack_names
                    or stack.stack_path in stack_names
                ]
                self.log.debug(
                    f"Requested stacks: {stack_names}, matched stacks: {stacks}"
                )

                # Assert all stacks has been addressed
                if len(stack_names) != len(stacks):
                    missing_stacks = list(stack_names)
                    for stack in stacks:
                        missing_stacks.remove(stack.stack_name)
                    raise error.StackNotFound(
                        f"This stack is not defined in config: {','.join(missing_stacks)}"
                    )

        # Clean decorator argument
        if "stacks_names" in kwargs:
            del kwargs["stacks_names"]

        # Last sanity tests
        if len(self.get_children()) < 1:
            raise error.StackNotFound(
                "There are no stacks configured yet for this project, please edit your paasify.yml config"
            )
        if len(stacks) < 1:
            raise error.StackNotFound(
                f"This stack is not defined in config: {stack_names}"
            )
        assert isinstance(stacks, list), f"Got: {stacks}"

        # Last user report
        stacks_names = ",".join([stack.stack_name for stack in stacks])
        self.log.info(f"Running command '{fn.__name__}' on stacks: {stacks_names}")
        return fn(self, *args, stacks=stacks, **kwargs)

    return wrapper


class StackManager(NodeList, PaasifyObj):
    "Manage a list of stacks"

    conf_schema = {
        # "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Paasify Stack configuration",
        "description": "Stacks are defined in a list of objects",
        "type": "array",
        "default": [],
        "items": Stack.conf_schema,
    }

    conf_children = Stack
    ident = "main"

    def node_hook_final(self):
        "Enable CLI logging and validate config"

        # Safety checks
        dup_names = []
        dup_dirs = []
        curr_index = -1
        for stack in self.get_children():
            curr_index += 1
            stack_name = stack.stack_name

            # Check for duplicates names
            if stack_name in dup_names:
                index = dup_names.index(stack_name)
                raise error.ProjectInvalidConfig(
                    f"Cannot have duplicate stack names, stacks {index} and {curr_index} share the same name: '{stack_name}'"
                )
            dup_names.append(stack_name)

            # Check for duplicates dirs
            stack_dir = stack.stack_dir
            if stack_dir in dup_dirs:
                index = dup_dirs.index(stack_dir)
                raise error.ProjectInvalidConfig(
                    f"Cannot have duplicate stack dir, stacks {index} and {curr_index} share the same dir: '{stack_dir}'"
                )
            dup_dirs.append(stack_dir)

        # Notice user because this is weird
        children = self.get_children()
        if not children:
            self.log.warning("No stacks found for this project!")

    # Stack management API
    # ======================

    def list_stacks(self):
        "Get stacks children (deprecated)"
        return self.get_children()

    def get_stacks_attr_ident(self):
        "List stack per idents"
        return [x.ident for x in self.get_children()]

    def get_stacks_attr(self, attr="ident"):
        "List stacks by attribute"
        return [getattr(x, attr) for x in self.get_children()]

    def get_stacks_obj(self, attr=None, values=None):
        """
        Get stack instance matching in values

        If attr or value is None, return all instances
        Values must be an array of valid vallues.
        """

        sub_dir = self._node_parent.runtime.sub_dir
        if values is None and sub_dir:
            # attr = path
            values = sub_dir.split(os.path.sep)[0]
            print(f"Automatch subdir: {values}")

        if isinstance(attr, str) and values is not None:
            if not isinstance(values, list):
                values = [values]
            result = [
                stack for stack in self.get_children() if getattr(stack, attr) in values
            ]
            return result

        return self.get_children()

    # Command Base API
    # ======================

    @stack_target
    def cmd_stack_assemble(self, stacks=None, vars_only=False, explain=False):
        "Assemble a stack"

        self.log.info("Asemble stacks:")
        for stack in stacks:
            self.log.notice(f"Assemble stack: {stack.stack_name}")
            stack.assemble(vars_only=vars_only, explain=explain)

    @stack_target
    def cmd_stack_up(self, stacks=None):
        "Start a stack"

        self.log.info("Start stacks:")
        for stack in stacks:
            self.log.notice(f"  Start stack: {stack.stack_name}")
            stack.engine.up(**stack.default_sh_args)

    @stack_target
    def cmd_stack_down(self, stacks=None, ignore_errors=False):
        "Stop a stack"

        stacks = list(stacks)
        stacks.reverse()
        self.log.info("Stop stacks:")
        for stack in stacks:
            self.log.notice(f"  Stop stack: {stack.stack_name}")
            try:
                stack.engine.down(**stack.default_sh_args)
            except error.DockerCommandFailed:
                if not ignore_errors:
                    raise
                self.log.debug(
                    f"Ignoring stop failure in case of recreate for stack: {stack.stack_name}"
                )

    @stack_target
    def cmd_stack_ps(self, stacks=None):
        "List stacks process"

        if len(stacks) < 1:
            self.log.notice("  No process founds")
            return

        # self.log.notice("List of processes:")
        for stack in stacks:
            # self.log.notice(f"Process of stack: {stack.stack_name}")
            stack.engine.ps()

    # Shortcuts
    # ======================
    @stack_target
    def cmd_stack_apply(self, stacks=None):
        "Apply a stack"

        self.log.notice("Apply stacks")
        self.cmd_stack_assemble(stacks=stacks)
        self.cmd_stack_up(stacks=stacks)
        self.log.notice("Stack has been applied")

    @stack_target
    def cmd_stack_recreate(self, stacks=None):
        "Recreate a stack"

        self.log.notice("Recreate stacks")
        self.cmd_stack_down(stacks=stacks, ignore_errors=True)
        self.cmd_stack_assemble(stacks=stacks)
        self.cmd_stack_up(stacks=stacks)
        self.log.notice("Stack has been recreated")

    # Other commands
    # ======================

    def cmd_stack_ls(self, stacks=None):
        "List command to stacks"

        for stack in self.get_children():
            stack_app = stack.app.app if stack.app else None
            print(f"  - {stack.stack_name}:")
            print(f"      app: {stack_app}")
            print(f"      path: {stack.stack_path}")

    @stack_target
    def cmd_stack_vars(self, stacks=None, vars_=None, explain=False):
        "Show vars of stack"

        if isinstance(vars_, list):
            self.log.info(f"Restrict output to variables: {','.join(vars_)}")

        for stack in stacks:
            self.log.notice(f"Get stack vars: {stack.stack_name}")
            ret = stack.assemble(vars_only=vars_ or True, explain=explain)
            # TODO: PAtch cafram to support ordered yaml output !
            # See: https://github.com/barbu-it/cafram/blob/main/cafram/utils.py#L261
            # See: https://stackoverflow.com/questions/40226610/ruamel-yaml-equivalent-of-sort-keys
            if ret:
                pprint(ret)
            # print (to_yaml(ret))

    @stack_target
    def cmd_stack_explain(self, stacks=None):
        "Show informations on project plugins"

        for stack in stacks:
            stack.explain_tags()

        # if isinstance(mode, str):
        #     dst_path = mode
        #     self.log.notice("Generate documentation in dir:", dst_path)
        #     for stack in self.get_children():
        #         stack.gen_doc(output_dir=dst_path)

    @stack_target
    def cmd_stack_logs(self, stacks=None, follow=False):
        "Display stack/services logs"

        if follow and len(stacks) > 1:
            self.log.warning(
                "Disabling log following as it's not possible on more tha one stack"
            )
            follow = None

        for stack in stacks:
            self.log.notice(f"Logs of stack: {stack.stack_name}")
            stack.engine.logs(follow)
