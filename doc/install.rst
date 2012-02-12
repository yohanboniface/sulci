Installation
============

Configure the env 
-----------------

Sulci is built on top of `Django <https://www.djangoproject.com/>`_, and
therefore you will need Django installed and an active `project 
<https://docs.djangoproject.com/en/1.3/intro/tutorial01/#creating-a-project>`_ 
to be able to use sulci.

Also, a SQL database (we use Postgresql) is needed.

Import the trained data
-----------------------

Retrieve the three files of the three tables:

#. `sulci_descriptor <http://ubuntuone.com/5Pw6pi8uDChIPxOWxyu9RC>`_
#. `sulci_trigger <http://ubuntuone.com/2wZoykoCy75MwLWZJlm8t2>`_
#. `sulci_triggertodescriptor <http://ubuntuone.com/4sA08VxMJAuy8OqKfZ0Xo8>`_

.. warning::
   Be careful to load at last the sulci_triggertodescriptor, as it has FK to the
   others.

.. note::
   You may have to change the table owner handly in the SQL files.

Load these three files into your database.

Install sulci
-------------

A easy way is to use pip::

    pip install git+git@github.com:yohanboniface/sulci.git

.. note::
   A very good habit is to use a `virtualenv` to do so.

Or you can retrieve the code, and "python setup.py install" or put the sulci folder in your 
PYTHONPATH::

 $ export PYTHONPATH=$PYTHONPATH:`pwd`

Then add "sulci" to your INSTALLED_APPS.

Try it from shell
-----------------

Sample usage::

    >>> from sulci.textmining import SemanticalTagger
    >>> text = u"""«La Russie et la Chine finiront par regretter leur décision qui
                 les a vues s’aligner sur un dictateur en fin de vie et qui les a
                 mises en porte-à-faux avec le peuple syrien.»"""
    >>> s = SemanticalTagger(text)
    >>> s.descriptors
    [(<Descriptor: Russie>, 100.0),
     (<Descriptor: Chine>, 100.0),
     (<Descriptor: diplomatie>, 14.798308089447328),
     (<Descriptor: Dmitri Medvedev>, 10.337552742616033)]

Configure for training
----------------------

If you plan to train you own Sulci or to use the command line,
you have to add these settings (with you own values, of course)::

 SULCI_CLI_CONTENT_MANAGER_METHOD_NAME = 'objects'
 SULCI_CLI_CONTENT_APP_NAME = 'libe'
 SULCI_CLI_CONTENT_MODEL_NAME = 'article'
 SULCI_CLI_KEYWORDS_PROPERTY = 'keywords'
 SULCI_CLI_CONTENT_PROPERTY = "content"
