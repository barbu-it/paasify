{

  // Get first value from vars, or return default
  // env: Must be an object
  // keys: keys you want to lookup, first present is returned
  // default: What is returned if not matches
  // prune: Set to false to disable pruning, first value, even null will be returned
  env_valid(vars, keys, default=null, prune=true):
    local env_keys = [key for key in std.objectFields(vars)];
    local req_keys = if std.isArray(keys) then keys else [keys];
    local match = [ key for key in req_keys if std.member(env_keys, key) ];
    local match2 = if prune then std.prune(match) else match;
    if std.length(match2) > 0 then
      std.get(vars, match2[0])
    else
      default,

  // Get first non null value from arr, or return default
  // arr: a list of element to filter out if empty
  // default: default value returned if nothing found
  first_valid(arr, default=null):
    local match = std.prune(arr);
    if std.length(match) > 0 then
      match[0]
    else
      default,

  // Merge obj1 into obj2
  // Takes all obj1 and replace them by their equivalent in obj2
  // If an object does not exists in obj2, it keeps its initial value of obj1
  // By default, obj2 is pruned, set `false` to disable this behavior
  update_defaults(obj1, obj2, prune=true):
    local source = if prune then std.prune(obj2) else obj2;
    { [key]: std.get(source, key, obj1[key]) for key in std.objectFields(obj1) },



}
