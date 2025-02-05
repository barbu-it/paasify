from pprint import pprint

from lib.store_base import Source, UndefinedVarError
from lib.store_template import RenderableStoreManager


def main1():
    "Firs featureset"
    varmgr = RenderableStoreManager()

    vars_1app_cli = {
        "app_name": "dataset1",
    }
    vars_1project_env = {
        # "project_name": "project1",
        "project_name": "project1+${stack_name}",
        # This create a circular reference that raise an exception
        # this must be tested
        # "project_name": "project1+${stack_fname}",
    }
    vars_1stack_env = {
        "stack_name": "dataset3",
        "stack_fname": "${project_name}_${stack_name}",
    }

    varmgr.add_sources(
        [
            # App sources
            Source("app_cli", level=300, help="Application main CLI"),
            Source("app_env", level=300, help="Application environment variables"),
            Source("app_secret", level=300, help="Application secrets"),
            Source("app_config", level=400, help="Application configuration"),
            Source("app_defaults", level=999, help="Application defaults"),
            # Project sources
            Source("project_cli", level=300, help="Project main CLI"),
            Source("project_env", level=300, help="Project environment variables"),
            Source("project_secret", level=300, help="Project secrets"),
            Source("project_config", level=400, help="Project configuration"),
            Source("project_defaults", level=999, help="Project defaults"),
            # Stack sources
            Source("stack_defaults", level=999, help="Stack defaults"),
            Source("stack_cli", level=300, help="Stack main CLI"),
            Source("stack_env", level=300, help="Stack environment variables"),
            Source("stack_secret", level=999, help="Stack secrets"),
            Source("stack_config", level=999, help="Stack configuration"),
        ]
    )

    varmgr.set_scopes(
        {
            "scope_app": [
                "app_cli",
                "app_env",
                "app_defaults",
            ],
            "scope_project": [
                "project_cli",
                "project_env",
                "project_defaults",
                # Defaults
                "scope_app",
            ],
            "scope_stack": [
                "stack_cli",
                "stack_env",
                "stack_defaults",
                # Defaults
                "scope_project",
            ],
        }
    )

    # pprint(out)
    # print("========================== Dumping OBJ:")
    # pprint (varmgr.__dict__)
    # print("========================== ")

    varmgr.set_layer("app_cli", vars_1app_cli)
    varmgr.set_layer("project_env", vars_1project_env)
    varmgr.set_layer("stack_env", vars_1stack_env)
    print("========================== Dumping OBJ:")
    pprint(varmgr.__dict__)

    # Test scope_stack renderer

    renderer = varmgr.get_renderer("scope_stack")
    # out = renderer.render_var("stack_fname")
    # print("\nRESULT: stack_fname1")
    # pprint(out)

    def test_cache_debug():

        # Do not use cache and validate
        out1 = renderer.render_var("stack_fname", debug=True, cache=False)
        print("\nRESULT: stack_fname2")
        pprint(out1)

        # AI THIS TEST IS NOT COVERED BY UNIT TESTS
        out2 = renderer.render_var("stack_fname", debug=True, cache=False)
        print("\nRESULT: stack_fname2")
        # pprint(out1)
        pprint(out2)

        assert out1 == out2

        # Use cache and validate
        out1 = renderer.render_var("stack_fname", debug=True, cache=True)
        print("\nRESULT: stack_fname2")
        pprint(out1)

        out2 = renderer.render_var("stack_fname", debug=True, cache=True)
        print("\nRESULT: stack_fname2")
        pprint(out2)

        assert out1 != out2

    def test_cache():

        # Do not use cache and validate
        out1 = renderer.render_var("stack_fname", debug=False, cache=False)
        print("\nRESULT: stack_fname2")
        pprint(out1)

        out2 = renderer.render_var("stack_fname", debug=False, cache=False)
        print("\nRESULT: stack_fname2")
        pprint(out2)

        assert out1 == out2

        # Use cache and validate
        out1 = renderer.render_var("stack_fname", debug=False, cache=True)
        print("\nRESULT: stack_fname2")
        pprint(out1)

        out2 = renderer.render_var("stack_fname", debug=False, cache=True)
        print("\nRESULT: stack_fname2")
        pprint(out2)

        assert out1 == out2

    def test_values():

        out = renderer.render_values()
        pprint(out)
        expected = {
            "app_name": "dataset1",
            "project_name": "project1+dataset3",
            "stack_fname": "project1+dataset3_dataset3",
            "stack_name": "dataset3",
        }
        assert expected == out

    test_cache_debug()
    test_cache()
    test_values()

    print("Tests POC3 OK")


def main2():
    "Second featureset"

    # varmgr = StoreManager()


if __name__ == "__main__":
    main1()
    main2()
