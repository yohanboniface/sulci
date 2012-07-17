# -*- coding: utf-8 -*-
"""
All tests regarding sulci.base.Token class.
"""

import unittest

from sulci.base import Token, Sample
from sulci.textmining import Stemm

__all__ = [
    "TokenInitTest",
    "TokenIsStrongPunctuationTest",
    "TokenGetNeighborsTest",
    'TokenNeighborsBigramTest',
    'TokenComparisonTests',
]


class TokenInitTest(unittest.TestCase):

    def test_should_create_a_token(self):
        token = Token("mot", original="mot")
        self.assertTrue(isinstance(token, Token))

    def test_should_define_verified_tag_and_lemme(self):
        token = Token("xxx", original="mots/SBC:sg/mot")
        self.assertEqual(token.verified_tag, "SBC:sg")
        self.assertEqual(token.verified_lemme, "mot")

    def test_should_define_default_verified_lemme(self):
        token = Token("xxx", original="mot/SBC:sg")
        self.assertEqual(token.verified_tag, "SBC:sg")
        self.assertEqual(token.verified_lemme, "mot")


class TokenIsStrongPunctuationTest(unittest.TestCase):

    def test_period_is_strong_punctuation(self):
        token = Token("xxx", ".")
        self.assertTrue(token.is_strong_punctuation())

    def test_question_mark_is_strong_punctuation(self):
        token = Token("xxx", "?")
        self.assertTrue(token.is_strong_punctuation())

    def test_exclamation_point_is_strong_punctuation(self):
        token = Token("xxx", "!")
        self.assertTrue(token.is_strong_punctuation())

    def test_comma_is_not_strong_punctuation(self):
        token = Token("xxx", ",")
        self.assertFalse(token.is_strong_punctuation())


class InSampleTokenBaseTest(unittest.TestCase):

    def setUp(self):
        sentence = Sample("sample")
        self.first = Token("one", "Une")
        sentence.append(self.first)
        self.second = Token("two", "phrase")
        sentence.append(self.second)
        self.third = Token("three", "simple")
        sentence.append(self.third)


class TokenGetNeighborsTest(InSampleTokenBaseTest):

    def test_should_return_neighbors(self):
        neighbors = self.second.get_neighbors(-1, 1)
        self.assertEqual(neighbors[0], self.first)
        self.assertEqual(neighbors[1], self.third)
        neighbors = self.first.get_neighbors(1, 2)
        self.assertEqual(neighbors[0], self.second)
        self.assertEqual(neighbors[1], self.third)
        neighbors = self.third.get_neighbors(-1, -2)
        self.assertEqual(neighbors[0], self.second)
        self.assertEqual(neighbors[1], self.first)

    def test_should_return_empty_list(self):
        # When not all the neighbors asked are available, it returns an empty list
        neighbors = self.second.get_neighbors(1, 2)
        self.assertEqual(neighbors, [])


class TokenNeighborsBigramTest(InSampleTokenBaseTest):

    def test_should_get_previous_bigram(self):
        self.assertEqual(self.third.previous_bigram, [self.first, self.second])

    def test_should_not_get_previous_bigram(self):
        # There is no previous bigram
        self.assertEqual(self.second.previous_bigram, None)

    def test_should_get_next_bigram(self):
        self.assertEqual(self.first.next_bigram, [self.second, self.third])

    def test_should_not_get_next_bigram(self):
        # There is no next bigram
        self.assertEqual(self.second.next_bigram, None)


class TokenComparisonTests(unittest.TestCase):

    def test_could_compare_with_other_token(self):
        token1 = Token("xxx", original="bla")
        token2 = Token("yyy", original="bla")
        token3 = Token("yyy", original="bleh")
        self.assertTrue(token1 == token2)
        self.assertTrue(token2 == token1)
        self.assertFalse(token1 == token3)
        self.assertFalse(token3 == token1)

    def test_could_compare_with_string(self):
        token = Token("xxx", original="bla")
        self.assertTrue(token == "bla")
        self.assertTrue("bla" == token)
        self.assertFalse(token == "bleh")

    def test_could_compare_a_stemme(self):
        token1 = Token("xxx", original="bla")
        token2 = Token("yyy", original="bla")
        token3 = Token("aaa", original="bleh")
        stemme1 = Stemm("zzz", text=None)
        stemme2 = Stemm("bbb", text=None)
        stemme1.occurrences.append(token1)
        stemme2.occurrences.append(token3)
        # We can only make the comparison with token before
        # See Token.__eq__ and Stemm.__eq__ for details
        self.assertTrue(token2 == stemme1)
        self.assertFalse(token2 == stemme2)

if __name__ == "__main__":
    unittest.main()
