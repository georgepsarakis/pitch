from collections import namedtuple

from requests.structures import CaseInsensitiveDict
from boltons.typeutils import make_sentinel


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


class HierarchicalDict(CaseInsensitiveDict):
    _MISSING = make_sentinel()

    def __add__(self, other):
        new = self.copy()
        new.update(other)
        return new

    def __iadd__(self, other):
        self.update(other)
        return self

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            self.items()
        )

    def remove(self, *keys):
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

    def find_first(self, key: str, others: list, default: object=_MISSING):
        if key in self:
            return self[key]

        for other in others:
            if key in other:
                return other[key]

        return default
