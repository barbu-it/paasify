local paasify = import 'paasify.libsonnet';

local plugin = {

  // Provides plugin metadata
  metadata: {
      local meta = self,

      name: "Paasify std lib",
      description: 'Paasify standard tag library',

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

        // docker_net_ident: vars.app_network, // default
        //docker_net_name: vars.app_network_name,
        
        # // vars.app_network_name
        //docker_net_ns: vars._prj_namespace,
        // docker_net_name: vars._stack_name + "_default",

        docker_net_external: true,

        //docker_svc_ident: vars.app_service,
        //docker_net_full_name: null,

    },

  // Override vars
  global_assemble(vars)::
    {
      // docker_net_full_name: vars._prj_namespace + vars.paasify_sep_net + vars.docker_net_name,
      docker_net_service_idents: std.split(vars.app_service, ','),
    },
 

    // docker_override
  docker_transform (vars, docker_file)::
    docker_file + {
        networks+: paasify.DockerNetDef(vars.app_network, 
          net_external=vars.docker_net_external, 
          net_name=vars.app_network_name),
        services+: {
            [vars.app_service]+: 
                paasify.DockerServiceNet(vars.app_network) for svc_name in vars.docker_net_service_idents
            },
    },
    

};

paasify.main(plugin)
