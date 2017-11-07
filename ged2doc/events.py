"""Utilities related to individual or family events.
"""

from __future__ import absolute_import, division, print_function

from collections import namedtuple

# Event structure, reflection of <EVENT_DETAIL>. Only releavant
# pieces appear here.
Event = namedtuple("Event", "tag value type date place note")

_indi_events_tags = set([
    'BIRT', 'CHR', 'DEAT', 'BURI', 'CREM', 'ADOP', 
    'BAPM', 'BARM', 'BASM', 'BLES', 'CHRA', 'CONF', 'FCOM', 'ORDN',
    'NATU', 'EMIG', 'IMMI', 'CENS', 'PROB', 'WILL',
    'GRAD', 'RETI', 'EVEN'])

_indi_attr_tags = set([
    'CAST', 'DSCR', 'EDUC', 'IDNO', 'NATI', 'NCHI', 'NMR', 'OCCU',
    'PROP', 'RELI', 'RESI', 'SSN', 'TITL', 'FACT'])

_fam_events_tags = set([
    'ANUL', 'CENS', 'DIV', 'DIVF', 'ENGA', 'MARB', 'MARC',
    'MARR', 'MARL', 'MARS', 'RESI', 'EVEN'])


def _get_events(record, tags):
    """Return events corresponding to a record.

    :param record: GEDCOM record (:py:class:`ged4py.model.Record` instance)
    :param tags: List/set of tag names.
    :return: List of :py:class:`Event` instances.
    """
    events = []
    for rec in record.sub_records:
        if rec.tag in tags:
            events.append(Event(tag=rec.tag,
                                value=rec.value,
                                type=rec.sub_tag_value('TYPE'),
                                date=rec.sub_tag_value('DATE'),
                                place=rec.sub_tag_value('PLAC'),
                                note=rec.sub_tag_value('NOTE')))
    return events


def indi_events(person):
    """Returns all events for given individual.

    :param person: INDI record (:py:class:`ged4py.model.Record` instance)
    :return: List of :py:class:`Event` instances.
    """
    return _get_events(person, _indi_events_tags)


def indi_attributes(person):
    """Returns all attributes for given individual.

    :param person: INDI record (:py:class:`ged4py.model.Record` instance)
    :return: List of :py:class:`Event` instances.
    """
    return _get_events(person, _indi_attr_tags)


def family_events(family):
    """Returns all attributes for given family.

    :param family: FAM record (:py:class:`ged4py.model.Record` instance)
    :return: List of :py:class:`Event` instances.
    """
    return _get_events(family, _fam_events_tags)
