#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from base import TextManager
from utils import log
from rules_templates import LemmatizerTemplateGenerator

class Lemmatizer(TextManager):
    """
    This class give a lemma for a token, using his tag.
    """
    PATH = "corpus"
    VALID_EXT = ".lem.crp"
    
    def __init__(self):
        self._tokens = None
        self._raw_content = None
        self._len = None
    
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
            log("Loading Lemmatizer corpus...", "GREEN", True)
            self._samples, self._tokens = self.instantiate_text(self.content.split())
        return self._tokens
    
    @property
    def samples(self):
        if self._samples is None:
            self.tokens # Load tokens and samples
        return self._samples
    
    def do(self, token):
        """
        A Token object or a list of token objects is expected.
        Return the token or the list.
        """
        tks = hasattr(token, "__iter__") and token or [token]
        rules = LemmatizerTemplateGenerator.load() # Cache me
        for rule in rules:
            template, _ = LemmatizerTemplateGenerator.get_instance(rule)
            template.apply_rule(tks, rule)
        return hasattr(token, "__iter__") and tks or tks[0]

