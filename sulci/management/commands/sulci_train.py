#!/usr/bin/env python
# -*- coding:Utf-8 -*-
import time

from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings

from sulci.pos_tagger import PosTagger
from sulci.lexicon import Lexicon
from sulci.corpus import Corpus
from sulci.textmining import SemanticalTagger
from sulci.thesaurus import Thesaurus
from sulci.log import sulci_logger
from sulci.trainers import SemanticalTrainer, LemmatizerTrainer, LexicalTrainer,\
                                                   ContextualTrainer, POSTrainer
from sulci.lemmatizer import Lemmatizer
from sulci import content_model
from sulci_cli import SulciBaseCommand

class Command(SulciBaseCommand):
    """
    Sulci command for training the algoritms.
    """
    help = __doc__
    option_list = SulciBaseCommand.option_list + (
        make_option("-x", "--lexicon", action="store_true", 
                    dest="lexicon", help = "Build the lexicon"),
        make_option("-e", "--lexical", action="store_true", 
                    dest="lexical", help = "Launch the lexical trainer"),
        make_option("-c", "--contextual", action="store_true", 
                    dest="contextual", help = "Launch the contextual trainer"),
        make_option("-m", "--mode", action="store", type="string", dest="mode",
                    default = None, 
                    help="Trainer mode : master, slave, or full (default)"),
        make_option("-r", "--lemmatizer", action="store_true", dest="lemmatizer", 
                    help = "Launch Lemmatizer training."),
        make_option("-s", "--subprocesses", action="store", type="int", 
                    dest="subprocesses",
                    default = None, help = "Launch trainer with x subprocesses"),
        make_option("-n", "--semantical", action="store_true", dest="semantical", 
                    help = "Launch the sementical training. Launch it with python -O."),
        make_option("-a", "--add_candidate", action="store_true", 
                    dest="add_candidate", help="Prepare article for manual POS indexing"),
        make_option("-b", "--add_lemmes", action="store_true", dest="add_lemmes", 
                    help="Add lemme also when preparing a text for POS indexing"),
        )
    
    def handle(self, *args, **options):
        super(Command, self).handle(self, *args, **options)
        C = Corpus()
        L = Lexicon()
        P = PosTagger(lexicon=L)
        if self.LEXICON:
            L.make(self.FORCE)
        if self.SUBPROCESSES:
            import subprocess
            training_kind = self.LEXICAL and "-e"\
                            or self.LEMMATIZER and "-r"\
                            or self.SEMANTICAL and "-n"\
                            or "-c" # CONTEXTUAL
            # Create slaves
            for i in xrange(0,self.SUBPROCESSES):
                sulci_logger.info(u"Opening slave subprocess %d" % i, "BLUE", True)
                python_kind = not __debug__ and ["-O"] or []
                subprocess.Popen(["python"] + python_kind + ["manage.py", "sulci_train", training_kind, "--mode=slave"])
            # Set the mode to the trainer
            self.MODE = "master"
            # Wait to leave time to slave to launch
            time.sleep(1)
        if self.LEXICAL:
            T = LexicalTrainer(P,C,self.MODE)
            T.do()
        elif self.CONTEXTUAL:
            T = ContextualTrainer(P,C,self.MODE)
            T.do()
        elif self.LEMMATIZER:
            M = Lemmatizer(L)
            T = LemmatizerTrainer(M,self.MODE)
            T.do()
        elif self.SEMANTICAL:
            T = Thesaurus()
            S = SemanticalTrainer(T,P,self.MODE)
            if self.PK:
                # Should not have PK in MODE == "master"
                a = content_model.objects.get(pk=self.PK)
                S.train(a)
            else:
                if self.FORCE:
                    S.begin()
                S.do()
#                if TRAINER_MODE == "master" and FORCE:
#                    S.clean_connections()
        if self.ADD_CANDIDATE:
            if not self.PK:
                print "A PK is needed. Use -k xxx"
            else:
                a = content_model.objects.get(pk=self.PK)
                t = getattr(a, settings.SULCI_CONTENT_PROPERTY)
                T = TextCorpus()
                T.prepare(t, P, M)
                T.export(self.PK, self.FORCE, self.ADD_LEMMES)
        if self.IPDB:
            import ipdb; ipdb.set_trace()

if __name__ == '__main__':
    main()
