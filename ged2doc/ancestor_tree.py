"""Module containing methods/classes for laying out ancestor trees."""

from __future__ import annotations

__all__ = ["AncestorTree", "AncestorTreeVisitor", "TreeNode"]

import abc
import logging
from collections.abc import Iterator
from typing import TYPE_CHECKING

from .size import Size
from .textbox import TextBox

if TYPE_CHECKING:
    from ged4py import model


_log = logging.getLogger(__name__)


class TreeNode:
    """Class representing node in a tree, which is a box with a person name.

    Parameters
    ----------
    person : `ged4py.model.Individual`
        Corresponding individual, may be ``None``.
    gen : `int`
        Generation number, 0 for the tree root.
    mother_node : `TreeNode`
        Node for mother, can be ``None``.
    father_node : `TreeNode`
        Node for father, can be ``None``.
    box_width : `ged2doc.size.Size`
        Desired width of this node, actual width can grow.
    max_box_width : `ged2doc.size.Size`
        Maximum width this node can grow to.
    font_size : `ged2doc.size.Size`
        Size of the font for the text.
    gen_dist : `ged2doc.size.Size`
        Horiz. distance between generations.
    """

    _vpadding = Size("2pt")  # vertical padding around each sub-tree or node

    def __init__(
        self,
        person: model.Individual | None,
        gen: int,
        mother_node: TreeNode | None,
        father_node: TreeNode | None,
        box_width: Size,
        max_box_width: Size,
        font_size: Size,
        gen_dist: Size,
    ):
        self.mother = mother_node
        self.father = father_node
        self.generation = gen
        self._person = person

        # displayed persons name
        if person is None:
            self.name = "?"
        elif gen == 0:
            self.name = (person.name.first or "") + " " + (person.name.maiden or person.name.surname or "")
            if not self.name.strip():
                self.name = "..."
        else:
            self.name = (person.name.first or "") + " " + (person.name.surname or "")
        href = None if person is None else (f"#person.{person.xref_id}")
        x0 = gen * (gen_dist + box_width)
        self._box = TextBox(
            text=self.name, x0=x0, width=box_width, maxwidth=max_box_width, font_size=font_size, href=href
        )
        self.setY0(Size())

    @property
    def person(self) -> model.Individual | None:
        """Person corresponding to this node, can be None
        (`ged4py.model.Individual`).
        """
        return self._person

    @property
    def textbox(self) -> TextBox:
        """Textbox for this node (`TextBox`)."""
        return self._box

    @property
    def subTreeHeight(self) -> Size:
        """The height of the whole tree including parent boxes (`Size`)."""
        h = Size()
        if self.mother and self.father:
            h = self.mother.subTreeHeight + self.father.subTreeHeight + self._vpadding
        h = max(h, self._box.height)
        _log.debug("TreeNode.name = %s; height = %s", self.name, h)
        return h

    def setY0(self, y0: Size | str) -> None:
        """Recalculate Y position of box tree so that topmost box is at `y0`.

        Parameters
        ----------
        y0 : `ged2doc.size.Size`
            New topmost box position, accepts anything convertible to
            `ged2doc.size.Size`.
        """
        y0 = Size(y0)
        _log.debug("TreeNode.name = %s; setY0 = %s", self.name, y0)
        if self.mother and self.father:
            self.mother.setY0(y0)
            self.father.setY0(y0 + self._vpadding + self.mother.subTreeHeight)
            # sodd formula need for better precision
            self._box.y0 = (
                2 * self.mother.textbox.y0
                + self.mother.textbox.height
                + 2 * self.father.textbox.y0
                + self.father.textbox.height
                - 2 * self.textbox.height
            ) / 4
        else:
            self._box.y0 = y0


class AncestorTree:
    """Class implementing layout of ancestor trees.

    Parameters
    ----------
    person : `ged4py.model.Individual`
        Corresponding individual, may be ``None``.
    max_gen : `int`
        Maximum number of generations to plot, default is 4.
    width : `ged2doc.size.Size`, optional
        Specification for plot width, accepts anything convertible to
        `ged2doc.size.Size`.
    gen_dist : `ged2doc.size.Size`, optional
        Distance between generations, accepts anything convertible to
        `ged2doc.size.Size`.
    font_size :  `ged2doc.size.Size`, optional
        Font size, accepts anything convertible to `ged2doc.size.Size`.
    """

    def __init__(
        self,
        person: model.Individual | None,
        max_gen: int = 4,
        width: Size | str = "5in",
        gen_dist: Size | str = "12pt",
        font_size: Size | str = "10pt",
    ):
        self.max_gen = max_gen
        self._width = Size(width)
        self._height = Size()
        self.gen_dist = Size(gen_dist)
        self.font_size = Size(font_size)
        self.root = None

        def _genDepth(person: model.Individual | None, max_gen: int) -> int:
            """Return number known generations for a person."""
            if not person:
                return 0
            if max_gen == 0:
                return 0
            return max(_genDepth(person.father, max_gen - 1), _genDepth(person.mother, max_gen - 1)) + 1

        def _boxes(box: TreeNode) -> Iterator[TreeNode]:
            """Generate nodes for person parents, returns None for unknown
            parent.
            """
            yield box
            if box.mother:
                for p in _boxes(box.mother):
                    yield p
            if box.father:
                for p in _boxes(box.father):
                    yield p

        # get the number of generations, limit to max_gen
        ngen = _genDepth(person, self.max_gen)
        _log.debug("parent_tree: person = %s", person)
        _log.debug("parent_tree: ngen = %d", ngen)

        # if no parents then tree is empty
        if ngen < 2:
            return

        # calculate horizontal size of each box
        box_width = (self._width - (self.max_gen - 1) * self.gen_dist - Size("4pt")) / self.max_gen
        max_box_width = (self._width - (ngen - 1) * self.gen_dist - Size("4pt")) / ngen

        # build tree
        self.root = self._makeTree(person, 0, ngen, box_width, max_box_width)

        # add small padding, get full height
        if self.root:
            self._height = self.root.subTreeHeight + Size("4pt")
            self.root.setY0("2pt")

        # update box width for every generation and calculate total width
        totwidth = Size("2pt")  # extra 1pt to avoid cropping
        for gen in range(ngen):
            assert self.root is not None
            gen_width = max(pbox.textbox.width for pbox in _boxes(self.root) if pbox.generation == gen)
            for pbox in _boxes(self.root):
                if pbox.generation == gen:
                    pbox.textbox.width = gen_width
                    pbox.textbox.x0 = totwidth
                    _log.debug("parent_tree: %s", pbox.textbox)
            totwidth += gen_width + self.gen_dist
        totwidth -= self.gen_dist
        totwidth += Size("2pt")  # extra 1pt to avoid cropping
        self._width = totwidth
        _log.debug("parent_tree: size = %s x %s", self._width, self._height)

    @property
    def width(self) -> Size:
        """Full width of the tree (`ged2doc.size.Size`)."""
        return self._width

    @property
    def height(self) -> Size:
        """Full height of the tree (`ged2doc.size.Size`)."""
        return self._height

    def visit(self, visitor: AncestorTreeVisitor) -> None:
        """Visit every node and edge in a tree.

        Parameters
        ----------
        visitor : `AncestorTreeVisitor`
            Tree visitor.
        """
        if self.root:
            self._visit(visitor, self.root)

    def _visit(self, visitor: AncestorTreeVisitor, node: TreeNode) -> None:
        """Visit nodes recursively."""
        visitor.visitNode(node)
        if node.mother:
            self._visit(visitor, node.mother)
            visitor.visitMotherEdge(node, node.mother)
        if node.father:
            self._visit(visitor, node.father)
            visitor.visitFatherEdge(node, node.father)

    def _makeTree(
        self, person: model.Individual | None, gen: int, max_gen: int, box_width: Size, max_box_width: Size
    ) -> TreeNode | None:
        """Recursively generate tree of TreeNode instances.

        For internal use only.
        """
        if gen < max_gen:
            mother_tree = None
            father_tree = None
            if person and (person.mother or person.father):
                mother_tree = self._makeTree(person.mother, gen + 1, max_gen, box_width, max_box_width)
                father_tree = self._makeTree(person.father, gen + 1, max_gen, box_width, max_box_width)
            box = TreeNode(
                person, gen, mother_tree, father_tree, box_width, max_box_width, self.font_size, self.gen_dist
            )
            return box
        return None


class AncestorTreeVisitor(metaclass=abc.ABCMeta):
    """Interface for tree visitors.

    Instances of this class can be passed to `AncestorTree.visit()` method to
    iterate over all nodes and edges in an ancestor tree.
    """

    @abc.abstractmethod
    def visitNode(self, node: TreeNode) -> None:
        """Visitor method for a node in tree.

        Parameters
        ----------
        node : `TreeNode`
            Tree node.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def visitMotherEdge(self, node: TreeNode, parent_node: TreeNode) -> None:
        """Visitor method for an edge leading from node to its mother.

        It is guaranteed that `visitNode` is called for both nodes before
        this method is called.

        Parameters
        ----------
        node : `TreeNode`
            Tree node.
        parent_node : `TreeNode`
            Parent tree node.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def visitFatherEdge(self, node: TreeNode, parent_node: TreeNode) -> None:
        """Visitor method for an edge leading from node to its mother.

        It is guaranteed that `visitNode` is called for both nodes before
        this method is called.

        Parameters
        ----------
        node : `TreeNode`
            Tree node.
        parent_node : `TreeNode`
            Parent tree node.
        """
        raise NotImplementedError()
