from __future__ import unicode_literals
from collections import MutableMapping, namedtuple
import six
from requests import Request
from .utils import to_iterable


class ReadOnlyContainer(object):
    def __init__(self, **fields):
        self._factory = namedtuple(
            typename='read_only_container',
            field_names=fields.keys()
        )
        self._container = self._factory(**fields)

    def __getattr__(self, name):
        return getattr(self._container, name)


class InstanceInfo(ReadOnlyContainer):
    def __init__(self, process_id, loop_id, threads):
        thread_id = loop_id % threads + 1
        loop_id += 1
        super(InstanceInfo, self).__init__(
            process_id=process_id,
            thread_id=thread_id,
            loop_id=loop_id
        )


class PitchDict(MutableMapping):
    def __init__(self, *args, **kwargs):
        self._dict = dict(*args, **kwargs)

    def __getitem__(self, item):
        return self._dict.__getitem__(item)

    def __setitem__(self, key, value):
        self._dict.__setitem__(key, value)

    def __delitem__(self, key):
        del self._dict[key]

    def __len__(self):
        return self._dict.__len__()

    def __iter__(self):
        return self._dict.__iter__()

    def __add__(self, other):
        new = self.copy()
        new.update(other)
        return new

    def __iadd__(self, other):
        self.update(other)
        return self

    def __repr__(self):
        return 'PitchDict({})'.format(self._dict.items())

    def iteritems(self):
        return six.iteritems(self._dict)

    def copy(self):
        return self.__class__(self)

    def remove_keys(self, *keys):
        dictionary_copy = self.copy()
        for key in keys:
            try:
                del dictionary_copy[key]
            except KeyError:
                pass
        return dictionary_copy

    def get_any_item_by_key(self, *keys, **kwargs):
        for key in keys:
            try:
                return key, self[key]
            except KeyError:
                pass
        return None, kwargs.get('default')

    def get_first_from_multiple(self, key, other, default=None):
        other = to_iterable(other)
        if key in self:
            return self[key]
        for other_dict in other:
            if key in other_dict:
                return other_dict[key]
        return default

    def nested_get(self, key, default=None):
        from jinja2 import Environment
        environment = Environment()
        expression = environment.compile_expression(key)
        result = expression(**self)
        if result is None:
            result = default
        return result

    def inplace_transform(self, key, fn, *args, **kwargs):
        self[key] = fn(self[key], *args, **kwargs)


class PitchRequest(Request):
    def update(self, **kwargs):
        for property_name, value in six.iteritems(kwargs):
            setattr(self, property_name, value)
