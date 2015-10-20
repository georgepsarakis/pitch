from __future__ import unicode_literals
import itertools
import yaml
from ..common.utils import to_iterable
from ..templating.structures import PitchTemplate, JinjaExpressionResolver


class ControlFlowStatement(object):
    def __init__(self, statement_type):
        self.__statement_type = statement_type

    @property
    def type(self):
        return self.__statement_type


class Conditional(ControlFlowStatement):
    def __init__(self, step_context_proxy):
        self.__step_context_proxy = step_context_proxy
        self.__conditional_default = PitchTemplate('true')
        self.__expression = None
        self.__value = None
        super(Conditional, self).__init__('conditional')

    def __reinitialize(self):
        self.__expression = None
        self.__value = None

    @property
    def value(self):
        return self.__value

    @property
    def expression(self):
        return self.__expression

    def evaluate(self):
        self.__reinitialize()
        context = self.__step_context_proxy.get_context()
        default = self.__conditional_default
        step_conditional = context.step.get('when', default)
        if isinstance(step_conditional, bool):
            evaluated_value = step_conditional
            self.__expression = str(step_conditional)
        else:
            resolver = JinjaExpressionResolver(step_context=context)
            resolved_value = resolver(step_conditional)
            evaluated_value = yaml.safe_load(context.renderer(resolved_value))
            self.__expression = step_conditional.as_string()
        self.__value = evaluated_value
        return self.__value


class Loop(ControlFlowStatement):
    def __init__(self, step_context_proxy):
        self.__step_context_proxy = step_context_proxy
        self.__items = None
        self.__command_iterable = None
        self.__command = None
        self.__command_details = None
        super(Loop, self).__init__('loop')

    def __reinitialize(self):
        self.__items = None

    def is_effective(self):
        return self.__command is not None

    @property
    def items(self):
        return self.__command_iterable

    @property
    def command(self):
        return self.__command

    def set_loop_variable(self, item):
        active_context = self.__step_context_proxy.get_context()
        active_context.template_context['item'] = item
        return item

    def evaluate(self):
        self.__reinitialize()
        step_context = self.__step_context_proxy.get_context()
        step = step_context.step
        loop_command_key, loop_command_details = step.get_any_item_by_key(
            'with_items',
            'with_indexed_items',
            'with_nested'
        )
        loop_command_details = to_iterable(loop_command_details)
        if loop_command_key is None:
            with_items_iterable = [(None,)]
        else:
            loop_command_details = map(
                step_context.renderer,
                loop_command_details
            )
            with_items_iterable = filter(
                None,
                list(
                    itertools.product(
                        *filter(
                            None,
                            map(
                                step_context.template_context.nested_get,
                                loop_command_details
                            )
                        )
                    )
                )
            )
            if loop_command_key == 'with_indexed_items':
                with_items_iterable = enumerate(with_items_iterable)
        self.__command_iterable = map(
            lambda item: item if len(item) > 1 else item[0],
            with_items_iterable
        )
        self.__command = loop_command_key
        self.__command_details = loop_command_details
