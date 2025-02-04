from pprint import pprint

from varmgr import Varmgr, Source, UndefinedVarError


def main():
    varmgr = Varmgr()

    dataset1 = {
        "name": "dataset1",
        # "description": "This is a dataset for testing",
        "path": "/home/user/dataset1",
    }
    dataset2 = {
        # "name": "dataset2",
        "description": "This is a dataset for testing Tollyo",
        "path": "/home/user/dataset2",
        "options": "value",
    }
    dataset3 = {
        # "name": "dataset3",
        "description": "This is a dataset for testing ds3",
        "path": "/home/user/dataset3",
        # "options": "value",
    }

    varmgr.set_order(
        [
            Source("override", level=0),
            Source("cli", level=100),
            Source("env_vars", level=200),
            Source("config_files", level=300),
            Source("secrets", level=400),
            Source("other_level1"),
            Source("other_level2"),
            Source("defaults", level=999),
        ]
    )

    varmgr.import_source("cli", dataset1)
    varmgr.import_source("config_files", dataset2, source="main.yml")
    varmgr.import_source("other_level1", dataset3, source="options.yml")

    out = varmgr.dump()
    # pprint(out)

    # Ensure we get all keys
    out = varmgr.get_all_var_names()
    # pprint(out)
    assert out == ["description", "name", "options", "path"]

    # TEst some vars
    val = varmgr.get_value("description")
    print(val)
    assert val == "This is a dataset for testing Tollyo"

    val = varmgr.get_value("path")
    assert val == "/home/user/dataset1"

    val = varmgr.get_value("name")
    assert val == "dataset1"

    val = varmgr.get_value("options")
    assert val == "value"

    # print ("RESULT: ", val)
    # val = varmgr.get_value("description")
    # print ("RESULT: ", val)
    # Ensure it raise an exception on unknown variable
    try:
        val = varmgr.get_value("unknown")
    except UndefinedVarError as e:
        print("Exception raised: ", e)

    print("OK tests1")


if __name__ == "__main__":
    main()
