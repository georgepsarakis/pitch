from __future__ import unicode_literals
from .common import (
    BasePlugin,
    LoggerPlugin,
    DelayPlugin,
    UpdateContext
)
from ..lib.common.utils import get_exported_plugins


class BaseRequestPlugin(BasePlugin):
    def __init__(self):
        self._phase = 'request'


class RequestLoggerPlugin(LoggerPlugin, BaseRequestPlugin):
    _name = 'request_logger'


class RequestDelayPlugin(DelayPlugin, BaseRequestPlugin):
    _name = 'request_delay'


class RequestUpdateContext(UpdateContext, BaseRequestPlugin):
    _name = 'pre_register'


class FileInputPlugin(BaseRequestPlugin):
    _name = 'file_input'

    def __init__(self, filename):
        import os
        self._filename = os.path.expanduser(os.path.abspath(filename))
        self._directory = os.path.dirname(filename)
        if not os.path.isfile(self._filename):
            raise OSError(
                "Directory {} does not exist".format(
                    self._directory
                )
            )

    def execute(self, plugin_context):
        with open(self._filename, 'r') as f:
            self._result = f.read()


class ProfilerPlugin(BaseRequestPlugin):
    _name = 'profiler'

    def __init__(self):
        import time
        self._start_time = time.clock()

    @property
    def start_time(self):
        return self._start_time


class JSONPostDataPlugin(BaseRequestPlugin):
    import json
    _name = 'json_post_data'
    _encoder = json.dumps

    def execute(self, plugin_context):
        plugin_context.request.data = self._encoder(
            plugin_context.request.data
        )


class AddHeaderPlugin(BaseRequestPlugin):
    _name = 'add_header'

    def __init__(self, header, value):
        self._header = header
        self._value = value

    def execute(self, plugin_context):
        plugin_context.request.headers[self._header] = self._value


exported_plugins = get_exported_plugins(BaseRequestPlugin)