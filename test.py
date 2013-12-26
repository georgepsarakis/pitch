#!/usr/bin/python
import unittest
from pitch import Pitch, PitchInvalidSetting, PitchConfigurationRequired
from difflib import SequenceMatcher
import yaml

class TestPitch(unittest.TestCase):
  def test_initialize(self):
    ''' Initialization tests '''
    self.assertRaises(PitchInvalidSetting, Pitch, False)
    P = Pitch(False, url='google.com')
    self.assertIsInstance(P.URLS, list)
    self.assertListEqual(P.URLS, ['http://google.com'])
    self.assertIsInstance(P.ELEMENTS, dict)
    self.assertIsInstance(P.DATA, dict)
    self.assertIsInstance(P.HEADERS, dict)
    self.assertIsInstance(P.OUTPUT, dict)
    self.assertIsInstance(P.HEADERS, dict)
    self.assertIsInstance(P.DIFFER, dict)
    self.assertIsNone(P.REDIS)

  def test_similarity(self):
    P = Pitch(False, url='google.com')
    test_string_1 = """Lorem Ipsum is simply   dummy text of the printing and   typesetting industry. 
    Lorem Ipsum has been the industry's    standard dummy text    ever since the 1500s, 
    when an unknown printer       took a galley    of type and scrambled   it to make a type specimen    book. 
    It has survived not only         five centuries, 
    but also the leap into electronic typesetting, remaining essentially unchanged."""
    test_string_2 = """Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged."""
    self.assertTupleEqual(P.similarity(test_string_1, test_string_2), (True, 1.))

  def test_sample_yaml(self):
    ''' Test sample configuration files for valid YAML '''
    for config in ['diff', 'benchmark', 'fetch']:
      with open('./sample.%s.yml' % config, 'r') as f:
        yaml.load("".join(f.readlines()))

  def test_ternary(self):
    self.assertIsNone(Pitch.ternary(1>2, 0))
    self.assertEqual(Pitch.ternary(1>2, 0, 2), 2)
    self.assertEqual(Pitch.ternary(3>2, 1), 1)

  def test_getdefault(self):
    test_list = [ 1, 2 ]
    test_dict = { 'a' : 1, 'b' : 2 }
    self.assertIsNone(Pitch.getdefault(test_dict, 'c'))
    self.assertEqual(Pitch.getdefault(test_dict, 'c', 5), 5)
    self.assertEqual(Pitch.getdefault(test_dict, 'a', 0), 1)
    self.assertIsNone(Pitch.getdefault(test_list, 3))
    self.assertEqual(Pitch.getdefault(test_list, 0), 1)

if __name__ == "__main__":
  unittest.main(verbosity=2, buffer=True, failfast=True)
