"""Module which produces HTML output.
"""

from __future__ import absolute_import, division, print_function

__all__ = ["HtmlWriter"]

import logging

from ged4py.parser import GedcomReader

_log = logging.getLogger(__name__)


class HtmlWriter(object):
    """Abstract interface for file locator instances.
    """

    def __init__(self, flocator, options):

        self._floc = flocator
        self._options = options

    def save(self, output):
        """Produce output at given destination.

        :param str output: Location of output file.
        """

        gfile = self._floc.open_gedcom()
        if not gfile:
            raise OSError("Failed to locate input file")

        encoding = self._options.get('encoding')
        errors = self._options.get('encoding_errors', 'strict')
        reader = GedcomReader(gfile, encoding=encoding, errors=errors)
