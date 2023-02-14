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
  default_vars(vars)::
    local dir_prefix = vars.stack_path + '/';
    {

    //   # Default settings
    //   # --------------------------

    //   app_name: vars.stack_name,
    //   app_namespace: vars.prj_namespace,
    //   app_domain: std.get(vars, 'app_domain', default='localhost') ,
    //   #app_domain: std.prune(vars.app_domain, self.app_namespace, 'localdomain'),
    //   // app_name: vars.paasify_stack,
    //   // app_fqdn: vars.paasify_stack + '.' + vars.app_domain,
    //   app_fqdn: self.app_name + '.' + self.app_domain,

    //   # Compose structure
    //   # --------------------------
    //   app_service: vars.stack_service,

    //   app_network: vars.stack_network,
    //   app_network_external: false,
    //   app_network_name: vars.prj_namespace + vars.paasify_sep + vars.stack_name,

    //   # App user informations
    //   # --------------------------

    //   app_admin_login: 'admin',
    //   app_admin_email: 'admin@' + self.app_domain,
    //   app_admin_passwd: 'admin',

    //   app_user_login: 'user',
    //   app_user_email: 'user@' + self.app_domain,
    //   app_dir_root: dir_prefix,
    //   app_dir_build: dir_prefix + 'build', # Build dir
    //   net_backup: vars.prj_namespace + vars.paasify_sep + 'backup', # For backup network

        docker_net_ident: vars.app_network,
        docker_net_name: vars.app_network_name,
        #docker_net_name_full: vars.prj_namespace + self.traefik_sep + 'traefik', // vars.app_network_name
        docker_net_external: false,

        docker_svc_ident: vars.app_service,

    },



    // docker_override
  docker_override (in_vars, docker_file)::
    local vars = self.default_vars(in_vars) + std.prune(in_vars);

    #local service = std.get(conf, 'paasify_stack_service');
    local services = std.split(vars.app_service, ',');

    docker_file + {
        ["x-paasify-debug"]: {
            new_custom_service: null,
            },


        networks+: {
        [vars.docker_net_ident]: {
            name: vars.docker_net_name,
            external: vars.docker_net_external,
            }
        },
        services+: {
            [vars.docker_svc_ident]+:
                {
                    networks+: {
                        [vars.docker_net_ident]: null
                    }

                } for svc_name in services
            },
    },


};

paasify.main(plugin)
