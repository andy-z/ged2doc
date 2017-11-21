'''Python module responsible for internationalization of ged2doc.

It covers all aspects that are language- or locale-dependent. In particular
it does these things:

  - translates short string messages from application language into output
    language
  - translates dates into printable format according to locale preferences

Note that we do not use system locale, instead we expect client to provide
small set of configuration options such as output language and date format.
'''

from __future__ import absolute_import, division, print_function

import gettext
import logging
import pkg_resources
import string

from ged4py.detail.date import CalendarDate

_LOG = logging.getLogger(__name__)

# acceptable date formats
DATE_FORMATS = [
    'YMD', 'MDY', 'DMY',  # space separated with month name (2017 Oct 12)
    'Y-M-D', 'D-M-Y',  # dash-separated with month name (2017-Oct-12; 2017-Oct)
    'Y/M/D', 'M/D/Y',  # slash-separated, month number (2017/10/12, 10/2017)
    'Y.M.D', 'D.M.Y',  # dot-separated, month number (12.10.2017, 10.2017)
    'MD,Y',  # comma after day, month name (Oct 12, 2017; Oct 2017)
    ]

# maps language name to its default date format
DEFAULT_DATE_FORMAT = {
    "en": "MD,Y",
    "ru": "D.M.Y"
    }

# this is no-op function, only used to mark translatable strings,
# to extract all strings run "pygettext -k TR ..."
TR = lambda x: x  # NOQA

# These are extra strings that do not appear in the source as they are
# constructed dynamically. List all of them here so that pygettext could
# generate them
_extra_tr = [
    TR("EVENT.BIRT"),
    TR("EVENT.CHR"),
    TR("EVENT.DEAT"),
    TR("EVENT.BURI"),
    TR("EVENT.CREM"),
    TR("EVENT.ADOP"),
    TR("EVENT.BAPM"),
    TR("EVENT.BARM"),
    TR("EVENT.BASM"),
    TR("EVENT.BLES"),
    TR("EVENT.CHRA"),
    TR("EVENT.CONF"),
    TR("EVENT.FCOM"),
    TR("EVENT.ORDN"),
    TR("EVENT.NATU"),
    TR("EVENT.EMIG"),
    TR("EVENT.IMMI"),
    TR("EVENT.CENS"),
    TR("EVENT.PROB"),
    TR("EVENT.WILL"),
    TR("EVENT.GRAD"),
    TR("EVENT.RETI"),
    TR("EVENT.EVEN"),

    TR("FAMEVT.ANUL"),
    TR("FAMEVT.CENS"),
    TR("FAMEVT.DIV"),
    TR("FAMEVT.DIVF"),
    TR("FAMEVT.ENGA"),
    TR("FAMEVT.MARB"),
    TR("FAMEVT.MARC"),
    TR("FAMEVT.MARR"),
    TR("FAMEVT.MARL"),
    TR("FAMEVT.MARS"),
    TR("FAMEVT.RESI"),
    TR("FAMEVT.EVEN"),

    TR("ATTR.CAST"),
    TR("ATTR.DSCR"),
    TR("ATTR.EDUC"),
    TR("ATTR.IDNO"),
    TR("ATTR.NATI"),
    TR("ATTR.NCHI"),
    TR("ATTR.NMR"),
    TR("ATTR.OCCU"),
    TR("ATTR.PROP"),
    TR("ATTR.RELI"),
    TR("ATTR.RESI"),
    TR("ATTR.SSN"),
    TR("ATTR.TITL"),
    TR("ATTR.FACT"),

    TR("DATE_VALUE.FROM $date1 TO $date2"),
    TR("DATE_VALUE.FROM $date"),
    TR("DATE_VALUE.TO $date"),
    TR("DATE_VALUE.BETWEEN $date1 AND $date2"),
    TR("DATE_VALUE.BEFORE $date"),
    TR("DATE_VALUE.AFTER $date"),
    TR("DATE_VALUE.ABOUT $date"),
    TR("DATE_VALUE.CALCULATED $date"),
    TR("DATE_VALUE.ESTIMATED $date"),
    TR("DATE_VALUE.INTERPRETED $date ($phrase)"),
    TR("DATE_VALUE.($phrase)"),
    TR("DATE_VALUE.$date"),

    TR("MONTH.JAN"),
    TR("MONTH.FEB"),
    TR("MONTH.MAR"),
    TR("MONTH.APR"),
    TR("MONTH.MAY"),
    TR("MONTH.JUN"),
    TR("MONTH.JUL"),
    TR("MONTH.AUG"),
    TR("MONTH.SEP"),
    TR("MONTH.OCT"),
    TR("MONTH.NOV"),
    TR("MONTH.DEC"),
    TR("MONTH_HEBR.TSH"),
    TR("MONTH_HEBR.CSH"),
    TR("MONTH_HEBR.KSL"),
    TR("MONTH_HEBR.TVT"),
    TR("MONTH_HEBR.SHV"),
    TR("MONTH_HEBR.ADR"),
    TR("MONTH_HEBR.ADS"),
    TR("MONTH_HEBR.NSN"),
    TR("MONTH_HEBR.IYR"),
    TR("MONTH_HEBR.SVN"),
    TR("MONTH_HEBR.TMZ"),
    TR("MONTH_HEBR.AAV"),
    TR("MONTH_HEBR.ELL"),
    TR("MONTH_FRE.VEND"),
    TR("MONTH_FRE.BRUM"),
    TR("MONTH_FRE.FRIM"),
    TR("MONTH_FRE.NIVO"),
    TR("MONTH_FRE.PLUV"),
    TR("MONTH_FRE.VENT"),
    TR("MONTH_FRE.GERM"),
    TR("MONTH_FRE.FLOR"),
    TR("MONTH_FRE.PRAI"),
    TR("MONTH_FRE.MESS"),
    TR("MONTH_FRE.THER"),
    TR("MONTH_FRE.FRUC"),
    TR("MONTH_FRE.COMP"),
    ]


class _NullFallback(object):
    """Special fallback class for gettext which returns None for missing
    translations.
    """
    def gettext(self, message):
        return None

    def ugettext(self, message):
        return None


class I18N(object):
    """Class with methods responsible for various aspects of translations.

    :param str lang: Output language such as "en", "ru".
    :param str datefmt: Printable date format.
    :param domain: gettext domain (message file name)
    """

    def __init__(self, lang, datefmt=None, domain="ged2doc"):
        self._lang = lang
        self._datefmt = datefmt
        if self._datefmt is None:
            self._datefmt = DEFAULT_DATE_FORMAT.get(lang, "YMD")
        self._tr = None

        # open MO file
        path = "data/lang/{}/{}.mo".format(lang, domain)
        try:
            _LOG.debug("Opening translations file %r", path)
            mofile = pkg_resources.resource_stream(__name__, path)
            _LOG.debug("mofile = %r", mofile)
            self._tr = gettext.GNUTranslations(mofile)
            self._tr.add_fallback(_NullFallback())
            _LOG.debug("self._tr = %r", self._tr)
        except IOError:
            _LOG.warn("Cannot locate translations for language %r", lang)

    def tr(self, text, gender=None):
        """Translates given text , takes into account gender.

        :param str text: Text to translate
        :param str gender: One of 'F', 'M', 'U', or None.
        """
        _LOG.debug("text = %r", text)
        if self._tr:
            variants = [text]
            if gender:
                variants = [text + "#" + gender] + variants
            _LOG.debug("variants = %r", variants)
            for txt in variants:
                _LOG.debug("variant = %r", txt)
                if hasattr(self._tr, "ugettext"):
                    tr_text = self._tr.ugettext(txt)
                else:
                    tr_text = self._tr.gettext(txt)
                _LOG.debug("translation = %r", tr_text)
                if tr_text:
                    return tr_text
        _LOG.debug("return original = %r", text)
        return text

    def tr_date(self, date):
        """Produce language-specific date representation.

        :param date: Instance of :py:class:`ged4py.detail.date.DateValue`.
        :return: String representation of a date.
        """
        tmpl = string.Template(self.tr("DATE_VALUE." + date.template))
        kw = {}
        for key, val in date.kw.items():
            if isinstance(val, CalendarDate):
                # localized date
                kw[key] = self._tr_cal_date(val)
            else:
                # anything else assume to be a text
                kw[key] = val
        return tmpl.substitute(kw)

    def _tr_cal_date(self, date):
        """Produce language-specific calendar date representation.

        Uses date format provided in constructor, month name is translated
        into a destination language.

        :param date: Instance of :py:class:`ged4py.detail.date.CalendarDate`.
        :return: String representation of a date.
        """
        items = []
        for code in self._datefmt:
            if code == 'Y':
                if date.year is not None:
                    items += [date.year]
            elif code == 'M':
                if '/' in self._datefmt or '.' in self._datefmt:
                    month = date.month_num
                    if month is not None:
                        month = "{:02d}".format(month)
                else:
                    month = self._monthName(date.month)
                if month is not None:
                    items += [month]
            elif code == 'D':
                day = date.day
                if day is not None and ',' in self._datefmt:
                    items += [str("{:02d},".format(day))]
                elif day is not None:
                    items += ["{:02d}".format(day)]
        if '/' in self._datefmt:
            sep = '/'
        elif '.' in self._datefmt:
            sep = '.'
        elif '-' in self._datefmt:
            sep = '-'
        else:
            sep = ' '
        return sep.join(items)

    def _monthName(self, month):
        """Returns translation of a month name.

        For a given GEDCOM month name return translated month name.

        :param str month: Month name in GEDCOM format.
        :return: Name of this month in destination language
        """
        if month is not None:
            month = self.tr("MONTH." + month.upper())
        return month
