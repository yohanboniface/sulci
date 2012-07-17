# -*- coding: utf-8 -*-

import unittest

from sulci.textutils import modern_istitle, normalize_text, tokenize_text, strip_tags, unescape_entities

__all__ = [
    "TextUtilsTests",
]


class TextUtilsTests(unittest.TestCase):

    def test_strip_tags(self):
        def do(value):
            self.assertEqual(strip_tags(value), u"Just a test")
        do(u'<b>Just a test</b>')
        do(u'<b class="foo">Just a test</b>')
        do(u'<span class="foo">Just a</span> test')
        do(u'<span class="foo">Just <a href="#">a</a></span> <i>test</i>')

    def test_unescape_entities(self):
        self.assertEqual(unescape_entities('&eacute;'), u"é")
        self.assertEqual(unescape_entities('&amp;'), u"&")

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
        self.failIf(normalize_text(u"est-ce\n") != u"est - ce\n")

    def test_tokenize_text(self):

        def do(t, out):  # shortener
            self.failIf(tokenize_text(t) != out)

        do(u"un deux trois", [u"un", u"deux", u"trois"])
        do(u"en 2011", [u"en", u"2011"])
        do(u"M. Duchmol", [u"M.", u"Duchmol"])
        do(u"A. B.", [u"A.", u"B."])
        do(u"200 personnes", [u"200", u"personnes"])
        do(u"2 chats", [u"2", u"chats"])
        do(u"3,5 millions", [u"3,5", u"millions"])
        do(u"3.5 millions", [u"3.5", u"millions"])
        do(u"2.000.000 millions", [u"2.000.000", u"millions"])
        do(u"2 000 000 millions", [u"2 000 000", u"millions"])
        do(u"1, 2, 3", [u"1", u",", u"2", u",", u"3"])
        do(u"100%", [u"100", u"%"])
        do(u"bof…", [u"bof", u"…"])
        do(u"«entre guillemets»", [u"«", u"entre", u"guillemets", u"»"])
        do(u"Un point.", [u"Un", u"point", u"."])
        do(u"une virgule, ici", [u"une", u"virgule", u",", u"ici"])
        do(u"un point ; virgule", [u"un", u"point", u";", u"virgule"])
        do(u"Oh!", [u"Oh", u"!"])
        do(u"Ah?", [u"Ah", u"?"])
        do(u"Ah ?", [u"Ah", u"?"])
        do(u"peut-être", [u"peut-être"])
        do(u"Port-la-Forêt", [u"Port-la-Forêt"])
        do(u"l'aviron", [u"l'", u"aviron"])
        do(u"qu'il", [u"qu'", u"il"])
#        do(u"il est 19h30", [u"il", u"est", u"19h30"])
#        do(u"5e position", [u"5e", u"position"])
#        do(u"1er du mois", [u"1er", u"du", u"mois"])
        do(u"c'est-à-dire", [u"c'est-à-dire"])
#        do(u"http://libe.fr", [u"http://libe.fr",])

if __name__ == "__main__":
    unittest.main()
