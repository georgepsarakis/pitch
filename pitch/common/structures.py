from argparse import Namespace
from collections import MutableMapping, namedtuple

from requests import Request


class ReadOnlyContainer(object):
    """
    Base class for read-only property containers.
    """
    def __init__(self, **fields):
        """
        Initialize the property container from the given field-value pairs.
        :param fields: container field-value pairs as keyworded arguments.
        """
        self._factory = namedtuple(
            typename='read_only_container',
            field_names=fields.keys()
        )
        self._container = self._factory(**fields)

    def __getattr__(self, name):
        return getattr(self._container, name)


class InstanceInfo(ReadOnlyContainer):
    def __init__(self, process_id: int, loop_id: int, threads: int):
        """
        Instance information

        :param process_id: Process identifier
        :param loop_id: Current loop zero-based index
        :param threads: Total number of available threads
        """
        thread_id = loop_id % threads + 1
        loop_id += 1
        super(InstanceInfo, self).__init__(
            process_id=process_id,
            thread_id=thread_id,
            loop_id=loop_id
        )


# TODO: inherit from CaseInsensitiveDict
# TODO: consider removal
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

    def get_any(self, *keys):
        for key in keys:
            try:
                return key, self[key]
            except KeyError:
                pass

    def find_first(self, key: str, others: list, default: object):
        if key in self:
            return self[key]

        for other in others:
            if key in other:
                return other[key]

        return default

    def set_transform(self, key, fn, *args, **kwargs):
        self[key] = fn(self[key], *args, **kwargs)


class PitchRequest(Request):
    def __init__(self, *args, **kwargs):
        super(PitchRequest, self).__init__(*args, **kwargs)
        self.__pitch_properties = Namespace()

    @property
    def pitch_properties(self):
        return self.__pitch_properties

    def update(self, **kwargs):
        for property_name, value in kwargs.items():
            setattr(self.__pitch_properties, property_name, value)
            if hasattr(self, property_name):
                setattr(self, property_name, value)
