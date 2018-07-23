from pitch.plugins.common import BasePlugin


class Registry(object):
    def __init__(self):
        self._request = {}
        self._response = {}

    def add_subclasses(self, base_plugin_class):
        return [self.add(cls) for cls in base_plugin_class.__subclasses__()]

    @property
    def request_plugins(self):
        return self._request

    @property
    def response_plugins(self):
        return self._response

    @property
    def phases(self) -> tuple:
        return 'request', 'response'

    def all(self):
        return {
            'request': self.request_plugins,
            'response': self.response_plugins
        }

    def by_phase(self, name):
        if name == 'request':
            return self.request_plugins
        elif name == 'response':
            return self.response_plugins
        else:
            raise NameError(name)

    def exists(self, cls):
        name = cls.get_name()
        phase = cls.get_phase()
        return self.by_phase(phase).get(name) is not None

    def add(self, cls):
        name = cls.get_name()
        phase = cls.get_phase()
        self.by_phase(phase)[name] = cls
        return cls


def register(cls: BasePlugin):
    if not registry.exists(cls):
        registry.add(cls)
    return cls


registry = Registry()
