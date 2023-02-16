local paasify = import 'paasify.libsonnet';

local plugin = {

  // Provides plugin metadata
  metadata: {
      local meta = self,

      name: "Paasify std lib",
      description: 'Paasify standard tag library',
      ident: '_paasify',

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

  // Return default vars
  global_default(vars)::
    // Rules:
    // - Only static variables
    // - Referenced variables must be defined first in _paasify or in tag deps
    // - No self usage
    // - No variable composition here
    local paasify_extra_vars = if paasify.values(vars, ['paasify_extra_vars'], true) then true else false ;
    {

      is_swarm: false,
      swarm_nodes: 1,
      paasify_extra_vars: paasify_extra_vars,

      # Generic (Allow user overrides)
      # --------------------------
      app_product_path: std.get(vars, 'app_product_path', default=vars._stack_app_path) ,
      app_product_dir: std.get(vars, 'app_product_dir', default=vars._stack_app_dir) ,
      app_tags: std.get(vars, 'app_tags', default=vars._prj_stack_tags) ,
      app_name: std.get(vars, 'app_name', default=vars._stack_name) ,
      app_product: std.prune([std.get(vars, 'app_product', default=vars._stack_app_name), self.app_name ])[0],
      app_alias: std.get(vars, 'app_alias', default=self.app_name) ,
      app_namespace: std.get(vars, 'app_namespace', default=vars._prj_ns) , # Deprecate this ?
      app_ns: std.get(vars, 'app_namespace', default=vars._prj_ns) ,  # Shorter alias !
      app_domain: std.get(vars, 'app_domain', default=vars._prj_domain + '.localhost') ,
      app_adm_name: self.app_name + "-adm",
      app_slug: self.app_ns + '_' + self.app_name,

      app_instance: if self.app_product == self.app_name then self.app_product else self.app_product + '-' + self.app_name,

      # Networking
      # --------------------------
      app_service: std.get(vars, 'app_service', default=vars._stack_service) ,

      app_network_name_prefix: self.app_namespace,
      // Considered as a constant as it mimic/guess docker-compose network naming pattern
      app_network_name_sufix: self.app_name + "_default",
      app_network: std.get(vars, 'app_network', default=vars._stack_network) ,
      app_network_external: null, # can be true, false or null
      app_network_key: "default",


      # App exposition
      # --------------------------
      app_expose: false,

      # IP to expose service
      app_expose_ip: '0.0.0.0',
      # Port to expose service
      app_expose_port: null,
      # Protocol to expose, tcp or UDP
      app_expose_prot: null,


      app_port: '80',
      app_prot: 'http', # http,tcp,udp

      # Default app log level
      app_log_level: 'INFO',
      # Should the access log to be enabled ?
      app_log_access: false,


      # App configuration
      # --------------------------

      # Possible choices: always, no, unless-stopped, on-failure
      # See: https://docs.docker.com/compose/compose-file/compose-file-v3/#restart
      # TODO: Rename this app_restart_policy -> app_restart_default_policy
      app_restart_policy: 'unless-stopped', # default, does not override

      app_puid: '1000',
      app_pgid: '1000',

      app_lang: 'en_US',
      app_tz: 'UTC',
      app_tz_var: 'TZ',
      app_tz_mount: false,
      app_tz_mounts: '/etc/timezone:/etc/timezone:ro,/etc/localtime:/etc/localtime:ro',

      app_debug: 'false',

    } + if paasify_extra_vars then {

      # Orginaisation
      # --------------------------
      app_org_name: 'MyOrg',

      # App user informations
      # --------------------------

      app_setup: false, # Used to trigger initial setup
      app_locale: 'en-US',

      # User accounts
      app_admin_user: 'admin',
      app_admin_pass: null,
      app_default_user: 'user',
      app_default_pass: null,

      app_readonly_user: 'readonly',
      app_readonly_pass: null,


      # App Backend info
      # --------------------------
      app_db_type: null, # Can be mysql, mariadb, postgres ... not normalized

      app_db_host: 'db',
      app_db_port: '3306',
      # app_db_name: self.app_instance,  # SHould we change that for app_name ? If user changes, it break everything tho ... Yep, too boring ... we ^Z
      app_db_name: self.app_product,
      app_db_user: self.app_product,
      app_db_pass: null,

      app_db_admin_user: 'root',
      app_db_admin_pass: null,

      # LDAP pattern
      # ---------------------------
      ldap_domain: self.app_domain,
      ldap_org: self.app_domain,
      ldap_host: 'ldap',

      ldap_tls: false,
      ldap_port: 386,
      ldap_prot: 'ldap',

      # ldap_tls: true,
      # ldap_port: 636,
      # ldap_prot: 'ldaps',

    } else {} ,

  global_assemble(vars)::
    // Rules:
    // - Can ONLY reference vars defined in defaults or in core !
    // - No self usage, use local vars instead !
    // - ONLY variable composition here
    local dir_prefix = vars._stack_path_abs + vars.paasify_sep_dir;
    {

      # Generic composes
      # --------------------------
      app_fqdn: vars.app_name + '.' + vars.app_domain,
      app_user_email: 'user@' + vars.app_domain,
      app_adm_fqdn: vars.app_adm_name + '.' + vars.app_domain,
      app_description: self.app_fqdn + " instance",

      # App directories
      # --------------------------

      # App prefix
      app_dir_template: vars._stack_app_path,
      app_dir_helpers: vars._stack_app_path + vars.paasify_sep_dir + 'helpers',
      app_dir_build: vars._stack_app_path + '/build', # Build dir

      # Usual app dirs
      app_dir_root: vars._stack_path_abs,
      app_dir_script: dir_prefix + 'scripts', # Dir for storing container scripts and helpers
      app_dir_secrets: dir_prefix + 'secrets', # Autogenerated secrets
      app_dir_media: dir_prefix + 'media',
      app_dir_plugins: dir_prefix + 'plugins',
      app_dir_internal: dir_prefix + 'internal',
      app_dir_license: dir_prefix + 'license', # For licenses files

      # Runtime dir
      app_dir_conf: dir_prefix + 'conf', # Commitables files into git
      app_dir_backup: dir_prefix + 'backup', # Backup directory
      app_dir_data: dir_prefix + 'data', # Backup data
      app_dir_share: dir_prefix + 'share', # No backup, data for apps
      app_dir_debug: dir_prefix + 'debug', # No backup, data for apps
      app_dir_lib: dir_prefix + 'lib', # No backup, data for apps
      app_dir_state: dir_prefix + 'state', # No backup, data for apps

      # Temp dirs
      app_dir_cache: dir_prefix + 'cache', # Cache files
      app_dir_logs: dir_prefix + 'logs', # Backup ?
      app_dir_tmp: dir_prefix + 'tmp', # Just a tmp pool dir

      # Other dir helpers
      app_dir_db_data: dir_prefix + 'db_data', # Backup data
      app_dir_db_conf: dir_prefix + 'db_conf', # Commitables files into git


      app_dir_urandom: '/dev/urandom', # Commitables files into git
      app_dir_random: '/dev/urandom', # Commitables files into git

      app_docker_socket: '/var/run/docker.sock', # DEPRECATED
      app_docker_sock: '/var/run/docker.sock',

    } + if vars.paasify_extra_vars then {

      app_admin_email: vars.app_admin_user + '@' + vars.app_domain,

      # App Networks
      # --------------------------

      ldap_uri: vars.ldap_prot + '://' + vars.ldap_host + ':' + vars.ldap_port,
      ldap_base_dn: paasify.LdapBaseDNFromDomain(vars.ldap_domain, sep='dc'),
      ldap_user_base_dn: 'ou=people,' + self.ldap_base_dn,
      ldap_group_base_dn: 'ou=groups,' + self.ldap_base_dn,
      ldap_admin_bind_dn: 'cn=admin,' + self.ldap_base_dn,

      # Generic networks
      // We NEED to follow docker default name convention
      app_network_name_default: vars.app_namespace + vars.paasify_sep_net + vars.app_name + "_default",

      app_network_name: vars.app_network_name_prefix + vars.paasify_sep_net + vars.app_network_name_sufix,

      net_backup: vars.app_namespace + vars.paasify_sep_net + 'backup', # For backup network
      net_docker: vars.app_namespace + vars.paasify_sep_net + 'docker', # For docker socket access
      net_proxy: vars.app_namespace + vars.paasify_sep_net + 'proxy',
      net_proxy_web: vars.app_namespace + vars.paasify_sep_net + 'proxy',
      net_proxy_ip: vars.app_namespace + vars.paasify_sep_net + 'proxy',

      net_mail: vars.app_namespace + vars.paasify_sep_net + 'mail',
      net_vpn: vars.app_namespace + vars.paasify_sep_net + 'vpn',
      net_ldap: vars.app_namespace + vars.paasify_sep_net + 'ldap',
      net_sql: vars.app_namespace + vars.paasify_sep_net + 'sql',
      net_nosql: vars.app_namespace + vars.paasify_sep_net + 'nosql',
      net_queue: vars.app_namespace + vars.paasify_sep_net + 'queue',
      net_ostorage: vars.app_namespace + vars.paasify_sep_net + 'ostorage', # Object storage
      net_fstorage: vars.app_namespace + vars.paasify_sep_net + 'fstorage', # File storage
      net_bstorage: vars.app_namespace + vars.paasify_sep_net + 'bstorage', # Block storage

    } else {},


  // Apply docker-compose transformations
  docker_transform (vars, docker_file)::

    if vars.paasify_extra_vars then

      local svc_keys = std.objectFields(docker_file.services);
      local net_keys = std.objectFields(docker_file.networks);
      local vol_keys = std.objectFields(docker_file.volumes);
      local secret_keys = std.objectFields(docker_file.secrets);
      local config_keys = std.objectFields(docker_file.configs);
      local pref_base = 'paasify.';

      docker_file + {
        # Global modifications

        // We enforce best known version
        version: '3.8',

        // For ALL services, update sanity defaults
        services+: {
          [svc_name]+: {

            // Ensure hostname is correctly set
            hostname: svc_name,

            // Update default labels for each containers
            labels+: {
              [pref_base + 'path']: vars.app_dir_root,

              #[pref_base + 'managed']: true,
              #[pref_base + 'name']: vars.app_name,
              #[pref_base + 'namespace']: vars.app_namespace,
              #[pref_base + 'fqdn']: vars.app_fqdn,
              #[pref_base + 'domain']: vars.app_domain,
              //[pref_base + 'networks']: std.join(',', net_keys),
            },

            // Update restart policy of not already set
            restart: std.get(docker_file.services[svc_name], 'restart', vars.app_restart_policy),
          } for svc_name in svc_keys
        },

      } + {
        # Main service modifications

        // Update default/$app_network_key network
        networks+: if std.objectHas(docker_file.networks, vars.app_network_key)
          then paasify.DockerNetDef(
            vars.app_network_key,
            net_name = vars.app_network_name,
            net_external = vars.app_network_external,
          )
          else {},

        // Update the main service only
        services+: {
          [vars.app_service]+: {

            // hostname: svc_name, # only when working on all containers
            hostname: vars.app_name,

            // Update default labels for each containers
            labels+: {
              [pref_base + 'principal']: true,
              [pref_base + 'fqdn']: vars.app_fqdn,
            },
          }
        },
      }
    else docker_file,

};

paasify.main(plugin)
