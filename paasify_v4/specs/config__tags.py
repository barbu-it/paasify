from pprint import pprint

from superconf.configuration import Configuration, ConfigurationDict
from superconf.fields import Field, FieldConf

#############################################################


class AppFeature(Configuration):
    """Application feature"""

    class Meta:
        cache = True

    desc = Field(help="Feature description")
    provides = Field(help="Feature provides")
    requires = Field(help="Feature requires")

    public_provides = Field(help="Feature provides")
    public_requires = Field(help="Feature requires")

    def get_providers(self, mode="local"):
        "Get providers"
        if mode == "local":
            return self.provides
        elif mode == "public":
            return self.public_provides
        else:
            raise ValueError(f"Invalid mode: {mode}")

    def get_requires(self, mode="local"):
        "Get requires"
        if mode == "local":
            return self.requires
        elif mode == "public":
            return self.public_requires
        else:
            raise ValueError(f"Invalid mode: {mode}")


class AppFeatures(ConfigurationDict):
    """Application features"""

    class Meta:
        cache = True
        children_class = AppFeature

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     # self.parse_features()

    def parse_features(self):
        "Parse features"

        # pprint(self.__dict__)
        # print("FEATURES:", self)
        for feature in self:
            # print("FEATURE:", feature)
            prov = feature.get_providers()
            # pprint(feature.__dict__)
            print("PROVIDERS:", feature.key, prov)
            # req = feature.get_requires()
            # pprint(req)


class AppSides(ConfigurationDict):
    """Application sides"""

    class Meta:
        cache = True


class AppPlugins(ConfigurationDict):
    """Application plugins"""

    class Meta:
        cache = True
