"""Various utility methods.
"""

from __future__ import absolute_import, division, print_function

def resize(size, max_size, reduce_only=True):
    """Resize a box so that it fits into other box and keeps aspect ratio.

    Parameters
    ----------
    size : tuple (width, height)
        Box to resize.
    max_size : tuple (width, height)
        Box to fit new resized box into.
    reduce_only : boolean, optional
        If True (default) and size is smaller than max_size then return
        original box.

    Returns
    -------
    Tuple (width, height) representing resized box.
    """

    w, h = size
    if reduce_only and w <= max_size[0] and h <= max_size[1]:
        return size

    h = max_size[1]
    w = (h * size[0]) / size[1]
    if w > max_size[0]:
        w = max_size[0]
        h = (w * size[1]) / size[0]
    return w, h
