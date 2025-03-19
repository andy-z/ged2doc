"""Python module for generating SVG.

Only the most trivial features are implemented, stuff that is required by
ged2doc package.
"""

from __future__ import annotations

__all__ = ["Doc", "Element", "Hyperlink", "Line", "Rect", "Text", "Tspan"]

from typing import Any


class Doc:
    """Class for SVG document, top-level structure.

    Parameters
    ----------
    width, height : `int` or `str`
        Document width and height, int for pixels or string.
    """

    def __init__(self, width: int | str, height: int | str):
        self._width = width
        self._height = height
        self._top = Element(
            "svg",
            [
                ("width", str(self._width)),
                ("height", str(self._height)),
                ("version", "1.1"),
                ("xmlns", "http://www.w3.org/2000/svg"),
                ("xmlns:xlink", "http://www.w3.org/1999/xlink"),
            ],
        )

    def add(self, element: Element) -> None:
        """Add new element to the document.

        Parameters
        ----------
        element : `Element`
            Element to add.
        """
        self._top.add(element)

    def xml(self, full_xml: bool = True) -> str:
        """Produce XML representation of the document.

        Parameters
        ----------
        full_xml : `bool`, optional
            If True then proper XML header is added.

        Returns
        -------
        doc : `str`
            String containing XML.
        """
        text = ""
        if full_xml:
            text += (
                '<?xml version="1.0" standalone="no"?>\n'
                '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" '
                '"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n'
            )
        text += self._top.xml()
        return text


class Element:
    """Base class for all SVG elements.

    Parameters
    ----------
    tag : `str`
        SVG tag name
    attributes :`list` [ `tuple` ], optional
        List of tuples (attribute, attr_value).
    value : `str`, optional
        Element value (text).
    """

    def __init__(self, tag: str, attributes: list[tuple[str, Any]] | None = None, value: str = ""):
        self._tag = tag
        self._attributes = attributes or []
        self._value = value
        self._elements: list[Element] = []

    def add(self, element: Element) -> None:
        """Add new sub-element to the element.

        Parameters
        ----------
        element : `Element`
            Element to add.
        """
        self._elements.append(element)

    def xml(self) -> str:
        """Produce XML fragment for this element.

        Returns
        -------
        xml : `str`
            String containing XML fragment.
        """
        lines = []
        txt = "<" + self._tag
        for attr, val in self._attributes:
            txt += f' {attr}="{val}"'
        if not self._value and not self._elements:
            txt += " />"
            lines += [txt]
        else:
            txt += ">"
            lines += [txt]
            if self._value:
                lines += [self._value]
            lines += [elem.xml() for elem in self._elements]
            lines += ["</" + self._tag + ">"]
        return "\n".join(lines)


class Line(Element):
    """Class for SVG line element.

    Parameters
    ----------
    x1, y1, x2, y2 : `str`
        Coordinates of line ends.
    style : `str`, optional
        Line style.
    """

    def __init__(self, x1: str, y1: str, x2: str, y2: str, style: str | None = None):
        attr = [("x1", x1), ("y1", y1), ("x2", x2), ("y2", y2)]
        if style:
            attr += [("style", style)]
        Element.__init__(self, "line", attr)


class Rect(Element):
    """Class for SVG rect element.

    Parameters
    ----------
    x, y : `str`
        Coordinates of top left corner of the box.
    width, height : `str`
        Width and height of the box.
    style : `str`, optional
        Line style.
    """

    def __init__(self, x: str, y: str, width: str, height: str, style: str | None = None):
        attr = [("x", x), ("y", y), ("width", width), ("height", height)]
        if style:
            attr += [("style", style)]
        Element.__init__(self, "rect", attr)


class Text(Element):
    """Class for SVG text element.

    Parameters
    ----------
    value : `str`, optional
        Text to display.
    font_size : `str`, optional
        Font size for text.
    text_anchor : `str`
        Text anchor property.
    style : `str`, optional
        Text style.
    class_ : `str`, optional
        Text CSS class.
    """

    def __init__(
        self,
        value: str = "",
        font_size: str | None = None,
        text_anchor: str | None = None,
        style: str | None = None,
        class_: str | None = None,
    ):
        attr = []
        if font_size:
            attr += [("font-size", font_size)]
        if text_anchor:
            attr += [("text-anchor", text_anchor)]
        if style:
            attr += [("style", style)]
        if class_:
            attr += [("class", class_)]
        Element.__init__(self, "text", attr, value)


class Tspan(Element):
    """Class for SVG tspan element.

    Parameters
    ----------
    x, y : `str`
        Coordinates of the box.
    value : `str`, optional
        Text to display.
    """

    def __init__(self, x: str, y: str, value: str = ""):
        attr = [("x", x), ("y", y)]
        Element.__init__(self, "tspan", attr, value)


class Hyperlink(Element):
    """Class for SVG "a" element.

    Parameters
    ----------
    href : `str`
        Hyperlink value.
    """

    def __init__(self, href: str):
        attr = [("xlink:href", href)]
        Element.__init__(self, "a", attr)
