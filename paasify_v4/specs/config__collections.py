from pprint import pprint

from superconf import ConfigurationObj, ConfigurationDict,  Field, FieldConf


class GenericCollection(ConfigurationObj):
    """Generic collection"""


class GenericCollections(ConfigurationDict):
    """Generic collections configuration"""

    class Meta:
        children_class = GenericCollection
