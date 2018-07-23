import itertools

import yaml

from boltons.typeutils import get_all_subclasses


def get_loop_classes():
    return get_all_subclasses(Loop)


class Command(object):
    def __init__(self, fn):
        self._fn = fn

    def execute(self, *args, **kwargs):
        return self._fn(*args, **kwargs)


class ControlFlowStatement(object):
    __keyword__ = None
    __default__ = None

    def __init__(self, context_proxy):
        self._name = self.__class__.__name__.lower()
        self._context_proxy = context_proxy

    @property
    def context(self):
        return self._context_proxy.context

    @property
    def keyword(self):
        return self.__keyword__

    @property
    def default(self):
        return self.__default__

    @property
    def name(self):
        return self._name

    def is_defined(self, instruction):
        return instruction.get(self.keyword) is not None


class Conditional(ControlFlowStatement):
    __keyword__ = 'when'
    __default__ = 'true'

    def _parse(self, expression):
        return yaml.safe_load(
            self.context.step['rendering'].render(expression)
        )

    def evaluate(self, expression):
        if isinstance(expression, bool):
            return expression
        else:
            return self._parse(expression)


class Loop(ControlFlowStatement):
    def __init__(self, *args, **kwargs):
        self._keyword_prefix = 'with_'
        self._items = None
        super(Loop, self).__init__(*args, **kwargs)

    @property
    def items(self):
        return self._items

    @items.setter
    def items(self, iterable):
        self._items = iterable


class Simple(Loop):
    __keyword__ = 'items'

    @property
    def keyword(self):
        return '{}{}'.format(self._keyword_prefix, self.__keyword__)

    def iterate(self):
        for item in self.items:
            yield item


class Indexed(Simple):
    __keyword__ = 'indexed_items'

    @property
    def keyword(self):
        return '{}{}'.format(self._keyword_prefix, self.__keyword__)

    def iterate(self):
        return enumerate(super(Indexed, self).iterate())


class Nested(Loop):
    __keyword__ = 'nested'

    @property
    def keyword(self):
        return '{}{}'.format(self._keyword_prefix, self.__keyword__)

    def evaluate(self):
        for item in itertools.product(*self.items):
            yield item


class Client(object):
    def __init__(self, context_proxy):
        self._context_proxy = context_proxy

    @property
    def context(self):
        return self._context_proxy.context

    def run(self, instruction):
        results = []

        for item in self._generate_loop(instruction).iterate():
            self._set_loop_variable(item)
            if self._evaluate_conditional(instruction):
                result = Command(fn=instruction['_function']).execute(
                    *instruction['_args'],
                    **instruction['_kwargs']
                )
                results.append(result)

        return results

    def _generate_loop(self, instruction):
        for loop_class in get_loop_classes():
            loop = loop_class(self._context_proxy)
            if loop.is_defined(instruction):
                loop.items = self._read_loop_items(loop, instruction)
                return loop

        default = Simple(self._context_proxy)
        default.items = [None]
        return default

    def _read_loop_items(self, loop, instruction):
        loop_items = self.context.step['rendering'].get(
            instruction[loop.keyword]
        )
        loop_items = self.context.step['rendering'].get(loop_items)

        return loop_items

    def _evaluate_conditional(self, instruction) -> Conditional:
        conditional = Conditional(context_proxy=self._context_proxy)
        expression = instruction.get(conditional.keyword, conditional.default)
        return conditional.evaluate(expression)

    def _set_loop_variable(self, item):
        self.context.templating['item'] = item
        return item
