import pytest
from varmgr import Varmgr, Source, UndefinedVarError, AlreadyExistingSourceError

@pytest.fixture
def varmgr():
    mgr = Varmgr()
    mgr.set_order([
        Source("override", level=0),
        Source("cli", level=100),
        Source("env_vars", level=200),
        Source("config_files", level=300),
        Source("secrets", level=400),
        Source("other_level1"),
        Source("other_level2"),
        Source("defaults", level=999),
    ])
    return mgr

@pytest.fixture
def sample_datasets():
    dataset1 = {
        "name": "dataset1",
        "path": "/home/user/dataset1",
        "enabled": True,
        "disabled": False,
        "count": 0,
        "positive": 1,
        "negative": -1,
        "empty": None,
        "tags": ["tag1", "tag2", "tag3"],
        "nested": {
            "key1": "value1",
            "key2": 2,
            "key3": False,
            "deep": {
                "a": 1,
                "b": None,
                "c": [1, 2, 3]
            }
        }
    }
    dataset2 = {
        "description": "This is a dataset for testing Tollyo",
        "path": "/home/user/dataset2",
        "options": "value",
        "flags": {
            "debug": True,
            "verbose": False,
            "level": 0
        },
        "empty_list": [],
        "empty_dict": {},
        "mixed_list": [1, "two", False, None, {"key": "value"}],
        "status": None,
        "counts": {
            "success": 1,
            "failure": 0,
            "skipped": -1
        }
    }
    dataset3 = {
        "description": "This is a dataset for testing ds3",
        "path": "/home/user/dataset3",
        "active": True,
        "priority": 0,
        "retries": -1,
        "config": None,
        "matrix": [
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1]
        ],
        "settings": {
            "timeout": 30,
            "enabled": True,
            "defaults": None,
            "limits": {
                "min": -1,
                "max": 1,
                "default": 0
            }
        }
    }
    # Get all unique keys from the datasets
    all_keys = set()
    for dataset in [dataset1, dataset2, dataset3]:
        all_keys.update(dataset.keys())
    all_keys = sorted(list(all_keys))

    return dataset1, dataset2, dataset3, all_keys

def test_source_import(varmgr, sample_datasets):
    dataset1, dataset2, dataset3, all_keys = sample_datasets
    
    varmgr.import_source("cli", dataset1)
    varmgr.import_source("config_files", dataset2, source="main.yml")
    varmgr.import_source("other_level1", dataset3, source="options.yml")
    
    # Test that all variables are present
    var_names = varmgr.get_all_var_names()
    expected_var_names = all_keys
    assert sorted(var_names) == sorted(expected_var_names)

def test_variable_precedence(varmgr, sample_datasets):
    dataset1, dataset2, dataset3, all_keys = sample_datasets
    
    varmgr.import_source("cli", dataset1)
    varmgr.import_source("config_files", dataset2)
    varmgr.import_source("other_level1", dataset3)
    
    # Test precedence - cli (level 100) should override config_files (level 300)
    assert varmgr.get_value("path") == "/home/user/dataset1"
    
    # Test value from config_files when not in cli
    assert varmgr.get_value("description") == "This is a dataset for testing Tollyo"
    
    # Test value only present in cli
    assert varmgr.get_value("name") == "dataset1"
    
    # Test value only present in config_files
    assert varmgr.get_value("options") == "value"

def test_undefined_variable(varmgr):
    with pytest.raises(UndefinedVarError):
        varmgr.get_value("unknown")

def test_source_metadata(varmgr, sample_datasets):
    dataset1, _, _, _ = sample_datasets
    
    # Test source metadata is preserved
    varmgr.import_source("cli", dataset1, source="test_source")
    dump = varmgr.dump()
    
    # Verify the dump contains source information
    assert "cli" in str(dump)
    assert "test_source" in str(dump)

def test_empty_varmgr():
    mgr = Varmgr()
    assert mgr.get_all_var_names() == []
    
    with pytest.raises(UndefinedVarError):
        mgr.get_value("any_var")

def test_source_order_validation():
    mgr = Varmgr()
    
    # Test that sources must be unique
    with pytest.raises(AlreadyExistingSourceError):
        mgr.set_order([
            Source("same", level=1),
            Source("same", level=2)
        ])

def test_multiple_source_levels(varmgr, sample_datasets):
    dataset1, dataset2, _, _ = sample_datasets
    
    # Import same variable in different sources
    varmgr.import_source("cli", {"test_var": "cli_value"})
    varmgr.import_source("config_files", {"test_var": "config_value"})
    varmgr.import_source("defaults", {"test_var": "default_value"})
    
    # Should get the value from highest precedence source (cli)
    assert varmgr.get_value("test_var") == "cli_value"
