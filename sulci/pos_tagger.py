#!/usr/bin/env python
# -*- coding:Utf-8 -*-

import os

from collections import defaultdict
from operator import itemgetter

from utils import load_file, save_to_file, log
from rules_templates import ContextualTemplateGenerator, \
                            LexicalTemplateGenerator, RuleTemplate
from base import Token

class PosTagger(object):
    """
    Part-of-Speach tagger.
    """

    def __init__(self, lexicon):
        self.lexicon = lexicon
    
    def default_tag(self, token):
        if isinstance(token, Token):
            token = token.original
        if token in self.lexicon:
            return self.lexicon[token][0]
        elif token[0].isupper():
            return "SBP:sg"
#        elif token.endswith("s") or token.endswith("x"):
#            return "SBC:pl"
        else:
            return "SBC:sg"
    
    def lexical_tag(self, token):
        """
        Apply lexical tag to a token or list of tokens
        """
        tks = hasattr(token, "__iter__") and token or [token]
        rules = LexicalTemplateGenerator.load()
        for rule in rules:
            template, _ = LexicalTemplateGenerator.get_instance(rule, self.lexicon)
            template.apply_rule(tks, rule)
        # Return a list if a list was given
        return hasattr(token, "__iter__") and tks or tks[0]
    
    def contextual_tag(self, token):
        tks = hasattr(token, "__iter__") and token or [token]
        rules = ContextualTemplateGenerator.load()
        for rule in rules:
            template, _ = ContextualTemplateGenerator.get_instance(rule)
            template.apply_rule(tks, rule)
        return hasattr(token, "__iter__") and tks or tks[0]
    
    def get_tag(self, tokens):
        final = []
        for token in tokens:
            final.append((token, self.default_tag(token)))
        return final
    
    def tag(self, token, mode="final"):
        token.tag = self.default_tag(token)
        return token
        #manage final and just lexical modes
    
    def tag_all(self, tokens, lexical=True, contextual=True):
        for tk in tokens:
            self.tag(tk)
        if lexical:
            self.lexical_tag(tokens)
        if contextual:
            self.contextual_tag(tokens)


