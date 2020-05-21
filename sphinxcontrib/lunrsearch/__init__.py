import os
from os.path import dirname, join, exists
import json
import warnings
import itertools

from six import iteritems
import sphinx.search
from sphinx.util.osutil import copyfile
from sphinx.jinja2glue import SphinxFileSystemLoader


# pre-generate search index
_PREGENERATE_INDEX = True
_LUNR_INDEX_FILENAME = "lunrindex.json"

lunr = None
if _PREGENERATE_INDEX:
    try:
        # if python-lunr is available we pre-build the index
        import lunr
    except ImportError:
        print("python package `lunr==0.5.8` required in order "
              "to pre-build search index.")


def _make_iter(inp):
    """make sure input is an iterable"""
    if not hasattr(inp, "__iter__"):
        return (inp, )
    return inp


class IndexBuilder(sphinx.search.IndexBuilder):
    def freeze(self):
        """Create a usable data structure for serializing."""
        data = super(IndexBuilder, self).freeze()
        try:
            # Sphinx >= 1.5 format
            # Due to changes from github.com/sphinx-doc/sphinx/pull/2454
            base_file_names = data['docnames']
        except KeyError:
            # Sphinx < 1.5 format
            base_file_names = data['filenames']

        lunrdocuments = {}
        c = itertools.count()
        for prefix, items in iteritems(data['objects']):
            # This parses API objects
            for name, (index, typeindex, _, shortanchor) in iteritems(items):
                objtype = data['objtypes'][typeindex]
                if objtype.startswith('cpp:'):
                    # C++ API entities
                    split =  name.rsplit('::', 1)
                    if len(split) != 2:
                        warnings.warn("What's up with %s?" % str((prefix, name, objtype)))
                        continue
                    prefix, name = split
                    last_prefix = prefix.split('::')[-1]
                    displayname = name

                elif objtype.startswith("py:"):
                    # Python API entitites 
                    last_prefix = prefix.split('.')[-1]
                    if objtype == "py:method":
                        displayname = last_prefix + "." + name  
                    else:
                        displayname = prefix + "." + name

                else:
                    last_prefix = prefix.split('.')[-1]
                    displayname = name

                ref = next(c)
                lunrdocuments[ref] = {
                    'ref': str(ref),
                    'filename': base_file_names[index],
                    'objtype': objtype,
                    'prefix': prefix,
                    'last_prefix': last_prefix,
                    'name': name,
                    'displayname': displayname,
                    'shortanchor': shortanchor,
                }

        titles = data['titles']
        for titleterm, indices in data['titleterms'].items():
            # Title components; the indices map to index in base_file_name
            for index in _make_iter(indices):
                ref = next(c)
                lunrdocuments[ref] = {
                    'ref': str(ref),
                    'filename': base_file_names[index],
                    'objtype': "",
                    'prefix': titleterm,
                    'last_prefix': '',
                    'name': titles[index],
                    'displayname': titles[index],
                    'shortanchor': ''
                }

        # this is just too big for regular use 
        # for term, indices in data['terms'].items():
        #     # In-file terms
        #     for index in _make_iter(indices):
        #         ref = next(c)
        #         lunrdocuments[ref] = {
        #             'ref': str(ref),
        #             'filename': base_file_names[index],
        #             'objtype': "",
        #             'prefix': term,
        #             'last_prefix': '',
        #             'name': titles[index],
        #             'displayname': titles[index],
        #             'shortanchor': ''
        #         }

        if lunr:
            print("\nPre-building search index ...")
            # pre-compile the data store into a lunr index
            fields = ["ref", "prefix", dict(field_name="name", boost=10)]
            lunr_index = lunr.lunr(ref='ref', fields=fields,
                                   documents=list(lunrdocuments.values()))
            lunr_index_json = lunr_index.serialize()
            lunr_index_json = json.dumps(lunr_index_json)

            try:
                fname = join(dirname(__file__), "js", _LUNR_INDEX_FILENAME)
                with open(fname, 'w') as fil:
                    fil.write(lunr_index_json)
            except Exception as err:
                print("Failed saving lunr index to", fname, err)

        # we also need this for back-referencing that which the index finds
        data.update({'lunrdocuments': lunrdocuments})

        return data


def builder_inited(app):
    # adding a new loader to the template system puts our searchbox.html
    # template in front of the others, it overrides whatever searchbox.html
    # the current theme is using.
    # it's still up to the theme to actually _use_ a file called searchbox.html
    # somewhere in its layout. but the base theme and pretty much everything
    # else that inherits from it uses this filename.
    app.builder.templates.loaders.insert(0, SphinxFileSystemLoader(dirname(__file__)))

    # adds the variable to the context used when rendering the searchbox.html
    app.config.html_context.update({
        'lunrsearch_highlight': json.dumps(bool(app.config.lunrsearch_highlight))
    })


def copy_static_files(app, _):
    # because we're using the extension system instead of the theme system,
    # it's our responsibility to copy over static files outselves.
    files = [join('js', 'searchbox.js'), join('css', 'searchbox.css')]

    if lunr:
        files.append(join('js', _LUNR_INDEX_FILENAME))

    for f in files:
        src = join(dirname(__file__), f)
        dest = join(app.outdir, '_static', f)
        if not exists(dirname(dest)):
            os.makedirs(dirname(dest))
        copyfile(src, dest)


def setup(app):
    # adds <script> and <link> to each of the generated pages to load these
    # files.
    app.add_javascript('https://cdnjs.cloudflare.com/ajax/libs/lunr.js/2.3.8/lunr.min.js')
    app.add_stylesheet('css/searchbox.css')
    app.add_javascript('js/searchbox.js')

    app.connect('builder-inited', builder_inited)
    app.connect('build-finished', copy_static_files)
    app.add_config_value('lunrsearch_highlight', True, 'html')

    sphinx.search.IndexBuilder = IndexBuilder
