"""Module defining TexBox class and related methods.
"""

from __future__ import absolute_import, division, print_function

__all__ = ['TextBox']

import logging

from .dumbsvg import Rect, Text, Tspan, Hyperlink
from .size import Size


_log = logging.getLogger(__name__)


class TextBox(object):
    """Class representing an SVG box with text inside.

    This class takes care of the text wrapping and optional resizing of the
    box in vertical direction to fit all text.

    :param Size x0: lowest X coordinate of corner (def: 0)
    :param Size y0: lowest Y coordinate of corner (def: 0)
    :param Size width: width of a box (def: 0)
    :param Szie maxwidth: maximum width of a box (def: 0)
    :param Size height: height of a box (def: 0)
    :param str text: text contained in a box (def: '')
    :param Size font_size: font size (def: 10pt)
    :param str rect_style: SVG style for rectangle
    :param str text_style: SVG style for text
    :param Size line_spacing: space between lines (def: 3pt)
    :param Size padding: box padding space (def: 3pt)
    """

    def __init__(self, x0=0, y0=0, width=0, maxwidth=0, height=0, text='',
                 font_size='10pt', padding='4pt', line_spacing='1.5pt',
                 rect_style='', text_style='', href=None):
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
        self._rect_style = rect_style
        self._text_style = text_style
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

    def reflow(self):
        '''
        Split the text inside the box so that it fits into box width, then
        recalculate box height so that all text fits inside the box.
        '''
        self._lines = self._splitText(self._text)
        nlines = len(self._lines)
        self._height = nlines * self._font_size + \
            (nlines - 1) * self._line_spacing + 2 * self._padding

    def move(self, x0, y0):
        ''' Sets new coordinates fo x0 and y0 '''
        self._x0 = Size(x0)
        self._y0 = Size(y0)

    def svg(self, textclass=None, units='in'):
        ''' Produces list of SVG elements (pysvg objects) '''

        shapes = []

        # render box
        kw = dict(x=self.x0 ^ units, y=self.y0 ^ units,
                  width=self.width ^ units, height=self.height ^ units)
        if self._rect_style:
            kw['style'] = self._rect_style
        rect = Rect(**kw)
        shapes.append(rect)

        # render text
        kw = dict(text_anchor='middle', font_size=self._font_size ^ 'pt')
        if self._text_style:
            kw['style'] = self._text_style
        if textclass:
            kw['class_'] = textclass
        txt = Text(**kw)
        if self._href:
            a = Hyperlink(self._href)
            a.add(txt)
            shapes.append(a)
        else:
            shapes.append(txt)
        for i, line in enumerate(self._lines):
            x = self.midx
            y = self.y0 + self._padding + self._font_size * (i + 1) + \
                self._line_spacing * i
            tspan = Tspan(x=x ^ units, y=y ^ units, value=line)
            txt.add(tspan)

        return shapes

    def _splitText(self, text):
        '''
        Tries to split a line of text into a number of lines which fit into
        box width. It honors embedded newlines, line will always be split at
        those first.
        '''

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
        '''
        Tries to split a line of text into a number of lines which fit into
        box width.
        '''

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
        ''' Calculates approximate width of the string of text '''

        # just  a wild guess for now, try to do better later
        return self._font_size * len(text) * 0.5
