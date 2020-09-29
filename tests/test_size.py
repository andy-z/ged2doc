"""Unit test for size module
"""

import pytest

from ged2doc.size import Size, String2Size


def test_size_1_val():

    assert Size().value == 0.
    assert Size().dpi == 96.
    assert Size(1).value == 1.
    assert Size(1).dpi == 96.
    assert Size(1.).value == 1.
    assert Size(1., 300.).value == 1.
    assert Size(1., 300.).dpi == 300.


def test_size_2_str():
    assert Size("1").value == 1.
    assert Size("1").dpi == 96.
    assert Size("1", 300).dpi == 300.
    assert Size("0.01").value == 0.01
    assert Size("100").value == 100.

    assert Size("72pt").value == 1.
    assert Size("6.6pt").value == 6.6 / 72
    assert Size("2.54cm").value == 1
    assert Size("2.54mm").value == 0.1

    assert Size("96px").value == 1.
    assert Size("300px", 300).value == 1.

    with pytest.raises(TypeError):
        Size([])
    with pytest.raises(ValueError):
        Size('12pf')


def test_size_3_arith():

    s1 = Size("144pt", 100.)
    s2 = Size("72pt", 200.)

    s3 = s1 + s2
    assert s3.value == 3.
    assert s3.dpi == 100.
    s3 = s2 + s1
    assert s3.value == 3.
    assert s3.dpi == 200.
    s3 = s1 - s2
    assert s3.value == 1.
    assert s3.dpi == 100.
    s3 = s2 - s1
    assert s3.value == -1.
    assert s3.dpi == 200.
    s3 = s1 * 3
    assert s3.value == 6.
    assert s3.dpi == 100.
    s3 = 3 * s1
    assert s3.value == 6.
    assert s3.dpi == 100.
    s3 = s1 / 4
    assert s3.value == 0.5
    assert s3.dpi == 100.

    s3 = s1 + 1
    assert s3.value == 3
    assert s3.dpi == 100.
    s3 = 1 + s1
    assert s3.value == 3
    assert s3.dpi == 100.
    s3 = "72pt" + s1
    assert s3.value == 3
    assert s3.dpi == 100.
    s3 = s1 + "72pt"
    assert s3.value == 3
    assert s3.dpi == 100.
    s3 = s1 + "100px"
    assert s3.value == 3
    assert s3.dpi == 100.
    s3 = "100px" + s1
    assert s3.value == 3
    assert s3.dpi == 100.

    s3 = s1 - 1
    assert s3.value == 1
    assert s3.dpi == 100.
    s3 = 3 - s1
    assert s3.value == 1
    assert s3.dpi == 100.
    s3 = "216pt" - s1
    assert s3.value == 1
    assert s3.dpi == 100.
    s3 = s1 - "72pt"
    assert s3.value == 1
    assert s3.dpi == 100.
    s3 = "300px" - s1
    assert s3.value == 1
    assert s3.dpi == 100.
    s3 = s1 - "100px"
    assert s3.value == 1
    assert s3.dpi == 100.

    s3 = s1 * 5.25
    assert s3.value == 10.5
    assert s3.dpi == 100.
    s3 = s1 / 2.5
    assert s3.value == 0.8
    assert s3.dpi == 100.
    s3 = (s1 * 5.25) // 3
    assert s3.value == 3.
    assert s3.dpi == 100.


def test_size_4_meth():

    s1 = Size("144pt")
    assert s1.pt == 144
    assert s1.inches == 2
    assert s1.mm == 25.4 * 2
    assert s1.px == 96. * 2

    s1 = Size("2in", 300)
    assert s1.pt == 144
    assert s1.inches == 2
    assert s1.mm == 25.4 * 2
    assert s1.px == 300. * 2


def test_size_5_copy():

    s1 = Size("144pt")
    s2 = Size(s1 * 2)
    assert s2.value == 4
    assert s2.dpi == 96.

    s2 = Size(s2 * 2, 150.)
    assert s2.value == 8
    assert s2.dpi == 150.

    s2 = Size(s2 * 2)
    assert s2.value == 16
    assert s2.dpi == 150.

    s2 = Size(s2 * 2, 300)
    assert s2.value == 32
    assert s2.dpi == 300.


def test_size_6_str():

    assert str(Size()) == "0.0in"
    assert str(Size(2)) == "2.0in"
    assert str(Size("1.5in")) == "1.5in"


def test_size_7_xor():

    assert Size(1) ^ "in" == "1in"
    assert Size("2in") ^ "pt" == "144pt"
    assert Size("30mm") ^ "cm" == "3cm"
    assert Size("72pt") ^ "mm" == "25.4mm"
    assert Size("25.4mm") ^ "px" == "96px"


def test_size_8_cmp():

    assert Size("1in") < Size("73pt")
    assert Size("1in") > Size("71pt")
    assert Size("1in") <= Size("72pt")


def test_str2size_1_default_unit():

    str2size = String2Size()
    assert str2size("96").inches == 96.

    str2size = String2Size(default_unit="px")
    assert str2size("96").px == 96.

    str2size = String2Size(default_unit="in")
    assert str2size("96").inches == 96.

    str2size = String2Size(default_unit="in")
    assert str2size("72pt").inches == 1.


def test_str2size_2_accepted():

    str2size = String2Size(accepted_units=["pt", "in"])
    assert str2size("72pt").pt == 72.
    assert str2size("1").inches == 1.
    assert str2size("2in").inches == 2.
    with pytest.raises(ValueError):
        str2size("96px")

    # default unit is "in"
    str2size = String2Size(accepted_units=["mm", "cm"])
    with pytest.raises(ValueError):
        str2size("1")


def test_str2size_3_rejected():

    str2size = String2Size(rejected_units=["pt", "in"])
    assert str2size("96px").px == 96.
    with pytest.raises(ValueError):
        str2size("1in")
    with pytest.raises(ValueError):
        str2size("72pt")
    with pytest.raises(ValueError):
        str2size("2")
