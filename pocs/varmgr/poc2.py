from pprint import pprint

from lib.store import StoreManager, Source, UndefinedVarError


def main1():
    "Firs featureset"
    varmgr = StoreManager()

    dataset1 = {
        "name": "dataset1",
        # "description": "This is a dataset for testing",
        "path": "/home/user/dataset1",
        "test_override": "dataset1",
        "fallback_app": "fallback_dataset1",
    }
    dataset2 = {
        # "name": "dataset2",
        "description": "This is a dataset for testing Tollyo",
        "path": "/home/user/dataset2",
        "options": "value",
        "test_override": "dataset2",
        "fallback_project": "fallback_dataset2",
    }
    dataset3 = {
        # "name": "dataset3",
        "description": "This is a dataset for testing ds3",
        "path": "/home/user/dataset3",
        # "options": "value",
        "test_override": "dataset3",
        "fallback_stack": "fallback_dataset3",
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

    varmgr.set_layer("app_cli", dataset1)
    varmgr.set_layer("project_env", dataset2)
    varmgr.set_layer("stack_env", dataset3)
    print("========================== Dumping OBJ:")
    pprint(varmgr.__dict__)
    print("========================== ")

    def test_get_source_names():

        # TEst get_source_names
        # ===================================
        print("========================== get_source_names")

        out = varmgr.get_source_names()
        expected = [
            "app_cli",
            "app_env",
            "app_secret",
            "project_cli",
            "project_env",
            "project_secret",
            "stack_cli",
            "stack_env",
            "app_config",
            "project_config",
            "app_defaults",
            "project_defaults",
            "stack_defaults",
            "stack_secret",
            "stack_config",
        ]
        pprint(out)
        assert out == expected

        out = varmgr.get_source_names(scope="scope_app")
        expected = ["app_cli", "app_env", "app_defaults"]
        # pprint(expected)
        pprint(out)
        assert out == expected

        out = varmgr.get_source_names(scope="scope_project")
        expected = [
            "project_cli",
            "project_env",
            "project_defaults",
            "app_cli",
            "app_env",
            "app_defaults",
        ]

        pprint(out)
        assert out == expected

        out = varmgr.get_source_names(scope="scope_stack")
        expected = [
            "stack_cli",
            "stack_env",
            "stack_defaults",
            "project_cli",
            "project_env",
            "project_defaults",
            "app_cli",
            "app_env",
            "app_defaults",
        ]

        pprint(out)
        assert out == expected

    def test_get_values_overrides():

        out = varmgr.get_value("test_override")
        pprint(out)
        assert out == "dataset1"

        out = varmgr.get_value("test_override", scope="scope_app")
        pprint(out)
        assert out == "dataset1"

        out = varmgr.get_value("test_override", scope="scope_project")
        pprint(out)
        assert out == "dataset2"

        out = varmgr.get_value("test_override", scope="scope_stack")
        pprint(out)
        assert out == "dataset3"

    def test_get_values_fallback():

        out = varmgr.get_value("fallback_app", scope="scope_app")
        pprint(out)
        assert out == "fallback_dataset1"

        out = varmgr.get_value("fallback_project", scope="scope_project")
        pprint(out)
        assert out == "fallback_dataset2"

        out = varmgr.get_value("fallback_stack", scope="scope_stack")
        pprint(out)
        assert out == "fallback_dataset3"

    def test_get_values():

        out = varmgr.get_values(scope="scope_app")
        pprint(out)
        expected = {
            "fallback_app": "fallback_dataset1",
            "name": "dataset1",
            "path": "/home/user/dataset1",
            "test_override": "dataset1",
        }
        assert out == expected

        out = varmgr.get_values(scope="scope_project")
        pprint(out)
        expected = {
            "description": "This is a dataset for testing Tollyo",
            "fallback_app": "fallback_dataset1",
            "fallback_project": "fallback_dataset2",
            "name": "dataset1",
            "options": "value",
            "path": "/home/user/dataset2",
            "test_override": "dataset2",
        }

        assert out == expected

        out = varmgr.get_values(scope="scope_stack")
        pprint(out)
        expected = {
            "description": "This is a dataset for testing ds3",
            "fallback_app": "fallback_dataset1",
            "fallback_project": "fallback_dataset2",
            "fallback_stack": "fallback_dataset3",
            "name": "dataset1",
            "options": "value",
            "path": "/home/user/dataset3",
            "test_override": "dataset3",
        }

        pprint(varmgr.inspect_var("description", scope="scope_stack"))

        assert out == expected
        # assert False, "WIPPP"

    def test_show_sources_help():

        varmgr.show_sources_help()
        varmgr.show_sources_help(scope="scope_stack")

    def test_unknown_var():
        try:
            varmgr.get_var("unknown")
            assert False, "Exception should have been raised"
        except UndefinedVarError as e:
            print("Exception raised: ", e)

    test_get_source_names()
    test_get_values_overrides()
    test_get_values_fallback()
    test_get_values()
    test_show_sources_help()
    test_unknown_var()



def main2():
    "Second featureset"

    # varmgr = StoreManager()


if __name__ == "__main__":
    main1()
    main2()
