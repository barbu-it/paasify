from pprint import pprint

from superconf.configuration import Configuration, ConfigurationDict
from superconf.fields import Field, FieldConf


class GenericVar(Configuration):
    """Generic var"""


class GenericVars(ConfigurationDict):
    """Generic vars configuration"""

    class Meta:
        cache = True
        children_class = GenericVar
