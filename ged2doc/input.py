"""Module which handles input files
"""

from __future__ import absolute_import, division, print_function

__all__ = ["make_file_locator", "MultipleFiles"]

import errno
import fnmatch
import logging
import os
import shutil
import tempfile
import zipfile


_log = logging.getLogger(__name__)


class MultipleFiles(RuntimeError):
    '''Class for exceptions generated when there is more than one file
    matching specified criteria.
    '''
    pass


class _FileLocator(object):
    '''Interface for all kinds of file locators.
    '''

    def open_gedcom(self):
        """Returns file object for the input GEDCOM file.

        If no GEDCOM  file is found the None is returned. If more than one
        file is found than MultipleFiles exception is raised. Can throw other
        exceptions if file cannot be open.

        Returned file object will be open in binary mode. Note that this may
        be a temporary file which will be deleted after file is closed.
        """
        raise NotImplementedError("Method _FileLocator.open_gedcom() is not implemented")

    def open_image(self, name):
        """Returns file object for the named image file.

        If image file is not found the None is returned. If more than one
        matching file is found than MultipleFiles exception is raised. Can
        throw other exceptions if file cannot be open.
        Note that this file object may not support all operations (it may be
        an object inside zip file for example) so you may need to copy it if
        you want full file protocol support.
        """
        raise NotImplementedError("Method _FileLocator.open_image() is not implemented")


class _FSFileSearch(object):
    """Implementation of recursive file search on filesystem.

    :param str path: Directory on a filesystem to search for files.
    """

    def __init__(self, path=None):

        self._path = path
        self._files = None

    def find_file(self, name):
        '''Returns file path for the named file.'''

        _log.debug("_FSFileSearch.find_file: find file %s", name)

        if self._files is None:
            self._files = []
            if self._path:
                # make the list of files in the directory and all sub-directories
                _log.debug("_FSFileSearch.find_file: recursively scan directory " + self._path)
                self._files = list(os.walk(self._path))

        matches = [os.path.join(fldr, name) for fldr, _, files in self._files if name in files]
        if not matches:
            _log.debug("_FSFileSearch.find_file: nothing found")
            return
        elif len(matches) > 1:
            _log.debug("_FSFileSearch.find_file: many files found: " + str(matches))
            raise MultipleFiles('More than file matches name ' + name)
        else:
            _log.debug("_FSFileSearch.find_file: found: " + matches[0])
            return matches[0]


class _FSLocator(_FileLocator):
    """Implementation of _FileLocatorinterface which can find files located
    on a regular filesystem.

    :param str input_file: Path of the input file or file object, can be a ZIP
            archive or a GEDCOM file. If argument is a file object then it
            must support ``seek()`` method and be open in a binary mode.
    :param str file_name_pattern: If input file is a ZIP archive then this
            pattern is used to search for a GEDCOM file in archive
    :param str image_path: Directory on a filesystem where images are found.
            Images could be located in sub-directories of the given path.
            If ``file_name`` is a ZIP archive then images are searched inside
            ZIP archive and then in ``image_path``. If ``image_path`` is
            ``None`` then filesystem is not searched for files. If
            ``image_path`` is an empty string then current directory is
            searched.
    """

    def __init__(self, input_file, image_path=None):

        self._input_file = input_file
        self._fsearch = _FSFileSearch(image_path)

    def open_gedcom(self):
        '''Returns file object for the input GEDCOM file.'''

        _log.debug("_FSLocator.open_gedcom")
        if hasattr(self._input_file, 'read'):
            # it's likely a file
            return self._input_file
        return open(self._input_file, 'rb')

    def open_image(self, name):
        '''Returns file object for the named image file.'''

        _log.debug("_FSLocator.open_image: find image %s", name)
        fname = self._fsearch.find_file(name)
        if fname is not None:
            return open(fname, 'rb')


class _ZipLocator(_FileLocator):
    """Implementation of _FileLocatorinterface which can find files located
    in zip archive.

    :param str file_name: Path of the input ZIP archive
    :param str file_name_pattern: name pattern to search for a GEDCOM file
    :param str image_path: Directory on a filesystem where images are found.
            Images could be located in sub-directories of the given path.
            Images are searched inside ZIP archive and then in ``image_path``.
            If ``image_path`` is ``None`` then filesystem is not searched
            for files. If ``image_path`` is an empty string then current
            directory is searched.
    """

    def __init__(self, file_name, file_name_pattern, image_path):
        self._zip = zipfile.ZipFile(file_name, 'r')
        self._toc = self._zip.namelist()
        self._pattern = file_name_pattern
        self._fsearch = _FSFileSearch(image_path)

    def open_gedcom(self):
        '''Returns file object for the input GEDCOM file.'''

        matches = [f for f in self._toc if fnmatch.fnmatch(f, self._pattern)]
        if not matches:
            return None
        if len(matches) > 1:
            raise MultipleFiles('Multiple matching files found in archive: '
                                + ' '.join(matches))
        member = matches[0]
        _log.debug("_ZipLocator.open_gedcom: " + member)

        # wee need a file on disk which supports seek, open in binary mode
        fobj = tempfile.NamedTemporaryFile("w+b", suffix=os.path.basename(member))
        with self._zip.open(member, 'r') as src:
            shutil.copyfileobj(src, fobj)
        fobj.seek(0)
        return fobj

    def open_image(self, name):
        '''Returns file object for the named image file.'''

        _log.debug("_ZipLocator.open_image: find image %s", name)

        paths = [f for f in self._toc if os.path.basename(f) == name]
        if len(paths) > 1:
            raise MultipleFiles('Multiple image files found in archive matching name ' + name)
        if paths:
            _log.debug("_ZipLocator.open_image: " + paths[0])
            return self._zip.open(paths[0], 'r')

        # search on filesystem
        fname = self._fsearch.find_file(name)
        if fname is not None:
            return open(fname, 'rb')


def make_file_locator(input_file, file_name_pattern, image_path):
    """Create and return file locator instance

    For a given input file (which can be GEDCOM file or ZIP archive) return
    corresponding file locator (file factory) object.

    :param str input_file: Path of the input file or file object, can be a ZIP
            archive or a GEDCOM file. If argument is a file object then it
            must support ``seek()`` method and be open in a binary mode.
    :param str file_name_pattern: If input file is a ZIP archive then this
            pattern is used to search for a GEDCOM file in archive
    :param str image_path: Directory on a filesystem where images are found.
            Images could be located in sub-directories of the given path.
            If ``file_name`` is a ZIP archive then images are searched inside
            ZIP archive and then in ``image_path``. If ``image_path`` is
            ``None`` then filesystem is not searched for files. If
            ``image_path`` is an empty string then current directory is
            searched.
    """

    if zipfile.is_zipfile(input_file):
        return _ZipLocator(input_file, file_name_pattern, image_path)
    elif hasattr(input_file, 'read'):
        if not hasattr(input_file, 'seek'):
            raise AttributeError('File object has no `seek` attribute')
        input_file.seek(0)
        return _FSLocator(input_file, image_path)
    elif os.path.exists(input_file):
        return _FSLocator(input_file, image_path)
    else:
        raise OSError(errno.ENOENT, input_file)
