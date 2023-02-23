local paasify = import 'paasify.libsonnet';

local plugin = {

  // Provides plugin metadata
  metadata: {
      local meta = self,

      name: "Docker debug Container",
      description: 'Attach container to project',
      ident: 'debug',

      author: "mrjk",
      email: '',
      license: '',
      version: '',

      depends: ['_paasify'],

      require: '',
      api: 1,
      jsonschema: {
          ['$schema']: 'http://json-schema.org/draft-07/schema#',
          type: 'object',
          title: meta.name,
          description: 'Provide default common variables',
      },
    },

  // Return global vars
  global_default(vars)::
    {

        // Determine wich var we want to be dumped
        _debug_dump_vars_prefixes: paasify.values(vars, 'debug_dump_vars_prefixes' ,['debug']),

        // Can define constants
        debug_dump_vars: true,

        // Can define defaults, from previous plugins dependencies
        debug_domain: vars.app_domain,

        // Can define defaults, from optional dependencies
        // You MUST use the std.get with a default value in this case
        #debug_name: std.get(vars, 'traefik_svc_name', 'NO-NAME'),
        debug_name: paasify.values(vars, ['traefik_svc_name', 'traefik_svc_ident'], 'NO-NAME'),

    },

  // Override vars
  global_assemble(vars):: {

        // Can create new vars by manipulating other vars
        debug_fqdn: vars.debug_name + '.' + vars.debug_domain,

    },


  // docker_override
  docker_transform (vars, docker_file)::

    // We can use paasify.FilterVarsPrefix to fetch only our plugins vars
    #local tag_vars = paasify.FilterVarsPrefix(vars, "debug") + paasify.FilterVarsPrefix(vars, "tag");
    local tag_vars = paasify.FilterVarsPrefix(vars, vars._debug_dump_vars_prefixes);

    // Then prepare the output
    local dump_vars = if vars.debug_dump_vars then { ["x-test" + vars.tag_suffix + "-vars" ]: tag_vars } else {};

    // Finally we process the docker-compose
    docker_file + dump_vars,
};

paasify.main(plugin)
