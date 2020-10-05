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

__all__ = ["make_file_locator", "FileLocator", "MultipleMatchesError"]

import abc
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


class FileLocator(metaclass=abc.ABCMeta):
    """Abstract interface for file locator instances.
    """

    @abc.abstractmethod
    def open_gedcom(self):
        """Returns file object for the input GEDCOM file.

        If no GEDCOM file is found `None` is returned. If more than one
        file is found than :py:exc:`MultipleMatchesError` exception is raised.
        Can throw other exceptions, e.g. if file cannot be open.

        Returned file object will be open in binary mode and will support
        ``seek()`` and ``tell()`` methods. Note that this may be a temporary
        file which will be deleted after file is closed.

        Returns
        -------
        file
            File object open in binary mode supporting ``seek()`` and
            ``tell()`` methods.

        Raises
        ------
        MultipleMatchesError
            Raised if more than one file file is found.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def open_image(self, name):
        """Returns open file object for the named image file.

        If image file is not found `None` is returned. If more than one
        matching file is found than :py:exc:`MultipleMatchesError` exception
        is raised. Can throw other exceptions if file cannot be open.

        Note that this file object may not support all operations (it may be
        an object inside zip archive for example) so you may need to copy it if
        you want full file protocol support.

        Parameters
        ----------
        name : `str`
            Name of the image file to open. This can be relative or absolute
            path name. Usually this is the name that is stored in GEDCOM file
            and it can use separator character which is different from a
            system reading this file.

        Returns
        -------
        image
            File object open in binary mode, only ``read()`` method is
            guaranteed to work.

        Raises
        ------
        MultipleMatchesError
            Raised if more than one file is found.
        """
        raise NotImplementedError("Method open_image() is not implemented")


class _Path:
    """Internal representation of the (relative) file path.

    In this representation path is a just a sequence of path components -
    zero or more folders and a file name.

    Parameters
    ----------
    components : `list` [ `str` ]
        List of (unicode) strings representing path.
    dirname : `str`, optional
        Optional prefix directory.
    """

    def __init__(self, components, dirname=None):
        self.components = components[:]
        self.dirname = dirname

    @classmethod
    def from_path(cls, path, dirname=None):
        """Construct instance of this type from full path name.

        Parameters
        ----------
        path : `str`
            String representing path.
        dirname : `str`, optional
            Optional prefix directory.
        """
        # Trouble here is that GEDCOM file can be prepared on different type
        # of system with different path separator. First try to convert path
        # into canonical form using slashes as separators and stripping
        # Windows drive.
        if len(path) > 2 and path[0].isalpha() and path[1] == ':':
            # strip windows drive name
            path = path[2:]
        path = path.replace('\\', '/').lstrip('/')

        # split file name into components
        return cls(path.split('/'), dirname)

    def match_rank(self, other):
        """Returns match "rank" with the other path.

        Rank is a count of identical matching components at the end of paths.

        Parameters
        ----------
        other : `_Path`
            Path instance to match.

        Returns
        -------
        rank : `int`
            Match rank.
        """
        if self.components[-1] != other.components[-1]:
            return 0
        rank = 0
        for comp1, comp2 in zip(reversed(self.components),
                                reversed(other.components)):
            if comp1 != comp2:
                break
            rank += 1
        return rank

    def os_path(self):
        """Return full path of the file as a string.

        Returns
        -------
        path : `str`
        """
        if self.dirname:
            return os.path.join(self.dirname, *self.components)
        else:
            return os.path.join(*self.components)

    def __str__(self):
        return "/".join(self.components)


class _FileSearch(metaclass=abc.ABCMeta):
    """Implementation of recursive file search in a folder tree.

    This is an abstract class which can match files but does not know how
    to build folder tree. Sub classes must implement `_paths()` method which
    returns the list of file "paths" to match.
    """

    _path_cache = None

    @staticmethod
    def _enc(name):
        """If string is Unicode encode it into UTF-8"""
        if isinstance(name, str):
            name = name.encode("utf_8")
        return name

    @staticmethod
    def _enc_list(path):
        """If strings are Unicode encode them into UTF-8"""
        return [_FileSearch._enc(comp) for comp in path]

    def find_file(self, name):
        """Returns file path for the named file.

        Parameters
        ----------
        name : `str`
            File name to search, this is usually the path as it comes directly
            from GEDCOM file.
        """

        path = _Path.from_path(name)

        # for each match assign its rank
        matches = []
        max_rank = 1  # need at least basename match
        for cand in self.paths:
            rank = path.match_rank(cand)
#             _log.debug("find_file: %s and %s: rank=%s", path, cand, rank)
            if rank > max_rank:
                matches = [cand]
                max_rank = rank
            elif rank == max_rank:
                matches += [cand]

        if not matches:
            _log.debug("_FileSearch.find_file: nothing found")
            return
        elif len(matches) > 1:
            _log.debug("_FileSearch.find_file: many files found: %s",
                       matches)
            raise MultipleMatchesError('More than one file matches name ' +
                                       str(path) + ": " +
                                       ', '.join(str(m) for m in matches))
        else:
            _log.debug("_FileSearch.find_file: found: %s", matches[0])
            return matches[0]

    @property
    def paths(self):
        """The list of all path names (_Path instances) to use for matching.
        """
        if self._path_cache is None:
            self._path_cache = self._paths()
        return self._path_cache

    @abc.abstractmethod
    def _paths(self):
        """Return list of file paths (_Path instances), must be implemented
        in a subclass.

        Returns
        -------
        paths : `list` [ `_Path` ]
        """
        raise NotImplementedError()


class _FSFileSearch(_FileSearch):
    """Implementation of recursive file search on file system.

    One complication here is encoding, `os.listdir` is returning stings/bytes
    of the same type as its argument (self._path). To avoid complications we
    convert self._path to unicode using UTF-8 encoding. This could fail in
    some cases.

    Parameters
    ----------
    path : `str`
        Directory on a file system to search for files.
    """

    def __init__(self, path):

        if path is not None and not isinstance(path, str):
            path = path.decode("utf_8")
        self._path = path

    def _paths(self):
        # docstring inherited from _FileSearch class
        _log.debug("_FSFileSearch.find_file: recursively scan "
                   "directory %r", self._path)
        if self._path is None:
            # do not search
            return []
        return list(self._scan(self._path))

    def _scan(self, path, current=None):
        """Recursively scan folder, return each file path as a list of
        its components.

        Parameters
        ----------
        path : `str`
            Filesystem directory to scan.
        current : `list` [ `str` ], optional
            Current context, to support recursion.

        Yields
        ------
        path : `_Path`
        """
        for fname in os.listdir(path):
            fpath = os.path.join(path, fname)
            components = (current or []) + [fname]
            if os.path.isdir(fpath):
                # scan recursively
                for p in self._scan(fpath, components):
                    yield p
            elif os.path.isfile(fpath):
                p = _Path(components, self._path)
#                 _log.debug("_scan: %s", p)
                yield p


class _ZIPFileSearch(_FileSearch):
    """Implementation of recursive file search on file system.

    Parameters
    ----------
    toc : `list` [ `str` ]
        List of entries in ZIP archive.
    """
    def __init__(self, toc):
        self._toc = toc

    def _paths(self):
        # docstring inherited from _FileSearch class
        paths = []
        for entry in self._toc:
            paths.append(_Path([comp for comp in entry.split('/') if comp]))
        return paths


class _FSLocator(FileLocator):
    """Implementation of `FileLocator` interface which can find files located
    on a regular file system.

    Parameters
    ----------
    input_file : `str`
        Path of the input GEDCOM file or file object. If argument is a file
        object then it must support ``seek()`` method and be open in a binary
        mode.
    image_path : `str`
        Directory on a file system where images are found. Images could be
        located in sub-directories of the given path. If ``image_path`` is
        ``None`` then file system is not searched for files. If ``image_path``
        is an empty string then current directory is searched.
    """
    def __init__(self, input_file, image_path=None):

        self._input_file = input_file
        if image_path is None:
            # use parent folder of GEDCOM file for image search
            if hasattr(input_file, 'read'):
                # it's probably a file
                image_path = getattr(input_file, "name", None)
            else:
                image_path = input_file
            if image_path:
                image_path = os.path.dirname(os.path.abspath(image_path))
            _log.debug("_FSLocator: use image folder: %r", image_path)
        self._image_path = image_path
        self._fsearch = _FSFileSearch(image_path)

    def open_gedcom(self):
        # docstring inherited from base class
        _log.debug("_FSLocator.open_gedcom")
        if hasattr(self._input_file, 'read'):
            # it's likely a file
            return self._input_file
        return io.open(self._input_file, 'rb')

    def open_image(self, name):
        # docstring inherited from base class

        # `name` could be an absolute or relative path name, usually this is
        # the name given in GEDCOM file. GEDCOM file can be prepared on a
        # a different type of system where file names can use different
        # separators. This method first tries to open the file using argument
        # as a file name, if that does not succeed then it strips folder part
        # from file name and tries to search recursively for that file name
        # in the configured folder.
        _log.debug("_FSLocator.open_image: find image %s", name)

        # first, if file name looks like absolute path (on current OS)
        # try unmodified name
        if os.path.isabs(name):
            try:
                _log.debug('_ZipLocator.open_image: Trying FS path %s', name)
                return open(name, 'rb')
            except IOError:
                pass
        else:
            # if path looks like relative path try to open it relative to image
            # search path
            if self._image_path:
                try:
                    path = os.path.join(self._image_path, name)
                    _log.debug('_ZipLocator.open_image: Trying FS path %s',
                               name)
                    return open(path, 'rb')
                except IOError:
                    pass

        # Otherwise try to search in the image folder.
        fname = self._fsearch.find_file(name)
        if fname is not None:
            return open(fname.os_path(), 'rb')


class _ZipLocator(FileLocator):
    """Implementation of `FileLocator` interface which can find files located
    in zip archive.

    Parameters
    ----------
    input_file : `str`
        Path of the input ZIP file or file object.
    file_name_pattern : `str`
        Name pattern (in ``fnmatch`` syntax) to search for a GEDCOM file.
    image_path : `str`
        Directory on a filesystem where images are found. Images could be
        located in sub-directories of the given path. Images are searched
        inside ZIP archive and then in ``image_path``. If ``image_path`` is
        ``None`` then filesystem is not searched for files. If ``image_path``
        is an empty string then current directory is searched.
    """
    def __init__(self, input_file, file_name_pattern, image_path):
        self._zip = zipfile.ZipFile(input_file, 'r')
        self._toc = self._zip.namelist()
        self._pattern = file_name_pattern
        self._zipsearch = _ZIPFileSearch(self._toc)
        self._fsearch = _FSFileSearch(image_path)

    def open_gedcom(self):
        # docstring inherited from base class
        matches = [f for f in self._toc if fnmatch.fnmatch(f, self._pattern)]
        if not matches:
            return None
        if len(matches) > 1:
            raise MultipleMatchesError('Multiple matching files found in '
                                       'archive: ' + ' '.join(matches))
        member = matches[0]
        _log.debug("_ZipLocator.open_gedcom: %r", member)

        # wee need a file on disk which supports seek, open in binary mode
        fobj = tempfile.NamedTemporaryFile("w+b",
                                           suffix=os.path.basename(member))
        with self._zip.open(member, 'r') as src:
            shutil.copyfileobj(src, fobj)
        fobj.seek(0)
        return fobj

    def open_image(self, name):
        # docstring inherited from base class
        _log.debug("_ZipLocator.open_image: find image %s", name)

        _log.debug('_ZipLocator.open_image: Trying archive name %r', name)
        fname = self._zipsearch.find_file(name)
        if fname:
            _log.debug("_ZipLocator.open_image: found in ZIP: %r", fname)
            return self._zip.open(str(fname), 'r')

        # if file name looks like absolute path (on current OS)
        # try unmodified name
        if os.path.isabs(name):
            try:
                _log.debug('_ZipLocator.open_image: Trying FS path %s', name)
                return open(name, 'rb')
            except IOError:
                pass

        # search on filesystem
        _log.debug('_ZipLocator.open_image: Trying FS name %s', name)
        fname = self._fsearch.find_file(name)
        if fname is not None:
            return open(fname.os_path(), 'rb')


def make_file_locator(input_file, file_name_pattern, image_path):
    """Create and return file locator instance

    For a given input file (which can be GEDCOM file or ZIP archive) return
    corresponding file locator object (instance of :py:class:`FileLocator`
    type).

    Parameters
    ----------
    input_file
        Path of the input file or file object, can be a ZIP archive or a
        GEDCOM file. If argument is a file object then it must support
        ``seek()`` method and be open in a binary mode.
    file_name_pattern : `str`
        If input file is a ZIP archive then this pattern is used to search
        for a GEDCOM file in archive. Could be ``"*.ged"`` for example or can
        include more specific pattern.
    image_path : `str`
        Directory on a filesystem where images are found. Images could be
        located in sub-directories of the given path. If ``file_name`` is a
        ZIP archive then images are searched inside ZIP archive and then in
        ``image_path``. If ``image_path`` is ``None`` then filesystem is not
        searched for files. If ``image_path`` is an empty string then current
        directory is searched.

    Returns
    -------
    locator : `FileLocator`
        File locator instance.

    Raises
    ------
    OSError
        Raised if file is not found.
    AttributeError
        Raised if file object is given as input file but it does not support
        ``seek()`` method.
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
