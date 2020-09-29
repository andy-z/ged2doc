"""Unit test for input module
"""

import os
import pytest
import shutil
import tempfile
import zipfile

from ged2doc import input as ged2doc_input


@pytest.fixture
def files_on_disk():
    """Fixture that creates directory tree with files on disk
    """
    tmpdir = tempfile.mkdtemp()
    files = [("xxx.ged",),
             ("dir1", "one.jpg"),
             ("dir1", "dir2", "one.jpg"),
             ("dir1", "two.gif"),
             ("dir2", "two.gif")]
    for fname in files:
        fdir = os.path.join(tmpdir, *fname[:-1])
        if fdir != tmpdir:
            try:
                os.makedirs(os.path.join(tmpdir, *fname[:-1]))
            except OSError:
                pass
        path = os.path.join(tmpdir, *fname)
        with open(path, "wb") as fobj:
            data = '/'.join(fname).encode('ascii')
            fobj.write(data)

    yield tmpdir

    shutil.rmtree(tmpdir)


@pytest.fixture
def files_in_zip():
    """Fixture that creates zip archive with few files
    """
    fd, aname = tempfile.mkstemp(".zip")
    os.close(fd)
    with zipfile.ZipFile(aname, "w") as archive:
        files = [("xxx.ged",),
                 ("dir1", "one.jpg"),
                 ("dir1", "dir2", "one.jpg"),
                 ("dir1", "two.gif"),
                 ("dir2", "two.gif")]
        for fname in files:
            path = '/'.join(fname)
            data = path.encode('ascii')
            archive.writestr(path, data)

    yield aname

    os.unlink(aname)


def checkFilesLoc(loc):
    ged = loc.open_gedcom()
    assert ged.read() == b"xxx.ged"

    with pytest.raises(ged2doc_input.MultipleMatchesError):
        img = loc.open_image("one.jpg")

    with pytest.raises(ged2doc_input.MultipleMatchesError):
        img = loc.open_image("two.gif")

    img = loc.open_image("dir1/one.jpg")
    assert img.read() == b"dir1/one.jpg"

    img = loc.open_image("dir2/one.jpg")
    assert img.read() == b"dir1/dir2/one.jpg"

    img = loc.open_image("dir1/dir2/one.jpg")
    assert img.read() == b"dir1/dir2/one.jpg"

    img = loc.open_image(r"d:\x\y\z\dir2\one.jpg")
    assert img.read() == b"dir1/dir2/one.jpg"

    img = loc.open_image("dir1/two.gif")
    assert img.read() == b"dir1/two.gif"

    img = loc.open_image("dir2/two.gif")
    assert img.read() == b"dir2/two.gif"

    img = loc.open_image("/home/joe/Pictures/dir2/two.gif")
    assert img.read() == b"dir2/two.gif"

    assert loc.open_image("three.pdf") is None


def test_FSLocator_name(files_on_disk):
    """Test for _FSLocator with file name.
    """
    tmpdir = files_on_disk

    loc = ged2doc_input._FSLocator(os.path.join(tmpdir, "xxx.ged"), tmpdir)
    checkFilesLoc(loc)


def test_FSLocator_fobj(files_on_disk):
    """Test for _FSLocator with file object.
    """
    tmpdir = files_on_disk

    with open(os.path.join(tmpdir, "xxx.ged"), 'rb') as fobj:
        loc = ged2doc_input._FSLocator(fobj, tmpdir)
        checkFilesLoc(loc)


def test_make_file_locator_name(files_on_disk):
    """Test for make_file_locator with file name.
    """
    tmpdir = files_on_disk

    loc = ged2doc_input.make_file_locator(os.path.join(tmpdir, "xxx.ged"), "", tmpdir)
    assert isinstance(loc, ged2doc_input._FSLocator)
    checkFilesLoc(loc)


def test_make_file_locator_fobj(files_on_disk):
    """Test for make_file_locator with file object.
    """
    tmpdir = files_on_disk

    with open(os.path.join(tmpdir, "xxx.ged"), 'rb') as fobj:
        loc = ged2doc_input.make_file_locator(fobj, "", tmpdir)
        assert isinstance(loc, ged2doc_input._FSLocator)
        checkFilesLoc(loc)


def test_ZipLocator_name(files_in_zip):
    """Test for _ZipLocator with file name.
    """
    archive = files_in_zip

    loc = ged2doc_input._ZipLocator(archive, "*.ged", None)
    checkFilesLoc(loc)

    loc = ged2doc_input._ZipLocator(archive, "*.ged*", None)
    checkFilesLoc(loc)

    loc = ged2doc_input._ZipLocator(archive, "*.egd", None)
    assert loc.open_gedcom() is None

    loc = ged2doc_input._ZipLocator(archive, "*.gif", None)
    with pytest.raises(ged2doc_input.MultipleMatchesError):
        assert loc.open_gedcom()


def test_ZipLocator_fobj(files_in_zip):
    """Test for _ZipLocator with file object.
    """
    archive = files_in_zip
    with open(archive, 'rb') as fobj:

        loc = ged2doc_input._ZipLocator(fobj, "*.ged", None)
        checkFilesLoc(loc)


def test_make_file_locator_zip_name(files_in_zip):
    """Test for make_file_locator with zip file name.
    """
    archive = files_in_zip

    loc = ged2doc_input.make_file_locator(archive, "*.ged", None)
    assert isinstance(loc, ged2doc_input._ZipLocator)
    checkFilesLoc(loc)


def test_make_file_locator_zip_fobj(files_in_zip):
    """Test for make_file_locator with file object.
    """
    archive = files_in_zip

    with open(archive, 'rb') as fobj:
        loc = ged2doc_input.make_file_locator(fobj, "*.ged", None)
        assert isinstance(loc, ged2doc_input._ZipLocator)
        checkFilesLoc(loc)
