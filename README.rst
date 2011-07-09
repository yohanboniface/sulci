=====
Sulci
=====

Sulci is a French text mining tool, initially designed for the analysis of
the corpus and thesaurus of `Libération <http://www.liberation.fr/>`_, a 
French newspaper.

This code is "work in progress", but it's yet used in production at Libération.

Therefore, here is a demo page with the frozen 0.1 alpha version:
 
 http://alpha.sulci.dotcloud.com

Sulci provides 4 algorithms, designed to be run in sequence: each algorithm
needs the data provided by the previous one :

#. Part of Speech tagging
#. Lemmatization
#. Collocation and key entities extraction
#. Semantical tagging

Each algorithm must be *trained* to be operational. Therefore, a trained set of 
data is provided (see fixtures/). This is the result of a training with the
Libération corpus.

Therefore, if you want a text mining most accurate to your own texts, you must
should train it.

What does "training" mean?

#. You first need to prepare a corpus, for each of the algorithms. A corpus is a 
   set of texts with the final output you want : for example, the corpus for the 
   PosTagger is some texts where each word is pos tagged, with a verified value.
#. You then have to launch the training with the command line.
#. Each algorithm has it's own trainer. This trainer will take the input texts, 
   remove the verified output, and begin to find the best rules to determine the
   right output. The trainer will analyze its mistakes, and change its processing
   rules/weights/triggers/... in order to avoid making those mistakes again in 
   the future. The trainer will loop over the corpus until it considers that no 
   more rules could be inferred.

.. note::
   You can also use the algorithm to help you create the corpus : give a text to
   the algorithm, and correct the output.

.. warning: each algorithm needs the previous algorithm to work, so remember
   to train the algorithms in the order they are called.

.. note::
   The trained data provided with the Sulci alpha version has been made with a
   corpus of :
   #. 15500 POS tagged words
   #. 2000 words in lexicon (lexicon must be smaller than POS corpus)
   #. FIXME: 2000 lemmatized words
   #. 28000 semantical tagged words
   #. 17000 descriptors in thesaurus

Before running the first algorithm, the text is split into tokens
(words, symbols, punctuation marks, etc.), using simple regular expressions.

Sulci compared to other tools
----------------------------
We were looking for a Python tool. We looked at NLTK but ...
There are good Java tools: Apache UIMA, Gate, Apache SOLR.


Part-Of-Speech tagging
----------------------

The PosTagger finds out the "POS tag", or "lexical class", or "lexical 
category" of each word. 
The algorithm used is similar to the `Brill POS-tagging algorithm
<http://en.wikipedia.org/wiki/Brill_tagger>`_.

Some possible classes are:

* VCJ:sg (Verbe ConJugé singulier),
* PAR:pl (PARticipe pluriel),
* PREP (PREPosition),
* etc.

To see more available classes, see in base.py the methods named is_<something> or
run the following command (it provides the tag stats in corpus)::

 python manage.py sulci_cli -g

The format used is a plain text file; tokens are separated by spaces;
each token is annotated with its POS tag, separated with a slash. Example::

  Mon/DTN:sg cher/ADJ:sg Fred/SBP:sg ,/, Je/PRV:sg quitte/VCJ:sg 
  Paris/SBP:sg demain/ADV matin/SBC:sg ./. 

This format combines "input" and "output": the input is the token, the output
is the POS tag.

Check "corpus/*.crp" to see more examples of "valid output".

Lemmatization
-------------

The Lemmatizer tries to find the *Lemma* of each word. The lemma of a word
is almost similar to its stem. A few examples:

* "mangerons" lemma is "manger" (infinitive form of the verb)
* "bonnes" lemma is "bon" (masculine singular form of the adjective)
* "filles" lemma is "fille" (singular form of the noun)

The format used is similar to the one of the PosTagger, but each token
is annotated by both its POS tag and its lemma. Example::

  «/« Ce/PRV:sg/ce n'/ADV/ne est/ECJ:sg/être pas/ADV à/PREP moi/PRO:sg 
  de/PREP partir/VNCFF ./. Je/PRV:sg/je me/PRV:sg battrai/VCJ:sg/battre 
  jusqu'/PREP/jusque au/DTC:sg bout/SBC:sg ./. »/» 

If a word and its lemma are identical, the lemma is omitted. Note that
this is case-sensitive (as you can see on the first word of the above
excerpt).

Check "corpus/*.lem.lxc.crp" to see more examples of "valid output".

Semantical tagging (Collocation and key entities extraction)
------------------------------------------------------------

The Semantical Tagger tries to find "collocations" -- i.e., sequence of tokens
that have a higher chance of appearing together -- and key entities -- i.e. words
that may help to find the significance of the text : proper nouns, for example, or
ones with many occurrences in the text, etc.
A few examples:

* Président de la République
* voiture électrique
* Barack Obama

The Semantical Tagger will actually use two different algorithms:

* a purely statistical algorithm, scoring n-grams according to their
  relatives frequencies in the corpus.
* an heuristics-based algorithm, scoring n-grams (sequences of words) with
  hand-crafted rules;

The statistical algorithm uses `Point-wise mutual information 
<http://en.wikipedia.org/wiki/Pointwise_mutual_information>`_.

The first one is mainly used do determine whether or not a sequence of words is 
a collocation ; the second one, to determine whether or not a word or a collocation
is representative of the text.


Semantical training
-------------------

*  each text of the semantical corpus is processed by the previous algorithm, to
find the key entities (triggers)
* each of the triggers found are linked with a weight to the descriptors to the
text processed
* finally, the more a trigger was linked to a descriptors, the more this trigger
will trigger the descriptors in the tagging process.


After the training phase...
---------------------------

Once all algorithms have been trained to a satisfactory level, they are 
ready to analyze new texts without your guidance (i.e., you won't have
to pre-tag those texts, indeed).

Steps 1 to 4 are run in sequence, and trigger to descriptors relations are used
to extract the must pertinent descriptors.

Example of full training
------------------------

**Warning**

 the training of Sulci is a hard North face, be sure to have the 
 minimum of French knowledge, some time, some pre-categorized texts, some fast
 computer...

First, we need to create some text corpus, in two groups:

* one group with texts where only the POS tag for each word is set. Example::

 Tout/PRV:sg était/ECJ:sg tellement/ADV absurde/ADJ:sg et/COO compliqué/ADJ:sg

These texts need to have the `.crp` extension ; this group must be bigger.

* one other with texts where both the POS tag and the lemme are set. Example::

 Dans/PREP/dans les/DTN:pl/le faits/SBC:pl/fait ,/, la/DTN:sg/le répression/SBC:sg
 est/ECJ:sg/être contrebalancée/PAR:sg/contrebalancer

These texts will be used to build the lexicon ; the valid extension is 
'.lxc.lem.crp' ; this group must be smaller.

Then, we can build the lexicon::

 ./manage.py sulci_cli -m
 
This will write the new lexicon in temporary `.pdg` (pending) file. For now, we
have to manually rename it in `lexicon.lxc`.

Now, we can launch the lexical training::

 ./manage.py sulci_cli -i

or, to load-balance the work in more than one process (using zmq), here one 
master and 4 slaves subprocesses::

 ./manage.py sulci_cli -i -s 4

Another time, we have to manually rename the file generated in `/corpus/` from 
`lexical_rules.pdg` to `lexical_rules.rls`.

Then, we can launch the contextual training (remember to rename the file after)::

 ./manage.py sulci_cli -c -s 4

Now, the lemmatizer trainer::

 ./manage.py sulci_cli -r -s 4

Now, the last step, but the bigger : the semantical training. Here a big corpus 
of categorized texts is needed. For example, in Libération we are using now a 
corpus of 35000 texts.

Make sure you have configured the needed settings (see Installation below).

Then launch the command line::

 ./manage.py sulci_cli -n -s 4



Installation
------------

You have to unzip the SQL fixtures (52Mo) and load them in DB.
After that, "python setup.py install" or put the sulci folder in your 
PYTHONPATH::

 $ export PYTHONPATH=$PYTHONPATH:`pwd`

Add "sulci" to your INSTALLED_APPS.

If you plan to train you own Sulci or to use the command line,
you have to add these settings (with you own values, of course)::

 SULCI_CLI_CONTENT_MANAGER_METHOD_NAME = 'objects'
 SULCI_CLI_CONTENT_APP_NAME = 'libe'
 SULCI_CLI_CONTENT_MODEL_NAME = 'article'
 SULCI_CLI_KEYWORDS_PROPERTY = 'keywords'
 SULCI_CLI_CONTENT_PROPERTY = "content"

Sample usage::

  >> from sulci.textmining import SemanticalTagger
  >> my_text = u"Voici mon magnifique texte en français qui parle de Charlie Chaplin en Europe."
  >> S = SemanticalTagger(my_text)
  >> S.descriptors()
  ((Charlie Chaplin, 87.8984),
  (Europe, 78.4387))

Generic road-map for the beta version
------------------------------------

* More categorized texts for the POS tagger corpus (15000 words now, I'd like to
have almost 30000)

* Find a way to build unit tests for every algorithm

* Refine the key entities extraction

* Make a documentation (Sphinx)

* Find a way to remove useless relations in triggertodescriptors

* Clean thesaurus

* Be able to train the algorithm for one new descriptor

* Generic python optimization

* Generic algorithm optimization

Feel free to contribute any help!

How can I help?
---------------

* You're a python killer: there is many optimizations to do in the actual code

* You're a language expert: all the algorithm can be optimized

* You know well French language: you can add texts in the POS corpus, or make a 
proof read of the actual texts (in corpus/*.crp)

* You're an enthusiast: you can play with the demo, with the debug, and make
tickets for the bug seen ; you can help for making the doc, etc.

* in any case,
  Meet us for IRC chats: #sulci on irc.freenode.net
