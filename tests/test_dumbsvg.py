"""Unit test for dumbsvg module
"""

from ged2doc.dumbsvg import Doc, Element, Hyperlink, Line, Rect, Text, Tspan


def test_001_element_noval():
    "Test case for Element class"

    elem = Element('elem')
    assert elem.xml() == "<elem />"

    elem = Element('elem', [("attr", "avalue")])
    assert elem.xml() == '<elem attr="avalue" />'

    elem = Element('elem', [("attr", "avalue"), ("bttr", "bval")])
    assert elem.xml() == '<elem attr="avalue" bttr="bval" />'


def test_002_element_val():
    "Test case for Element class"

    elem = Element('elem', value="some text")
    assert elem.xml() == "<elem>\nsome text\n</elem>"

    elem = Element('elem', [("attr", "avalue")], value="some text")
    assert elem.xml() == '<elem attr="avalue">\nsome text\n</elem>'


def test_003_element_subelem():
    "Test case for Element class"

    elem = Element('elem')
    elem.add(Element('elem2'))
    assert elem.xml() == "<elem>\n<elem2 />\n</elem>"

    elem = Element('elem')
    elem.add(Element('elem2', value="value2"))
    assert elem.xml() == "<elem>\n<elem2>\nvalue2\n</elem2>\n</elem>"

    elem = Element('elem', value="value")
    elem.add(Element('elem2', value="value2"))
    assert elem.xml() == "<elem>\nvalue\n<elem2>\nvalue2\n</elem2>\n</elem>"


def test_010_doc():
    "Test case for Doc class"

    doc = Doc(100, 100)
    doc.add(Element('elem'))
    doc.add(Element('elem2'))
    assert doc.xml() == """\
<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="100" height="100" version="1.1" xmlns="http://www.w3.org/2000/svg" \
xmlns:xlink="http://www.w3.org/1999/xlink">
<elem />
<elem2 />
</svg>"""


def test_020_line():
    "Test case for Line class"

    elem = Line(0, 10, 90, 100)
    assert elem.xml() == '<line x1="0" y1="10" x2="90" y2="100" />'

    elem = Line(0, 10, 90, 100, style="fancy")
    assert elem.xml() == '<line x1="0" y1="10" x2="90" y2="100" style="fancy" />'


def test_030_rect():
    "Test case for Rect class"

    elem = Rect(0, 10, 90, 100)
    assert elem.xml() == '<rect x="0" y="10" width="90" height="100" />'

    elem = Rect(0, 10, 90, 100, style="fancy")
    assert elem.xml() == '<rect x="0" y="10" width="90" height="100" style="fancy" />'


def test_040_text():
    "Test case for Text class"

    elem = Text(value="", font_size=None, text_anchor=None, style=None, class_=None)
    assert elem.xml() == '<text />'

    elem = Text(value="Some text", font_size=None, text_anchor=None, style=None, class_=None)
    assert elem.xml() == '<text>\nSome text\n</text>'

    elem = Text(font_size="10px", text_anchor="middle", style="fancy", class_="fclass")
    assert elem.xml() == '<text font-size="10px" text-anchor="middle" style="fancy" class="fclass" />'


def test_050_tspan():
    "Test case for Tspan class"

    elem = Tspan(x=10, y="20px", value="")
    assert elem.xml() == '<tspan x="10" y="20px" />'

    elem = Tspan(x=10, y="20px", value="Some text")
    assert elem.xml() == '<tspan x="10" y="20px">\nSome text\n</tspan>'


def test_050_hyperlink():
    "Test case for Hyperlink class"

    elem = Hyperlink("link_value")
    assert elem.xml() == '<a xlink:href="link_value" />'

    elem = Hyperlink("link_value")
    elem.add(Text(value="Some text"))
    assert elem.xml() == '<a xlink:href="link_value">\n<text>\nSome text\n</text>\n</a>'
