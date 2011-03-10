#!/usr/bin/python
# -*- coding: UTF-8 -*-

import string
import re
import unicodedata

from operator import itemgetter
from collections import defaultdict

from Stemmer import Stemmer

from django.utils.html import strip_tags
from django.utils.text import unescape_entities
from django.conf import settings

from utils import save_to_file, product, log
from stopwords import stop_words

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

def token_is_valid(token):
    return token not in stop_words and len(token) > 2

def filter_tokens(tokens):
    return [token for token in tokens if token_is_valid(token)]

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

def ngrams(text, min_length = 2, max_length = 10, min_count = 2):
    """
    Take a text as a list of sentences. Return ngrams and frequency.
    """
    final = {}
#    sentence = tuple(sentences[0])
    for sentence in [tokenize_text(sentence) for sentence in split_in_sentences(text)]:
        sentence = tuple(sentence)
        for begin in range(0,len(sentence)):
            for end in range(begin + min_length, len(sentence) + 1):
                g = sentence[begin:end]
#                if "projet" in g: log(g, RED)
                if normalize_token(g[0]) in stop_words or normalize_token(g[len(g)-1]) in stop_words:
                    continue
                if not g in final: final[g] = 1
                else: final[g] += 1
    return sorted([(k, v) for k, v in final.iteritems() if v >= min_count], key=itemgetter(1), reverse=True)

def guess_collocation(ngram, ngram_count, text):
    """
    Text may be tokenized.
    Return a confidence number, from 0 to 1.
    """
    confidence = 100.0
    # Lets define that a ngram of 10 for a text of 100 words
    # means 1 of confidence, so 0.1
    log("Ngram count : %f" % ngram_count, "GRAY")
    confidence *= 1.0 * ngram_count / len(text) / 0.1
    log("Confidence after counting ngram : %f" % confidence, "GRAY")
    confidence *= statistical_mutual_information(ngram, text)
    log("Confidence after SMI : %f" % confidence, "GRAY")
    confidence *= is_title(ngram)
    log("Confidence after is_title : %f" % confidence, "GRAY")
    return confidence

def statistical_mutual_information(ngram, text):
    """
    Return the probability of all the terms of the ngram to appear together.
    Do we may consider the stop_words ?
    """
    candidates = [(k, v) for k, v in enumerate(ngram) if normalize_token(v) not in stop_words \
                  and not v.isdigit() and len(v) > 1]
    alone_count = {}
    if len(candidates) == 0: return 0.1
    for candidate in candidates:
        next = candidates.index(candidate) < len(candidates) - 1 \
               and candidates[candidates.index(candidate) + 1] \
               or None
        previous = candidates.index(candidate) > 0 \
               and candidates[candidates.index(candidate) - 1] \
               or None
        alone_count[candidate] = 0
        indexes = [ idx for idx, value in enumerate(text) if value == candidate[1] ]
        for idx in indexes:
            if next is not None:
                positions_diff = next[0] - candidate[0]
                if idx >= len(text) - (positions_diff + 1) \
                   or not text[idx+positions_diff] == next[1]:
                    #we are close end of text, next can't be found
                    alone_count[candidate] += 1
            if previous is not None:
                positions_diff = candidate[0] - previous[0]
                if idx < positions_diff \
                   or not text[idx-positions_diff] == previous[1]:
                    #we are close beggin of text, preivous can't be found
                    alone_count[candidate] += 1
    res = [v for k,v in alone_count.items()]
#    print [v for v in alone_count.items()]
    if 0 in res:
        return 1
    else:
        return product([1.0 * len(ngram) / (len(ngram) + v) for v in res])

def is_title(ngram, factor = 2.0):
    """
    Define the probability of a ngram to be a title.
    Factor is for the confidence coex max.
    """
    confidence = 1
    to_test = [n for n in ngram if n not in stop_words]
    for item in to_test:
        if item.istitle(): confidence += factor / len(to_test)
#        print item, confidence
    return confidence

def make_index(expression):
    """
    Make a standardization in the expression to return a tuple who maximise
    maching possibilities.
    expression must be a list or tuple
    """
    stemmer = Stemmer("french")
    expression = [stemmer.stemWord(normalize_token(w)) for w in expression]
    expression.sort()
    return tuple(expression)

def words_occurrences(text):
    occurrences = defaultdict(int)
    for k in text:
        occurrences[k] += 1
    return occurrences

def more_frequents_token(text, min_count=2):
    occurrences = words_occurrences(text)
    candidates = [(k, v) for k, v in occurrences.iteritems() if v >= min_count \
                  and normalize_token(k) not in stop_words and not k.isdigit()\
                  and len(k) > 1]
    return sorted(candidates, key=itemgetter(1), reverse=True)

def add_to_corpus(article_id):
    """
    Retrieve an article in db, clean it, and add it to corpus.
    """
    t = Article.objects.get(pk=article_id).content
    t = normalize_text(unescape_entities(t))
    t = t.encode("utf-8")
    t = t.decode("string_escape")
    save_to_file("corpus/%s.txt" % article_id, t)
    print normalize_text(t)

#_THESAURUS = None
#def load_thesaurus():
#    print "loading thesaurus"
#    _THESAURUS = None#hack
#    if _THESAURUS is None:
#        thesaurus = {}
#        with open("thesaurus.txt") as f:
#            for line in f:
#                line = line.decode("utf-8")
#                line = line.replace("\t", "")
#                line = line.replace("\n", "")
#                line = line.replace("  ", "")
#                line = line.replace("- ", "")
#                thesaurus[make_index(tokenize_text(line))] = line
#        _THESAURUS = thesaurus
#    print "thesaurus loaded"
#    return _THESAURUS

def is_in_thesaurus(t, s):
    i = make_index(s)
    if i in t:
        print t[i]
        return True
    else:
        return False

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

