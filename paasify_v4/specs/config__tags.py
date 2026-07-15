import os
from types import SimpleNamespace
from pprint import pprint




from superconf import ConfigurationObj, ConfigurationDict, Field, FieldConf, FieldList, FieldBool, FieldDict, FieldString, NOT_SET
import re
from paasify_v4.common import find_file_in_path


#############################################################


class RuleSet(SimpleNamespace):
    "Simple Tag ruleset"


class TagRule:
    "Tag rule"

    def __init__(self, key, parent=None, config=None):

        # Check syntax
        assert re.match(r"^[a-zA-Z0-9_\.]+$", key), f"Invalid key: {key}"

        # key = re.sub(r'[^a-zA-Z0-9\.]', '', key)
        self.key = key
        self.parts = key.split(".")

        self.config = config
        self.parent = parent

        self.feature = self.parent

    def __repr__(self):
        return f"TagRule({self.config})"

    def gen_rules(self, extra_suffixes=None):
        "Generate a list of string rules for a given sufixes"
        extra_suffixes = extra_suffixes or [""]
        out = []
        for sufix in extra_suffixes:
            prefix = self.config
            if sufix:
                prefix = ":".join([prefix, sufix])
            out.append(prefix)
        out = list(set(sorted(out)))
        pprint(out)
        out = [RuleSet(rule=x, tag=self, feat=self.parent) for x in out]
        return out

    # def gen_rules_v1(self, extra_sufixes=None):
    #     "Get providers and requires rules"
    #     extra_sufixes = extra_sufixes or [""]
    #     out = []
    #     for sufix in extra_sufixes:
    #         rules = list(self.parts)
    #         if sufix:
    #             rules.append(sufix)
    #         last = ""
    #         for part in rules:
    #             last = part if not last else ".".join([last, part])
    #             out.append(last)

    #     out = list(set(sorted(out)))
    #     return out


class AppPlugin(ConfigurationObj):
    "App plugin"

    public = FieldBool(help="Public plugin", default=False)
    availability = FieldString(help="Availability")

    provides = FieldList(help="Feature provides")
    requires = FieldList(help="Feature requires")

class AppFeature(ConfigurationObj):
    """Application feature"""


    desc = Field(help="Feature description")
    file = Field(help="Feature file")
    enable = FieldBool(help="Enable feature", default=False)
    auto_enable = FieldBool(help="Auto enable feature", default=False)

    provides = FieldList(help="Feature provides")
    requires = FieldList(help="Feature requires")

    public_provides = FieldList(help="Feature provides")
    public_requires = FieldList(help="Feature requires")

    vars = FieldDict(help="Feature vars")

    group_mode = Field(help="Group mode")
    group_default = Field(help="Group default")
    group = Field(help="Group")


    def pre_load(self, value):
        "Hook to pre-load a value"
        # If a value is set to a boolean, we need to convert it to a dict
        if isinstance(value, bool):
            value = {
                "enable": value,
            }
        return value

    @property
    def name(self):
        "Get name"
        return self.key

    def get_file(self, path):
        "Get file"
        if self.file != NOT_SET:
            assert os.path.exists(self.file), f"File not found: {self.file}"
            return self.file

        # path = self._parent.path
        candidates = [
            f"docker-compose.{self.name}.yml",
            f"docker-compose.{self.name}.yaml",
            f"compose.{self.name}.yml",
            f"compose.{self.name}.yaml",
        ]
        matches = find_file_in_path(candidates, path)
        if len(matches) > 1:
            raise ValueError(f"Multiple files found for feature: {self.name}")
        if len(matches) == 0:
            raise ValueError(f"No file found for feature: {self.name}")

        return matches[0]

    def get_providers(self, mode="local", extra_suffixes=None, metadata=None):
        "Get providers"
        extra_suffixes = extra_suffixes or [""]
        raw_rules = []
        if mode == "local":
            raw_rules = self.provides
        elif mode == "public":
            raw_rules = self.public_provides
        else:
            raise ValueError(f"Invalid mode: {mode}")

        rules = [
            RuleSet(rule = f"{raw_rule}@{metadata.pod_fname}", raw=raw_rule, parent=self, metadata=metadata)
            for raw_rule in raw_rules
        ]
        return rules

        # Create tag children
        assert isinstance(raw_rules, list), f"Items should be a list, got: {raw_rules}"
        out = []
        pprint(raw_rules)
        for raw_rule in raw_rules:
            assert isinstance(
                raw_rule, str
            ), f"Item should be a string, got: {raw_rule}"
            rule = TagRule(raw_rule, parent=self)
            pprint(rule.__dict__)
            out.append(rule)

        print("OUT")
        pprint(out)
        assert False

        # Create tag map
        ret = []
        for tag_rule in out:
            out = tag_rule.gen_rules(extra_suffixes=extra_suffixes)
            ret.extend(out)

        return out

    def get_requires(self, mode="local", extra_suffixes=None, metadata=None):
        "Get consumers"
        raw_rules = []
        if mode == "local":
            raw_rules = self.requires
        elif mode == "public":
            raw_rules = self.public_requires
        else:
            raise ValueError(f"Invalid mode: {mode}")

        rules = [
            RuleSet(rule = f"{raw_rule}", 
                    # raw=raw_rule, 
                    parent=self, metadata=metadata)
            for raw_rule in raw_rules
        ]
        return rules



    # def get_requires(self, mode="local", extra_suffixes=None):
    #     "Get requires"
    #     extra_suffixes = extra_suffixes or [""]
    #     if mode == "local":
    #         items = self.requires
    #     elif mode == "public":
    #         items = self.public_requires
    #     else:
    #         raise ValueError(f"Invalid mode: {mode}")

    #     # Create tag children
    #     assert isinstance(items, list), f"Items should be a list, got: {items}"
    #     out = []
    #     for item in items:
    #         assert isinstance(item, str), f"Item should be a string, got: {item}"
    #         rule = TagRule(item, parent=self)
    #         out.append(rule)

    #     # Create tag map
    #     ret = []
    #     for tag_rule in out:
    #         out = tag_rule.gen_rules(extra_suffixes=extra_suffixes)
    #         ret.extend(out)

    #     return out


class AppFeatures(ConfigurationDict):
    """Application features"""

    class Meta:
        children_class = AppFeature
        # list_support=True

    # def transform_value(self, value):
    #     "Hook to transform a value"
    #     # assert False, "WIP HERE"

    #     if isinstance(value, list):
    #         out = {}
    #         for item in value:
    #             if isinstance(item, str):
    #                 out[item] = {}
    #             elif isinstance(item, dict):
    #                 assert len(item.keys()) == 1, f"Expected 1 key, got too many keys: {item}"
    #                 key = list(item.keys())[0]
    #                 out[key] = item[key]
    #             else:
    #                 assert False, "Unsupported type: {type(item)}"
    #         value = out

    #         pprint(value)
    #         assert False, "WIP HERE"
    #     return value

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     # self.parse_features()

    # def parse_features(self):
    #     "Parse features"

    #     # pprint(self.__dict__)
    #     # print("FEATURES:", self)
    #     for feature in self:
    #         # print("FEATURE:", feature)
    #         prov = feature.get_providers()
    #         # pprint(feature.__dict__)
    #         print("PROVIDERS:", feature.key, prov)
    #         # req = feature.get_requires()
    #         # pprint(req)

    def filter_enabled(self, names, rest=False):
        "Get enabled plugins names"
        assert isinstance(names, list), "Names should be a list"

        ret = []
        matches = []
        for plugin in self:
            # print(plugin.name, plugin.key)
            if plugin.name in names:
                ret.append(plugin)
                matches.append(plugin.name)

        if not rest:
            return ret

        rest = [x for x in names if x not in matches]
        return ret, rest


class PodFeature(AppFeature):
    "Pod feature with slight differents defaults"

    enable = FieldBool(help="Enable feature", default=True)
    auto_enable = FieldBool(help="Auto enable feature", default=True)


class PodFeatures(AppFeatures):
    """Pod features"""

    class Meta:
        children_class = PodFeature
        # list_support=True


class AppSides(ConfigurationDict):
    """Application sides"""



class AppPlugins(ConfigurationDict):
    """Application plugins"""

