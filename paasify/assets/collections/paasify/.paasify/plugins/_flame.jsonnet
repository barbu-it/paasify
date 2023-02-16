local paasify = import 'paasify.libsonnet';

local plugin = {

  // Provides plugin metadata
  metadata: {
      local meta = self,

      name: "Flame integration",
      description: 'Integrate with Flame (https://github.com/pawelmalak/flame)',

      ident: "flame",

      author: "mrjk",
      email: '',
      license: '',
      version: '',

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
                  flame_name: {
                    description: 'Name of the application',
                    type: "string",
                  },
                  flame_svc: {
                    description: 'Name of the service to apply labels',
                    type: "string",
                  },
                  flame_type: {
                    description: 'Namespace of the application',
                    type: "string",
                    default: "application",
                  },
                  flame_url: {
                    description: 'Domain of the application',
                    type: "string",
                  },
                  flame_icon: {
                    description: 'Fully Qualified Domain Name of the application',
                    type: "string",
                    default: "docker",
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

  // Return default vars
  global_default(vars)::
    // Rules:
    // - Only static variables
    // - Referenced variables must be defined first in _paasify or in tag deps
    // - No self usage
    // - No variable composition here
    {
      flame_service: vars.app_service,
      flame_name: vars.app_name,
      flame_type: 'application',
      flame_icon: 'docker',

    },

  global_assemble(vars)::
    // Rules:
    // - Can ONLY reference vars defined in defaults or in core !
    // - No self usage, use local vars instead !
    // - ONLY variable composition here
    {
      flame_services: vars.app_service,
      flame_url: vars.app_prot + '://' + vars.app_fqdn,
    },

  // Automagically change the network name
  // This is due to default compose config behavior to add networks where none as been defined
  docker_transform (vars, docker_file)::
    local svc_keys = std.objectFields(docker_file.services);
    local pref_base = 'flame.';

    docker_file + {
      services+: {
        [svc_name]+: {
          // Update default labels for each containers
          labels+: {
            [pref_base + 'type']: vars.flame_type,
            [pref_base + 'name']: vars.flame_name,
            [pref_base + 'url']: vars.flame_url,
            [pref_base + 'icon']: vars.flame_icon,
          },
        } for svc_name in svc_keys
      },
    },

};

paasify.main(plugin)
