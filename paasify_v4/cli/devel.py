import logging
import os
from pprint import pprint

from clak import Argument, Command, Parser
from clak.views import ListView, ShowView

from paasify_v4.models.core_catalog import PaasifyCatalog
from paasify_v4.models.core_namespace import PaasifyNamespace
from paasify_v4.models.core_stack import PaasifyStack

logger = logging.getLogger("paasify_v4.cli.devel")


# Devel commands
# ================================================

# WIP
