"""Module which defines base class for all writer classes.
"""

from __future__ import absolute_import, division, print_function

__all__ = ["Writer"]

import logging

from .events import indi_attributes, indi_events, family_events
from .name import name_fmt

from . import utils
from ged4py import model, parser


_log = logging.getLogger(__name__)

# this is no-op function, only used to mark translatable strings,
# to extract all strings run "pygettext -k TR ..."


def TR(x): return x  # NOQA


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


class Writer(object):
    """Base class for document writers.

    This class knows how to extract all relevant information from GEDCOM data
    and convert it into output document. It defines basic structure of the
    produced document (sequence of section and sub-sections) and it depends
    on the subclasses to implement specific rendering of output information
    into document-specific format. Subclasses will need to implement small set
    of methods (see _render methods below).

    :param flocator: Instance of :py:class:`input.FileLocator`
    :param dict options: Dictionary with options
    :param tr: Instance of :py:class:`i18n.I18N` class
    """

    def __init__(self, flocator, options, tr):

        self._floc = flocator
        self._options = options
        self._tr = tr

    def save(self):
        """Produce output document.

        This is the main (and the only one client-callable) method of the
        writers, it will parse GEDCOM structure and produce output document
        from it.
        """

        gfile = self._floc.open_gedcom()
        if not gfile:
            raise OSError("Failed to locate input file")

        encoding = self._options.get('encoding')
        errors = self._options.get('encoding_errors', 'strict')
        reader = parser.GedcomReader(gfile, encoding=encoding, errors=errors)

        # generate starting sequence
        self._render_prolog()

        # title page
        title = self._tr.tr(TR(u"Person List"))
        self._render_section(1, 'personList', title)

        # Index of all INDI records
        _log.debug('Scan all INDI records')

        # filter out some fake records that some apps add
        indis = []
        for indi in reader.records0('INDI'):
            if indi.sub_tag_value("_UID") == "Unassociated photos":
                continue
            indis.append(indi)

        # loop over all individuals
        order = self._options.get("sort_order", model.ORDER_SURNAME_GIVEN)
        indis.sort(key=lambda x: x.name.order(order))
        fmt_mask = self._options.get('name_fmt', 0)
        for person in indis:

            name = name_fmt(person.name, fmt_mask)

            person_id = "person." + person.xref_id
            self._render_section(2, person_id, name, True)

            _log.debug('Found INDI: %s', person)
            _log.debug('INDI name: %r', name)

            image_data = self._make_main_image(person)

            attributes = []

            # birth date and place
            born = []
            bday = person.sub_tag("BIRT/DATE")
            if bday:
                born += [self._tr.tr_date(bday.value)]
            else:
                born += [self._tr.tr(TR('Date Unknown'), person.sex)]
            bplace = person.sub_tag_value("BIRT/PLAC")
            if bplace:
                born += [bplace]
            born = ', '.join(born)
            if born:
                attributes += [(self._tr.tr(TR('Born'), person.sex), born)]

            # maiden name
            if person.name.maiden:
                attributes += [(self._tr.tr(TR('Maiden name'), person.sex),
                                person.name.maiden)]

            # Parents
            if person.mother:
                attributes += [(self._tr.tr(TR('Mother'), person.mother.sex),
                                self._person_ref(person.mother))]
            if person.father:
                attributes += [(self._tr.tr(TR('Father'), person.father.sex),
                                self._person_ref(person.father))]

            # add some extra info
            indi_attr = indi_attributes(person)
            for tag in ['EDUC', 'OCCU', 'RESI', 'NMR', 'NCI']:
                for attrib in indi_attr:
                    if attrib.tag == tag:
                        attributes += [self._formatIndiAttr(person, attrib)]

            # all families as spouse
            families = []
            own_kids = []
            fams = person.sub_tags("FAMS")
            for fam in fams:

                spouse = _spouse(person, fam)
                children = fam.sub_tags("CHIL")

                children_ids = [rec.xref_id for rec in children]
                _log.debug('spouse = %s; children ids = %s; children = %s',
                           spouse, children_ids, children)

                if spouse:
                    pfmt = u'{person}: {ref}'
                    family = pfmt.format(person=self._tr.tr(TR('Spouse'),
                                                            spouse.sex),
                                         ref=self._person_ref(spouse))
                    kids = []
                    if children:
                        kids = [self._person_ref(c, c.name.first)
                                for c in children]
                        family += "; " + self._tr.tr(TR('kids')) + ': ' + \
                            ', '.join(kids)
                    families += [family]
                else:
                    own_kids += [self._person_ref(c, c.name.first)
                                 for c in children]
            if own_kids:
                family = self._tr.tr(TR('Kids')) + ': ' + ', '.join(own_kids)
                families += [family]

            # collect all events from person and families
            events = self._events(person)

            # Comments are published as set of paragraphs
            notes = []
            for note in person.sub_tags('NOTE'):
                notes += note.value.split('\n')

            # render whole person info
            self._render_person(person, image_data, attributes, families,
                                events, notes)

        # generate some stats
        if self._options.get('make_stat', True):
            section = self._tr.tr(TR("Statistics"))
            self._render_section(1, 'statistics', section)

            section = self._tr.tr(TR("Total Statistics"))
            self._render_section(2, 'total_statistics', section)

            nmales = len([person for person in indis if person.sex == 'M'])
            nfemales = len([person for person in indis if person.sex == 'F'])
            self._render_name_stat(len(indis), nfemales, nmales)

            section = self._tr.tr(TR("Name Statistics"))
            self._render_section(2, 'name_statistics', section)

            section = self._tr.tr(TR("Female Name Frequency"))
            self._render_section(3, 'female_name_freq', section)
            name_freq = self._name_freq(person for person in indis
                                        if person.sex == 'F')
            self._render_name_freq(name_freq)

            section = self._tr.tr(TR("Male Name Frequency"))
            self._render_section(3, 'male_name_freq', section)
            name_freq = self._name_freq(person for person in indis
                                        if person.sex == 'M')
            self._render_name_freq(name_freq)

        # add table of contents
        if self._options.get('make_toc', True):
            self._render_toc()

        # finish
        self._finalize()

    def _events(self, person):
        """Returns a list of events for a given person.

        Returned list contains tuples (date, info).
        """
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
                        ref=self._person_ref(spouse))
                    facts += [note]
                facts += [evt.value,
                          evt.place,
                          evt.note]
                events += [(evt.date, facts)]

            for child in fam.sub_tags("CHIL"):
                for evt in indi_events(child, ['BIRT']):
                    pfmt = self._tr.tr(TR(u"CHILD.BORN {child}"),
                                       child.sex)
                    childRef = self._person_ref(child, child.name.first)
                    facts = [pfmt.format(child=childRef),
                             evt.value,
                             evt.place,
                             evt.note]
                events += [(evt.date, facts)]

        # only use events with dates
        events = [evt for evt in events if evt[0]]

        # order events
        sevents = []
        for date, facts in sorted(events):
            facts = [fact for fact in facts if fact]
            facts = u"; ".join(facts)
            sevents += [(self._tr.tr_date(date), facts)]

        return sevents

    def _make_main_image(self, person):
        '''Returns image for a person.

        :param person: Individual record
        :return: Bytes of the image data or None.
        '''

        if not self._options.get("make_images", True):
            return None

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
                return imgdata

        return None

    def _name_freq(self, people):
        """Returns name frequency table,list of (name, count) ordered by name.
        """
        namefreq = {}
        for person in people:
            namefreq.setdefault(person.name.first, 0)
            namefreq[person.name.first] += 1
        namefreq = [(key, val) for key, val in namefreq.items()]
        # sort ascending in name
        namefreq.sort()
        return namefreq

    def _formatIndiAttr(self, person, attrib, prefix="ATTR."):
        """Formatting of the individual's attributes.

        :param Record person: Individual record
        :param events.Event attrib: Attribute structure.
        :return: Tuple (attribute, value).
        """

        attr = self._tr.tr(prefix + attrib.tag, person.sex)

        props = []
        if attrib.value:
            props.append(attrib.value)
        if attrib.date:
            props.append(self._tr.tr_date(attrib.date))
        if attrib.place:
            props.append(attrib.place)
        if attrib.note:
            props.append(attrib.note)
        props = u", ".join(props)
        return (attr, props)

    def _person_ref(self, person, name=None):
        """Returns encoded person reference.

        If person is None then None is returned. If name is not given then
        properly formatted person full name is used.

        Encoded reference consists of ASCII character SOH (\001) followed by
        reference ID, STX (\002), person name, and ETX (\003). This sequence
        will be embedded in the text and it should be interpreted lated by a
        subclasses to produce properly formatted reference in a backend-
        specific format.
        """
        if person is None:
            return None
        if name is None:
            fmt_mask = self._options.get('name_fmt', 0)
            name = name_fmt(person.name, fmt_mask)
        return utils.embed_ref(person.xref_id, name)

    def _render_prolog(self):
        """Generate initial document header/title.
        """
        raise NotImplemented()

    def _render_section(self, level, ref_id, title, newpage=False):
        """Produces new section in the output document.

        This method should also save section reference so that TOC can be
        later produced when :py:meth:`_render_toc` method is called.

        :param int level: Section level (1, 2, 3, etc.).
        :param str ref_id: Unique section identifier.
        :param str title: Printable section name.
        :param newpage: If ``True`` then start new page (for documents that
                support pagination).
        """
        raise NotImplemented()

    def _render_person(self, person, image_data, attributes, families,
                       events, notes):
        """Output person information.

        TExtual information in parameters to this method can include
        references to other persons (e.g. moter/father). Such references are
        embedded into text in encoded format determined by
        :py:meth:`_person_ref` method. It is responsibility of the subclasses
        to extract these references from text and re-encode them using proper
        bacenf representation.

        :param person: :py:class:`ged4py.Individual` instance
        :param bytes image_data: Either `None` or binary image data (typically
                content of JPEG image)
        :param list attributes: List of (attr_name, text) tuples, may be empty.
        :param list families: List of strings (possibly empty), each string
                contains description of one family and should be typically
                rendered as a separate paragraph.
        :param list events: List of (date, text) tuples, may be empty. Date
                is properly formatted string and does not need any other
                formatting.
        :param list notes: List of strings, each string should be rendered
                as separate paragraph.
        """
        raise NotImplemented()

    def _render_name_stat(self, n_total, n_females, n_males):
        """Produces summary table.

        Sum of male and female counters can be lower than total count due to
        individuals with unknown/unspecified gender.

        :param int n_total: Total number of individuals.
        :param int n_females: Number of female individuals.
        :param int n_males: Number of male individuals.
        """
        raise NotImplemented()

    def _render_name_freq(self, freq_table):
        """Produces name statistics table.

        :param freq_table: list of (name, count) tuples.
        """
        raise NotImplemented()

    def _render_toc(self):
        """Produce table of contents using info collected in _render_section().
        """
        raise NotImplemented()

    def _finalize(self):
        """Finalize output.
        """
        raise NotImplemented()