#!/usr/bin/env python
# -*- coding:Utf-8 -*-
import time

from sulci.pos_tagger import PosTagger
from sulci.lexicon import Lexicon
from sulci.corpus import Corpus, TextCorpus
from sulci.textmining import SemanticalTagger
from sulci.thesaurus import Thesaurus
from sulci.log import sulci_logger
from sulci.trainers import SemanticalTrainer, LemmatizerTrainer, LexicalTrainer,\
                                                   ContextualTrainer, POSTrainer
from sulci.lemmatizer import Lemmatizer
from sulci.utils import load_file
from sulci_cli import SulciBaseCommand

class Command(SulciBaseCommand):
    """
    Command for monitoring the corpus and data of Sulci.
    """
    help = __doc__

    def define_args(self):
        super(Command, self).define_args()
        self.parser.add_argument(
            "-u",
            "--check_corpus",
            action="store_true", 
            dest="check_corpus", default = None, 
            help="""
                 Check the corpus.
                 Use -w, -g or -p to specify what to check.
                 Use -p to specify a path to check a specific text.
                 """
        )
        self.parser.add_argument(
            "-x",
            "--check_lexicon",
            action="store_true",
            dest="check_lexicon",
            default = None, 
            help="Check lexicon. Use -w to check a specific word to check."
        )
        self.parser.add_argument(
            "-w",
            "--word",
            action="store",
            type=str,
            dest="word",
            default = None, 
            help="Retrieve word usage in corpus."
        )
        self.parser.add_argument(
            "-e",
            "--display_errors",
            action="store_true",
            dest="display_errors", 
            help="Display errors remaining in corpus after runing the pos tagger."
        )
        self.parser.add_argument(
            "-c",
            "--count",
            action="store_true",
            dest="count", 
            help="Display number of words. Use -u or -x to specify corpus of lexicon"
        )
        self.parser.add_argument(
            "-g",
            "--tags_stats",
            action="store_true",
            dest="tags_stats", 
            help="Display tags usage statistics. Use -w to specify a word."
        )
        self.parser.add_argument(
            "-m",
            "--use_lemmes",
            action="store_true",
            dest="use_lemmes", 
            help="Use lemmes"
        )
        self.parser.add_argument(
            "-M",
            "--lemme",
            action="store",
            type=str,
            dest="lemme", 
            default=None,
            help = "Specify a lemme when needed"
        )
        self.parser.add_argument(
            "-t",
            "--tag",
            action="store",
            type=str,
            dest="tag", 
            default=None, help = "Specify a tag when needed"
        )
        self.parser.add_argument(
            "-p",
            "--path",
            action="store",
            type=str,
            dest="path", 
            default=None,
            help="Specify a file path when needed. Relative to /sulci/"
        )
        self.parser.add_argument(
            "-i",
            "--case_insensitive",
            action="store_true",
            dest="case_insensitive", 
            help="Case insensitive"
        )
    
    def handle(self, *args, **options):
        C = Corpus()
        L = Lexicon()
        P = PosTagger(lexicon=L)
        M = Lemmatizer(L)
        if self.WORD:
            self.WORD = self.WORD.decode("utf-8")
        if self.LEMME:
            self.LEMME = self.LEMME.decode("utf-8")
        if self.CHECK_LEXICON:
            if self.COUNT:
                sulci_logger.info(u"Words in lexicon : %d" % len(L), "WHITE")
            elif self.WORD:
                L.get_entry(self.WORD)
            else:
                L.check()
        elif self.CHECK_CORPUS:
            if self.PATH:
                corpus = TextCorpus(self.PATH)
            else:
                corpus = C
            if self.COUNT:
                sulci_logger.info(u"Words in corpus : %d" % len(corpus), "WHITE")
            elif self.TAGS_STATS:
                corpus.tags_stats(self.WORD, self.CASE_INSENSITIVE)
            elif self.WORD or self.TAG or self.LEMME:
                corpus.check_usage(
                    word=self.WORD, 
                    tag=self.TAG, 
                    lemme=self.LEMME,
                    case_insensitive=self.CASE_INSENSITIVE
                )
            else:
                corpus.check(L, self.USE_LEMMES)
        if self.DISPLAY_ERRORS:
            T = POSTrainer(P,C)
            T.display_errors()
        if self.IPDB:
            import ipdb; ipdb.set_trace()

if __name__ == '__main__':
    command = Command()
    command.handle()