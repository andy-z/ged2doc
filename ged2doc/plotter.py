"""Module responsible for making plots, e.g. parent tree plots.
"""

from __future__ import absolute_import, division, print_function

import logging

from .dumbsvg import Doc, Line
from .size import Size
from .textbox import TextBox

_rect_style = "fill:none;stroke-width:1pt;stroke:black"
_rect_unknown_style = "fill:none;stroke-width:1pt;stroke:grey"
_pline_style = "fill:none;stroke-width:0.5pt;stroke:black"
_pline_unknown_style = "fill:none;stroke-width:0.5pt;stroke:grey"

_log = logging.getLogger(__name__)


class _PersonBox(object):
    """Class implementing "drawing" of SVG box with person name.

    :param person: `Person`
    :param int gen:
        Generation number, 0 for the tree root
    :param motherBox: `_PersonBox`
    :param fatherBox: `_PersonBox` Boxes for parents
    :param box_width: `Size`
    :param max_box_width: `Size`
    :param font_size: `Size`
    :param gen_dist: `Size`,  Distance between boxes of different generations
    """

    _margin = Size('1pt')

    def __init__(self, person, gen, motherBox, fatherBox, box_width,
                 max_box_width, font_size, gen_dist):
        self.mother = motherBox
        self.father = fatherBox
        self.generation = gen

        # displayed persons name
        if person is None:
            self.name = '?'
        elif gen == 0:
            self.name = (person.name.first or '') + ' ' + \
                (person.name.maiden or person.name.surname or '')
            if not self.name.strip():
                self.name = '...'
        else:
            self.name = (person.name.first or '') + ' ' + \
                (person.name.surname or '')
        style = _rect_unknown_style if person is None else _rect_style
        href = None if person is None else ('#person.' + person.xref_id)
        x0 = gen * (gen_dist + box_width) + Size('1pt')
        self.box = TextBox(text=self.name, x0=x0, width=box_width,
                           maxwidth=max_box_width, font_size=font_size,
                           rect_style=style, href=href)

        self.setY0(Size())

    def height(self):
        """Calculate the height of the whole tree including parent boxes.
        """
        h = Size()
        if self.mother:
            h = self.mother.height() + self.father.height() + 2 * self._margin
        h = max(h, self.box.height + 2 * self._margin)
        _log.debug('_PersonBox.name = %s; height = %s', self.name, h)
        return h

    def setY0(self, y0):
        """REcalculate Y position of box tree so that topmost box is at `y0`.
        """
        _log.debug('_PersonBox.name = %s; setY0 = %s', self.name, y0)
        if self.mother:
            self.mother.setY0(y0 + self._margin)
            mheight = self.mother.height()
            self.father.setY0(y0 + mheight + self._margin)
            self.box.y0 = (self.mother.box.midy + self.father.box.midy -
                           self.box.height) / 2
        else:
            self.box.y0 = y0 + self._margin

    def svg(self, units='in'):
        """Generate SVG (XML) for this box including links to parents
        """
        textclass = None if self.name == '?' else 'svglink'
        elements = self.box.svg(textclass, units)

        if self.mother:
            x0 = self.box.x1
            y0 = self.box.midy
            pbox1 = self.mother
            x1 = pbox1.box.x0
            y1 = pbox1.box.midy
            midx = (x0 + x1) / 2
            style = _pline_unknown_style if pbox1.name == '?' else _pline_style
            elements.append(Line(x1=x0 ^ units, y1=y0 ^ units,
                                 x2=midx ^ units, y2=y0 ^ units,
                                 style=_pline_style))
            elements.append(Line(x1=midx ^ units, y1=y0 ^ units,
                                 x2=midx ^ units, y2=y1 ^ units,
                                 style=style))
            elements.append(Line(x1=midx ^ units, y1=y1 ^ units,
                                 x2=x1 ^ units, y2=y1 ^ units,
                                 style=style))
            pbox2 = self.father
            y1 = pbox2.box.midy
            style = _pline_unknown_style if pbox2.name == '?' else _pline_style
            elements.append(Line(x1=midx ^ units, y1=y0 ^ units,
                                 x2=midx ^ units, y2=y1 ^ units,
                                 style=style))
            elements.append(Line(x1=midx ^ units, y1=y1 ^ units,
                                 x2=x1 ^ units, y2=y1 ^ units,
                                 style=style))

        return elements


class Plotter(object):
    """Class implementing plotting of the person trees.

    :param int max_gen: Maximum number of generations to plot, default is 4
    :param str width: Specification for plot width, accepts any CSS-style
        length, default is "5in"
    :param str gen_dist: Distance between generations, accepts any CSS-style
        length, default is "12pt"
    :param str font_size: Font size, accepts any CSS-style size, default
        is "10pt"
    :param boolean full_xml: If True (default) produce full XML document with
        headers, otherwise only SVG contents.
    :param boolean refs: If True make person name a link. This parameter is
        ignored for now, links are always made.

    """

    def __init__(self, max_gen=4, width="5in", gen_dist="12pt",
                 font_size="10pt", fullxml=True, refs=False):
        self.max_gen = max_gen
        self.width = Size(width)
        self.gen_dist = Size(gen_dist)
        self.font_size = Size(font_size)
        self.fullxml = fullxml
        self.refs = refs
        self.vmargin = Size("4pt")
        self.vmargin2 = Size("6pt")

    def parent_tree(self, person, units):
        """Plot parent tree of a person, max_gen gives the max total
        number of generations plotted.

        If tree cannot be plotted (e.g. when person has no parents) then None
        is returned, otherwise a four-tuple is returned.

        :param person: `Person`, Person for which to plot the tree.
        :param str units: Units name for output, e.g. "in" or "px" (all
            lengths are converted to that unit).
        :return:
            image : bytes, Image data (XML contents)
            mime_type : str, Type of produced image (currently image/svg).
            image_width : `Size`
            image_height : `Size`
        """

        # returns number known generations for a person
        def _genDepth(person):
            if not person:
                return 0
            return max(_genDepth(person.father), _genDepth(person.mother)) + 1

        # generator for person parents, returns None for unknown parent
        def _boxes(box):
            yield box
            if box.mother:
                for p in _boxes(box.mother):
                    yield p
                for p in _boxes(box.father):
                    yield p

        # get the number of generations, limit to 4
        ngen = min(_genDepth(person), self.max_gen)
        _log.debug('parent_tree: person = %s', person.name)
        _log.debug('parent_tree: ngen = %d', ngen)

        # if no parents then do not plot anything
        if ngen < 2:
            return

        # calculate horizontal size of each box
        box_width = (self.width - (ngen - 1) * self.gen_dist -
                     Size('2pt')) / self.max_gen
        max_box_width = (self.width - (ngen - 1) * self.gen_dist -
                         Size('2pt')) / ngen

        # build tree of boxes
        boxtree = self._makeTree(person, 0, ngen, box_width, max_box_width)

        # get full height
        height = boxtree.height()

        # update box width for every generation and calculate total width
        width = Size('1pt')
        for gen in range(ngen):
            gen_width = max(pbox.box.width for pbox in _boxes(boxtree)
                            if pbox.generation == gen)
            for pbox in _boxes(boxtree):
                if pbox.generation == gen:
                    pbox.box.width = gen_width
                    pbox.box.x0 = width
            width += gen_width + self.gen_dist
        width -= self.gen_dist
        width += Size('1pt')

        # produce complete XML
        svg = Doc(width=width ^ units, height=height ^ units)
        for pbox in _boxes(boxtree):
            for element in pbox.svg(units):
                svg.add(element)

        # generate full XML
        xml = svg.xml(self.fullxml)

        return xml, 'image/svg', width, height

    def _makeTree(self, person, gen, max_gen, box_width, max_box_width):
        """Recursively generate tree of _PersonBox instances
        """
        if gen < max_gen:

            motherTree = None
            fatherTree = None
            if person and (person.mother or person.father):
                motherTree = self._makeTree(person.mother, gen + 1, max_gen,
                                            box_width, max_box_width)
                fatherTree = self._makeTree(person.father, gen + 1, max_gen,
                                            box_width, max_box_width)
            box = _PersonBox(person, gen, motherTree, fatherTree, box_width,
                             max_box_width, self.font_size, self.gen_dist)
            return box
