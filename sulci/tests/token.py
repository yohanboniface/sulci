# -*- coding: utf-8 -*-
"""
All tests regarding sulci.base.Token class.
"""

from django.test import TestCase

from sulci.base import Token

__all__ = ["TokenTest", "TokenIsStrongPunctuationTest"]

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
