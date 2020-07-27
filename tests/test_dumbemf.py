"""Unit test for dumbemf module
"""

from __future__ import absolute_import, division, print_function

import logging
import pytest

from ged2doc.dumbemf import EMF
from ged2doc.size import Size


logging.basicConfig(level=logging.DEBUG)

_dpi = 300.
_size = Size("5in", _dpi), Size("3in", _dpi)

_header_bytes = 88
_EOF_bytes = 5 * 4
_pen_bytes = 7 * 4
_font_bytes = 332
_select_object_bytes = 3 * 4
_rect_bytes = 6 * 4
_text_align_bytes = 3 * 4
_text_color_bytes = 3 * 4


def _text_bytes(text):
    size = 9 * 4
    size += len(text) * 2
    if size % 4 != 0:
        size += 2
    return size


def test_001_empty():
    "Test for empty EMF, with only header and EOF"

    emf = EMF(*_size)
    data = emf.data()

    assert isinstance(data, type(b""))
    assert len(data) == _header_bytes + _EOF_bytes


def test_create_pen():

    emf = EMF(*_size)

    pen = emf.create_pen("solid", Size("1pt", _dpi), 0)
    assert pen == 1
    pen = emf.create_pen("solid", Size("1pt", _dpi), 0x112233)
    assert pen == 2
    data = emf.data()

    assert isinstance(data, type(b""))
    assert len(data) == _header_bytes + _EOF_bytes + _pen_bytes * 2


def test_create_font():

    emf = EMF(*_size)

    font = emf.create_font(Size("10pt", _dpi))
    assert font == 1
    font = emf.create_font(Size("16pt", _dpi))
    assert font == 2
    data = emf.data()

    assert isinstance(data, type(b""))
    assert len(data) == _header_bytes + _EOF_bytes + _font_bytes * 2


def test_rectangle():

    emf = EMF(*_size)

    # it needs a pen
    pen = emf.create_pen("solid", Size("1pt", _dpi), 0)
    emf.rectangle(Size("0pt", _dpi), Size("0pt", _dpi),
                  Size("1000pt", _dpi), Size("1000pt", _dpi),
                  pen)

    data = emf.data()
    assert isinstance(data, type(b""))
    assert len(data) == _header_bytes + _EOF_bytes + _pen_bytes + \
        _select_object_bytes + _rect_bytes


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
    font = emf.create_font(Size("16pt", _dpi))
    text = "abcd"
    emf.text(Size("0pt", _dpi), Size("0pt", _dpi), text, font)

    data = emf.data()
    assert isinstance(data, type(b""))
    assert len(data) == _header_bytes + _EOF_bytes + _font_bytes + \
        _select_object_bytes + _text_bytes(text)
