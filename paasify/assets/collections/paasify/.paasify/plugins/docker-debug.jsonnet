local paasify = import 'paasify.libsonnet';

local plugin = {

  // Provides plugin metadata
  metadata: {
      local meta = self,

      name: "Docker debug Container",
      description: 'Attach container to project',
      ident: 'docker-debug',

      author: "mrjk",
      email: '',
      license: '',
      version: '',

      depends: ['_paasify'],

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
                  docker_debug_image: {
                    description: 'Docker image to use for debugging purpose',
                    default: 'nicolaka/netshoot',
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
  global_default(vars)::
    {
        docker_debug_image: "nicolaka/netshoot",
        docker_debug_vars: "debug",
    },

  // Override vars
  global_assemble(vars):: {},


  // docker_override
  docker_transform (vars, docker_file)::
    local main_svc = docker_file.services[vars.app_service];

    # We only keep the network names here, in way to not copy ip address or existing aliases
    local main_networks = { [x]: null for x in std.objectFields(main_svc.networks)};
    local dump_vars =
        if std.isString(vars.docker_debug_vars) then
          { ["x-debug-vars"]+: paasify.FilterVarsPrefix(vars, std.split(vars.docker_debug_vars, ',') ) }
        else
          {};

    docker_file + {
        services+: {
            debug: {
              image: vars.docker_debug_image,
              tty: true,
              # Not working ... with alpine at least .. command: "tail -f /dev/null",
              # See: https://www.fpcomplete.com/blog/2016/10/docker-demons-pid1-orphans-zombies-signals/
              command: "/bin/bash -c 'trap : TERM INT; sleep infinity & wait'",
              # stop_grace_period: "1s",
              volumes: std.get(main_svc, 'volumes', []) + [
                vars.app_dir_debug + ":/root:rw"
              ],
              networks: main_networks,
            }
          },
      } + dump_vars,
};

paasify.main(plugin)
