# -*- coding: utf-8 -*-
"""
All tests regarding sulci.base.Token class.
"""

from django.test import TestCase

from sulci.base import Token, Sample

__all__ = [
    "TokenTest", 
    "TokenIsStrongPunctuationTest", 
    "TokenGetNeighborsTest", 
    'TokenNeighborsBigramTest'
]

class TokenTest(TestCase):
    
    def test_should_create_a_token(self):
        token = Token("mot", original="mot")
        self.assertTrue(isinstance(token, Token))

class TokenIsStrongPunctuationTest(TestCase):
    
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

class InSampleTokenBaseTest(TestCase):
    
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
