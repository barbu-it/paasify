# -*- coding: utf-8 -*-
"""
Core Paasify Library
"""

import logging
from pathlib import Path
from single_version import get_version
from cafram.utils import addLoggingLevel

# Add logging levels for the whole apps
addLoggingLevel("NOTICE", logging.INFO + 5)
addLoggingLevel("EXEC", logging.DEBUG + 5)
addLoggingLevel("TRACE", logging.DEBUG - 5)

# Manage version from poetry
__version__ = get_version("paasify", Path(__file__).parent.parent)
