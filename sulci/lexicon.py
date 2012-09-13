"""
Define the Lexicon class.

For now, the lexicon is stored in a flat file, with special syntax :

* word[TAB]POStag1/lemme1[TAB]POStag2/lemme2

"""
# -*- coding:Utf-8 -*-

from collections import defaultdict
from operator import itemgetter

from base import TextManager
from utils import load_file, save_to_file
from sulci.log import sulci_logger
from corpus import Corpus


class Lexicon(TextManager):
    """
    The lexicon is a list of unique words and theirs possible POS tags.
    """

    _loaded = {}

    def __init__(self, path="corpus"):
        self.CORPUS_EXT = ".lxc.lem.crp"
        self.VALID_EXT = ".lxc"
        self.PENDING_EXT = ".pdg"
        self.PATH = path
        self._raw_content = ""
        self._prefixes = None
        self._suffixes = None
        self.factors = set()

    def __iter__(self):
        return self.loaded.__iter__()

    def __getitem__(self, item):
        return self.loaded.__getitem__(item)

    def __len__(self):
        return len(self.loaded)

    def items(self):
        return self.loaded.items()

    def __contains__(self, key):
        if isinstance(key, object) and key.__class__.__name__ == "Token":
            key = key.original
        return key in self.loaded

    @property
    def loaded(self):
        """
        Load lexicon in RAM, from file.

        The representation will be a dict {"word1": [{tag1 : lemme1}]}
        """
        if not self.PATH in self._loaded:  # Caching and lazy loading
            sulci_logger.debug("Loading lexicon...", "RED", True)
            lx = load_file("%s/lexicon.lxc" % self.PATH)
            self._loaded[self.PATH] = {}
            for line in lx.split("\n"):
                if line:
                    lexicon_entity = LexiconEntity(line)
                    self.add_factors(lexicon_entity.word)
                    self._loaded[self.PATH][lexicon_entity.word] = lexicon_entity
        return self._loaded[self.PATH]

    def add_factors(self, token):
        """
        Build the list of factors (pieces of word).

        These factors are used by the POStagger, to determine if an
        unnown word could be a derivate of another.
        """
        prefix = token
        while prefix:
            suffix = prefix
            while suffix:
                if not suffix == token:  # Don't add the initial graph
                    self.factors.add(suffix)
                suffix = suffix[1:]
            prefix = prefix[:-1]

    def make(self, force=False):
        """
        Build the lexicon.
        """
        final = {}
        lemme_to_original = {}
        C = Corpus(self.CORPUS_EXT)
        for tk in C.tokens:
            # Don't take Proper nouns (SBP) in lexicon
            if tk.verified_tag[:3] == "SBP":
                continue
            # Manage tags frequences
            if not tk.original in final:
                final[tk.original] = defaultdict(int)
            final[tk.original][tk.verified_tag] += 1
            # Manage lemmes frequences
            if not tk.original in lemme_to_original:
                lemme_to_original[tk.original] = {}
            if not tk.verified_tag in lemme_to_original[tk.original]:
                lemme_to_original[tk.original][tk.verified_tag] = defaultdict(int)
            # Frequence of this lemme for this tag for this word...
            lemme_to_original[tk.original][tk.verified_tag][tk.verified_lemme] += 1

        def get_one_line(key):
            """
            Return one line of the lexicon.
            Take the token.original string in parameter.
            """
            return u"%s\t%s" % (key, get_tags(key))

        def get_tags(key):
            """
            Return sorted tags for a original word compiled in a string :
            tag/lemme tag/lemme
            """
            # Retrieve tags
            tags = sorted([(k, v) for k, v in final[key].iteritems()],
                                             key=itemgetter(1), reverse=True)
            # Build final datas
            final_data = []
            for tag, score in tags:
                computed_lemmes = get_lemmes(key, tag)
                lemme, score = computed_lemmes[0]
                final_data.append(u"%s/%s" % (tag, lemme))

            # Return it as a string
            return u" ".join(final_data)

        def get_lemmes(key, tag):
            """
            Return sorted lemmes for one word with one POS tag.
            """
            return sorted(((k, v) for k, v in lemme_to_original[key][tag].iteritems()),
                                                key=itemgetter(1), reverse=True)

        d = []
        for k, v in sorted(final.iteritems()):
            d.append(get_one_line(k))
        final_d = u"\n".join(d)
#            d +=  u"%s\t%s\n" % (k, " ".join([u"%s/%s" % (tp[0], sorted(lemme_to_original[k][tp[0]], key=itemgetter(1), reverse=True)[0]) for tp in sorted([(k2, v2) for k2, v2 in v.iteritems()], key=itemgetter(1), reverse=True)]))
        ext = force and self.VALID_EXT or self.PENDING_EXT
        save_to_file("%s/lexicon%s" % (self.PATH, ext), unicode(final_d))

    def create_afixes(self):
        """
        We determinate here the most frequent prefixes and suffixes.
        """
        prefixes = defaultdict(int)
        suffixes = defaultdict(int)
        max_prefix_length = 3
        max_suffix_length = 5
        for tokenstring, _ in self.items():
            tlen = len(tokenstring)
            for i in xrange(1, min(max_prefix_length + 1, tlen)):
                prefix = tokenstring[0:i]
                prefixes[prefix] += len(prefix)
            for i in xrange(1, min(max_suffix_length + 1, tlen)):
                suffix = tokenstring[tlen - i:tlen]
                suffixes[suffix] += len(suffix)
        #We make a set, to speed contains, so sorted doesn't meens nothing
        self._prefixes = set(key for key, value in \
                         sorted(((k, v) for k, v in prefixes.items() if v > len(k) * 2),
                         key=itemgetter(1), reverse=True))
        self._suffixes = set(key for key, value in \
                         sorted(((k, v) for k, v in suffixes.items() if v > len(k) * 2),
                         key=itemgetter(1), reverse=True))

    @property
    def prefixes(self):
        if self._prefixes is None:
            self.create_afixes()
        return self._prefixes

    @property
    def suffixes(self):
        if self._suffixes is None:
            self.create_afixes()
        return self._suffixes

    def get_entry(self, entry):
        if entry in self:
            sulci_logger.info(unicode(self[entry]), "WHITE")
        else:
            sulci_logger.info(u'No entry for "%s"' % entry, "WHITE")

    def check(self):
        """
        Util method to try to individuate errors in the Lexicon.
        For this, we display the entries with several tags, in case
        they are wrong duplicate.
        """
        for key, entity in self.items():
            if len(entity.tags) > 1:
                sulci_logger.info(u"%s tags for %s" % (len(entity.tags), key), "RED")
                sulci_logger.info(entity.tags, "WHITE")


class LexiconEntity(object):
    """
    One word of a lexicon.
    """

    def __init__(self, raw_data, **kwargs):
        self.default_tag = None
        self.default_lemme = None
        # Initalize data from original line
        self.word, tags = raw_data.split("\t")
        self.tags = dict()
        tags = tags.split()
        for one_tag in tags:
            tag, lemme = one_tag.split("/")
            if self.default_tag is None:
                self.default_tag = tag
            if self.default_lemme is None:
                self.default_lemme = lemme
            self.tags[tag] = lemme

    def __unicode__(self):
        return u"%s => %s" % (self.word, self.tags)

    def __contains__(self, key):
        return self.tags.__contains__(key)

    def __getitem__(self, key):
        return self.tags[key]
