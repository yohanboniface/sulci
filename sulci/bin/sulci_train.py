#!/usr/bin/env python
# -*- coding:Utf-8 -*-
import time

from sulci.pos_tagger import PosTagger
from sulci.lexicon import Lexicon
from sulci.corpus import Corpus, TextCorpus
from sulci.thesaurus import Thesaurus
from sulci.log import sulci_logger
from sulci.trainers import SemanticalTrainer, LemmatizerTrainer, LexicalTrainer,\
                                           ContextualTrainer, GlobalPMITrainer
from sulci.lemmatizer import Lemmatizer
from sulci.base import UseDB
from sulci import config

from sulci_cli import SulciBaseCommand


class Command(SulciBaseCommand):
    """
    Sulci command for training the algoritms.
    """
    help = __doc__

    def define_args(self):
        super(Command, self).define_args()
        self.parser.add_argument(
            "-x",
            "--lexicon",
            action="store_true",
            dest="lexicon",
            help="Build the lexicon"
        )
        self.parser.add_argument(
            "-e",
            "--lexical",
            action="store_true",
            dest="lexical",
            help="Launch the lexical trainer"
        )
        self.parser.add_argument(
            "-c",
            "--contextual",
            action="store_true",
            dest="contextual",
            help="Launch the contextual trainer"
        )
        self.parser.add_argument(
            "-m",
            "--mode",
            action="store",
            type=str,
            dest="mode",
            default=None,
            help="Trainer mode : master, slave, or full (default)"
        )
        self.parser.add_argument(
            "-r",
            "--lemmatizer",
            action="store_true",
            dest="lemmatizer",
            help="Launch Lemmatizer training."
        )
        self.parser.add_argument(
            "-s",
            "--subprocesses",
            action="store",
            type=int,
            dest="subprocesses",
            default=None,
            help="Launch trainer with x subprocesses"
        )
        self.parser.add_argument(
            "-n",
            "--semantical",
            action="store_true",
            dest="semantical",
            help="Launch the sementical training. Launch it with python -O."
        )
        self.parser.add_argument(
            "-p",
            "--pmi",
            action="store_true",
            dest="pmi",
            help="Launch the PMI training. Launch it with python -O."
        )
        self.parser.add_argument(
            "-a",
            "--add_candidate",
            action="store_true",
            dest="add_candidate",
            help="Prepare article for manual POS indexing"
        )
        self.parser.add_argument(
            "-b",
            "--add_lemmes",
            action="store_true",
            dest="add_lemmes",
            help="Add lemme also when preparing a text for POS indexing"
        )

    def handle(self, *args, **options):
        with UseDB(config.TRAINING_DATABASE):
            C = Corpus()
            L = Lexicon()
            M = Lemmatizer(L)
            P = PosTagger(lexicon=L)
            if self.LEXICON:
                L.make(self.FORCE)
            if self.SUBPROCESSES:
                import subprocess
                training_kind = self.LEXICAL and "-e"\
                                or self.LEMMATIZER and "-r"\
                                or self.SEMANTICAL and "-n"\
                                or self.PMI and "-p"\
                                or "-c"  # CONTEXTUAL
                # Create slaves
                for i in xrange(0, self.SUBPROCESSES):
                    sulci_logger.info(u"Opening slave subprocess %d" % i, "BLUE", True)
                    python_kind = not __debug__ and ["-O"] or []
                    subprocess.Popen(["python"] + python_kind + ["sulci_train.py", training_kind, "--mode=slave"])
                # Set the mode to the trainer
                self.MODE = "master"
                # Wait to leave time to slave to launch
                time.sleep(1)
            if self.LEXICAL:
                T = LexicalTrainer(P, C, self.MODE)
                T.do()
            elif self.CONTEXTUAL:
                T = ContextualTrainer(P, C, self.MODE)
                T.do()
            elif self.LEMMATIZER:
                T = LemmatizerTrainer(M, self.MODE)
                T.do()
            elif self.PMI:
                T = Thesaurus()
                G = GlobalPMITrainer(T, P, self.MODE)
                G.do()
            elif self.SEMANTICAL:
                T = Thesaurus()
                S = SemanticalTrainer(T, P, self.MODE)
                if self.PK:
                    # Should not have PK in MODE == "master"
                    a = config.content_model_getter(self.PK)
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
                    a = config.content_model_getter(self.PK)
                    t = getattr(a, config.SULCI_CONTENT_PROPERTY)
                    T = TextCorpus()
                    T.prepare(t, P, M)
                    T.export(self.PK, self.FORCE, self.ADD_LEMMES)
            if self.IPDB:
                import ipdb
                ipdb.set_trace()

if __name__ == '__main__':
    command = Command()
    command.handle()
