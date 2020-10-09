"""Unit test for name module
"""

from collections import namedtuple

from ged2doc.name import name_fmt, NameFormat


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

    flags = NameFormat.SURNAME_FIRST

    name = Name(given="Jane", surname="Smith", maiden=None)
    assert name_fmt(name, flags) == "Smith Jane"

    name = Name(given=None, surname="Smith", maiden=None)
    assert name_fmt(name, flags) == "Smith"

    name = Name(given="Jane", surname=None, maiden=None)
    assert name_fmt(name, flags) == "Jane"

    name = Name(given="Jane", surname="Smith", maiden="Sawyer")
    assert name_fmt(name, flags) == "Smith Jane"


def test_003_comma():

    flags = NameFormat.COMMA

    name = Name(given="Jane", surname="Smith", maiden=None)
    assert name_fmt(name, flags) == "Jane Smith"

    name = Name(given=None, surname="Smith", maiden=None)
    assert name_fmt(name, flags) == "Smith"

    name = Name(given="Jane", surname=None, maiden=None)
    assert name_fmt(name, flags) == "Jane"

    name = Name(given="Jane", surname="Smith", maiden="Sawyer")
    assert name_fmt(name, flags) == "Jane Smith"

    flags = NameFormat.COMMA | NameFormat.SURNAME_FIRST

    name = Name(given="Jane", surname="Smith", maiden=None)
    assert name_fmt(name, flags) == "Smith, Jane"

    name = Name(given=None, surname="Smith", maiden=None)
    assert name_fmt(name, flags) == "Smith"

    name = Name(given="Jane", surname=None, maiden=None)
    assert name_fmt(name, flags) == "Jane"

    name = Name(given="Jane", surname="Smith", maiden="Sawyer")
    assert name_fmt(name, flags) == "Smith, Jane"


def test_004_maiden():

    flags = NameFormat.MAIDEN

    name = Name(given="Jane", surname="Smith", maiden=None)
    assert name_fmt(name, flags) == "Jane Smith"

    name = Name(given="Jane", surname="Smith", maiden="Sawyer")
    assert name_fmt(name, flags) == "Jane Smith (Sawyer)"

    flags = NameFormat.MAIDEN | NameFormat.SURNAME_FIRST

    name = Name(given="Jane", surname="Smith", maiden="Sawyer")
    assert name_fmt(name, flags) == "Smith (Sawyer) Jane"

    flags = NameFormat.MAIDEN | NameFormat.SURNAME_FIRST | NameFormat.COMMA

    name = Name(given="Jane", surname="Smith", maiden="Sawyer")
    assert name_fmt(name, flags) == "Smith (Sawyer), Jane"


def test_005_maiden_only():

    flags = NameFormat.MAIDEN_ONLY

    name = Name(given="Jane", surname="Smith", maiden=None)
    assert name_fmt(name, flags) == "Jane Smith"

    name = Name(given="Jane", surname="Smith", maiden="Sawyer")
    assert name_fmt(name, flags) == "Jane Sawyer"

    flags = NameFormat.MAIDEN_ONLY | NameFormat.SURNAME_FIRST

    name = Name(given="Jane", surname="Smith", maiden="Sawyer")
    assert name_fmt(name, flags) == "Sawyer Jane"

    flags = NameFormat.MAIDEN_ONLY | NameFormat.SURNAME_FIRST | NameFormat.COMMA

    name = Name(given="Jane", surname="Smith", maiden="Sawyer")
    assert name_fmt(name, flags) == "Sawyer, Jane"


def test_006_capital():

    flags = NameFormat.MAIDEN | NameFormat.CAPITAL

    name = Name(given="Jane", surname="Smith", maiden=None)
    assert name_fmt(name, flags) == "Jane SMITH"

    name = Name(given="Jane", surname="Smith", maiden="Sawyer")
    assert name_fmt(name, flags) == "Jane SMITH (SAWYER)"

    flags = NameFormat.CAPITAL | NameFormat.MAIDEN | NameFormat.SURNAME_FIRST

    name = Name(given="Jane", surname="Smith", maiden="Sawyer")
    assert name_fmt(name, flags) == "SMITH (SAWYER) Jane"

    flags = NameFormat.CAPITAL | NameFormat.SURNAME_FIRST | NameFormat.MAIDEN | NameFormat.COMMA

    name = Name(given="Jane", surname="Smith", maiden="Sawyer")
    assert name_fmt(name, flags) == "SMITH (SAWYER), Jane"
