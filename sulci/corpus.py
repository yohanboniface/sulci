#!/usr/bin/env python
# -*- coding:Utf-8 -*-

import os

from collections import defaultdict
from operator import itemgetter

from sulci.textutils import normalize_text
from sulci.utils import load_file, save_to_file, get_dir
from sulci.base import TextManager
from sulci.log import sulci_logger


class CorpusMonitor(object):
    """
    Convenience class to store common methors between Corpus and TextCorpus.
    """
    def check_usage(self, word=None, tag=None, lemme=None, case_insensitive=False):
        """
        Find occurrences of a word or tag or both in the corpus loaded.
        """
        if not any((word, tag, lemme)):
            raise ValueError("You must specify at least a word, a tag or a lemme")
        found = False
        for t in self:
            # If a specific word is asked
            if word:
                original = t.original
                if case_insensitive:
                    word = word.lower()
                    original = original.lower()
                if not word == original:
                    continue
            # If a specific tag is asked
            if tag and not tag == t.verified_tag:
                continue
            # don't care about texts without lemmes, when a lemme is asked
            if lemme:
                if not t.sample.parent.has_verified_lemmes:
                    continue
                if not lemme == t.verified_lemme:
                    continue
            sulci_logger.info("%s :" % unicode(t.sample.parent), "YELLOW")
            sulci_logger.info(t.show_context(), "WHITE")
            found = True
        if not found:
            not_found = u'No occurrence found for'
            if word:
                not_found += " %s" % word
            if tag:
                not_found += " %s" % tag
            sulci_logger.info(not_found, "RED")

    def tags_stats(self, word=None, case_insensitive=None):
        """
        Display tags usage stats.
        """
        d = defaultdict(int)
        for t in self:
            if word:
                original = t.original
                if case_insensitive:
                    word = word.lower()
                    original = original.lower()
                if not word == original:
                    continue
            if t.verified_tag == None:
                sulci_logger.info(u"No verified tag for %s" % unicode(t), "RED", True)
            d[t.verified_tag] += 1
        log = u"Tag usage :"
        if word:
            log = u"Tag usage for word '%s'" % word
        sulci_logger.info(log, "WHITE")
        for k, v in sorted(d.iteritems(), key=itemgetter(1), reverse=True):
            sulci_logger.info(u"%s => %d" % (k, v), "CYAN")

    def check(self, lexicon, check_lemmes=False):
        """
        Check the text of the corpus, and try to determine if there are some errors.
        Compare with lexicon.
        """
        sulci_logger.info(u"Checking text %s" % self.path, "YELLOW")
        found = False
        for t in self:
            if t in lexicon:
                # Check that current tag is in lexicon
                # If not, it *could* be an error, we display it
                if not t.verified_tag in lexicon[t]:
                    sulci_logger.info(u"Word in lexicon, but not this tag for %s (%s)" \
                                      % (unicode(t), t.verified_tag), "RED")
                    sulci_logger.info(u"In Lexicon : %s" % lexicon[t])
                    sulci_logger.info(u"Context : %s" % t.show_context(), "MAGENTA")
                    found = True
                if check_lemmes:
                    if t.verified_tag in lexicon[t] \
                             and t.verified_lemme != lexicon[t][t.verified_tag]:
                        sulci_logger.info(u"Word in lexicon, but not this lemme for %s (%s)" \
                                          % (unicode(t), t.verified_lemme), "BLUE")
                        sulci_logger.info(u"In Lexicon : %s" % lexicon[t][t.verified_tag], "GRAY")
                        sulci_logger.info(u"Context : %s" % t.show_context(), "YELLOW")
                    found = True
        if not found:
            sulci_logger.info(u"No error found", "YELLOW")


class Corpus(CorpusMonitor):
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


class TextCorpus(TextManager, CorpusMonitor):
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
            self.tokens  # Load tokens and samples
        return self._samples

    def __iter__(self):
        return self.tokens.__iter__()

    def __len__(self):
        return self.tokens.__len__()

    def __unicode__(self):
        return self.path

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
            self.content += u"\n"  # Carriage return on each sample, for human reading
        # Define extention
        ext = self.PENDING_EXT
        if force:
            if add_lemmes:
                ext = self.LEXICON_EXT
            else:
                ext = self.VALID_EXT
        save_to_file(os.path.join(self.PATH, "%s%s" % (name, ext)), self.content)

    @property
    def has_verified_lemmes(self):
        """
        Returns True if the text is supposed to contains verified lemmes.
        """
        return self.path.endswith(self.LEXICON_EXT)
