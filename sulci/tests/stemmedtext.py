# -*- coding: utf-8 -*-

import unittest

from sulci.textmining import StemmedText


class InstantiateTextTests(unittest.TestCase):

    def test_base(self):
        text = StemmedText("One sentence. Another.")
        self.assertEqual(len(text.samples), 2)
        self.assertEqual(len(text.samples[0]), 3)
        self.assertEqual(len(text.samples[1]), 2)
        self.assertEqual(text.samples[0][0].original, "One")
        self.assertEqual(text.samples[0][1].original, "sentence")
        self.assertEqual(text.samples[0][2].original, ".")
        self.assertEqual(text.samples[1][0].original, "Another")
        self.assertEqual(text.samples[1][1].original, ".")

    def test_comma_is_not_a_sentence_delimiter(self):
        text = StemmedText("One sentence, the same.")
        self.assertEqual(len(text.samples), 1)

    def test_exclamation_point_is_a_sentence_delimiter(self):
        text = StemmedText("One sentence! Another.")
        self.assertEqual(len(text.samples), 2)
