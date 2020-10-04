"""Module containing methods/classes for laying out ancestor trees.
"""

__all__ = ["EMFTreeVisitor"]

import logging

from . import dumbemf
from .size import Size

from .ancestor_tree import AncestorTreeVisitor


_log = logging.getLogger(__name__)

_BLACK = 0x0
_GRAY = 0xa0a0a0


class EMFTreeVisitor(AncestorTreeVisitor):
    """`~ged2doc.ancestor_tree.AncestorTreeVisitor` implementation which makes
    EMF image.

    Parameters
    ----------
    width, height : `ged2doc.size.Size`
        Width and height of the image.
    dpi : `float`
        Image resolution.
    """
    def __init__(self, width, height, dpi=300):
        self._width = width.to_dpi(dpi)
        self._height = height.to_dpi(dpi)
        self._dpi = dpi
        self._emf = dumbemf.EMF(self._width, self._height)
        self._nodes = 0

        self._black_pen = ("solid", Size("1pt", self._dpi), _BLACK)
        self._gray_pen = ("solid", Size("1pt", self._dpi), _GRAY)
        self._emf.set_bkmode(dumbemf.BackgroundMode.TRANSPARENT)

        self._fonts = {}

    def visitNode(self, node):
        # docstring inherited from base class
        self._nodes += 1
        textbox = node.textbox

        pen = self._gray_pen if node.person is None else self._black_pen
        with self._emf.use_pen(*pen):

            # draw a box/rectangle
            left = textbox.x0.to_dpi(self._dpi)
            right = textbox.x1.to_dpi(self._dpi)
            top = textbox.y0.to_dpi(self._dpi)
            bottom = textbox.y1.to_dpi(self._dpi)
            self._emf.rectangle(left, top, right, bottom)

        self._emf.text_align("c")
        self._emf.text_color(_GRAY if node.person is None else _BLACK)

        fontsize = textbox.font_size.to_dpi(self._dpi)
        with self._emf.use_font(fontsize):
            for line, (x, y) in textbox.lines_pos():
                self._emf.text(x.to_dpi(self._dpi), y.to_dpi(self._dpi), line)

    def visitMotherEdge(self, node, parentNode):
        # docstring inherited from base class
        x0 = node.textbox.x1.to_dpi(self._dpi)
        y0 = node.textbox.midy.to_dpi(self._dpi)
        x1 = parentNode.textbox.x0.to_dpi(self._dpi)
        y1 = parentNode.textbox.midy.to_dpi(self._dpi)
        midx = (x0 + x1) / 2

        # draw connections
        with self._emf.use_pen(*self._black_pen):
            points = [(x0, y0), (midx, y0)]
            self._emf.polyline(points)

        pen = self._gray_pen if parentNode.person is None else self._black_pen
        with self._emf.use_pen(*pen):
            points = [(midx, y0), (midx, y1), (x1, y1)]
            self._emf.polyline(points)

    def visitFatherEdge(self, node, parentNode):
        # docstring inherited from base class
        x0 = node.textbox.x1.to_dpi(self._dpi)
        y0 = node.textbox.midy.to_dpi(self._dpi)
        x1 = parentNode.textbox.x0.to_dpi(self._dpi)
        y1 = parentNode.textbox.midy.to_dpi(self._dpi)
        midx = (x0 + x1) / 2

        # draw connections
        pen = self._gray_pen if parentNode.person is None else self._black_pen
        with self._emf.use_pen(*pen):
            points = [(midx, y0), (midx, y1), (x1, y1)]
            self._emf.polyline(points)

    def makeEMF(self):
        """Produce EMF image from a visited tree.

        Returns
        -------
        document : `bytes`
            Concents of generated EMF image.
        mime_type : `str`
            MIME type of produced document.
        width : `ged2doc.size.Size`
            Width of SVG document
        height : `ged2doc.size.Size`
            Height of SVG document
        """
        if self._nodes == 0:
            return None

        emf = self._emf.data()
        return emf, 'image/x-emf', self._width, self._height
