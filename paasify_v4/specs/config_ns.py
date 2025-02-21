"Tag manager spec model"
from pprint import pprint

from superconf.configuration import (Configuration, ConfigurationDict,
                                     ConfigurationList)
from superconf.fields import Field, FieldConf

from paasify_v4.specs.config__collections import GenericCollections
from paasify_v4.specs.config__tags import AppFeatures, AppPlugins, AppSides
from paasify_v4.specs.config__vars import GenericVars


class NamespaceMetadata(Configuration):
    """Application configuration"""

    # Define configuration fields
    name = Field(help="Namespace name")
    desc = Field(help="Namespace description")


class NamespaceStacks(ConfigurationList):
    """Namespace stacks"""

    class Meta:
        cache = True


#############################################################


class PaasifyNamespaceConfig(Configuration):
    """Main namespace configuration"""

    class Meta:
        cache = True
        env_prefix = "PAASIFY_NS"

    # Application configuration
    meta = FieldConf(children_class=NamespaceMetadata)
    collections = FieldConf(children_class=GenericCollections)
    vars = FieldConf(children_class=GenericVars)
    stacks = FieldConf(children_class=NamespaceStacks)
