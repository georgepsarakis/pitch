import yaml #  flake8: noqa

from yaml import SafeLoader


def construct_yaml_str(self, node):
    # Override the default string handling function
    # to always return unicode objects
    return self.construct_scalar(node)


SafeLoader.add_constructor(u'tag:yaml.org,2002:str', construct_yaml_str)
