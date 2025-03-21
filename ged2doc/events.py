"""Utilities related to individual or family events."""

from __future__ import annotations

__all__ = ["Event", "family_events", "indi_attributes", "indi_events"]

from typing import NamedTuple

import ged4py.date
import ged4py.model


# Event structure, reflection of <EVENT_DETAIL>. Only relevant
# pieces appear here.
class Event(NamedTuple):
    """Class representing GEDCOM event structure.

    This is a reflection of <EVENT_DETAIL>, but only relevant pieces appear
    in this class.

    Attributes
    ----------
    tag : `str`
    value : `str`, optional
    type : `str`, optional
    date : `ged4py.model.Date`, optional
    place : `str`, optional
    note : `str`, optional
    cause : `str`, optional
    """

    tag: str
    """GEDCOM tag name for the event."""

    value: str | None
    """GEDCOM record value, optional (`str` or ``None``)"""

    type: str | None
    """GEDCOM event type, optional (`str` or ``None``)"""

    date: ged4py.date.DateValue
    """Event date, optional (`ged4py.date.DateValue` or ``None``)"""

    place: str | None
    """Place where event happened, optional (`str` or ``None``)"""

    note: str | None
    """Arbitrary text note, optional (`str` or ``None``)"""

    cause: str | None
    """What caused the event, optional (`str` or ``None``)"""


_indi_events_tags = set(
    [
        "BIRT",
        "CHR",
        "DEAT",
        "BURI",
        "CREM",
        "ADOP",
        "BAPM",
        "BARM",
        "BASM",
        "BLES",
        "CHRA",
        "CONF",
        "FCOM",
        "ORDN",
        "NATU",
        "EMIG",
        "IMMI",
        "CENS",
        "PROB",
        "WILL",
        "GRAD",
        "RETI",
        "EVEN",
    ]
)

_indi_attr_tags = set(
    [
        "CAST",
        "DSCR",
        "EDUC",
        "IDNO",
        "NATI",
        "NCHI",
        "NMR",
        "OCCU",
        "PROP",
        "RELI",
        "RESI",
        "SSN",
        "TITL",
        "FACT",
    ]
)

_fam_events_tags = set(
    ["ANUL", "CENS", "DIV", "DIVF", "ENGA", "MARB", "MARC", "MARR", "MARL", "MARS", "RESI", "EVEN"]
)


def _get_events(record: ged4py.model.Record, tags: set[str]) -> list[Event]:
    """Return events corresponding to a record.

    Parameters
    ----------
    record : `ged4py.model.Record`
        GEDCOM record.
    tags : collection of `str`
        List/set of tag names.

    Returns
    -------
    events : `list` [ `Event` ]
        List of events.
    """
    events = []
    for rec in record.sub_records:
        if rec.tag in tags:
            events.append(
                Event(
                    tag=rec.tag,
                    value=rec.value,  # type: ignore
                    type=rec.sub_tag_value("TYPE"),
                    date=rec.sub_tag_value("DATE"),
                    place=rec.sub_tag_value("PLAC"),
                    note=rec.sub_tag_value("NOTE"),
                    cause=rec.sub_tag_value("CAUS"),
                )
            )
    return events


def indi_events(person: ged4py.model.Individual, tags: set[str] | None = None) -> list[Event]:
    """Return all events for a given individual.

    Parameters
    ----------
    person : `ged4py.model.Individual`
        GEDCOM INDI record.
    tags : `list` [ `str` ], optional
        Set of tags to return, default is all event tags.

    Returns
    -------
    events : `list` [ `Event` ]
        List of events.
    """
    return _get_events(person, tags or _indi_events_tags)


def indi_attributes(person: ged4py.model.Individual, tags: set[str] | None = None) -> list[Event]:
    """Return all attributes for a given individual.

    Parameters
    ----------
    person : `ged4py.model.Individual`
        GEDCOM INDI record.
    tags : `list` [ `str` ], optional
        Set of tags to return, default is all attribute tags.

    Returns
    -------
    events : `list` [ `Event` ]
        List of events.
    """
    return _get_events(person, tags or _indi_attr_tags)


def family_events(family: ged4py.model.Record, tags: set[str] | None = None) -> list[Event]:
    """Return all events for a given family.

    Parameters
    ----------
    family : `ged4py.model.Record`
        GEDCOM FAM record.
    tags : `list` [ `str` ], optional
        Set of tags to return, default is all attribute tags.

    Returns
    -------
    events : `list` [ `Event` ]
        List of events.
    """
    return _get_events(family, tags or _fam_events_tags)
