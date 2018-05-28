from copy import deepcopy
from itertools import chain
import logging

from pitch.common.utils import compose_url
import requests

from pitch.plugins.utils import execute_plugins
from pitch.structures import Context, ContextProxy, JinjaEvaluator, \
    HTTPRequest, KEYWORDS
from pitch.interpreter.command import Client
from pitch.encoding import yaml


class SequenceLoader(object):
    def __init__(self, filename: str):
        self._filename = filename
        with open(filename, 'r') as f:
            self._sequence = yaml.safe_load(f)

    def get(self, key):
        return self._sequence[key]

    def validate(self):
        """
        TODO: add marshmallow validation
        """
        return True


class SequenceExecutor(object):
    def __init__(self, sequence_loader: SequenceLoader, logger: logging.Logger):
        self._sequence_loader = sequence_loader
        self._context = self._initialize_context()
        self._context_proxy = ContextProxy(self._context)
        self._command_client = Client(context_proxy=self._context_proxy)
        self._logger = logger

    @property
    def logger(self):
        return self._logger

    def _initialize_context(self) -> Context:
        context = Context()
        context.step['http_session'] = requests.Session()
        context.templating['response'] = requests.Response()
        context.templating['variables'] = self._sequence_loader.get(
            'variables'
        )
        context.step['rendering'] = JinjaEvaluator(
            context.templating
        )
        return context

    def _get_base_http_parameters(self):
        base_url = self._sequence_loader.get('base_url')
        step_definition = self.context.step['definition']
        url = compose_url(
            base_url,
            self.context.step['definition']['url']
        )
        method = self.context.step['rendering'].render(
            step_definition.get('method', 'GET').upper()
        )
        url = self.context.step['rendering'].render(url)
        return {
            'url': url,
            'method': method
        }

    @property
    def context(self) -> Context:
        return self._context

    def on_before_request(self):
        request = HTTPRequest()
        request.update(**self._get_request_parameters())
        self.context.templating['request'] = request.prepare()
        self.context.step['phase'] = 'request'
        execute_plugins(self.context)

    def on_before_response(self):
        response = self._send_request()
        self.context.templating['response'] = response

    def on_after_response(self):
        self.logger.info(
            '[response] Completed HTTP request to URL: {}'.format(
                self.context.templating['response'].url
            )
        )
        self.context.step['phase'] = 'response'
        execute_plugins(self.context)

    def run(self):
        steps = deepcopy(self._sequence_loader.get('steps'))
        for step in steps:
            self.context.step['definition'] = step
            step.update({
                '_function': self._step_execution,
                '_args': (),
                '_kwargs': {}
            })
            self._command_client.run(step)

    def _step_execution(self):
        self.on_before_request()
        self.on_before_response()
        self.on_after_response()

    def _get_request_parameters(self):
        request_definition = self._sequence_loader.get('requests')
        parameters = self.context.step['rendering'].render_nested({
            key: value
            for key, value in chain(
                request_definition.items(),
                self.context.step['definition'].items()
            )
            if key not in KEYWORDS
        })
        base_http_parameters = self._get_base_http_parameters()
        parameters.update(base_http_parameters)
        return parameters

    def _send_request(self):
        request = self.context.templating['request']
        self.logger.info(
            '[request] Sending HTTP request to URL: {}'.format(
                request.url
            )
        )
        return self.context.step['http_session'].send(request)
