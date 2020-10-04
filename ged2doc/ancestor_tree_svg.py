"""Module containing methods/classes for laying out ancestor trees.
"""

__all__ = ["SVGTreeVisitor"]

import logging

from .ancestor_tree import AncestorTreeVisitor
from .dumbsvg import Doc, Line, Rect, Text, Tspan, Hyperlink

_log = logging.getLogger(__name__)

# styles for displaying elements
_rect_style = "fill:none;stroke-width:1pt;stroke:black"
_rect_unknown_style = "fill:none;stroke-width:1pt;stroke:grey"
_pline_style = "fill:none;stroke-width:0.5pt;stroke:black"
_pline_unknown_style = "fill:none;stroke-width:0.5pt;stroke:grey"


class SVGTreeVisitor(AncestorTreeVisitor):
    """`~ged2doc.ancestor_tree.AncestorTreeVisitor` implementation which makes
    SVG plots.

    Parameters
    ----------
    units : `str`
        Type of dimension units for output SVG document.
    fullxml : `bool`, optional
        If ``True`` then generate full XML header.
    """
    def __init__(self, units='in', fullxml=True):
        self._units = units
        self._fullxml = fullxml
        self._elements = []

    def visitNode(self, node):
        # docstring inherited from base class
        units = self._units

        textclass = None if node.person is None else 'svglink'
        style = _rect_unknown_style if node.person is None else _rect_style
        self._elements += self._textbox_svg(node.textbox, textclass=textclass,
                                            units=units, rect_style=style)

    def visitMotherEdge(self, node, parentNode):
        # docstring inherited from base class
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
        # docstring inherited from base class
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
        """Produce SVG document from a visited tree.

        Parameters
        ----------
        width : `ged2doc.size.Size`
            Width of SVG document
        height : `ged2doc.size.Size`
            Height of SVG document

        Returns
        -------
        document : `str`
            Concents of generated SVG document.
        mime_type : `str`
            MIME type of produced document.
        width : `ged2doc.size.Size`
            Width of SVG document
        height : `ged2doc.size.Size`
            Height of SVG document
        """

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

    def _textbox_svg(self, textbox, textclass=None, units='in', rect_style=None):
        """Produces list of SVG elements for a textbox.
        """
        shapes = []

        # render box
        kw = dict(x=textbox.x0 ^ units, y=textbox.y0 ^ units,
                  width=textbox.width ^ units, height=textbox.height ^ units)
        if rect_style:
            kw['style'] = rect_style
        rect = Rect(**kw)
        shapes.append(rect)

        # render text
        kw = dict(text_anchor='middle', font_size=textbox.font_size ^ 'pt')
        if textclass:
            kw['class_'] = textclass
        txt = Text(**kw)
        if textbox.href:
            a = Hyperlink(textbox.href)
            a.add(txt)
            shapes.append(a)
        else:
            shapes.append(txt)
        for line, (x, y) in textbox.lines_pos():
            tspan = Tspan(x=x ^ units, y=y ^ units, value=line)
            txt.add(tspan)

        return shapes
