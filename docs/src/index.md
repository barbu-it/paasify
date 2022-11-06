# Overview

Paasify try to make docker compose files deployment easier and more reproducible. The whole point is to deploy
docker containers:

* docker container: Actual workload
* docker-compose: Create docker containers
* paasify: Manage many docker-compose

So paasify is built over the concept of project, where is defined a sequential list of stacks. Each stacks corresponds to
a docker-compose file to be deployed. The whole is configured via a `paasify.yml` config file along a predetermined
file hierarchy.

Below a ten thousand foot overview.

## Quickstart example project

There is a simple config file that illustrate all componants:
``` yaml title="paasify.yml"
source:
    default:
        url: http://gthub.com/mrjk/...git
    internal:
        url: http://internal.org/mrjk/...git
config:
    vars:
        app_domain: domain.com
stacks:
  - name: traefik
    vars:
        app_fqdn: front.domain-admin.com
  - name: wordpress
    tags:
        mysql-sidecar
  - name: hello
    source: internal
    tags:
        mysql-sidecar
```

A source is a list of git repo collections. The config contains all settings that will
apply to the project and its stacks. The stacks is a list of sequential stacks to be applied.
Each stack is configurable and allow a fine grained configuration override dependings the user needs.
To each stack can be applied vars or a list of tags.

Then, you just have to run the following to set all up and running:

``` console
paasify apply
```

You should be able to access to a fresh Wordpress example on localhost.


## Where to start


Please start with one of:

* [Introduction](introduction)
* [Tutorial](howto/learn_101)
* [Concepts](concepts.md)
* [Reference](schema_doc/index.md)
* [Examples directory](examples)



