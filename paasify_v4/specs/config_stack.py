"Tag manager spec model"
from pprint import pprint

from superconf import ConfigurationObj, ConfigurationDict, Field, FieldConf, FieldDict

from paasify_v4.specs.config__collections import GenericCollections

from paasify_v4.specs.config__tags import AppFeatures, AppPlugins, AppSides, PodFeatures

# from paasify_v4.specs.config__vars import GenericVars


class StackMetadata(ConfigurationObj):
    """Stack configuration"""

    # Define configuration fields
    name = Field(help="Stack name")
    desc = Field(help="Stack description")


class StackPod(ConfigurationObj):
    """Stack pod"""

    class Meta:
        extra_fields = True

    # Define configuration fields
    app = Field(help="app to use")
    # features = Field(help="features to use")
    features = FieldConf(PodFeatures, help="features to use")

    vars = FieldDict(help="vars to use")

    # # plugins = Field(help="plugins to use")
    # sides = Field(help="sides to use")
    # # vars = FieldConf(children_class=GenericVars, help="Pod vars to use")
    # tags = Field(help="tags to use")
    # import_ = Field(help="import to use", key="import")
    # link = Field(help="link to use")


class StackPods(ConfigurationDict):
    """Stack pods"""

    class Meta:
        children_class = StackPod


#############################################################


class PaasifyStackConfigFile(ConfigurationObj):
    """Main namespace configuration"""

    # class Meta:
    #     env_prefix = "PAASIFY_STACK"

    # Application configuration
    meta = FieldConf(StackMetadata)
    collections = FieldConf(GenericCollections)
    vars = FieldDict(help="vars to use")
    apps = FieldConf(StackPods)
