#!/usr/bin/env python
# -*- coding:Utf-8 -*-
import time
import argparse

from sulci.pos_tagger import PosTagger
from sulci.lexicon import Lexicon
from sulci.corpus import Corpus, TextCorpus
from sulci.textmining import SemanticalTagger
from sulci.thesaurus import Thesaurus
from sulci.log import sulci_logger
from sulci.lemmatizer import Lemmatizer
from sulci import config

class SulciBaseCommand(object):
    """
    Common options and methods for all sulci commands
    """

    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.define_args()
        args = self.parser.parse_args()
        for arg, value in args.__dict__.iteritems():
            setattr(self, arg.upper(), value)

    def define_args(self):
        self.parser.add_argument(
            "-f",
            "--force",
            action="store_true",
            dest="force",
            help="Some options can take a FORCE option"
        )
        self.parser.add_argument(
            "-d",
            "--ipdb",
            action="store_true",
            dest="ipdb",
            help="Launch ipdb at the end of the process"
        )
        self.parser.add_argument(
            "-k",
            "--pk",
            action="store",
            type=str,
            dest="pk",
            default=None,
            help="Pk of model to process"
        )
        self.parser.add_argument(
            "-l",
            "--limit",
            type=int,
            action="store",
            dest="limit",
            default=None, help = "Limit the process."
        )


class Command(SulciBaseCommand):
    """
    Launch sulci semantical tagger. See options for details.
    """
    help = __doc__
    
    def handle(self, *args):
        if not self.PK:
            sulci_logger.info(u"A PK is needed. Use -k xxx", "RED")
        else:
            C = Corpus()
            L = Lexicon()
            P = PosTagger(lexicon=L)
            M = Lemmatizer(L)
            a = config.content_model_getter(self.PK)
            t = getattr(a, config.SULCI_CONTENT_PROPERTY)
            T = Thesaurus()
            S = SemanticalTagger(t, T, P, lexicon=L)
            if __debug__:
                S.debug()
            sulci_logger.info(u"Scored descriptors", "YELLOW", True)
            for d, value in S.descriptors:
                sulci_logger.info(u"%s %f" % (unicode(d), value), "BLUE")
            
        if self.IPDB:
            import ipdb; ipdb.set_trace()

if __name__ == '__main__':
    command = Command()
    command.handle()
