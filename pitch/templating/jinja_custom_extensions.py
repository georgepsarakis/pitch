import json
import os
from typing import Callable

_FILTERS = {}
_TESTS = {}


def _get_name(name):
    return name.split('_', 2)[-1]


def register_filter(func: Callable):
    name = _get_name(func.__name__)
    _FILTERS[name] = func


def register_test(func: Callable):
    name = _get_name(func.__name__)
    _TESTS[name] = func


def _core_filter_from_environment(value, default=None):
    return os.environ.get(value, default=default)


def _core_filter_to_json(value):
    return json.dumps(value)


def _core_filter_from_json(value):
    return json.loads(value)


def _core_test_json_serializable(value):
    try:
        json.loads(value)
        return True
    except ValueError:
        return False


register_filter(_core_filter_from_environment)
register_filter(_core_filter_to_json)
register_filter(_core_filter_from_json)
register_test(_core_test_json_serializable)


def get_registered_filters():
    return _FILTERS.copy()


def get_registered_tests():
    return _TESTS.copy()
