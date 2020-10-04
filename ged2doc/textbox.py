"""Module defining `TexBox` class and related methods.
"""

__all__ = ['TextBox']

import logging

from .size import Size


_log = logging.getLogger(__name__)


class TextBox:
    """Class representing an SVG box with a text inside.

    This class takes care of the text wrapping and optional resizing of the
    box in vertical direction to fit all text.

    Parameters
    ----------
    x0 : `~ged2doc.size.Size`, optional
        Lowest X coordinate of corner (def: 0)
    y0 : `~ged2doc.size.Size`, optional
        Lowest Y coordinate of corner (def: 0)
    width : `~ged2doc.size.Size`, optional
        Width of a box (def: 0)
    maxwidth : `~ged2doc.size.Size`, optional
        Maximum width of a box (def: 0)
    height : `~ged2doc.size.Size`, optional
        Height of a box (def: 0)
    text : `str`, optional
        Text contained in a box (def: '')
    font_size : `~ged2doc.size.Size`, optional
        Font size (def: 10pt)
    rect_style : `str`, optional
        SVG style for rectangle
    text_style : `str`
        SVG style for text
    line_spacing : `~ged2doc.size.Size`, optional
        Space between lines (def: 1.5pt)
    padding : `~ged2doc.size.Size`, optional
        Box padding space (def: 4pt)
    """
    def __init__(self, x0=0, y0=0, width=0, maxwidth=0, height=0, text='',
                 font_size='10pt', padding='4pt', line_spacing='1.5pt', href=None):
        self._x0 = Size(x0)
        self._y0 = Size(y0)
        self._width = Size(width)
        self._maxwidth = Size(maxwidth)
        self._height = Size(height)
        self._text = text
        self._lines = self._text.split('\n')
        self._font_size = Size(font_size)
        self._padding = Size(padding)
        self._line_spacing = Size(line_spacing)
        self._href = href

        # calculate height if needed
        if self._height.value == 0:
            self.reflow()

    @property
    def x0(self):
        return self._x0

    @x0.setter
    def x0(self, x):
        self._x0 = x

    @property
    def x1(self):
        return self._x0 + self._width

    @property
    def y0(self):
        return self._y0

    @y0.setter
    def y0(self, y):
        self._y0 = y

    @property
    def y1(self):
        return self._y0 + self._height

    @property
    def midx(self):
        return self._x0 + self._width / 2

    @property
    def midy(self):
        return self._y0 + self._height / 2

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, width):
        self._width = width

    @property
    def height(self):
        return self._height

    @property
    def text(self):
        return self._text

    @property
    def href(self):
        return self._href

    @property
    def font_size(self):
        return self._font_size

    @property
    def lines(self):
        return self._lines

    def lines_pos(self):
        """Iterate over lines and their positions.

        For each line of test iterator returns a tuple of two items:

        - text for that line
        - position as a tuple of two ``Size`` instances, for horizontal
          position it returns the center of the box (same as ``midx``),
          and for vertical position it returns the baseline position of
          that line

        Yields
        ------
        line : `str`
            Text for a line.
        pos : `tuple` [ `Size` ]
            Text position.
        """
        x = self.midx
        for i, line in enumerate(self._lines):
            y = self.y0 + self._padding + self._font_size * (i + 1) + \
                self._line_spacing * i
            yield line, (x, y)

    def reflow(self):
        """Split the text inside the box so that it fits into box width, then
        recalculate box height so that all text fits inside the box.
        """
        self._lines = self._splitText(self._text)
        nlines = len(self._lines)
        self._height = nlines * self._font_size + \
            (nlines - 1) * self._line_spacing + 2 * self._padding

    def move(self, x0, y0):
        """Sets new coordinates fo x0 and y0

        Parameters
        ----------
        x0, y0 : `int` or `Size`
            New box coordinates.
        """
        self._x0 = Size(x0)
        self._y0 = Size(y0)

    def _splitText(self, text):
        """Tries to split a line of text into a number of lines which fit into
        box width. It honors embedded newlines, line will always be split at
        those first.

        Parameters
        ----------
        text : `str`
            Text to split into lines.

        Returns
        -------
        lines : `list` [ `str` ]
        """
        width = self._width - 2 * self._padding

        # _log.debug('=========================================================')
        # _log.debug('_splitText: %s width=%s', text, width)

        lines = self._splitText1(text, width)

        # _log.debug('_splitText: lines=[%s]', ' | '.join(lines))

        if len(lines) > 1 and self._maxwidth > Size():
            # try to increase box width up to a maximum allowed width

            width = self._maxwidth - 2 * self._padding
            lines1 = self._splitText1(text, width)

            if len(lines1) < len(lines):
                self._width = max(self._textWidth(line) for line in lines1) + \
                    2 * self._padding
                return lines1

        return lines

    def _splitText1(self, text, width):
        """Tries to split a line of text into a number of lines which fit into
        box width.
        """

        lines = []
        for line in text.split('\n'):
            words = line.split()
            idx = 0
            while idx + 1 < len(words):
                twowords = ' '.join(words[idx:idx + 2])
                twwidth = self._textWidth(twowords)
                # _log.debug('_splitText1: %s width=%s', twowords, twwidth)
                if twwidth <= width:
                    words[idx:idx + 2] = [twowords]
                else:
                    idx += 1
            lines += words

        return lines

    def _textWidth(self, text):
        """Calculates approximate width of the string of text.
        """

        # just  a wild guess for now, try to do better later
        return self._font_size * len(text) * 0.5

    def __str__(self):
        return "TextBox(x0={}, x1={}, y0={}, y1={}, w={}, h={})".format(
            self.x0, self.x1, self.y0, self.y1, self.width, self.height
        )
