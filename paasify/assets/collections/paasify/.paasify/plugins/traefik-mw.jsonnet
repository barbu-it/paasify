local paasify = import 'paasify.libsonnet';


# Internal functions
# -------------------------------------

# Base routing
local LabelsTraefikMiddleware(name, middleware, conf={}, protocol='http') =
  std.prune({
    ["traefik." + protocol + ".middlewares." + name + "." + middleware + "." + key]: conf[key],
      for key in std.objectFields(conf)
  });

# Middleware
local LabelsTraefikAuthelia(svc, authservice) =
  if std.isString(authservice) && std.length(authservice) > 0 then
    {
      ["traefik.http.routers." + svc + ".middlewares"]: authservice + '@docker',
    } else {};


# local indexes(arr) = std.range(0, std.length(arr) - 1);

## TLS management
#local LabelsTraefikTls(svc, status=null, main=null, sans=null, certresolver=null, domains=[]) =
#  local domains_ = { ["traefik.http.routers." + svc + ".tls.domains[" + i + "].main"]: std.get(domains[i], "main") for i in indexes(domains) } ;
#
#  local sans_ = {
#      ["traefik.http.routers." + svc + ".tls.domains[" + i + "].sans"]: std.join(',', std.get(domains[i], "sans", []))
#          for i in indexes(domains)
#    } ;
#  local status_ = if std.type(status) == "null" then std.isString(certresolver) else status;
#
#  std.prune({
#    ["traefik.http.routers." + svc + ".tls"]: std.toString(status_),
#    ["traefik.http.routers." + svc + ".tls.certresolver"]: certresolver,
#  } + domains_ + sans_
#  );
#
#
##### OLD
#local LabelsTraefikTls1(svc, status=null, main=null, sans=null, certresolver=null) =
#  if status == true then
#  {
#    ["traefik.http.routers." + svc + ".tls"]: "true",
#  } else {};
#
#local LabelsTraefikCertResolver(svc, name) =
#  if std.isString(name) && std.length(name) > 0 then
#  LabelsTraefikTls(svc, true) + {
#    ["traefik.http.routers." + svc + ".tls.certresolver"]: name,
#  } else {};





## Networking
#local TraefikSvcNetwork_old(id, name, priority=1000, current=null) =
#  if std.isString(id) then
#  {
#    [id]+:
#    {
#      #name: std.get(current, id, null),
#      priority: priority,
#    },
#  } else {};
#
#
#local TraefikSvcNetwork(current, id, name, priority=1000, aliases=[]) =
#  local current_net = std.get(current, id, {});
#  local netconfig = if std.isObject(current_net) then current_net else {};
#  if std.isString(id) then
#  current + {
#    [id]: netconfig + std.prune({
#      #name: std.get(current, id, null),
#      priority: priority,
#      aliases+: aliases,
#    }),
#  } else current;
#
#
#
#local TraefikPrjNetwork(id, name, external) =
#  if std.isString(id) then
#  {
#    [id]+: {
#      name: name
#    },
#  } +
#  if external == true then
#  {
#    [id]+: {
#      external: true,
#    },
#  } else {}
#  else {};



# Plugin API
# -------------------------------------



local plugin = {

  // Provides plugin metadata
  metadata: {
    local meta = self,
    name: "Traefik Middleware",
    description: 'Create traefik middleware',

    ident: 'traefik-mw',

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
                  traefik_svc_entrypoints: "web,websecure",
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

            # TODO: To be renamed to  traefik_svc_ident
            traefik_ident: {
              description: 'Traefik key name of the service, must NOT contains dot (dynamic)',
              type: "string",
              default: "${app_ns}_${app_name}",
            },

            // Traefik service settings, should be proivided in app for this one
            traefik_svc_key: {
              description: 'Name of the key in services:{} as in docker-compose',
              type: "string",
              default: "$app_service",
            },

            traefik_svc_name: {
              description: 'First part of the FQDN (dynamic)',
              type: "string",
              default: "$app_service",
            },

            traefik_svc_fqdn: {
              description: 'Fully Qualified Domain Name of the application (dynamic)',
              default: "$traefik_svc_name.$vars.app_domain",
              type: "string",
            },

            traefik_svc_entrypoints: {
              description: 'Traefik entrypoints of the application',
              type: "string",
              default: "web",
            },
            traefik_svc_port: {
              description: 'Listening port of the application',
              type: "string",
              default: "80",
            },
            traefik_svc_group: {
              description: 'Traefik group name to assign this container, add more separated with comma',
              type: "string",
              default: "$app_namespace-traefik",
            },
            traefik_svc_certresolver: {
              description: 'Certresolver of the application',
              type: "string",
              default: null,
            },
            traefik_svc_net: {
              description: 'Network to use to reach this app, no need to configure except you kwno what to do, you can"t use it if you want to expose this app to multiple traefik with dedicated interfaces. CAnnot be used multi time.',
              type: "string",
              default: null,
            },
            traefik_svc_rule: {
              description: 'Rule to match this app',
              type: "string",
              default: null,
            },
            traefik_svc_rule_extra: {
              description: 'Rule to append to the default rule',
              type: "string",
              default: null,
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

            traefik_svc_tls_domains: {
              description: 'The domains to support',
              type: "array",
              default: [],
            },
            #traefik_svc_tls_main: {
            #  description: 'The main domain to request certificate',
            #  type: "string",
            #  default: null,
            #},
            #traefik_svc_tls_sans: {
            #  description: 'The sans domains, separated by coma',
            #  type: "string",
            #  default: null,
            #},


            // Network settings
            traefik_net_key: {
              description: 'Name of the key in networks:{} as in docker-compose',
              type: "string",
              default: "$app_network",
            },
            traefik_net_name: {
              description: 'Name of the docker network to use',
              type: "string",
              default: "$app_namespace-traefik",
            },
            traefik_net_external: {
              description: 'Determine if network is external or not',
              type: "string",
              default: true,
            },
            traefik_net_priority: {
              description: 'Determine traefik network priority',
              type: "number",
              default: 1000,
            },


            // Other settings
            traefik_sep: {
              description: 'String to separe names',
              default: "_",
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
  global_default(vars)::
    {
      # Name of the key in services:{} in docker-compose,
      traefik_svc_key: vars.app_service,
      traefik_mw_name: null,
      traefik_mw_type: null,
      traefik_mw_conf: {},
      traefik_mw_prot: 'http',
    },

  // Return global assemble
  global_assemble(vars)::
    {},

  // docker_override
  docker_transform (vars, docker_file)::
    assert std.isString(vars.traefik_mw_name): "The variable 'traefik_mw_name' must be set to middleware name";
    assert std.isString(vars.traefik_mw_type): "The variable 'traefik_mw_type' must be set to middleware type";

    docker_file + {
      services+: {
        [vars.traefik_svc_key]+: {
          labels+:
            LabelsTraefikMiddleware(
                vars.traefik_mw_name,
                vars.traefik_mw_type,
                conf=vars.traefik_mw_conf,
                protocol=vars.traefik_mw_prot,
            ),
        },
      },

      // ["x-debug"]: std.prune(vars),
      // ["x-debug2"]: traefik_ident,
    },


};

paasify.main(plugin)
