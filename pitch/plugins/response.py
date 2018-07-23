import json
import os
import logging
import sys
import time

import requests

from pitch.plugins.common import BasePlugin, LoggerPlugin, UpdateContext
from pitch.common.utils import to_iterable

logger = logging.getLogger()


class BaseResponsePlugin(BasePlugin):
    _phase = 'response'


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
        response = plugin_context.templating['response']
        response.as_json = None
        try:
            response.as_json = json.loads(response.text)
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
        super(JSONFileOutputPlugin, self).__init__()

    def execute(self, plugin_context):
        with open(self._filename, 'w') as f:
            json.dump(plugin_context.templating['response'].json(), f)


class ProfilerPlugin(BaseResponsePlugin):
    """ Keep track of the time required for the HTTP request & processing
    """
    _name = 'profiler'

    def __init__(self):
        self._end_time = time.clock()
        self._elapsed_time = self._end_time
        super(ProfilerPlugin, self).__init__()

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
        self.__expect = [int(code) for code in to_iterable(expect)]
        super(AssertHttpStatusCode, self).__init__()

    def execute(self, plugin_context):
        response = plugin_context.templating['response']
        failfast = plugin_context.step.get(
            'failfast',
            plugin_context.globals['failfast']
        )
        if response.status_code not in self.__expect:
            message = 'Expected HTTP status code {}, received {} - ' \
                      'Reason={} - URL = {}'
            message = message.format(
                self.__expect,
                response.status_code,
                response.text,
                response.request.url
            )
            if failfast:
                raise SystemExit(message)
        if response.status_code < requests.codes.bad_request:
            reporter = logger.info
        else:
            reporter = logger.error
        reporter(
            '[response] Received response (HTTP code={}) from '
            'URL: {}'.format(
                response.status_code,
                response.url
            )
        )
        if response.status_code >= requests.codes.bad_request:
            if failfast:
                response.raise_for_status()
