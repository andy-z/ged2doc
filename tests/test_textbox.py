"""Unit test for textbox module
"""

from __future__ import absolute_import, division, print_function

from ged2doc.size import Size
from ged2doc.textbox import TextBox


def test_1_constr():

    box = TextBox(x0=Size(1), y0=Size(2), width=Size(4), height=Size(8), text='abc')
    assert box.x0.value == 1
    assert box.y0.value == 2
    assert box.width.value == 4
    assert box.height.value == 8
    assert box.text == 'abc'

def test_2_dim():

    box = TextBox(x0=Size(1), y0=Size(2), width=Size(4), height=Size(8))
    assert box.x1.value == 5
    assert box.y1.value == 10
    assert box.midx.value == 3
    assert box.midy.value == 6

def test_3_split():

    box = TextBox(width='36pt', font_size='10pt')
    lines = box._splitText('abcdefg')
    assert lines == ['abcdefg']
    lines = box._splitText('abcdefg ABCDEFG')
    assert lines == ['abcdefg', 'ABCDEFG']
    lines = box._splitText('abcdefg     ABCDEFG')
    assert lines == ['abcdefg', 'ABCDEFG']
    lines = box._splitText('abc defg   ABCD EFG')
    assert lines == ['abc', 'defg', 'ABCD', 'EFG']

def test_4_reflow():

    box = TextBox(width='36pt', text='abcdefg ABCDEFG', font_size='10pt',
                  line_spacing='3pt', padding='5pt')
    box.reflow()
    assert box.height.pt == 10 * 2 + 3 + 2 * 5

def test_5_xml():

    box = TextBox(width='36pt', text='abcdefg ABCDEFG', font_size='10pt',
                  line_spacing='3pt', padding='5pt')
    box.reflow()
    xml = '\n'.join([elem.xml() for elem in box.svg(units="pt")])
    assert xml == """\
<rect x="0pt" y="0pt" width="36pt" height="33pt" />
<text font-size="10pt" text-anchor="middle">
<tspan x="18pt" y="15pt">
abcdefg
</tspan>
<tspan x="18pt" y="28pt">
ABCDEFG
</tspan>
</text>"""
