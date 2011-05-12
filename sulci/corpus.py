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
    
    def __init__(self, extension=VALID_EXT, tagger=None):
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
    
    def check_word(self, word):
        """
        Find occurrences of a word in the corpus loaded.
        """
        found = False
        for t in self.tokens:
            if word == t:
                sulci_logger.info("%s :" % unicode(t.sample.parent), "YELLOW")
                sulci_logger.info(t.show_context(), "WHITE")
                found = True
        if not found:
            sulci_logger.info(u'No occurrence found for "%s"' % word, "RED")
    
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
    
    PATH = "corpus"
    VALID_EXT = ".crp"
    PENDING_EXT = ".pdg"
    LEXICON_EXT = ".lxc.lem.crp"
    
    def __init__(self, path=None):
        """
        Load a text, given a path.
        
        The path is optionnal, because content can be loaded from the prepare
        method.
        """
        self.path = path
        self.content = ""
        if path:
            self.load()
        self._tokens = None
        self._samples = None
    
    def load(self):
        self.content = load_file(self.path)
    
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
    
    def __unicode__(self):
        return self.path
    
    def check_text(self, lexicon, check_lemmes=False):
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
                if check_lemmes:
                    if t.verified_tag in lexicon[t] \
                             and t.verified_lemme != lexicon[t][t.verified_tag]:
                        sulci_logger.info(u"Word in lexicon, but not this lemme for %s (%s)" \
                                          % (unicode(t), t.verified_lemme), "BLUE")
                        sulci_logger.info(u"In Lexicon : %s" % lexicon[t][t.verified_tag], "GRAY")
    
    def prepare(self, text, tagger, lemmatizer):
        """
        Given a raw text, clean it, and make tokens and samples.
        
        (Maybe this method should be in the TextManager class.)
        """
        text = normalize_text(text)
        tokenized_text = self.tokenize(text)
        self._samples, self._tokens = self.instantiate_text(tokenized_text)
        tagger.tag_all(self.tokens)
        lemmatizer.do(self.tokens)
    
    def export(self, name, force=False, add_lemmes=False):
        """
        Export tokens in a file.
        
        force for export in the valid extension, otherwise it use the pending.
        """
        self.content = ""
        for sample in self.samples:
            for token in sample:
                lemme = ""
                if add_lemmes:
                    # Add lemme only if different from original
                    if token.lemme != token.original:
                        lemme = u"/%s" % token.lemme
                self.content += u"%s/%s%s " % (unicode(token.original), token.tag, lemme)
            self.content += u"\n" # Carriage return on each sample, for human reading
        # Define extention
        ext = self.PENDING_EXT
        if force:
            if add_lemmes:
                ext = self.LEXICON_EXT
            else:
                ext = self.VALID_EXT
        save_to_file(os.path.join(self.PATH, "%s%s" % (name, ext)), self.content)

