# Base



Paasify provides a way to extend apps, via different concepts:

* project
* repository
* collection
* app
* tag
    * docker-compose tag
    * jsonnet tag

## Concepts

A repo:

* is collection or a set of collections hierarchically organized

A collection can include:

* A set of apps definitions (/<app_name>/)
* A set of plugins (.paasify/plugins/*.jsonnet)

An app can include:

* a set of default variables (vars.yml)
* An app definitions (docker-compose.yml)
* Tags definitions (docker-compose.<tag>.yml)
* A set of plugin for this app (<tag>.jsonnet)

A tag can be:

* A simple docker-compose file prefixed with the tag name
* A jsonnet file that understand a json API

A project is:

* A directory where lives `paasify.yml`
* Can include all of the above





## Project


### File hierarchy

Each component must follow a hierarchical file structure convention:

Project file structure:

```
* project1/
    * paasify.yml: Main configuration config
    * .paasify/
        * collections/: Managed paasify sources dir ! (TMP dir)
        * plugins/
            * <tag_name>.jsonnet
    * stack1/
        * vars.yml
        * docker-compose.yml: Default docker-compose file, overrides from source
        * docker-compose.run.yaml: Generated docker compose file !
        * docker-compose.<tag_name>.yml: Custom tags
    * stack2/
    * stack3/
* project2/
```


## App

TODO

### Tags


!!! info
    A dedicated page is [available here](extend_tags) for tags.


## Collection

TODO

### File hierarchy

Collection file structure:
```
* collection_ident1:
    * .paasify/
        * plugins/
            * <tag_name>.jsonnet: Common stack plugins
    * stack1/
        * vars.yml
        * docker-compose.yml
        * docker-compose.<tag_name>.yml
            * docker-compose.debug.yml
            * docker-compose.mysql.yml
            * docker-compose.smtp.yml
        * <tag_name>.jsonnet: Local stack plugin
    * stack2/
* collection_ident2:
```

Each collection is contained in a git repo. A git repo can have many collections. Many app are available
inside each collection. A collection can alos provides plugins, like stacks.



## Repository

TODO

### File hierarchy
