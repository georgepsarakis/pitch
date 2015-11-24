from __future__ import unicode_literals
from itertools import chain
import six
if six.PY2:
    from types import NoneType
else:
    NoneType = type(None)
from .utils import to_iterable


def combine(*args):
    return tuple(chain.from_iterable(map(to_iterable, args)))


t_int = six.integer_types
t_string = six.string_types
t_int_none = combine(t_int, NoneType)
t_string_none = combine(t_string, NoneType)

