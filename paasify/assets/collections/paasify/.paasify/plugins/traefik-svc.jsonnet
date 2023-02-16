local paasify = import 'paasify.libsonnet';


# Internal functions
# -------------------------------------

# Base routing
local LabelsTraefik(svc, domain, entrypoints, port, group, rule=null, rule_extra=null, network=null, type='http', prio=null ) =
  local _rule_extra = if std.isString(rule_extra) then " " + rule_extra else "";
  local _rule = if std.isString(rule) then rule + _rule_extra else 'Host(`' + domain + '`)' + _rule_extra;
  std.prune({
    ["traefik.enable"]: "true",
    ["traefik.docker.network"]: network, # This break the routing for an unknown reason .. It can never find the network ...
    ["traefik.group"]: group,
    ["traefik." + type + ".routers." + svc + ".priority"]: prio,
    ["traefik." + type + ".routers." + svc + ".rule"]: _rule,
    ["traefik." + type + ".routers." + svc + ".entrypoints"]: entrypoints,
    ["traefik." + type + ".routers." + svc + ".service"]: svc,
    ["traefik." + type + ".services." + svc + ".loadbalancer.server.port"]: std.format("%s", port),
  });

# Middleware
local LabelsTraefikAuthelia(svc, authservice, type='http') =
  if std.isString(authservice) && std.length(authservice) > 0 then
    {
      ["traefik." + type + ".routers." + svc + ".middlewares"]: authservice + '@docker',
    } else {};

local indexes(arr) = std.range(0, std.length(arr) - 1);

# TLS management
local LabelsTraefikTls(svc, status=null, main=null, sans=null, certresolver=null, domains=[], type='http') =
  local router_name = "traefik." + type + ".routers." + svc;
  local domains_ = { [router_name + ".tls.domains[" + i + "].main"]: std.get(domains[i], "main") for i in indexes(domains) } ;

  local sans_ = {
      [router_name + ".tls.domains[" + i + "].sans"]: std.join(',', std.get(domains[i], "sans", []))
          for i in indexes(domains)
    } ;
  local status_ = if std.type(status) == "null" then std.isString(certresolver) else status;

  std.prune({
    [router_name + ".tls"]: std.toString(status_),
    [router_name + ".tls.certresolver"]: certresolver,
  } + domains_ + sans_
  );


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





# Networking
local TraefikSvcNetwork(current, id, name, priority=1000, aliases=[]) =
  local current_net = std.get(current, id, {});
  local netconfig = if std.isObject(current_net) then current_net else {};
  if std.isString(id) then
  current + {
    [id]: netconfig + std.prune({
      #name: std.get(current, id, null),
      priority: if priority > 0 then priority else null,
      aliases+: aliases,
    }),
  } else current;



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

    ident: 'traefik-svc',

    author: "mrjk",
    email: '',
    license: '',
    version: '',

    readme: '# This is My traefik REDAME !!!!      yeah title',

    // readme: |||
    //       line 1
    //       line 2
    //       line 3
    //     |||,

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
            traefik_svc_type: {
              description: 'Protocol type: http, tcp, udp',
              type: "string",
              default: "http",
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
            traefik_svc_priority: {
              description: 'The application rule priority, higher means processed first',
              type: "integer",
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
              description: 'Network to use to reach this app, no need to configure except you kwno what to do, you can"t use it if you want to expose this app to multiple traefik with dedicated interfaces. CAnnot be used multi time.',
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
              default: 0,
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
  //local svc_domain = vars.app_name + '.' + vars.app_domain;
    {

      # Default settings
      # --------------------------

      traefik_sep: '_', //vars.paasify_sep,

      # Name of the key in networks:{} in docker-compose,
      #traefik_net_key: 'traefik',
      traefik_net_key: 'default',
      traefik_net_aliases: null,

      # Name of the network
      traefik_net_name: vars.app_network_name,

      # Name of the key in services:{} in docker-compose,
      traefik_svc_key: vars.app_service,

      # Traefik service name (from traefik POV)
      traefik_svc_name:  vars.app_name,

      # Traefik port to map
      traefik_svc_port: vars.app_port,
      traefik_svc_type: 'http',

      traefik_ident : vars.app_namespace + self.traefik_sep + vars.app_name,
      traefik_net_priority: 0,

      # Traefik group
      traefik_svc_rule: null,
      traefik_svc_rule_extra: null,
      traefik_svc_fqdn: null,
      traefik_svc_group: null,
      traefik_svc_priority: null,

      traefik_svc_auth: null,
      traefik_svc_tls: null,
      traefik_svc_tls_domains: [],
      traefik_svc_certresolver: null,

    },


  // Return global assemble
  global_assemble(vars)::
    {
    traefik_svc_fqdn : std.prune([
      vars.traefik_svc_fqdn,
      vars.traefik_svc_name + '.' + vars.app_domain,
      vars.app_fqdn])[0],
    traefik_svc_entrypoints: if vars.traefik_svc_certresolver == null then "web" else "websecure",
    traefik_svc_group: vars.traefik_net_name,
    traefik_net_external: if vars.traefik_net_name == vars.app_network_name then false else true,
  },

  // docker_override
  docker_transform (vars, docker_file)::

    local _cur_svc_net = docker_file.services[vars.traefik_svc_key].networks;

    docker_file + {

      //["x-trafik-svc"]: vars,
      //["x-trafik-2"]:
      //      LabelsTraefikTls(
      //          _traefik_ident,
      //          vars.traefik_svc_tls),

      # Append stack network
      networks+: TraefikPrjNetwork(
          vars.traefik_net_key,
          vars.traefik_net_name,
          vars.traefik_net_external)
      ,
      #networks+:{
      #  [vars.traefik_net_key]+: TraefikPrjNetwork(
      #    vars.traefik_net_key,
      #    vars.traefik_net_name,
      #    vars.traefik_net_external)
      #},

      # Apply per services labels
      services+: {
        [vars.traefik_svc_key]+: {
          labels+:
            LabelsTraefik(
              vars.traefik_ident,
              vars.traefik_svc_fqdn,
              vars.traefik_svc_entrypoints,
              vars.traefik_svc_port,
              vars.traefik_svc_group,
              network=vars.traefik_net_name,
              rule=vars.traefik_svc_rule,
              prio=vars.traefik_svc_priority,
              rule_extra=vars.traefik_svc_rule_extra,
              type=vars.traefik_svc_type,
              )
            + LabelsTraefikAuthelia(
                vars.traefik_ident,
                vars.traefik_svc_auth,
                type=vars.traefik_svc_type)
            + LabelsTraefikTls(
                vars.traefik_ident,
                status=vars.traefik_svc_tls,
                domains=vars.traefik_svc_tls_domains,
                #main=vars.traefik_svc_tls_main,
                #sans=vars.traefik_svc_tls_sans,
                certresolver=vars.traefik_svc_certresolver,
                type=vars.traefik_svc_type,
                )
            #+ LabelsTraefikCertResolver(
            #    vars.traefik_ident,
            #    vars.traefik_svc_certresolver)
            ,

          // We need here to override the whole struct as some keys
          networks: TraefikSvcNetwork(
            docker_file.services[vars.traefik_svc_key].networks,
            vars.traefik_net_key,
            vars.traefik_net_name,
            priority=vars.traefik_net_priority,
            aliases=vars.traefik_net_aliases,
          ),
        },
      },

      //["x-debug-" + vars.tag_instance ]: std.prune(vars),
      // ["x-debug2"]: traefik_ident,
    },


};

paasify.main(plugin)
