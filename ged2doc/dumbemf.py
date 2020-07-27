'''Python module for generating EMF.

Only the most trivial features are implemented, stuff that is required by
ged2doc package.
'''

from __future__ import absolute_import, division, print_function

__all__ = ['EMF']

import logging
import math
import struct

from .size import Size


_LOG = logging.getLogger(__name__)


# Record types, only few selected that we need
EMR_HEADER = 0x00000001
EMR_EOF = 0x0000000E
EMR_SETTEXTALIGN = 0x00000016
EMR_SETTEXTCOLOR = 0x00000018
EMR_SELECTOBJECT = 0x00000025
EMR_CREATEPEN = 0x00000026
EMR_RECTANGLE = 0x0000002B
EMR_EXTCREATEFONTINDIRECTW = 0x00000052
EMR_EXTTEXTOUTW = 0x00000054
EMR_SMALLTEXTOUT = 0x0000006C
EMR_SETTEXTJUSTIFICATION = 0x00000078

# text alignment
TA_LEFT = 0x0000
TA_TOP = 0x0000
TA_NOUPDATECP = 0x0000
TA_UPDATECP = 0x0001
TA_RIGHT = 0x0002
TA_CENTER = 0x0006
TA_BOTTOM = 0x0008
TA_BASELINE = 0x0018
TA_RTLREADING = 0x0100

GM_COMPATIBLE = 0x00000001
GM_ADVANCED = 0x00000002

# ExtTextOutOptions
ETO_OPAQUE = 0x00000002
ETO_CLIPPED = 0x00000004
ETO_GLYPH_INDEX = 0x00000010
ETO_RTLREADING = 0x00000080
ETO_NO_RECT = 0x00000100
ETO_SMALL_CHARS = 0x00000200
ETO_NUMERICSLOCAL = 0x00000400
ETO_NUMERICSLATIN = 0x00000800
ETO_IGNORELANGUAGE = 0x00001000
ETO_PDY = 0x00002000
ETO_REVERSE_INDEX_MAP = 0x00010000


_pen_styles = {
    "solid": 0x0,
    "dash": 0x1,
    "dot": 0x2,
    "dashdot": 0x3,
    "dashdotdot": 0x4,
}


def _pack(*args):
    """Helper method to simplify struct.pack call.

    Accepts a list of tuples, each tuple has a characted format code as first
    element and packed data values as remaining elements. Example:

        _pack(("I", 1, 2, 3), ("H", 4, 5))

    is equivalent to:

        struct.pack("IIIHH", 1, 2, 3, 4, 5)
    """
    fmt = "<"
    values = ()
    for tup in args:
        tval = tup[1:]
        fmt += tup[0] * len(tval)
        values += tval
    _LOG.debug("_pack: fmt=%s", fmt)
    return struct.pack(fmt, *values)


def _strencode(str, size):
    encoded = str[:size//2].encode("utf_16_le", "strict")
    encoded += b"\0" * (size - len(encoded))
    return encoded


class EMF(object):
    """Class for EMF, top-level structure.

    :param Size width: Document width, int for pixels or string.
    :param Size height: Document height, int for pixels or string.
    """
    def __init__(self, width, height):
        self._width = Size(width)
        self._height = Size(height)
        self._records = []  # List of all records added so far
        self._nhandles = 0  # Counter for handles
        _LOG.debug("EMF: size = %s x %s (dpi %s x %s)",
                   self._width, self._height, self._width.dpi, self._height.dpi)

    def data(self):
        """Produce complete EMF structure.

        :return: Byte-string with EMF data.
        """

        records = self._records + [_EOFRecord()]
        n_rec = len(records)
        rec_size = sum(rec.size() for rec in records)
        header = _HeaderRecord(self._width, self._height, n_rec, rec_size, self._nhandles)
        records.insert(0, header)
        return b"".join(rec.data() for rec in records)

    def create_pen(self, style, width, color):
        style = _pen_styles.get(style, style)
        width = int(math.ceil(width.pxf))  # math.ceil returns float in Python2
        self._nhandles += 1
        index = self._nhandles  # 1-based
        rec = GeneralRecord(EMR_CREATEPEN, ("I", index, style, width, width, color))
        self._records.append(rec)
        _LOG.debug("EMF: create_pen: id=%s style=%s width=%s color=%s",
                   index, style, width, color)
        return index

    def create_font(self, size, fontname="Times New Roman"):

        self._nhandles += 1
        ihFonts = self._nhandles  # 1-based

        height = - size.px  # negative to enable matching
        width = 0
        weight = 400  # normal

        facename = _strencode(fontname, 64)
        fullname = _strencode("", 128)
        style = _strencode("", 64)
        _LOG.debug("EMF: create_font: facename=%r", facename)

        rec = GeneralRecord(
            EMR_EXTCREATEFONTINDIRECTW,
            ("I", ihFonts),
            # LogFont
            ("i", height, width),
            ("i", 0, 0, weight),
            ("B", 0, 0, 0, 0),  # ital/underl/strike/charset
            ("B", 0, 0, 0, 0),  # OutPrec/ClipPrec/Qual/Pitch
            ("64s", facename),
            ("128s", fullname),
            ("64s", style),
            ("I", 0, 0, 0, 0, 0, 0),  # version/stylesize/match/resv/vendor/culture
            ("B", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),  # panose
            ("H", 0),  # padding
        )
        self._records.append(rec)
        _LOG.debug("EMF: create_font: rec.size=%s", rec.size())

        return ihFonts

    def rectangle(self, left, top, right, bottom, pen):
        rect = tuple(pos.px for pos in (left, top, right, bottom))
        _LOG.debug("EMF: rect: pen=%s left=%s top=%s right=%s bottom=%s", pen, *rect)
        rec = GeneralRecord(EMR_SELECTOBJECT, ("I", pen))
        self._records.append(rec)
        rec = GeneralRecord(EMR_RECTANGLE, ("i",) + rect)
        self._records.append(rec)

    def text_align(self, align_mode="c"):
        """Set text alignment for next text drawing operation

        :param str align_mode: one of "l", "c", "r"
        """
        if align_mode == "l":
            align_mode = TA_LEFT
        elif align_mode == "r":
            align_mode = TA_RIGHT
        elif align_mode == "c":
            align_mode = TA_CENTER
        align_mode |= TA_BASELINE
        _LOG.debug("EMF: text_align: align=%x", align_mode)
        rec = GeneralRecord(EMR_SETTEXTALIGN, ("I", align_mode))
        self._records.append(rec)

    def text_color(self, color):
        _LOG.debug("EMF: text_color: color=%o", color)
        rec = GeneralRecord(EMR_SETTEXTCOLOR, ("I", color))
        self._records.append(rec)

    def text(self, x, y, text, font):

        rec = GeneralRecord(EMR_SELECTOBJECT, ("I", font))
        self._records.append(rec)

        pos = tuple(pos.px for pos in (x, y))
        cChars = len(text)  # number of characters, not bytes
        fuOptions = ETO_NO_RECT
        iGraphicsMode = GM_COMPATIBLE
        exScale, eyScale = 1., 1.

        # encode as UTF16-LE and pad to 4-byte
        txt_bytes = text.encode("utf_16_le", "replace")
        if len(txt_bytes) % 4 != 0:
            txt_bytes += b"\0\0"

        _LOG.debug("EMF: text: pos=%s, txt_bytes=%r", pos, txt_bytes)

        rec = GeneralRecord(
            EMR_SMALLTEXTOUT,
            ("i", pos[0], pos[1]),  # x, y
            ("I", cChars),
            ("I", fuOptions),
            ("I", iGraphicsMode),
            ("f", exScale, eyScale),
            ("{}s".format(len(txt_bytes)), txt_bytes)
            )
        self._records.append(rec)


class Record(object):
    """Base class for all EMF records.
    """

    def __init__(self):
        pass

    def size(self):
        """Return size of this record in bytes.

        :return: Record size, always multiple of 4.
        """
        raise NotImplementedError()

    def data(self):
        """Produce record contents as byte string.

        :return: Byte-string with record data.
        """
        raise NotImplementedError()


class GeneralRecord(Record):
    """Base class for all EMF records.
    """

    def __init__(self, type, *pack_args):
        rec = _pack(*pack_args)
        self._size = len(rec) + 8
        self._rec = struct.pack("II", type, self._size) + rec

    def size(self):
        return self._size

    def data(self):
        return self._rec


class _HeaderRecord(Record):
    """EMF header record.

    Clients don't need to add it explicitly, it is for internal use.

    :param Size width, height: size of the image
    :param int n_rec: Number of records in file, not including header
    :param int rec_size: Size of all of records in file, not including header
    """

    def __init__(self, width, height, n_rec, rec_size, n_handles):
        self._type = EMR_HEADER
        self._width = width
        self._height = height
        self._n_rec = n_rec
        self._rec_size = rec_size
        self._n_handles = n_handles

    def data(self):
        boundsX = int(math.ceil(self._width.pxf))
        boundsY = int(math.ceil(self._height.pxf))
        frameX = int(math.ceil(self._width.mm * 100))
        frameY = int(math.ceil(self._height.mm * 100))
        sizeXmm = int(math.ceil(self._width.mm))
        sizeYmm = int(math.ceil(self._height.mm))
        version = 0x00010000
        emf_size = self._rec_size + self.size()
        nDescription, offDescription = 0, 0
        nPalEntries = 0
        _LOG.debug("EMF: header: bounds = %s x %s; frame = %s x %s; size_mm = %s x %s",
                   boundsX, boundsY, frameX, frameY, sizeXmm, sizeYmm)
        return _pack(
            ("I", self._type, self.size()),
            ("I", 0, 0, boundsX, boundsY),
            ("I", 0, 0, frameX, frameY),
            ("c", b" ", b"E", b"M", b"F"),
            ("I", version, emf_size, self._n_rec),
            ("H", self._n_handles, 0),
            ("I", nDescription, offDescription, nPalEntries),
            ("I", boundsX, boundsY),
            ("I", sizeXmm, sizeYmm),
        )

    def size(self):
        size = 88
        return size


class _EOFRecord(Record):
    """EMF record for EOF.

    Clients don't need to add it explicitly, it is for internal use.
    """

    def __init__(self):
        self._type = EMR_EOF

    def data(self):
        size = self.size()
        return _pack(
            ("I", self._type, size, 0, 0, size)
        )

    def size(self):
        return 20
