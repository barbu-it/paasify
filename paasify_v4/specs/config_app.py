"Tag manager spec model"
from pprint import pprint

from superconf import ConfigurationObj, ConfigurationDict, Field, FieldConf, FieldDict, FieldList

from paasify_v4.specs.config__tags import AppFeatures, AppPlugins, AppSides, AppPlugin, AppFeature


class AppMetadata(ConfigurationObj):
    """Application configuration"""

    # Define configuration fields
    desc = Field(help="Application description")
    url = Field(help="Application url")
    icon = Field(help="Application icon")
    git_url = Field(help="Application git url")

    main_file = Field(help="Application main yaml file")


#############################################################
#############################################################


class AppMainConfig(ConfigurationObj):
    """Main Application example"""

    class Meta:
        # app_name = "my-app"
        # env_prefix = "MYAPP"
        extra_fields = False

    # Application configuration
    meta = FieldConf(AppMetadata)
    vars = FieldDict(help="vars to use")
    resource_model = FieldDict(help="resource model to use")
    remap_rules = FieldDict(help="remap rules to use")
    default_features = FieldList(help="Default features enabled")

    # features = FieldConf(AppFeatures)
    features = FieldConf(ConfigurationDict, children_class=AppFeature)
    plugins = FieldConf(ConfigurationDict, children_class=AppPlugin)


    # plugins = FieldConf(children_class=AppPlugins)
    # sides = FieldConf(children_class=AppSides)

    # @property
    # def root_dir(self):
    #     """Return root dir"""
    #     return self.config.root_dir

    # @property
    # def module_dir(self):
    #     """Return module dir"""
    #     return self.config.module_dir

    # @property
    # def data_dir(self):
    #     """Return data dir"""
    #     return self.config.data_dir
