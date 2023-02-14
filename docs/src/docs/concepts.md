# Concepts

Paasify try to make docker compose files deployment easier and more reproducible. The whole point is to deploy
docker containers. A general overview of docker looks like:

* docker: container engine
* docker container: containerized process
* docker-compose: create docker containers with yaml files

Paasify introduces some new top level concepts:

* paasify project: a custom association of stacks
* paasify stacks: an application deployable with docker-compose
* paasify collection: collection of stacks in a git repo
* paasify: program to manage paasify project

So paasify is built over the concept of project, where is defined a sequential list of stacks. Each stacks corresponds to
a docker-compose file to be deployed. The whole is contained inside the notion of project,  which is declared in
a `paasify.yml` config file, at the root of your project directory.


## Overview

Paasify provides two interfaces:

* Executable program via the `paasify` binary
* Python library called `paasify`

Paasify is shipped with a an executable called `paasify`. It provides a first class interface to
interact with a paasify project. It is also possible to use Paasify via it's
python API `paasify` ([Documentation](/schema_doc/python_app)).

### Configuration file

By convention, a paasify store it's whole configuration in a `paasify.yml` file.
This is the entrypoint of a project. This file is usually meant to be commited, if you use git.


### Ten thousand feet overview

A project exists when a `paasify.yml` configuration file exists in a directory. The
presence of this file determines the project root repository. A project is composed of the following elements:


* `config:` A global default configuration:
    * Allow to apply settings on each stacks.
    * Define global behaviors

* `sources:` A list of sources:
    * Each source is mapped to a collection of reusable applications
    * They can be a path or a git url
    * May provide matter to deploy to your project
    * May be considered as your project dependencies
    * A collection:
        * It's a directory containing applications and jsonnet plugins
        * You can either use predefined collections or make your owns
        * A collection is usually managed as a git repo
        * A collection can also provides jsonnet plugins
        * An application:
            * Provides at least one `docker-compose.yml` file
            * Optionnaly provides tagged `docker-compose.$TAG.yml` files
            * Optionnaly provides jsonnet plugin `$TAG.jsonnet` files

* `stacks:` A list of stacks:
    * Each stack represent application(s) to deploy
    * Each stack is binded to one `docker-compose.run.yml` file
    * This list is sequential, created in the config order, removed in the reversed order
    * Stack:
        * Defined by a name and binded to a subdirectory
        * Allow to define which vars and tags you want your stack have


The following chapters will explore more in depth each components.


## Project stacks

A stack is a simple set of dependant services, it would be comparable
to a kubernetes pod.

The simplest stack form is
``` yaml title="paasify.yml"
stacks:
  - name: traefik
```

A Stack is support most of CLI operations, like: start, stop, build, info ...

#### Stacks vars

To assign vars to stack:

``` yaml title="paasify.yml" hl_lines="3-4"
stacks:
  - name: traefik
    vars:
      myvar: my_value_override
```

And globally:

``` yaml title="paasify.yml" hl_lines="1-3"
config:
  vars:
    myvar: my_value_default
stacks:
  - name: traefik
    vars:
      myvar: my_value_override
```

You can call other vars as well with this syntax, and do things like:

``` yaml title="paasify.yml" hl_lines="3-4 8-9"
config:
  vars:
    myvar: default
    myvar_prefix: my_value
stacks:
  - name: traefik
    vars:
      myvar: ${myvar_prefix}_override
      myvar_orig: $myvar
```

!!! warning "Stack vars and container environment variables are different"

    Stack vars are used to feed the docker-compose parserr; none of these variables
    are passed to container environment by default.


#### Stacks tags

A tag can either corresponds to:

* a docker-compose: `docker-compose.<tag_name>.yml` YAML file
* a jsonnet script: `<tag_name>.jsonnet` jsonnet file


!!! info "There are two types of plugins"

    Related documentation is available [here](../refs/extend_tags)


Both mechanisms allow to achieve different things, while the former
provide a well-known docker-compose merge mechanism, it may not
sufficient to provide advanced functionnality; and this is where the
later become useful, leveraging the jsonnet language support to modify
docker-compose structure.

Checkout [Advanced topics](../refs/extend_tags) to learn more.

To assign vars to stack:
``` yaml title="paasify.yml" hl_lines="3-5"
stacks:
  - name: traefik
    tags:
      - tag1
      - tag2
```

To assign vars to jsonnet tag:

``` yaml title="paasify.yml" hl_lines="8-11"
config:
  tags_prefix:
      - tag1
      - tag2
stacks:
  - name: traefik
    tags:
      - tag3
      - tag4:
          tag_var1: value1
          tag_var2: value2
```

#### Stacks App Collection

Paasify provides a way to make your code DRY be exposing a app repository
feature. You can use any git repo to create a stack collection

``` yaml title="paasify.yml" hl_lines="1-3 6"
sources:
    myapps:
      url: http://github.com/mrjk/paasify_collection.git
stacks:
  - name: traefik
    app_source: myapps
  - app: myapps:traefik
```


### Project sources

In way to keep code DRY, Paasify allow to package reusable apps.

It is composed of the following conepts:

* Application:
    * Provide default configuration
    * Provide optional docker tags
    * Provide options jsonnet plugins
    * Provide a default vars.yml
* Application collection:
    * A git repository containing a list of applications
    * Provide collection jsonnet tags

#### Apps

An app is a single application component.

TODO

#### Apps collections

TODO

#### Source management

Paasify provides some way to deal with sources:

``` console
# Install missing depenencies
paasify src install
paasify src install <source_name>

# Update dependencies
paasify src update
paasify src update <source_name>
```

## Stacks (Operation)

When configuration is ok, you can play with actual containers lifecycle.

### Check configuration

To test paasify config:

```
paasify config
```

The command must return 0 exit code or return an error message in `stderr`.

### Common operations

Most common operations are the following:

``` console
paasify up
paasify down
paasify apply

paasify recreate stack_name

```

### Debug and troubleshooting

Paasify provides logging support:

``` console
paasify logs
paasify logs -f
paasify logs -f stack1
paasify logs -f stack1 service
```

You can always recreate a an app without wiping data:
```
paasify reset stack1 service
```

Or completely delete all data:
```
paasify reset --erase stack1 service
```


### Managing many projects

TODO


## Glossary


* Project
* Project Config
* Project Config
* Project Config Vars
* Project Config Tags
* Project Source
* Project Stacks

* Stack
* Stack Config
* Stack Vars
* Stack Tags
* Stack Collection App

* Collection Repository
* Collection App
* Collection Plugin
