#!/usr/bin/env python
# -*- coding:Utf-8 -*-

import os

from collections import defaultdict
from operator import itemgetter

from django.utils.text import unescape_entities

from sulci.textutils import normalize_text
from sulci.utils import load_file, save_to_file, get_dir
from sulci.base import TextManager
from sulci.lemmatizer import Lemmatizer
from sulci.log import sulci_logger

class Corpus(object):
    """
    The corpus is a collection of manualy categorised texts.
    
    We have different kind of categorised texts :
    
    - .crp => just POS tag
    
    - .lem... => also manualy lemmatized
    
    - .lcx... => will be used to make the Lexicon
    
    When loading a Corpus, you'll need to specify the kind of texts to load.
    """
    PATH = "corpus"
    VALID_EXT = ".crp"
    PENDING_EXT = ".pdg"
    NEW_EXT = ".new"
    LEXICON_EXT = ".lxc"

    def __init__(self, tagger=None, extension=VALID_EXT):
        """
        You can force a tagger.
        Extension will be used to load the category of manually tagged files.
        """
        self.tagger = tagger
        self._raw_content = ""
        self.extension = extension
        self._tokens = None
        self._samples = None
        self._texts = None
    
    def attach_tagger(self, tagger):
        """
        Attach a tagger. Used for preparing texts.
        """
        self.tagger = tagger
    
    @property
    def files(self):
        """
        Return a list of files for the corpus extension.
        """
        return [x for x in os.listdir(get_dir(__file__) + self.PATH) \
                                                  if x.endswith(self.extension)]
    
    @property
    def texts(self):
        if self._texts is None:
            self._texts = []
            for f in self.files:
                t = TextCorpus(os.path.join(self.PATH, f))
                self._texts.append(t)
        return self._texts
    
    @property
    def tokens(self):
        if self._tokens is None:
            self._tokens = []
            for corpus_text in self.texts:
                self._tokens += corpus_text.tokens
        return self._tokens
    
    @property
    def samples(self):
        if self._samples is None:
            self._samples = []
            for corpus_text in self.texts:
                self._samples += corpus_text.samples
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
    
class TextCorpus(TextManager):
    """
    One single text of the corpus.
    
    This is not a raw text, but a manualy categorized text.
    
    The normalisation is : word/TAG/lemme word2/TAG2/lemme2, etc.
    """
    
    def __init__(self, path=None):
        """
        Load a text, given a path.
        """
        self.path = path
        self.content = load_file(path)
        self._tokens = None
        self._samples = None
    
    @property
    def tokens(self):
        if self._tokens is None:
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
    
    def check_text(self, lexicon):
        """
        Check the text of the corpus, and try to determine if there are some errors.
        Compare with lexicon.
        """
        for t in self:
            if t in lexicon:
                # Check that current tag is in lexicon
                # If not, it *could* be an error, we display it
                if not t.verified_tag in lexicon[t]:
                    sulci_logger.info(u"Word in lexicon, but not this tag for %s (%s)" \
                                      % (unicode(t), t.verified_tag), "RED")
                    sulci_logger.info(u"In Lexicon : %s" % lexicon[t])


