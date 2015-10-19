from __future__ import unicode_literals
from copy import deepcopy, copy
import six
from ..common.structures import ReadOnlyContainer, PitchDict
from ..templating.structures import PitchTemplate
from ..common.utils import compose_url
from ..plugins.structures import PluginCollection


class SchemeStepContext(object):
    STEP_KEYWORDS = [
        'plugins',
        'base_url',
        'when',
        'with_items',
        'with_indexed_items',
        'with_nested'
    ]
    DEFAULT_PLUGINS = [
        'assert_http_status_code',
        'response_as_json'
    ]

    def __init__(self, preprocessed_scheme):
        self._preprocessed_scheme = preprocessed_scheme
        self.step = None
        self.processed_step = None
        self.phase = None
        self.template_context = None
        self.renderer = None
        self._default_plugins = PluginCollection()
        for plugin_name in self.DEFAULT_PLUGINS:
            self._default_plugins.append(
                PitchDict(plugin=PitchTemplate(plugin_name))
            )

    @property
    def scheme(self):
        return copy(self._preprocessed_scheme)

    def add(self, parameter):
        setattr(self, parameter.name, parameter.value)
        if not parameter.is_system():
            if isinstance(self.template_context, PitchDict):
                self.template_context[parameter.name] = parameter.value
        return self

    def set_phase(self, name):
        from ..common.errors import InvalidPluginPhaseError
        if name not in ['request', 'response']:
            raise InvalidPluginPhaseError('Invalid Phase: {}'.format(name))
        self.add(ContextParameter(name='phase', value=name))

    def set_step(self, step_details):
        self.add(ContextParameter(name='step', value=step_details))
        self.analyze()

    def variable_resolver(self, key, default):
        return self.processed_step.get_first_from_multiple(
            key=key,
            other=self._preprocessed_scheme,
            default=default
        )

    def analyze(self):
        from ..plugins.utils import verify_plugins
        step_defaults = {
            'base_url': '',
            'url': '',
            'method': 'GET'
        }
        self.processed_step = PitchDict(deepcopy(self.step))
        self.processed_step.update({
            variable:
                self.variable_resolver(
                    key=variable,
                    default=default
                )
            for variable, default in six.iteritems(step_defaults)
        })
        for render_key in step_defaults.keys():
            self.processed_step.inplace_transform(
                render_key,
                self.renderer
            )
        base_url = self.processed_step['base_url']
        self.processed_step['url'] = compose_url(
            base_url,
            self.processed_step['url']
        )
        self.processed_step['method'] = self.processed_step['method'].upper()
        if 'plugins' not in self.processed_step:
            self.processed_step['plugins'] = copy(self._default_plugins)
        else:
            plugins = PluginCollection(list(self._default_plugins))
            plugins.extend(self.processed_step['plugins'])
            self.processed_step['plugins'] = plugins
        requested_plugin_names = [
            self.renderer(plugin_details['plugin'])
            for plugin_details in self.processed_step['plugins']
        ]
        verify_plugins(requested_plugin_names)

    def get_request_parameters(self):
        merged_request_parameters = self._preprocessed_scheme.get(
            'requests', PitchDict()
        ) + self.processed_step.remove_keys(*self.STEP_KEYWORDS)
        return self.renderer(merged_request_parameters)

    def __contains__(self, item):
        return hasattr(self, item)


class ContextParameter(ReadOnlyContainer):
    SYSTEM_PARAMETERS = (
        'renderer',
        'step',
        'progress',
        'instance',
        'step_plugins',
        'phase'
    )

    def __init__(self, name, value):
        super(ContextParameter, self).__init__(name=name, value=value)

    def is_system(self):
        return self.name in self.SYSTEM_PARAMETERS


class SchemeStepContextProxy(object):
    def __init__(self):
        self._step_context = None

    def set_context(self, step_context):
        self._step_context = step_context

    def get_context(self):
        return self._step_context
