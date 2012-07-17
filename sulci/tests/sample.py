# -*- coding: utf-8 -*-
"""
All tests regarding sulci.base.Sample class.
"""

import unittest

from sulci.base import Token, Sample

__all__ = ["SampleGenericTest", "SampleAppendTokenTest"]


class SampleGenericTest(unittest.TestCase):

    def test_should_create_a_sample(self):
        sample = Sample("xxx")
        self.assertTrue(isinstance(sample, Sample))


class SampleAppendTokenTest(unittest.TestCase):

    def test_should_append_token_and_update_its_position(self):
        sample = Sample("xxx")
        token = Token("yyy", original="bla")
        sample.append(token)
        self.assertIn(token, sample)
        self.assertEqual(token.parent, sample)
        other_token = Token("zzz", original="bleh")
        sample.append(other_token)
        self.assertIn(other_token, sample)
        self.assertEqual(other_token.parent, sample)
        self.assertEqual(other_token.position, 1)

    def test_should_raise_if_item_not_a_token(self):
        sample = Sample("xxx")
        self.assertRaises(ValueError, sample.append, "bla")

if __name__ == "__main__":
    unittest.main()
