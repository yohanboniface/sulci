#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from sulci.base import TextManager
from sulci.log import sulci_logger
from sulci.rules_templates import LemmatizerTemplateGenerator


class Lemmatizer(TextManager):
    """
    This class give a lemma for a token, using his tag.
    """
    PATH = "corpus"
    VALID_EXT = ".lem.crp"

    def __init__(self, lexicon):
        self._tokens = None
        self._raw_content = None
        self._len = None
        self.lexicon = lexicon

    def __len__(self):
        if self._len is None:
            self._len = len(self.tokens)
        return self._len

    @property
    def content(self):
        if self._raw_content is None:
            self._raw_content = ""
            self.load_valid_files()
            self._raw_content = self._raw_content.replace("\n", " ").replace("  ", " ")
        return self._raw_content

    @property
    def tokens(self):
        if self._tokens is None:
            sulci_logger.info("Loading Lemmatizer corpus...", "GREEN", True)
            self._samples, self._tokens = self.instantiate_text(self.content.split())
        return self._tokens

    @property
    def samples(self):
        if self._samples is None:
            self.tokens  # Load tokens and samples
        return self._samples

    def do(self, token):
        """
        A Token object or a list of token objects is expected.
        Return the token or the list.
        """
        tks = token if hasattr(token, "__iter__") else [token]
        rules = LemmatizerTemplateGenerator.load()  # Cache me
        for rule in rules:
            template, _ = LemmatizerTemplateGenerator.get_instance(rule)
            template.apply_rule(tks, rule)
        # We force lemme if word is in lexicon with the current POS tag
        for tk in tks:
            if tk in self.lexicon and tk.tag in self.lexicon[tk]:
                tk.lemme = self.lexicon[tk][tk.tag]
        return tks if hasattr(token, "__iter__") else tks[0]
