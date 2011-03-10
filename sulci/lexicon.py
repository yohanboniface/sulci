#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from collections import defaultdict
from operator import itemgetter

from base import TextManager
from utils import load_file, save_to_file, log

class Lexicon(TextManager):
    """
    The lexicon is a list of unique words and theirs possible  POS tags.
    """
    
    def __init__(self):
        self.VALID_EXT = ".lxc.crp"
        self.PATH = "corpus"
        self._loaded = None
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
        """
        if self._loaded is None:#Caching and lazy loading
            log("Loading lexicon...", "RED", True)
            lx = load_file("corpus/lexicon.lxc")
            self._loaded = {}
            for line in lx.split("\n"):
                els = line.split("\t")
                if len(els) == 2:
                    cat = els[1].split()
                    self._loaded[els[0]] = cat
                    self.add_factors(els[0])
        return self._loaded
    
    def add_factors(self, token):
        prefix = token
        while prefix:
            suffix = prefix
            while suffix:
                if not suffix == token:#Don't add the initial graph
                    self.factors.add(suffix)
                suffix = suffix[1:]
            prefix = prefix[:-1]
    
    def make(self):
        final = {}
        self.load_valid_files()
        _, tokens = self.instantiate_text(self._raw_content.split())
        for tk in tokens:
            if not tk.original in final:
                final[tk.original] = defaultdict(int)
            final[tk.original][tk.verified_tag] += 1
        d = ""
        for k, v in sorted(final.items()):
            d +=  u"%s\t%s\n" % (k, " ".join([tp[0] for tp in sorted([(k2, v2) for k2, v2 in v.iteritems()], key=itemgetter(1), reverse=True)]))
        save_to_file("corpus/lexicon.pdg", unicode(d))
    
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
            log(u"%s => %s" % (entry, self[entry]), "WHITE")
        else:
            log(u'No entry for "%s"' % entry, "WHITE")

