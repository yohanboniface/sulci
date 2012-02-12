Example of full training
========================

.. warning::
   the training of Sulci is a hard North face, be sure to have the 
   minimum of French knowledge, some time, some pre-categorized texts, some fast
   computer, before taking this way

.. warning:: each algorithm needs the previous algorithm to work, so remember
   to train the algorithms in the order they are called.

.. note::
   The trained data provided with the Sulci alpha version has been made with a
   corpus of :
   
   #. 30000 POS tagged words
   #. 3500 words in lexicon (lexicon must be smaller than POS corpus)
   #. FIXME: 2000 lemmatized words
   #. 40000 semantical tagged texts
   #. 17000 descriptors in thesaurus

Lexical training
----------------

First, we need to create some text corpus, in two groups:

* one group with texts where only the POS tag for each word is set. Example::

   Tout/PRV:sg était/ECJ:sg tellement/ADV absurde/ADJ:sg et/COO compliqué/ADJ:sg

  These texts need to have the `.crp` extension ; this group must be bigger.

* one other with texts where both the POS tag and the lemme are set. Example::

   Dans/PREP/dans les/DTN:pl/le faits/SBC:pl/fait ,/, la/DTN:sg/le répression/SBC:sg
   est/ECJ:sg/être contrebalancée/PAR:sg/contrebalancer

  These texts will be used to build the lexicon ; the valid extension is 
  `.lxc.lem.crp` ; this group must be smaller.

.. note::
   You can also use the algorithm to help you create the corpus : give a text to
   the algorithm, and correct the output.

Then, we can build the lexicon::

 ./manage.py sulci_train -x
 
This will write the new lexicon in temporary `.pdg` (pending) file. For now, we
have to manually rename it in `lexicon.lxc` if the result is ok for us.

Now, we can launch the lexical training::

 ./manage.py sulci_train -e

or, to load-balance the work in more than one process (using zmq), here one 
master and 4 slaves subprocesses::

 ./manage.py sulci_train -e -s 4

Another time, we have to manually rename the file generated in `/corpus/` from 
`lexical_rules.pdg` to `lexical_rules.rls`.

Then, we can launch the contextual training (remember to rename the file after)::

 ./manage.py sulci_train -c -s 4

Lemmatization
-------------

Now, the lemmatizer trainer::

 ./manage.py sulci_train -r -s 4

Semantical training
-------------------

Now, the last step, but the bigger : the semantical training. Here a big corpus 
of categorized texts is needed. For example, in Libération we are using now a 
corpus of 35000 texts.

Make sure you have configured the needed settings (see Installation below).

Then launch the command line::

 ./manage.py sulci_train -n -s 4

Postprocessing
--------------

Finally, we can clean manually to reduce noise and remove useless rows, 
for example, removing all synapses that have been seen just one time 
(triggertodescriptor.weight == 1) or those where the pondered_weight is too low 
(triggertodescriptor.pondered_weight < 0.01 for example). And after that, triggers
with no synapse can be also deleted.

