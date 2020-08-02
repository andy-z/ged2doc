#!/usr/bin/env python

"""Trivial script to debug content of EMF, just in case some poor schmuck
decides to repeat this futile exercise.
"""

from ged2doc.dumbemf import EMF
from ged2doc.size import Size

dpi = 300
width = Size("5in", dpi)
height = Size("2in", dpi)
emf = EMF(width, height)

# emf.text_color(0)

with emf.use_pen("solid", Size("1pt", dpi), 0x000000):
    emf.rectangle(
        Size("1in", dpi),
        Size(".5in", dpi),
        Size("4in", dpi),
        Size("1.5in", dpi),
    )

emf.text_align("c")
fontsize = Size("16pt", dpi)
with emf.use_font(fontsize):
    emf.text(Size("2.5in", dpi), Size("1.25in", dpi), "Test1 Проверка1")

with open("test.emf", "wb") as out:
    out.write(emf.data())
