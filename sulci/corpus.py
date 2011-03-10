#!/usr/bin/env python
# -*- coding:Utf-8 -*-

import os

from collections import defaultdict
from operator import itemgetter

from django.utils.text import unescape_entities

from textminingutils import normalize_text
from utils import load_file, save_to_file, log
from base import TextManager

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
        self._samples = []
    
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
            log("Loading corpus...", "RED", True)
            self._samples, self._tokens = self.instantiate_text(self.content.split())
        return self._tokens
    
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

    def prepare_candidate(self, name):
        c = load_file(os.path.join(self.PATH, "%s%s" % (name, self.NEW_EXT)))
        tks = self.tokenize(c)
        samples, tokens = self.instantiate_text(tks)
        self.tagger.tag_all(tokens)
        final = ""
        for sample in samples:
            for tgdtk in sample:
                final += u"%s/%s " % (unicode(tgdtk.original), tgdtk.tag)
            final += u"\n"
        save_to_file(os.path.join(self.PATH, "%s%s" % (name, self.PENDING_EXT)), final)
    
    def check_word(self, word):
        found = False
        for t in self.tokens:
            if word == t:
                log(t.show_context(), "WHITE")
                found = True
        if not found:
            log(u'No occurrence found for "%s"' % word, "WHITE")
    
    def tags_stats(self):
        """
        Display tags usage stats.
        """
        d = defaultdict(int)
        for t in self:
            if t.verified_tag == None: log(u"No verified tag for %s" % unicode(t), "RED", True)
            d[t.verified_tag] += 1
        log(u"Tag usage :", "WHITE")
        for k, v in sorted(d.iteritems(), key=itemgetter(1), reverse=True):
            log(u"%s => %d" % (k, v), "CYAN")

