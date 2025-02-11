# Path Anchoring Tutorial


This tutorial demonstrates how to use the `PathAnchor` and `FileAnchor` classes to handle path manipulations in a clean and predictable way. These classes are particularly useful when dealing with relative paths and nested configurations.

## Basic Concepts

The `PathAnchor` system provides a way to:
- Handle both relative and absolute paths consistently
- Maintain path relationships when dealing with nested configurations
- Clean and normalize paths
- Control path output format (relative vs absolute)

## 1. Basic Path Anchoring

### Simple Path Resolution

```python
from superconf.anchors2 import PathAnchor

# Create a root anchor
project_dir = "/fake_root/project"
root_anchor = PathAnchor(project_dir)

# Create paths relative to the root
config_path = PathAnchor("justafile.yml", anchor=root_anchor)
nested_path = PathAnchor("subdir/subdir/file", anchor=root_anchor)
```

The paths will be resolved relative to the root anchor. You can get the resolved path using:
```python
$ config_path.get_dir()  # Returns the directory path
/fake_root/project/justafile.yml


```

### Complex Path Resolution

The system can handle complex relative paths:
```python
complex_path = PathAnchor("subdir2/../../subdir2/file", anchor=root_anchor)
```

## 2. Nested Anchors

One of the most powerful features is the ability to nest anchors:

```python
# Create a hierarchy of anchors
project_dir = "/fake/prj"
root_anchor = PathAnchor(project_dir)
conf_anchor = PathAnchor("../../common_conf", anchor=root_anchor)
inventory_anchor = PathAnchor("inventory/", anchor=conf_anchor)

# Each anchor maintains its relationship to its parent
```

### Important Concepts for Nested Anchors:
1. Each anchor uses its parent as the reference point
2. Paths are resolved through the chain of anchors
3. The final path maintains the correct relationships

## 3. Path Modes

You can control how paths are output using modes:

```python
# Absolute mode - always outputs absolute paths
abs_anchor = PathAnchor("path", anchor=root_anchor, mode="abs")

# Relative mode - always outputs relative paths
rel_anchor = PathAnchor("path", anchor=root_anchor, mode="rel")
```

## 4. Working with Files

The `FileAnchor` class extends `PathAnchor` to work specifically with files:

```python
from superconf.anchors2 import FileAnchor

# Create a file anchor
config_file = FileAnchor("config/settings.yml", anchor=root_anchor)

# Get different components
file_path = config_file.get_path()  # Full path including filename
directory = config_file.get_dir()   # Just the directory
filename = config_file.get_file()   # Just the filename
```

## 5. Path Cleaning

Both classes support path cleaning to normalize paths:

```python
anchor = PathAnchor("subdir/../otherdir/file")
clean_path = anchor.get_dir(clean=True)    # Normalizes the path
raw_path = anchor.get_dir(clean=False)     # Keeps the original form
```

## Best Practices

1. Always establish a clear root anchor for your project
2. Use modes consistently across related anchors
3. Consider using `clean=True` when resolving paths to avoid path traversal issues
4. Use `FileAnchor` when working with files to get additional file-specific functionality

## Common Patterns

### Configuration Management
```python
root = PathAnchor("/project")
config = PathAnchor("config/", anchor=root)
templates = PathAnchor("templates/", anchor=config)

# Files in these locations
main_config = FileAnchor("main.yml", anchor=config)
template = FileAnchor("base.tpl", anchor=templates)
```

### Inventory Management
```python
inventory = PathAnchor("inventory/", anchor=root)
group_vars = PathAnchor("group_vars/", anchor=inventory)
host_vars = PathAnchor("host_vars/", anchor=inventory)
```

## Error Handling

The anchor system will raise appropriate exceptions when:
- Invalid paths are provided
- Anchor relationships can't be resolved
- Path operations would result in invalid states

Always test path resolutions in your application to ensure they behave as expected. 


