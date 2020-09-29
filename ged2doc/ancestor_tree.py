"""Module containing methods/classes for laying out ancestor trees.
"""

from __future__ import absolute_import, division, print_function

__all__ = ["AncestorTree", "AncestorTreeVisitor", "TreeNode"]

import abc
import logging

from .size import Size
from .textbox import TextBox


_log = logging.getLogger(__name__)


class TreeNode(object):
    """Class representing node in a tree, which is a box with a person name.

    :param Individual person: Corresponding individual, may be None.
    :param int gen: Generation number, 0 for the tree root.
    :param TreeNode motherNode: Node for mather, can be None.
    :param TreeNode fatherNode: Node for mather, can be None.
    :param Size box_width: desired width of this node, actual width can grow.
    :param Size max_box_width: Maximum width this node can grow to.
    :param Size font_size: Size of the font for the text.
    :param Size gen_dist: Horiz. distance between generations.
    """

    _vpadding = Size('2pt')  # vertical padding around each sub-tree or node

    def __init__(self, person, gen, motherNode, fatherNode, box_width,
                 max_box_width, font_size, gen_dist):
        self.mother = motherNode
        self.father = fatherNode
        self.generation = gen
        self._person = person

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
        href = None if person is None else ('#person.' + person.xref_id)
        x0 = gen * (gen_dist + box_width)
        self._box = TextBox(text=self.name, x0=x0, width=box_width,
                            maxwidth=max_box_width, font_size=font_size,
                            href=href)
        self.setY0(Size())

    @property
    def person(self):
        """Person corresponding to this node, can be None (`ged4py.model.Individual`).
        """
        return self._person

    @property
    def textbox(self):
        """Textbox for this node (`TextBox`).
        """
        return self._box

    @property
    def subTreeHeight(self):
        """The height of the whole tree including parent boxes (`Size`).
        """
        h = Size()
        if self.mother:
            h = self.mother.subTreeHeight + self.father.subTreeHeight + self._vpadding
        h = max(h, self._box.height)
        _log.debug('TreeNode.name = %s; height = %s', self.name, h)
        return h

    def setY0(self, y0):
        """Recalculate Y position of box tree so that topmost box is at `y0`.
        """
        y0 = Size(y0)
        _log.debug('TreeNode.name = %s; setY0 = %s', self.name, y0)
        if self.mother:
            self.mother.setY0(y0)
            self.father.setY0(y0 + self._vpadding + self.mother.subTreeHeight)
            # sodd formula need for better precision
            self._box.y0 = (2 * self.mother.textbox.y0 + self.mother.textbox.height +
                            2 * self.father.textbox.y0 + self.father.textbox.height -
                            2 * self.textbox.height) / 4
        else:
            self._box.y0 = y0


class AncestorTree(object):
    """Class implementing layout of ancestor trees.

    :param Individual person: Corresponding individual, may be None.
    :param int max_gen: Maximum number of generations to plot, default is 4
    :param Size width: Specification for plot width, accepts `Size` or `str`.
    :param Size gen_dist: Distance between generations, `Size` or `str`,
        default is "12pt"
    :param Size font_size: Font size, accepts `Size` or `str`.
    """

    def __init__(self, person, max_gen=4, width="5in", gen_dist="12pt", font_size="10pt"):
        self.max_gen = max_gen
        self._width = Size(width)
        self._height = Size()
        self.gen_dist = Size(gen_dist)
        self.font_size = Size(font_size)
        self.root = None

        def _genDepth(person):
            """Return number known generations for a person"""
            if not person:
                return 0
            return max(_genDepth(person.father), _genDepth(person.mother)) + 1

        def _boxes(box):
            """Generator for person parents, returns None for unknown parent"""
            yield box
            if box.mother:
                for p in _boxes(box.mother):
                    yield p
                for p in _boxes(box.father):
                    yield p

        # get the number of generations, limit to max_gen
        ngen = min(_genDepth(person), self.max_gen)
        _log.debug('parent_tree: person = %s', person.name)
        _log.debug('parent_tree: ngen = %d', ngen)

        # if no parents then tree is empty
        if ngen < 2:
            return

        # calculate horizontal size of each box
        box_width = (self._width - (self.max_gen - 1) * self.gen_dist -
                     Size('4pt')) / self.max_gen
        max_box_width = (self._width - (ngen - 1) * self.gen_dist -
                         Size('4pt')) / ngen

        # build tree
        self.root = self._makeTree(person, 0, ngen, box_width, max_box_width)

        # add small padding, get full height
        self._height = self.root.subTreeHeight + Size("4pt")
        self.root.setY0("2pt")

        # update box width for every generation and calculate total width
        width = Size('2pt')  # extra 1pt to avoid cropping
        for gen in range(ngen):
            gen_width = max(pbox.textbox.width for pbox in _boxes(self.root)
                            if pbox.generation == gen)
            for pbox in _boxes(self.root):
                if pbox.generation == gen:
                    pbox.textbox.width = gen_width
                    pbox.textbox.x0 = width
                    _log.debug('parent_tree: %s', pbox.textbox)
            width += gen_width + self.gen_dist
        width -= self.gen_dist
        width += Size('2pt')  # extra 1pt to avoid cropping
        self._width = width
        _log.debug('parent_tree: size = %s x %s', self._width, self._height)

    @property
    def width(self):
        """Full width of the tree (`Size`)
        """
        return self._width

    @property
    def height(self):
        """Full height of the tree (`Size`)
        """
        return self._height

    def visit(self, visitor):
        """Visit every node and edge in a tree.

        :param AncestorTreeVisitor visitor: Tree visitor.
        """
        if self.root:
            self._visit(visitor, self.root)

    def _visit(self, visitor, node):
        """Helper method for recursive visiting of the nodes.
        """
        visitor.visitNode(node)
        if node.mother:
            self._visit(visitor, node.mother)
            visitor.visitMotherEdge(node, node.mother)
        if node.father:
            self._visit(visitor, node.father)
            visitor.visitFatherEdge(node, node.father)

    def _makeTree(self, person, gen, max_gen, box_width, max_box_width):
        """Recursively generate tree of TreeNode instances
        """
        if gen < max_gen:

            motherTree = None
            fatherTree = None
            if person and (person.mother or person.father):
                motherTree = self._makeTree(person.mother, gen + 1, max_gen,
                                            box_width, max_box_width)
                fatherTree = self._makeTree(person.father, gen + 1, max_gen,
                                            box_width, max_box_width)
            box = TreeNode(person, gen, motherTree, fatherTree, box_width,
                           max_box_width, self.font_size, self.gen_dist)
            return box


class AncestorTreeVisitor(metaclass=abc.ABCMeta):
    """Interface for tree visitors.

    Instances of this class can be passed to `visit()` method to
    iterate over all nodes and edges in an ancestor tree.
    """

    @abc.abstractmethod
    def visitNode(self, node):
        """Visitor method for a node in tree.

        :param TreeNode node: Tree node.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def visitMotherEdge(self, node, parentNode):
        """Visitor method for an edge leading from node to its mother.

        It is guaranteed that `visitNode` is called for both nodes before
        this method is called.

        :param TreeNode node: Tree node.
        :param TreeNode parentNode: Parent tree node.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def visitFatherEdge(self, node, parentNode):
        """Visitor method for an edge leading from node to its mother.

        It is guaranteed that `visitNode` is called for both nodes before
        this method is called.

        :param TreeNode node: Tree node.
        :param TreeNode parentNode: Parent tree node.
        """
        raise NotImplementedError()
