"""Module containing methods/classes for laying out ancestor trees.
"""

from __future__ import absolute_import, division, print_function

__all__ = ["SVGTreeVisitor"]

import logging

from .ancestor_tree import AncestorTreeVisitor
from .dumbsvg import Doc, Line

_log = logging.getLogger(__name__)

# styles for displaying elements
_rect_style = "fill:none;stroke-width:1pt;stroke:black"
_rect_unknown_style = "fill:none;stroke-width:1pt;stroke:grey"
_pline_style = "fill:none;stroke-width:0.5pt;stroke:black"
_pline_unknown_style = "fill:none;stroke-width:0.5pt;stroke:grey"


class SVGTreeVisitor(AncestorTreeVisitor):
    """AncestorTreeVisitor implementation which makes SVG plots.
    """
    def __init__(self, units='in', fullxml=True):
        self._units = units
        self._fullxml = fullxml
        self._elements = []

    def visitNode(self, node):

        units = self._units

        textclass = None if node.person is None else 'svglink'
        style = _rect_unknown_style if node.person is None else _rect_style
        self._elements += node.textbox.svg(textclass=textclass, units=units, rect_style=style)

    def visitMotherEdge(self, node, parentNode):

        units = self._units

        x0 = node.textbox.x1
        y0 = node.textbox.midy
        x1 = parentNode.textbox.x0
        y1 = parentNode.textbox.midy
        midx = (x0 + x1) / 2
        style = _pline_unknown_style if parentNode.person is None else _pline_style
        self._elements += [
            Line(x1=x0 ^ units, y1=y0 ^ units, x2=midx ^ units, y2=y0 ^ units, style=_pline_style),
            Line(x1=midx ^ units, y1=y0 ^ units, x2=midx ^ units, y2=y1 ^ units, style=style),
            Line(x1=midx ^ units, y1=y1 ^ units, x2=x1 ^ units, y2=y1 ^ units, style=style),
        ]

    def visitFatherEdge(self, node, parentNode):

        units = self._units

        x0 = node.textbox.x1
        y0 = node.textbox.midy
        x1 = parentNode.textbox.x0
        y1 = parentNode.textbox.midy
        midx = (x0 + x1) / 2
        style = _pline_unknown_style if parentNode.person is None else _pline_style
        self._elements += [
            Line(x1=midx ^ units, y1=y0 ^ units, x2=midx ^ units, y2=y1 ^ units, style=style),
            Line(x1=midx ^ units, y1=y1 ^ units, x2=x1 ^ units, y2=y1 ^ units, style=style),
        ]

    def makeSVG(self, width, height):

        if not self._elements:
            return None

        units = self._units

        # produce complete XML
        svg = Doc(width=width ^ units, height=height ^ units)
        for element in self._elements:
            svg.add(element)

        # generate full XML
        xml = svg.xml(self._fullxml)

        return xml, 'image/svg', width, height
