# -*- coding: utf-8 -*-
"""
Collection Library
"""


# Imports
# =====================================================================


import os
from pathlib import PosixPath

# from pprint import pprint

import anyconfig
from json_schema_for_humans.generation_configuration import GenerationConfiguration
from json_schema_for_humans.template_renderer import TemplateRenderer

from json_schema_for_humans.generate import copy_additional_files_to_target
from json_schema_for_humans.schema.schema_to_render import SchemaToRender

from cafram.utils import (
    to_yaml,
    to_json,
    write_file,
    read_file,
    first,
)
import paasify.errors as error

from paasify.framework import PaasifyObj, FileLookup
from paasify.stack_components import StackAssembler

# from paasify.common import get_paasify_pkg_dir


# Global variables
# =====================================================================


DOC_APP_1 = """
# {name}

Documentation for app: `{name}`

## Documentation

{app_readme}


## Variables

``` yaml title="vars.yml"
{app_vars}
```

## Docker compose files



"""

DOC_APP_2 = """

### {name}


``` yaml title="{source}"
{dockerfile}
```


"""


DOC_JSONNET_1 = """
# {requested_ident}

{name}


{description}

## Documentation

{meta_readme}


## Metadata

``` yaml
{meta_yaml}
```

## Tag documentation

This documentation is autogenerated from the plugin source code. The single
html page is [here]({slug}.html).

<script type="text/javascript" src="https://code.jquery.com/jquery-1.8.3.js"></script>
<script type="text/javascript" src="/paasify/static/paasify.js"></script>

<iframe id="schemadoc" src="../{slug}.html"
width="100%" height="600px"
frameborder="0"
overflow="hidden"
/>

"""


DOC_SITE_1 = """
# {title}


{app_readme}


## Applications

{app_list_fragment}

## Jsonnet plugins

{jsonnet_list_fragment}


---

<sup>Made with :heart: by [mrjk](https://github.com/mrjk) for [Paasify](https://github.com/barbu-it/paasify)</sup>

"""


# Helpers
# =====================================================================


def gen_schema_doc(schema_file, dest_dir, filename, config=None, **kwargs):
    "Generate documentation for a given schema"

    # Prepare config
    final_config = dict(
        minify=True,
        deprecated_from_description=False,
        default_from_description=False,
        expand_buttons=False,
        link_to_reused_ref=False,
        # copy_css=copy_css,
        # copy_js=copy_js,
        # config=config_file,
        # config_parameters=config,
    )
    user_config = config or {}
    final_config.update(user_config)
    config = GenerationConfiguration(**final_config)

    dest_html = os.path.join(dest_dir, filename)
    schema_to_render = SchemaToRender(
        PosixPath(schema_file),  # Source schema
        PosixPath(dest_html),  # Destination file
        PosixPath(dest_dir),  # Destination dir
    )

    template_renderer = TemplateRenderer(config)
    schema_to_render.render(template_renderer, None)
    copy_additional_files_to_target([schema_to_render], config)

    return dest_html


# Main Application class
# =====================================================================


class CollectionScanner(PaasifyObj):
    """A Collection Scanner Object

    Useful for scanning the content of a collection

    requirement: one path to lookup
    """

    # ident = "CollectionScanner"

    def __init__(self, *args, parent=None, path=None, **kwargs):

        # print ("RECEIVED", args, kwargs)

        # super().__init__(*args, **kwargs)
        self.log = parent.log

        self.path_raw = path
        self.jsonnets = None
        self.apps = None

        # Init object
        self.scan_collection(path)

    def scan_collection(self, path):
        "Find available apps for a given collection path"

        search_for_jsonnet = False
        match_apps = {}
        match_jsonnets = []

        # Check for apps
        for root, dirs, files in os.walk(path):
            for name in dirs:
                if name.startswith("_"):
                    pass
                elif name == ".paasify":
                    search_for_jsonnet = True
                else:
                    target = os.path.join(path, name)
                    match_apps[name] = self.scan_app(target)

            # Itereate one leve deep only, so we quit here
            # Maybe we should find for all docker-compose.yml ...
            break

        # Check for jsonnet plugins
        if search_for_jsonnet:
            plugin_dir = os.path.join(path, ".paasify", "plugins")
            match_jsonnets = self.scan_jsonnets(plugin_dir)

        # Return results
        self.apps = match_apps
        self.jsonnets = match_jsonnets
        return {
            "jsonnets": match_jsonnets,
            "apps": match_apps,
        }

    def scan_app_file(self, path, name):
        "Scan a single app file to determine what it is"

        ret = None
        file_dir = os.path.join(path, name)
        file_ = name
        if file_.startswith("_"):
            # We ignore everything starting by _
            pass
        elif file_ in ["README.md"]:
            ret = {
                "type": "doc",
                "dir": file_dir,
                "name": "main",
            }
        elif file_.endswith("md"):
            name = file_.replace(".md", "")
            ret = {
                "type": "doc",
                "dir": file_dir,
                "name": name,
            }
        elif file_ in ["vars.yml"]:
            ret = {
                "type": "vars",
                "dir": file_dir,
                "name": "main",
            }
        elif file_.startswith("docker-compose"):
            if file_ == "docker-compose.yml" or file_ == "docker-compose.yaml":
                ret = {
                    "type": "docker_file",
                    "dir": file_dir,
                    "name": "main",
                }
            else:
                name = file_.replace(".yml", "")
                name = name.replace("docker-compose.", "")
                ret = {
                    "type": "docker_file",
                    "dir": file_dir,
                    "name": name,
                }
        elif file_.endswith("jsonnet"):
            name = file_.replace(".jsonnet", "")
            ret = {
                "type": "jsonnet_app",
                "dir": file_dir,
                "name": name,
            }

        return ret

    def scan_app(self, path, name=None):
        "Scan a single app"

        if not os.path.isdir(path):
            return None

        name = name or os.path.basename(path)
        matches = []
        for root, dirs, files in os.walk(path):
            for file_ in files:
                ret = self.scan_app_file(path, file_)
                if ret:
                    matches.append(ret)

            break
        return matches

    def scan_jsonnets(self, path):
        "Scan single dir for jsonnets"

        if not os.path.isdir(path):
            return None

        matches = []
        for root, dirs, files in os.walk(path):

            for file_ in files:
                ret = None
                file_dir = os.path.join(path, file_)
                if file_.startswith("_"):
                    pass
                elif file_.endswith("jsonnet"):
                    name = file_.replace(".jsonnet", "")
                    ret = {
                        "type": "jsonnet",
                        "dir": file_dir,
                        "name": name,
                    }
                if ret:
                    matches.append(ret)
            break
        return matches


class CollectionDocumator(PaasifyObj):
    """A Collection Documator Object

    Generate documentation for a path that represent a collection

    requirement: one path to lookup,
    optional : dest_dir,  otherwhise inside .paasify/docs/
    """

    ident = "DocGen"

    DEFAULT_DOC_DIR = "_docs"

    def __init__(self, parent=None, path=None, dest_dir=None, name=None, **kwargs):

        self.log = parent.log
        # super().__init__(*args, **kwargs)

        # print ("NEW COLLECTION", path)
        path_abs = os.path.abspath(path or ".")

        self.path = path
        self.dest_dir = dest_dir
        self.name = str(name or os.path.basename(path_abs)).strip(os.sep)

        # print ("CURRENT ANEM", self.name, path)
        self.scanner = CollectionScanner(parent=self, ident=self.name, path=path)

    def generate(
        self, format=None, path=None, dest_dir=None, singleton=True, mkdocs_config=None
    ):
        "Generate collection documentation"

        path = path or self.path
        dest_dir = dest_dir or self.dest_dir

        assert path, f"Path does not exists: {path}"
        if not os.path.exists(path):
            assert False, f"Path does not exists: {path}"

        # Prepare stack builder
        sta = StackAssembler(parent=self, ident=f"{self}")
        dest_dir = dest_dir or os.path.join(path, ".paasify", self.DEFAULT_DOC_DIR)

        # Ensure that dest dir exists
        if not os.path.isdir(dest_dir):
            self.log.notice(f"Creating parent directories: {dest_dir}")
            os.makedirs(dest_dir)

        jsonnet_list = self._generate_jsonnet(sta, dest_dir)
        app_list = self._generate_apps(dest_dir)
        self._generate_index_page(
            dest_dir, app_list=app_list, jsonnet_list=jsonnet_list
        )
        if mkdocs_config:
            self._generate_mkdoc_config(mkdocs_config)

        self.log.notice(f"Documentation generated in: {dest_dir}")

    def retitle(self, md_text, lvl):
        "Increase title levels"
        char = "#"
        ret = []
        for line in md_text.split("\n"):

            if line.startswith(char):
                line = char * lvl + line
            ret.append(line)
        return "\n".join(ret)

    def _generate_apps(self, dest_dir):
        "Generate apps doc"

        apps = self.scanner.apps

        # Loop over each jsonnet
        ret = []
        for app_name, files in apps.items():

            self.log.info(f"Generate app doc '{app_name}' having {len(files)} file(s)")

            slug = f"app_{app_name}"
            main_components = [file_ for file_ in files if file_.get("name") == "main"]

            # README and vars
            file_readme = first([f for f in main_components if f.get("type") == "doc"])
            file_vars = first([f for f in main_components if f.get("type") == "vars"])

            app_conf = {}
            app_readme = "No readme"
            app_vars = "No var file"
            if file_readme:
                app_readme = read_file(file_readme["dir"])
                app_readme = self.retitle(app_readme, 2)
            if file_vars:
                app_vars = read_file(file_vars["dir"])
                conf = anyconfig.load(file_vars["dir"])
                app_conf = conf or {}

            # Generate docker compose doc fragements
            docker_files = [f for f in files if f.get("type") == "docker_file"]

            if len(docker_files) < 1:
                self.log.warning(f"Skip invalid app: {app_name}")
                continue

            # docker_file_main = [ret for ret in docker_files if ret.get("name") == "main" ]
            index = next(
                (
                    i
                    for i, item in enumerate(docker_files)
                    if item.get("name") == "main"
                ),
                -1,
            )
            docker_file_main = [docker_files.pop(index)]

            extra = []
            loop = docker_file_main + docker_files
            for docker_file in loop:

                content = read_file(docker_file["dir"])
                source = os.path.basename(docker_file["dir"])

                frag = DOC_APP_2.format(
                    name=docker_file["name"], source=source, dockerfile=content
                )

                extra.append(frag)

            # Generate top fragment
            _dest = f"{dest_dir}/{slug}.md"
            vars_ = {
                "name": app_name,
                "requested_ident": app_name,
                "kind": "app",
                "app_vars": app_vars,
                "app_readme": app_readme,
                "md_file": _dest,
            }
            vars_.update(app_conf)
            app_doc = DOC_APP_1.format(**vars_)
            app_doc = app_doc + "\n".join(extra)

            # Write output

            self.log.info(f"Write app markdown doc: {_dest}")
            write_file(_dest, app_doc)
            ret.append(vars_)

        return ret

    def _generate_jsonnet(self, sta, dest_dir):
        "Generate jsonnect schema doc"

        jsonnets = self.scanner.jsonnets

        # Prepare json-schemadoc
        config = dict(
            minify=False,
            deprecated_from_description=True,
            default_from_description=False,
            expand_buttons=False,
            link_to_reused_ref=False,
            # copy_css=copy_css,
            # copy_js=copy_js,
            # config=config_file,
            # config_parameters=config,
        )

        # Loop over each jsonnet
        ret = []
        for jsonnet in jsonnets:
            self.log.info(f"Generating doc for {jsonnet}")

            # Prepare vars
            # =========================
            name = jsonnet["name"]
            type_ = jsonnet["type"]
            jsonnet_desc = jsonnet.get("description")
            slug = f"{type_}_{name}"
            jsonnet_file = jsonnet["dir"]
            # pkg_dir = get_paasify_pkg_dir()
            # conf_file = os.path.join(pkg_dir, "assets", f"jsondoc_jsonnet_{type_}.yml")

            # Parse jsonnet metadata
            # =========================
            params = {
                "args": {},
            }
            try:
                plugin_meta = sta.process_jsonnet_exec(
                    jsonnet_file,
                    "metadata",
                    params,
                    # import_dirs=jsonnet_lookup_dirs,
                )
            except error.JsonnetBuildFailed:
                self.log.error(f"Skip invalid jsonnet: {jsonnet}")
                continue

            # Extract plugin metadata
            json_schema = plugin_meta.pop("jsonschema", {})
            md_readme = plugin_meta.pop(
                "readme", "No documentation provided by the plugin"
            )
            md_readme = self.retitle(md_readme, 2)
            yaml_meta = to_yaml(plugin_meta)

            # Create markdown doc
            # =========================
            vars_ = {
                "requested_ident": name,
                "name": name,
                "description": jsonnet_desc,
                "slug": slug,
                "meta_readme": md_readme,
                "meta_yaml": yaml_meta,
                "kind": type_,
                # name=name,
                # slug=slug,
                # meta_readme=md_readme,
                # meta_yaml=to_yaml(plugin_meta),
                # kind=type_,
            }
            vars_.update(plugin_meta)

            # Generated various docs
            md_doc = DOC_JSONNET_1.format(**vars_)
            _dest = f"{dest_dir}/{slug}.md"
            self.log.info(f"Write markdown doc: {_dest}")
            write_file(_dest, md_doc)

            _dest_schema = f"{dest_dir}/{slug}.json"
            self.log.info(f"Write json schema: {_dest_schema}")
            write_file(_dest_schema, to_json(json_schema))

            # Update results
            vars_.update(
                {
                    "md_file": _dest,
                    "json_schema_file": _dest_schema,
                }
            )
            ret.append(vars_)

            # Generate jsonnet schema doc
            # =========================
            # dest_html = os.path.join(dest_dir, f"{slug}.{ext}")
            gen_schema_doc(_dest_schema, dest_dir, f"{slug}.html", config=config)

        return ret

    def _generate_index_page(self, dest_dir, app_list=None, jsonnet_list=None):
        "Generate a singleton module documentation"

        app_list = app_list or []
        jsonnet_list = jsonnet_list or []
        path = self.path
        pattern = ["README.md", "README.txt"]

        # Generate README
        app_readme = "No readme"
        file_readme = FileLookup(path=path, pattern=pattern).paths(first=True)
        if file_readme:
            app_readme = read_file(file_readme)
            app_readme = self.retitle(app_readme, 2)

        # Generate app fragments
        app_list_fragment = ["List of applications: ", ""]
        for app in app_list:
            fname = os.path.basename(app["md_file"])
            # app_ident = app["requested_ident"]
            app_name = app["name"]
            app_product = app.get("app_product", None)
            app_desc = app.get("app_description", app.get("homepage_description", ""))
            app_image = app.get("app_image", "")
            app_image_name = app.get("app_image_name")
            app_image_version = app.get("app_image_version")

            # app_icon = app.get("app_icon")

            if app_image_name:
                app_image = app_image_name
                if app_image_version:
                    app_image = f"{app_image}:{app_image_version}"

            app_sup = ""
            if app_image:
                app_sup += app_image
            if len(app_sup) > 0:
                app_sup = f" <sup>({app_sup})</sup>"

            app_line = []
            if app_product and app_product != app_name:
                app_line.append(app_product)
            if app_desc:
                app_line.append(app_desc)

            app_line = (": " + ", ".join(app_line)) if len(app_line) > 0 else ""
            if len(app_sup) > 0:
                app_line += app_sup

            line = f"  * [`{app_name}`]({fname}){app_line}"
            app_list_fragment.append(line)

        # Generate jsonnet fragments
        jsonnet_list_fragment = ["List of jsonnet plugins:", ""]
        for jsonnet in jsonnet_list:
            fname = os.path.basename(jsonnet["md_file"])
            jsonnet_ident = jsonnet["requested_ident"]
            jsonnet_name = jsonnet["name"]
            jsonnet_desc = jsonnet.get("description", None)

            jsonnet_line = (jsonnet_desc or jsonnet_name) if jsonnet_desc else ""
            jsonnet_line = (": " + jsonnet_line) if len(jsonnet_line) > 0 else ""
            line = f"  * [`{jsonnet_ident}`]({fname}){jsonnet_line}"
            jsonnet_list_fragment.append(line)

        # Generate format vars
        vars_ = {
            "name": self.name,
            "title": "Overview",
            "app_readme": app_readme,
            "app_list_fragment": "\n".join(app_list_fragment),
            "jsonnet_list_fragment": "\n".join(jsonnet_list_fragment),
        }

        # Generate doc
        col_doc = DOC_SITE_1.format(**vars_)
        _dest = f"{dest_dir}/index.md"
        self.log.info(f"Write collection markdown doc: {_dest}")
        write_file(_dest, col_doc)

    def _generate_mkdoc_config(self, dest_dir):
        "Generate mkdocs config"

        self.log.info("Gen mkdocs not implemented yet")
