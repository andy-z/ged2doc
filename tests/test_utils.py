"""Unit test for utils module
"""

from __future__ import absolute_import, division, print_function

from ged2doc import utils

def test_1_reduceonly():

    bound = (10, 10)

    box = (1, 1)
    resized = utils.resize(box, bound, reduce_only=True)
    assert resized == box

    box = (100, 100)
    resized = utils.resize(box, bound, reduce_only=True)
    assert resized == bound

    box = (1, 100)
    resized = utils.resize(box, bound, reduce_only=True)
    assert resized == (0.1, 10)

    box = (100, 1)
    resized = utils.resize(box, bound, reduce_only=True)
    assert resized == (10, .1)

def test_2():

    bound = (10, 10)

    box = (1, 1)
    resized = utils.resize(box, bound, reduce_only=False)
    assert resized == bound

    box = (100, 100)
    resized = utils.resize(box, bound, reduce_only=False)
    assert resized == bound

    box = (1, 2)
    resized = utils.resize(box, bound, reduce_only=False)
    assert resized == (5, 10)

    box = (2, 1)
    resized = utils.resize(box, bound, reduce_only=False)
    assert resized == (10, 5)
