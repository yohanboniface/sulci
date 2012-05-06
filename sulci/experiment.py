# -*- coding:Utf-8 -*-

from zlib import compress

def ncd(s1, s2):
    """
    Determine a distance between two strings, using compression as clustering algo.
    
    Here is the formula:

        NCD(x,y) = [min(Z(xy), Z(yx)) – min(Z(x), Z(y))] / max(Z(x), Z(y))

    Where Z(x) is the len of the text x compressed.
    
    NCD stands for `normalized compression distance`.
    
    From <http://homepages.cwi.nl/~paulv/papers/cluster.pdf>.
    """

    def Z(s):
        """
        Returns the compressed size of `s`.
        """
        return float(len(compress(s.encode('utf-8'))))
    
    zs1 = Z(s1)
    zs2 = Z(s2)
    zs1s2 = Z(s1+s2)
    zs2s1 = Z(s2+s1)
    # Normalized compression distance
    return (min(zs1s2, zs2s1) - min(zs1, zs2)) / max(zs1, zs2)
