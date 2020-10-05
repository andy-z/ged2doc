"""Tests for `ged2doc.cli` module."""

import os
import pytest
import shutil
import tempfile

from ged2doc.cli import _make_writer
from ged2doc.utils import languages
from ged2doc.i18n import DATE_FORMATS


@pytest.fixture
def data_folder():
    tests = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(tests, "data")


@pytest.fixture
def tmp_folder():
    """Create temporary folder"""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.mark.parametrize("type", ["odt", "html"])
@pytest.mark.parametrize("lang", languages())
@pytest.mark.parametrize("datefmt", DATE_FORMATS)
def test_writer(data_folder, tmp_folder, type, lang, datefmt):
    input = os.path.join(data_folder, "allged.ged")
    output = os.path.join(tmp_folder, "output." + type)
    args, writer = _make_writer(["-t", type, "-l", lang, "-d", datefmt, input, output])
    writer.save()
