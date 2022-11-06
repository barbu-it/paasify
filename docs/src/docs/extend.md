# Extend with Jsonnet



!!! info
    Plugin reference is [available here](/extend/extend_plugins/#jsonnet-tag)

Start here to extend paasify functionnalities with a jsonnet plugin.

## Plugins Development

TODO: Link and explain link to paasify.libjsonnet


Actions:

* metadata
* vars_default(vars)
* vars_override(vars)
* docker_transform(vars, docker_compose)

LINK: To variable processing order


### Base Plugins

This what looks like a basic plugin:
```
local paasify = import 'paasify.libsonnet';

local plugin = {

  // Provides plugin metadata
  metadata: {
      name: "Example plugins",
      description: 'Example plugin',

      author: "My Name",
      email: '',
      license: '',
      version: '',

      require: '',
      api: 1,
      schema: {},
    },

};

paasify.main(plugin)
```

### Vars Plugins

Notes:

* There must be function that accept vars argument as object.

```
local plugin = {

  // Return default vars
  default_vars(vars)::
    {
        default_var1: 'part1',
        default_var2: 'part2',
    },

  // Provides processed vars
  override_vars(vars):: 
    {
        config: vars.default_var1 + '.' + vars.default_var2,
    },
};
```



### Transform Plugins

This exemple will add custom networks and services:
```
local plugin = {

  // Transform docker compose structure
  docker_override (vars, docker_file)::
    docker_file + {

      //["x-debug"]: vars,

      # Append stack network
      networks+: {
        "new_network": null,
      },

      # Append new service
      services+: {
        "new_service": null,
      },


};
```




