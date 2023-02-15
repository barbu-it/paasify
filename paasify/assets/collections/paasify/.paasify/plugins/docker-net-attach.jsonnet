local paasify = import 'paasify.libsonnet';

local plugin = {

  // Provides plugin metadata
  metadata: {
      local meta = self,

      name: "Docker Net Attach",
      description: 'Attach network to container',
      ident: 'docker-net-attach',

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
          //default: conf_default,
          properties: {
            variables: {
                type: 'object',
                properties: {
                  app_name: {
                    description: 'Name of the application',
                    type: "string",
                  },
                  app_namespace: {
                    description: 'Namespace of the application',
                    type: "string",
                  },
                  app_domain: {
                    description: 'Domain of the application',
                    type: "string",
                  },
                  app_fqdn: {
                    description: 'Fully Qualified Domain Name of the application',
                    type: "string",
                  },
                },
            },
            transform_variables: {
                type: 'null',
            },
            transform: {
                type: 'null',
                description: 'Do nothing',
            },
          },
      },
    },

  // Return global vars
  global_default(vars)::
    {

        docker_net_key: 'default',
        # docker_net_name: null,
        docker_net_name: vars.app_network_name,

        docker_net_external: true,
        docker_net_ipv4: null,
        docker_net_aliases: null,
        docker_net_priority: 0,

    },

  // Override vars
  #global_assemble(vars)::
  #  {
  #    // docker_net_full_name: vars._prj_namespace + vars.paasify_sep_net + vars.docker_net_name,
  #    docker_net_service_idents: std.split(vars.app_service, ','),
  #  },


    // docker_override
  docker_transform (vars, docker_file)::
    assert std.isString(vars.docker_net_name) : 'You must define the network name to use with: docker_net_name' ;
    docker_file + {
        networks+: paasify.DockerNetDef(
          vars.docker_net_key,
          net_external=vars.docker_net_external,
          net_name=vars.docker_net_name),
        services+: {
            [vars.app_service]+: paasify.DockerServiceNet(
              vars.docker_net_key,
              net_ipv4=vars.docker_net_ipv4,
              net_aliases=vars.docker_net_aliases,
              priority=vars.docker_net_priority,
              ),
            },
    },


};

paasify.main(plugin)
