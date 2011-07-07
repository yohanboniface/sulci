# -*- coding:Utf-8 -*-
#We define stop words, words that don't add meaning to the entity or sample they are in
stop_words = [u'a', u'à', u'après', u'au', u'aux', u'avec', u'ce', u'ces', u'comme', 
              u'dans', u'de', u'des', u'du',
              u'elle', u'en', u'entre', u'et', u'eux', u'il', u'je', u"jusque", 
              u"jusqu", u'la', u'le', u'leur', u'lui', u'lors',
              u'ma', u'mais', u'me', u'même', u'mes', u'moi', u'mon', u'ne', u'nos', 
              u'notre', u'nous', u'on', u'ou', u"où", u'par', u'pas', u'pour', u'qu', u'que', 
              u'qui', u'sa', u'se', u'ses', u'son', u'sur', u'ta', u'te', u'tes', u'toi', 
              u'ton', u'tu', u'un', u'une', u'vos', u'votre', u'vous', u'c', u'd', u'j', 
              u'l', u'à', u'm', u'n', u's', u't', u'y', u'été', u'étée', u'étées', u'étés',
              u'étant', u'suis', u'es', u'est', u'sommes', u'êtes', u'sont', u'serai', 
              u'seras', u'sera', u'serons', u'serez', u'seront', u'serais', u'serait',
              u'serions', u'seriez', u'seraient', u'étais', u'était', u'étions', 
              u'étiez', u'étaient', u'fus', u'fut', u'fûmes', u'fûtes', u'furent', 
              u'sois', u'soit', u'soyons', u'soyez', u'soient', u'fusse', u'fusses', 
              u'fût', u'fussions', u'fussiez', u'fussent', u'ayant', u'eu', u'eue', 
              u'eues', u'eus', u'ai', u'as', u'avons', u'avez', u'ont', u'aurai', 
              u'auras', u'aura', u'aurons', u'aurez', u'auront', u'aurais', u'aurait', 
              u'aurions', u'auriez', u'auraient', u'avais', u'avait', u'avions', 
              u'aviez', u'avaient', u'eut', u'eûmes', u'eûtes', u'eurent', u'aie', 
              u'aies', u'ait', u'ayons', u'ayez', u'aient', u'eusse', u'eusses', u'eût', 
              u'eussions', u'eussiez', u'eussent', u'ceci', u'celà', u'cet', u'cette', 
              u'ici', u'ils', u'les', u'leurs', u'quel', u'quels', u'quelle', 
              u'quelles', u'sans', u'soi', u"quelque", u"quelques", u"si", 
              u"jusqu'au", u"jusqu'à", u"jusqu’au", u"jusqu’à", u"alors", u"ça", u"fait",
              u"faite", u"faits", u"faites", u"qu'"]

#We define usual_words, words that are very common, and so have less chance to be special keywords
usual_words = stop_words + [u'pourquoi', u'chez', u"avant", u"après", u"plus", 
                            u"ensuite", u"autant", u"surtout", u"plutôt", u"car",
                            u"toujours", u"encore", u"parmi", u"malgré", u"depuis",
                            u"donc", u"tout", u"tous", u"toute", u"toutes", u"aussi",
                            u"très", u"avoir", u"faire", u"quant"]
