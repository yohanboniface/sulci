# -*- coding: utf-8 -*-
"""
All tests regarding sulci.base.Token class.
"""

from django.test import TestCase

from sulci.base import Token

__all__ = ["TokenTest"]

class TokenTest(TestCase):

    def test_should_create_a_token(self):
        token = Token("mot", original="mot")
        self.assertTrue(isinstance(token, Token))
