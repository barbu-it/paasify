import pytest
from pprint import pprint

from lib.store_base import (
    StoreManager,
    Source,
    UndefinedVarError,
    VarMgrError,
    VarMgrAppError,
    AlreadyExistingSourceError,
)


@pytest.fixture
def varmgr():
    """Set up test fixtures."""
    varmgr = StoreManager()

    # Test datasets
    dataset1 = {
        "name": "dataset1",
        "path": "/home/user/dataset1",
        "test_override": "dataset1",
        "fallback_app": "fallback_dataset1",
    }
    dataset2 = {
        "description": "This is a dataset for testing Tollyo",
        "path": "/home/user/dataset2",
        "options": "value",
        "test_override": "dataset2",
        "fallback_project": "fallback_dataset2",
    }
    dataset3 = {
        "description": "This is a dataset for testing ds3",
        "path": "/home/user/dataset3",
        "test_override": "dataset3",
        "fallback_stack": "fallback_dataset3",
    }

    # Add sources
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

    # Set scopes
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

    # Set layers
    varmgr.set_layer("app_cli", dataset1)
    varmgr.set_layer("project_env", dataset2)
    varmgr.set_layer("stack_env", dataset3)

    return varmgr


def test_get_source_names(varmgr):
    """Test getting source names with and without scopes."""
    # Test all sources
    expected_all = [
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
    assert varmgr.get_source_names() == expected_all

    # Test app scope
    expected_app = ["app_cli", "app_env", "app_defaults"]
    assert varmgr.get_source_names(scope="scope_app") == expected_app

    # Test project scope
    expected_project = [
        "project_cli",
        "project_env",
        "project_defaults",
        "app_cli",
        "app_env",
        "app_defaults",
    ]
    assert varmgr.get_source_names(scope="scope_project") == expected_project

    # Test stack scope
    expected_stack = [
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
    assert varmgr.get_source_names(scope="scope_stack") == expected_stack


def test_get_values_overrides(varmgr):
    """Test value overrides across different scopes."""
    # Test default scope
    assert varmgr.get_value("test_override") == "dataset1"

    # Test app scope
    assert varmgr.get_value("test_override", scope="scope_app") == "dataset1"

    # Test project scope
    assert varmgr.get_value("test_override", scope="scope_project") == "dataset2"

    # Test stack scope
    assert varmgr.get_value("test_override", scope="scope_stack") == "dataset3"


def test_get_values_fallback(varmgr):
    """Test fallback values in different scopes."""
    # Test app scope fallback
    assert varmgr.get_value("fallback_app", scope="scope_app") == "fallback_dataset1"

    # Test project scope fallback
    assert (
        varmgr.get_value("fallback_project", scope="scope_project")
        == "fallback_dataset2"
    )

    # Test stack scope fallback
    assert (
        varmgr.get_value("fallback_stack", scope="scope_stack") == "fallback_dataset3"
    )


def test_get_values(varmgr):
    """Test getting all values in different scopes."""
    # Test app scope values
    expected_app = {
        "fallback_app": "fallback_dataset1",
        "name": "dataset1",
        "path": "/home/user/dataset1",
        "test_override": "dataset1",
    }
    assert varmgr.get_values(scope="scope_app") == expected_app

    # Test project scope values
    expected_project = {
        "description": "This is a dataset for testing Tollyo",
        "fallback_app": "fallback_dataset1",
        "fallback_project": "fallback_dataset2",
        "name": "dataset1",
        "options": "value",
        "path": "/home/user/dataset2",
        "test_override": "dataset2",
    }
    assert varmgr.get_values(scope="scope_project") == expected_project

    # Test stack scope values
    expected_stack = {
        "description": "This is a dataset for testing ds3",
        "fallback_app": "fallback_dataset1",
        "fallback_project": "fallback_dataset2",
        "fallback_stack": "fallback_dataset3",
        "name": "dataset1",
        "options": "value",
        "path": "/home/user/dataset3",
        "test_override": "dataset3",
    }
    assert varmgr.get_values(scope="scope_stack") == expected_stack


def test_get_var_names(varmgr):
    """Test getting variable names."""
    expected_names = {
        "name",
        "path",
        "test_override",
        "fallback_app",
        "description",
        "options",
        "fallback_project",
        "fallback_stack",
    }
    assert set(varmgr.get_var_names()) == expected_names


def test_unknown_var(varmgr):
    """Test handling of unknown variables."""
    with pytest.raises(UndefinedVarError):
        varmgr.get_var("unknown")


def test_inspect_var(varmgr):
    """Test inspecting variables across layers."""
    layers = varmgr.inspect_var("test_override", scope="scope_stack")
    assert len(layers) == 3
    assert layers[0].payload["test_override"] == "dataset3"
    assert layers[1].payload["test_override"] == "dataset2"
    assert layers[2].payload["test_override"] == "dataset1"


def test_add_duplicate_source():
    """Test adding a duplicate source raises an error."""
    varmgr = StoreManager()

    # Add first source
    varmgr.add_sources(Source("test_source", level=100))

    # Try to add the same source again
    with pytest.raises(AlreadyExistingSourceError):
        varmgr.add_sources(Source("test_source", level=200))

    varmgr.add_sources(Source("test_source", level=200), force=True)


def test_reference_missing_source():
    """Test referencing a non-existent source raises an error."""
    varmgr = StoreManager()

    with pytest.raises(VarMgrAppError):
        varmgr.set_scopes({"test_scope": ["non_existent_source"]})


def test_circular_scope_reference():
    """Test circular scope references raise an error."""
    varmgr = StoreManager()
    varmgr.add_sources([Source("source1", level=100), Source("source2", level=200)])

    with pytest.raises(VarMgrAppError):
        varmgr.set_scopes(
            {"scope1": ["source1", "scope2"], "scope2": ["source2", "scope1"]}
        )


def test_empty_source_and_scope():
    """Test behavior with empty sources and scopes."""
    varmgr = StoreManager()

    # Test empty source list
    varmgr.add_sources([])
    assert len(varmgr.get_source_names()) == 0

    # Test empty scope
    varmgr.set_scopes({"empty_scope": []})
    assert len(varmgr.get_source_names(scope="empty_scope")) == 0


def test_source_level_ordering():
    """Test sources are correctly ordered by level."""
    varmgr = StoreManager()

    # Add sources with different levels in non-sorted order
    sources = [
        Source("high", level=900),
        Source("low", level=100),
        Source("mid", level=500),
        Source("default", level=None),  # Should use DEFAULT_LEVEL
    ]
    varmgr.add_sources(sources)

    ordered_names = varmgr.get_source_names()
    assert ordered_names == ["low", "mid", "default", "high"]


def test_get_var_edge_cases(varmgr):
    """Test edge cases for variable retrieval."""
    # Test retrieving from non-existent scope
    with pytest.raises(KeyError):
        varmgr.get_var("test_override", scope="non_existent_scope")

    # Test retrieving non-existent var in valid scope
    with pytest.raises(UndefinedVarError):
        varmgr.get_var("non_existent_var", scope="scope_app")


def test_source_help_text():
    """Test source help text functionality."""
    varmgr = StoreManager()

    # Source with help text
    source_with_help = Source("test1", level=100, help="Test help message")
    # Source without help text
    source_without_help = Source("test2", level=200)

    varmgr.add_sources([source_with_help, source_without_help])

    # Verify help text is preserved
    sources = varmgr._sources
    assert sources["test1"].get_help() == "Test help message"
    assert sources["test2"].get_help() == "Source test2"


def test_scope_inheritance():
    """Test complex scope inheritance scenarios."""
    varmgr = StoreManager()

    # Create a chain of sources
    sources = [
        Source("base", level=100),
        Source("middle", level=200),
        Source("top", level=300),
    ]
    varmgr.add_sources(sources)

    # Create nested scopes
    varmgr.set_scopes(
        {
            "base_scope": ["base"],
            "middle_scope": ["middle", "base_scope"],
            "top_scope": ["top", "middle_scope"],
        }
    )

    # Add test data
    varmgr.set_layer("base", {"value": "base", "unique_base": "base"})
    varmgr.set_layer("middle", {"value": "middle", "unique_middle": "middle"})
    varmgr.set_layer("top", {"value": "top", "unique_top": "top"})

    # Test value resolution through inheritance chain
    values = varmgr.get_values(scope="top_scope")
    assert values["value"] == "top"
    assert values["unique_base"] == "base"
    assert values["unique_middle"] == "middle"
    assert values["unique_top"] == "top"
