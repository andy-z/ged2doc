'''Python module for generating EMF.

Only the most trivial features are implemented, stuff that is required by
ged2doc package.
'''

__all__ = ['EMF', 'BackgroundMode']

import abc
import contextlib
import logging
import math
import struct

from .size import Size


_LOG = logging.getLogger(__name__)


# Record types, only few selected that we need
EMR_HEADER = 0x00000001
EMR_POLYLINE = 0x00000004
EMR_SETWINDOWEXTEX = 0x00000009
EMR_SETWINDOWORGEX = 0x0000000A
EMR_SETVIEWPORTEXTEX = 0x0000000B
EMR_SETVIEWPORTORGEX = 0x0000000C
EMR_EOF = 0x0000000E
EMR_SETMAPMODE = 0x00000011
EMR_SETBKMODE = 0x00000012
EMR_SETPOLYFILLMODE = 0x00000013
EMR_SETROP2 = 0x00000014
EMR_SETTEXTALIGN = 0x00000016
EMR_SETTEXTCOLOR = 0x00000018
EMR_MOVETOEX = 0x0000001B
EMR_SETWORLDTRANSFORM = 0x00000023
EMR_MODIFYWORLDTRANSFORM = 0x00000024
EMR_SELECTOBJECT = 0x00000025
EMR_CREATEPEN = 0x00000026
EMR_DELETEOBJECT = 0x00000028
EMR_RECTANGLE = 0x0000002B
EMR_GDICOMMENT = 0x00000046
EMR_LINETO = 0x00000036
EMR_ARCTO = 0x00000037
EMR_POLYDRAW = 0x00000038
EMR_SETMITERLIMIT = 0x0000003A
EMR_BEGINPATH = 0x0000003B
EMR_ENDPATH = 0x0000003C
EMR_CLOSEFIGURE = 0x0000003D
EMR_STROKEPATH = 0x00000040
EMR_EXTCREATEFONTINDIRECTW = 0x00000052
EMR_EXTTEXTOUTW = 0x00000054
EMR_EXTCREATEPEN = 0x0000005F
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


class BackgroundMode:
    TRANSPARENT = 0x0001
    OPAQUE = 0x000


class MapMode:
    MM_TEXT = 0x01
    MM_LOMETRIC = 0x02
    MM_HIMETRIC = 0x03
    MM_LOENGLISH = 0x04
    MM_HIENGLISH = 0x05
    MM_TWIPS = 0x06
    MM_ISOTROPIC = 0x07
    MM_ANISOTROPIC = 0x08


class StockObjects:
    NULL_BRUSH = 0x80000005
    NULL_PEN = 0x80000008
    DEVICE_DEFAULT_FONT = 0x8000000E


class PenStyle:
    PS_COSMETIC = 0x00000000
    PS_ENDCAP_ROUND = 0x00000000
    PS_JOIN_ROUND = 0x00000000
    PS_SOLID = 0x00000000
    PS_DASH = 0x00000001
    PS_DOT = 0x00000002
    PS_DASHDOT = 0x00000003
    PS_DASHDOTDOT = 0x00000004
    PS_NULL = 0x00000005
    PS_INSIDEFRAME = 0x00000006
    PS_USERSTYLE = 0x00000007
    PS_ALTERNATE = 0x00000008
    PS_ENDCAP_SQUARE = 0x00000100
    PS_ENDCAP_FLAT = 0x00000200
    PS_JOIN_BEVEL = 0x00001000
    PS_JOIN_MITER = 0x00002000
    PS_GEOMETRIC = 0x00010000


_pen_styles = {
    "solid": PenStyle.PS_SOLID | PenStyle.PS_GEOMETRIC,
    "dash": PenStyle.PS_DASH | PenStyle.PS_GEOMETRIC,
    "dot": PenStyle.PS_DASH | PenStyle.PS_GEOMETRIC,
    "dashdot": PenStyle.PS_DASHDOT | PenStyle.PS_GEOMETRIC,
    "dashdotdot": PenStyle.PS_DASHDOTDOT | PenStyle.PS_GEOMETRIC,
}


def _pack(*args):
    """Helper method to simplify struct.pack call.

    Accepts a list of tuples, each tuple has a characted format code as first
    element and packed data values as remaining elements. Example:

        _pack(("I", 1, 2, 3), ("H", 4, 5))

    is equivalent to:

        struct.pack("IIIHH", 1, 2, 3, 4, 5)

    Parameters
    ----------
    *args : `tuple`
        Tuple where first item is a string format for `struct.pack` call
        and remaining items are values to to be packed.
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


class EMF:
    """Class for EMF, top-level structure.

    Parameters
    ----------
    width, height : `ged2doc.size.Size`
        Document width and height, accepts anything convertible to
        `ged2doc.size.Size`.
    """
    def __init__(self, width, height):
        self._width = Size(width)
        self._height = Size(height)
        self._records = []  # List of all records added so far
        _LOG.debug("EMF: size = %s x %s (dpi %s x %s)",
                   self._width, self._height, self._width.dpi, self._height.dpi)
        # self._handles = {}

        # self._records += [
        #     GeneralRecord(EMR_SETMAPMODE, ("I", MapMode.MM_TEXT)),
        #     GeneralRecord(EMR_MODIFYWORLDTRANSFORM, ("f", 1., 0., 0., 1., 0., 0.), ("I", 2)),
        #     GeneralRecord(EMR_SETBKMODE, ("I", BackgroundMode.TRANSPARENT)),
        #     GeneralRecord(EMR_SETPOLYFILLMODE, ("I", 2)),
        #     GeneralRecord(EMR_SETTEXTALIGN, ("I", TA_CENTER | TA_BASELINE)),
        #     GeneralRecord(EMR_SETTEXTCOLOR, ("I", 0)),
        #     GeneralRecord(EMR_SETROP2, ("I", 0x000D)),
        # ]

    # def _handle_for(self, what):

    #     handle = self._handles.get(what)
    #     if handle is None:
    #         handle = len(self._handles) + 1
    #         self._handles[what] = handle
    #     return handle

    def data(self):
        """Produce complete EMF structure.

        Returns
        -------
        data : `bytes`
            Byte-string with EMF data.
        """
        records = self._records + [_EOFRecord()]
        n_rec = len(records) + 1
        rec_size = sum(rec.size() for rec in records)
        n_handles = 2
        header = _HeaderRecord(self._width, self._height, n_rec, rec_size, n_handles)
        records.insert(0, header)
        return b"".join(rec.data() for rec in records)

    @contextlib.contextmanager
    def use_pen(self, style, width, color):
        """Context manager which sets pen parameters.

        Parameters
        ----------
        style : `str`
            Pen style.
        width : `ged2doc.size.Size`
            Pen width.
        color : `int`
            Pen color.
        """

        pen_handle = 1  # self._handle_for("pen")

        style = _pen_styles.get(style, style)
        width = int(math.ceil(width.pxf))  # math.ceil returns float in Python2
        # rec = GeneralRecord(EMR_CREATEPEN, ("I", pen_handle, style, width, width, color))
        rec = GeneralRecord(EMR_EXTCREATEPEN, ("I", pen_handle, 0, 0, 0, 0, style, width, 0, color, 6, 0, 0))
        self._records.append(rec)
        _LOG.debug("EMF: create_pen: id=%s style=%s width=%s color=%s",
                   pen_handle, style, width, color)
        rec = GeneralRecord(EMR_SELECTOBJECT, ("I", pen_handle))
        self._records.append(rec)
        yield pen_handle

        rec = GeneralRecord(EMR_SELECTOBJECT, ("I", StockObjects.NULL_PEN))
        self._records.append(rec)
        rec = GeneralRecord(EMR_DELETEOBJECT, ("I", pen_handle))
        self._records.append(rec)

    @contextlib.contextmanager
    def use_font(self, size, fontname="Times New Roman"):
        """Context manager which sets font parameters.

        Parameters
        ----------
        size : `ged2doc.size.Size`
            Font size.
        fontname : `str`
            Font family name.
        """
        font_handle = 1  # self._handle_for("font")

        height = - size.px  # negative to enable matching
        width = 0
        weight = 400  # normal

        facename = _strencode(fontname, 64)
        # fullname = _strencode("", 128)
        # style = _strencode("", 64)
        _LOG.debug("EMF: create_font: facename=%r", facename)

        rec = GeneralRecord(
            EMR_EXTCREATEFONTINDIRECTW,
            ("I", font_handle),
            # LogFont
            ("i", height, width),
            ("i", 0, 0, weight),
            ("B", 0, 0, 0, 1),  # ital/underl/strike/charset
            ("B", 0, 0, 0, 0),  # OutPrec/ClipPrec/Qual/Pitch
            ("64s", facename),
            # ("128s", fullname),
            # ("64s", style),
            # ("I", 0, 0, 0, 0, 0, 0),  # version/stylesize/match/resv/vendor/culture
            # ("B", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),  # panose
            # ("H", 0),  # padding
        )
        self._records.append(rec)
        _LOG.debug("EMF: create_font: rec.size=%s", rec.size())
        rec = GeneralRecord(EMR_SELECTOBJECT, ("I", font_handle))
        self._records.append(rec)

        yield font_handle

        rec = GeneralRecord(EMR_SELECTOBJECT, ("I", StockObjects.DEVICE_DEFAULT_FONT))
        self._records.append(rec)
        rec = GeneralRecord(EMR_DELETEOBJECT, ("I", font_handle))
        self._records.append(rec)

    def set_bkmode(self, mode):
        """Set background mode.

        Parameters
        ----------
        mode : `int`
            Mode, one of `BackgroundMode` constants.
        """
        rec = GeneralRecord(EMR_SETBKMODE, ("I", mode))
        self._records.append(rec)

    def polyline(self, points):
        """Draw polyline.

        Parameters
        ----------
        points : `list` [ `tuple` ]
            List of 2-tuples with (x, y) coordinates, each coordinate is
            `ged2doc.size.Size`.
        """
        points = [(x.px, y.px) for x, y in points]
        left = min(x for x, y in points)
        right = max(x for x, y in points)
        top = min(y for x, y in points)
        bottom = max(y for x, y in points)

        coords = []
        for x, y in points:
            coords += [x, y]
        rec = GeneralRecord(
            EMR_POLYLINE,
            ("i", left, top, right, bottom),
            ("I", len(points)),
            ("i",) + tuple(coords)
        )
        self._records.append(rec)

    def rectangle(self, left, top, right, bottom):
        """Draw rectangle.

        Parameters
        ----------
        left, top, right, bottom : `ged2doc.size.Size`
            Rectangle coordinates.
        """
        left, top, right, bottom = [pos.px for pos in (left, top, right, bottom)]
        _LOG.debug("EMF: rect: left=%s top=%s right=%s bottom=%s", left, top, right, bottom)
        # rec = GeneralRecord(EMR_SELECTOBJECT, ("I", StockObjects.NULL_BRUSH))
        # self._records.append(rec)
        # rec = GeneralRecord(EMR_RECTANGLE, ("i",) + rect)
        # self._records.append(rec)

        self._records.append(GeneralRecord(EMR_BEGINPATH))
        self._records.append(GeneralRecord(EMR_MOVETOEX, ("I", left, top)))
        self._records.append(GeneralRecord(EMR_LINETO, ("I", right, top)))
        self._records.append(GeneralRecord(EMR_LINETO, ("I", right, bottom)))
        self._records.append(GeneralRecord(EMR_LINETO, ("I", left, bottom)))
        self._records.append(GeneralRecord(EMR_CLOSEFIGURE))
        self._records.append(GeneralRecord(EMR_ENDPATH))
        self._records.append(GeneralRecord(EMR_STROKEPATH, ("i", 0, 0, -1, -1)))

    def text_align(self, align_mode="c"):
        """Set text alignment for next text drawing operation

        Parameters
        ----------
        align_mode : `str`, optional
            One of "l", "c", "r".
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
        """Set text color for next text drawing operation

        Parameters
        ----------
        color : `int`
        """
        _LOG.debug("EMF: text_color: color=%o", color)
        rec = GeneralRecord(EMR_SETTEXTCOLOR, ("I", color))
        self._records.append(rec)

    def text(self, x, y, text):
        """Draw text.

        Parameters
        ----------
        x, y : `ged2doc.size.Size`
            Text coordinates.
        text : `str`
            Text to draw.
        """
        pos = tuple(pos.px for pos in (x, y))
        iGraphicsMode = GM_COMPATIBLE
        exScale, eyScale = 1., 1.

        nChars = len(text)  # number of characters, not bytes
        # encode as UTF16-LE and pad to 4-byte
        txt_bytes = text.encode("utf_16_le", "replace")
        if len(txt_bytes) % 4 != 0:
            txt_bytes += b"\0\0"

        _LOG.debug("EMF: text: pos=%s, txt_bytes=%r", pos, txt_bytes)

        offString = 76
        offDx = 0
        options = 0

        rec = GeneralRecord(
            EMR_EXTTEXTOUTW,
            ("i", 0, 0, -1, -1),  # bounds
            ("I", iGraphicsMode),
            ("f", exScale, eyScale),
            ("i", pos[0], pos[1]),  # x, y
            ("I", nChars),
            ("I", offString),
            ("I", options),
            ("i", 0, 0, -1, -1),  # Rectangle
            ("I", offDx),
            ("{}s".format(len(txt_bytes)), txt_bytes),
            )
        self._records.append(rec)


class Record(metaclass=abc.ABCMeta):
    """Base class for all EMF records.
    """

    @abc.abstractmethod
    def size(self):
        """Return size of this record in bytes.

        Returns
        -------
        size : `int`
            Record size, always multiple of 4.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def data(self):
        """Produce record contents as byte string.

        Returns
        -------
        data : `bytes`
            Byte-string with record data.
        """
        raise NotImplementedError()


class GeneralRecord(Record):
    """Base class for all EMF records.

    Parameters
    ----------
    type : `int`
        Records type, one of EMR_* constants.
    *pack_args : `tuple`
        Data to pack into record, same format as for `_pack` method.
    """
    def __init__(self, type, *pack_args):
        if pack_args:
            rec = _pack(*pack_args)
            self._size = len(rec) + 8
            self._rec = struct.pack("II", type, self._size) + rec
        else:
            self._size = 8
            self._rec = struct.pack("II", type, self._size)

    def size(self):
        # docstring inherited from base class
        return self._size

    def data(self):
        # docstring inherited from base class
        return self._rec


class _HeaderRecord(Record):
    """EMF header record.

    Clients don't need to add it explicitly, it is for internal use.

    Parameters
    ----------
    width, height : `ged2doc.size.Size`
        Size of the image.
    n_rec : `int`
        Number of records in file, not including header.
    rec_size : `int`
        Size of all of records in file, not including header.
    """
    def __init__(self, width, height, n_rec, rec_size, n_handles):
        self._type = EMR_HEADER
        self._width = width
        self._height = height
        self._n_rec = n_rec
        self._rec_size = rec_size
        self._n_handles = n_handles

    def data(self):
        # docstring inherited from base class
        boundsX = int(math.ceil(self._width.pxf))
        boundsY = int(math.ceil(self._height.pxf))
        sizeXmm = int(math.ceil(self._width.mm))
        sizeYmm = int(math.ceil(self._height.mm))
        frameX = sizeXmm * 100
        frameY = sizeYmm * 100
        version = 0x00010000
        emf_size = self._rec_size + self.size()
        nDescription, offDescription = 7, 108
        nPalEntries = 0
        cbPixelFormat, offPixelFormat = 0, 0
        bOpenGL = 0
        MicrometersX = sizeXmm * 1000
        MicrometersY = sizeYmm * 1000
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
            ("I", cbPixelFormat, offPixelFormat, bOpenGL),
            ("I", MicrometersX, MicrometersY),
            ("16s", b"\0d\0u\0m\0b\0e\0m\0f\0\0"),
        )

    def size(self):
        # docstring inherited from base class
        size = 108 + 16
        return size


class _EOFRecord(Record):
    """EMF record for EOF.

    Clients don't need to add it explicitly, it is for internal use.
    """

    def __init__(self):
        self._type = EMR_EOF

    def data(self):
        # docstring inherited from base class
        size = self.size()
        return _pack(
            ("I", self._type, size, 0, 16, size)
        )

    def size(self):
        # docstring inherited from base class
        return 20


def _parse():
    """Simple command line utility to parse/dump EMF.

    .. note::

        This method is for testing only, not a part of regular interface.
    """
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=argparse.FileType("rb"))
    parser.add_argument("-v", dest="verbose", action="store_true", default=False,
                        help="verbose output")
    args = parser.parse_args()

    data = args.file.read(8)
    while data:

        rectype, size = struct.unpack("II", data)
        for name, value in globals().items():
            if name.startswith("EMR_") and value == rectype:
                rectype = name
        print("{} size={}".format(rectype, size))

        # read remaining data
        data += args.file.read(size - 8)
        if args.verbose:
            offset = 0
            while data:
                line, data = data[:16], data[16:]
                fline = "    {:03d}:".format(offset)
                bline = list(line)
                bline += [None] * (16 - len(bline))

                for i, b in enumerate(bline):
                    if i % 4 == 0:
                        fline += "  "
                    if b is not None:
                        fline += " {:02X}".format(b)
                    else:
                        fline += "   "

                for i, b in enumerate(bline):
                    if i % 4 == 0:
                        fline += "  "
                    if b is None:
                        fline += "  "
                    elif 32 <= b < 127:
                        fline += " {}".format(chr(b))
                    else:
                        fline += " ."

                for i in (0, 4, 8, 12):
                    if i < len(line):
                        v, = struct.unpack("I", line[i:i+4])
                        fline += " {:010d}".format(v)

                print(fline)
                offset += 16

        # next record, if any
        data = args.file.read(8)


if __name__ == "__main__":
    _parse()
