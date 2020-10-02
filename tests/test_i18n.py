# -*- coding: utf-8 -*-

"""Unit test for utils module
"""

from ged2doc import i18n
from ged4py.date import CalendarDate, DateValue


def test_001_tr_en():

    tr = i18n.I18N('en')
    assert tr.tr("Person List") == "Person List"
    assert tr.tr("CHILD.BORN {child}", "M") == "Born son {child}"
    assert tr.tr("CHILD.BORN {child}", "F") == "Born daughter {child}"
    assert tr.tr("CHILD.BORN {child}") == "Born {child}"
    assert tr.tr("EVENT.BIRT") == "Birth"
    assert tr.tr("Random string $$$") == "Random string $$$"


def test_002_tr_ru():

    tr = i18n.I18N('ru')
    assert tr.tr("Person List") == "Персоналии"
    assert tr.tr("CHILD.BORN {child}", "M") == "Родился сын {child}"
    assert tr.tr("CHILD.BORN {child}", "F") == "Родилась дочь {child}"
    assert tr.tr("CHILD.BORN {child}") == "Родился {child}"
    assert tr.tr("EVENT.BIRT") == "Рождение"
    assert tr.tr("Random string $$$") == "Random string $$$"


def test_011_month_en():
    """Test month name translation, do not care about non-Gregorian
    calendars here.
    """
    tr = i18n.I18N('en')
    assert tr._monthName("JAN") == "Jan"
    assert tr._monthName("jan") == "Jan"
    assert tr._monthName("Jan") == "Jan"
    assert tr._monthName("DEC") == "Dec"
    assert tr._monthName("dec") == "Dec"


def test_011_month_ru():
    """Test month name translation, do not care about non-Gregorian
    calendars here.
    """
    tr = i18n.I18N('ru')
    assert tr._monthName("JAN") == "Янв"
    assert tr._monthName("jan") == "Янв"
    assert tr._monthName("Jan") == "Янв"
    assert tr._monthName("DEC") == "Дек"
    assert tr._monthName("dec") == "Дек"


def test_021_cal_date_en():
    """Test calendar date translations"""

    # year only
    date = CalendarDate.parse("1975")

    # default format (same as YD,M)
    tr = i18n.I18N('en')
    assert tr._tr_cal_date(date) == "1975"
    assert tr._tr_cal_date(CalendarDate.parse("2000B.C.")) == "2000 B.C."

    for fmt in i18n.DATE_FORMATS:
        tr = i18n.I18N('en', fmt)
        assert tr._tr_cal_date(date) == "1975"


def test_022_cal_date_en():
    """Test calendar date translations"""

    # year only
    date = CalendarDate.parse("JAN 1975")

    # default format (same as YD,M)
    tr = i18n.I18N('en')
    assert tr._tr_cal_date(date) == "Jan 1975"
    assert tr._tr_cal_date(CalendarDate.parse("JAN 2000 B.C.")) == "Jan 2000 B.C."

    expect = {'YMD': "1975 Jan",
              'MDY': "Jan 1975",
              'DMY': "Jan 1975",
              'Y-M-D': "1975-Jan",
              'D-M-Y': "Jan-1975",
              'Y/M/D': "1975/01",
              'M/D/Y': "01/1975",
              'Y.M.D': "1975.01",
              'D.M.Y': "01.1975",
              'MD,Y': "Jan 1975"}

    for fmt in i18n.DATE_FORMATS:
        tr = i18n.I18N('en', fmt)
        assert tr._tr_cal_date(date) == expect[fmt]


def test_023_cal_date_en():
    """Test calendar date translations"""

    # year only
    date = CalendarDate.parse("9 JAN 1975")

    # default format (same as YD,M)
    tr = i18n.I18N('en')
    assert tr._tr_cal_date(date) == "Jan 09, 1975"
    assert tr._tr_cal_date(CalendarDate.parse("31 JAN 2000 B.C.")) == "Jan 31, 2000 B.C."

    expect = {'YMD': "1975 Jan 09",
              'MDY': "Jan 09 1975",
              'DMY': "09 Jan 1975",
              'Y-M-D': "1975-Jan-09",
              'D-M-Y': "09-Jan-1975",
              'Y/M/D': "1975/01/09",
              'M/D/Y': "01/09/1975",
              'Y.M.D': "1975.01.09",
              'D.M.Y': "09.01.1975",
              'MD,Y': "Jan 09, 1975"}

    for fmt in i18n.DATE_FORMATS:
        tr = i18n.I18N('en', fmt)
        assert tr._tr_cal_date(date) == expect[fmt]


def test_031_cal_date_ru():
    """Test calendar date translations"""

    # year only
    date = CalendarDate.parse("1975")

    # default format (same as YD,M)
    tr = i18n.I18N('ru')
    assert tr._tr_cal_date(date) == "1975"
    assert tr._tr_cal_date(CalendarDate.parse("2000 B.C.")) == "2000 B.C."

    for fmt in i18n.DATE_FORMATS:
        tr = i18n.I18N('ru', fmt)
        assert tr._tr_cal_date(date) == "1975"


def test_032_cal_date_ru():
    """Test calendar date translations"""

    # year only
    date = CalendarDate.parse("JAN 1975")

    # default format (same as D.M.Y)
    tr = i18n.I18N('ru')
    assert tr._tr_cal_date(date) == "01.1975"
    assert tr._tr_cal_date(CalendarDate.parse("JAN 2000B.C.")) == "01.2000 B.C."

    expect = {'YMD': "1975 Янв",
              'MDY': "Янв 1975",
              'DMY': "Янв 1975",
              'Y-M-D': "1975-Янв",
              'D-M-Y': "Янв-1975",
              'Y/M/D': "1975/01",
              'M/D/Y': "01/1975",
              'Y.M.D': "1975.01",
              'D.M.Y': "01.1975",
              'MD,Y': "Янв 1975"}

    for fmt in i18n.DATE_FORMATS:
        tr = i18n.I18N('ru', fmt)
        assert tr._tr_cal_date(date) == expect[fmt]


def test_033_cal_date_ru():
    """Test calendar date translations"""

    # year only
    date = CalendarDate.parse("9 JAN 1975")

    # default format (same as YD,M)
    tr = i18n.I18N('ru')
    assert tr._tr_cal_date(date) == "09.01.1975"
    assert tr._tr_cal_date(CalendarDate.parse("31 JAN 2000B.C.")) == "31.01.2000 B.C."

    expect = {'YMD': "1975 Янв 09",
              'MDY': "Янв 09 1975",
              'DMY': "09 Янв 1975",
              'Y-M-D': "1975-Янв-09",
              'D-M-Y': "09-Янв-1975",
              'Y/M/D': "1975/01/09",
              'M/D/Y': "01/09/1975",
              'Y.M.D': "1975.01.09",
              'D.M.Y': "09.01.1975",
              'MD,Y': "Янв 09, 1975"}

    for fmt in i18n.DATE_FORMATS:
        tr = i18n.I18N('ru', fmt)
        assert tr._tr_cal_date(date) == expect[fmt]


def test_041_date_en():
    """Test DateValue translations"""

    # year only
    date = DateValue.parse("ABT 1975")

    for fmt in i18n.DATE_FORMATS:
        tr = i18n.I18N('en', fmt)
        assert tr.tr_date(date) == "about 1975"


def test_042_date_ru():
    """Test DateValue translations"""

    # year only
    date = DateValue.parse("ABT 1975")

    for fmt in i18n.DATE_FORMATS:
        tr = i18n.I18N('ru', fmt)
        assert tr.tr_date(date) == "около 1975"
