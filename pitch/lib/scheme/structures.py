from __future__ import unicode_literals, print_function
from copy import deepcopy
import requests
import six
import yaml
from ..plugins.utils import execute_plugins
from ..plugins.structures import PluginCollection
from ..templating.structures import PitchTemplate, RecursiveTemplateRenderer
from ..common.structures import PitchDict, PitchRequest
from ..scheme.context import (
    SchemeStepContext,
    SchemeStepContextProxy,
    ContextParameter
)
from ..common.display import ProgressLog
from ..logic.command import (
    ControlFlowCommand,
    StepCommand,
    CommandClient,
    CommandInvoker
)
from ..logic.control_flow import Loop, Conditional


class SchemeLoader(object):
    def __init__(self, filename):
        self._filename = filename
        with open(filename, 'r') as f:
            self._scheme = yaml.safe_load(f)
        self._template_scheme = PitchDict(
            self._recursive_scheme_conversion(
                deepcopy(self._scheme)
            )
        )
        self._scheme = PitchDict(self._scheme)

    @property
    def scheme(self):
        return self._scheme

    @property
    def template_scheme(self):
        return self._template_scheme

    def _recursive_scheme_conversion(self, sub_tree, parent=None, key=None):
        if isinstance(sub_tree, list):
            iterable = enumerate(sub_tree)
            parent = sub_tree
        elif isinstance(sub_tree, dict):
            if parent is not None:
                parent[key] = PitchDict(sub_tree)
            iterable = six.iteritems(sub_tree)
            parent = sub_tree
        else:
            if isinstance(sub_tree, six.string_types):
                return PitchTemplate(sub_tree)
            else:
                return sub_tree
        for key, value in iterable:
            sub_tree[key] = self._recursive_scheme_conversion(
                value,
                key=key,
                parent=parent
            )
        if isinstance(sub_tree, dict):
            return PitchDict(sub_tree)
        else:
            return sub_tree


class SchemeExecutor(object):
    def __init__(self, scheme_loader, instance):
        self._instance = instance
        self._scheme_loader = scheme_loader
        self._step_context = None
        self._progress = ProgressLog(instance=self._instance)
        self._progress.important('Initializing scheme execution ...')
        self._template_context = PitchDict({
            "variables": self._scheme_loader.template_scheme.get(
                'variables',
                {}
            ),
            "response": requests.Response(),
            "request": None
        })
        self._renderer = RecursiveTemplateRenderer(self._template_context)
        self._session = requests.Session()
        self._step_context_proxy = SchemeStepContextProxy()

    @property
    def template_context(self):
        return self._template_context

    def _set_context(self, step):
        step_context = SchemeStepContext(self._scheme_loader.template_scheme)
        context_variables = (
            {'name': 'step', 'value': step},
            {'name': 'renderer', 'value': self._renderer},
            {'name': 'progress', 'value': self._progress},
            {'name': 'instance', 'value': self._instance},
            {'name': 'template_context', 'value': self._template_context},
            {'name': 'session', 'value': self._session}
        )
        for context_variable_args in context_variables:
            step_context.add(ContextParameter(**context_variable_args))
        step_context.set_step(step)
        self._step_context_proxy.set_context(step_context)

    def _initialize_response_array(self, value):
        if 'response_array' not in self._step_context_proxy.get_context():
            self._step_context_proxy.get_context().add(
                ContextParameter(name='response_array', value=value)
            )

    def _create_scheme_commands(self, steps):
        client = CommandClient(CommandInvoker())
        for step in steps:
            client.receive(StepCommand())
            client.get_last().add_instruction(self._set_context, step)

            loop = Loop(self._step_context_proxy)
            loop_command = ControlFlowCommand(loop)

            conditional = Conditional(self._step_context_proxy)
            conditional_command = ControlFlowCommand(conditional)

            loop_command.add_sub_command(conditional_command)
            client.receive(loop_command)

            inner_loop_commands = StepCommand()
            conditional_command.add_sub_command(inner_loop_commands)
            inner_loop_commands.add_instruction(
                lambda phase:
                    self._step_context_proxy.get_context().set_phase(phase),
                'request'
            )
            inner_loop_commands.add_instruction(self._process_request)
            inner_loop_commands.add_instruction(
                lambda phase:
                    self._step_context_proxy.get_context().set_phase(phase),
                'response'
            )
            inner_loop_commands.add_instruction(
                lambda current_loop:
                    self._initialize_response_array([])
                    if current_loop.is_effective()
                    else self._initialize_response_array(None),
                loop
            )
            inner_loop_commands.add_instruction(self._process_response)
        return client

    def execute_scheme(self):
        scheme = self._scheme_loader.template_scheme
        client = self._create_scheme_commands(deepcopy(scheme['steps']))
        client.invoke()
        self._progress.important('Scheme completed successfully')

    def _process_request(self):
        step_context = self._step_context_proxy.get_context()
        step_context.analyze()
        request = PitchRequest()
        request.plugins = PluginCollection()
        step_context.add(ContextParameter(name='request', value=request))
        execute_plugins(step_context=step_context)
        request.update(**step_context.get_request_parameters())
        step_context.progress.info(
            message='[request] Preparing request to URL: {}'.format(
                step_context.request.url
            )
        )
        executed_plugins = request.plugins
        request = request.prepare()
        request.plugins = executed_plugins
        step_context.add(ContextParameter(name='request', value=request))
        self._send_request()

    def _send_request(self):
        step_context = self._step_context_proxy.get_context()
        step_context.progress.info(
            message='[request] Sending request to URL: {}'.format(
                step_context.request.url
            )
        )
        response = step_context.session.send(step_context.request)
        step_context.add(ContextParameter(name='response', value=response))

    def _process_response(self):
        step_context = self._step_context_proxy.get_context()
        step_context.response.plugins = step_context.request.plugins
        step_context.add(
            ContextParameter(name='response', value=step_context.response)
        )
        if step_context.response_array is not None:
            step_context.response_array.append(step_context.response)
        execute_plugins(step_context=step_context)
