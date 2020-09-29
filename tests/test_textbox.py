"""Unit test for textbox module
"""

from ged2doc.size import Size
from ged2doc.textbox import TextBox


def test_1_constr():

    box = TextBox(x0=Size(1), y0=Size(2), width=Size(4), height=Size(8), text='abc')
    assert box.x0.value == 1
    assert box.y0.value == 2
    assert box.width.value == 4
    assert box.height.value == 8
    assert box.text == 'abc'
    assert box.lines == ['abc']


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
    assert box.x0.value == 0.
    assert box.y0.value == 0.
    assert box.width.pt == 36
    assert box.height.pt == 10 * 2 + 3 + 2 * 5
    assert box.lines == ['abcdefg', 'ABCDEFG']
    lines_pos = list(box.lines_pos())
    assert lines_pos == [
        ("abcdefg", (Size("18pt"), Size("15pt"))),
        ("ABCDEFG", (Size("18pt"), Size("28pt"))),
    ]
