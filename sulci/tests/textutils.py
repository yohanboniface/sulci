# -*- coding: utf-8 -*-

from django.test import TestCase

from sulci.textutils import modern_istitle, normalize_text

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

