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
        tks = hasattr(token, "__iter__") and token or [token]
        rules = LexicalTemplateGenerator.load()
        for rule in rules:
            template, _ = LexicalTemplateGenerator.get_instance(rule, self.lexicon)
            template.apply_rule(tks, rule)
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

class Trainer(object):
    """
    Pos Tagger trainer.
    """
    def __init__(self, tagger, corpus, mode = "full"):
        self.tagger = tagger
        self.corpus = corpus
        self.tag_all()
        self.initial = self.corpus.tokens[:]
        self.mode = mode
    
    def setup_socket_master(self):
        import zmq
        self.reqsocket = zmq.Socket(zmq.Context(), zmq.XREQ)
        self.reqsocket.bind("ipc:///tmp/textmining.action")
        self.pubsocket = zmq.Socket(zmq.Context(), zmq.PUB)
        self.pubsocket.bind("ipc:///tmp/textmining.apply")
    
    def setup_socket_slave(self):
        import zmq
        self.repsocket = zmq.Socket(zmq.Context(), zmq.XREP)
        self.repsocket.connect("ipc:///tmp/textmining.action")
        self.subsocket = zmq.Socket(zmq.Context(), zmq.SUB)
        self.subsocket.connect("ipc:///tmp/textmining.apply")
        self.subpoller = zmq.Poller()
        self.subpoller.register(self.subsocket, zmq.POLLIN)
        self.reppoller = zmq.Poller()
        self.reppoller.register(self.repsocket, zmq.POLLIN)
        self.subsocket.setsockopt(zmq.SUBSCRIBE, "")
    
    def train(self):
        #We have to apply rules one after one to all objects
        log("Begin of training session.", "WHITE", True)
        final_rules = []
        tag_errors = self.get_errors()
        while tag_errors:
            run_applied_rule = False
            log("%d errors for now..." % len(tag_errors), "RED", True)
            for tag_error in tag_errors[:]:
                rules_candidates = []
                log(u"Error : %s, tagged %s instead of %s" % (unicode(tag_error), tag_error.tag, tag_error.verified_tag), "WHITE")
                #Make rules candidates
                for tpl, _ in self.template_generator.register.items():
    #                    print "tpl", tpl
                    template, _ = self.template_generator.get_instance(tpl, lexicon=self.tagger.lexicon)
                    rules_candidates += template.make_rules(tag_error)
                #Test the rules
                pondered_rules = self.test_rules(rules_candidates)
                #Select one rule
                rule_candidate, score = RuleTemplate.select_one(pondered_rules, len(self.corpus), 3)
                #Maybe the test "rule_candidate in final_rules" have to be done before...
                if rule_candidate and not rule_candidate in final_rules:#How to calculate the score min ?
                    template, _ = self.template_generator.get_instance(rule_candidate, lexicon=self.tagger.lexicon)
                    final_rules.append((rule_candidate, score))
                    #Apply the rule to the tokens
                    log(u"Applying rule %s (%s)" % (rule_candidate, score), "RED")
                    template.apply_rule(self.initial, rule_candidate)
                    if self.mode == "master":
                        self.pubsocket.send(" %s" % rule_candidate.encode("utf-8"))
                    run_applied_rule = True
                    #We have applied a rule, we can try another run
                    tag_errors = self.get_errors()
                    break#break the for
            if run_applied_rule: continue#go back to while
            tag_errors = None#Nothing applied, we stop here.
        self.display_errors()
        self.template_generator.export(final_rules)
    
    def do(self):
        if self.mode == "slave":
            self.slave()
        elif self.mode == "master":
            self.setup_socket_master()
            self.train()
            self.pubsocket.send(" stop")
        else:
            self.train()
    
    def slave(self):
        self.setup_socket_slave()
#        import ipdb; ipdb.set_trace()
        while True:
            if self.subpoller.poll(0):
                rule = self.subsocket.recv()[1:]
                if rule == "stop": return
                rule = rule.decode("utf-8")
                template, _ = self.template_generator.get_instance(rule, lexicon=self.tagger.lexicon)
                #Apply the rule to the tokens
                log(u"Applying rule %s" % rule, "RED")
                template.apply_rule(self.initial, rule)
            if self.reppoller.poll(0):
                idx, action, rule = self.repsocket.recv_multipart()
                _, good, bad = self.test_rule(rule.decode("utf-8"))
                self.repsocket.send_multipart([idx, rule, str(good), str(bad)])
    
    def test_rules(self, rules_candidates):
        pondered_rules = []
        if self.mode == "master":
            #Send order
            for rule in rules_candidates:
                self.reqsocket.send_multipart(["check", rule.encode("utf-8")])
            #Receive results
            for rule in rules_candidates:
                resp = self.reqsocket.recv_multipart()
                r, good, bad = resp
                pondered_rules.append((r.decode("utf-8"), int(good), int(bad)))
                log(u"Received rule %s" % r.decode("utf-8"), "MAGENTA")
            log(u"All rules are received from slaves")
        else:
            for rule in rules_candidates:
                pondered_rules.append(self.test_rule(rule))
        return pondered_rules
    
    def test_rule(self, rule):
        template, _ = self.template_generator.get_instance(rule, lexicon=self.tagger.lexicon)
        bad = 0
        good = 0
        for ttk in self.initial:
            test = template.test_rule(ttk, rule)
            if test == 1:
                good += 1
            elif test == -1:
                bad += 1
        log(u"%s g: %d b : %d" % (rule, good, bad), "GRAY")
        return rule, good, bad
    
    def get_first_error(self, tokens):
        for token in tokens:
            if token.tag != token.verified_tag:
                return token
        return None
    
    def get_errors(self):
        final = []
        for token in self.corpus:
            if token.tag != token.verified_tag:
                final.append(token)
        return final
    
    def display_errors(self):
        """
        Display errors in current step.
        """
        remaining_errors = self.get_errors()
        errors_count = len(remaining_errors)
        total_words = len(self.corpus)
        log(u"Remaining %d errors (%f %% of %d total words)" %
           (errors_count, 100.0 * errors_count / total_words, total_words), "RED")
        for r_error in remaining_errors:
            log(u"%s tagged %s instead of %s" % (unicode(r_error), r_error.tag, r_error.verified_tag), "GRAY")
    
    def tag_all(self):
        self.tagger.tag_all(self.corpus.tokens)

class LexicalTrainer(Trainer):
    
    template_generator = LexicalTemplateGenerator
    
    def tag_all(self):
        self.tagger.tag_all(self.corpus.tokens, lexical=False, contextual=False)
    
    def get_errors(self):
        final = []
        for token in self.corpus:
#            if token.tag != token.verified_tag:
            if token.tag != token.verified_tag \
               and not token in self.tagger.lexicon:
                final.append(token)
        return final

class ContextualTrainer(Trainer):
    
    template_generator = ContextualTemplateGenerator
    
    def tag_all(self):
        self.tagger.tag_all(self.corpus.tokens, contextual=False)

