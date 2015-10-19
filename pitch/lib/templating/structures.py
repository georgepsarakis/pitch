from __future__ import unicode_literals
import uuid
import collections
from jinja2 import Template
import six
from ..common.structures import PitchDict
from .jinja_custom_filters import filters, tests


class PitchTemplate(Template):
    def __init__(self, template_string):
        self._template_string = template_string
        super(PitchTemplate, self).__new__(Template, template_string)
        self.environment.filters.update(filters)
        self.environment.tests.update(tests)

    def __deepcopy__(self, _):
        return PitchTemplate(self._template_string)

    def __str__(self):
        return '<PitchTemplate:{}>'.format(self.as_string())

    def as_string(self):
        return self._template_string


class RecursiveTemplateRenderer(object):
    def __init__(self, template_context):
        self._template_context = template_context

    @property
    def context(self):
        return self._template_context

    def render(self, structure):
        return self(structure)

    def __call__(self, structure):
        if isinstance(structure, (list, collections.MutableSequence)):
            iterable = enumerate(structure)
        elif isinstance(structure, (PitchDict, dict)):
            iterable = six.iteritems(structure)
        elif isinstance(structure, PitchTemplate):
            return structure.render(**self._template_context)
        else:
            return structure
        for key, value in iterable:
            structure[key] = self(value)
        return structure


class JinjaExpressionResolver(object):
    def __init__(self, step_context):
        self._step_context = step_context

    def __call__(self, value):
        if isinstance(value, PitchTemplate):
            if '{{' not in value.as_string():
                value = PitchTemplate('{{ %s }}' % value.as_string())
        elif isinstance(value, six.string_types):
            default = str(uuid.uuid4())
            stored_value = self._step_context.template_context.nested_get(
                key=value,
                default=default
            )
            if stored_value != default:
                value = stored_value
        return value