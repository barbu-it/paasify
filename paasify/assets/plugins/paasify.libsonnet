
// Default functions
// =============================
local _metadata_default = 
  {
    "ERROR": "Metadata is not set !"
  };

local _fn_empty(vars) =
  {};

local _fn_docker_override (vars, docker_file) = docker_file;


// Library functions
// =============================


// Create a network definition
local DockerNetDef(net_id, net_name=null, net_external=false, net_labels={}, net_ipam={}) =
  std.prune(
  if std.isString(net_id) then
  {
    [net_id]+: {
      name: net_name,
      external: net_external,
      labels: net_labels,
      ipam: net_ipam,
    },
  }
  else {});

// Attach a network to a service
local DockerServiceNet(net_id, net_aliases=[], net_ipv4=null, net_ipv6=null) =
  if std.isString(net_id) then
  {
    networks+: {
      [net_id]: std.prune({
        aliases: net_aliases,
        ipv4_address: net_ipv4,
        ipv6_address: net_ipv6,
      }),
    },
  }
  else {};

// Create ldap base DN from domain
local LdapBaseDNFromDomain( domain, sep='dc')=
  local domain_parts = [ sep + '=' + x for x in std.split(domain, '.')];
  std.join(',', domain_parts);


// Main wrapper
// =============================
{
  local lib_paasify = self,

  // Internal lib
  // =====================

  // Return the current value of input vars
  getConf(name)::
    std.parseJson(std.extVar(name)),


  get_global_vars(vars, fn_global_default, fn_global_assemble)::
    local defaults = fn_global_default(vars);
    local assemble = fn_global_assemble(defaults + vars);
    defaults + assemble,


  // Std lib
  // =====================
  DockerServiceNet:: DockerServiceNet,
  DockerNetDef:: DockerNetDef,
  LdapBaseDNFromDomain:: LdapBaseDNFromDomain,

  main(plugin)::
    // Get plugin config
    local metadata = std.get(plugin, "metadata", default=_metadata_default);

    // local fn_global_default = std.get(plugin, "global_default", default=_fn_empty);
    // local fn_global_assemble = std.get(plugin, "global_assemble", default=_fn_empty);

    // local fn_instance_default = std.get(plugin, "instance_default", default=_fn_empty);
    // local fn_instance_assemble = std.get(plugin, "instance_assemble", default=_fn_empty);

    // local fn_docker_transform = std.get(plugin, "docker_transform", default=_fn_docker_override);

    // Extract user input
    local action = $.getConf('action'); // expect a string
    local args = $.getConf('args'); // expect a dict

    // Extract plugins function
    
    if action == 'docker_transform' then
      local fn = std.get(plugin, "docker_transform", default=_fn_docker_override);
      fn(args, $.getConf('docker_data'))
    else
      local fn = std.get(plugin, action, default=_fn_empty);
      fn(args)
    ,





  main_OLD(plugin)::

    // Get plugin config
    local metadata = std.get(plugin, "metadata", default=_metadata_default);

    local fn_global_default = std.get(plugin, "global_default", default=_fn_empty);
    local fn_global_assemble = std.get(plugin, "global_assemble", default=_fn_empty);

    local fn_instance_default = std.get(plugin, "instance_default", default=_fn_empty);
    local fn_instance_assemble = std.get(plugin, "instance_assemble", default=_fn_empty);

    local fn_docker_transform = std.get(plugin, "docker_transform", default=_fn_docker_override);


    // local fn_override_instance_vars = std.get(plugin, "override_instance_vars", default=_fn_empty);
    // local fn_docker_override = std.get(plugin, "docker_override", default=_fn_docker_override);

    // Extract user input
    local action = $.getConf('action'); // expect a string
    local vars = $.getConf('user_data'); // expect a dict

    // Prepare output
    local out = {
      action: action,
    };

    // // Auto sanity test , which may have a good perf impact :/
    // local processed_default_vars = fn_default_vars(vars);
    // local processed_override_vars = fn_override_vars(processed_default_vars);

    // Process action
    if action == 'metadata' then
      out + {
        metadata:  metadata,
      }

    else if action == 'process_transform' then
      out + {
        current_vars: vars,
        docker_file:: $.getConf('docker_file'),

        glob:: $.get_global_vars(vars, fn_global_default, fn_global_assemble) + vars,
        inst :: $.get_global_vars(self.glob, fn_instance_default, fn_instance_assemble),

        instance_vars: self.inst,
        process_transform: fn_docker_transform(self.inst + vars, self.docker_file),
      }

    else if action == 'process_globals' then
      // Processed as one instance
      out + {
        current_vars: vars,

        glob:: $.get_global_vars(vars, fn_global_default, fn_global_assemble) + vars,
        inst :: $.get_global_vars(self.glob, fn_instance_default, fn_instance_assemble) + vars,

        globals: self.glob,
        instance: self.inst,
      }

    // else if action == 'vars_default' then
    //   out + {
    //     current_vars: vars,
    //     // vars_default: fn_default_vars(vars),
    //   }
    // else if action == 'vars_override' then
    //   out + {
    //     current_vars: vars,
    //     // vars_override: fn_override_vars(vars),
    //   }
    // else if action == 'vars_instance_override' then
    //   out + {
    //     current_vars: vars,
    //     // vars_instance_override: fn_override_instance_vars(vars),
    //   }


    // else if action == 'docker_override' then
    //   local docker_file = self.getConf('docker_file'); // expect a dict of docker-compose
    //   out + {
    //     current_vars: vars,
    //     // docker_override: fn_docker_override(vars, docker_file),
    //   }
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

