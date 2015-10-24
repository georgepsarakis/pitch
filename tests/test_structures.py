#!/usr/bin/env python
from __future__ import unicode_literals
import unittest
import math
import os
from copy import deepcopy
from jinja2 import Template
import yaml
from pitch.lib.common.structures import InstanceInfo, ReadOnlyContainer
from pitch.lib.scheme.structures import SchemeLoader, PitchDict
from pitch.lib.templating.structures import (
    PitchTemplate,
    RecursiveTemplateRenderer,
    JinjaExpressionResolver
)
from pitch.lib.scheme.context import SchemeStepContext, ContextParameter


def get_sample_context():
    return {
        'a': 'test',
        'b': 1,
        'c': {
            'd': 'test2'
        },
        'e': 101
    }


def get_sample_scheme():
    scheme_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'json_api_schemes',
        'github-scheme.yml'
    )
    with open(scheme_file, 'r') as f:
        return yaml.load(f)


def get_scheme_loader():
    scheme_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'json_api_schemes',
        'github-scheme.yml'
    )
    return SchemeLoader(scheme_file)


class TestSchemeStepContext(unittest.TestCase):
    def setUp(self):
        self.scheme_loader = get_scheme_loader()
        self.scheme = self.scheme_loader.scheme
        self.scheme_step_context = SchemeStepContext(
            preprocessed_scheme=PitchDict(self.scheme)
        )
        self.scheme_step_context.template_context = PitchDict()
        self.renderer = RecursiveTemplateRenderer(
            self.scheme_step_context.template_context
        )

    def test_add(self):
        self.scheme_step_context.add(
            ContextParameter('prop1', 1)
        )
        self.assertTrue(
            hasattr(self.scheme_step_context, 'prop1')
        )
        self.assertEqual(self.scheme_step_context.prop1, 1)
        self.assertIn('prop1', self.scheme_step_context.template_context)

    def test_contains(self):
        self.scheme_step_context.add(ContextParameter('prop1', 1))
        self.assertIn('prop1', self.scheme_step_context)

    def test_get_request_parameters(self):
        from pitch.lib.common.utils import identity
        step = PitchDict(self.scheme['steps'][0])
        self.scheme_step_context.processed_step = PitchDict(step)
        self.scheme_step_context.renderer = identity
        self.assertDictEqual(
            dict(self.scheme_step_context.get_request_parameters()),
            {
                'headers': {'User-Agent': 'pitch-json-api-client-test'},
                'method': 'get',
                'params': {'per_page': 10},
                'url': '/users'
            }
        )

    def test_change_phase(self):
        from pitch.lib.plugins.utils import InvalidPluginPhaseError
        with self.assertRaises(InvalidPluginPhaseError):
            self.scheme_step_context.set_phase('test')
        for phase in ['request', 'response']:
            self.scheme_step_context.set_phase(phase)
            self.assertEqual(self.scheme_step_context.phase, phase)

    def test_analyze_step(self):
        step = PitchDict(self.scheme_loader.template_scheme['steps'][0])
        self.scheme_step_context.add(
            ContextParameter('renderer', self.renderer)
        )
        self.scheme_step_context.set_step(step)
        processed_step = self.scheme_step_context.processed_step
        response_plugin = processed_step['plugins'][0]['plugin'].as_string()
        self.assertEqual(
            response_plugin,
            'assert_http_status_code'
        )


class TestReadOnlyContainer(unittest.TestCase):
    def test_container(self):
        container = ReadOnlyContainer(a=1, b=2)
        self.assertListEqual(
            [container.a, container.b],
            [1, 2]
        )
        with self.assertRaises(AttributeError):
            container.c


class TestInstanceInfo(unittest.TestCase):
    def test_instance_info(self):
        instance_info = InstanceInfo(
            loop_id=30,
            threads=8,
            process_id=4
        )
        self.assertListEqual(
            [
                instance_info.process_id,
                instance_info.thread_id,
                instance_info.loop_id
            ],
            [4, 7, 31]
        )


class TestPitchDict(unittest.TestCase):
    def setUp(self):
        self.pitch_dict = PitchDict({
            'a': 1,
            'b': range(10),
            'c': {
                'd': 2
            }
        })

    def test_get_any_of(self):
        self.assertTupleEqual(
            self.pitch_dict.get_any_item_by_key('z', 'a'),
            ('a', 1)
        )
        self.assertTupleEqual(
            self.pitch_dict.get_any_item_by_key('z', 'x'),
            (None, None)
        )
        self.assertTupleEqual(
            self.pitch_dict.get_any_item_by_key('z', 'x', default=10),
            (None, 10)
        )

    def test_get_first_from_multiple(self):
        other_dict = {
            'x': 10,
            'z': 11
        }
        other_dict2 = {'y': 12}
        fn = self.pitch_dict.get_first_from_multiple
        self.assertEqual(fn('x', other_dict), 10)
        self.assertEqual(fn('y', (other_dict, other_dict2)), 12)
        self.assertEqual(fn('a', other_dict), 1)
        self.assertEqual(fn('y', other_dict, 100), 100)

    def test_remove_keys(self):
        modified_dict = self.pitch_dict.remove_keys('a')
        self.assertNotEqual(
            id(modified_dict),
            id(self.pitch_dict)
        )
        self.assertIsInstance(modified_dict, PitchDict)
        self.assertDictEqual(
            {
                key: self.pitch_dict[key]
                for key in self.pitch_dict if key != 'a'
            },
            dict(modified_dict)
        )

    def test_nested_get(self):
        self.assertIsNone(self.pitch_dict.nested_get('a.z', default=None))
        self.assertEqual(self.pitch_dict.nested_get('a'), 1)
        self.assertEqual(self.pitch_dict.nested_get('c.d'), 2)
        self.assertEqual(self.pitch_dict.nested_get('b.3'), 3)

    def test_inplace_transform(self):
        self.pitch_dict.inplace_transform('b', sum)
        self.assertEqual(self.pitch_dict['b'], 45)
        self.pitch_dict['e'] = 2
        self.pitch_dict.inplace_transform('e', math.pow, 3)
        self.assertEqual(self.pitch_dict['e'], 8)
        with self.assertRaises(KeyError):
            self.pitch_dict.inplace_transform('x', lambda x: x)

    def test_add(self):
        pitch_dict_2 = PitchDict([('a', 2), ('e', 100)])
        new_pitch_dict = self.pitch_dict + pitch_dict_2
        self.assertNotEqual(id(new_pitch_dict), id(self.pitch_dict))

    def test_iadd(self):
        pitch_dict_2 = PitchDict([('a', 2), ('e', 100)])
        self.pitch_dict += pitch_dict_2
        self.assertEqual(self.pitch_dict['a'], 2)
        self.assertEqual(self.pitch_dict['e'], 100)


class TestPitchTemplate(unittest.TestCase):
    def test_methods(self):
        template_string = 'Test #{{ number }}'
        template = PitchTemplate(template_string)
        self.assertIsInstance(template._template, Template)
        self.assertNotEqual(
            id(template),
            id(deepcopy(template))
        )
        self.assertEqual(
            template.as_string(),
            template_string
        )


class TestRecursiveTemplateRenderer(unittest.TestCase):
    def setUp(self):
        self.context = get_sample_context()
        self.template = PitchTemplate('{{ a }}')
        self.structure_dict_template = {
            'a': PitchTemplate('{{ a }}'),
            'b': {
                'c': PitchTemplate('{{ b + 2 }}')
            }
        }
        self.structure_list_template = [
            PitchTemplate('{{ b + 1 }}'),
            PitchTemplate('{{ e + 1 }}')
        ]
        self.renderer = RecursiveTemplateRenderer(self.context)

    def test_attributes(self):
        self.assertDictEqual(
            self.context,
            self.renderer.context
        )

    def test_render(self):
        self.assertEqual(self.renderer(self.template), 'test')
        self.assertEqual(
            self.renderer(self.template),
            self.renderer.render(self.template)
        )
        self.assertDictEqual(
            self.renderer(self.structure_dict_template),
            {
                'a': 'test',
                'b': {
                    'c': '3'
                }
            }
        )
        self.assertListEqual(
            self.renderer(self.structure_list_template),
            ['2', '102']
        )


class MockSchemeStepContext(object):
    def __init__(self, context):
        self.scheme = get_sample_scheme()
        self.renderer = RecursiveTemplateRenderer(template_context=context)
        self.template_context = PitchDict(context)


class TestJinjaExpressionResolver(unittest.TestCase):
    def setUp(self):
        self.context = get_sample_context()
        self.step_context = MockSchemeStepContext(self.context)
        self.interpreter = JinjaExpressionResolver(self.step_context)

    def test_interpretation(self):
        self.assertEqual(
            '{{ a }}',
            self.interpreter(PitchTemplate('a')).as_string()
        )
        self.assertEqual(
            'test',
            self.interpreter('a')
        )
        self.assertEqual(
            'test2',
            self.interpreter(PitchTemplate('c.d')).render(**self.context)
        )

if __name__ == "__main__":
    unittest.main(verbosity=2, failfast=True)
