"""Unit test for name module
"""

from __future__ import absolute_import, division, print_function

from collections import namedtuple

from ged2doc.name import *

# mock for Name class
Name = namedtuple("Name", "given surname maiden")


def test_001_default():

    name = Name(given="Jane", surname="Smith", maiden=None)
    assert name_fmt(name) == "Jane Smith"

    name = Name(given=None, surname="Smith", maiden=None)
    assert name_fmt(name) == "Smith"

    name = Name(given="Jane", surname=None, maiden=None)
    assert name_fmt(name) == "Jane"

    name = Name(given="Jane", surname="Smith", maiden="Sawyer")
    assert name_fmt(name) == "Jane Smith"


def test_002_surname_first():

    flags = FMT_SURNAME_FIRST

    name = Name(given="Jane", surname="Smith", maiden=None)
    assert name_fmt(name, flags) == "Smith Jane"

    name = Name(given=None, surname="Smith", maiden=None)
    assert name_fmt(name, flags) == "Smith"

    name = Name(given="Jane", surname=None, maiden=None)
    assert name_fmt(name, flags) == "Jane"

    name = Name(given="Jane", surname="Smith", maiden="Sawyer")
    assert name_fmt(name, flags) == "Smith Jane"


def test_003_comma():

    flags = FMT_COMMA

    name = Name(given="Jane", surname="Smith", maiden=None)
    assert name_fmt(name, flags) == "Jane Smith"

    name = Name(given=None, surname="Smith", maiden=None)
    assert name_fmt(name, flags) == "Smith"

    name = Name(given="Jane", surname=None, maiden=None)
    assert name_fmt(name, flags) == "Jane"

    name = Name(given="Jane", surname="Smith", maiden="Sawyer")
    assert name_fmt(name, flags) == "Jane Smith"

    flags = FMT_COMMA | FMT_SURNAME_FIRST

    name = Name(given="Jane", surname="Smith", maiden=None)
    assert name_fmt(name, flags) == "Smith, Jane"

    name = Name(given=None, surname="Smith", maiden=None)
    assert name_fmt(name, flags) == "Smith"

    name = Name(given="Jane", surname=None, maiden=None)
    assert name_fmt(name, flags) == "Jane"

    name = Name(given="Jane", surname="Smith", maiden="Sawyer")
    assert name_fmt(name, flags) == "Smith, Jane"


def test_004_maiden():

    flags = FMT_MAIDEN

    name = Name(given="Jane", surname="Smith", maiden=None)
    assert name_fmt(name, flags) == "Jane Smith"

    name = Name(given="Jane", surname="Smith", maiden="Sawyer")
    assert name_fmt(name, flags) == "Jane Smith (Sawyer)"

    flags = FMT_MAIDEN | FMT_SURNAME_FIRST

    name = Name(given="Jane", surname="Smith", maiden="Sawyer")
    assert name_fmt(name, flags) == "Smith (Sawyer) Jane"

    flags = FMT_MAIDEN | FMT_SURNAME_FIRST | FMT_COMMA

    name = Name(given="Jane", surname="Smith", maiden="Sawyer")
    assert name_fmt(name, flags) == "Smith (Sawyer), Jane"


def test_005_maiden_only():

    flags = FMT_MAIDEN_ONLY

    name = Name(given="Jane", surname="Smith", maiden=None)
    assert name_fmt(name, flags) == "Jane Smith"

    name = Name(given="Jane", surname="Smith", maiden="Sawyer")
    assert name_fmt(name, flags) == "Jane Sawyer"

    flags = FMT_MAIDEN_ONLY | FMT_SURNAME_FIRST

    name = Name(given="Jane", surname="Smith", maiden="Sawyer")
    assert name_fmt(name, flags) == "Sawyer Jane"

    flags = FMT_MAIDEN_ONLY | FMT_SURNAME_FIRST | FMT_COMMA

    name = Name(given="Jane", surname="Smith", maiden="Sawyer")
    assert name_fmt(name, flags) == "Sawyer, Jane"


def test_006_capital():

    flags = FMT_MAIDEN | FMT_CAPITAL

    name = Name(given="Jane", surname="Smith", maiden=None)
    assert name_fmt(name, flags) == "Jane SMITH"

    name = Name(given="Jane", surname="Smith", maiden="Sawyer")
    assert name_fmt(name, flags) == "Jane SMITH (SAWYER)"

    flags = FMT_CAPITAL | FMT_MAIDEN | FMT_SURNAME_FIRST

    name = Name(given="Jane", surname="Smith", maiden="Sawyer")
    assert name_fmt(name, flags) == "SMITH (SAWYER) Jane"

    flags = FMT_CAPITAL | FMT_SURNAME_FIRST | FMT_MAIDEN | FMT_COMMA

    name = Name(given="Jane", surname="Smith", maiden="Sawyer")
    assert name_fmt(name, flags) == "SMITH (SAWYER), Jane"

