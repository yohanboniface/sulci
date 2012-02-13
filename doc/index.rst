.. sulci documentation master file, created by
   sphinx-quickstart on Sun Feb 12 18:21:18 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to sulci's documentation!
=================================

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


Contents
========

.. toctree::
   :maxdepth: 6
   
   install
   overview
   training
   contributing
   management_commands
   api/sulci

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

