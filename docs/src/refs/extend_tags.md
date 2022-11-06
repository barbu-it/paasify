# Tag plugins


## Two kinds of plugins

There are two kinds of plugins:

* a docker-compose: `docker-compose.<tag_name>.yml` YAML file
* a jsonnet script: `<tag_name>.jsonnet` jsonnet file

A plugin can be used for:

* Providing extra variables
* Transform docker-compose final file

How to choose between both?

|  | docker-compose | jsonnet |
|---|---|---|
| Pros | <ul> <li>Well known merge mecanism, supported by docker</li><li>Easy to learn</li></ul> | <ul> <li>Can be used many times, with differents parameters</li><li>Allow to create variables</li> <li>Very powerful turing language to manupulate docker-compose content</li> <li>Provides a convenient API/plugin system </li></ul> |
| Cons | <ul> <li>Can be used only once</li><li>Quite limited on advanced use case, such as rewrite or modification</li></ul> | <ul> <li>Need to learn jsonnet language</li><li>Hard to learn and debug</li></ul> |

See how to [create plugins](extend/extend_plugins.md) for further infos.


::: paasify.stack_components.PaasifyStackTag.lookup_docker_files_tag
    options:
      show_root_heading: False
      show_source: true
      heading_level: 3
      # show_category_heading: true

::: paasify.stack_components.PaasifyStackTag.lookup_jsonnet_files_tag
    options:
      show_root_heading: False
      show_source: true
      heading_level: 3
      # show_category_heading: true



## docker-compose tag

This is the easiest and simplest form of modularity to use. Just create
your `docker-compose.<tag_name>.yml` fragments, like explained
[here](https://docs.docker.com/compose/extends/).


#### Documenting Plugins

TODO: jsonschema

#### Test and debug Plugins

TODO: Add features to support plugin development


## Jsonnet tag

This is a full turing compliant language avaialable to modify the
docker-compose internal structure. Jsonnet language is 
documented [here](https://jsonnet.org/learning/tutorial.html)





#### Documenting Plugins

TODO: jsonschema

#### Test and debug Plugins

TODO: Add features to support plugin development


