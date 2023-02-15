local paasify = import 'paasify.libsonnet';

local plugin = {

  // Provides plugin metadata
  metadata: {
      local meta = self,

      name: "Docker debug Container",
      description: 'Attach container to project',
      ident: 'example',

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
        _example_dump_vars_prefixes: paasify.values(vars, 'example_dump_vars_prefixes' ,['example']),

        // Can define constants
        example_dump_vars: true,

        // Can define defaults, from previous plugins dependencies
        example_domain: vars.app_domain,

        // Can define defaults, from optional dependencies
        // You MUST use the std.get with a default value in this case
        #example_name: std.get(vars, 'traefik_svc_name', 'NO-NAME'),
        example_name: paasify.values(vars, ['traefik_svc_name', 'traefik_svc_ident'], 'NO-NAME'),

    },

  // Override vars
  global_assemble(vars):: {

        // Can create new vars by manipulating other vars
        example_fqdn: vars.example_name + '.' + vars.example_domain,

    },


  // docker_override
  docker_transform (vars, docker_file)::

    // We can use paasify.FilterVarsPrefix to fetch only our plugins vars
    #local tag_vars = paasify.FilterVarsPrefix(vars, "example") + paasify.FilterVarsPrefix(vars, "tag");
    local tag_vars = paasify.FilterVarsPrefix(vars, vars._example_dump_vars_prefixes);

    // Then prepare the output
    local dump_vars = if vars.example_dump_vars then { ["x-test" + vars.tag_suffix + "-vars" ]: tag_vars } else {};

    // Finally we process the docker-compose
    docker_file + dump_vars,
};

paasify.main(plugin)
