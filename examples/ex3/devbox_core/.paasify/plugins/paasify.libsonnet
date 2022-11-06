

local _metadata_default = 
  {
    "ERROR": "Metadata is not set !"
  };

local _fn_default_vars(vars) =
  {};

local _fn_docker_override (vars, docker_file) = docker_file;



{
  local lib_paasify = self,

  // Return the current value of input vars
  getConf(name)::
    std.parseJson(std.extVar(name)),


  main(plugin)::

    // Get plugin config
    local metadata = std.get(plugin, "metadata", default=_metadata_default);
    local fn_default_vars = std.get(plugin, "default_vars", default=_fn_default_vars);
    // local fn_override_vars = std.get(plugin, "override_vars", default=_fn_default_vars);
    local fn_docker_override = std.get(plugin, "docker_override", default=_fn_docker_override);

    // Extract user input
    local action = self.getConf('action'); // expect a string
    local vars = self.getConf('user_data'); // expect a dict

    // Prepare output
    local out = {
      action: action,
    };

    // Process action
    if action == 'metadata' then
      out + {
        metadata:  metadata,
      }
    else if action == 'vars_default' then
      out + {
        current_vars: vars,
        vars_default: fn_default_vars(vars),
      }
    // else if action == 'vars_override' then
    //   out + {
    //     current_vars: vars,
    //     vars_override: fn_override_vars(vars),
    //   }
    else if action == 'docker_override' then
      local docker_file = self.getConf('docker_file'); // expect a dict of docker-compose
      out + {
        current_vars: vars,
        docker_override: fn_docker_override(vars, docker_file),
      }
    else
      out + {
        msg: "Action not set !"
      }






  // // Run hook
  // run_vars() ::
  //   {}
  // ,
  // run_transform() ::
  //   {}
  // ,

  // // Init point
  // main(metadata, global_vars_default, global_vars_override, docker_transform) ::

  //   // local getConf(name) = std.parseJson(std.extVar(name));
  //   local action = self.getConf('action');

  //   if action == 'metadata' then
  //     metadata

  //   else if action == 'vars' then
  //     local user_data = self.getConf('user_data');
  //     local default_data = global_vars_default(user_data);
  //     local common =  { [x]: std.get(user_data, std.lstripChars(x, '_'), default_data[x] ) for x in std.objectFields(default_data) };
  //     {
  //       input: user_data,
        
  //       diff: default_data + common + global_vars_override(default_data + user_data ),
  //       merged: user_data + global_vars_override(default_data + user_data ),
  //     }

  //   else if action == 'docker_transform' then
  //     local user_data = self.getConf('user_data');
  //     local docker_data = self.getConf('docker_data');

  //     {
  //       input: user_data,

  //       #diff: docker_transform(user_data + global_vars_override(user_data), docker_data),
  //       diff: docker_transform(user_data, docker_data),
  //       merged: docker_data + self.diff,
  //   },

  // // Init point
  // main2(
  //   metadata=null,
  //   fn_vars=null,
  //   fn_transform=null)::
  //   // global_vars_default, global_vars_override, docker_transform) ::

  //   // local getConf(name) = std.parseJson(std.extVar(name));
  //   local action = self.getConf('action');

  //   local _metadata = if std.isObject(metadata) then metadata else metadata_default;
  //   // std.isFunction()

  //   if action == 'metadata' then
  //     _metadata

  //   else if action == 'docker_vars' then
  //     local user_data = self.getConf('user_data');
  //     // #local default_data = global_vars_default(user_data);
  //     // #local common =  { [x]: std.get(user_data, std.lstripChars(x, '_'), default_data[x] ) for x in std.objectFields(default_data) };
  //     {
  //       input: user_data,
  //       TMP: _metadata,
        
  //       // diff: default_data + common + global_vars_override(default_data + user_data ),
  //       // merged: user_data + global_vars_override(default_data + user_data ),
  //     }

  //   else if action == 'docker_transform' then
  //     local user_data = self.getConf('user_data');
  //     local docker_data = self.getConf('docker_data');

  //     {
  //       input: user_data,

  //       #diff: docker_transform(user_data + global_vars_override(user_data), docker_data),
  //       // diff: docker_transform(user_data, docker_data),
  //       // merged: docker_data + self.diff,
  //   },



}

# Run main script !
#main()

