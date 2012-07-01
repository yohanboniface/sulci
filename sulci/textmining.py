#!/usr/bin/env python
# -*- coding:Utf-8 -*-

import os
import re
import urllib2
import time, datetime
import math

from collections import defaultdict
from operator import itemgetter
from GenericCache.GenericCache import GenericCache
from GenericCache.decorators import cached

from sulci.utils import uniqify, sort, product
from sulci.stopwords import stop_words, usual_words
from sulci.textutils import lev, normalize_text, words_occurrences
from sulci.base import RetrievableObject, Token, TextManager
from sulci.pos_tagger import PosTagger
from sulci.lexicon import Lexicon
from sulci.thesaurus import Trigger, Thesaurus
from sulci.lemmatizer import Lemmatizer
from sulci.log import sulci_logger

#Cache
cache = GenericCache()

class StemmedText(TextManager):
    """
    Basic text class, with tokens, samples, etc.
    """
    def __init__(self, text, pos_tagger=None, lemmatizer=None, lexicon=None):
        self._raw_text = text
        self.normalized_text = normalize_text(text)
        if len(self.normalized_text) == 0:
            # For now, raise value error, because an empty text create
            # too much problems here and there (zero division, etc.)
            # TODO : make empty texts possible.
            raise ValueError("Can't process an empty text.")
        self.samples = []
        self.keyentities = []
        self.lexicon = lexicon or Lexicon()
        self.postagger = pos_tagger or PosTagger(lexicon=self.lexicon)
        self.lemmatizer = lemmatizer or Lemmatizer(self.lexicon)
        self.make()
        self._stemms = None
    
    def __iter__(self):
        return self.words.__iter__()
    
    def __len__(self):
        return len(self.words)
    
    def make(self):
        """
        Text is expected to be tokenized.
        And filtered ?
        """
        self.samples, self.tokens = self.instantiate_text(self.tokenize(self.normalized_text))
        self.postagger.tag_all(self.tokens)
        self.create_stemm()
    
    def create_stemm(self):
        self._stemms = set() # A set because order don't mind
                             # And we want no duplicates
        for tkn in self.tokens:
            self.lemmatizer.do(tkn)
            # We don't take the sg or pl in the tag name
            stm, created = Stemm.get_or_create((unicode(tkn.lemme), tkn.tag.split(u":")[0]), self, original=unicode(tkn.lemme), text=self)
            stm.occurrences.append(tkn)
            tkn.stemm = stm
            self._stemms.add(stm)
        sulci_logger.debug("Initial stemms", "BLUE", highlight=True)
        sulci_logger.debug([unicode(s) for s in self._stemms], "CYAN")
    
    @property
    @cached(cache)
    def medium_word_count(self):
        """
        The medium occurrences count.
        """
        return float(len(self.words)) / len(set(self.distinct_words()))

    @property
    def words(self):
        return [w for s in self.samples for w in s]

    @property
    def meaning_words(self):
        return [w for s in self.samples for w in s if w.has_meaning()]

    @property
    def stemms(self):
        if self._stemms is None: # Should not occurs
            self._stemms = uniqify([t.stemm for t in self.meaning_words], lambda x: x.id)
        return self._stemms

    def words_count(self):
        """
        Return the number of words in the text.
        """
        return sum([len(s) for s in self.samples])

    def meaning_words_count(self):
        """
        Return the number of words in the text.
        """
        return sum([s.meaning_words_count() for s in self.samples])
    
    def distinct_words(self):
        return uniqify(self.words, lambda x: x.original)
    
    def distincts_meaning_words(self):
        return uniqify(self.meaning_words, lambda x: x.original)


class SemanticalTagger(object):
    """
    Main class.
    """
    def __init__(self, text, thesaurus=None, pos_tagger=None, lemmatizer=None, lexicon=None):
        self.thesaurus = thesaurus or Thesaurus()
        if isinstance(text, StemmedText):
            self.text = text
        else:
            self.text = StemmedText(text, pos_tagger, lemmatizer, lexicon)
        self.keyentities = []
        self.lexicon = lexicon or Lexicon()
        self.postagger = pos_tagger or PosTagger(lexicon=self.lexicon)
        self.lemmatizer = lemmatizer or Lemmatizer(self.lexicon)
        self.make_keyentities()
        self._triggers = None
        self._stemms = None
    
    def keystems(self, min_count=3):
        #Min_count may be proportionnal to text length...
        return sort([s for s in self.text.stemms if s.has_interest_alone()], "count", reverse=True)
    
    def ngrams(self, min_length = 2, max_length = 15, min_count = 2):
        final = {}
    #    sentence = tuple(sentences[0])
        for idxs, sentence in enumerate(self.text.samples):
            sentence = tuple(sentence)
            for begin in range(0,len(sentence)):
                id_max = min(len(sentence) + 1, begin + max_length + 1)
                for end in range(begin + min_length, id_max):
                    g = sentence[begin:end]
                    #We make the comparison on stemmes
                    idxg = tuple([w.stemm for w in g])
                    if not g[0].has_meaning() or not g[len(g)-1].has_meaning():
                        continue#continuing just this for loop. Good ?
#                    if "projet" in g: sulci_logger.debug(g, RED)
#                    if g[1].original == "Bourreau" and len(g) == 2: print g
                    if not idxg in final:
                        final[idxg] = {"count": 1, "stemms": [t.stemm for t in g]}
                    else:
                        final[idxg]["count"] += 1
#                        if g[1].original == "Bourreau" and len(g) == 2: print "yet", idxg, final[idxg]['stemms'], final[idxg]["count"]
#        return final
#        pouet = sorted([u" ".join([s.main_occurrence.original for s in v["stemms"]]) for k, v in final.iteritems()])
#        for ppouet in pouet:
#            print ppouet
        return sorted([(v["stemms"], v["count"]) for k, v in final.iteritems() if self.filter_ngram(v)], key=itemgetter(1), reverse=True)

    def filter_ngram(self, candidate):
        """
        Here we try to keep the right ngrams to make keyentities.
        """
        return candidate["count"] >= 2 \
               or all([s.istitle() for s in candidate["stemms"]]) \
               or False

    def make_keyentities(self, min_length = 2, max_length = 10, min_count = 2):
        # From ngrams
        keyentities = []
        candidates = self.ngrams()
        # Candidates are tuples : (ngram, ngram_score)
        sulci_logger.debug("Ngrams candidates", "BLUE", highlight=True)
        for c in candidates:
            sulci_logger.debug([unicode(s) for s in c[0]], "CYAN")
        for candidate in candidates:
            kp, created = KeyEntity.get_or_create([unicode(s.main_occurrence) for s in candidate[0]],
                                                  self.text,
                                                  stemms=candidate[0], 
                                                  count=candidate[1],
                                                  text=self.text)
            keyentities.append(kp)
        # From frequency
        candidates = self.keystems()
        sulci_logger.debug("Frequent stems candidates", "BLUE", highlight=True)
        for c in candidates:
            sulci_logger.debug(unicode(c), "CYAN")
        for candidate in candidates:
            kp, created = KeyEntity.get_or_create([unicode(candidate.main_occurrence)], 
                                                  self.text,
                                                  stemms=[candidate], 
                                                  count=candidate.count,
                                                  text=self.text)
            keyentities.append(kp)
        self.keyentities = keyentities
#        self.deduplicate_keyentities()
    
    def deduplicate_keyentities(self):
        """
        If a KeyEntity is contained in an other (same stemms in same place) longuer
        delete the one with the smaller confidence, or the shortest if same confidence
        We have to begin from the shortest ones.
        """
        sulci_logger.debug(u"Deduplicating keyentities...", "BLUE", highlight=True)
        tmp_keyentities = sorted(self.keyentities, key=lambda kp: len(kp))
        sulci_logger.debug([unicode(kp) for kp in tmp_keyentities], "GRAY")
        for idx, one in enumerate(tmp_keyentities):
            for two in tmp_keyentities[idx+1:]:
                if one in self.keyentities and two in self.keyentities:
                    if one.is_duplicate(two):
                        sulci_logger.debug(u"%s is duplicate %s" % (unicode(one), unicode(two)), "MAGENTA")
                        if one > two:#and not two.is_strong()
                            sulci_logger.debug(u"%s will be deleted" % unicode(two), "RED")
                            self.keyentities.remove(two)
                        elif two > one:
                            sulci_logger.debug(u"%s will be deleted" % unicode(one), "RED")
                            self.keyentities.remove(one)
                        else:
                            sulci_logger.debug(u"No deletion")
        sulci_logger.debug(u"... keyentities deduplicated", "BLUE", highlight=True)
    
    def keyentities_for_trainer(self):
        return sorted(self.keyentities, key=lambda kp: kp.frequency_relative_pmi_confidence * kp._confidences["pos"], reverse=True)[:20]
    
    @property
    def triggers(self):
        """
        Select triggers available for the current keyentities.
        """
        if self._triggers is None:
            self._triggers = set()
            for kp in self.keyentities:
                try:
                    t = Trigger.get(original=unicode(kp))
                    self._triggers.add((t, kp.trigger_score))
                except Trigger.DoesNotExist:
                    pass
        return self._triggers
    
    @property
    def descriptors(self):
        return self.get_descriptors()
    
    def get_descriptors(self, min_score=10):
        """
        Final descriptors for the text.
        
        Only descriptors triggered up to min_score will be returned.
        """
        self._scored_descriptors = {}
        total_score = 0
        max_score = 0
        for t, score in self.triggers:
            # Take the trigger relations
            for d in t:
                # Preventing from rehiting the db
                # By him-self, Django to retrieve the reverse FK in the cache...
                if d.weight.hget() > 2: # How to define this min ?
                    key = d.descriptor.pk.get()
                    # Add the descriptor if needed
                    if not key in self._scored_descriptors:
                        self._scored_descriptors[key] = {"weight":0, "descriptor": d.descriptor}
                    # Trying to keep the same instance when the same
                    # descriptor is seen few times (should occurs)
                    d._descriptor = self._scored_descriptors[key]["descriptor"]
                    # Update descriptor final score
                    self._scored_descriptors[key]["weight"] += d.pondered_weight * score
            total_score += score
            max_score = max(max_score,score)
        # We make a percentage of the max score possible
        for key, d in self._scored_descriptors.items():
            self._scored_descriptors[key]["weight"] = d["weight"] / max_score * 100.0
        return [
            (d["descriptor"], d["weight"]) for key,d in 
            sorted(self._scored_descriptors.items(), key=lambda t: t[1]["weight"], reverse=True) 
            if d["weight"] > min_score
               ]
    
    def debug(self):
        sulci_logger.debug("Normalized text", "WHITE")
        sulci_logger.debug(self.text.normalized_text, "WHITE")
        sulci_logger.debug("Number of words", "WHITE")
        sulci_logger.debug(self.text.words_count(), "GRAY")
        sulci_logger.debug("Number of meaning words", "WHITE")
        sulci_logger.debug(self.text.meaning_words_count(), "GRAY")
        sulci_logger.debug("Number of differents words", "WHITE")
        sulci_logger.debug(len(self.text.distinct_words()), "GRAY")
        sulci_logger.debug("Frequents stemms", "WHITE")
        sulci_logger.debug([(unicode(s), s.count) for s in self.keystems()], "GRAY")
        sulci_logger.debug("Lexical diversity", "WHITE")
        sulci_logger.debug(1.0 * len(self.text.words) / len(set(self.text.distinct_words())), "GRAY")
        sulci_logger.debug("Tagged words", "WHITE")
        sulci_logger.debug([(unicode(t), t.tag) for t in self.text.tokens], "GRAY")
        sulci_logger.debug("Sentences", "WHITE")
        for sample in self.text.samples:
            sulci_logger.debug(sample, "GRAY")
        sulci_logger.debug("Final keyentities", "WHITE")
        for kp in sorted(self.keyentities, key=lambda kp: kp.keyconcept_confidence):
            sulci_logger.debug(u"%s (%f)" % (unicode(kp), kp.confidence), "YELLOW")
            sulci_logger.debug(kp._confidences, "GRAY")
        sulci_logger.debug(u"Keyentities by keyconcept_confidence", "BLUE", True)
        for kp in sorted(self.keyentities, key=lambda kp: kp.keyconcept_confidence, reverse=True)[:10]:
            sulci_logger.debug(u"%s (%f)" % (unicode(kp), kp.keyconcept_confidence), "YELLOW")
        sulci_logger.debug(u"Keyentities by statistical_mutual_information_confidence", "BLUE", True)
        for kp in sorted(self.keyentities, key=lambda kp: kp._confidences["statistical_mutual_information"], reverse=True)[:10]:
            sulci_logger.debug(u"%s (%f)" % (unicode(kp), kp._confidences["statistical_mutual_information"]), "YELLOW")
        sulci_logger.debug(u"Keyentities by pos_confidence", "BLUE", True)
        for kp in sorted(self.keyentities, key=lambda kp: kp._confidences["pos"], reverse=True)[:10]:
            sulci_logger.debug(u"%s (%f)" % (unicode(kp), kp._confidences["pos"]), "YELLOW")
        sulci_logger.debug(u"Keyentities by frequency_relative_pmi_confidence", "BLUE", True)
        for kp in sorted(self.keyentities, key=lambda kp: kp.frequency_relative_pmi_confidence, reverse=True)[:10]:
            sulci_logger.debug(u"%s (%f)" % (unicode(kp), kp.frequency_relative_pmi_confidence), "YELLOW")
        sulci_logger.debug(u"Keyentities by keyconcept_confidence * pos confidence", "BLUE", True)
        for kp in sorted(self.keyentities, key=lambda kp: kp.keyconcept_confidence * kp._confidences["pos"], reverse=True)[:10]:
            sulci_logger.debug(u"%s (%f)" % (unicode(kp), kp.keyconcept_confidence * kp._confidences["pos"]), "YELLOW")
        sulci_logger.debug(u"Keyentities by nrelative * pos confidence", "BLUE", True)
        for kp in sorted(self.keyentities, key=lambda kp: kp.trigger_score, reverse=True)[:20]:
            sulci_logger.debug(u"%s (%f)" % (unicode(kp), kp.trigger_score), "YELLOW")
        sulci_logger.debug(u"Triggers and relation with descriptors", "BLUE", True)
        for t, score in self.triggers:
            if len(t._synapses) > 0:
                sulci_logger.debug(u"%s (Local score : %f)" % (unicode(t), score), "GRAY", highlight=True)
                sulci_logger.debug(u"Trigger total count : %s" % t.count.hget(), "GRAY")
                for d in sorted(t, key=lambda t2d: t2d.weight, reverse=True):
                    sulci_logger.debug(u"%s %f" % (unicode(d), d.pondered_weight), "CYAN")

class KeyEntity(RetrievableObject):
    count = 0
    _confidences = {}

    def __init__(self, pk, **kwargs):
        self.id = pk
        self.stemms = kwargs["stemms"]
        self.count = kwargs["count"]
        self.text = kwargs["text"]
        self._confidences = {"frequency": None,
                            "title": None,
                            "heuristical_mutual_information": None,
                            "statistical_mutual_information": None,
                            "nrelative_frequency": None,
#                            "thesaurus": None,
                            "pos": None
                           }
        self.compute_confidence()
        self._istitle = None
    
    def __unicode__(self):
        return u" ".join([unicode(t.main_occurrence) for t in self.stemms])
    
    def __repr__(self):
        return u"<KE %s>" % u" ".join([repr(t) for t in self.stemms]).decode("utf-8")
    
    def __iter__(self):
        return self.stemms.__iter__()
    
    def __len__(self):
        return len(self.stemms)

    def __getitem__(self, key):
        return self.stemms[key]

    def __eq__(self, other):
        """
        This is NOT for confidence or length comparison.
        For this use is_equal
        This is for content comparison.
        """
        return self.stemms == other.stemms

    def is_equal(self, other):
        """
        This is for confidence and length comparison.
        NOT for content comparison.
        """
        return self.confidence == other.confidence and len(self) == len(other)

    def __gt__(self, other):
        """
        We try here to define which from two keyentities competitor is the 
        best concentrate of information.
        (Remember that if an expression A is included in B, A is mathematicaly
        almost frequent than B.)
        Examples :
        - Ernesto Che Guevara, is more informative than "Che" or "Che 
        Guevara", even if "Che Guevara" is very more frequent.
        - "loi Création et Internet" is more concentrate, and so more informative,
        than "le projet de loi Création et Internet"
        - "ministère de la Culture" is more informative than "Culture" and "ministère"
        """
        #First of all, we check that both are competitors
        if not self in other and not other in self:
            raise ValueError("keyentities must be parent for this comparison.")
        sulci_logger.debug(u"Comparing '%s' and '%s'" % (unicode(self), unicode(other)), "GRAY")
        sulci_logger.debug(self._confidences, "WHITE")
        sulci_logger.debug(other._confidences, "WHITE")
        # If there is a title in the comparison, make a special case
        if self.istitle() and other.istitle():
            # If both are title, use PMI
            return self.statistical_mutual_information_confidence() > other.statistical_mutual_information_confidence()
        elif self.istitle() or other.istitle():
            # If just one is title: do nothing
            # Idea : prevent from deleting "Laurent Gbagbo" because of "président
            # sortant Laurent Gbagbo" many times in a text (as an example)
            # And in the same time prevent from deleting "Forces républicaines"
            # because "Forces" is title, and not "Forces républicaines"
            # This make more false positive cases, but make also more true positive
            # More false positive means also more noise, and so
            # maybe there the scenario for training should be different
            # to create the less noise relations possible
            return False
        else: # No title in the comparison
            if not self.statistical_mutual_information_confidence() == other.statistical_mutual_information_confidence():
                return self.statistical_mutual_information_confidence() > other.statistical_mutual_information_confidence()
            elif not self.heuristical_mutual_information_confidence() == other.heuristical_mutual_information_confidence():
                return self.heuristical_mutual_information_confidence() > other.heuristical_mutual_information_confidence()
            elif not self.confidence == other.confidence:
                return self.confidence > other.confidence
            elif not len(self) == len(other):
                return len(self) > len(other)
            else: return False

    def __lt__(self, other):
        return other > self
#        if other.confidence > self.confidence: return True
#        elif other.confidence == self.confidence \
#             and len(other) > len(self): return True
#        else: return False

    def __le__(self, other):
        """
        Do not use.
        """
        raise NotImplementedError("This have no sens.")

    def __ge__(self, other):
        """
        Do not use.
        """
        raise NotImplementedError("This have no sens.")
    
    def istitle(self):
        """
        A keyEntity is a title when all its stemms are title.
        """
        if self._istitle is None:
            self._istitle = all(s.istitle() for s in self)
        return self._istitle
    
    def index(self, key):
        return self.stemms.index(key)
    
    def __contains__(self, item):
        """
        Special behaviour if item is KeyEntity :
        determine if item is contained in self, or self in item.
        """
        if isinstance(item, KeyEntity):
            if len(item) > len(self): return False
            #item is shorter or equal
            if not item[0] in self: return False#The first element is not there
            idx = self.index(item[0])
            return item[:] == self[idx:idx+len(item)]
        else:
            return self.stemms.__contains__(item)

    @property
    def confidence(self):
        return self.collocation_confidence * self.keyconcept_confidence
#        return product([100] + [v for k, v in self._confidences.items()])
    
    @property
    def trigger_score(self):
        """
        Score used by trigger, may be the final confidence ?
        """
        return self.frequency_relative_pmi_confidence * self._confidences["pos"]
    
    @property
    def collocation_confidence(self):
        return ((self._confidences["heuristical_mutual_information"] 
                + self._confidences["statistical_mutual_information"]) / 2) \
                * self._confidences["pos"]
#                self._confidences["title"] * self._confidences["thesaurus"] \

    @property
    def keyconcept_confidence(self):
#        return ((self._confidences["nrelative_frequency"] + self._confidences["frequency"]) / 2 )
        return self._confidences["nrelative_frequency"]
    
    @property
    def frequency_relative_pmi_confidence(self):
        return self._confidences["statistical_mutual_information"] \
               * self._confidences["nrelative_frequency"]
    
    def compute_confidence(self):
        """
        Compute scores that will be used to order, select, deduplicate 
        keytentities.
        """
        self._confidences["frequency"] = self.frequency_confidence()
        self._confidences["nrelative_frequency"] = self.nrelative_frequency_confidence()
        self._confidences["title"] = self.title_confidence()
        self._confidences["pos"] = self.pos_confidence()
        self._confidences["heuristical_mutual_information"] = self.heuristical_mutual_information_confidence()
        self._confidences["statistical_mutual_information"] = self.statistical_mutual_information_confidence()

    def frequency_confidence(self):
        """
        Lets define that a ngram of 10 for a text of 100 words
        means 1 of confidence, so 0.1
        """
        if self._confidences["frequency"] is None:
            self._confidences["frequency"] = 1.0 * self.count / len(self.text.words) / 0.1
        return self._confidences["frequency"]

    def nrelative_frequency_confidence(self):
        """
        This is the frequency of the entity relatively to the possible entity
        of its length.
        """
        ngram_possible = len(self.text) - len(self) + 1
        if self._confidences["nrelative_frequency"] is None:
            self._confidences["nrelative_frequency"] = 1.0 * self.count / ngram_possible
        return self._confidences["nrelative_frequency"]

    def title_confidence(self):
        """
        Define the probability of a ngram to be a title.
        Factor is for the confidence coex max.
        This may not have a negative effect, just positive :
        a title is a good candidate to be a collocation
        but this doesn't means that if it's not a title it's not a collocation.
        Two things have importance here : the proportion of title AND the number
        of titles.
        Ex. :
        - "Jérôme Bourreau" is "more" title than "Bourreau"
        - "projet de loi Création et Internet" is "less" title than "loi Création
        et Internet"
        """
        if self._confidences["title"] is None:
            confidence = 1
            factor = 3.0
            to_test = [n.main_occurrence for n in self if n.main_occurrence.has_meaning()]
            for item in to_test:
                # Proportion and occurrences
                if item.istitle(): confidence += factor / len(to_test) + 0.1
            self._confidences["title"] = confidence
        return self._confidences["title"]
    
    def pos_confidence(self):
        """
        Give a score linked to the POS of the subelements.
        """
        confidence = 0
        if self._confidences["pos"] is None:
            for stemm in self:
                if stemm.tag[:3] == "SBP": confidence += 2.5
                elif stemm.tag[:3] == "ADJ": confidence += 1.7
                elif stemm.tag[:3] == "SBC": confidence += 1.5
                elif stemm.main_occurrence.is_verb(): confidence += 1.2
                elif stemm.tag[:3] == ('ADV'): confidence += 1.0
                elif stemm.main_occurrence.is_avoir() \
                     or stemm.main_occurrence.is_etre(): confidence += 0.3
                else:
                    confidence += 0.1
            self._confidences["pos"] = confidence / len(self)
        return self._confidences["pos"]
    
    def heuristical_mutual_information_confidence(self):
        """
        Return the probability of all the terms of the ngram to appear together.
        The matter is to understand the dependance or independance of the terms.
        If just some terms appears out of this context, it may be normal (for
        exemple, a name, which appaers sometimes with both firstname and lastname
        and sometimes with just lastname). And if these terms appears many many
        times, but some others appears just in this context, the number doesn't
        count.
        If NO term appears out of this context, with have a good probability for
        a collocation.
        If each term appears out of this context, and specialy if this occurs
        often, we can doubt of this collocation candidate.
        Do we may consider the stop_words ?
        This may affect negativly and positivly the main confidence.
        """
        if self._confidences["heuristical_mutual_information"] is None:
            #We test just from interessant stemms, but we keep original position
            candidates = [(k, v) for k, v in enumerate(self) if v.is_valid()]
            alone_count = {}
            if len(self) == 1: return 1#Just one word, PMI doesn't make sense
            if len(candidates) == 0: return 0.1
            for position, stemm in candidates:
                alone_count[position] = 0
                neighbours = [(s, p - position) for p, s in enumerate(self) if not s is stemm]
                for tkn in stemm.occurrences:
                    if not tkn.is_neighbor(neighbours):
                        alone_count[position] += 1
            res = [v for k,v in alone_count.items()]
            if sum(res) == 0:
                return 3 * len(self)#We trust this collocation
            elif 0 in res:#Almost one important term appears just in this context
                return 2
            else:
                #We don't know, but not so confident...
                #The more the terms appears alone, the less we are confident
                #So the smaller is the coef
                return product([2.0 * len(self) / (len(self) + v) for v in res])
        return self._confidences["heuristical_mutual_information"]

    def statistical_mutual_information_confidence(self):
        """
        Number of occurrences of the ngram / number of ngrams possible
        /
        probability of each member of the ngram.
        """
        if self._confidences["statistical_mutual_information"] is None:
            if len(self) == 1: return 1.0#TODO : find better way for 1-grams...
            ngram_possible = len(self.text) - len(self) + 1
            members_probability = product([1.0 * s.count/len(self.text) for s in self])
            self._confidences["statistical_mutual_information"] = \
            math.log(1.0 * self.count / ngram_possible / members_probability)
        return self._confidences["statistical_mutual_information"]

    def thesaurus_confidence(self):
        """
        Try to find a descriptor in thesaurus, calculate levenshtein distance,
        and make a score.
        This may not be < 1, because if there is a descriptor, is a good point
        for the collocation, but if not, is doesn't means that this is not a 
        real collocation.
        """
        if self._confidences["thesaurus"] is None:
            if self.descriptor is None: return 1
            else:
                sorig = unicode(self)
                dorig = unicode(self.descriptor)
                return math.log(max(1, (len(sorig) - lev(dorig, sorig))))
        return self._confidences["thesaurus"]

    def is_duplicate(self, KeyEntity):
        """
        Say two keyentities are duplicate if one is contained in the other.
        """
        return len(self) > len(KeyEntity) and KeyEntity in self or self in KeyEntity

    def merge(self, other):
        """
        Other is merged in self.
        Merging equal to say that other and self are the same KeyEntity, and self
        is the "delegate" of other.
        So (this is the case if other is smaller than self) each time other appears
        without the specific terms of self, we concider that is the same concept.
        So, we keep the highest frequency_confidence.
        """
        self._confidences["frequency"] = max(other._confidences["frequency"],
                                             self._confidences["frequency"])
        self._confidences["nrelative_frequency"] = max(other._confidences["nrelative_frequency"],
                                             self._confidences["nrelative_frequency"])

class Stemm(RetrievableObject):
    """
    Subpart of text, grouped by meaning (stem).
    This try to be the *core* meaning of a word, so many tokens can point to
    the same stemm.
    Should be renamed in Lemm, because we are talking about lemmatisation,
    not stemmatisation.
    """
    count = 0

    def __init__(self, pk, **kwargs):
        self.id = pk
        self.text = kwargs["text"]
        self.occurrences = []
        self._main_occurrence = None
    
    def __unicode__(self):
        return unicode(self.id)
    
    def __repr__(self):
        return u"<Stemm '%s'>" % unicode(self.id)
    
    def __hash__(self):
        return self.id.__hash__()

    def __eq__(self, y):
        """
        WATCH OUT of the order you make the comparison between a Token and a Stemm :
        if stemm == token means that the comparison is on the stemme of bof
        if token == stemm means that the comparison is on the graph of both
        y could be a string or a Token or a Stemm
        """
        s = y
        if isinstance(y, Token):
            s = s.stemm # Will turn one time.
        elif isinstance(y, Stemm):
            s = s.id 
        return self.id == s

    def __ne__(self, y):
        return not self.__eq__(y)

    def istitle(self):
        return self.main_occurrence.istitle()
#        return all([o.istitle() for o in self.occurrences])
        #We try to use the majority instead of all (sometimes a proper name is also a common one)...
#        return [o.istitle() for o in self.occurrences].count(True) >= len(self.occurrences) / 2
    
    @property
    def tag(self):
        return self.main_occurrence.tag
    
    def is_valid(self):
        return self.main_occurrence.has_meaning()

    def is_valid_alone(self):
        return self.main_occurrence.has_meaning_alone()

    def has_interest(self):
        """
        Do we take it in count as potential KeyEntity?
        If count is less than x, but main_occurrence is a title, we try to keep it
        """
        return self.is_valid() and (self.count > 2 or self.istitle())

    def has_interest_alone(self):
        """
        Do we take it in count if alone ??
        If count is less than x, but main_occurrence is a title, we try to keep it
        """
        return self.is_valid_alone() and (self.count >= self.text.medium_word_count or self.istitle())

    @property
    def main_occurrence(self):
        """
        Returns the "main" one from the linked tokens.
        """
        if self._main_occurrence is None:
            self._main_occurrence = sorted(words_occurrences([t for t in self.occurrences]).iteritems(),
                      key=itemgetter(1), reverse=True)[0][0]
        return self._main_occurrence

    @property
    def count(self):
        """
        Number of occurrences of this stemm.
        """
        return len(self.occurrences)

