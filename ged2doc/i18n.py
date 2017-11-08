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

_LOG = logging.getLogger(__name__)

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

    def __init__(self, lang, datefmt, domain="ged2doc"):
        self._lang = lang
        self._datefmt = datefmt
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
                tr_text = self._tr.ugettext(txt)
                _LOG.debug("translation = %r", tr_text)
                if tr_text:
                    return tr_text
        _LOG.debug("return original = %r", text)
        return text
