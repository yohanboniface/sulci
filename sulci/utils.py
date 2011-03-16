# -*- coding:Utf-8 -*-
import codecs
import os

def save_to_file(filename, content, verbose = False):
    if verbose:
        print "INFOS **** Writing to file: %s" % filename
#    print content
    pwd = not filename.startswith("/") and get_dir() or ""
    f = codecs.open(pwd + filename, 'w', "utf-8") 
    f.write(content)
    f.close()    

def load_file(path):
    pwd = not path.startswith("/") and get_dir() or ""
    f = codecs.open(pwd + path, "r", "utf-8")
    c = f.read()
    f.close()
    return c

def get_dir(fileref=__file__):
    """
    Return absolute path of a file with the trailing slash.
    """
    pwd = os.path.realpath(os.path.dirname(fileref))
    return "%s/" % pwd

def sort(seq, attr, reverse=True):
    intermed = [ (getattr(seq[i],attr), i, seq[i]) for i in xrange(len(seq)) ]
    intermed.sort()
    if reverse: intermed.reverse()
    return [ tup[-1] for tup in intermed ]

def product(nums):
    """
    Like sum, but for product.
    """
    return reduce(lambda x,y:x*y,nums)

def has_index(indexable, value):
    try:
        indexable.index(value)
        return True
    except ValueError:
        return False

def uniqify(seq, idfun=None):
    """
    From http://www.peterbe.com/plog/uniqifiers-benchmark
    """
    # order preserving
    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
    return result

class Memoize:
    def __init__ (self, f):
        self.f = f
        self.mem = {}
    def __call__ (self, *args, **kwargs):
        if (args, str(kwargs)) in self.mem:
            return self.mem[args, str(kwargs)]
        else:
            tmp = self.f(*args, **kwargs)
            self.mem[args, str(kwargs)] = tmp
            return tmp


# Utils functions
def log(s, color=None, highlight=False, mode=None):
    colors = {
              "GRAY": 0,
              "RED": 1,
              "GREEN": 2,
              "YELLOW": 3,
              "BLUE": 4,
              "MAGENTA": 5,
              "CYAN": 6,
              "WHITE": 7,
              "CRIMSON": 8
             }
    DEBUG = True
    prefix = suffix = u""
    if color is not None:
        base = highlight and 40 or 30
        prefix = u"\033[1;%sm" % (base + colors[color])
        suffix = u"\033[1;m"
    if __debug__:
        print u"*%s* - %s%s%s" % (os.getpid(),prefix, s, suffix)

