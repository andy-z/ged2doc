# -*- coding: utf-8 -*-

"""Unit test for utils module
"""

from ged2doc import utils
from ged4py import model


def test_001_resize_reduceonly():

    bound = (10, 10)

    box = (1, 1)
    resized = utils.resize(box, bound, reduce_only=True)
    assert resized == box

    box = (100, 100)
    resized = utils.resize(box, bound, reduce_only=True)
    assert resized == bound

    box = (1, 100)
    resized = utils.resize(box, bound, reduce_only=True)
    assert resized == (0.1, 10)

    box = (100, 1)
    resized = utils.resize(box, bound, reduce_only=True)
    assert resized == (10, .1)


def test_002_resize():

    bound = (10, 10)

    box = (1, 1)
    resized = utils.resize(box, bound, reduce_only=False)
    assert resized == bound

    box = (100, 100)
    resized = utils.resize(box, bound, reduce_only=False)
    assert resized == bound

    box = (1, 2)
    resized = utils.resize(box, bound, reduce_only=False)
    assert resized == (5, 10)

    box = (2, 1)
    resized = utils.resize(box, bound, reduce_only=False)
    assert resized == (10, 5)


def test_050_person_image_file():
    """Test person_image_file method."""

    # FORM is subordinate of OBJE
    dialect = model.Dialect.MYHERITAGE
    form = model.make_record(2, None, "FORM", "JPG",
                             [], 0, dialect, None).freeze()
    file = model.make_record(
        2, None, "FILE", "/path/to/file.jpeg", [], 0, dialect, None).freeze()
    obje = model.make_record(1, None, "OBJE", "", [
                             file, form], 0, dialect, None).freeze()
    person = model.make_record(0, None, "INDI", "", [
                               obje], 0, dialect, None).freeze()
    assert utils.person_image_file(person) == "/path/to/file.jpeg"

    # FORM is subordinate of FILE
    dialect = model.Dialect.MYHERITAGE
    form = model.make_record(3, None, "FORM", "JPG",
                             [], 0, dialect, None).freeze()
    file = model.make_record(
        2, None, "FILE", "/path/to/file.jpeg", [form], 0, dialect, None).freeze()
    obje = model.make_record(1, None, "OBJE", "", [
                             file], 0, dialect, None).freeze()
    person = model.make_record(0, None, "INDI", "", [
                               obje], 0, dialect, None).freeze()
    assert utils.person_image_file(person) == "/path/to/file.jpeg"

    # FORM is subordinate of OBJE
    dialect = model.Dialect.MYHERITAGE
    form = model.make_record(2, None, "FORM", "WAV",
                             [], 0, dialect, None).freeze()
    file = model.make_record(
        2, None, "FILE", "/path/to/file.wav", [], 0, dialect, None).freeze()
    obje = model.make_record(1, None, "OBJE", "", [
                             file, form], 0, dialect, None).freeze()
    person = model.make_record(0, None, "INDI", "", [
                               obje], 0, dialect, None).freeze()
    assert utils.person_image_file(person) is None

    # FORM is subordinate of FILE
    dialect = model.Dialect.MYHERITAGE
    form = model.make_record(3, None, "FORM", "WAV",
                             [], 0, dialect, None).freeze()
    file = model.make_record(
        2, None, "FILE", "/path/to/file.wav", [form], 0, dialect, None).freeze()
    obje = model.make_record(1, None, "OBJE", "", [
                             file], 0, dialect, None).freeze()
    person = model.make_record(0, None, "INDI", "", [
                               obje], 0, dialect, None).freeze()
    assert utils.person_image_file(person) is None

    # _PRIM flag is set on one of the two OBJE
    dialect = model.Dialect.MYHERITAGE
    form = model.make_record(2, None, "FORM", "JPG",
                             [], 0, dialect, None).freeze()
    file = model.make_record(
        2, None, "FILE", "/path/to/file.jpg", [], 0, dialect, None).freeze()
    obje1 = model.make_record(1, None, "OBJE", "", [
                              file, form], 0, dialect, None).freeze()
    prim_y = model.make_record(
        2, None, "_PRIM", "Y", [], 0, dialect, None).freeze()
    form = model.make_record(2, None, "FORM", "JPG",
                             [], 0, dialect, None).freeze()
    file = model.make_record(
        2, None, "FILE", "/path/to/file_primary.jpg", [], 0, dialect, None).freeze()
    obje2 = model.make_record(1, None, "OBJE", "", [
                              file, form, prim_y], 0, dialect, None).freeze()
    person = model.make_record(0, None, "INDI", "", [
                               obje1, obje2], 0, dialect, None).freeze()
    assert utils.person_image_file(person) == "/path/to/file_primary.jpg"
    person = model.make_record(0, None, "INDI", "", [
                               obje2, obje1], 0, dialect, None).freeze()
    assert utils.person_image_file(person) == "/path/to/file_primary.jpg"

    # multiple FILEs per OBJE, choose JPG over WAV
    dialect = model.Dialect.MYHERITAGE
    form = model.make_record(3, None, "FORM", "JPG",
                             [], 0, dialect, None).freeze()
    file1 = model.make_record(
        2, None, "FILE", "/path/to/file.jpeg", [form], 0, dialect, None).freeze()
    form = model.make_record(3, None, "FORM", "WAV",
                             [], 0, dialect, None).freeze()
    file2 = model.make_record(
        2, None, "FILE", "/path/to/file.wav", [form], 0, dialect, None).freeze()
    obje = model.make_record(1, None, "OBJE", "", [
                             file1, file2], 0, dialect, None).freeze()
    person = model.make_record(0, None, "INDI", "", [
                               obje], 0, dialect, None).freeze()
    assert utils.person_image_file(person) == "/path/to/file.jpeg"
    obje = model.make_record(1, None, "OBJE", "", [
                             file2, file1], 0, dialect, None).freeze()
    person = model.make_record(0, None, "INDI", "", [
                               obje], 0, dialect, None).freeze()
    assert utils.person_image_file(person) == "/path/to/file.jpeg"


def test_60_embed_ref():
    """test for embed_ref method"""

    eref = utils.embed_ref("id", "name")
    assert eref == "\001person.id\002name\003"

    eref = utils.embed_ref("id", "Иван Иванович")
    assert eref == "\001person.id\002Иван Иванович\003"


def test_61_split_refs():
    """test for split_refs method"""

    text = "\001person.id\002name\003"
    items = list(utils.split_refs(text))
    assert items == [("person.id", "name")]

    text = "\001person.id\002Иван Иванович\003"
    items = list(utils.split_refs(text))
    assert items == [("person.id", "Иван Иванович")]

    text = "text before \001person.id\002name\003 text after"
    items = list(utils.split_refs(text))
    assert items == ["text before ", ("person.id", "name"), " text after"]

    text = "\001person.id\002name\003 text after"
    items = list(utils.split_refs(text))
    assert items == [("person.id", "name"), " text after"]

    text = "text before \001person.id\002name\003"
    items = list(utils.split_refs(text))
    assert items == ["text before ", ("person.id", "name")]

    text = "text1\001person.id\002name\003text2\001p.id2\002name2\003text3"
    items = list(utils.split_refs(text))
    assert items == ["text1", ("person.id", "name"), "text2",
                     ("p.id2", "name2"), "text3"]
