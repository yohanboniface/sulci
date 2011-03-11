#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings

from sulci.pos_tagger import PosTagger, LexicalTrainer, ContextualTrainer, Trainer
from sulci.lexicon import Lexicon
from sulci.corpus import Corpus
from sulci.textmining import SemanticalTagger
from sulci.thesaurus import Thesaurus
from sulci.utils import log
from sulci.trainers import SemanticalTrainer, LemmatizerTrainer
from sulci.lemmatizer import Lemmatizer
from __init__ import content_model# ugly

class Command(BaseCommand):
    """
    Manage sulci textmining. TODO more later.
    """
    help = __doc__
    option_list = BaseCommand.option_list + (
        make_option("-m", 
                    "--makedict", 
                    action="store_true", 
                    dest="makedict", 
                    help = "Build the lexicon"),
        make_option("-i", 
                    "--lexical_traintagger", 
                    action="store_true", 
                    dest="lexical_traintagger", 
                    help = "Train tagger"),
        make_option("-c", 
                    "--contextual_traintagger", 
                    action="store_true", 
                    dest="contextual_traintagger", 
                    help = "Train tagger"),
        make_option("-l",
                    "--limit", 
                    type="int", 
                    action="store", 
                    dest="limit",
                    default=None,
                    help = "Limit the process."),
        make_option("-f", 
                    "--force", 
                    action="store_true", 
                    dest="force", 
                    help="Some options can take a FORCE option"),
        make_option("-d", 
                    "--ipdb", 
                    action="store_true", 
                    dest="ipdb", 
                    help="Launch ipdb at the end of the process"),
        make_option("-p", 
                    "--preparetext", 
                    action="store", 
                    type="string", 
                    dest="preparetext",
                    default = None, 
                    help="Name of the text to prepare, without extension"),
        make_option("-t", 
                    "--trainer_mode", 
                    action="store", 
                    type="string", 
                    dest="trainer_mode",
                    default = None, 
                    help="Trainer mode : master, slave, or full (default)"),
        make_option("-a", 
                    "--addcandidate", 
                    action="store_true", 
                    dest="addcandidate", 
                    help="Prepare article for manual POS indexing"),
        make_option("-k",
                    "--pk", 
                    action="store", 
                    type="int", 
                    dest="pk",
                    default = None, 
                    help = "Pk of article to process with sementictagger"),
        make_option("-w", 
                    "--checkword", 
                    action="store", 
                    type="string", 
                    dest="checkword",
                    default = None, 
                    help = "Retrieve word usage in corpus."),
        make_option("-x", 
                    "--checkentry", 
                    action="store", 
                    type="string", 
                    dest="checkentry",
                    default = None, 
                    help = "Retrive entry in lexicon."),
        make_option("-e", 
                    "--display_errors", 
                    action="store_true", 
                    dest="display_errors", 
                    help = "Display errors remaining in corpus after runing the pos tagger."),
        make_option("-o", 
                    "--lexicon_count", 
                    action="store_true", 
                    dest="lexicon_count", 
                    help = "Display number of words in lexicon"),
        make_option("-u", 
                    "--corpus_count", 
                    action="store_true", 
                    dest="corpus_count", 
                    help = "Display number of words in corpus"),
        make_option("-g", 
                    "--tags_stats", 
                    action="store_true", 
                    dest="tags_stats", 
                    help = "Display tags usage statistics"),
        make_option("-r", 
                    "--lemmatizer_training", 
                    action="store_true", 
                    dest="lemmatizer_training", 
                    help = "Launch Lemmatizer training."),
        make_option("-s", 
                    "--subprocesses", 
                    action="store", 
                    type="int", 
                    dest="subprocesses",
                    default = None, help = "Launch trainer with x subprocesses"),
        make_option("-n", 
                    "--semantical_trainer", 
                    action="store_true", 
                    dest="semantical_trainer", 
                    help = "Launch the sementical training"),
        make_option("-z", 
                    "--semantical_tagger", 
                    action="store_true", 
                    dest="semantical_tagger", 
                    help = "Launch the sementical tagging of a text. Needs a pk.")
        )
    
    def handle(self, *args, **options):
        MAKE_DICT = options.get("makedict")
        LEXICAL_TRAIN_TAGGER = options.get("lexical_traintagger")
        CONTEXTUAL_TRAIN_TAGGER = options.get("contextual_traintagger")
        PREPARE_TEXT = options.get("preparetext")
        ADD_CANDIDATE = options.get("addcandidate")
        CHECK_WORD = options.get("checkword")
        CHECK_ENTRY = options.get("checkentry")
        DISPLAY_ERRORS = options.get("display_errors")
        FORCE = options.get("force")
        IPDB = options.get("ipdb")
        LIMIT = options.get("limit")
        PK = options.get("pk")
        TRAINER_MODE = options.get("trainer_mode")
        SUBPROCESSES = options.get("subprocesses")
        LEXICON_COUNT = options.get("lexicon_count")
        CORPUS_COUNT = options.get("corpus_count")
        TAGS_STATS = options.get("tags_stats")
        SEMANTICAL_TRAINER = options.get("semantical_trainer")
        SEMANTICAL_TAGGER = options.get("semantical_tagger")
        LEMMATIZER_TRAINING = options.get("lemmatizer_training")
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
                a = content_model.objects.get(pk=PK)
                t = getattr(a, settings.SULCI_CONTENT_PROPERTY)
                C.add_candidate(t, PK)
                C.prepare_candidate(PK)
        if SUBPROCESSES:
            import subprocess
            training_kind = LEXICAL_TRAIN_TAGGER and "-i" or "-c"
            # Create slaves
            for i in xrange(0,SUBPROCESSES):
                log(u"Opening slave subprocess %d" % i, "BLUE", True)
                python_kind = not __debug__ and ["-O"] or []
                subprocess.Popen(["python"] + python_kind + ["manage.py", training_kind, "--trainer_mode=slave"])
            # Set the mode to the trainer
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
                if FORCE:# otherwise it has no sens, as the list will not be overwrited
                    manager = getattr(content_model, settings.SULCI_CONTENT_MANAGER_METHOD_NAME)
                    qs = manager.all()
                    if LIMIT:
                        qs = qs[:LIMIT]
#                    for a in Article.objects.filter(editorial_source=Article.EDITORIAL_SOURCE.PRINT).exclude(keywords__isnull=True).exclude(keywords=""):
                    for a in qs:
                        S.train(getattr(a, settings.SULCI_CONTENT_PROPERTY), getattr(a, settings.SULCI_KEYWORDS_PROPERTY))
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
            a = content_model.objects.get(pk=PK)
#            t = a.title + ". " + a.subtitle + ". " + a.content#Make some method
            t = getattr(a, settings.SULCI_CONTENT_PROPERTY)
            T = Thesaurus()
            S = SemanticalTagger(t, T, P)
            if __debug__:
                S.debug()
        if IPDB:
            import ipdb; ipdb.set_trace()

if __name__ == '__main__':
    main()
