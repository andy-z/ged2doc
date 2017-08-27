"""Unit test for size module
"""

from __future__ import absolute_import, division, print_function

__all__ = ['SizeUnitTest']

import unittest

from ged2doc.size import Size, String2Size

class SizeUnitTest(unittest.TestCase):

    def test_1_val(self):

        self.assertEqual(Size().value, 0.)
        self.assertEqual(Size(1).value, 1.)
        self.assertEqual(Size(1.).value, 1.)

    def test_2_str(self):
        self.assertEqual(Size("1").value, 1.)
        self.assertEqual(Size("0.01").value, 0.01)
        self.assertEqual(Size("100").value, 100.)

        self.assertEqual(Size("72pt").value, 1.)
        self.assertEqual(Size("6.6pt").value, 6.6 / 72)
        self.assertEqual(Size("2.54cm").value, 1)
        self.assertEqual(Size("2.54mm").value, 0.1)

        self.assertEqual(Size("96px").value, 1.)

        self.assertRaises(TypeError, Size, ([]))
        self.assertRaises(ValueError, Size, ('12pf'))

    def test_3_arith(self):

        s1 = Size("144pt")
        s2 = Size("72pt")

        s3 = s1 + s2
        self.assertEqual(s3.value, 3.)
        s3 = s1 - s2
        self.assertEqual(s3.value, 1.)
        s3 = s1 * 3
        self.assertEqual(s3.value, 6.)
        s3 = 3 * s1
        self.assertEqual(s3.value, 6.)
        s3 = s1 / 4
        self.assertEqual(s3.value, 0.5)

        s3 = s1 + 1
        self.assertEqual(s3.value, 3)
        s3 = 1 + s1
        self.assertEqual(s3.value, 3)
        s3 = "72pt" + s1
        self.assertEqual(s3.value, 3)
        s3 = s1 + "72pt"
        self.assertEqual(s3.value, 3)

        s3 = s1 - 1
        self.assertEqual(s3.value, 1)
        s3 = 3 - s1
        self.assertEqual(s3.value, 1)
        s3 = "216pt" - s1
        self.assertEqual(s3.value, 1)
        s3 = s1 - "72pt"
        self.assertEqual(s3.value, 1)

    def test_4_meth(self):

        s1 = Size("144pt")
        self.assertEqual(s1.pt, 144)
        self.assertEqual(s1.inches, 2)

    def test_5_copy(self):

        s1 = Size("144pt")
        s2 = Size(s1 * 2)
        self.assertEqual(s2.value, 4)

    def test_6_str(self):

        self.assertEqual(str(Size()), "0.0in")
        self.assertEqual(str(Size(2)), "2.0in")
        self.assertEqual(str(Size("1.5in")), "1.5in")

    def test_7_xor(self):

        self.assertEqual(Size(1) ^ "in", "1in")
        self.assertEqual(Size("2in") ^ "pt", "144pt")
        self.assertEqual(Size("30mm") ^ "cm", "3cm")
        self.assertEqual(Size("72pt") ^ "mm", "25.4mm")
        self.assertEqual(Size("25.4mm") ^ "px", "96px")

    def test_8_cmp(self):

        self.assertLess(Size("1in"), Size("73pt"))
        self.assertGreater(Size("1in"), Size("71pt"))
        self.assertLessEqual(Size("1in"), Size("72pt"))


class String2SizeUnitTest(unittest.TestCase):

    def test_1_default_unit(self):

        str2size = String2Size()
        self.assertEqual(str2size("96").inches, 96.)

        str2size = String2Size(default_unit="px")
        self.assertEqual(str2size("96").px, 96.)

        str2size = String2Size(default_unit="in")
        self.assertEqual(str2size("96").inches, 96.)

        str2size = String2Size(default_unit="in")
        self.assertEqual(str2size("72pt").inches, 1.)

    def test_2_accepted(self):

        str2size = String2Size(accepted_units=["pt", "in"])
        self.assertEqual(str2size("72pt").pt, 72.)
        self.assertEqual(str2size("1").inches, 1.)
        self.assertEqual(str2size("2in").inches, 2.)
        self.assertRaises(ValueError, str2size, "96px")

        # default unit is "in"
        str2size = String2Size(accepted_units=["mm", "cm"])
        self.assertRaises(ValueError, str2size, "1")

    def test_3_rejected(self):

        str2size = String2Size(rejected_units=["pt", "in"])
        self.assertEqual(str2size("96px").px, 96.)
        self.assertRaises(ValueError, str2size, "1in")
        self.assertRaises(ValueError, str2size, "72pt")
        self.assertRaises(ValueError, str2size, "2")


if __name__ == "__main__":
    unittest.main(verbosity=2)

