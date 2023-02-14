local paasify = import 'paasify.libsonnet';


# Internal functions
# -------------------------------------

# Base routing
local LabelsTraefik(svc, domain, entrypoints, port, group) =
  {
    ["traefik.enable"]: "true",
    ["traefik.group"]: group,
    ["traefik.http.routers." + svc + ".rule"]: 'Host(`' + domain + '`)',
    ["traefik.http.routers." + svc + ".entrypoints"]: entrypoints,
    ["traefik.http.routers." + svc + ".service"]: svc,
    ["traefik.http.services." + svc + ".loadbalancer.server.port"]: std.format("%s", port),
  };

# Middleware
local LabelsTraefikAuthelia(svc, authservice) =
  if std.isString(authservice) && std.length(authservice) > 0 then
    {
      ["traefik.http.routers." + svc + ".middlewares"]: authservice + '@docker',
    } else {};

# TLS management
local LabelsTraefikTls(svc, status) =
  if status == true then
  {
    ["traefik.http.routers." + svc + ".tls"]: "true",
  } else {};

local LabelsTraefikCertResolver(svc, name) =
  if std.isString(name) && std.length(name) > 0 then
  LabelsTraefikTls(svc, true) + {
    ["traefik.http.routers." + svc + ".tls.certresolver"]: name,
  } else {};

# Networking
local TraefikSvcNetwork(id, name) =
  if std.isString(id) then
  {
    [id]: null,
  } else {};

local TraefikPrjNetwork(id, name, external) =
  if std.isString(id) then
  {
    [id]+: {
      name: name
    },
  } +
  if external == true then
  {
    [id]+: {
      external: true,
    },
  } else {}
  else {};



# Plugin API
# -------------------------------------



local plugin = {

  // Provides plugin metadata
  metadata: {
    local meta = self,
    name: "Traefik Service",
    description: 'Bind service to traefik instance',

    author: "mrjk",
    email: '',
    license: '',
    version: '',

    require: '',
    api: 1,
    jsonschema: {
      // $schema: 'http://json-schema.org/draft-07/schema#',
      type: 'object',
      title: meta.name,
      description: 'Create a traefik service for a given service',
      examples: [
        {
          stacks: [
            {
              app: "my_app_name",
              vars: [
                {
                  traefik_svc_entrypoints: "default-http,default-https",
                },
                {
                  traefik_svc_port: 8080,
                },
                {
                  traefik_svc_group: "trafik_prod",
                },
              ],
              tags: [
                "traefik-svc"
              ],
            },
          ],

        },
      ],
      properties: {
        variables: {
          type: 'object',
          properties: {

            // Traefik service settings
            traefik_svc_ident: {
              description: 'Name of the key in services:{} as in docker-compose',
              type: "string",
              default: "$app_service",
            },
            traefik_svc_name: {
              description: 'Name of the service (dynamic)',
              type: "string",
              default: "$app_service",
            },
            traefik_svc_domain: {
              description: 'Fully Qualified Domain Name of the application (dynamic)',
              default: "$traefik_svc_name.$vars.app_domain",
              type: "string",
            },

            traefik_svc_entrypoints: {
              description: 'Traefik entrypoints of the application',
              type: "string",
              default: "default-http",
            },
            traefik_svc_port: {
              description: 'Listening port of the application',
              type: "string",
              default: "80",
            },
            traefik_svc_group: {
              description: 'Traefik group name to assign this container',
              type: "string",
              default: "$prj_namespace-traefik",
            },

            traefik_svc_auth: {
              description: 'Service Authentication to use',
              type: "string",
              default: null,
            },
            traefik_svc_tls: {
              description: 'The application is availalble on TLS',
              type: "boolean",
              default: false,
            },
            traefik_svc_certresolver: {
              description: 'Certresolver of the application',
              type: "string",
              default: null,
            },


            // Network settings
            traefik_net_ident: {
              description: 'Name of the key in networks:{} as in docker-compose',
              type: "string",
              default: "$app_network",
            },
            traefik_net_name: {
              description: 'Name of the docker network to use',
              type: "string",
              default: "$prj_namespace-traefik",
            },
            traefik_net_external: {
              description: 'Determine if network is external or not',
              type: "string",
              default: true,
            },


            // Other settings
            traefik_sep: {
              description: 'String to separe names',
              default: "-",
              type: "string",
            },
          },

        },
        // variables: {
        //     type: 'null',
        // },
        transform: {
            type: 'object',
            description: 'Add correct traefik labels for a given service. Also append traefik network if not already present.',
        },
      },

    }
  },

  // Return global vars
  default_vars(vars)::
  //local svc_domain = vars.app_name + '.' + vars.app_domain;
    {

      # Default settings
      # --------------------------

      // app_name: vars.stack_name,
      // app_domain: vars.prj_namespace,
      // // app_name: vars.paasify_stack,
      // // app_fqdn: vars.paasify_stack + '.' + vars.app_domain,


      // # Compose structure
      // # --------------------------
      // app_service: vars.stack_service,

      // app_network: vars.stack_network,
      // app_network_external: false,
      // app_network_name: vars.prj_namespace + vars.paasify_sep + vars.stack_name,

      # App exposition
      # --------------------------
      # Required by API

      traefik_sep: vars.paasify_sep,


      # Name of the key in networks:{} in docker-compose,
      traefik_net_ident: vars.app_network, // vars.app_network

      # Name of the network
      traefik_net_name: vars.prj_namespace + self.traefik_sep + 'traefik', // vars.app_network_name
      traefik_net_external: true,

      # Name of the key in services:{} in docker-compose,
      traefik_svc_ident: vars.app_service , // vars.app_service

      # Traefik service name (from traefik POV)
      traefik_svc_name:  vars.app_service,
      traefik_svc_name_full: null,

      # Traefik port to map
      traefik_svc_port: vars.app_port , // vars.app_port

      # Traefik group
      traefik_svc_group: vars.prj_namespace + self.traefik_sep + 'traefik',

      traefik_svc_domain: null,
      traefik_svc_entrypoints: "default-http",


      traefik_svc_auth: null,
      traefik_svc_tls: null,
      traefik_svc_certresolver: null,

      #traefik_svc_name: vars.prj_namespace + self.traefik_sep + vars.app_service,
      # traefik_svc_name_full: vars.prj_namespace + self.traefik_sep + self.traefik_svc_name,

      // traefik_svc_name: std.prune(default_svc_name)[0],
      // traefik_svc_domain: std.prune(default_svc_domain)[0],
      #traefik_svc_domain: self.traefik_svc_name + '.' + vars.app_domain,

      // traefik_svc_entrypoints: std.prune(default_svc_entrypoints)[0],
      // traefik_svc_auth: std.get(conf, 'traefik_svc_auth', default=null),
      // traefik_svc_tls: std.get(conf, 'traefik_svc_tls', default=false),
      // traefik_svc_certresolver: std.get(conf, 'traefik_svc_certresolver', default=null),

    },

  // override_vars(vars)::

  //   {
  //     //app_fqdn: vars.app_name + '.' + vars.app_domain,
  //     // app_name: vars.paasify_stack,
  //     // app_fqdn: vars.paasify_stack + '.' + vars.app_domain,

  //   },

    // docker_override
  docker_override (in_vars, docker_file)::
    local vars = self.default_vars(in_vars) + std.prune(in_vars);

    # Determine full name to apply config
    local _traefik_svc_name_full = std.prune([
      vars.traefik_svc_name_full,
      vars.prj_namespace + vars.traefik_sep + vars.traefik_svc_name])[0];
    local _traefik_svc_domain = std.prune([
      vars.traefik_svc_domain,
      vars.traefik_svc_name + '.' + vars.app_domain])[0];


    docker_file + {

      //["x-trafik-svc"]: vars,

      # Append stack network
      networks+: TraefikPrjNetwork(
        vars.traefik_net_ident,
        vars.traefik_net_name,
        vars.traefik_net_external),

      # Apply per services labels
      services+: {
        [vars.traefik_svc_ident]+: {
          labels+:
            LabelsTraefik(
              _traefik_svc_name_full,
              _traefik_svc_domain,
              vars.traefik_svc_entrypoints,
              vars.traefik_svc_port,
              vars.traefik_svc_group)
            + LabelsTraefikAuthelia(
                _traefik_svc_name_full,
                vars.traefik_svc_auth)
            + LabelsTraefikTls(
                _traefik_svc_name_full,
                vars.traefik_svc_tls)
            + LabelsTraefikCertResolver(
                _traefik_svc_name_full,
                vars.traefik_svc_certresolver)
            ,
          networks+: TraefikSvcNetwork(
            vars.traefik_net_ident,
            vars.traefik_network_name),
        },
      },

      // ["x-debug"]: std.prune(vars),
      // ["x-debug2"]: traefik_svc_name_full,
    },


};

paasify.main(plugin)
