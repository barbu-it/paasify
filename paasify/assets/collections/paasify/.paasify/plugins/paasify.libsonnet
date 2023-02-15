local _p = import '_p.libsonnet';

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
      [net_id]+: std.prune({
        name: net_name,
        external: net_external,
        labels: net_labels,
        ipam: net_ipam,
      }),
    }
    else {}
  );

// Attach a network to a service
local DockerServiceNet(net_id, net_aliases=[], net_ipv4=null, net_ipv6=null, priority=0) =
  if std.isString(net_id) then
  {
    networks+: {
      [net_id]: std.prune({
        aliases+: net_aliases,
        priority: priority , #if priority > 0 then priority else null,
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


// Generic jsonnet helpers
// =============================

// Like std.startsWith, but prefixes accept an array of string instead of just a string
local startsWithOneOf(key, prefixes)=
  local tmp1 = [ std.startsWith(key, prefix) for prefix in prefixes ];
  local tmp2 = std.filter((function(x) x == true), tmp1);
  std.length(tmp2) > 0;


// Extract all environments variables starting with prefix, prefix can be a string or an array of string
local FilterVarsPrefix(vars, prefix)=
  local _prefixes = if std.isArray(prefix) then prefix else [prefix];
  { [name]: vars[name]
      for name in [
            key for key in std.objectFields(vars) if startsWithOneOf(key, _prefixes)
      ]
  };


// Get first value from vars, or return default
local values(vars, keys, default=null, prune=true)=
  local env_keys = [key for key in std.objectFields(vars)];
  local req_keys = if std.isArray(keys) then keys else [keys];
  local match = [ key for key in req_keys if std.member(env_keys, key) ];
  local match2 = if prune then std.prune(match) else match;
  if std.length(match2) > 0 then
    std.get(vars, match2[0])
  else
    default;


// Main wrapper
// =============================
{
  local lib_paasify = self,
  local allowed_actions = ["global_default", "global_assemble", "docker_transform", "plugin_vars", "metadata"],

  // Internal lib
  // =====================

  // Validate if a plugin command is allowed
  validate_command(action, allowed_actions)::
    local match = [ x for x in allowed_actions if x == action];
    assert std.length(match) > 0: 'Plugin option must be one of ' + allowed_actions + ", got: " + action;
    match[0],

  // Return the current value of input vars
  getConf(name)::
    std.parseJson(std.extVar(name)),

  # Return plugin vars
  get_global_vars(plugin, vars, prune=false)::
    local fn_default = std.get(plugin, "global_default", default=_fn_empty);
    local fn_assemble = std.get(plugin, "global_assemble", default=_fn_empty);
    #local vars2 = std.prune(vars);
    local vars2 = vars;
    local defaults = fn_default(vars2);
    {
      def: _p.update_defaults(defaults, vars2, prune=prune),
      dyn: _p.update_defaults(fn_assemble(defaults + vars2), vars2, prune=prune),
      tmp: defaults,

      # For QA&Docs
      #raw_def: defaults,
      #raw_dyn: fn_assemble(vars2 + defaults),
    },

  # Allow nested calls from one plugin to another one
  // Remove all vars from called plugin
  // plugin_name: name of the plugin
  call_other(plugin, df, vars, override={})::

    // Key a array of dynamic keys to delete from the target config
    local rm_keys = std.objectFields(plugin.global_assemble(vars));

    // Delete all plugins dynamic keys in the vars context
    local env2 = std.prune({ [key]: if std.member(rm_keys, key) then null else vars[key]
          for key in std.objectFields(vars) }) ;

    // Forward to usual loader, and assemble result
    local env = self.get_global_vars(plugin, env2 + override , prune=true);
    local merged = env.def + env.dyn;

    // Return plugin processing with the freshly crafted env
    plugin.docker_transform(merged, df),
    # Debug: { zz_result: plugin.docker_transform(merged, df), zzzz_debug: env, zzzz_rm_keys: env2 },

  // Std lib
  // =====================
  DockerServiceNet:: DockerServiceNet,
  DockerNetDef:: DockerNetDef,
  LdapBaseDNFromDomain:: LdapBaseDNFromDomain,
  FilterVarsPrefix:: FilterVarsPrefix,
  values:: values,


  # Helpers libs
  startsWithOneOf:: startsWithOneOf,

  // Main app
  // =====================
  main(plugin)::

    // Get plugin config
    local metadata = std.get(plugin, "metadata", default=_metadata_default);

    // Extract user input
    local parent = $.getConf('parent');                                       // expect a string
    local args = $.getConf('args');                                           // expect a dict
    local action = $.validate_command($.getConf('action'), allowed_actions);  // expect a string

    assert std.objectHas(plugin.metadata, 'ident'): "Missing ident field in plugin metadata, this plugin is not valid!";

    // Choose action to execute
    if plugin.metadata.ident != parent then    # For imports ?
      // Extract plugins function
      // This manage the case where a module want to import another module
      plugin

    else if action == 'docker_transform' then
      // Return a modified docker-compose data
      local fn = std.get(plugin, "docker_transform", default=_fn_docker_override);
      local params = $.get_global_vars(plugin, args);
      local merged =  params.def + params.dyn + args;
      fn(merged, $.getConf('docker_data'))

    else if action == 'plugin_vars' then
      // Return dict of plugin variables
      $.get_global_vars(plugin, args)

    else if action == 'metadata' then
      // Return dict of plugin variables
      metadata

    else
      assert false: 'Unknown action';
      null,
}

# Run main script !
#main()
