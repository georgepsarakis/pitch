from __future__ import unicode_literals
import json
import sys
import requests
from .common import BasePlugin, LoggerPlugin, UpdateContext
from ..lib.common.utils import (
    stop_execution,
    to_iterable
)
from ..lib.common.utils import get_exported_plugins


class BaseResponsePlugin(BasePlugin):
    def __init__(self):
        self._phase = 'response'


class ResponseUpdateContext(UpdateContext, BaseResponsePlugin):
    """ Add variables to the template context after the response has completed
    """
    _name = 'post_register'


class JSONResponsePlugin(BaseResponsePlugin):
    """
    Serialize the response body as JSON and store in response.as_json
    """
    _name = 'response_as_json'

    def execute(self, plugin_context):
        plugin_context.response.as_json = None
        try:
            plugin_context.response.as_json = json.loads(
                plugin_context.response.text
            )
            self._result = (True, None)
        except ValueError as e:
            self._result = (False, e)


class ResponseLoggerPlugin(LoggerPlugin, BaseResponsePlugin):
    """
    Setup a logger, attach a file handler and log a message.
    """
    _name = 'response_logger'


class JSONFileOutputPlugin(BaseResponsePlugin):
    """
    Write a JSON-serializable response to a file
    """
    _name = 'json_file_output'

    def __init__(self, filename, create_dirs=True):
        import os
        self._filename = os.path.expanduser(os.path.abspath(filename))
        self._directory = os.path.dirname(filename)
        if not os.path.exists(self._directory):
            if create_dirs:
                os.makedirs(self._directory)
            else:
                raise OSError(
                    "Directory {} does not exist".format(
                        self._directory
                    )
                )

    def execute(self, plugin_context):
        with open(self._filename, 'w') as f:
            json.dump(plugin_context.response.as_json, f)


class ProfilerPlugin(BaseResponsePlugin):
    """ Keep track of the time required for the HTTP request & processing
    """
    _name = 'profiler'

    def __init__(self):
        import time
        self._end_time = time.clock()
        self._elapsed_time = self._end_time

    def execute(self, plugin_context):
        request_profiler_plugin = plugin_context.request.plugins.get(
            self._name
        )
        if request_profiler_plugin is None:
            self._result = None
        else:
            self._result -= request_profiler_plugin.start_time

    @property
    def end_time(self):
        return self._end_time

    @property
    def elapsed_time(self):
        return self._result


class StdOutWriterPlugin(BaseResponsePlugin):
    """
    Print a JSON-serializable response to STDOUT
    """
    _name = 'stdout_writer'

    def execute(self, plugin_context):
        sys.stdout.write(
            "{}\n".format(
                json.dumps(
                    plugin_context.response.as_json,
                    sort_keys=True,
                    indent=4
                )
            )
        )
        sys.stdout.flush()


class AssertHttpStatusCode(BaseResponsePlugin):
    """ Examine the response HTTP status code and raise error/stop execution
    """
    _name = 'assert_http_status_code'

    def __init__(self, expect=requests.codes.ok):
        self.__expect = map(int, to_iterable(expect))

    def execute(self, plugin_context):
        response = plugin_context.response
        failfast = plugin_context.processed_step.get_first_from_multiple(
            key='failfast',
            other=plugin_context.scheme,
            default=True
        )
        if response.status_code not in self.__expect:
            message = 'Expected HTTP status code {}, received {}'.format(
                self.__expect,
                response.status_code
            )
            if failfast:
                stop_execution(plugin_context.progress.error, message)
        if response.status_code < requests.codes.bad_request:
            reporter = plugin_context.progress.success
        else:
            reporter = plugin_context.progress.error
        reporter(
            message='[response] Received response (HTTP code={}) from '
                    'URL: {}'.format(
                        response.status_code,
                        response.url
                    )
        )
        if response.status_code >= requests.codes.bad_request:
            if failfast:
                response.raise_for_status()


exported_plugins = get_exported_plugins(BaseResponsePlugin)
