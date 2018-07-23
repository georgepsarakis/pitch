import yaml


def construct_yaml_str(self, node):
    # Override the default string handling function
    # to always return unicode objects
    return self.construct_scalar(node)


yaml.SafeLoader.add_constructor(u'tag:yaml.org,2002:str', construct_yaml_str)
