"Tag manager spec model"
from pprint import pprint

from superconf.configuration import (Configuration, ConfigurationDict,
                                     ConfigurationList)
from superconf.fields import Field, FieldConf

from paasify_v4.specs.config__collections import GenericCollections
from paasify_v4.specs.config__tags import AppFeatures, AppPlugins, AppSides
from paasify_v4.specs.config__vars import GenericVars


class StackMetadata(Configuration):
    """Stack configuration"""

    # Define configuration fields
    name = Field(help="Stack name")
    desc = Field(help="Stack description")


class StackPod(Configuration):
    """Stack pod"""

    # Define configuration fields
    app = Field(help="app to use")
    features = Field(help="features to use")
    # plugins = Field(help="plugins to use")
    sides = Field(help="sides to use")
    vars = Field(help="vars to use")


class StackPods(ConfigurationDict):
    """Stack pods"""

    class Meta:
        cache = True
        children_class = StackPod


#############################################################


class PaasifyStackConfig(Configuration):
    """Main namespace configuration"""

    class Meta:
        cache = True
        env_prefix = "PAASIFY_NS"

    # Application configuration
    meta = FieldConf(children_class=StackMetadata)
    collections = FieldConf(children_class=GenericCollections)
    vars = FieldConf(children_class=GenericVars)
    apps = FieldConf(children_class=StackPods)
