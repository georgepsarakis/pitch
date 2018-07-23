from copy import deepcopy
import inspect
import importlib
import itertools
import logging
import re

from pitch.exceptions import InvalidPluginPhaseError, UnknownPluginError
from pitch.plugins.structures import registry
from pitch.plugins.request import BaseRequestPlugin
from pitch.plugins.response import BaseResponsePlugin

logger = logging.getLogger(__name__)


def loader(request_plugins_modules=None, response_plugins_modules=None):
    if request_plugins_modules is not None:
        for module_path in request_plugins_modules:
            _import_plugins(module_path)

    if response_plugins_modules is not None:
        for module_path in response_plugins_modules:
            _import_plugins(module_path)

    return {
        'request': registry.add_subclasses(BaseRequestPlugin),
        'response': registry.add_subclasses(BaseResponsePlugin)
    }


def _import_plugins(from_path):
    return importlib.import_module(
        from_path.replace('.', '_'),
        from_path
    )


def verify_plugins(given_plugins):
    registered_plugin_names = set()
    for phase in registry.phases:
        registered_plugin_names.union(set(
            itertools.chain.from_iterable([
                phase_plugins.keys()
                for phase_plugins in registry.by_phase(phase).values()
            ])
        ))

    requested_plugin_names = set(given_plugins)
    if not requested_plugin_names.issubset(registered_plugin_names):
        raise UnknownPluginError(
            'Unregistered plugins: {}'.format(
                ','.join(requested_plugin_names - registered_plugin_names)
            )
        )


def list_plugins():
    plugins = {}
    for phase, available_plugins in sorted(registry.all().items()):
        phase_plugins = plugins.setdefault(phase, {})

        for name, plugin_class in available_plugins.items():
            plugin_specification = phase_plugins.setdefault(name, {})
            constructor_signature = inspect.getfullargspec(
                plugin_class.__init__
            )
            plugin_specification['arguments'] = []

            plugin_args = constructor_signature.args
            plugin_args.remove('self')
            if constructor_signature.defaults is not None:
                defaults = constructor_signature.defaults
                args_with_default = len(plugin_args) - len(defaults)
                for index, argument in enumerate(plugin_args):
                    plugin_specification['arguments'].append(
                        {'name': argument}
                    )
                    if index >= args_with_default:
                        plugin_specification['arguments'][-1]['default'] = \
                            defaults[index - args_with_default]

            if constructor_signature.varkw is not None:
                plugin_specification['arguments'].append(
                    {'name': '**{}'.format(constructor_signature.varkw)}
                )

            plugin_specification['docstring'] = re.sub(
                r'\s+',
                ' ',
                str(plugin_class.__doc__).strip().split("\n")[0]
            )
    return plugins


def execute_plugins(context):
    step_plugins = context.step['definition'].get('plugins')
    phase_plugins = registry.by_phase(context.step['phase'])
    step_phase_plugins = filter(
        lambda plugin_details:
        plugin_details.get('plugin')
        in phase_plugins,
        step_plugins
    )
    _valid_phase_or_raise(context.step['phase'])

    phase_object = context.templating[context.step['phase']]

    phase_object.plugins = []
    for plugin_execution_args in step_phase_plugins:
        phase_object.plugins.append(
            _execute_plugin(
                context=context,
                plugin_args=plugin_execution_args
            )
        )


def _valid_phase_or_raise(name):
    if name not in registry.phases:
        raise InvalidPluginPhaseError('Invalid Phase: {}'.format(name))


def _execute_plugin(context, plugin_args):
    phase = context.step['phase']
    renderer = context.step['rendering'].render_nested
    plugin_execution_args = renderer(
        deepcopy(plugin_args)
    )
    plugin_name = renderer(plugin_execution_args['plugin'])
    current_plugin_display_info = "plugin={}.plugins.{}".format(
        phase,
        plugin_name
    )
    plugin_instance = registry.by_phase(phase)[plugin_name](
        **{key: value
           for key, value in plugin_execution_args.items()
           if key != 'plugin'}
    )
    logger.info(
        "{} status={}".format(current_plugin_display_info, 'running')
    )
    plugin_instance.execute(context)
    logger.info(
        "{} status={}".format(current_plugin_display_info, 'done')
    )
    return {'plugin': plugin_name, 'instance': plugin_instance}
