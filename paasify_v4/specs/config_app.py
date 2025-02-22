"Tag manager spec model"
from pprint import pprint

from superconf.configuration import Configuration, ConfigurationDict
from superconf.fields import Field, FieldConf, FieldDict

from paasify_v4.specs.config__tags import AppFeatures, AppPlugins, AppSides


class AppMetadata(Configuration):
    """Application configuration"""

    class Meta:
        cache = True

    # Define configuration fields
    desc = Field(help="Application description")
    url = Field(help="Application url")
    icon = Field(help="Application icon")
    git_url = Field(help="Application git url")

    main_file = Field(help="Application main yaml file")


#############################################################
#############################################################


class AppMainConfig(Configuration):
    """Main Application example"""

    class Meta:
        cache = True
        app_name = "my-app"
        env_prefix = "MYAPP"

    # Application configuration
    meta = FieldConf(children_class=AppMetadata)
    vars = FieldDict(help="vars to use")

    features = FieldConf(children_class=AppFeatures)
    plugins = FieldConf(children_class=AppPlugins)
    sides = FieldConf(children_class=AppSides)

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
