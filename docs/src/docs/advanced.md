# Advanced


## Why a tag can't be both jsonnet and docker-compose

Actually, this would be redundant as a jsonnet can generate and even modify
existing docker-compose files, as it's a full featured json language.


## Stack assemble workflow

How is assembled a stack?

* Read variables:
    * Generate default stack vars (paasify)
    * Read all tags default_variables (<tags>.jsonnet)
    * Read upstream app vars (vars.yml)
    * Read local app vars (vars.yml)
    * Read global conf variables (conf.vars)
    * Read stack variables (stack.vars)
    * Read all tags override_variables (<tags>.jsonnet)
* Get docker-files:
    * Find all docker-files matching tags in local app (docker-compose.<tags>.yaml)
    * Fallback on found all docker-files matching tags in upstream app (docker-compose.<tags>.yaml)
* Build docker-compose file:
    * Assemble all found docker-files with all vars
* On the `docker-compose config` output
    * Read all tags with jsonnet and apply transform hook (<tags>.jsonnet)
        * All vars defined in a tag config are local
* Write final docker-compose:
    * Write into: <stack_dir>/docker-compose.run.yml


Related piece of code: `paasify.stacks2.PaasifyStack.assemble()`

::: paasify.stacks2.PaasifyStack.assemble
    options:
      show_root_heading: False
      show_source: true
      heading_level: 4
      # show_category_heading: true


