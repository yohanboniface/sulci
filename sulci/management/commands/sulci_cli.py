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


class SulciBaseCommand(BaseCommand):
    """
    Common options and methods for all sulci commands
    """
    option_list = BaseCommand.option_list + (
        make_option("-f", "--force", action="store_true", dest="force", 
                    help="Some options can take a FORCE option"),
        make_option("-d", "--ipdb", action="store_true", dest="ipdb", 
                    help="Launch ipdb at the end of the process"),
        make_option("-k", "--pk", action="store", type="int", dest="pk",
                    default = None, help = "Pk of model to process"),
        make_option("-l", "--limit", type="int", action="store", dest="limit",
                    default=None, help = "Limit the process."),
        )
    
    def handle(self, *args, **options):
        for option in self.option_list:
            setattr(self, option.dest.upper(), options.get(option.dest))

class Command(SulciBaseCommand):
    """
    Launch suci semantical tagger.
    """
    help = __doc__
    
    def handle(self, *args, **options):
        super(Command, self).handle(self, *args, **options)
        if not self.PK:
            sulci_logger.info(u"A PK is needed. Use -k xxx", "RED")
        else:
            C = Corpus()
            L = Lexicon()
            P = PosTagger(lexicon=L)
            M = Lemmatizer(L)
            a = content_model.objects.get(pk=self.PK)
            t = getattr(a, settings.SULCI_CONTENT_PROPERTY)
            T = Thesaurus()
            S = SemanticalTagger(t, T, P, lexicon=L)
            if __debug__:
                S.debug()
            sulci_logger.info(u"Scored descriptors", "YELLOW", True)
            for d, value in S.descriptors:
                print u"%s %f" % (unicode(d), value)
            
        if self.IPDB:
            import ipdb; ipdb.set_trace()

if __name__ == '__main__':
    main()
