# Concepts

## User Interface

Paasify provides two interfaces:

* Executable program via the `paasify` binary
* Python library called `paasify`


Paasify is shipped with a an executable called `paasify`. It provides a first class interface to
interact with a paasify project. It is also possible to use Paasify via it's 
python API `paasify` ([Documentation](/schema_doc/python_app)).

### Configuration file

By convention, a paasify store the whole user configuration in a `paasify.yml` file.
This is the entrypoint of a project.

### Current directory context

The command line is contextualized depending your current working directory. Paasify
will try to find the upper level `paasify.yml` file. If a project is found, will work 
as if executed at the root of this project directory. If your current working directory
is inside a stack, then all commands will apply on this stack:


``` console
# For a given file hierarchy
$ tree .


# No project enabled
$ paasify ctx
Outside project
No current stack

# Only project enables
$ cd prj1
$ ls -1
paasify.yml
$ paasify ctx
Inside project
No current stack

# Project and stack enabled
$ cd stack1
$ paasify ctx
Inside project
Current stack: stack1
```

!!! tip "Specifying specific stacks/service from project"
    You can most of the time just prepend the stack name
    at the end of the command. An optional last argument can accept
    a specific service, like:
    ``` console
    paasify recreate <stack_name>
    paasify logs <stack_name> <service>
    ```

This behavior is similar for both CLI and python library.

## Project (Configuration)

A project exists when a `paasify.yml` configuration file exists in a directory. The
presence of this file determines the project root repository.

A project will define:

* A list of stacks:
    * Each stack represent an application to deploy
    * Each stack is binded to one `docker-compose.yml` file
    * This list is sequential, created in the defined order, removed in the reversed order
* A list of sources:
    * Each source is a reusable application
    * They can be deployed and distributed
    * May be considered as a project dependencies
    * May provide some extras plugins
* A global default configuration:
    * Allow to apply settings on each stacks.
    * Allow to default some behaviors



### Project stacks

A project is the top level configuration for a list of given stacks.

#### Stacks

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

But globally:
``` yaml title="paasify.yml" hl_lines="1-3"
config:
  vars:
    myvar: my_value_default
stacks:
  - name: traefik
    vars:
      myvar: my_value_override
```


#### Stacks tags


A tag can either corresponds to:

* a docker-compose: `docker-compose.<tag_name>.yml` YAML file
* a jsonnet script: `<tag_name>.jsonnet` jsonnet file


!!! info "There are two types of plugins"
    Related documentation is available [here](/advanced#two-kinds-of-plugins)
    

Both mechanisms allow to achieve different things, while the former
provide a well-known docker-compose merge mechanism, it may not
sufficient to provide advanced functionnality, and this is where the 
later become useful, leveraging the jsonnet language support to modify
docker-compose structure. 

Checkout [Advanced topics](advanced.md) to learn more.

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
