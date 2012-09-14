#!/usr/bin/env python
# -*- coding:utf-8 -*-

from operator import itemgetter
from GenericCache.GenericCache import GenericCache

from utils import load_file, save_to_file, log
from base import RetrievableObject

# Cache
cache = GenericCache()


class RuleTemplate(RetrievableObject):
    """
    Class for managing rules creation and analysis.
    """

    def __init__(self, pk, **kwargs):
        self.id = pk

    def test_rule(self, token, rule):
        to_tag = self.get_to_tag(rule)
        if not self.is_candidate(token, rule):
            return 0
        elif token.has_verified_tag(to_tag) and not token.is_tagged(to_tag):
            return 1
        else:
            return -1

    def get_to_tag(self, rule):
        from_tag, to_tag, _, complement = self.uncompile_rule(rule)
        return to_tag

    def apply_rule(self, tokens, rule):
        """
        Apply rule to candidates in a set of tokens.
        """
        to_tag = self.get_to_tag(rule)
        for token in tokens:
            if self.is_candidate(token, rule):
                token.tag = to_tag
                # Maybe we should do this only in training mode
                token.sample.reset_trainer_status()

    @classmethod
    def select_one(cls, rules, MAX, minval=2):
        """
        Select one rule between a set of tested rules.

        rules is a iterable of tuples : (rule, good, bad), where good is the
        number of errors corrected, and bad the number of error generated.
        """

        # Questions are :
        # - which rule to select ?
        # - what to advantage ?
        # - The difference between good and bad ?
        # - the rapport between good and bad ?
        # - a mix of both ?
        # - with which coeff ?
        # Remainder (from kilobug) :
        # En gros on a deux options :
        # - soit good/(good + bad) * A + good/MAX * B
        # - soit (good/(good + bad)) ^ A * good/MAX ^ B
        # (moyenne arithmétique ou géométrique)
        # Mais pour simplifier on doit pouvoir s'en sortir avec un seul coefficient :
        # - good/(good + bad) + good/MAX * B
        # - (good/(good + bad)) * (good/MAX) ^ B
        # For example :
        # - SBC:pl CHANGESUFFIX "rs" "r" g: 15 b : 0
        # - SBC:pl CHANGESUFFIX "s" "" g: 179 b : 18
        # => which one have to be chosen ?
        # The first means : go straight to human logic (try to create less error
        # when applying rules)
        # The second : use your own logic (create error if it seems a good operation,
        # and create new rules to correct the new errors created)

        # Sorting using the rapport good / bad,
        # Giving advantage to the more numerous, if rapport is close.
        coeff = 0.1  # The lower the coeff, the stronger the rules with bad = 0
        g = lambda good, bad: (float(good) / (float(good) + float(bad))) * ((float(good) / MAX) ** coeff)
        try:
            return sorted([(r[0], g(r[1], r[2])) for r in rules if r[1] / max(r[2], 1) >= minval], key=itemgetter(1), reverse=True)[0]
        except IndexError:
            return None, None
        # Sorting with the difference between good and bad,
        # diving advantage to the less bad if same difference
        # Adding 0.1 to prevent from division by 0.
#        return sorted([(r[0], (r[1] - r[2] - (r[2] / (r[1] + 0.1)))) for r in rules], key=itemgetter(1), reverse=True)[0]

    def make_rules(self, token):
        comp = self.get_complement(token)
        if len(comp) > 0:
            return [self.compile_rule(token.tag, token.verified_tag, comp)]
        return []

    def test_complement(self, token, complement):
        return complement == self.get_complement(token)  # cache this

    def is_candidate(self, token, rule):
        # Should we check if word is in lexicon and to_tag a possible tag for it?
        from_tag, to_tag, _, complement = self.uncompile_rule(rule)
        # We not always have a from_tag (eg. template hassuf)
        if (from_tag and token.tag != from_tag) or \
           not self.test_complement(token, complement):
            return False
        return True


class ContextualTemplateGenerator(type):

    register = dict()
    _loaded_rules = None

    def __new__(mcs, name, base, dict):
        theclass = type.__new__(mcs, name, base, dict)
        if name.isupper():
            ContextualTemplateGenerator.register[name] = theclass
        return theclass

    @classmethod
    def get_instance(cls, s, **kwargs):
        """
        Returns and instance of a rule, from a template name or a rule string.

        `s` can be template name or rule.
        """
        if s.count(" ") > 0:  # rule
            _, _, name, _ = ContextualBaseTemplate.uncompile_rule(s)
        else:
            name = s
        child_class = cls.register[name]
        return child_class.get_or_create(name, ContextualTemplateGenerator)

    @classmethod
    def export(cls, rules):
        """
        Export rules to the provisory config file.

        `rules` are tuples (rule, score).
        """
        save_to_file("corpus/contextual_rules.pdg",
                     "\n".join(rule for rule, score in rules))

    @classmethod
    def load(cls):
        """
        Load rules from config file.
        """
        if cls._loaded_rules is None:
            log("Loading contextual rules...", "CYAN", True)
            lx = load_file("corpus/contextual_rules.rls")
            cls._loaded_rules = [r for r in lx.split(u"\n") if len(r) > 1]
        return cls._loaded_rules


class ContextualBaseTemplate(RuleTemplate):
    """
    Base class for the contextual rules.
    """
    __metaclass__ = ContextualTemplateGenerator
    _uncompiled_rules = {}

    def compile_rule(self, from_tag, to_tag, complement):
        """
        Make the final rule string.
        complement must be an iterable
        """
        comp = " ".join(unicode(c) for c in complement)
        return u"%s %s %s %s" % (from_tag, to_tag, self.__class__.__name__, comp)

    @classmethod
    def uncompile_rule(self, rule):
        try:
            return self._uncompiled_rules[rule]
        except KeyError:
            els = rule.split()
            self._uncompiled_rules[rule] = els[0], els[1], els[2], els[3:]
            return self._uncompiled_rules[rule]


class LexicalTemplateGenerator(type):

    register = dict()
    _loaded_rules = None  # caching

    def __new__(mcs, name, base, dict):
        theclass = type.__new__(mcs, name, base, dict)
        if name.islower():
            LexicalTemplateGenerator.register[name] = theclass
        return theclass

    @classmethod
    def get_instance(cls, s, lexicon):
        """
        s can be template name or rule.
        """
        if s.count(" ") > 0:  # rule
            _, _, name, _ = LexicalBaseTemplate.uncompile_rule(s)
        else:
            name = s
        child_class = cls.register[name]
        return child_class.get_or_create(name, LexicalTemplateGenerator, lexicon=lexicon)

    @classmethod
    def export(cls, rules):
        """
        Rules are tuples (rule, score)
        """
        save_to_file("corpus/lexical_rules.pdg",
                     "\n".join("%s\t%f" % (rule, float(score))
                     for rule, score
                     in sorted(rules, key=itemgetter(1), reverse=True)))

    @classmethod
    def load(cls):
        if cls._loaded_rules is None:
            log("Loading lexical rules...", "CYAN", True)
            cls._loaded_rules = []
            lx = load_file("corpus/lexical_rules.rls")
            for line in lx.split(u"\n"):
                els = line.split(u"\t")
                if els[0] != u"":
                    cls._loaded_rules.append(els[0])
        return cls._loaded_rules


class LexicalBaseTemplate(RuleTemplate):
    """
    Base class for the lexical rules.
    """
    __metaclass__ = LexicalTemplateGenerator
    _uncompiled_rules = {}

    def __init__(self, pk, **kwargs):
        self.id = pk
        self.lexicon = kwargs["lexicon"]
        self.check_from_tag = self.__class__.__name__.startswith(u"f")

    def compile_rule(self, from_tag, to_tag, complement):
        if self.check_from_tag:
            return u"%s %s %s %d %s" % (from_tag, unicode(complement), self.__class__.__name__, len(complement), to_tag)
        else:
            return u"%s %s %d %s" % (unicode(complement), self.__class__.__name__, len(complement), to_tag)

    @classmethod
    def _uncompile_rule(cls, rule):
        els = rule.split()
        for el in els:
            if el in LexicalTemplateGenerator.register:  # Here is classname
                if u"good" in el:  # proximity structure
                    if el.startswith("f"):
                        from_tag, complement, classname, to_tag = els
                    else:
                        complement, classname, to_tag = els
                        from_tag = None
                else:  # string check with
                    if el.startswith("f"):
                        from_tag, complement, classname, _, to_tag = els
                    else:
                        complement, classname, _, to_tag = els
                        from_tag = None
                break
        cls._uncompiled_rules[rule] = from_tag, to_tag, classname, complement

    @classmethod
    def uncompile_rule(cls, rule):
        if not rule in cls._uncompiled_rules:
            cls._uncompile_rule(rule)
        return cls._uncompiled_rules[rule]

    def test_complement(self, token, complement):
        return complement in self.get_complement(token)


class ProximityCheckTemplate(LexicalBaseTemplate):

    def compile_rule(self, from_tag, to_tag, complement):
        """
        No len...
        """
        if self.check_from_tag:
            return u"%s %s %s %s" % (from_tag, unicode(complement), self.__class__.__name__, to_tag)
        else:
            return u"%s %s %s" % (unicode(complement), self.__class__.__name__, to_tag)


class NoLexiconCheckTemplate(LexicalBaseTemplate):

    def make_rules(self, token):
        final = []
        for affix in self.get_complement(token):
            to_tag = token.verified_tag  # verified_tag
            from_tag = token.tag
            rule = self.compile_rule(from_tag, to_tag, affix)
            final.append(rule)
        return final


class LexiconCheckTemplate(LexicalBaseTemplate):
    """
    Base templates for those who have to check lexicon.
    """

    def make_rules(self, token):
        final = []
        for affix, ceased_tk in self.get_complement(token):
            if ceased_tk in self.lexicon:
                to_tag = token.verified_tag  # verified_tag / or lexicon token tag ?
                if self.check_from_tag:
                    rule = u"%s %s %s %d %s" % (token.tag, unicode(affix), self.__class__.__name__, len(affix), to_tag)
                else:
                    rule = u"%s %s %d %s" % (unicode(affix), self.__class__.__name__, len(affix), to_tag)
                final.append(rule)
        return final

    def test_complement(self, token, complement):
        """
        For the Lexicon Check rules, we need to check if modified word is
        in lexicon.
        """
        return self.modified_token(token, complement) in self.lexicon


class deletesuf(LexiconCheckTemplate):
    """
    Change current tag to tag X, if removing suffix Y lead in a entry of the lexicon.
    """

    def get_complement(self, token):
        """
        Return a tuple of afix, ceased_token.
        """
        final = []
        tlen = len(token.original)
        for i in xrange(1, min(5 + 1, tlen)):
            affix = token.original[tlen - i:tlen]
            ceased_tk = token.original[:i]
            final.append((affix, ceased_tk))
        return final

    def test_complement(self, token, complement):
        """
        Test if token has the right suffix, and if deleting it result in a
        word in the lexicon
        """
        return token[-len(complement):] == complement and \
               token[:-len(complement)] in self.lexicon


class fdeletesuf(deletesuf):
    """
    Change current tag to tag X, if removing suffix Y lead in a entry of lexicon
    and if current tag is Z.
    """
    pass


class deletepref(LexiconCheckTemplate):
    """
    Change current tag to tag X, if removing prefix Y lead in a entry of the lexicon.

    Prefix Y lenght from 1 to 4 (Y < 4) :
    Syntax : Y deletepref len(Y) X
    Ex. : re deletepref 2 VNCFF
    """

    def get_complement(self, token):
        final = []
        tlen = len(token.original)
        for i in xrange(1, min(5, tlen)):
            ceased_tk = token.original[i:]
            affix = token.original[0:i]
            final.append((affix, ceased_tk))
        return final

    def test_complement(self, token, complement):
        """
        Tests if token has the right prefix, and if deleting it result in a
        word in the lexicon
        """
        return token[:len(complement)] == complement and \
               token[len(complement):] in self.lexicon


class fdeletepref(deletepref):
    """
    Change current tag to tag X, if removing prefix Y lead in a entry of the lexicon
    and if current tag is Z.

    Prefix Y lenght from 1 to 4 (Y < 4):
    Syntax : Z Y fdeletepref len(Y) X
    Ex. : ADV re fdeletepref 2 VNCFF
    """
    pass


class addpref(LexiconCheckTemplate):
    """
    Change current tag to tag X, if adding prefix Y lead in a entry of the lexicon.

    Prefix Y lenght from 1 to 4 (Y < 4):
    Syntax : Y addpref len(Y) X
    Ex. : er addpref 2 VNCFF
    """

    def get_complement(self, token):
        final = []
        if token.original in self.lexicon.factors:
            for affix in self.lexicon.prefixes:
                increased_tk = self.modified_token(token, affix)
                final.append((affix, increased_tk))
        return final

    def modified_token(self, token, complement):
        return complement + token.original


class faddpref(addpref):
    """
    Change current tag to tag X, if adding prefix Y lead in a entry of the lexicon
    and if current tag is Z.

    Prefix Y lenght from 1 to 4 (Y < 4):
    Syntax : Z Y faddpref len(Y) X
    Ex. : SBC:sg re faddpref 2 VNCFF
    """
    pass


class addsuf(LexiconCheckTemplate):
    """
    Change current tag to tag X, if adding suffix Y lead in a entry of the lexicon.

    Suffix Y lenght from 1 to 4 (Y < 4):
    Syntax : Y addsuf len(Y) X
    Ex. : re addsuf 2 VNCFF
    """

    def get_complement(self, token):
        final = []
        if token.original in self.lexicon.factors:
            for affix in self.lexicon.suffixes:
                increased_tk = self.modified_token(token, affix)
                final.append((affix, increased_tk))
        return final

    def modified_token(self, token, complement):
        return token.original + complement


class faddsuf(addsuf):
    """
    Change current tag to tag X, if removing prefix Y lead in a entry of the
    lexicon and current tag is Z.

    Suffix Y lenght from 1 to 4 (Y <= 4) :
    Syntax : Z Y faddsuf len(Y) X
    Ex. : SBC:sg re faddsuf 2 VNCFF
    """
    pass


class hassuf(NoLexiconCheckTemplate):
    """
    Change current tag to tag X, if suffix is Y.

    Suffix Y is length from 1 to 4 (y <= 4)
    Syntax: Y hassuf len(Y) X
    Ex. : ment hassuf 4 ADV
    """
    def get_complement(self, token):
        """
        Return a tuple of afix, ceased_token.
        """
        final = set()
        tlen = len(token.original)
        for i in xrange(1, min(5 + 1, tlen)):
            affix = token.original[tlen - i:tlen]
            if affix in self.lexicon.suffixes:
                final.add(affix)
        return final


class fhassuf(hassuf):
    """
    Change current tag to tag X, if suffix is Y and current tag is Z.

    Suffix Y is length from 1 to 4 (y <= 4)
    Syntax: Z Y hassuf len(Y) X
    Ex. : SBC:sg ment hassuf 4 ADV
    """
    pass


class haspref(NoLexiconCheckTemplate):
    """
    Change current tag to tag X, if prefix is Y.

    Prefix Y is length from 1 to 4 (y <= 4)
    Syntax: Z Y haspref len(Y) X
    Ex. : pro haspref 3 SBC:sg
    """

    def get_complement(self, token):
        final = []
        tlen = len(token.original)
        for i in xrange(1, min(5, tlen)):
            affix = token.original[0:i]
            if affix in self.lexicon.prefixes:
                final.append(affix)
        return final


class fhaspref(haspref):
    """
    Change current tag to tag X, if prefix is Y and current tag is Z.

    Prefix Y is length from 1 to 4 (y <= 4)
    Syntax: Z Y hassuf len(Y) X
    Ex. : ADV bla haspref 3 DTC:sg
    """
    pass


class goodright(NoLexiconCheckTemplate, ProximityCheckTemplate):
    """
    The current word is at the right of the word X.
    """
    def get_complement(self, token):
        return [unicode(t.original) for t in token.get_neighbors(-1)]


class fgoodright(goodright):
    pass


class goodleft(NoLexiconCheckTemplate, ProximityCheckTemplate):
    """
    The current word is at the right of the word x.
    """
    def get_complement(self, token):
        return [unicode(t.original) for t in token.get_neighbors(1)]


class fgoodleft(goodleft):
    pass


class WordBasedTemplate(ContextualBaseTemplate):
    """
    Abstract Class for words based template.
    """
    def get_complement(self, token):
        args = self.get_target()
        return [unicode(e.original) for e in token.get_neighbors(*args)]


class TagBasedTemplate(ContextualBaseTemplate):
    """
    Abastract Class for tags based template.
    """
    def get_complement(self, token):
        args = self.get_target()
        return [e.verified_tag for e in token.get_neighbors(*args)]


class WordTagBasedTemplate(ContextualBaseTemplate):
    """
    Abastract Class for mixed based template : word, than tag.
    """
    def get_complement(self, token):
        args = self.get_target()
        nbors = token.get_neighbors(*args)  # must return empty []
        if nbors:
            return [unicode(nbors[0].original), nbors[1].verified_tag]
        else:
            return []


class TagWordBasedTemplate(ContextualBaseTemplate):
    """
    Abastract Class for mixed based template : tag, than word.
    """
    def get_complement(self, token):
        args = self.get_target()
        nbors = token.get_neighbors(*args)
        if nbors:
            return [nbors[0].verified_tag, unicode(nbors[1])]
        else:
            return []


class NEXTBIGRAM(WordBasedTemplate):
    """
    The next two words are X and Y.
    """
    def get_target(self):
        return 1, 2


class PREVBIGRAM(WordBasedTemplate):
    """
    The previous two words are X and Y.
    """
    def get_target(self):
        return -2, -1


class OrTemplate(ContextualBaseTemplate):
    """
    Abstract class for template where we check not specific position.
    """
    def test_complement(self, token, complement):
#        print complement, self.get_complement(token)
        return complement[0] in self.get_complement(token)

    def make_rules(self, token):
        nb = self.get_complement(token)
        final = []
        if len(nb) > 0:
            for w in nb:
                final += [self.compile_rule(token.tag, token.verified_tag, [w])]
        return final


class NEXT1OR2OR3TAG(OrTemplate, TagBasedTemplate):
    """
    One of the next three words is tagged X.
    """
    def get_target(self):
        return 1, 2, 3


class NEXT1OR2TAG(OrTemplate, TagBasedTemplate):
    """
    One of the next three token is tagged X.
    """
    def get_target(self):
        return 1, 2


class PREV1OR2OR3TAG(OrTemplate, TagBasedTemplate):
    """
    One of the next three token is tagged X.
    """
    def get_target(self):
        return -3, -2, -1


class PREV1OR2TAG(OrTemplate, TagBasedTemplate):
    """
    One of the next three token is tagged X.
    """
    def get_target(self):
        return -2, -1


class NEXTTAG(TagBasedTemplate):
    """
    The next token is tagged X.
    """
    def get_target(self):
        return (1,)


class NEXT2TAG(TagBasedTemplate):
    """
    The token after next token is tagged X.
    """
    def get_target(self):
        return (2,)


class PREVTAG(TagBasedTemplate):
    """
    The next token is tagged X.
    """
    def get_target(self):
        return (-1,)


class PREV2TAG(TagBasedTemplate):
    """
    The token after next token is tagged X.
    """
    def get_target(self):
        return (-2,)


class SURROUNDTAG(TagBasedTemplate):
    """
    The preceding word is tagged x and the following word is tagged y.
    """
    def get_target(self):
        return -1, 1


class NEXT1OR2WD(OrTemplate, WordBasedTemplate):
    """
    One of the next two token is word X.
    """
    def get_target(self):
        return 1, 2


class NEXT2WD(WordBasedTemplate):
    """
    One of the next three token is word X.
    """
    def get_target(self):
        return (2,)


class NEXTWD(WordBasedTemplate):
    """
    One of the next three token is word X.
    """
    def get_target(self):
        return (1,)


class CURWD(WordBasedTemplate):
    """
    The word is X.
    I have doubt on the interest of this template...
    """
    def get_target(self):
        return (0,)


class PREV1OR2WD(OrTemplate, WordBasedTemplate):
    """
    One of the next two token is word X.
    """
    def get_target(self):
        return -2, -1


class PREV2WD(WordBasedTemplate):
    """
    One of the next three token is word X.
    """
    def get_target(self):
        return (-2,)


class PREVWD(WordBasedTemplate):
    """
    One of the next three token is word X.
    """
    def get_target(self):
        return (-1,)


class WDAND2BFR(WordBasedTemplate):
    """
    One of the next three token is word X.
    """
    def get_target(self):
        return (-2, 0)


class WDAND2AFT(WordBasedTemplate):
    """
    One of the next three token is word X.
    """
    def get_target(self):
        return (0, 2)


class LBIGRAM(WordBasedTemplate):
    """
    One of the next three token is word X.
    """
    def get_target(self):
        return (-1, 0)


class RBIGRAM(WordBasedTemplate):
    """
    One of the next three token is word X.
    """
    def get_target(self):
        return (0, 1)


class WDAND2TAGAFT(WordTagBasedTemplate):
    """
    Current word, and tag of two token after.
    """
    def get_target(self):
        return 0, 2


class WDAND2TAGBFR(TagWordBasedTemplate):
    """
    Current word, and tag of two token before.
    """
    def get_target(self):
        return -2, 0


class WDNEXTTAG(WordTagBasedTemplate):
    """
    Current word, and tag of token after.
    """
    def get_target(self):
        return 0, 1


class WDPREVTAG(TagWordBasedTemplate):
    """
    Current word, and tag of token before.
    """
    def get_target(self):
        return -1, 0


class LemmatizerTemplateGenerator(type):

    register = dict()
    _loaded_rules = None

    def __new__(mcs, name, base, dict):
        theclass = type.__new__(mcs, name, base, dict)
        if name.isupper():
            LemmatizerTemplateGenerator.register[name] = theclass
        return theclass

    @classmethod
    def get_instance(cls, s, **kwargs):
        """
        s can be template name or rule.
        """
        if s.count(" ") > 0:  # rule
            name = s.split(" ")[1]
        else:
            name = s
        child_class = cls.register[name]
        return child_class.get_or_create(name, LemmatizerTemplateGenerator)

    @classmethod
    def export(cls, rules):
        """
        Rules are tuples (rule, score)
        """
        save_to_file("corpus/lemmatizer_rules.pdg",
                     "\n".join("%s\t%f" % (rule, float(score))
                     for rule, score
                     in rules))
#                     in sorted(rules, key=itemgetter(1), reverse=True)))

    @classmethod
    def load(cls):
        if cls._loaded_rules is None:
            log("Loading lemmatizer rules...", "CYAN", True)
            lx = load_file("corpus/lemmatizer_rules.rls")
            cls._loaded_rules = []
            for line in lx.split(u"\n"):
                els = line.split(u"\t")
                if els[0] != u"":
                    cls._loaded_rules.append(els[0])
        return cls._loaded_rules


class LemmatizerBaseTemplate(RetrievableObject):
    """
    For the Lemmatizer training, the is just one template :
    it create as many possible rules as letters in the token tested.
    MAKELOWER
    GIVELEMME
    CHANGESUFFIX
    """
    __metaclass__ = LemmatizerTemplateGenerator

    def __init__(self, pk, **kwargs):
        self.id = pk

    def make_rules(self, token):
        pass  # Must be overwrited

    def compile_rule(self):
        pass

    def test_rule(self, token, rule):
        pass

    def is_candidate(self, token, rule):
        from_tag = self.uncompile_rule(rule)[0]
        return token.tag == from_tag

    def uncompile_rule(self, rule):
        return rule.split(" ")

    def __unicode__(self):
        return u"<%s %s>" % (self.__class__.__name__, self.id)


class MAKELOWER(LemmatizerBaseTemplate):
    """
    Make the original lower, if the tag is x.
    """
    def make_rules(self, token):
        if token.lemme[0].isupper():
            return [self.compile_rule(token.tag)]
        else:
            return []

    def compile_rule(self, tag):
        return '''%s %s''' % (tag, self.__class__.__name__)

#    def is_candidate(self, token, rule):
#        tag, _ = self.uncompile_rule(rule)
#        #the token have the right tag for rule
#        return token.tag == tag\
#               and token[0].isupper()#the first letter is upper

    def test_rule(self, token, rule):
#        print token, token.lemme, token.verified_lemme, rule, token.tag
        if not self.is_candidate(token, rule):
            return 0
        elif token.verified_lemme[0] == token.lemme[0].lower():
            return 1
        else:
            return -1

    def apply_rule(self, tokens, rule):
        for token in tokens:
            if self.is_candidate(token, rule):
                token.lemme = token.lemme.lower()
                # Maybe we should do this only in training mode
                token.sample.reset_trainer_status()


class CHANGESUFFIX(LemmatizerBaseTemplate):
    """
    Make the original lower, if the tag is x.
    """
    def make_rules(self, token):
        """
        We make one rule for each possible transformation making verified_lemme
        from token.original.
        """
        final_rules = set()
        for i in xrange(1, len(token) + 1):
            suffix = token.lemme[-i:]
            stem = token.lemme[:-i]
            if token.verified_lemme[:len(stem)] == stem:  # potential rule
                final_rules.add(self.compile_rule(token.tag, suffix, token.verified_lemme[len(stem):]))
        return final_rules

    def compile_rule(self, tag, to_delete, to_add):
        return '''%s %s "%s" "%s"''' % (tag, self.__class__.__name__, to_delete, to_add)

    def uncompile_rule(self, rule):
        els = rule.split(" ")
        return els[0], els[2][1:-1], els[3][1:-1]

    def is_candidate(self, token, rule):
        tag, to_delete, to_add = self.uncompile_rule(rule)
        #the token have the right tag for rule
        return token.tag == tag\
               and token.lemme[-len(to_delete):] == to_delete  # the suffix is the rule one

    def test_rule(self, token, rule):
        tag, to_delete, to_add = self.uncompile_rule(rule)
        if not self.is_candidate(token, rule):
            return 0
        elif token.verified_lemme == token.lemme[:-len(to_delete)] + to_add:
            return 1
        else:
            return -1

    def apply_rule(self, tokens, rule):
        tag, to_delete, to_add = self.uncompile_rule(rule)
        for token in tokens:
            if self.is_candidate(token, rule):
                token.lemme = token.lemme[:-len(to_delete)] + to_add
                # Maybe we should do this only in training mode
                token.sample.reset_trainer_status()


class FORCELEMME(LemmatizerBaseTemplate):
    """
    Give lemme y, if the tag is x.
    """
    def make_rules(self, token):
        return [self.compile_rule(token.tag, token.verified_lemme)]

    def compile_rule(self, tag, lemme):
        return '''%s %s %s''' % (tag, self.__class__.__name__, lemme)

    def is_candidate(self, token, rule):
        tag, _, lemme = self.uncompile_rule(rule)
        return token.tag == tag  # the token have the right tag for rule

    def test_rule(self, token, rule):
        tag, _, lemme = self.uncompile_rule(rule)
        if not self.is_candidate(token, rule):
            return 0
        elif token.verified_lemme == lemme:
            return 1
        else:
            return -1

    def apply_rule(self, tokens, rule):
        tag, _, lemme = self.uncompile_rule(rule)
        for token in tokens:
            if self.is_candidate(token, rule):
                token.lemme = lemme
                # Maybe we should do this only in training mode
                token.sample.reset_trainer_status()
