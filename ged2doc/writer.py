"""Module which defines base class for all writer classes.
"""

from __future__ import absolute_import, division, print_function

__all__ = ["Writer"]

import locale
import logging

from .events import indi_attributes, indi_events, family_events
from .name import name_fmt

from . import utils
from ged4py import model, parser
from ged4py.date import DateValue


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

    :param flocator: Instance of :py:class:`ged2doc.input.FileLocator`
    :param tr: Instance of :py:class:`ged2doc.i18n.I18N` class
    :param str encoding: GEDCOM file encoding, if ``None`` then encoding is
        determined from file itself
    :param str encoding_errors: Controls error handling behavior during string
        decoding, one of "strict" (default), "ignore", or "replace".
    :param sort_order: Determines ordering of person in output file, one of
        the constants defined in :py:mod:`ged4py.model` module.
    :param int name_fmt: Bit mask with flags from :py:mod:`ged2doc.name`
    :param bool make_images: If ``True`` (default) then generate images for
        persons.
    :param bool make_stat: If ``True`` (default) then generate statistics
        section.
    :param bool make_toc: If ``True`` (default) then generate Table of
        Contents.
    :param bool events_without_dates: If ``True`` (default) then show events
        that have no associated dates.
    """

    def __init__(self, flocator, tr, encoding=None, encoding_errors="strict",
                 sort_order=model.ORDER_SURNAME_GIVEN, name_fmt=0,
                 make_images=True, make_stat=True, make_toc=True,
                 events_without_dates=True):

        self._floc = flocator
        self._encoding = encoding
        self._encoding_errors = encoding_errors
        self._sort_order = sort_order
        self._name_fmt = name_fmt
        self._make_images = make_images
        self._make_stat = make_stat
        self._make_toc = make_toc
        self._events_without_dates = events_without_dates
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

        reader = parser.GedcomReader(gfile, encoding=self._encoding,
                                     errors=self._encoding_errors)

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
        indis.sort(key=self._indi_sort_key)
        for person in indis:

            name = name_fmt(person.name, self._name_fmt)

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
            for tag in ['EDUC', 'OCCU', 'RESI', 'NMR', 'NCHI', 'TITL', 'DSCR',
                        'RELI', 'FACT']:
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
        if self._make_stat:
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
        if self._make_toc:
            self._render_toc()

        # finish
        self._finalize()

    def _indi_sort_key(self, indi):
        """Return name ordering key for individual
        """
        # make key from name, this is a tuple of unicode strings
        key = indi.name.order(self._sort_order)

        # we want locale-aware ordering
        key = tuple(locale.strxfrm(x) for x in key)

        return key

    def _events(self, person):
        """Returns a list of events for a given person.

        Returned list contains tuples (date, info).
        """
        # collect all events from person and families
        events = []
        for evt in indi_events(person):
            # BIRT was already rendered
            if evt.tag != 'BIRT':
                # for generic EVEN event, use TYPE as even name, we cannot
                # translate it because it can be anything
                if evt.tag == 'EVEN' and evt.type:
                    event = evt.type
                else:
                    event = self._tr.tr("EVENT." + evt.tag, person.sex)
                facts = [event,
                         evt.value,
                         evt.place,
                         evt.note]
                if evt.cause:
                    pfmt = self._tr.tr(TR("EVENT.CAUSE: {cause}"), person.sex)
                    facts.append(pfmt.format(cause=evt.cause))
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

        def _date_key(event):
            "Return event date, used for comparison"
            date = event[0]
            if date is None:
                # use date in the future
                date = DateValue.parse(None)
            return date

        # order events (only those with dates)
        sevents = []
        for date, facts in sorted(events, key=_date_key):
            facts = [fact for fact in facts if fact]
            facts = u"; ".join(facts)
            if date is None:
                if self._events_without_dates:
                    sevents += [(self._tr.tr(TR("Event Date Unknown")), facts)]
            else:
                sevents += [(self._tr.tr_date(date), facts)]

        return sevents

    def _make_main_image(self, person):
        '''Returns image for a person.

        :param person: Individual record
        :return: Bytes of the image data or None.
        '''

        if not self._make_images:
            return None

        path = utils.personImageFile(person)
        if path:

            _log.debug('Found media file name %s', path)

            # find image file, try to open it
            imgfile = self._floc.open_image(path)
            if not imgfile:
                _log.warning('Failed to locate image file "%s"', path)
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

        # for generic FACT attribute, use TYPE as fact name, we cannot
        # translate it because it can be anything
        if attrib.tag == 'FACT' and attrib.type:
            attr = attrib.type
        else:
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
            name = name_fmt(person.name, self._name_fmt)
        return utils.embed_ref(person.xref_id, name)

    def _render_prolog(self):
        """Generate initial document header/title.
        """
        raise NotImplementedError()

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
        raise NotImplementedError()

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
        raise NotImplementedError()

    def _render_name_stat(self, n_total, n_females, n_males):
        """Produces summary table.

        Sum of male and female counters can be lower than total count due to
        individuals with unknown/unspecified gender.

        :param int n_total: Total number of individuals.
        :param int n_females: Number of female individuals.
        :param int n_males: Number of male individuals.
        """
        raise NotImplementedError()

    def _render_name_freq(self, freq_table):
        """Produces name statistics table.

        :param freq_table: list of (name, count) tuples.
        """
        raise NotImplementedError()

    def _render_toc(self):
        """Produce table of contents using info collected in _render_section().
        """
        raise NotImplementedError()

    def _finalize(self):
        """Finalize output.
        """
        raise NotImplementedError()
