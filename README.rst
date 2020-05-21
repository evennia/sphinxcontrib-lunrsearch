sphinxcontrib-lunrsearch
========================

This extension modifies the search box in Sphinx documentation
to show instant results as you type. It's particularly suited for
searching through APIs.

To get started, ``$ pip install sphinxcontrib-lunrsearch`` and then add ``'sphinxcontrib.lunrsearch'`` to the list
of extensions in your Sphinx ``conf.py`` file.

Evennia modifications
---------------------

The ``evennia-mods`` branch adds the following additions:
- Add the optional ability to pre-generate the search index as a static file
  (activate by having the `lunr==0.5.8` Python package installed when building docs)
- Up the supported `lunr.js` version from 0.6.0 to latest stable 2.3.8, also
  resolves a bunch of compatibility issues moving to latest lunr.
- Make the searchbox not show the same name more than once (it's not very helpful
  to the user). 
- Add tokenization of all parts of documentation corpus, not just the API docs, split
  them into separate index files since (especially the terms-file) can become very 
  large for a bigger document corpus. 

The pre-generated index will be loaded into the static file storage as
`js/lunrindex.json`. The updated `searchbox.js` will load it if possible,
otherwise fall back to generating the index on the fly.

In addition, there will over time be more fine-tuning of the search parameters;
this will by necessity be Evennia-doc specific. 

Options
-------

The following options can be set in conf.py:

- lunrsearch_highlight: bool

  Whether to highlight the seach term after navigating to a results.
  The default is ``False``.

Example
-------

.. image:: http://i.giphy.com/3o85xmqkbt14LuRcZO.gif
  
