"""Unit test for events module
"""

from __future__ import absolute_import, division, print_function

from ged2doc import events
from ged4py import model


def test_001_indi_events():
    """Test indi_events method."""

    dialect = model.DIALECT_MYHERITAGE

    rtype = model.make_record(2, None, "TYPE", "SomeType", [], 0, dialect, None).freeze()
    rec1 = model.make_record(1, None, "BIRT", "", [rtype], 0, dialect, None).freeze()
    plac = model.make_record(2, None, "PLAC", "Some Place", [], 0, dialect, None).freeze()
    rec2 = model.make_record(1, None, "DEAT", "Y", [plac], 0, dialect, None).freeze()
    rec3 = model.make_record(1, None, "OCCU", "", [], 0, dialect, None).freeze()
    rec4 = model.make_record(1, None, "EDUC", "", [], 0, dialect, None).freeze()
    person = model.make_record(0, None, "INDI", "", [rec1, rec2, rec3, rec4], 0, dialect, None).freeze()
    evts = events.indi_events(person)
    assert len(evts) == 2
    assert evts[0].tag == 'BIRT'
    assert evts[0].value == ''
    assert evts[0].type == 'SomeType'
    assert evts[0].place is None
    assert evts[1].tag == 'DEAT'
    assert evts[1].value == 'Y'
    assert evts[1].type is None
    assert evts[1].place == 'Some Place'


def test_002_indi_attributes():
    """Test indi_attributes method."""

    dialect = model.DIALECT_MYHERITAGE

    rec1 = model.make_record(1, None, "BIRT", "", [], 0, dialect, None).freeze()
    rec2 = model.make_record(1, None, "DEAT", "Y", [], 0, dialect, None).freeze()
    rtype = model.make_record(2, None, "TYPE", "SomeType", [], 0, dialect, None).freeze()
    rec3 = model.make_record(1, None, "OCCU", "Occupational Occupation", [rtype], 0, dialect, None).freeze()
    plac = model.make_record(2, None, "PLAC", "Some Place", [], 0, dialect, None).freeze()
    rec4 = model.make_record(1, None, "EDUC", "Sunday Church", [plac], 0, dialect, None).freeze()
    person = model.make_record(0, None, "INDI", "", [rec1, rec2, rec3, rec4], 0, dialect, None).freeze()
    evts = events.indi_attributes(person)
    assert len(evts) == 2
    assert evts[0].tag == 'OCCU'
    assert evts[0].value == 'Occupational Occupation'
    assert evts[0].type == 'SomeType'
    assert evts[0].place is None
    assert evts[1].tag == 'EDUC'
    assert evts[1].value == 'Sunday Church'
    assert evts[1].type is None
    assert evts[1].place == 'Some Place'


def test_003_family_events():
    """Test family_events method."""

    dialect = model.DIALECT_MYHERITAGE

    rtype = model.make_record(2, None, "TYPE", "SomeType", [], 0, dialect, None).freeze()
    rec1 = model.make_record(1, None, "MARR", "Y", [rtype], 0, dialect, None).freeze()
    plac = model.make_record(2, None, "PLAC", "Some Place", [], 0, dialect, None).freeze()
    rec2 = model.make_record(1, None, "DIV", "", [plac], 0, dialect, None).freeze()
    rec3 = model.make_record(1, None, "OCCU", "", [], 0, dialect, None).freeze()
    rec4 = model.make_record(1, None, "EDUC", "", [], 0, dialect, None).freeze()
    person = model.make_record(0, None, "FAM", "", [rec1, rec2, rec3, rec4], 0, dialect, None).freeze()
    evts = events.family_events(person)
    assert len(evts) == 2
    assert evts[0].tag == 'MARR'
    assert evts[0].value == 'Y'
    assert evts[0].type == 'SomeType'
    assert evts[0].place is None
    assert evts[1].tag == 'DIV'
    assert evts[1].value == ''
    assert evts[1].type is None
    assert evts[1].place == 'Some Place'

