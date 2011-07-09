# -*- coding: utf-8 -*-

from django.test import TestCase

from sulci.textutils import modern_istitle

class TextUtilsTests(TestCase):

    def test_modern_istitle(self):
        self.failIf(modern_istitle("al-Assad") != True)
        self.failIf(modern_istitle("el-Assad") != True)
        self.failIf(modern_istitle("iPhone") != True)
        self.failIf(modern_istitle("eMac") != True)
        self.failIf(modern_istitle("Basic") != True)
        self.failIf(modern_istitle("BASIC") != True)

