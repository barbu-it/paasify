from pprint import pprint

from superconf.configuration import Configuration, ConfigurationDict
from superconf.fields import Field, FieldConf


class GenericCollection(Configuration):
    """Generic collection"""


class GenericCollections(ConfigurationDict):
    """Generic collections configuration"""

    class Meta:
        cache = True
        children_class = GenericCollection
