local paasify = import 'paasify.libsonnet';


// Validate the bare minimum vars are available
local assert_base_vars(vars) =
        assert std.objectHas(vars, 'stack_name');
        assert std.objectHas(vars, 'prj_namespace');
        assert std.objectHas(vars, 'stack_service');
        assert std.objectHas(vars, 'stack_network');
        assert std.objectHas(vars, 'paasify_sep');
        assert std.objectHas(vars, 'stack_path');
        //assert std.objectHas(vars, 'stack_pathxx2');
        true ;

// Validate there is a valid docker-compose document
local assert_docker_file(docker_file) =
        assert std.objectHas(docker_file, 'services');
        true ;

local plugin = {

  // Provides plugin metadata
  metadata: 
    {
        local meta = self,

        name: "Paasify API validator",
        description: 'Test if the Paasify Plugin API works as expected',

        author: "mrjk",
        email: '',
        license: '',
        version: '',

        require: '',
        api: 1,
        jsonschema: {
            // ['$schema']: 'http://json-schema.org/draft-07/schema#',
            type: 'object',
            title: meta.name,
            description: 'Raise an error if the Plugin API does not answer correctly. Mostly usedful for testing Paasify.',
            properties: {
                transform_variables: {
                    type: "null",
                },
                variables: {
                    type: "null",
                },
                transform: {
                    type: "null",
                },
            },
            
        }
    },

  // Return global vars
  default_vars(vars)::
    assert assert_base_vars(vars);
    {
        var1_UatoaL5seibis6Ee: "UatoaL5seibis6Ee",
        var2_UatoaL5seibis6Ee: "UatoaL5seibis6Ee",
        
    },

//   override_vars(vars):: 
//     assert assert_base_vars(vars);
//     assert std.assertEqual(vars.var1_UatoaL5seibis6Ee, "UatoaL5seibis6Ee");
//     assert std.assertEqual(vars.var2_UatoaL5seibis6Ee, "UatoaL5seibis6Ee");
//     {
//         var2_UatoaL5seibis6Ee: "overrided",
//         var3_UatoaL5seibis6Ee: "overrided",

//     },

    // docker_override
  docker_override (vars, docker_file)::
    assert assert_base_vars(vars);
    assert assert_docker_file(docker_file);
    assert std.assertEqual(vars.var1_UatoaL5seibis6Ee, "UatoaL5seibis6Ee");
    // Is this one a good idea ? REsult should be overrided ... override_vars is more like default_vars with this ...
    assert std.assertEqual(vars.var2_UatoaL5seibis6Ee, "UatoaL5seibis6Ee");
    assert std.assertEqual(vars.var3_UatoaL5seibis6Ee, "overrided");

    // Assert a "services" definition exists
    docker_file + {
      ["x-paasify-debug"]: {
          status: "PASSED",
        },        
      },
    

};

paasify.main(plugin)
