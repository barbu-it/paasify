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

        docker_net_ident: vars.app_network,
        # docker_net_name: vars.app_network_name,
        #docker_net_name_full: vars.prj_namespace + self.traefik_sep + 'traefik', // vars.app_network_name
        docker_net_ns: vars.prj_namespace,
        docker_net_external: false,

        docker_svc_ident: vars.app_service,
        docker_net_full_name: null,
        docker_net_aliases: [],

    },



    // docker_override
  docker_override (in_vars, docker_file)::
    local vars = self.default_vars(in_vars) + std.prune(in_vars);

    #local service = std.get(conf, 'paasify_stack_service');
    local services = std.split(vars.app_service, ',');
    local _net_name = std.prune([
      vars.docker_net_full_name,
      vars.docker_net_ns + vars.paasify_sep + vars.docker_net_name ])[0];
    local _net_external = std.prune([
      vars.docker_net_full_name,
      vars.docker_net_ns + vars.sep + vars.docker_net_name ])[0];

    docker_file + {
        networks+: paasify.DockerNetDef(vars.docker_net_ident, net_external=false, net_name=_net_name),
        services+: {
            [vars.docker_svc_ident]+:
                paasify.DockerServiceNet(vars.docker_net_ident, net_aliases=vars.docker_net_aliases) for svc_name in services
            },
    },


};

paasify.main(plugin)
