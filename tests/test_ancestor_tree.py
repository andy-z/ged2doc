
from collections import namedtuple
from pytest import approx

from ged2doc.size import Size
from ged2doc.ancestor_tree import AncestorTree, AncestorTreeVisitor, TreeNode


MockName = namedtuple("MockName", "first surname maiden")
MockIndividual = namedtuple("MockIndividual", "name mother father xref_id")


class MockTreeVisitor(AncestorTreeVisitor):

    node_count = 0
    edge_count = 0

    def visitNode(self, node):
        self.node_count += 1

    def visitMotherEdge(self, node, parentNode):
        self.edge_count += 1

    def visitFatherEdge(self, node, parentNode):
        self.edge_count += 1


def test_tree_node():

    kw = dict(box_width=Size(2), max_box_width=Size(3), font_size="10pt", gen_dist="10pt")

    oneLineHeightPt = 10. + 2 * 4.  # 4pt is default padding
    twoLineHeightPt = 2 * 10. + 1.5 + 2 * 4.  # 4pt is default padding

    # single person, no parents
    person = MockIndividual(name=MockName(first="John", surname="Smith", maiden=None),
                            mother=None, father=None, xref_id="@id0@")
    node = TreeNode(person, 0, motherNode=None, fatherNode=None, **kw)
    assert node.person is person
    assert node.mother is None
    assert node.father is None
    assert node.name == "John Smith"
    assert node.textbox.width == Size(2)
    assert node.textbox.height.pt == oneLineHeightPt
    assert node.subTreeHeight.pt == oneLineHeightPt
    assert node.textbox.x0 == Size()
    assert node.textbox.y0 == Size()

    # person, one parent
    mother = MockIndividual(name=MockName(first="Jane", surname="Smith", maiden="Huang"),
                            mother=None, father=None, xref_id="@id1@")
    person = MockIndividual(name=MockName(first="John", surname="Smith", maiden=None),
                            mother=mother, father=None, xref_id="@id0@")
    mother_node = TreeNode(mother, 1, motherNode=None, fatherNode=None, **kw)
    father_node = TreeNode(None, 1, motherNode=None, fatherNode=None, **kw)
    node = TreeNode(person, 0, motherNode=mother_node, fatherNode=father_node, **kw)
    assert node.person is person
    assert node.mother is mother_node
    assert node.mother.person is mother
    assert node.father is father_node
    assert node.father.person is None
    assert node.name == "John Smith"
    assert node.mother.name == "Jane Smith"
    assert node.subTreeHeight.pt == approx(2 * oneLineHeightPt + TreeNode._vpadding.pt)
    assert node.textbox.x0 == Size()
    assert node.textbox.midy.pt == approx(node.subTreeHeight.pt / 2)

    # person, two parents, father's name is very long
    mother = MockIndividual(name=MockName(first="Jane", surname="Smith", maiden="Huang"),
                            mother=None, father=None, xref_id="@id1@")
    father = MockIndividual(name=MockName(first="King Huan Carlos TwentySecond",
                                          surname="Smith-and-sometimes-Ivanov", maiden=None),
                            mother=None, father=None, xref_id="@id1@")
    person = MockIndividual(name=MockName(first="John", surname="Smith", maiden=None),
                            mother=mother, father=None, xref_id="@id0@")
    mother_node = TreeNode(mother, 1, motherNode=None, fatherNode=None, **kw)
    father_node = TreeNode(father, 1, motherNode=None, fatherNode=None, **kw)
    node = TreeNode(person, 0, motherNode=mother_node, fatherNode=father_node, **kw)
    assert node.person is person
    assert node.mother is mother_node
    assert node.mother.person is mother
    assert node.father is father_node
    assert node.father.person is father
    assert node.name == "John Smith"
    assert node.mother.name == "Jane Smith"
    assert node.father.name == "King Huan Carlos TwentySecond Smith-and-sometimes-Ivanov"
    assert node.father.textbox.height.pt == approx(twoLineHeightPt)
    assert node.subTreeHeight.pt == approx(twoLineHeightPt + oneLineHeightPt + TreeNode._vpadding.pt)
    assert node.textbox.midy.pt == approx((node.mother.textbox.midy.pt + node.father.textbox.midy.pt) / 2)


def test_tree():

    oneLineHeightPt = 10. + 2 * 4.  # 4pt is default padding

    # single person, no parents
    person = MockIndividual(name=MockName(first="John", surname="Smith", maiden=None),
                            mother=None, father=None, xref_id="@id0@")
    tree = AncestorTree(person)
    assert tree.root is None

    # person, one parent
    mother = MockIndividual(name=MockName(first="Jane", surname="Smith", maiden="Huang"),
                            mother=None, father=None, xref_id="@id1@")
    person = MockIndividual(name=MockName(first="John", surname="Smith", maiden=None),
                            mother=mother, father=None, xref_id="@id0@")
    tree = AncestorTree(person)
    assert tree.root is not None
    assert tree.width.pt == approx(((5 * 72 - 3 * 12 - 4) / 4) * 2 + 12 + 4)
    assert tree.height.pt == approx(2 * oneLineHeightPt + TreeNode._vpadding.pt + 4)

    visitor = MockTreeVisitor()
    tree.visit(visitor)
    assert visitor.node_count == 3
    assert visitor.edge_count == 2
