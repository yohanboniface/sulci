#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sulci.rules_templates import ContextualTemplateGenerator, LexicalTemplateGenerator
from sulci.base import Token
from sulci.textutils import modern_istitle


class PosTagger(object):
    """
    Part-of-speech tagger.
    """

    def __init__(self, lexicon):
        self.lexicon = lexicon

    def default_tag(self, token):
        if isinstance(token, Token):
            token = token.original
        if token in self.lexicon:
            return self.lexicon[token].default_tag
        elif modern_istitle(token):
            return "SBP:sg"
#        elif token.endswith(["s", "x"]):
#            return "SBC:pl"
        else:
            return "SBC:sg"

    def lexical_tag(self, token):
        """
        Apply lexical tag to a token or list of tokens
        """
        tks = token if hasattr(token, "__iter__") else [token]
        rules = LexicalTemplateGenerator.load()
        for rule in rules:
            template, _ = LexicalTemplateGenerator.get_instance(rule, self.lexicon)
            template.apply_rule(tks, rule)
        # Return a list if a list was given
        return tks if hasattr(token, "__iter__") else tks[0]

    def contextual_tag(self, token):
        tks = token if hasattr(token, "__iter__") else [token]
        rules = ContextualTemplateGenerator.load()
        for rule in rules:
            template, _ = ContextualTemplateGenerator.get_instance(rule)
            template.apply_rule(tks, rule)
        return tks if hasattr(token, "__iter__") else tks[0]

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
