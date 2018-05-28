from jinja2 import Environment, Undefined
from requests.structures import CaseInsensitiveDict
from boltons.typeutils import make_sentinel

from pitch.templating.jinja_custom_extensions import \
    get_registered_filters, get_registered_tests

from requests import Request
from argparse import Namespace


KEYWORDS = (
    'plugins',
    'base_url',
    'when',
    'with_items',
    'with_indexed_items',
    'with_nested',
    'use_default_plugins',
    'use_scheme_plugins'
)

DEFAULT_PLUGINS = (
    CaseInsensitiveDict(plugin='assert_http_status_code'),
    CaseInsensitiveDict(plugin='response_as_json')
)


class HTTPRequest(Request):
    def __init__(self, *args, **kwargs):
        super(HTTPRequest, self).__init__(*args, **kwargs)
        self.__pitch_properties = Namespace()

    @property
    def pitch_properties(self):
        return self.__pitch_properties

    def update(self, **kwargs):
        for property_name, value in kwargs.items():
            setattr(self.__pitch_properties, property_name, value)
            setattr(self, property_name, value)


class Context(CaseInsensitiveDict):
    def __init__(self, *args, **kwargs):
        super(Context, self).__init__(*args, **kwargs)
        self.setdefault(
            'globals',
            CaseInsensitiveDict(
                failfast=True
            )
        )
        self.setdefault(
            'templating',
            CaseInsensitiveDict(
                variables=CaseInsensitiveDict(),
                response=None,
                request=None
            )
        )
        self.setdefault(
            'step',
            CaseInsensitiveDict(
                rendering=None,
                http_session=None,
                definition=None
            )
        )

    @property
    def globals(self):
        return self['globals']

    @property
    def templating(self):
        return self['templating']

    @property
    def step(self):
        return self['step']


class ContextProxy(object):
    def __init__(self, context: Context):
        self._context = context

    @property
    def context(self):
        """
        :rtype: Context
        """
        return self._context

    @context.setter
    def context(self, value: Context):
        self._context = value


class JinjaEvaluator(object):
    _MISSING = make_sentinel()

    def __init__(self, context: Context):
        self._context = context
        self._environment = Environment()
        self._environment.filters.update(get_registered_filters())
        self._environment.tests.update(get_registered_tests())

    def get(self, expression: str, default=None):
        """
        Evaluate a Jinja expression and return the corresponding
        Python object.
        """
        expression = expression.strip().lstrip('{').rstrip('}').strip()
        environment = Environment()
        expression = environment.compile_expression(
            expression,
            undefined_to_none=False
        )
        value = expression(**self._context)

        if isinstance(value, Undefined):
            return default
        else:
            return value

    def render(self, expression, default=_MISSING):
        if isinstance(expression, str):
            expression = self._environment.from_string(expression)
            value = expression.render(**self._context)
        else:
            value = expression

        if isinstance(value, Undefined):
            if default is self._MISSING:
                # TODO: add custom exception
                raise RuntimeError('expression can not be rendered')
            else:
                return default
        else:
            return value

    def render_nested(self, structure, default=_MISSING):
        if isinstance(structure, (CaseInsensitiveDict, dict)):
            iterator = structure.items()
        elif isinstance(structure, (list, tuple)):
            iterator = enumerate(structure)
        else:
            return self.render(structure, default)

        for key, value in iterator:
            structure[key] = self.render_nested(value, default)

        return structure
