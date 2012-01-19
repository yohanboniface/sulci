# -*- coding: utf-8 -*-
"""
All tests regarding sulci.base.Token class.
"""

from django.test import TestCase

from sulci.base import Token, Sample

__all__ = ["TokenTest", "TokenIsStrongPunctuationTest", "TokenGetNeighborsTest"]

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

class TokenGetNeighborsTest(TestCase):
    
    def setUp(self):
        sentence = Sample("sample")
        first = Token("one", "Une", parent=sentence, position=0)
        sentence.tokens.append(first)
        second = Token("two", "phrase", parent=sentence, position=1)
        sentence.tokens.append(second)
        third = Token("three", "simple", parent=sentence, position=2)
        sentence.tokens.append(third)
        self.first = first
        self.second = second
        self.third = third
    
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
