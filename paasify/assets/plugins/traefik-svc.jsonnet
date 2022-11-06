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
local TraefikSvcNetwork(id, name, current=null) =
  if std.isString(id) then
  {
    [id]: std.get(current, id, null),
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
            traefik_svc_key: {
              description: 'Traefik key name of the service, must NOT contains dot (dynamic)',
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
              default: "$app_namespace-traefik",
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
              default: "$app_namespace-traefik",
            },
            traefik_net_external: {
              description: 'Determine if network is external or not',
              type: "string",
              default: true,
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
      traefik_net_ident: 'traefik', 

      # Name of the network
      traefik_net_name: vars.net_proxy_web,
      traefik_net_external: true,

      # Name of the key in services:{} in docker-compose, 
      traefik_svc_ident: vars.app_service,

      # Traefik service name (from traefik POV)
      traefik_svc_key: null,
      traefik_svc_name:  vars.app_name,
      traefik_svc_name_full: null,

      # Traefik port to map
      traefik_svc_port: vars.app_port,
      
      # Traefik group
      traefik_svc_group: self.traefik_net_name,

      traefik_svc_fqdn: null,
      traefik_svc_entrypoints: "default-http",

      traefik_svc_auth: null,
      traefik_svc_tls: null,
      traefik_svc_certresolver: null,

    },

  // docker_override
  docker_transform (vars, docker_file)::

    # Determine full name to apply config
    local _traefik_svc_name_full = std.prune([
      vars.traefik_svc_key,
      vars.app_namespace + vars.traefik_sep + vars.traefik_svc_name])[0];
    local _traefik_svc_fqdn = std.prune([
      vars.traefik_svc_fqdn, 
      vars.app_fqdn, 
      vars.traefik_svc_name + '.' + vars.app_domain])[0];
      
    local _cur_svc_net = docker_file.services[vars.traefik_svc_ident].networks;

    docker_file + {

      //["x-trafik-svc"]: vars,
      //["x-trafik-2"]:
      //      LabelsTraefikTls(
      //          _traefik_svc_name_full,
      //          vars.traefik_svc_tls),

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
              _traefik_svc_fqdn,
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
            vars.traefik_network_name,
            current=_cur_svc_net
          ),
        },
      },

      // ["x-debug"]: std.prune(vars),
      // ["x-debug2"]: traefik_svc_name_full,
    },
    

};

paasify.main(plugin)
