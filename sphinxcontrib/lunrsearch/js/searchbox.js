/*jslint browser: true*/
/*global $, lunr, Search, DOCUMENTATION_OPTIONS*/

(function () {
    "use strict";

$.fn.textWidth = function(text, font) {
    if (!$.fn.textWidth.fakeEl) $.fn.textWidth.fakeEl = $('<span>').hide().appendTo(document.body);
    $.fn.textWidth.fakeEl.text(text || this.val() || this.text()).css('font', font || this.css('font'));
    return $.fn.textWidth.fakeEl.width();
};

var searchModule = (function ($, lunr, Search, DOCUMENTATION_OPTIONS) {
    "use strict";

    var lunrdocuments = Search.lunrdocuments;
    var index = null;
    var highlight = $("#ls_lunrsearch-highlight").value === "true";

    $.getJSON("_static/js/lunrindex.json", function(json) {
      // First, try to load the pre-generated index from file
      index = lunr.Index.load(json);
      console.log("Pre-generated lunr search index loaded.")
    }).fail(function(json, textStatus, error) {
      console.log("Could not load pre-generated lunr index (" + error + "). Generating index on the fly.")
      // We found no pre-built index; use the lunrdocuments data store to build index on the fly
      index = lunr(function () {
        this.ref('ref');
        this.field('name' , { boost: 10 });
        this.field('prefix');
        for (var docobj of Object.values(lunrdocuments)) {
          this.add({
            "ref": docobj.ref,
            "name": docobj.name,
            "prefix": docobj.prefix
          })
        }
      });
    });

    $("#ls_search-field")
        .keyup(function (event) {
            onKeyUp(event);
        })
        .keypress(function (event) {
            if (event.keyCode === 13) {
                event.preventDefault();
                var active = $('#ls_search-results li a.hover')[0];
                active.click();
            }
        })
        .focusout(function () {
            // http://stackoverflow.com/a/13980492/1079728
            window.setTimeout(function () {
                $('.results').hide();
            }, 100);
        })
        .focusin(function () {
            if ($('#ls_search-results li').length > 0) {
                $('#ls_search-results').show();
            }
        });

    function onKeyUp(event) {
        var keycode = event.keyCode || event.which,
            query = $("#ls_search-field").val(),
            ul = $('#ls_search-results'),
            i = 0,
            results = null;

        if (keycode === 13) {
            return;
        }
        if (keycode === 40 || keycode === 38) {
            return handleKeyboardNavigation(keycode);
        }
        if (query === '') {
            ul.empty().hide();
            return;
        }
        results = index.search(query);
        ul.empty().show();
        var duplicates = [];

        if (results.length === 0) {
            ul.append($('<li><a href="#">No results found</a></li>'));
        } else {
            console.log("matches:", results.length, results)
            for (i = 0; i < Math.min(results.length, 5); i += 1) {
                var doc = lunrdocuments[results[i].ref];
                var dupref = doc.name;
                if (doc.objtype === "py:method") {
                  dupref = doc.prefix;
                }
                console.log(doc)

                if(duplicates.includes(dupref)) {
                    continue;
                } else {
                  ul.append(createResultListElement(doc));
                  duplicates.push(dupref);
                }
            }
        }

        // set the width of the dropdown so that it contains all of the
        // list elements
        ul.width(Math.max(
            $('#ls_search-field').outerWidth(),
            Math.max.apply(null, ul.children().map(function(i, o) {
                return $(o).textWidth();
            })) + 20
        ));

    }  // end onKeyUp

    function handleKeyboardNavigation(keycode) {
        var ul = $('#ls_search-results'),
            active = $(ul.find('li a.hover')[0]);

        if (keycode === 40) {
            // next
            if (!active.length) {
                $(ul.find('li a')[0]).addClass('hover');
            } else {
                active.removeClass('hover');
                active.parent().next().find('a').addClass('hover');
            }
        } else if (keycode === 38) {
            // prev
            active.removeClass('hover');
            active.parent().prev().find('a').addClass('hover');
        }
    }  // end handleKeyboardNavigation

    function buildHref(s) {
        var highlightstring = highlight ? '?highlight=' + $.urlencode(s.name) : "";

        return DOCUMENTATION_OPTIONS.URL_ROOT + s.filename +
               DOCUMENTATION_OPTIONS.FILE_SUFFIX +
               highlightstring +
               '#' + s.shortanchor;
    } // end buildHref

    function createResultListElement(s) {

        var ul = $('#ls_search-results');

        return $('<li>')
            .append($('<a>')
                .attr('href', buildHref(s))
                .text(s.displayname)
                .mouseenter(function () {
                    ul.find('li a').removeClass('hover');
                    $(this).addClass('hover');
                })
                .mouseleave(function () {
                    $(this).removeClass('hover');
                })
                );
    } // end createResultListElement
});

window.onload = function() {
    searchModule($, lunr, Search, DOCUMENTATION_OPTIONS);
};

}());
