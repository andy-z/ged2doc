"""Module which produces HTML output.
"""

from __future__ import absolute_import, division, print_function

__all__ = ["HtmlWriter"]

import base64
import io
import logging
import pkg_resources
import string
from PIL import Image

from .plotter import Plotter
from .size import Size
from . import utils
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

            img = self._getMainImage(person)
            if img:
                doc += [img]

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

            # Parents
            pfmt = u'<p>{person}: {ref}</p>\n'
            if person.mother:
                doc += [pfmt.format(person=_('Mother', person.mother.sex),
                                    ref=_personRef(person.mother))]
            if person.father:
                doc += [pfmt.format(person=_('Father', person.father.sex),
                                    ref=_personRef(person.father))]

            # all families as spouse
            fams = person.sub_tags("FAMS")
            if fams:
                doc += ['<h3>' + _("Spouses and children", person) + '</h3>\n']

                own_kids = []
                for fam in fams:

                    # list of Pointers
                    spouses = fam.sub_tags("HUSB", "WIFE", follow=False)
                    spouses = [rec for rec in spouses if rec.value != person.xref_id]

                    # more than one spouse is odd (from the structural concern)
                    if spouses:
                        spouse = spouses[0].ref
                    else:
                        spouse = None

                    children = fam.sub_tags("CHIL")
                    children_ids = [rec.xref_id for rec in children]

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

            for fam in person.sub_tags("FAMS"):

                spouses = fam.sub_tags("HUSB", "WIFE", follow=False)
                spouses = [spouse for spouse in spouses if spouse.value != person.xref_id]

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
                    bday = child.sub_tag("BIRT/DATE")
                    if bday:
                        note = _personRef(child, child.name.first)
                        events += [(bday.value, "BORN", note)]

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

    def _getMainImage(self, person):
        '''Returns image for a person, return value is an <img> element.

        Iterates over all OBJE records and tries to find/open files.
        Returns first file that succeeds.
        '''

        for obje in person.sub_tags('OBJE'):

            for path, form, media in obje.files:

                _log.debug('Found media file name %s', path)

                # For open_image we need basename of the file, trouble here is
                # that GEDCOM file can be prepared on different type of system.
                # For now assume that path separator in GEDCOM can be either
                # slash or backslash
                basename = path.rsplit('/', 1)[-1]
                basename = basename.rsplit('\\', 1)[-1]
                _log.debug('Trying to open image %s', basename)

                # find image file, try to open it
                imgfile = self._floc.open_image(basename)
                if imgfile:
                    _log.debug('Opened image file %s', path)
                    imgdata = imgfile.read()
                    imgfile = io.BytesIO(imgdata)
                    img = Image.open(imgfile)

                    # resize it if larger than needed
                    width = Size(self._options.get('html_image_width', '300px')).px
                    height = Size(self._options.get('html_image_height', '300px')).px
                    maxsize = (width, height)
                    size = utils.resize(img.size, maxsize)
                    size = (int(size[0]), int(size[1]))
                    if size != img.size:
                        # means size was reduced
                        _log.debug('Resize image to %s', size)
                        img = img.resize(size, Image.LANCZOS)
                        imgsize = ""
                    else:
                        # means size was not changed and image is smaller than box,
                        # we may want to extend it
                        extend = utils.resize(img.size, maxsize, False)
                        imgsize = ' width="{}" height="{}"'.format(*extend)

                    # save to a buffer
                    imgfile = io.BytesIO()
                    img.save(imgfile, 'JPEG')

                    return '<img class="personImage"' + imgsize + ' src="data:image/jpg;base64,' + base64.b64encode(imgfile.getvalue()) + '">'
