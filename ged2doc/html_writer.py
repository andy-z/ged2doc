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

from .events import indi_attributes, indi_events, family_events
from .plotter import Plotter
from .size import Size
from . import utils
from ged4py import model, parser


_log = logging.getLogger(__name__)

# this is no-op function, only used to mark translatable strings,
# to extract all strings run "pygettext -k TR ..."
TR = lambda x: x  # NOQA


def _personRef(person, name=None):
    """Returns HTML fragment with person name linked to person.
    """
    if name is None:
        name = person.name.format(model.FMT_SURNAME_FIRST | model.FMT_MAIDEN)
    return u'<a href="#person.{0}">{1}</a>'.format(person.xref_id, name)


def _spouse(person, fam):
    """Returns person spouse in a given family
    """
    # list of Pointers
    spouses = fam.sub_tags("HUSB", "WIFE", follow=False)
    spouses = [rec for rec in spouses
               if rec.value != person.xref_id]
    # more than one spouse is odd (from the structural concern)
    if spouses:
        return spouses[0].ref
    return None


class HtmlWriter(object):
    """Format tree as HTML document.

    :param flocator: Instance of :py:class:`input.FileLocator`
    :param dict options: Dictionary with options
    """

    def __init__(self, flocator, options, tr):

        self._floc = flocator
        self._options = options
        self._tr = tr

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

        title = self._tr.tr(TR(u"Person List"))
        doc += [u'<h1 id="personList">{0}</h1>\n'.format(title)]
        toc += [(1, 'personList', title)]

        # Index of all INDI records
        _log.debug('Scan all INDI records')

        # filter out some fake records that some apps add
        indis = []
        for indi in reader.records0('INDI'):
            if indi.sub_tag_value("_UID") == "Unassociated photos":
                continue
            indis.append(indi)

        indis.sort(key=lambda x: x.name.order(model.ORDER_SURNAME_GIVEN))
        for person in indis:

            name = person.name.format(model.FMT_SURNAME_FIRST |
                                      model.FMT_MAIDEN)

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
            doc += ['<p>' + self._tr.tr(TR('Born'), person.sex) + ": "]
            bday = person.sub_tag("BIRT/DATE")
            if bday:
                doc += [bday.value.fmt()]
            else:
                doc += [self._tr.tr(TR('Date Unknown'), person.sex)]
            bplace = person.sub_tag("BIRT/PLAC")
            if bplace:
                doc += [", " + bplace.value]
            doc += ['</p>\n']

            # Parents
            pfmt = u'<p>{person}: {ref}</p>\n'
            if person.mother:
                doc += [pfmt.format(person=self._tr.tr(TR('Mother'),
                                                       person.mother.sex),
                                    ref=_personRef(person.mother))]
            if person.father:
                doc += [pfmt.format(person=self._tr.tr(TR('Father'),
                                                       person.father.sex),
                                    ref=_personRef(person.father))]

            # add some extra info
            attributes = indi_attributes(person)
            for tag in ['EDUC', 'OCCU', 'RESI', 'NMR', 'NCI']:
                for attrib in attributes:
                    if attrib.tag == tag:
                        doc += [self._formatIndiAttr(person, attrib)]

            # all families as spouse
            fams = person.sub_tags("FAMS")
            if fams:
                doc += ['<h3>' + self._tr.tr(TR("Spouses and children"),
                                             person.sex) + '</h3>\n']

                own_kids = []
                for fam in fams:

                    spouse = _spouse(person, fam)
                    children = fam.sub_tags("CHIL")
                    children_ids = [rec.xref_id for rec in children]

                    _log.debug('spouse = %s; children ids = %s; children = %s',
                               spouse, children_ids, children)
                    if spouse:
                        pfmt = u'<p>{person}: {ref}'
                        doc += [pfmt.format(person=self._tr.tr(TR('Spouse'),
                                                               spouse.sex),
                                            ref=_personRef(spouse))]
                        if children:
                            kids = [_personRef(c, c.name.first)
                                    for c in children]
                            doc += ["; " + self._tr.tr(TR('kids')) + ': ' +
                                    ', '.join(kids)]
                        doc += ['</p>\n']
                    else:
                        own_kids += [_personRef(c, c.name.first)
                                     for c in children]
                if own_kids:
                    doc += ['<p>' + self._tr.tr(TR('Kids')) + ': ' +
                            ', '.join(own_kids) + '</p>\n']

            # collect all events from person and families
            events = []
            for evt in indi_events(person):
                # BIRT was already rendered
                if evt.tag != 'BIRT':
                    facts = [self._tr.tr("EVENT." + evt.tag, person.sex),
                             evt.value,
                             evt.place,
                             evt.note]
                    events += [(evt.date, facts)]

            for fam in person.sub_tags("FAMS"):

                spouse = _spouse(person, fam)

                for evt in family_events(fam):
                    facts = [self._tr.tr("FAMEVT." + evt.tag)]
                    if spouse:
                        note = u'{spouse}: {ref}'.format(
                            spouse=self._tr.tr(TR('Spouse'), spouse.sex),
                            ref=_personRef(spouse))
                        facts += [note]
                    facts += [evt.value,
                              evt.place,
                              evt.note]
                    events += [(evt.date, facts)]

                for child in fam.sub_tags("CHIL"):
                    for evt in indi_events(child, ['BIRT']):
                        pfmt = self._tr.tr(TR(u"CHILD.BORN {child}"),
                                           child.sex)
                        childRef = _personRef(child, child.name.first)
                        facts = [pfmt.format(child=childRef),
                                 evt.value,
                                 evt.place,
                                 evt.note]
                    events += [(evt.date, facts)]

            # only use events with dates
            events = [evt for evt in events if evt[0]]

            if events:
                doc += ['<h3>' + self._tr.tr(TR("Events and dates")) +
                        '</h3>\n']
            # order events
            for date, facts in sorted(events):
                facts = [fact for fact in facts if fact]
                facts = u"; ".join(facts)
                doc += ['<p>' + date.fmt() + ": " + facts + '</p>']

            # Comments are published as set of paragraphs
            notes = person.sub_tags('NOTE')
            if notes:
                doc += ['<h3>' + self._tr.tr(TR("Comments")) + '</h3>\n']
                for note in notes:
                    for para in note.value.split('\n'):
                        doc += ['<p>' + para + '</p>\n']

            # plot ancestors tree
            tree_elem = self._getParentTree(person)
            if tree_elem:
                doc += ['<h3>' + self._tr.tr(TR("Ancestor tree")) + '</h3>\n']
                doc += ['<div class="centered">\n']
                doc += [tree_elem]
                doc += ['</div>\n']
            else:
                doc += ['<svg width="100%" height="1pt"/>\n']

        # generate some stats
        if self._options.get('make_stat', True):
            section = self._tr.tr(TR("Statistics"))
            doc += [u'<h1 id="statistics">{0}</h1>\n'.format(section)]
            toc += [(1, 'statistics', section)]

            section = self._tr.tr(TR("Total Statistics"))
            doc += [u'<h2 id="total_statistics">{0}</h2>\n'.format(section)]
            toc += [(2, 'total_statistics', section)]

            nmales = len([person for person in indis if person.sex == 'M'])
            nfemales = len([person for person in indis if person.sex == 'F'])
            doc += ['<p>%s: %d</p>' % (self._tr.tr(TR('Person count')),
                                       len(indis))]
            doc += ['<p>%s: %d</p>' % (self._tr.tr(TR('Female count')),
                                       nfemales)]
            doc += ['<p>%s: %d</p>' % (self._tr.tr(TR('Male count')), nmales)]

            section = self._tr.tr(TR("Name Statistics"))
            doc += [u'<h2 id="name_statistics">{0}</h2>\n'.format(section)]
            toc += [(2, 'name_statistics', section)]

            section = self._tr.tr(TR("Female Name Frequency"))
            doc += [u'<h3 id="female_name_freq">{0}</h3>\n'.format(section)]
            doc += self._namestat(person for person in indis
                                  if person.sex == 'F')

            section = self._tr.tr(TR("Male Name Frequency"))
            doc += [u'<h3 id="male_name_freq">{0}</h3>\n'.format(section)]
            doc += self._namestat(person for person in indis
                                  if person.sex == 'M')

        # add table of contents
        if self._options.get('make_toc', True):
            section = self._tr.tr(TR("Table Of Contents"))
            doc += [u'<h1>{0}</h1>\n'.format(section)]
            lvl = 0
            for toclvl, tocid, text in toc:
                while lvl < toclvl:
                    doc += ['<ul>']
                    lvl += 1
                while lvl > toclvl:
                    doc += ['</ul>']
                    lvl -= 1
                doc += [u'<li><a href="#{0}">{1}</a></li>\n'.format(tocid,
                                                                    text)]
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
        '''

        path = utils.personImageFile(person)
        if path:

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
            if not imgfile:
                _log.warn('Failed to locate image file "%s"', basename)
            else:
                _log.debug('Opened image file %s', path)
                imgdata = imgfile.read()
                imgfile = io.BytesIO(imgdata)
                img = Image.open(imgfile)

                # resize it if larger than needed
                width = Size(self._options.get('html_image_width',
                                               '300px')).px
                height = Size(self._options.get('html_image_height',
                                                '300px')).px
                maxsize = (width, height)
                size = utils.resize(img.size, maxsize)
                size = (int(size[0]), int(size[1]))
                if size != img.size:
                    # means size was reduced
                    _log.debug('Resize image to %s', size)
                    img = img.resize(size, Image.LANCZOS)
                    imgsize = ""
                else:
                    # means size was not changed and image is smaller
                    # than box, we may want to extend it
                    extend = utils.resize(img.size, maxsize, False)
                    imgsize = ' width="{}" height="{}"'.format(*extend)

                # save to a buffer
                imgfile = io.BytesIO()
                img.save(imgfile, 'JPEG')

                return '<img class="personImage"' + imgsize + \
                    ' src="data:image/jpg;base64,' + \
                    base64.b64encode(imgfile.getvalue()) + '">'

    def _namestat(self, people):
        """Produces name statistics table.
        """
        def _gencouples(namefreq):
            halflen = (len(namefreq) + 1) // 2
            for i in range(halflen):
                n1, c1 = namefreq[2 * i]
                n2, c2 = None, None
                if 2 * i + 1 < len(namefreq):
                    n2, c2 = namefreq[2 * i + 1]
                yield n1, c1, n2, c2

        namefreq = {}
        for person in people:
            namefreq.setdefault(person.name.first, 0)
            namefreq[person.name.first] += 1
        namefreq = [(key, val) for key, val in namefreq.items()]
        # sort ascending in name
        namefreq.sort()
        total = float(sum(count for _, count in namefreq))

        tbl = ['<table class="statTable">\n']

        for name1, count1, name2, count2 in _gencouples(namefreq):

            tbl += ['<tr>\n']

            tbl += [u'<td width="25%">{0}</td>'.format(name1 or '-')]
            tbl += ['<td width="20%">{0} ({1:.1%})</td>'.format(
                count1, count1 / total)]

            if count2 is not None:

                tbl += [u'<td width="25%">{0}</td>'.format(name2 or '-')]
                tbl += ['<td width="20%">{0} ({1:.1%})</td>'.format(
                    count2, count2 / total)]

            tbl += ['</tr>\n']

        tbl += ['</table>\n']
        return tbl

    def _formatIndiAttr(self, person, attrib, prefix="ATTR."):
        """Formatting of the individual's attributes.

        :param Record person: Individual record
        :param events.Event attrib: Attribute structure.
        :return: Formatted string.
        """

        attr = self._tr.tr(prefix + attrib.tag, person.sex)

        props = []
        if attrib.value:
            props.append(attrib.value)
        if attrib.date:
            props.append(attrib.date.fmt())
        if attrib.place:
            props.append(attrib.place)
        if attrib.note:
            props.append(attrib.note)
        props = u", ".join(props)
        return '<p>' + attr + ": " + props + '</p>'
