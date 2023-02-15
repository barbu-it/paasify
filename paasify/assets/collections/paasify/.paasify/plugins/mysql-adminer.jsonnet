local paasify = import 'paasify.libsonnet';
local _p = import '_p.libsonnet';


local add_traefik(vars, df)=
  local plugin_overrides = {
    traefik_ident: vars.app_slug + "_adminer",
    traefik_svc_key: vars.adminer_service,
    traefik_svc_name: vars.app_name + "-adminer",
    traefik_svc_port: "9000",
  };
  local plugin_lib = import 'traefik-svc.jsonnet';
  paasify.call_other(plugin_lib, df, vars, plugin_overrides);

local add_homepage(vars, df)=
  local plugin_overrides = {
    homepage_service: vars.adminer_service,
    homepage_icon: "adminer",
    homepage_href: vars.app_prot + '://' + vars.app_name + "-adminer." + vars.app_domain,

    homepage_name: "Adminer",
    homepage_group: 'Utils',
    homepage_desc: "Adminer is a full-featured database management tool written in PHP",
  };
  local plugin_lib = import 'homepage.jsonnet';
  paasify.call_other(plugin_lib, df, vars, plugin_overrides);


local plugin = {

  // Provides plugin metadata
  metadata: {
      local meta = self,

      name: "Provide amdiner web UI to manage MySQL",
      description: '',
      ident: 'mysql-adminer', # MUST ALWAYS MATCH THE FILENAME !

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
      # Adminer configuration
      adminer_image: "wodby/adminer",
      adminer_service: "adminer",

      # Extra integration
      adminer_traefik: if std.member(vars.app_tags, ':traefik-svc:') then true else false,
      adminer_homepage: if std.member(vars.app_tags, ':homepage:') then true else false,

      # Default external settings
      app_db_type: 'mysql',
      app_db_host: 'db',
      app_db_name: null,
    },

  global_assemble(vars)::
    {},

  // Automagically change the network name
  // This is due to default compose config behavior to add networks where none as been defined
  docker_transform (vars, docker_file)::
    local df = {
      services+: {
        [vars.adminer_service]: {
          image: vars.adminer_image,
          networks: {
            db: {}
          },
          environment: {
            ADMINER_DEFAULT_DB_DRIVER: _p.first_valid([vars.app_db_type, 'mysql']),
            ADMINER_DEFAULT_DB_HOST: _p.first_valid([vars.app_db_host, 'db']),
            ADMINER_DEFAULT_DB_NAME: _p.first_valid([vars.app_db_name, 'app']),
          },
        },
      }
    };

    // Final result
    local traefik_extra = if vars.adminer_traefik then add_traefik(vars, df) else {};
    local homepage_extra = if vars.adminer_homepage then add_homepage(vars, df) else {};
    docker_file + traefik_extra, #  + homepage_extra,

    # Broken, WIP ...
    # local proc1 = docker_file + homepage_extra;
    # local proc2 = proc1 + traefik_extra;

    # local proc1 = docker_file + homepage_extra;
    # local proc2 = docker_file + traefik_extra;
    # local labels =
    #     proc1.services[vars.adminer_service].labels +
    #     proc2.services[vars.adminer_service].labels ;
    # local over = { services+: { [vars.adminer_service]+: { labels: labels }} };
    # docker_file + over + df ,
    # #proc1 + proc2 + over,
    # #docker_file + homepage_extra + traefik_extra,
};

paasify.main(plugin)
