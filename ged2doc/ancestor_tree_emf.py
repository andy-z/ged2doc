"""Module containing methods/classes for laying out ancestor trees.
"""

from __future__ import absolute_import, division, print_function

__all__ = ["EMFTreeVisitor"]

import logging

from . import dumbemf
from .size import Size

from .ancestor_tree import AncestorTreeVisitor


_log = logging.getLogger(__name__)

_BLACK = 0x0
_GRAY = 0xa0a0a0


class EMFTreeVisitor(AncestorTreeVisitor):
    """AncestorTreeVisitor implementation which makes EMF image.
    """
    def __init__(self, width, height, dpi=300):
        self._width = Size(width, dpi)
        self._height = Size(height, dpi)
        self._dpi = dpi
        self._emf = dumbemf.EMF(self._width, self._height)
        self._nodes = 0

        self._black_pen = self._emf.create_pen("solid", Size("1pt", self._dpi), _BLACK)
        self._gray_pen = self._emf.create_pen("solid", Size("1pt", self._dpi), _GRAY)

        self._fonts = {}

    def visitNode(self, node):
        self._nodes += 1
        textbox = node.textbox

        pen = self._gray_pen if node.person is None else self._black_pen

        # draw a box/rectangle
        left = Size(textbox.x0, self._dpi)
        right = Size(textbox.x1, self._dpi)
        top = Size(textbox.y0, self._dpi)
        bottom = Size(textbox.y1, self._dpi)
        self._emf.rectangle(left, top, right, bottom, pen)

        # text
        fontsize = Size(textbox.font_size, self._dpi)
        font = self._fonts.get(fontsize.pt)
        if font is None:
            font = self._emf.create_font(fontsize)
            self._fonts[fontsize.pt] = font

        self._emf.text_align("c")
        self._emf.text_color(_BLACK if node.person is None else _GRAY)

        for line, (x, y) in textbox.lines_pos():
            self._emf.text(Size(x, self._dpi), Size(y, self._dpi), line, font)

    def visitMotherEdge(self, node, parentNode):
        pass

    def visitFatherEdge(self, node, parentNode):
        pass

    def makeEMF(self):

        if self._nodes == 0:
            return None

        emf = self._emf.data()
        return emf, 'image/x-emf', self._width, self._height
