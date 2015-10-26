from __future__ import unicode_literals
import inspect
import itertools
import re
import sys
from copy import deepcopy
import imp
import operator
import six
from ..common.errors import InvalidPluginPhaseError, UnknownPluginError
from ...plugins import PLUGINS, VALID_PHASES
from ..common.utils import stop_execution
from ..common.structures import PitchDict


def loader(request_plugins_modules=None, response_plugins_modules=None):
    if request_plugins_modules is not None:
        for module_path in request_plugins_modules:
            PLUGINS['request'].update(
                imp.load_source('_', module_path).exported_plugins
            )
    if response_plugins_modules is not None:
        for module_path in response_plugins_modules:
            PLUGINS['response'].update(
                imp.load_source('_', module_path).exported_plugins
            )


def verify_plugins(given_plugins):
        registered_plugin_names = set(
            itertools.chain.from_iterable([
                phase_plugins.keys()
                for phase_plugins in PLUGINS.values()
            ])
        )
        requested_plugin_names = set(given_plugins)
        if not requested_plugin_names.issubset(registered_plugin_names):
            raise UnknownPluginError(
                'Unregistered plugins: {}'.format(
                    ','.join(requested_plugin_names - registered_plugin_names)
                )
            )


def list_plugins():
    plugin_list = []
    for phase in sorted(PLUGINS.keys()):
        available_plugins = PLUGINS[phase]
        title = phase.title()
        plugin_list.append((None, '\n{}'.format(title)))
        plugin_list.append((None, '-' * len(title)))
        phase_plugin_list = []
        for name, plugin_class in six.iteritems(available_plugins):
            constructor_signature = inspect.getargspec(plugin_class.__init__)
            plugin_args = constructor_signature.args
            plugin_args.remove('self')
            if constructor_signature.defaults is not None:
                defaults = constructor_signature.defaults
                args_with_default = len(plugin_args) - len(defaults)
                for index, argument in enumerate(plugin_args):
                    if index >= args_with_default:
                        plugin_args[index] = '{}={}'.format(
                            argument,
                            defaults[index - args_with_default]
                        )
            if constructor_signature.keywords is not None:
                plugin_args.append(
                    '**{}'.format(constructor_signature.keywords)
                )
            docstring = re.sub(
                r'\s+',
                ' ',
                six.text_type(plugin_class.__doc__).strip().split("\n")[0]
            )
            phase_plugin_list.append(
                (
                    name,
                    '\n- {}({})\n  * {}'.format(
                        name, ', '.join(plugin_args),
                        docstring
                    )
                )
            )
        plugin_list.extend(
            sorted(phase_plugin_list, key=operator.itemgetter(0))
        )
    stop_execution(
        reporter=sys.stdout.write,
        message='{}\n'.format(
            '\n'.join(map(operator.itemgetter(1), plugin_list))
        ),
        exit_code=0
    )


def execute_plugins(step_context):
    step_plugins = step_context.processed_step.get('plugins')
    phase_plugins = PLUGINS[step_context.phase]
    step_phase_plugins = filter(
        lambda plugin_details:
            step_context.renderer(plugin_details.get('plugin'))
            in phase_plugins,
        step_plugins
    )
    if step_context.phase in VALID_PHASES:
        phase_object = getattr(step_context, step_context.phase)
    else:
        raise InvalidPluginPhaseError(
            'Invalid Phase: {}'.format(step_context.phase)
        )
    for plugin_execution_args in step_phase_plugins:
        phase_object.plugins.append(
            _execute_plugin(
                step_context=step_context,
                plugin_args=plugin_execution_args
            )
        )


def _execute_plugin(step_context, plugin_args):
    phase = step_context.phase
    plugin_execution_args = step_context.renderer(deepcopy(plugin_args))
    plugin_name = step_context.renderer(plugin_execution_args['plugin'])
    current_plugin_display_info = "[{}.plugins.{}]".format(
        phase,
        plugin_name
    )
    plugin_instance = PLUGINS[phase][plugin_name](
        **plugin_execution_args.remove_keys('plugin')
    )
    step_context.progress.info(
        "{} Executing ...".format(current_plugin_display_info)
    )
    plugin_instance.execute(step_context)
    step_context.progress.info(
        "{} Done".format(current_plugin_display_info)
    )
    return PitchDict({'plugin': plugin_name, 'instance': plugin_instance})
