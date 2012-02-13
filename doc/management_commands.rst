.. _ref-management-commands:

===================
Management Commands
===================

Sulci comes with three management commands. They are tools useful when you work
**on** Sulci.

.. note::
   You need do define the Sulci settings to be able to use the management commands.


``sulci_cli``
===============

The ``sulci_cli`` command lets you run the semantical tagger. 
In addition to the standard management command options, you must provide the
following argument::

    ``--pk``:
        The value is the pk of the content you want to process.

Ex.::

    $ ./manage.py sulci_cli --pk=746007

``sulci_monit``
===============
The ``sulci_monit`` command lets you inspect the corpus and lexicon data. 
In addition to the standard management command options, you can provide the
following arguments::

    ``--check_corpus,-u``:
        The action will be run on the corpus.
    ``--check_lexicon,-x``:
        The action will be run on the lexicon.
    ``--count,-c``:
        Run a count on the selected set of data.
    ``--word,-w``:
        Search for a word.
    ``--tags_stats,-g``:
        Display tags stats on the selected set of data.
    ``--lemme,-M``:
        Specify a lemme.
    ``--tag,-t``:
        Specify a tag.
    ``--path,-p``:
        Specify a path.
    ``--case_insensitive,-i``:
        Case insensitive.

Count words in corpus::

    ./manage.py sulci_monit -uc

Count entries in lexicon::

    ./manage.py sulci_monit -xc

Search for occurrences of 'bateau' in corpus::

    ./manage.py sulci_monit -uw bateau

Search for occurrences of "été" in corpus where tag is "SBC:sg"::

    ./manage.py sulci_monit -uw été -t SBC:sg

Search for tag stats of word "révolutionnaires"::

    ./manage.py sulci_monit -uw révolutionnaires -g

Search for occurrences of "relève" where lemme is "relever"::

    ./manage.py sulci_monit -uw relève -M relever

Search for occurrences of "tout" case insensitive::

    ./manage.py sulci_monit -uiw tout

``sulci_train``
===============
The ``sulci_train`` command lets you train Sulci. 
In addition to the standard management command options, you can provide the
following arguments::

    ``--lexicon,-x``:
        Build the lexicon.
    ``--lexical,-e``:
        Launch the lexical trainer.
    ``--contextual,-c``:
        Launch the contextual trainer.
    ``--lemmatizer,-r``:
        Launch the lemmatizer trainer.
    ``--semantical,-n``:
        Launch the semantical trainer.
    ``--subprocesses,-s``:
        Launch trainer with w subprocesses (using zeromq).
    ``--add_candidate,-a``:
        Prepare a content to manual POS tagging (before adding it in corpus).
    ``--add_lemmes,-a``:
        When preparing a content to POS tagging, prepare lemmes to.

Build lexicon::

    ./manage.py sulci_train -x

Launch lexical training with 4 subprocesses::

    ./manage.py sulci_train -e -s 4

Add a content for POS tagging

    ./manage.py sulci_train -a --pk=123456
