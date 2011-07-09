# -*- coding: UTF-8 -*-
"""
Sulci raw text utils.
"""
import string
import re
import unicodedata

from operator import itemgetter
from collections import defaultdict

from django.utils.html import strip_tags
from django.utils.text import unescape_entities
from django.conf import settings

from utils import save_to_file, product, log
from stopwords import stop_words

def modern_istitle(word):
    """
    Define if a word is title or not, handling some modern cases.
    """
    if word[0].isupper(): return True # Basic case
    try:
        if word[:3] == "al-" and word[3].isupper(): return True # al-Assad
        if word[:3] == "el-" and word[3].isupper(): return True # el-Assad
        if word[0] in ["e","i"] and word[1].isupper(): return True # eMac, iPhone
    except IndexError:
        pass
    return False

def clean(s,l):
    for c in l:
        s = s.replace(c,'')
    return s

def normalize_token(w):
    w = w.replace(u"l'", u"")
    w = w.replace(u"m'", u"")
    #w = w.replace(u"d'", u"")
    w = w.replace(u"-", u"")
    w = ''.join((c for c in unicodedata.normalize('NFD', w) if unicodedata.category(c) != 'Mn'))
    w = w.lower()
    return w

def normalize_text(text, language="french"):
    """
    Normalize text : clean, strip tags...
    Tests needed.
    """
    text = strip_tags(unescape_entities(text))
    text = text.replace(u"’", u"'")
    text = text.replace(u"qu'", u"qu' ")#qu' lorsqu', etc.
    text = re.sub(ur'(")([^ \n\.,!?]){1}', u"\xab\g<2>", text, re.U)#replacing opening quotes
    text = re.sub(ur'([^ \n]){1}(")', u"\g<1>\xbb", text, re.U)#replacing closing quotes
    #Replacing inverted pronouns.
    text = re.sub(ur"\-t\-", u" - t - ", text, re.U)
    text = re.sub(ur"\-(je|moi|tu|toi|il|le|elle|la|on|nous|vous|ils|elles|les|ci|là)([\W])", u" - \g<1>\g<2>", text, re.U)
    return text

def tokenize_text(text):
    """
    Split text into list.
    Tests needed.
    #TODO:
    il est 19h30.
    années 60, et
    Qu'est-ce
    Port-la-Forêt
    en 5e position
    le 1er
    c'est-à-dire
    """
    pattern = re.compile(ur"""
              \d{4}(?#Year)
              |[A-Z]{1}\.(?#M., R., etc.)
              |[\d]+[\d,.]*(?#Number)
              |\$\d+(?:\.\d{2})?(?#Dollars)
              |%(?#Percentage)
              |\u2026(?#Ellipsis)
              |[\xab\xbb"](?#« or »)
              |[\,\.\:\(\)\!\-\?\[\];]{1}(?#comma)
              |\w{1}[’\u2019']{1}(?#l' m', etc.)
              |qu[’\u2019']{1}(?#qu')
              |[\w’\u2019'\-]+(?#All others "words")
              """, re.U | re.X)
    return pattern.findall(text)

def split_in_sentences(text):
    """
    break a paragraph into sentences
    and return a list
    """
    enders = re.compile(ur"[.!?\:\u2026]", re.U)
    sentences = enders.split(text)
    return sentences

def words_occurrences(text):
    occurrences = defaultdict(int)
    for k in text:
        occurrences[k] += 1
    return occurrences

def lev(s1, s2, mode=3):
    if mode == 1: 
        if len(s1) < len(s2):
            return levenshtein(s2, s1)
        if not s1:
            return len(s2)
     
        previous_row = xrange(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
                deletions = current_row[j] + 1       # than s2
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
     
        return previous_row[-1]
    elif mode == 2:
        if not s1: return len(s2)
        if not s2: return len(s1)
        return min(lev(s1[1:], s2[1:])+(s1[0] != s2[0]), lev(s1[1:], s2)+1, lev(s1, s2[1:])+1)
    else:
        s1 = ' ' + s1
        s2 = ' ' + s2
        d = {}
        S = len(s1)
        T = len(s2)
        for i in range(S):
            d[i, 0] = i
        for j in range (T):
            d[0, j] = j
        for j in range(1,T):
            for i in range(1,S):
                if s1[i] == s2[j]:
                    d[i, j] = d[i-1, j-1]
                else:
                    d[i, j] = min(d[i-1, j] + 1, d[i, j-1] + 1, d[i-1, j-1] + 1)
        return d[S-1, T-1]

