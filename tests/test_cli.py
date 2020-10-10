"""Tests for `ged2doc.cli` module."""

import os
import pytest
import tempfile

from ged2doc.cli import main
from ged2doc.utils import languages
from ged2doc.i18n import DATE_FORMATS


@pytest.fixture
def data_folder():
    tests = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(tests, "data")


@pytest.mark.parametrize("type", ["odt", "html"])
@pytest.mark.parametrize("lang", languages())
@pytest.mark.parametrize("datefmt", DATE_FORMATS)
def test_writer(data_folder, type, lang, datefmt):
    input = os.path.join(data_folder, "allged.ged")
    with tempfile.TemporaryDirectory() as tmp_folder:
        output = os.path.join(tmp_folder, "output." + type)
        rc = main(["-t", type, "-l", lang, "-d", datefmt, input, output])
        assert rc == 0
