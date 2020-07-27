"""Unit test for dumbemf module
"""

from __future__ import absolute_import, division, print_function

import logging

from ged2doc.dumbemf import EMF
from ged2doc.size import Size


logging.basicConfig(level=logging.DEBUG)

_dpi = 300.
_size = Size("5in", _dpi), Size("3in", _dpi)

_header_bytes = 88
_EOF_bytes = 5 * 4


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
    assert len(data) == _header_bytes + _EOF_bytes + 7 * 4 * 2


def test_create_font():

    emf = EMF(*_size)

    font = emf.create_font(Size("10pt", _dpi))
    assert font == 1
    font = emf.create_font(Size("16pt", _dpi))
    assert font == 2
    data = emf.data()

    assert isinstance(data, type(b""))
    assert len(data) == _header_bytes + _EOF_bytes + 332 * 2
