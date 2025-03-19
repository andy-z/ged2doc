from __future__ import annotations

from typing import NamedTuple

from ged2doc.size import Size
from ged2doc.ancestor_tree import AncestorTree, AncestorTreeVisitor, TreeNode
from pytest import approx


class MockName(NamedTuple):
    first: str
    surname: str
    maiden: str | None


class MockIndividual(NamedTuple):
    name: MockName
    mother: MockIndividual | None
    father: MockIndividual | None
    xref_id: str | None


class MockTreeVisitor(AncestorTreeVisitor):
    node_count = 0
    edge_count = 0

    def visitNode(self, node: TreeNode) -> None:
        self.node_count += 1

    def visitMotherEdge(self, node: TreeNode, parentNode: TreeNode) -> None:
        self.edge_count += 1

    def visitFatherEdge(self, node: TreeNode, parentNode: TreeNode) -> None:
        self.edge_count += 1


def test_tree_node() -> None:
    kw = dict(box_width=Size(2), max_box_width=Size(3), font_size=Size("10pt"), gen_dist=Size("10pt"))

    oneLineHeightPt = 10.0 + 2 * 4.0  # 4pt is default padding
    twoLineHeightPt = 2 * 10.0 + 1.5 + 2 * 4.0  # 4pt is default padding

    # single person, no parents
    person = MockIndividual(
        name=MockName(first="John", surname="Smith", maiden=None), mother=None, father=None, xref_id="@id0@"
    )
    node = TreeNode(person, 0, motherNode=None, fatherNode=None, **kw)  # type: ignore[arg-type]
    assert node.person is person  # type: ignore[comparison-overlap]
    assert node.mother is None
    assert node.father is None
    assert node.name == "John Smith"
    assert node.textbox.width == Size(2)
    assert node.textbox.height.pt == oneLineHeightPt
    assert node.subTreeHeight.pt == oneLineHeightPt
    assert node.textbox.x0 == Size()
    assert node.textbox.y0 == Size()

    # person, one parent
    mother = MockIndividual(
        name=MockName(first="Jane", surname="Smith", maiden="Huang"),
        mother=None,
        father=None,
        xref_id="@id1@",
    )
    person = MockIndividual(
        name=MockName(first="John", surname="Smith", maiden=None), mother=mother, father=None, xref_id="@id0@"
    )
    mother_node = TreeNode(mother, 1, motherNode=None, fatherNode=None, **kw)  # type: ignore[arg-type]
    father_node = TreeNode(None, 1, motherNode=None, fatherNode=None, **kw)
    node = TreeNode(person, 0, motherNode=mother_node, fatherNode=father_node, **kw)  # type: ignore[arg-type]
    assert node.person is person  # type: ignore[comparison-overlap]
    assert node.mother is mother_node
    assert node.mother.person is mother  # type: ignore[comparison-overlap]
    assert node.father is father_node
    assert node.father.person is None
    assert node.name == "John Smith"
    assert node.mother.name == "Jane Smith"
    assert node.subTreeHeight.pt == approx(2 * oneLineHeightPt + TreeNode._vpadding.pt)
    assert node.textbox.x0 == Size()
    assert node.textbox.midy.pt == approx(node.subTreeHeight.pt / 2)

    # person, two parents, father's name is very long
    mother = MockIndividual(
        name=MockName(first="Jane", surname="Smith", maiden="Huang"),
        mother=None,
        father=None,
        xref_id="@id1@",
    )
    father = MockIndividual(
        name=MockName(
            first="King Huan Carlos TwentySecond", surname="Smith-and-sometimes-Ivanov", maiden=None
        ),
        mother=None,
        father=None,
        xref_id="@id1@",
    )
    person = MockIndividual(
        name=MockName(first="John", surname="Smith", maiden=None), mother=mother, father=None, xref_id="@id0@"
    )
    mother_node = TreeNode(mother, 1, motherNode=None, fatherNode=None, **kw)  # type: ignore[arg-type]
    father_node = TreeNode(father, 1, motherNode=None, fatherNode=None, **kw)  # type: ignore[arg-type]
    node = TreeNode(person, 0, motherNode=mother_node, fatherNode=father_node, **kw)  # type: ignore[arg-type]
    assert node.person is person  # type: ignore[comparison-overlap]
    assert node.mother is mother_node
    assert node.mother.person is mother  # type: ignore[comparison-overlap]
    assert node.father is father_node
    assert node.father.person is father  # type: ignore[comparison-overlap]
    assert node.name == "John Smith"
    assert node.mother.name == "Jane Smith"
    assert node.father.name == "King Huan Carlos TwentySecond Smith-and-sometimes-Ivanov"
    assert node.father.textbox.height.pt == approx(twoLineHeightPt)
    assert node.subTreeHeight.pt == approx(twoLineHeightPt + oneLineHeightPt + TreeNode._vpadding.pt)
    assert node.textbox.midy.pt == approx((node.mother.textbox.midy.pt + node.father.textbox.midy.pt) / 2)


def test_tree() -> None:
    oneLineHeightPt = 10.0 + 2 * 4.0  # 4pt is default padding

    # single person, no parents
    person = MockIndividual(
        name=MockName(first="John", surname="Smith", maiden=None), mother=None, father=None, xref_id="@id0@"
    )
    tree = AncestorTree(person)  # type: ignore[arg-type]
    assert tree.root is None

    # person, one parent
    mother = MockIndividual(
        name=MockName(first="Jane", surname="Smith", maiden="Huang"),
        mother=None,
        father=None,
        xref_id="@id1@",
    )
    person = MockIndividual(
        name=MockName(first="John", surname="Smith", maiden=None), mother=mother, father=None, xref_id="@id0@"
    )
    tree = AncestorTree(person)  # type: ignore[arg-type]
    assert tree.root is not None
    assert tree.width.pt == approx(((5 * 72 - 3 * 12 - 4) / 4) * 2 + 12 + 4)
    assert tree.height.pt == approx(2 * oneLineHeightPt + TreeNode._vpadding.pt + 4)

    visitor = MockTreeVisitor()
    tree.visit(visitor)
    assert visitor.node_count == 3
    assert visitor.edge_count == 2
