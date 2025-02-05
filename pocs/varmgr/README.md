# Variable Manager (varmgr)

A powerful and flexible variable management system that provides hierarchical configuration management with scoping, layering, and variable resolution capabilities.

## Goal

The Variable Manager solves the common problem of managing configuration variables across different scopes and layers in complex applications. It addresses several key challenges:

- Managing configuration variables across different scopes (application, project, stack)
- Handling variable overrides and fallbacks in a predictable way
- Supporting variable resolution with dependencies
- Providing a clear hierarchy for configuration sources
- Enabling flexible configuration through multiple sources (CLI, environment, config files, etc.)

## Technical Implementation Overview

### Core Concepts

#### 1. Sources

Sources represent different configuration origins with assigned priority levels. Each source has:
- A unique name (e.g., `app_cli`, `project_env`)
- A priority level (lower numbers = higher priority)
- Optional help text describing its purpose

Example source definition:
```python
Source("app_cli", level=300, help="Application main CLI")
Source("app_env", level=300, help="Application environment variables")
Source("app_defaults", level=999, help="Application defaults")
```

#### 2. Scopes

Scopes define hierarchical configuration contexts that can inherit from each other. The system supports three main scopes:

- `scope_app`: Application-level configuration
- `scope_project`: Project-level configuration (inherits from app)
- `scope_stack`: Stack-level configuration (inherits from project)

Each scope can access variables from its own sources and inherited scopes.

#### 3. Variable Resolution

The system provides two main implementations:

1. `StoreManager`: Basic variable resolution with scope inheritance
2. `RenderableStoreManager`: Advanced variable resolution supporting template variables (e.g., `${var_name}`)

## Quickstart

### Basic Usage

```python
from lib.store import StoreManager, Source

# Create a variable manager instance
varmgr = StoreManager()

# Define and add sources
varmgr.add_sources([
    Source("app_cli", level=300, help="Application main CLI"),
    Source("app_env", level=300, help="Application environment variables"),
    Source("app_defaults", level=999, help="Application defaults"),
])

# Define scopes and their inheritance
varmgr.set_scopes({
    "scope_app": ["app_cli", "app_env", "app_defaults"],
    "scope_project": [
        "project_cli",
        "project_env",
        "project_defaults",
        "scope_app",  # Inherit from app scope
    ],
})

# Set configuration values
app_config = {
    "app_name": "myapp",
    "debug": True
}
varmgr.set_layer("app_cli", app_config)

# Get values
app_name = varmgr.get_value("app_name")  # Returns "myapp"
```

### Template Variables

Using the `RenderableStoreManager` for variable interpolation:

```python
from lib.store_template import RenderableStoreManager

# Create a renderable store manager
varmgr = RenderableStoreManager()

# Set up sources and scopes (same as basic usage)
# ...

# Set values with templates
config = {
    "project_name": "myproject",
    "env": "prod",
    "stack_name": "${project_name}-${env}"  # Will resolve to "myproject-prod"
}

varmgr.set_layer("project_env", config)

# Get rendered values
stack_name = varmgr.get_value("stack_name")  # Returns "myproject-prod"
```

### Working with Multiple Scopes

```python
# Set values in different scopes
app_vars = {
    "log_level": "INFO",
    "app_name": "myapp"
}
project_vars = {
    "project_id": "proj-123",
    "log_level": "DEBUG"  # Override app's log_level
}

varmgr.set_layer("app_defaults", app_vars)
varmgr.set_layer("project_env", project_vars)

# Get values from different scopes
app_log_level = varmgr.get_value("log_level", scope="scope_app")     # Returns "INFO"
proj_log_level = varmgr.get_value("log_level", scope="scope_project") # Returns "DEBUG"

# Get all values in a scope
project_values = varmgr.get_values(scope="scope_project")
# Returns merged values from project and app scopes
```

### Debugging and Inspection

```python
# Show available sources and their help text
varmgr.show_sources_help()

# Inspect variable resolution
var_info = varmgr.inspect_var("log_level", scope="scope_project")

# Get all source names for a scope
sources = varmgr.get_source_names(scope="scope_stack")
``` 