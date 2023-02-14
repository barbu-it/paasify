# Setup

This page explains how to get a full developper environment. It either can be installed via bash or direnv.

## Quickstart

### Install from git

Everything starts with:
```
$ git clone --recurse-submodules git@barbu-it.com:paasify/paasify.git
$ cd paasify
```

If you forgot the `--recurse-submodules`, you can do from inside the git repo:
```
$ git submodule update --init --recursive
```

The you will have to setup a python virtual environment, and install project dependencies


### With direnv

If you already have a working `direnv` setup, then review `.envrc` and enable it, otherwize skip to the next section:

```
$ cd paasify
$ direnv allow
```
The first run might be long to run as the script will ensure you have all development dependencies.

!!! info "Completion support"
    There is no support for completion within `direnv`, to enable completion
    simply source arctivate again: `. ./scripts/activate.sh`


### Manually

Each time you get into the project, you will have to source the project:

```
$ . ./scripts/activate.sh
```

This basically source into your shell everything that is required to have a working development 
environment. Be aware that the first run may take quite a long time. You wil have to source this file 
each time you enter in the project.

### Other actions

Paasify project follow the [scripts-to-rule-them-all](https://github.blog/2015-06-30-scripts-to-rule-them-all/) 
standard. You can get a list of available commands:

```
$ task --list
```

For more details, please check out [paasify](paasify.md) workflow.


## Implementation details

### Install project build dependencies

Once task is installed, it will take care of the rest to do:

```
$ task bootstrap
```

After few minutes, it will have done:

* Install or upgrade poetry
* Install project dependencies and dev dependencies.

You have now a fully working environment, but `paasify` is not available yet.

!!! question "When to run this command?"
    You may need to run this command again if you added or modified project dependencies


### Install paasify

Install paasify itself:

```
task setup
```

!!!  info: you may
     You may need to run this command again if you modified paasify script entry-points. Basically this one only run `poetry install --only-root`.
