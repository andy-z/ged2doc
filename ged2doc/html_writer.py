"""Module which produces HTML output.
"""

from __future__ import absolute_import, division, print_function

__all__ = ["HtmlWriter"]

import logging
import pkg_resources
import string

from .size import Size
from ged4py import model, parser


_log = logging.getLogger(__name__)


def _(x):
    return x


def _personRef(person, name=None):
    if name is None:
        name = person.name.full
    return u'<a href="#person.{0}">{1}</a>'.format(person.id, name)


class HtmlWriter(object):
    """Format tree as HTML document.

    :param flocator: Instance of :py:class:`input.FileLocator`
    :param dict options: Dictionary with options
    """

    def __init__(self, flocator, options):

        self._floc = flocator
        self._options = options

    def save(self, output):
        """Produce output at given destination.

        :param str output: Location of output file.
        """

        gfile = self._floc.open_gedcom()
        if not gfile:
            raise OSError("Failed to locate input file")

        encoding = self._options.get('encoding')
        errors = self._options.get('encoding_errors', 'strict')
        reader = parser.GedcomReader(gfile, encoding=encoding, errors=errors)

        # List of TOC entries
        toc = []

        # generate header
        doc = ['<!DOCTYPE html>']
        doc += ['<html>', '<head>']
        doc += ['<meta http-equiv="Content-Type" content="text/html;'
                ' charset=utf-8">\n']
        doc += ['<title>', 'Family Tree', '</title>\n']
        d = dict(page_width=Size(self._options.get('html_page_width')) ^ 'px')
        style = pkg_resources.resource_string(__name__, "data/styles/default")
        doc += [string.Template(style).substitute(d)]
        doc += ['</head>\n', '<body>\n']
        doc += ['<div id="contents_div"/>\n']

        doc += [u'<h1 id="personList">{0}</h1>\n'.format(_("Person List"))]
        toc += [(1, 'personList', _("Person List"))]

        # Index of all INDI records
        _log.debug('Scan all INDI records')
        indis = list(reader.records0('INDI'))
        indis.sort(key=lambda x: x.name.order(model.ORDER_SURNAME_GIVEN))
        for person in indis:

            name = person.name.format(model.FMT_SURNAME_FIRST | model.FMT_MAIDEN)

            _log.debug('Found INDI: %s', person)
            _log.debug('INDI name: %r', name)

            # page title
            doc += [u'<h2 id="person.{0}">{1}</h2>\n'.format(person.xref_id,
                                                             name)]
            toc += [(2, 'person.' + person.xref_id, name)]

        # add table of contents
        doc += [u'<h1>{0}</h1>\n'.format(_("Table Of Contents"))]
        lvl = 0
        for toclvl, tocid, text in toc:
            while lvl < toclvl:
                doc += ['<ul>']
                lvl += 1
            while lvl > toclvl:
                doc += ['</ul>']
                lvl -= 1
            doc += [u'<li><a href="#{0}">{1}</a></li>\n'.format(tocid, text)]
        while lvl > 0:
            doc += ['</ul>']
            lvl -= 1

        # closing
        doc += ['</body>']
        doc += ['</html>']

        if hasattr(output, 'write'):
            for line in doc:
                output.write(line.encode('utf-8'))
        else:
            out = open(output, 'wb')
            for line in doc:
                out.write(line.encode('utf-8'))
            out.close()
