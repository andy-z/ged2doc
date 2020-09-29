"""Unit test for image types.
"""

import io
import pytest

from PIL import Image
from ged2doc import utils


def _make_image(mode, size):
    """Makes an Image object with given pixel mode and size.
    """
    img = Image.new(mode, size)
    return img


def _make_img_file(mode, size, fmt, **kwargs):
    """Makes image file of given size, mode, and format.
    """
    img = _make_image(mode, size)
    imgfile = io.BytesIO()
    img.save(imgfile, fmt, **kwargs)
    imgfile.seek(0)
    return imgfile


def test_000_assumptions():
    "Test for general assumptions about PIL images"

    # check that image format is as expected after reading data from file
    formats = {'JPEG': ['RGB', 'L', 'CMYK'],
               'GIF': ['RGB:P', 'RGBA:P', 'L:P'],
               'PNG': ['1', 'L', 'P', 'RGB', 'RGBA']}
    for fmt, modes in formats.items():
        for mode in modes:
            wmode, _, rmode = mode.partition(':')
            if not rmode:
                rmode = wmode
            img = Image.open(_make_img_file(wmode, (100, 100), fmt))
            if rmode == 'P':
                assert img.palette is not None
            else:
                assert img.palette is None
            assert (img.format, img.mode) == (fmt, rmode)


def test_001_palette():
    "Testing palette images"

    img = Image.open(_make_img_file("RGB", (100, 100), "GIF"))
    assert img.mode == 'P'
    assert img.palette is not None

    imgfile = io.BytesIO()
    # cannot write P mode as JPEG
    with pytest.raises(IOError):
        img.save(imgfile, 'JPEG')

    # but should work OK with PNG
    img.save(imgfile, 'PNG')


def test_002_mime():
    "Testing MIME type guessing"

    img = Image.open(_make_img_file("RGB", (100, 100), "GIF"))
    assert utils.img_mime_type(img) == "image/gif"

    img = Image.open(_make_img_file("RGB", (100, 100), "JPEG"))
    assert utils.img_mime_type(img) == "image/jpeg"

    img = Image.open(_make_img_file("RGB", (100, 100), "PNG"))
    assert utils.img_mime_type(img) == "image/png"

    img = _make_image("RGB", (100, 100))
    assert utils.img_mime_type(img) is None


def test_003_img_resize():
    "Testing utils.img_resize() method."

    # palette image, no resize
    img = Image.open(_make_img_file("RGB", (100, 100), "GIF"))
    assert img.mode == 'P'
    newimg = utils.img_resize(img, (200, 200))
    assert newimg is img

    # reduce
    newimg = utils.img_resize(img, (50, 50))
    assert newimg is not img
    assert newimg.size == (50, 50)
    assert newimg.format is None
    assert newimg.mode == 'P'

    newimg = utils.img_resize(img, (200, 80))
    assert newimg is not img
    assert newimg.size == (80, 80)

    # RGBA image, no resize
    img = Image.open(_make_img_file("RGBA", (100, 100), "PNG"))
    assert img.mode == 'RGBA'
    newimg = utils.img_resize(img, (200, 200))
    assert newimg is img

    # reduce
    newimg = utils.img_resize(img, (50, 50))
    assert newimg is not img
    assert newimg.size == (50, 50)
    assert newimg.format is None
    assert newimg.mode == 'RGBA'

    newimg = utils.img_resize(img, (200, 80))
    assert newimg is not img
    assert newimg.size == (80, 80)


def test_004_img_save():
    "Testing utils.img_save() method."

    # keep original format
    img = Image.open(_make_img_file("RGB", (100, 100), "GIF"))
    assert img.mode == 'P'
    assert img.format == 'GIF'
    imgfile = io.BytesIO()
    utils.img_save(img, imgfile)
    newimg = Image.open(imgfile)
    assert newimg.format == 'GIF'

    # keep original format
    img = Image.open(_make_img_file("RGB", (100, 100), "JPEG"))
    assert img.mode == 'RGB'
    assert img.format == 'JPEG'
    imgfile = io.BytesIO()
    utils.img_save(img, imgfile)
    newimg = Image.open(imgfile)
    assert newimg.format == 'JPEG'

    # P and RGBA mode becomes PNG
    for mode in ('P', 'RGBA'):
        img = _make_image(mode, (100, 100))
        assert img.format is None
        imgfile = io.BytesIO()
        utils.img_save(img, imgfile)
        newimg = Image.open(imgfile)
        assert newimg.format == 'PNG'

    # anything else becomes JPEG
    for mode in ('1', 'L', 'RGB', 'CMYK', 'YCbCr'):
        img = _make_image(mode, (100, 100))
        assert img.format is None
        imgfile = io.BytesIO()
        utils.img_save(img, imgfile)
        newimg = Image.open(imgfile)
        assert newimg.format == 'JPEG'
