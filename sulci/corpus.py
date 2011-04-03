#!/usr/bin/env python
# -*- coding:Utf-8 -*-

import os

from collections import defaultdict
from operator import itemgetter

from django.utils.text import unescape_entities

from sulci.textminingutils import normalize_text
from sulci.utils import load_file, save_to_file
from sulci.base import TextManager
from sulci.lemmatizer import Lemmatizer
from sulci.log import sulci_logger

class Corpus(TextManager):
    """
    The corpus is a collection of manualy categorised texts.
    """
    PATH = "corpus"
    VALID_EXT = ".crp"
    PENDING_EXT = ".pdg"
    NEW_EXT = ".new"
    LEXICON_EXT = ".lxc"

    def __init__(self, tagger=None):
        self.tagger = tagger
        self._raw_content = None
        self._tokens = None
        self._samples = None
    
    @property
    def content(self):
        if self._raw_content is None:
            self._raw_content = ""
            self.load_valid_files()
            self._raw_content = self._raw_content.replace("\n", " ").replace("  ", " ")
        return self._raw_content
    
    def attach_tagger(self, tagger):
        self.tagger = tagger
    
    @property
    def tokens(self):
        if self._tokens is None:
            sulci_logger.debug("Loading corpus...", "RED", True)
            self._samples, self._tokens = self.instantiate_text(self.content.split())
        return self._tokens
    
    @property
    def samples(self):
        if self._samples is None:
            self.tokens # Load tokens and samples
        return self._samples
    
    def __iter__(self):
        return self.tokens.__iter__()

    def __len__(self):
        return self.tokens.__len__()
    
    def add_candidate(self, t, name):
        """
        Retrieve an article in db, clean it, and add it to corpus.
        """
        t = normalize_text(t)
        save_to_file(os.path.join(self.PATH, "%s%s" % (name, self.NEW_EXT)), unicode(t))

    def prepare_candidate(self, name, add_lemmes=False):
        c = load_file(os.path.join(self.PATH, "%s%s" % (name, self.NEW_EXT)))
        tks = self.tokenize(c)
        samples, tokens = self.instantiate_text(tks)
        self.tagger.tag_all(tokens)
        final = ""
        for sample in samples:
            for tgdtk in sample:
                lemme = ""
                if add_lemmes:
                    L = Lemmatizer()
                    L.do(tgdtk)
                    # Add lemme only if different from original
                    if tgdtk.lemme != tgdtk.original:
                        lemme = u"/%s" % tgdtk.lemme
                final += u"%s/%s%s " % (unicode(tgdtk.original), tgdtk.tag, lemme)
            final += u"\n"
        save_to_file(os.path.join(self.PATH, "%s%s" % (name, self.PENDING_EXT)), final)
    
    def check_word(self, word):
        found = False
        for t in self.tokens:
            if word == t:
                sulci_logger.info(t.show_context(), "WHITE")
                found = True
        if not found:
            sulci_logger.info(u'No occurrence found for "%s"' % word, "WHITE")
    
    def tags_stats(self):
        """
        Display tags usage stats.
        """
        d = defaultdict(int)
        for t in self:
            if t.verified_tag == None:
                sulci_logger.info(u"No verified tag for %s" % unicode(t), "RED", True)
            d[t.verified_tag] += 1
        sulci_logger.info(u"Tag usage :", "WHITE")
        for k, v in sorted(d.iteritems(), key=itemgetter(1), reverse=True):
            sulci_logger.info(u"%s => %d" % (k, v), "CYAN")

