# -*- coding: utf-8 -*-

import unittest

from sulci.textmining import SemanticalTagger


class NgramsTests(unittest.TestCase):

    def test_default(self):
        text = SemanticalTagger("Une phrase avec un mot dingue. "
                                "Une autre phrase avec le même mot dingue.")
        # We should get (stop words at end or beginning are skipped):
        expected_ngrams = set([
            (u"phrase", u"avec", u"un", u"mot", u"dingue"),
            (u"phrase", u"avec", u"un", u"mot"),
            (u"phrase", u"avec", u"le", u"même", u"mot", u"dingue"),
            (u"phrase", u"avec", u"le", u"même", u"mot"),
            (u"mot", u"dingue"),
        ])
        ngrams = text.ngrams()
        self.assertEqual(len(ngrams), 5)
        flat_ngrams = set()
        for ngram in ngrams:
            flat_ngrams.add(
                tuple(stemm.main_occurrence.lemme for stemm in ngram)
            )
        self.assertEqual(expected_ngrams, flat_ngrams)

    def test_retrieve_also_unigrams(self):
        """
        Passing min_count=1, all the ngrams >= bigram should be returned.
        """
        text = SemanticalTagger("Une phrase avec un mot dingue. "
                                "Une autre phrase avec le même mot dingue.")
        # We should get the same than by default, plus the
        # non stop words, so 5 + [phrase, mot, dingue] = 8
        ngrams = text.ngrams(min_length=1)
        self.assertEqual(len(ngrams), 8)

    def test_should_not_return_ngrams_longer_than_max_length(self):
        """
        Passing min_count=1, all the ngrams >= bigram should be returned.
        """
        text = SemanticalTagger("Une phrase avec un mot dingue. "
                                "Une autre phrase avec le même mot dingue.")
        # We should only get:
        # - phrase, avec, un, mot
        # - mot, dingue
        ngrams = text.ngrams(max_length=4)
        self.assertEqual(len(ngrams), 2)


class FilteredNgramsTests(unittest.TestCase):

    def test_default(self):
        text = SemanticalTagger("Une phrase avec un mot dingue. "
                                "Une autre phrase avec le même mot dingue.")
        # We should get "mot dingue", who occurs twice:
        ngrams = text.filtered_ngrams()
        self.assertEqual(len(ngrams), 1)
        self.assertEqual(
            tuple(stemm.main_occurrence.lemme for stemm in ngrams[0][0]),
            (u"mot", u"dingue")
        )
