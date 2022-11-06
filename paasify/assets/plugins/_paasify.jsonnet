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

  // Return default vars
  global_default(vars)::
    // Rules:
    // - Only static variables
    // - Referenced variables must be defined first in _paasify or in tag deps
    // - No self usage
    // - No variable composition here
    {
      
      is_swarm: false,
      swarm_nodes: 1,

      # Generic (Allow user overrides)
      # --------------------------
      app_name: std.get(vars, 'app_name', default=vars._stack_name) ,
      app_alias: std.get(vars, 'app_alias', default=self.app_name) ,
      app_namespace: std.get(vars, 'app_namespace', default=vars._prj_namespace) ,
      app_domain: std.get(vars, 'app_domain', default=vars._prj_domain + '.localhost') ,
      app_adm_name: self.app_name + "-adm",


      # Networking
      # --------------------------
      app_service: std.get(vars, 'app_service', default=vars._stack_service) ,

      app_network_name_prefix: self.app_namespace,
      // Considered as a constant as it mimic/guess docker-compose network naming pattern
      app_network_name_sufix: self.app_name + "_default",
      app_network: std.get(vars, 'app_network', default=vars._stack_network) ,
      app_network_external: false,


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


      # App configuration
      # --------------------------

      # See: https://docs.docker.com/compose/compose-file/compose-file-v3/#restart
      app_restart_policy: 'unless-stopped',
      # app_restart_policy: 'on-failure',
      # app_restart_policy: 'always',
      # app_restart_policy: 'no',

      app_puid: '1000',
      app_pgid: '1000',

      app_lang: 'en_US',
      app_tz: 'UTC',
      app_tz_var: 'TZ',
      app_tz_mount: false,
      app_tz_mounts: '/etc/timezone:/etc/timezone:ro,/etc/localtime:/etc/localtime:ro',

      app_debug: 'false',


      # App user informations
      # --------------------------

      app_admin_login: 'admin',
      app_admin_passwd: 'CHANGEME123!!!',

      app_user_login: 'user',
      app_user_passwd: 'CHANGEME!',

      app_readonly_login: 'readonly',
      app_readonly_passwd: 'CHANGEME',


      # App Backend info
      # --------------------------
      app_db_type: null,
      
      app_db_host: 'db',
      app_db_port: '3306',
      app_db_name: self.app_name,
      app_db_user: self.app_name,
      app_db_passwd: self.app_name,

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

    },

  global_assemble(vars)::
    // Rules:
    // - Can ONLY reference vars defined in defaults or in core !
    // - No self usage, use local vars instead !
    // - ONLY variable composition here
    local dir_prefix = vars._stack_path_abs + vars.paasify_sep_dir;
    {
      ldap_uri: vars.ldap_prot + '://' + vars.ldap_host + ':' + vars.ldap_port,
      ldap_base_dn: paasify.LdapBaseDNFromDomain(vars.ldap_domain, sep='dc'),
      ldap_user_base_dn: 'ou=people,' + self.ldap_base_dn,
      ldap_group_base_dn: 'ou=groups,' + self.ldap_base_dn,
      ldap_admin_bind_dn: 'cn=admin,' + self.ldap_base_dn,
      
      # Generic composes
      # --------------------------
      app_fqdn: vars.app_name + '.' + vars.app_domain,
      app_admin_email: vars.app_admin_login + '@' + vars.app_domain,
      app_user_email: 'user@' + vars.app_domain,

      app_adm_fqdn: vars.app_adm_name + '.' + vars.app_domain,

      app_description: self.app_fqdn + " instance",


      # App directories
      # --------------------------

      # App prefix
      app_dir_template: vars._stack_app_path,

      # Usual app dirs
      app_dir_root: dir_prefix,
      app_dir_build: dir_prefix + 'build', # Build dir
      app_dir_script: dir_prefix + 'scripts', # Dir for storing container scripts and helpers 
      app_dir_secrets: dir_prefix + 'secrets', # Autogenerated secrets

      # Runtime dir
      app_dir_conf: dir_prefix + 'conf', # Commitables files into git
      app_dir_backup: dir_prefix + 'backup', # Backup directory
      app_dir_data: dir_prefix + 'data', # Backup data
      app_dir_share: dir_prefix + 'share', # No backup, data for apps

      # Temp dirs
      app_dir_cache: dir_prefix + 'cache', # Cache files
      app_dir_logs: dir_prefix + 'logs', # Backup ?
      app_dir_tmp: dir_prefix + 'tmp', # Just a tmp pool dir

      # Other dir helpers
      app_dir_db_data: dir_prefix + 'db_data', # Backup data
      app_dir_db_conf: dir_prefix + 'db_conf', # Commitables files into git


      # App Networks
      # --------------------------

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
    


    },

  // Automagically change the network name
  // This is due to default compose config behavior to add networks where none as been defined
  docker_transform (vars, docker_file)::
    local svc_keys = std.objectFields(docker_file.services);
    local net_keys = std.objectFields(docker_file.networks);
    local vol_keys = std.objectFields(docker_file.volumes);
    local secret_keys = std.objectFields(docker_file.secrets);
    local config_keys = std.objectFields(docker_file.configs);
    local pref_base = 'paasify.';
  
    docker_file + {
      // We enforce best known version
      version: '3.8',

      networks+: {
        [net_key]+: {
          // Update default labels for each networks
          labels+: {
            [pref_base + 'managed']: true,
            //[pref_base + 'prj.' + vars.app_namespace]: true,
            //[pref_base + 'prj.' + vars.app_namespace + '.name']: vars.app_name,
            //[pref_base + 'prj.' + vars.app_namespace + '.fqdn']: vars.app_fqdn,
            //[pref_base + 'prj.' + vars.app_namespace + '.path']: vars.app_dir_root,
            //[pref_base + 'prj.' + vars.app_namespace + '.origin']: ! vars.app_network_external,
            //[pref_base + 'prj.' + vars.app_namespace + '.services']: std.join(',', svc_keys),
          }
        } for net_key in net_keys
      } + {
        // Update default network
        [vars.app_network]+: {
          // We ensure default network is correctly named
          name: vars.app_network_name,
          external: vars.app_network_external,
        },
      },

      services+: {
        [svc_name]+: {
          // Update default labels for each containers
          labels+: {
            [pref_base + 'managed']: true,
            [pref_base + 'name']: vars.app_name,
            [pref_base + 'namespace']: vars.app_namespace,
            //[pref_base + 'domain']: vars.app_domain,
            [pref_base + 'fqdn']: vars.app_fqdn,
            [pref_base + 'path']: vars.app_dir_root,
            //[pref_base + 'networks']: std.join(',', net_keys),
          },
          restart: vars.app_restart_policy,
        } for svc_name in svc_keys
      },

    },

};

paasify.main(plugin)

