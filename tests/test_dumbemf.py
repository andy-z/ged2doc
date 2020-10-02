"""Unit test for dumbemf module
"""

import logging
import pytest

from ged2doc.dumbemf import EMF
from ged2doc.size import Size


logging.basicConfig(level=logging.DEBUG)

_dpi = 300.
_size = Size("5in", _dpi), Size("3in", _dpi)

_header_bytes = 124
_EOF_bytes = 5 * 4
_use_pen_bytes = 56 + 12 + 12 + 12  # EXTCREATEPEN + SELECTOBJECT + SELECTOBJECT + DELETEOBJECT
_use_font_bytes = 104 + 12 + 12 + 12  # EXTCREATEFONTINDIRECTW + SELECTOBJECT + SELECTOBJECT + DELETEOBJECT
_select_object_bytes = 3 * 4
_rect_bytes = 112
_text_align_bytes = 3 * 4
_text_color_bytes = 3 * 4


def _text_bytes(text):
    size = 19 * 4
    size += len(text) * 2
    if size % 4 != 0:
        size += 2
    return size


def _polyline_bytes(n_points):
    size = 7 * 4
    size += n_points * 2 * 4
    return size


def test_001_empty():
    "Test for empty EMF, with only header and EOF"

    emf = EMF(*_size)
    data = emf.data()

    assert isinstance(data, type(b""))
    assert len(data) == _header_bytes + _EOF_bytes


def test_use_pen():

    emf = EMF(*_size)

    with emf.use_pen("solid", Size("1pt", _dpi), 0) as pen:
        assert pen == 1
    data = emf.data()

    assert isinstance(data, type(b""))
    assert len(data) == _header_bytes + _EOF_bytes + _use_pen_bytes


def test_use_font():

    emf = EMF(*_size)

    with emf.use_font(Size("10pt", _dpi)) as font:
        assert font == 1
    data = emf.data()

    assert isinstance(data, type(b""))
    assert len(data) == _header_bytes + _EOF_bytes + _use_font_bytes


def test_rectangle():

    emf = EMF(*_size)

    # it needs a pen
    with emf.use_pen("solid", Size("1pt", _dpi), 0):
        emf.rectangle(Size("0pt", _dpi), Size("0pt", _dpi),
                      Size("1000pt", _dpi), Size("1000pt", _dpi))

    data = emf.data()
    assert isinstance(data, type(b""))
    assert len(data) == _header_bytes + _EOF_bytes + _use_pen_bytes + \
        _rect_bytes


def test_text_align():

    for align in "lrc":
        emf = EMF(*_size)

        emf.text_align(align)

        data = emf.data()
        assert isinstance(data, type(b""))
        assert len(data) == _header_bytes + _EOF_bytes + _text_align_bytes

    emf = EMF(*_size)
    with pytest.raises(TypeError):
        emf.text_align("X")


def test_text_color():

    for color in [0, 0xffffff, 0xff00ff]:
        emf = EMF(*_size)

        emf.text_color(color)

        data = emf.data()
        assert isinstance(data, type(b""))
        assert len(data) == _header_bytes + _EOF_bytes + _text_color_bytes


def test_text():

    emf = EMF(*_size)

    # it needs a font
    with emf.use_font(Size("16pt", _dpi)):
        text = "abcd"
        emf.text(Size("0pt", _dpi), Size("0pt", _dpi), text)

    data = emf.data()
    assert isinstance(data, type(b""))
    assert len(data) == _header_bytes + _EOF_bytes + _use_font_bytes + \
        _text_bytes(text)


def test_polyline():

    emf = EMF(*_size)

    # it needs a pen
    with emf.use_pen("solid", Size("1pt", _dpi), 0):
        emf.polyline([
            (Size("1in", _dpi), Size("1in", _dpi)),
            (Size("1in", _dpi), Size("2in", _dpi)),
            (Size("2in", _dpi), Size("2in", _dpi)),
            (Size("2in", _dpi), Size("1in", _dpi)),
        ])

    data = emf.data()
    assert isinstance(data, type(b""))
    assert len(data) == _header_bytes + _EOF_bytes + _use_pen_bytes + \
        _polyline_bytes(4)
