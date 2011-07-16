#!/usr/bin/env python
# -*- coding:Utf-8 -*-
import time

from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings

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
from sulci import content_model
from sulci_cli import SulciBaseCommand

class Command(SulciBaseCommand):
    """
    Command for monitoring the corpus and data of Sulci.
    """
    help = __doc__
    option_list = SulciBaseCommand.option_list + (
        make_option("-c", "--check_corpus", action="store_true", 
                    dest="check_corpus", default = None, 
                    help = "Check the corpus. Use -w, -t or -p to specify what."),
        make_option("-w", "--word", action="store", type="string", 
                    dest="word", default = None, 
                    help = "Retrieve word usage in corpus."),
        make_option("-x", "--check_entry", action="store", type="string", 
                    dest="check_entry", default = None, 
                    help = "Retrive entry in lexicon."),
        make_option("-e", "--display_errors", action="store_true", dest="display_errors", 
                    help = "Display errors remaining in corpus after runing the pos tagger."),
        make_option("-q", "--check_lexicon", action="store_true", 
                    dest="check_lexicon", 
                    help = "Display multivaluate entries of lexicon."),
        make_option("-o", "--lexicon_count", action="store_true", 
                    dest="lexicon_count", 
                    help = "Display number of words in lexicon"),
        make_option("-u", "--corpus_count", action="store_true", dest="corpus_count", 
                    help = "Display number of words in corpus"),
        make_option("-g", "--tags_stats", action="store_true", dest="tags_stats", 
                    help = "Display tags usage statistics"),
        make_option("-m", "--use_lemmes", action="store_true", dest="use_lemmes", 
                    help = "Use lemmes"),
        make_option("-t", "--tag", action="store", type="string", dest="tag", 
                    default=None, help = "Specify a tag when needed"),
        make_option("-p", "--path", action="store",type="string", dest="path", 
                    default=None,
                    help = "Specify a file path when needed. Relative to /sulci/"),
        )
    
    def handle(self, *args, **options):
        super(Command, self).handle(self, *args, **options)
        C = Corpus()
        L = Lexicon()
        P = PosTagger(lexicon=L)
        M = Lemmatizer(L)
        if self.CHECK_LEXICON:
            L.check()
        if self.CHECK_CORPUS:
            if self.PATH:
                T = TextCorpus(self.PATH)
                T.check(L, self.USE_LEMMES)
            else:
                if self.WORD:
                    self.WORD = self.WORD.decode("utf-8")
                C.check_usage(word=self.WORD, tag=self.TAG)
        if self.DISPLAY_ERRORS:
            T = POSTrainer(P,C)
            T.display_errors()
        if self.CHECK_ENTRY:
            L.get_entry(self.CHECK_ENTRY.decode("utf-8"))
        if self.LEXICON_COUNT:
            sulci_logger.info(u"Words in lexicon : %d" % len(L), "WHITE")
        if self.CORPUS_COUNT:
            sulci_logger.info(u"Words in corpus : %d" % len(C), "WHITE")
        if self.TAGS_STATS:
            C.tags_stats()
        if self.IPDB:
            import ipdb; ipdb.set_trace()

if __name__ == '__main__':
    main()
