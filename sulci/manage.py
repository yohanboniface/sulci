#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from optparse import OptionParser

from pos_tagger import PosTagger, LexicalTrainer, ContextualTrainer, Trainer
from lexicon import Lexicon
from corpus import Corpus
from textmining import SemanticalTagger
from thesaurus import Thesaurus
from utils import log
from trainers import SemanticalTrainer, LemmatizerTrainer
from lemmatizer import Lemmatizer

def main():
    """
    Main function
    """
    # Manage command options
    p = OptionParser()
    p.add_option("-m", "--makedict", action="store_true", dest="makedict", help = "Build the lexicon")
    p.add_option("-l", "--lexical_traintagger", action="store_true", dest="lexical_traintagger", help = "Train tagger")
    p.add_option("-c", "--contextual_traintagger", action="store_true", dest="contextual_traintagger", help = "Train tagger")
    p.add_option("-d", "--debug", action="store_true", dest="debug", help = "Print detailed result")
    p.add_option("-f", "--force", action="store_true", dest="force", help = "Some options can take a FORCE option")
    p.add_option("-i", "--ipdb", action="store_true", dest="ipdb", help = "Launch ipdb at the end")
    p.add_option("-p", "--preparetext", action="store", type="string", dest="preparetext",\
                    default = None, help = "Name of the text to prepare, without extension")
    p.add_option("-t", "--trainer_mode", action="store", type="string", dest="trainer_mode",\
                    default = None, help = "Trainer mode : master, slave, or full (default)")
    p.add_option("-a", "--addcandidate", action="store_true", dest="addcandidate", help = "Prepare article for manual POS indexing")
    p.add_option("-k", "--pk", action="store", type="int", dest="pk",\
                    default = None, help = "Pk of article to process with sementictagger")
    p.add_option("-w", "--checkword", action="store", type="string", dest="checkword",\
                    default = None, help = "Retrieve word usage in corpus.")
    p.add_option("-x", "--checkentry", action="store", type="string", dest="checkentry",\
                    default = None, help = "Retrive entry in lexicon.")
    p.add_option("-e", "--display_errors", action="store_true", dest="display_errors", help = "Display errors remaining in corpus after runing the pos tagger.")
    p.add_option("-o", "--lexicon_count", action="store_true", dest="lexicon_count", help = "Display number of words in lexicon")
    p.add_option("-u", "--corpus_count", action="store_true", dest="corpus_count", help = "Display number of words in corpus")
    p.add_option("-g", "--tags_stats", action="store_true", dest="tags_stats", help = "Display tags usage statistics")
    p.add_option("-r", "--lemmatizer_training", action="store_true", dest="lemmatizer_training", help = "Launch Lemmatizer training.")
    p.add_option("-s", "--subprocesses", action="store", type="int", dest="subprocesses",\
                    default = None, help = "Launch trainer with x subprocesses")
    p.add_option("-n", "--semantical_trainer", action="store_true", dest="semantical_trainer", help = "Launch the sementical training")
    p.add_option("-z", "--semantical_tagger", action="store_true", dest="semantical_tagger", help = "Launch the sementical tagging of a text. Needs a pk.")
    (options,args) = p.parse_args()

    MAKE_DICT = options.makedict
    LEXICAL_TRAIN_TAGGER = options.lexical_traintagger
    CONTEXTUAL_TRAIN_TAGGER = options.contextual_traintagger
    PREPARE_TEXT = options.preparetext
    ADD_CANDIDATE = options.addcandidate
    CHECK_WORD = options.checkword
    CHECK_ENTRY = options.checkentry
    DISPLAY_ERRORS = options.display_errors
#    __debug__ = options.debug
    FORCE = options.force
    IPDB = options.ipdb
    PK = options.pk
    TRAINER_MODE = options.trainer_mode
    SUBPROCESSES = options.subprocesses
    LEXICON_COUNT = options.lexicon_count
    CORPUS_COUNT = options.corpus_count
    TAGS_STATS = options.tags_stats
    SEMANTICAL_TRAINER = options.semantical_trainer
    SEMANTICAL_TAGGER = options.semantical_tagger
    LEMMATIZER_TRAINING = options.lemmatizer_training
    C = Corpus()
    L = Lexicon()
    P = PosTagger(lexicon=L)
    C.attach_tagger(P)
    if MAKE_DICT:
        L.make()
    if PREPARE_TEXT is not None:
        C.prepare_candidate(PREPARE_TEXT)
    if CHECK_WORD is not None:
        C.check_word(CHECK_WORD.decode("utf-8"))
    if ADD_CANDIDATE:
        if not PK:
            print "A PK is needed."
        else:
            C.add_candidate(Article.objects.get(pk=PK).content, PK)
            C.prepare_candidate(PK)
    if SUBPROCESSES:
        import subprocess
        training_kind = LEXICAL_TRAIN_TAGGER and "-l" or "-c"
        #Create slaves
        for i in xrange(0,SUBPROCESSES):
            log(u"Opening slave subprocess %d" % i, "BLUE", True)
            subprocess.Popen(["python", "manage.py", training_kind, "--trainer_mode=slave"])
        #Set the mode to the trainer
        TRAINER_MODE = "master"
    if LEXICAL_TRAIN_TAGGER:
        T = LexicalTrainer(P,C,TRAINER_MODE)
        T.do()
    if CONTEXTUAL_TRAIN_TAGGER:
        T = ContextualTrainer(P,C,TRAINER_MODE)
        T.do()
    if DISPLAY_ERRORS:
        T = Trainer(P,C)
        T.display_errors()
    if SEMANTICAL_TRAINER:
        if FORCE:
            Thesaurus.reset_triggers()
        T = Thesaurus()
        S = SemanticalTrainer(T,P)
        if PK:
            a = Article.objects.get(pk=PK)
            S.train(a.content, a.keywords)
        else:
            S.begin()
            if FORCE:#otherwise it has no sens, as the list will not be overwrited
                for a in Article.objects.filter(editorial_source=Article.EDITORIAL_SOURCE.PRINT).exclude(keywords__isnull=True).exclude(keywords=""):
                    S.train(a.title + ". " + a.subtitle + ". " + a.content, a.keywords)
        S.export(FORCE)
    if CHECK_ENTRY:
        L.get_entry(CHECK_ENTRY.decode("utf-8"))
    if LEXICON_COUNT:
        log(u"Words in lexicon : %d" % len(L), "WHITE")
    if CORPUS_COUNT:
        log(u"Words in corpus : %d" % len(C), "WHITE")
    if TAGS_STATS:
        C.tags_stats()
    if LEMMATIZER_TRAINING:
        L = Lemmatizer()
        T = LemmatizerTrainer(L)
        T.train()
    if SEMANTICAL_TAGGER and PK:
        a = Article.objects.get(pk=PK)
        t = a.title + ". " + a.subtitle + ". " + a.content#Make some method
        T = Thesaurus()
        S = SemanticalTagger(t, T, P)
        if __debug__:
            S.debug()
    if IPDB:
        import ipdb; ipdb.set_trace()

if __name__ == '__main__':
    main()
