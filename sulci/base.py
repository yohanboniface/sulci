#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from sulci.utils import load_file, get_dir
from sulci.textutils import tokenize_text
from sulci.stopwords import usual_words


class TextManager(object):
    """
    This is an abstract class for all the "text", i.e. collection of samples
    and tokens.
    """
    VALID_EXT = None  # To be overwrited
    PENDING_EXT = None  # To be overwrited

    def get_files(self, kind):
        return [x for x in os.listdir(get_dir(__file__) + self.PATH) if x.endswith(kind)]

    def instantiate_text(self, text):
        """
        return samples and tokens.
        text is tokenized
        each token is : original + optionnal verified_tag (for training)
        """
        csamples = []
        ctokens = []
        current_sample = None
        previous_token = None
        sample_id = 0
        for idx, tk in enumerate(text):
            t, created = Token.get_or_create(idx, self, original=tk)
            if current_sample is None or t.begin_of_sample(previous_token):
                current_sample, created = Sample.get_or_create(
                                              sample_id,
                                              self,
                                              parent=self
                                          )
                sample_id += 1
                csamples.append(current_sample)
            current_sample.append(t)
            ctokens.append(t)
            previous_token = t
        return csamples, ctokens

    @property
    def valid_files(self):
        return self.get_files(self.VALID_EXT)

    @property
    def pending_files(self):
        return self.get_files(self.PENDING_EXT)

    def load_valid_files(self):
        for f in self.valid_files:
            self._raw_content += load_file(os.path.join(self.PATH, f))

    def tokenize(self, text):
        return tokenize_text(text)


class RetrievableObject(object):
    """
    Simple abstract class to manage RAM stored and retrievable objects.
    """

    @classmethod
    def get_or_create(cls, ref, parent_container, **kwargs):
        """
        Here, objects are created within a parent container.
        For exemple, the text, or a sample, or a lexicon, ecc.
        The store field is build from the name of the class.
        """
        key, pk = cls.make_key(ref)
        store_field_name = "_store_%s" % cls.__name__.lower()
        if not hasattr(parent_container, store_field_name):
            setattr(parent_container, store_field_name, {})
        store_field = getattr(parent_container, store_field_name)
        if key in store_field:
            return (store_field[key], False)
        else:
            store_field[key] = cls(pk, **kwargs)
            return (store_field[key], True)

    @classmethod
    def sort(cls, seq, attr, reverse=True):
        intermed = [(getattr(seq[i], attr), i, seq[i]) for i in xrange(len(seq))]
        intermed.sort()
        if reverse:
            intermed.reverse()
        return [tup[-1] for tup in intermed]

    @classmethod
    def make_key(cls, expression):  # TODO Optimize me !
        """
        Make a standardization in the expression to return a tuple who maximise
        maching possibilities.
        expression must be a list or tuple, or string or unicode
        """
        if not isinstance(expression, (list, tuple)):
            expression = unicode(expression).split()
        expression = tuple(expression)
        return "%s__%s" % (cls.__name__, expression), expression

    def __str__(self):
        return self.__unicode__().encode("utf-8")


class Sample(RetrievableObject):
    """
    A sentence of the text.
    """

    def __init__(self, pk, parent=None, **kwargs):
        self.id = pk
        self.tokens = []  # Otherwise all the objects have the same reference
        self._len = None  # For caching
        self.tag = None
        self.parent = parent
        # This field is used  just in training mode.
        # The idea is : every time a token with wrong tag is processed but
        # not corrected, we store his index, to prevent from reprocessing it until
        # the sample has changed.
        # Maybe, for design purpose, this field can be added by trainer or
        # whe should subclass the Sample with a TrainerSample...
        self._trainer_processed = set()
        # If each errors in the sample are processed but not corrected, it's not
        # necessary to reprocess there errors until the sample hasn't changed.
        self._trainer_candidate = True

    def __unicode__(self):
        return u" ".join([unicode(t) for t in self.tokens])

    def __repr__(self):
        return u" ".join([repr(t) for t in self.tokens]).encode("utf-8")

    def __iter__(self):
        return self.tokens.__iter__()

    def __len__(self):
        if self._len is None:
            self._len = len(self.tokens)
        return self._len

    def __getitem__(self, key):
        return self.tokens[key]

    def append(self, item):
        if not isinstance(item, Token):
            raise ValueError(
                "Sample object can deal only with Token instances. "
                "Got %s instead." % type(item)
                )
        item.position = len(self)
        item.parent = self
        self.tokens.append(item)
        self._len = None  # Flush cache as we add a token

    def has_position(self, pos):
        return 0 <= pos < len(self)

    def meaning_words_count(self):
        return len([t for t in self.tokens if t.has_meaning()])

    def is_token(self, stemm, position):
        """
        Check if there is stemm "stemm" in position "position".
        """
        if not self.has_position(position) or not stemm == self[position]:
            return False
        return True

    def show_context(self, position):
        """
        Returns a string of tokens around some positin of the sample.
        """
        begin = max(0, position - 5)
        end = min(len(self), position + 5)
        return u" ".join([t.__urepr__() for t in self[begin:end]])

    def get_errors(self, attr="tag"):
        """
        Retrieve errors, comparing attr and verified_attr.
        Possible values are : tag, lemme.
        """
        final = []
        # Squeeze the loop if False.
        if not self._trainer_candidate:
            return final
        for token in self:
            test_attr = getattr(token, attr)
            verified_attr = getattr(token, "verified_%s" % attr)
            if test_attr != verified_attr \
                and not token.position in self._trainer_processed:
                # If the position is in _trainer_processed, this means
                # that the error was yet processed but not corrected
                # and the sample has not changed until then.
                final.append(token)
        if final == []:
            # We use this as a cache, to prevent from looping over the errors
            # each time.
            # Remember that if some token is changed in the sample, the method
            # reset_trainer_status is normaly called.
            self._trainer_candidate = False
        return final

    def reset_trainer_status(self):
        """
        This method has to be called by the trainer each time a token of
        this sample is modified.
        """
        self._trainer_candidate = True
        self._trainer_processed = set()

    def set_trained_position(self, pos):
        """
        This method has to be called by trainer each time a token is processed
        but not corrected.
        """
        self._trainer_processed.add(pos)


class Token(RetrievableObject):
    """
    Simplest element of a text.
    """

    def __init__(self, pk, original, parent=None, position=0, **kwargs):
        """
        pk = unique string representing object (used to store in cache)
        original = raw string of token, when used in training mode, has tag and
        lemme attached, eg. word/tag/lemme
        parent = the parent sample; can be omitted here, but is needed for using
        the token, so it have to be setted manually if not passed here
        position = the position of the token in the parent sample (O indexed)
        """
        self.id = pk
        self.verified_tag = None
        orig = original.split("/")
        self.original = orig[0]
        self.lemme = orig[0]  # Default value
        # This will be done in training mode
        if len(orig) > 1:
            self.verified_tag = orig[1]
            self.verified_lemme = len(orig) > 2 and orig[2] or self.original
        self.parent = parent
        self.position = position
        self.tag = ""
        self._len = None

    def __unicode__(self):
        return unicode(self.lemme)

    def __urepr__(self):
        """
        Unicode version of repr.
        """
        tag = self.tag and u"/%s" % unicode(self.tag) or ""
        verified_tag = self.verified_tag and u"[%s]" % unicode(self.verified_tag) or ""
        final = u"<Token %s%s %s>" % (unicode(self.original), tag, verified_tag)
        return final

    def __repr__(self):
        """
        __repr__ *must* return a str, not a unicode.
        """
        return self.__urepr__().encode("utf-8")

    def lower(self):
        return self.original.lower()

    @property
    def sample(self):
        """
        For retrocompatibility.
        """
        return self.parent

    @property
    def previous_bigram(self):
        """
        Return the two previous token, or None if there is not two tokens before.
        """
        if self.position >= 2:
            return self.get_neighbors(-2, -1)

    @property
    def next_bigram(self):
        """
        Return the two next token, or None if there is not two tokens after.
        """
        if len(self.parent) - self.position > 2:
            return self.get_neighbors(1, 2)

    def get_neighbors(self, *args):  # cache this
        """
        Returns tokens neighbors in sample in positions passed as args, if available.

        Eg. token.get_neighbors(1, 2) will return the next and next again tokens.
        """
        neighbors = []
        for idx in args:
            pos = self.position + idx
            if not self.parent.has_position(pos):
                return []
            neighbors.append(self.parent[pos])
        return neighbors

    def is_strong_punctuation(self):
        return self.original in [u".", u"!", u"?", u"…"]

    def begin_of_sample(self, previous_token):
        if previous_token is None:
            return True
        # what about ":"?
        if (previous_token.is_strong_punctuation() or previous_token.is_closing_quote())\
           and (self.original[0].isupper() or self.is_opening_quote()):
            return True
        return False

    def is_opening_quote(self):
        return self.original == u'«' or self.original == u'"'

    def is_closing_quote(self):
        return self.original == u'»' or self.original == u'"'

    def is_tagged(self, tag):
        return self.tag == tag

    def has_verified_tag(self, tag):
        return self.verified_tag == tag

    def __hash__(self):
        return self.original.__hash__()

    def __eq__(self, other):
        """
        WATCH OUT of the sens you make the comparison between a Token and a
        Stemm other could be a string or a Token or a Stemm
        """
        s = other
        if isinstance(other, Token):
            s = other.original
        elif isinstance(other, object) and other.__class__.__name__ == "Stemm":
            s = other.main_occurrence  # Will come back one time.
        return self.original == s

    def __ne__(self, y):
        return not self.__eq__(y)

    def __len__(self):
        if self._len is None:
            self._len = len(self.original)
        return self._len

    def __getitem__(self, key):
        return self.original.__getitem__(key)

    def has_meaning(self):
        """
        What about isdigit ?
        """
        # We don't take stop words (by lemme)
        # We take words < 2 letters only if it's a number
        # We don't take tools words (by tag)
        # We don't take être and avoir
        return self.lemme not in usual_words \
               and (len(self.lemme) >= 2 or self.lemme.isdigit())\
               and not self.is_tool_word() \
               and not self.is_etre() \
               and not self.is_avoir()

    def is_tool_word(self):
        """
        Try to define if this word is a "mot outil".
        """
        tool_tags = [
            "DTN:sg",
            "DTN:pl",
            "DTC:sg",
            "DTC:pl",
            "PLU",
            "COO",
            "PREP",
            "REL",
            "SUB",
        ]
        return self.tag in tool_tags or self in usual_words \
                         or (self.position == 0 and self.lower() in usual_words)

    def is_verb(self):
        """
        We don't take in count the verbs Etre and Avoir.
        """
        return self.tag in [
            "VCJ:sg",
            "VCJ:pl",
            "PAR:sg",
            "PAR:pl",
            "VNCFF",
            "VNCNT",
        ]

    def is_etre(self):
        return self.tag in [
            "ECJ:sg",
            "ECJ:pl",
            "EPAR:sg",
            "ENCFF",
            "ENCNT",
        ]

    def is_avoir(self):
        return self.tag in [
            "ACJ:sg",
            "ACJ:pl",
            "APAR:sg",
            "APAR:pl",
            "ANCFF",
            "ANCNT",
        ]

    def has_meaning_alone(self):
        """
        Do we take it in count if alone?
        """
        # Similar to has_meaning, but we don't want numbers < 2
        return self.has_meaning() and len(self.lemme) >= 2

    def istitle(self):
        """
        Determine if the token is a title, using its tag.
        """
        return self.tag[:3] == "SBP"

    def is_neighbor(self, candidates):
        """
        Return true if word appears with right neighbours.
        False otherwise.
        candidates is tuple (Stemm object, distance)
        """
        for candidate, distance in candidates:
            if not self.parent.is_token(candidate, self.position + distance):
                return False
        return True

    def show_context(self):
            return self.parent.show_context(self.position)
