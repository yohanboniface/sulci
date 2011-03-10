#!/usr/bin/env python
# -*- coding:Utf-8 -*-

import re
import codecs
import os

from Stemmer import Stemmer#DRY ALERT

from textminingutils import tokenize_text, normalize_token, lev
from base import RetrievableObject
from utils import log, save_to_file

class Thesaurus(object):

    def __init__(self, path="thesaurus.txt"):
        self._triggers = None
        log("loading thesaurus", "BLUE", True)
        self.descriptors = {}
        f = codecs.open(path, "r", "utf-8")
        for idx, line in enumerate(f.readlines()):
            cleaned_line, options = self.split_line(line)
            if cleaned_line is not None:
    #                if idx == 9: print cleaned_line
                dpt, created = Descriptor.get_or_create(tokenize_text(cleaned_line),
                                                        self,
                                                        original=tokenize_text(cleaned_line),
                                                        options=options,
                                                        line=idx)
                dpt_indexes = dpt.aliases
                for dpt_index in dpt_indexes:
    #                    if "Fini" in line: print dpt_index
                    if not dpt_index in self:
                        self.descriptors[dpt_index] = []
                    if not dpt in self.descriptors[dpt_index]:
                        self.descriptors[dpt_index].append(dpt)
        f.close()
        log("thesaurus loaded", "BLUE", True)
    
    def __contains__(self, item):
        """
        The idea is to get a tuple, en compare it with each aliases.
        """
#        print "contains", item
        return self.normalize_item(item) in self.descriptors
    
    def __iter__(self): 
        return self.descriptors.__iter__()
    
    def __getitem__(self, key):
        idx = self.normalize_item(key)
        return self.descriptors[key][0]
        #Not sure we need it anymore, when using triggers
#        return sorted(((lev(u" ".join(d.original), u" ".join(unicode(stemm) for stemm in idx)), d) for d in self.descriptors[idx]), key=lambda tup: tup[0])[0][1]
    
    def normalize_item(self, item):
        from textmining import KeyEntity#Sucks...
        if isinstance(item, KeyEntity):
            tup = tuple([unicode(t) for t in item.stemms])
        elif isinstance(item, list):
            tup = tuple(item)
        elif isinstance(item, (unicode, str)):
            tup = tuple(item.split())
        else:
            tup = item
        return tuple(sorted(tup))

    def split_line(self, line):
        """
        The thesaurus is currently in plain text, so...
        """
        pattern = re.compile("\- (?P<descriptor>[\w\-'’ ]*)(#!/\[\[(?P<options>.*)\]\])?", re.U)
        r = pattern.search(line)
        if r is not None:
            return r.group("descriptor"), r.group("options")
        else:#Non valide line
            return None, None
    
    @property
    def triggers(self):
        if self._triggers is None:#cached and lazy
            self._triggers = set()
            self.load_triggers()
        return self._triggers
    
    def load_triggers(self):
        log("Loading triggers...", "YELLOW", True)
        f = codecs.open("corpus/triggers.trg", "r", "utf-8")
        for idx, line in enumerate(f.readlines()):
            #TODO check line validity
            t, created = Trigger.get_or_create(line, self, parent=self, original=line)
            self._triggers.add(t)
        f.close()
    
    @classmethod
    def reset_triggers(self):
        """
        For full training, we need to remove previous triggers.
        """
        save_to_file("corpus/triggers.trg", "")

class Descriptor(RetrievableObject): 
    """
    Entries of the Thésaurus.
    """
    def __init__(self, pk, **kwargs):
        self.id = pk
        self.original = kwargs["original"]
#        self.line = kwargs["line"]
        self.options = {}
        if "options" in kwargs:
            self.get_options(kwargs["options"])
        self.make_aliases()
    
    def __unicode__(self):
        return u" ".join([unicode(t) for t in self.original])
    
    def __hash__(self):
        return self.id.__hash__()
    
    def make_aliases(self):
        self.aliases = []
        candidates = [self.id]
        stemmer = Stemmer("french")#DRY ALERT !!!
        if "aliases" in self.options:
            for alias in self.options["aliases"].split(","):
                candidates.append(tuple([stemmer.stemWord(normalize_token(w)) for w in tokenize_text(alias.strip())]))
        for candidate in candidates:
            self.aliases.append(tuple(sorted(candidate)))
#        #Original graph
#        self.aliases.append(self.id)
#        #Ordered
#        if len(self.id) > 1:
#            l = list(self.id)
#            l = sorted(l)
#            self.aliases.append(tuple(l))
    
    def get_options(self, options):
        if options is not None:
            pattern = re.compile("([\w]+)=([\w ,_\-'\(\)&]+)")
            r = pattern.findall(options)
            for tup in r:
                self.options[tup[0]] = tup[1]

class Trigger(RetrievableObject):
    """
    The trigger is a keyentity who suggest some descriptors when in a text.
    It is linked to one or more descriptors, and the distance of the link
    between the trigger and a descriptor is stored in the relation.
    This score is populated during the sementical training.
    """
    def __init__(self, pk, **kwargs):
        self.id = pk#Tuple of original string
        self.original = u" ".join(pk)
        self.parent = kwargs["parent"]
        self._descriptors = {}
        self.init_descriptors(**kwargs)
    
    @classmethod
    def make_key(cls, line):
        """
        We receive a full line of file storage here, or the original string
        when comming from descriptors file.
        """
        #Tuple of original string
        expression = tuple(line.split("\t")[0].split())
        return "%s__%s" % (cls.__name__, expression), expression

    def __unicode__(self):
        return unicode(self.original)
    
    def __contains__(self, key):
        return key in self._descriptors
    
    def __setitem__(self, key, value):
        return self._descriptors.__setitem__(key, value)
    
    def __getitem__(self, key):
        return self._descriptors.__getitem__(key)
    
    def __delitem__(self, key):
        return self._descriptors.__delitem__(key)
    
    def __iter__(self):
        return self._descriptors.__iter__()
    
    def __len__(self):
        return self._descriptors.__len__()
    
    def items(self):
        return self._descriptors.items()
    
    def __hash__(self):
        return self.original.__hash__()
    
    @property
    def max_score(self):
        return max(self[d] for d in self)
    
    def init_descriptors(self, **kwargs):
        """
        Take a text descriptors storage and create the links.
        """
        #original may be the full orginal line
        if "original" in kwargs:
            for d in kwargs["original"].split("\t")[1:]:#TODO check errors
                ds = d.split()
                original = ds[:-1]
                dsc, created = Descriptor.get_or_create(original, self.parent, original=original)
                self.connect(dsc, float(ds[-1]))
    
    def connect(self, descriptor, score):
        """
        Create a connection with the descriptor if doesn't yet exists.
        In each case, update the connection weight.
        Delete the connection if the score is negative.
        """
        if not descriptor in self:
#            log(u"Creating connection %s - %s" % (self, descriptor), "CYAN")
            self[descriptor] = 0.0
        self[descriptor] += score
#        if self[descriptor] < 0:
#            del self[descriptor]
#            log(u"Removed connection %s - %s" % (self, descriptor), "RED")
    
    def clean_connections(self):
        """
        Remove the negative connections.
        """
        for descriptor in self._descriptors.copy().__iter__():
            if self[descriptor] < 0:
                del self[descriptor]
                log(u"Removed connection %s - %s" % (self, descriptor), "RED")        
    
    def export(self):
        """
        Return a string for file storage.
        """
        if len(self) == 0:
            log(u"No descriptors for %s" % unicode(self), "RED")
            return None
        return u"%s\t%s" % (unicode(self), u"\t".join(u"%s %f" % (unicode(k), float(v)) for k, v in self.items()))
