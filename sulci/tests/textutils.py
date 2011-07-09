# -*- coding: utf-8 -*-

from django.test import TestCase

from sulci.textutils import modern_istitle, normalize_text, tokenize_text

class TextUtilsTests(TestCase):

    def test_modern_istitle(self):
        self.failIf(modern_istitle("al-Assad") != True)
        self.failIf(modern_istitle("el-Assad") != True)
        self.failIf(modern_istitle("iPhone") != True)
        self.failIf(modern_istitle("eMac") != True)
        self.failIf(modern_istitle("Basic") != True)
        self.failIf(modern_istitle("BASIC") != True)
    
    def test_normalize_text(self):
        self.failIf(u"’" in normalize_text(u"’"))
        self.failIf(u"qu' " not in normalize_text(u"lorsqu'il"))
        self.failIf(u"<" in normalize_text(u"<b>pouet</b>"))
        self.failIf(u"&" in normalize_text(u"&eacute;"))
        self.failIf(normalize_text(u"mange-t-elle") != u"mange - t - elle")
        # Replacing quotes
        self.failIf(normalize_text(u' "pouet') != u' «pouet')
        self.failIf(normalize_text(u'pouet". ') != u'pouet». ')
        self.failIf(normalize_text(u'pouet"! ') != u'pouet»! ')
        self.failIf(normalize_text(u'pouet"? ') != u'pouet»? ')
        self.failIf(normalize_text(u'pouet?" ') != u'pouet?» ')
        # reflexive pronoun
        self.failIf(normalize_text(u'dis-je,') != u'dis - je,')
        self.failIf(normalize_text(u'dis-tu ') != u'dis - tu ')
        self.failIf(normalize_text(u'entends-toi!') != u'entends - toi!')
        self.failIf(normalize_text(u'sans-toit') != u'sans-toit')
        self.failIf(normalize_text(u'dit-il!') != u'dit - il!')
        self.failIf(normalize_text(u'dit-elle;') != u'dit - elle;')
        self.failIf(normalize_text(u'dis-le!') != u'dis - le!')
        self.failIf(normalize_text(u'ce camion-ci.') != u'ce camion - ci.')
        self.failIf(normalize_text(u'camion-citerne') != u'camion-citerne')
    
    def test_tokenize_text(self):
        
        def do(t, out): # shortener
            self.failIf(t != out)
        
        do(tokenize_text(u"un deux trois"), [u"un", u"deux", u"trois"])
        do(tokenize_text(u"en 2011"), [u"en", u"2011"])
        do(tokenize_text(u"M. Duchmol"), [u"M.", u"Duchmol"])
        do(tokenize_text(u"A. B."), [u"A.", u"B."])
        do(tokenize_text(u"200 personnes"), [u"200", u"personnes"])
        do(tokenize_text(u"3,5 millions"), [u"3,5", u"millions"])
        do(tokenize_text(u"3.5 millions"), [u"3.5", u"millions"])
        do(tokenize_text(u"2.000.000 millions"), [u"2.000.000", u"millions"])
#        do(tokenize_text(u"2 000 000 millions"), [u"2 000 000", u"millions"])
#        do(tokenize_text(u"1, 2, 3"), [u"1", u",", u"2", u",", u"3"])
        do(tokenize_text(u"100%"), [u"100", u"%"])
        do(tokenize_text(u"bof…"), [u"bof", u"…"])
        do(tokenize_text(u"«entre guillemets»"), [u"«", u"entre", u"guillemets", u"»"])
        do(tokenize_text(u"Un point."), [u"Un", u"point", u"."])
        do(tokenize_text(u"une virgule, ici"), [u"une", u"virgule", u",", u"ici"])
        do(tokenize_text(u"un point ; virgule"), [u"un", u"point", u";", u"virgule"])
        do(tokenize_text(u"Oh!"), [u"Oh", u"!"])
        do(tokenize_text(u"Ah?"), [u"Ah", u"?"])
        do(tokenize_text(u"Ah ?"), [u"Ah", u"?"])
        do(tokenize_text(u"peut-être"), [u"peut-être"])
        do(tokenize_text(u"Port-la-Forêt"), [u"Port-la-Forêt"])
        do(tokenize_text(u"l'aviron"), [u"l'", u"aviron"])
        do(tokenize_text(u"qu'il"), [u"qu'", u"il"])
#        do(tokenize_text(u"il est 19h30"), [u"il", u"est", u"19h30"])
#        do(tokenize_text(u"est-ce"), [u"est", u"-", u"ce"])
#        do(tokenize_text(u"5e position"), [u"5e", u"position"])
#        do(tokenize_text(u"1er du mois"), [u"1er", u"du", u"mois"])
#        do(tokenize_text(u"c'est-à-dire"), [u"c'est-à-dire",])


