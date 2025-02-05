"""Variable store implementation.

This module provides the core variable store functionality by combining the base StoreManager
with template rendering capabilities from RenderableStoreManager.

The main components are:

- StoreManager: Base class for managing variables and their sources
- Source: Class representing a variable source/scope
- UndefinedVarError: Exception raised when accessing undefined variables
- RenderableStoreManager: Extended store manager with template rendering

The module serves as the main entry point for using the variable management system,
providing both basic variable storage and template-based variable resolution.
"""

# pylint: disable=unused-import
from .store_base import StoreManager, Source, UndefinedVarError
from .store_template import RenderableStoreManager
