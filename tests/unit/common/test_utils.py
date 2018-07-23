from unittest import TestCase

from pitch.common.utils import merge_dictionaries


class TestUtils(TestCase):
    def test_merge_dictionaries(self):
        self.assertDictEqual(
            merge_dictionaries(
                {'a': {'b': 1}, 'c': 3, 'e': 10},
                {'a': {'b': 2, 'd': 4}, 'c': 3},
            ),
            {'a': {'b': 2, 'd': 4}, 'c': 3, 'e': 10}
        )
