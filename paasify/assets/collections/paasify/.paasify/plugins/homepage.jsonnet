local paasify = import 'paasify.libsonnet';


local plugin = {

  // Provides plugin metadata
  metadata: {
      local meta = self,

      name: "Homepage integration",
      description: 'Integrate with Homepage (https://gethomepage.dev)',

      ident : 'homepage',

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
                  homepage_name: {
                    description: 'Name of the application',
                    type: "string",
                  },
                  homepage_svc: {
                    description: 'Name of the service to apply labels',
                    type: "string",
                  },
                  homepage_group: {
                    description: 'Group of the application',
                    type: "string",
                    default: "application",
                  },
                  homepage_href: {
                    description: 'URL of the app',
                    type: "string",
                  },
                  homepage_desc: {
                    description: 'Application description',
                    type: "string",
                  },
                  homepage_icon: {
                    description: 'Icon file, see: https://github.com/walkxcode/dashboard-icons',
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

  // Return default vars
  global_default(vars)::
    // Rules:
    // - Only static variables
    // - Referenced variables must be defined first in _paasify or in tag deps
    // - No self usage
    // - No variable composition here
    {
      homepage_service: vars.app_service,
      homepage_name: vars.app_name,
      homepage_group: 'Docker',
      // See: https://github.com/walkxcode/dashboard-icons
      homepage_icon: vars.app_product,
      homepage_desc: vars.app_description,

    },

  global_assemble(vars)::
    // Rules:
    // - Can ONLY reference vars defined in defaults or in core !
    // - No self usage, use local vars instead !
    // - ONLY variable composition here
    {
      homepage_services: vars.app_service,
      homepage_href: vars.app_prot + '://' + vars.app_fqdn,
    },

  // Automagically change the network name
  // This is due to default compose config behavior to add networks where none as been defined
  docker_transform (vars, docker_file)::
    local svc_keys = std.objectFields(docker_file.services);
    local pref_base = 'homepage.';

    docker_file + {
      services+: {
        [vars.homepage_service]+: {
          // Update default labels for each containers
          labels+: {
            [pref_base + 'group']: vars.homepage_group,
            [pref_base + 'name']: vars.homepage_name,
            [pref_base + 'href']: vars.homepage_href,
            [pref_base + 'icon']: vars.homepage_icon,
            [pref_base + 'description']: vars.homepage_desc,
          },
        },
      },
    },

};

paasify.main(plugin)
