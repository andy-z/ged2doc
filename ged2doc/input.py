"""Module which handles input files.

This module is responsible for locating all files (GEDCOM data and images)
given the application inputs. Currently it handles two cases:

  - Input is specified as path to GEDCOM file, that file can contain names
    of image files that are either absolute or relative to directory
    containing GEDCOM file or some other directory. Program options can
    specify directory where images are located.
  - Input file is a ZIP archive that includes both GEDCOM file and files
    with images. Depending on how GEDCOM file and archive were prepared
    names of image files in GEDCOM file can be specified as absolute paths
    to their original location or relative paths to their common directory.

Additional issue to consider is that files can be prepared on a system
which is different from the system where the file is parsed. For example
GEDCOM file could be prepared on Windows machine and names of image files
could be given using Windows path convention (either absolute as
``C:\\Users\\JosephSmith\\Documents\\Pictures\\Family\\Tree\\Me.BMP``
or relative as ``Pictures\\Family\\Tree\\Me.BMP``) and later this GEDCOM
file could be copied to Linux host and processed using ``ged2doc`` package.
Files on Linux machine will have different absolute and possibly relative
paths (and definitely different path separator character).

In case of ZIP archive the names of images in GEDCOM file could be different
from the names in in the archive (e.g. image path in GEDCOM file
``C:\\Users\\JosephSmith\\Documents\\Pictures\\Family\\Tree\\Me.BMP`` could
be stored in ZIP archive as ``Pictures/Family/Tree/Me.BMP``).

Logic in this module is supposed to handle all those possible cases where
names of files in GEDCOM file could be different from their location on a
target storage system.

Typical use cases for GEDCOM file returned by this module is to be passed to
methods in :py:mod:`ged4py` package and that package expects true
filesystem-backed file which supports ``seek()`` and ``tell()`` methods.
Image files do not typically need support for these methods and are usually
read as a byte stream using ``read()`` method. This module returns seek-able
file object open in binary mode for GEDCOM file (meaning that temporary file
on disk may need to be created in some cases) and a "simple" binary stream
for images.
"""

from __future__ import absolute_import, division, print_function

__all__ = ["make_file_locator", "FileLocator", "MultipleMatchesError"]

import errno
import fnmatch
import io
import logging
import os
import shutil
import tempfile
import zipfile


_log = logging.getLogger(__name__)


class MultipleMatchesError(RuntimeError):
    """Class for exceptions generated when there is more than one file
    matching specified criteria.
    """
    pass


class FileLocator(object):
    """Abstract interface for file locator instances.
    """

    def open_gedcom(self):
        """Returns file object for the input GEDCOM file.

        If no GEDCOM file is found `None` is returned. If more than one
        file is found than :py:exc:`MultipleMatchesError` exception is raised.
        Can throw other exceptions, e.g. if file cannot be open.

        Returned file object will be open in binary mode and will support
        ``seek()`` and ``tell()`` methods. Note that this may be a temporary
        file which will be deleted after file is closed.

        :return: File object open in binary mode supporting ``seek()``
                and ``tell()`` methods.
        :raises: :py:exc:`MultipleMatchesError` in case more than one file
                file is found.
        """
        raise NotImplementedError("Method open_gedcom() is not implemented")

    def open_image(self, name):
        """Returns open file object for the named image file.

        If image file is not found `None` is returned. If more than one
        matching file is found than :py:exc:`MultipleMatchesError` exception
        is raised. Can throw other exceptions if file cannot be open.

        Note that this file object may not support all operations (it may be
        an object inside zip archive for example) so you may need to copy it if
        you want full file protocol support.

        :param str name: Name of the image file to open. This can be relative
                or absolute path name. Usually this is the name that is
                stored in GEDCOM file and it can use separator character which
                is different from a system reading this file.
        :return: File object open in binary mode, only ``read()`` method is
                guaranteed to work.
        :raises: :py:exc:`MultipleMatchesError` in case more than one file
                file is found.
        """
        raise NotImplementedError("Method open_image() is not implemented")


class _FSFileSearch(object):
    """Implementation of recursive file search on file system.

    :param str path: Directory on a file system to search for files.
    """

    def __init__(self, path=None):

        self._path = path
        self._files = None

    def find_file(self, name):
        '''Returns file path for the named file.

        One complication here is encoding, `os.walk` is returning stings/bytes
        of the same type as its argument (self._path) and if `name` has
        different type then comparison may fail in some cases. To void
        complications we convert both self._path and `name` to bytes.
        '''

        bname = name
        if isinstance(bname, type(u"")):
            bname = bname.encode("utf_8")

        _log.debug("_FSFileSearch.find_file: find file %s", name)

        if self._files is None:
            self._files = []
            if self._path:
                # make the list of files in the directory and all sub-dirs
                _log.debug("_FSFileSearch.find_file: recursively scan "
                           "directory " + self._path)
                path = self._path
                if isinstance(path, type(u"")):
                    path = path.encode("utf_8")
                self._files = list(os.walk(path))

        matches = [os.path.join(fldr, bname) for fldr, _, files in self._files
                   if bname in files]
        if not matches:
            _log.debug("_FSFileSearch.find_file: nothing found")
            return
        elif len(matches) > 1:
            _log.debug("_FSFileSearch.find_file: many files found: " +
                       str(matches))
            raise MultipleMatchesError('More than file matches name ' + name)
        else:
            _log.debug("_FSFileSearch.find_file: found: %s", matches[0])
            return matches[0]


class _FSLocator(FileLocator):
    """Implementation of FileLocator interface which can find files located
    on a regular file system.

    :param str input_file: Path of the input file or file object, can be a ZIP
            archive or a GEDCOM file. If argument is a file object then it
            must support ``seek()`` method and be open in a binary mode.
    :param str image_path: Directory on a file system where images are found.
            Images could be located in sub-directories of the given path.
            If ``image_path`` is ``None`` then file system is not searched for
            files. If `image_path` is an empty string then current directory is
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
        return io.open(self._input_file, 'rb')

    def open_image(self, name):
        '''Returns file object for the named image file.

        `name` could be an absolute or relative path name, usually this is
        the name given in GEDCOM file. GEDCOM file can be prepared on a
        a different type of system where file names can use different
        separators. This method first tries to open the file using argument
        as a file name, if that does not succeed then it strips folder part
        from file name and tries to search recursively for that file name
        in the configured folder.
        '''

        _log.debug("_FSLocator.open_image: find image %s", name)

        # first try unmodified name
        try:
            _log.debug('_ZipLocator.open_image: Trying FS path %s', name)
            return open(name, 'rb')
        except IOError:
            pass

        # We need basename of the file, trouble here is that GEDCOM file can
        # be prepared on different type of system. For now assume that path
        # separator in GEDCOM can be either slash or backslash
        basename = name.rsplit('/', 1)[-1]
        basename = basename.rsplit('\\', 1)[-1]
        _log.debug('_FSLocator.open_image: Trying base name %s', basename)

        fname = self._fsearch.find_file(basename)
        if fname is not None:
            return open(fname, 'rb')


class _ZipLocator(FileLocator):
    """Implementation of FileLocator interface which can find files located
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
            raise MultipleMatchesError('Multiple matching files found in '
                                       'archive: ' + ' '.join(matches))
        member = matches[0]
        _log.debug("_ZipLocator.open_gedcom: " + member)

        # wee need a file on disk which supports seek, open in binary mode
        fobj = tempfile.NamedTemporaryFile("w+b",
                                           suffix=os.path.basename(member))
        with self._zip.open(member, 'r') as src:
            shutil.copyfileobj(src, fobj)
        fobj.seek(0)
        return fobj

    def open_image(self, name):
        '''Returns file object for the named image file.'''

        _log.debug("_ZipLocator.open_image: find image %s", name)

        # We need basename of the file, trouble here is that GEDCOM file can
        # be prepared on different type of system. For now assume that path
        # separator in GEDCOM can be either slash or backslash
        basename = name.rsplit('/', 1)[-1]
        basename = basename.rsplit('\\', 1)[-1]

        # file names in _toc have slash as separator
        _log.debug('_ZipLocator.open_image: Trying base name %s', basename)
        paths = [f for f in self._toc if f.rsplit('/')[-1] == basename]
        if len(paths) > 1:
            raise MultipleMatchesError('Multiple image files found in archive '
                                       'matching name ' + name)
        if paths:
            _log.debug("_ZipLocator.open_image: found in ZIP: " + paths[0])
            return self._zip.open(paths[0], 'r')

        # first try unmodified name
        try:
            _log.debug('_ZipLocator.open_image: Trying FS path %s', name)
            return open(name, 'rb')
        except IOError:
            pass

        # search on filesystem
        _log.debug('_ZipLocator.open_image: Trying base name %s', basename)
        fname = self._fsearch.find_file(basename)
        if fname is not None:
            return open(fname, 'rb')


def make_file_locator(input_file, file_name_pattern, image_path):
    """Create and return file locator instance

    For a given input file (which can be GEDCOM file or ZIP archive) return
    corresponding file locator object (instance of :py:class:`FileLocator`
    type).

    :param input_file: Path of the input file or file object, can be a ZIP
            archive or a GEDCOM file. If argument is a file object then it
            must support ``seek()`` method and be open in a binary mode.
    :param str file_name_pattern: If input file is a ZIP archive then this
            pattern is used to search for a GEDCOM file in archive. Could
            be "\*.ged" for example or can include more specific pattern.
    :param str image_path: Directory on a filesystem where images are found.
            Images could be located in sub-directories of the given path.
            If `file_name`` is a ZIP archive then images are searched inside
            ZIP archive and then in `image_path`. If `image_path` is
            `None` then filesystem is not searched for files. If
            `image_path` is an empty string then current directory is
            searched.
    :return: :py:class:`FileLocator` instance.
    :raises OSError: if file is not found
    :raises AttributeError: if file object is given as input file but it
            does not support ``seek()`` method.
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
