#!/usr/bin/env python
# -*- coding:Utf-8 -*-

import os

#from collections import defaultdict
#from operator import itemgetter

from utils import load_file, save_to_file, log
from thesaurus import Trigger, Descriptor
from textmining import SemanticalTagger
from textminingutils import tokenize_text
from rules_templates import LemmatizerTemplateGenerator, RuleTemplate,\
                           ContextualTemplateGenerator, LexicalTemplateGenerator

class SemanticalTrainer(object):
    """
    Create and update triggers.
    """
    PENDING_EXT = ".pdg"
    VALID_EXT = ".trg"
    
    def __init__(self, thesaurus, pos_tagger):
        self.thesaurus = thesaurus
        self.pos_tagger = pos_tagger
#        self._triggers = self.thesaurus.triggers
    
    def begin(self):
        """
        Make one trigger for each descriptor of the thesaurus.
        Have to be called one time at the begining, and that's all.
        """
        # TODO Add aliases...
        for d in self.thesaurus:
            t = Trigger.objects.create(original=unicode(d))
            t.connect(d, 1)
#            self._triggers.add(t)
    
    def train(self, text, descriptors):
        """
        For the moment, human defined descriptors are a string with "," separator.
        """
        validated_descriptors = set()
        # Retrieve descriptors
        for d in descriptors.split(","):
            # Get this tokenize_text out of my eyes !
            d = d.strip().replace(u"’", u"'")
            if not d == "":
                # We create the descriptor not in thesaurus for now
                dsc, created = Descriptor.objects.get_or_create(name=d)
                validated_descriptors.add(dsc)
                if created:
                    log(u"Lairning descriptor not in thesaurus : %s" % unicode(dsc), "RED")
        # Retrieve keytentities :
        S = SemanticalTagger(text, self.thesaurus, self.pos_tagger)
        current_triggers = set()
        for ke in S.keyentities:
            # Retrieve or create triggers
            t, created = Trigger.objects.get_or_create(original=unicode(ke))
#            self._triggers.add(t)
            current_triggers.add(t)
            t.current_score = ke.trigger_score
        log(u"Current triggers", "WHITE")
        log([unicode(d) for d in current_triggers], "YELLOW")
        log(u"Descriptors validated by human", "WHITE")
        log([unicode(d) for d in validated_descriptors], "YELLOW")
        #Descriptors calculated by SemanticalTagger
        calculated_descriptors = set(d for d, value in S.descriptors)
        log(u"Descriptors calculated", "WHITE")
        log([unicode(d) for d in calculated_descriptors], "YELLOW")
        #Descriptors that where tagged by humans, but not calculated
        false_negative = validated_descriptors.difference(calculated_descriptors)
        #Descriptors that where not tagged by humans, but where calculated
        false_positive = calculated_descriptors.difference(validated_descriptors)
        #Validated descriptors that where also calculated
        true_positive = calculated_descriptors.intersection(validated_descriptors)
        
        for d in true_positive:
            for t in current_triggers:
                if d in t:
                    t.connect(d, 2 + t.current_score)#trust the relation
                    log(u"Adding 2 to connection %s - %s" % (t, d), "YELLOW")
        
        for d in false_positive:
            for t in current_triggers:
                if d in t:
                    t.connect(d, -(1 + t.current_score))#untrust the relation
                    log(u"Removing 1 to connection %s - %s" % (t, d), "BLUE")
        
        for d in false_negative:
            for t in current_triggers:
                t.connect(d, t.current_score)#guess the relation
                log(u"Connecting %s and %s" % (t, d), "WHITE")
    
    def clean_connections(self):
        """
        Delete all the connection where score < 0.
        """
        Trigger.clean_all_connections()

class RuleTrainer(object):
    """
    Main trainer class for rules based, for factorisation.
    """
    
    def do(self):
        if self.mode == "slave":
            self.slave()
        elif self.mode == "master":
            self.setup_socket_master()
            self.train()
            self.pubsocket.send(" stop")
        else:
            self.train()
    
    def setup_socket_master(self):
        """
        Configure the sockets for the master trainer.
        """
        import zmq
        # This is a socket load-balanced to every workers
        # listening the canal.
        self.reqsocket = zmq.Socket(zmq.Context(), zmq.XREQ)
        self.reqsocket.bind("ipc:///tmp/sulci.action")
        # This is a publisher socket, used to distribute data.
        # No response is expected.
        self.pubsocket = zmq.Socket(zmq.Context(), zmq.PUB)
        self.pubsocket.bind("ipc:///tmp/sulci.apply")
    
    def setup_socket_slave(self):
        """
        Configure sockets for the workers (slaves).
        """
        import zmq
        self.repsocket = zmq.Socket(zmq.Context(), zmq.XREP)
        self.repsocket.connect("ipc:///tmp/sulci.action")
        # This is the subscriber socket. Its used to subscribe to a canal
        # to receive data.
        self.subsocket = zmq.Socket(zmq.Context(), zmq.SUB)
        self.subsocket.connect("ipc:///tmp/sulci.apply")
        self.subpoller = zmq.Poller()
        self.subpoller.register(self.subsocket, zmq.POLLIN)
        self.reppoller = zmq.Poller()
        self.reppoller.register(self.repsocket, zmq.POLLIN)
        self.subsocket.setsockopt(zmq.SUBSCRIBE, "")
    
    def slave(self):
        self.setup_socket_slave()
        while True:
            if self.subpoller.poll(0):
                rule = self.subsocket.recv()[1:]
                if rule == "stop": return
                rule = rule.decode("utf-8")
                template = self.get_template_instance(rule)
                #Apply the rule to the tokens
                log(u"Applying rule %s" % rule, "RED")
                template.apply_rule(self.tokens, rule)
            if self.reppoller.poll(0):
                idx, action, rule = self.repsocket.recv_multipart()
                _, good, bad = self.test_rule(rule.decode("utf-8"))
                self.repsocket.send_multipart([idx, rule, str(good), str(bad)])
    
    def test_rules(self, rules_candidates):
        pondered_rules = []
        if self.mode == "master":
            # Send order
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
    
    def pretrain(self):
        """
        Trainer specific training session preparation.
        """
        pass
    
    def log_error(self, token):
        pass
    
    def get_template_instance(self, tpl):
        pass
    
    def select_one_rule(self, rules):
        pass
    
    def train(self):
        """
        Main factorized train method.
        """
        #We have to apply rules one after one to all objects
        log("Begin of training session.", "WHITE", True)
        final_rules = []
        errors = self.get_errors()
        while errors:
            run_applied_rule = False
            log("%d errors for now..." % len(errors), "RED", True)
            for token_with_error in errors[:]:
                rules_candidates = []
                self.log_error(token_with_error)
                # Make rules candidates
                for tpl, _ in self.template_generator.register.items():
    #                    print "tpl", tpl
                    template = self.get_template_instance(tpl)
                    rules_candidates += template.make_rules(token_with_error)
                # Test the rules
                pondered_rules = self.test_rules(rules_candidates)
                # Select one rule
                rule_candidate, score = self.select_one_rule(pondered_rules)
                # Maybe the test "rule_candidate in final_rules" have to be done before...
                if rule_candidate and not rule_candidate in final_rules:#How to calculate the score min ?
                    template = self.get_template_instance(rule_candidate)
                    final_rules.append((rule_candidate, score))
                    # Apply the rule to the tokens
                    log(u"Applying rule %s (%s)" % (rule_candidate, score), "RED")
                    template.apply_rule(self.tokens, rule_candidate)
                    if self.mode == "master":
                        # Send the rule to apply
                        self.pubsocket.send(" %s" % rule_candidate.encode("utf-8"))
                    run_applied_rule = True
                    # We have applied a rule, we can try another run
                    errors = self.get_errors()
                    break#break the for
                else:#No rule applied for this error
                    # We don't want to reprocess this error another time
                    # unless the sample (so the context) as changed.
                    token_with_error.sample.set_trained_position(token_with_error.position)
            if run_applied_rule: continue#go back to while
            errors = None#Nothing applied, we stop here.
        self.display_errors()
        self.template_generator.export(final_rules)
    
    def test_rule(self, rule):
        template = self.get_template_instance(rule)
        bad = 0
        good = 0
        for ttk in self.tokens:
            test = template.test_rule(ttk, rule)
            if test == 1:
                good += 1
            elif test == -1:
                bad += 1
        log(u"%s g: %d b : %d" % (rule, good, bad), "GRAY")
        return rule, good, bad
    
    def display_errors(self):
        """
        Display errors in current step.
        """
        remaining_errors = self.get_errors()
        errors_count = len(remaining_errors)
        total_words = len(self.tokens)
        log(u"Remaining %d errors (%f %% of %d total words)" %
           (errors_count, 100.0 * errors_count / total_words, total_words), "RED")
        for r_error in remaining_errors:
            self.log_error(r_error)
    
    def get_errors(self):
        """
        Retrieve token where tag !== verified_tag.
        """
        final = []
        for sample in self.samples:
            # We don't take in count sample yet processed and not modified.
            final += sample.get_errors(self.attr_name)
        return final

class LemmatizerTrainer(RuleTrainer):
    """
    Train the Lemmatizer.
    """
    template_generator = LemmatizerTemplateGenerator
    attr_name = "lemme" # Name of the attribute we test on 

    def __init__(self, lemmatizer, mode = "full"):
        self.lemmatizer = lemmatizer
        self.mode = mode
        self.tokens = self.lemmatizer.tokens
        self.samples = self.lemmatizer.samples
        self.pretrain()
    
    def pretrain(self):
        """
        We need to have the right tags, here
        """
        for token in self.tokens:
            token.tag = token.verified_tag
    
    def log_error(self, token):
        log(u"Error : %s, lemmatized %s instead of %s" \
            % (unicode(token), token.lemme, token.verified_lemme), "WHITE")
    
    def get_template_instance(self, tpl):
        template, _ = self.template_generator.get_instance(tpl)
        return template
    
    def select_one_rule(self, rules):
        """
        Having a set of rules candidate for correcting some error, select the
        one correcting the more case, and creating the less errors.
        """
        return RuleTemplate.select_one(rules, len(self.tokens))

class POSTrainer(RuleTrainer):
    """
    Pos Tagger trainer.
    """
    attr_name = "tag" # Name of the attribute we test on 
    
    def __init__(self, tagger, corpus, mode = "full"):
        self.tagger = tagger
        self.corpus = corpus
        self.pretrain()
        self.tokens = self.corpus.tokens
        self.samples = self.corpus.samples
        self.mode = mode
    
    def log_error(self, token):
        log(u"Error : %s, tagged %s instead of %s" % (unicode(token), token.tag, token.verified_tag), "WHITE")
    
    def get_template_instance(self, tpl):
        template, _ = self.template_generator.get_instance(tpl, lexicon=self.tagger.lexicon)
        return template
    
    def select_one_rule(self, rules):
        return RuleTemplate.select_one(rules, len(self.corpus), 3)
    
    def pretrain(self):
        self.tagger.tag_all(self.corpus.tokens)

class LexicalTrainer(POSTrainer):
    
    template_generator = LexicalTemplateGenerator
    
    def pretrain(self):
        """
        Tag the tokens, but not using POS rules, as we are training it.
        """
        self.tagger.tag_all(self.corpus.tokens, lexical=False, contextual=False)
    
    def get_errors(self):
        """
        We don't care about token in Lexicon, for lexical trainer.
        """
        final = []
        for sample in self.corpus.samples:
            # We don't take in count sample yet processed and not modified.
            final += [t for t in sample.get_errors() if not t in self.tagger.lexicon]
        return final

class ContextualTrainer(POSTrainer):
    
    template_generator = ContextualTemplateGenerator
    
    def pretrain(self):
        """
        Tag the tokens, but not using the contextual rules, as we are training it.
        """
        self.tagger.tag_all(self.corpus.tokens, contextual=False)

