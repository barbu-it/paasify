

--8<-- "../README.md::48"


<p align='center'>
<img src="static/overview.svg" alt="Overview">
</p>


--8<-- "../README.md:88:138"


### Configuration

There is a simple config file that illustrate all componants, taken from the previous [wordpress example project](https://github.com/barbu-it/paasify-example-wordpress):
``` yaml title="paasify.yml"
sources:
  - name: community
    remote: https://github.com/barbu-it/paasify-collection-community

config:
  namespace: demo-wp
  extra_vars:
    - secrets.yml
  vars:
    # We expose to 127.0.0.1, under the *.locahost domain
    app_expose_ip: 127.0.0.1
    app_domain: localhost

    # Other domain examples
    #app_domain: mydomain.org
    #app_domain: localtest.me
    #app_domain: ${app_expose_ip}.nip.io

    # Default traefik network
    traefik_net_name: ${_prj_ns}_proxy_default
  tags_prefix:
    - homepage
    - traefik-svc

stacks:
  - app: proxy
    vars:
      traefik_net_external: False
    tags:
      - expose_http
      - expose_admin
  - app: home
  - app: community:wordpress
```

The first config element is `sources`, which is a list of git repo collections. The config contains 
all settings that will apply to the project and its stacks. The `stacks` key is a list of sequential stack to be applied.
Each stack is configurable and allow a fine grained configuration override dependings the user needs.
To each stack can be applied vars and/or a list of tags. Finally the `config` key allow to put project
and default stack configuration.

Then, you just have to run the following to set all up and running:

``` console
paasify apply
```

You should be able to access to a fresh Wordpress instance on [http://wordpress.localhost]() url while your
project dashboard should be accessible on [http://home.localhost]().


## What next?

Please start with one of:

* [Tutorial](jupyter/learn_101): More examples with some uses cases
* [Concepts](docs/concepts): To understand Paasify core concepts
* [Usage](docs/usage): To see how to use Paasify
* [Plugins](plugins_apidoc/): Get collection reference
* [Reference](refs/): Get reference and config schemas

