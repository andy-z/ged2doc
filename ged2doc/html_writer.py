"""Module which produces HTML output.
"""

from __future__ import absolute_import, division, print_function

__all__ = ["HtmlWriter"]

import logging
import pkg_resources
import string

from .plotter import Plotter
from .size import Size
from ged4py import model, parser


_log = logging.getLogger(__name__)


def _(x, sex="U"):
    return x


def _personRef(person, name=None):
    """Returns HTML fragment with person name linked to person.
    """
    if name is None:
        name = person.name.format(model.FMT_SURNAME_FIRST | model.FMT_MAIDEN)
    return u'<a href="#person.{0}">{1}</a>'.format(person.xref_id, name)


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

            # birth date and place
            doc += ['<p>' + _('Born', person.sex) + ": "]
            bday = person.sub_tag("BIRT/DATE")
            if bday:
                doc += [bday.value.fmt()]
            else:
                doc += [_('Unknown', person.sex)]
            bplace = person.sub_tag("BIRT/PLAC")
            if bplace:
                doc += [", " + bplace.value]
            doc += ['</p>\n']

            # family as a child, potentially could be >1
            famc = person.sub_tag("FAMC")
            if famc:
                # Parents
                pfmt = u'<p>{person}: {ref}</p>\n'
                mother = famc.sub_tag("WIFE")
                if mother:
                    doc += [pfmt.format(person=_('Mother', mother.sex),
                                        ref=_personRef(mother))]
                father = famc.sub_tag("HUSB")
                if father:
                    doc += [pfmt.format(person=_('Father', father.sex),
                                        ref=_personRef(father))]

            # all families as spouse
            fams = [rec.ref for rec in person.sub_tags("FAMS")]
            fams = [rec for rec in fams if rec is not None]
            if fams:
                doc += ['<h3>' + _("Spouses and children", person) + '</h3>\n']

                own_kids = []
                for fam in fams:

                    # list of Pointers
                    spouses = fam.sub_tags("HUSB", "WIFE")
                    spouses = [rec for rec in spouses if rec.value != person.xref_id]

                    # more than one spouse is odd (from the structural concern)
                    if spouses:
                        spouse = spouses[0].ref
                    else:
                        spouse = None

                    children = fam.sub_tags("CHIL")
                    children_ids = [rec.value for rec in children]
                    children = [rec.ref for rec in children]

                    _log.debug('spouse = %s; children ids = %s; children = %s', spouse, children_ids, children)
                    if spouse:
                        pfmt = u'<p>{person}: {ref}'
                        doc += [pfmt.format(person=_('Spouse', spouse.sex),
                                            ref=_personRef(spouse))]
                        if children:
                            kids = [_personRef(c, c.name.first) for c in children]
                            doc += ["; " + _('kids') + ': ' + ', '.join(kids)]
                        doc += ['</p>\n']
                    else:
                        own_kids += [_personRef(c, c.name.first) for c in children]
                if own_kids:
                    doc += ['<p>' + _('Kids', '') + ': ' + ', '.join(own_kids) + '</p>\n']

            # collect all events from person and families
            events = []
            for rec in person.sub_records:
                date = rec.sub_tag('DATE')
                if not date:
                    continue
                place = rec.sub_tag('PLAC')
                if place is not None:
                    place = place.value
                events += [(date.value, rec.tag, place)]
            for fam_ptr in person.sub_tags("FAMS"):

                spouses = fam.sub_tags("HUSB", "WIFE")
                spouses = [spouse for spouse in spouses if spouse.value != person.xref_id]

                fam = fam_ptr.ref
                for rec in fam.sub_records:
                    date = rec.sub_tag('DATE')
                    if not date:
                        continue
                    # list of Pointers
                    if spouses:
                        spouse = spouses[0].ref
                        note = u'{person}: {ref}'.format(person=_('Spouse', spouse.sex),
                                                         ref=_personRef(spouse))
                    else:
                        note = None
                    events += [(date.value, rec.tag, note)]

                for child in fam.sub_tags("CHIL"):
                    child = child.ref
                    bday = child.sub_tag("BIRT/DATE")
                    if bday:
                        events += [(bday.value, "BORN", child.name.first)]

            # order events
            if events:
                doc += ['<h3>' + _("Events and dates") + '</h3>\n']
            for date, tag, note in sorted(events):
                doc += ['<p>' + date.fmt() + ": " + tag]
                if note:
                    doc += [', ' + note]
                doc += ['</p>\n']

            # Comments are published as set of paragraphs
            notes = person.sub_tags('NOTE')
            if notes:
                doc += ['<h3>' + _("Comments", person) + '</h3>\n']
                for note in notes:
                    for para in note.value.split('\n'):
                        doc += ['<p>' + para + '</p>\n']

            # plot ancestors tree
            tree_elem = self._getParentTree(person)
            if tree_elem:
                doc += ['<h3>' + _("Ancestor tree", person) + '</h3>\n']
                doc += ['<div class="centered">\n']
                doc += [tree_elem]
                doc += ['</div>\n']
            else:
                doc += ['<svg width="100%" height="1pt"/>\n']

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

    def _getParentTree(self, person):
        '''
        Returns element containg parent tree or None
        '''

        width = Size(self._options.get('html_page_width')) ^ 'px'

        plotter = Plotter(width=width, gen_dist="12pt", font_size="9pt",
                          fullxml=False, refs=True)
        img = plotter.parent_tree(person, 'px')
        if img is None:
            return

        # if not None then 4-tuple
        imgdata, imgtype, width, height = img

        # return unicode string
        return imgdata
