"""Tests for `ged2doc.cli` module."""

import os
import tempfile

import pytest

from ged2doc.cli import main
from ged2doc.i18n import DATE_FORMATS
from ged2doc.utils import languages


@pytest.fixture
def data_folder() -> str:
    """Return path for data folder."""
    tests = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(tests, "data")


@pytest.mark.parametrize("type", ["odt", "html"])
@pytest.mark.parametrize("lang", languages())
@pytest.mark.parametrize("datefmt", DATE_FORMATS)
def test_writer(data_folder: str, type: str, lang: str, datefmt: str) -> None:
    """Test CLI to convert test file."""
    input = os.path.join(data_folder, "allged.ged")
    with tempfile.TemporaryDirectory() as tmp_folder:
        output = os.path.join(tmp_folder, "output." + type)
        rc = main(["-t", type, "-l", lang, "-d", datefmt, input, output])
        assert rc == 0
