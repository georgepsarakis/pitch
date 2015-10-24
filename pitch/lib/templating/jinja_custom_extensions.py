from __future__ import unicode_literals
import json
import os
from types import FunctionType
import six


def get_filter_name(name):
    return name.split('_', 2)[-1]


def core_filter_from_environment(value, default=None):
    return os.environ.get(value, default=default)


def core_filter_to_json(value):
    return json.dumps(value)


def core_filter_from_json(value):
    return json.loads(value)


def core_test_json_serializable(value):
    try:
        json.loads(value)
        return True
    except ValueError:
        return False


filters = {
    get_filter_name(name): function
    for name, function in six.iteritems(locals())
    if isinstance(function, FunctionType) and name.startswith('core_filter_')
}

tests = {
    get_filter_name(name): function
    for name, function in six.iteritems(locals())
    if isinstance(function, FunctionType) and name.startswith('core_test_')
}
