

--8<-- "../README.md::46"


<p align='center'>
<img src="static/overview.svg" alt="Overview">
</p>


--8<-- "../README.md:85:111"




Below a ten thousand foot overview, this will deploy a wordpress with its database and a front proxy.

## Simple example project

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

A `source` is a list of git repo collections. The config contains all settings that will
apply to the project and its stacks. The `stacks` key is a list of sequential stack to be applied.
Each stack is configurable and allow a fine grained configuration override dependings the user needs.
To each stack can be applied vars and/or a list of tags.

Then, you just have to run the following to set all up and running:

``` console
paasify apply
```

You should be able to access to a fresh Wordpress example on localhost.


## Where to start


Please start with one of:

* [Tutorial](jupyter/learn_101)
* [Concepts](docs/concepts)
* [Usage](docs/usage)
* [Plugins](plugins_apidoc/)
* [Reference](refs/)
