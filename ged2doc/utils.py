"""Various utility methods."""

from __future__ import annotations

import locale
import logging
import mimetypes
from collections.abc import Iterator
from typing import TYPE_CHECKING, BinaryIO, cast

from PIL import Image

if TYPE_CHECKING:
    from ged4py import model

_log = logging.getLogger(__name__)


def resize(
    size: tuple[int | float, int | float], max_size: tuple[int | float, int | float], reduce_only: bool = True
) -> tuple[int | float, int | float]:
    """Resize a box so that it fits into other box and keeps aspect ratio.

    Parameters
    ----------
    size : `tuple`
        Box to resize, (width, height). Elements of tuple are either numbers
        or `ged2doc.size.Size` instances.
    max_size : `tuple`
        Box to fit new resized box into, (width, height).
    reduce_only : `bool`
        If True (default) and size is smaller than max_size then return
        original box.

    Returns
    -------
    width, height
        Tuple (width, height) representing resized box. Type of the elements
        is the same as the type of the ``size`` elements.
    """
    w, h = size
    if reduce_only and w <= max_size[0] and h <= max_size[1]:
        return size

    h = max_size[1]
    w = (h * size[0]) / size[1]
    if w > max_size[0]:
        w = max_size[0]
        h = (w * size[1]) / size[0]
    return w, h


def person_image_file(person: model.Individual) -> str | None:
    """Find primary person image file name.

    Scans INDI's OBJE records and finds "best" FILE record from those.

    Parameters
    ----------
    person : `ged4py.model.Individual`
            INDI record representation.

    Returns
    -------
    file_name : `str` or ``None``
        String with file name or ``None``.

    Notes
    -----
    OBJE record contains one (in 5.5) or few (in 5.5.1) related multimedia
    files. In 5.5 file contents can be embedded as BLOB record though we do
    not support this. In 5.5.1 file name is stored in a record.

    In 5.5.1 OBJE record is supposed to have structure::

        OBJE
          +1 FILE <MULTIMEDIA_FILE_REFN>    {1:M}
            +2 FORM <MULTIMEDIA_FORMAT>     {1:1}
                +3 MEDI <SOURCE_MEDIA_TYPE> {0:1}
          +1 TITL <DESCRIPTIVE_TITLE>       {0:1}
          +1 _PRIM {Y|N}                    {0:1}

    Some applications which claim to be  5.5.1 version still store OBJE
    record in 5.5-like format::

        OBJE
          +1 FILE <MULTIMEDIA_FILE_REFN>    {1:1}
          +1 FORM <MULTIMEDIA_FORMAT>       {1:1}
          +1 TITL <DESCRIPTIVE_TITLE>       {0:1}
          +1 _PRIM {Y|N}                    {0:1}

    This method returns the name of the FILE corresponding to _PRIM=Y, or if
    there is no _PRIM record then the first FILE record. Potentially we also
    need to look at MEDI record to only chose image type, but I have not seen
    examples of MEDI use yet, so for now I only select FORM which correspond
    to images.
    """
    first: str | None = None
    for obje in person.sub_tags("OBJE"):
        # assume by default it is some image format
        objform_rec = obje.sub_tag("FORM")
        objform = cast(str, objform_rec.value if objform_rec else "jpg")

        primary_rec = obje.sub_tag("_PRIM")
        primary = primary_rec.value == "Y" if primary_rec is not None else False

        files = obje.sub_tags("FILE")
        for file in files:
            form_rec = file.sub_tag("FORM")
            form = cast(str, form_rec.value if form_rec is not None else objform)

            if form.lower() in ("jpg", "gif", "tif", "bmp"):
                if primary:
                    return file.value  # type: ignore
                elif not first:
                    first = file.value  # type: ignore

    return first


def languages() -> list[str]:
    """Return list of supported languages.

    This should correspond to the existing translations and needs to be
    updated when new translation is added.

    Returns
    -------
    languages : `list` [ `str` ]
    """
    return ["en", "ru", "pl", "cz"]


def system_lang() -> str:
    """Try to guess system language.

    Returns
    -------
    language : `str`
        Guessed system language, "en" is returned as a fallback.
    """
    loclang, _ = locale.getlocale()
    if loclang:
        for lang in languages():
            if loclang.startswith(lang):
                return lang
    return "en"


def embed_ref(xref_id: str, name: str) -> str:
    """Return encoded person reference.

    Encoded reference consists of ASCII character ``SOH`` (``0x01``) followed
    by reference ID, ``STX`` (``0x02``), person name, and ``ETX`` (``0x03``).

    Parameters
    ----------
    xref_id : `str`
        Reference ID for a person.
    name : `str`
        Person name.
    """
    return "\001" + "person." + xref_id + "\002" + name + "\003"


def split_refs(text: str) -> Iterator[tuple[str, str] | str]:
    """Split text with embedded references into a sequence of text
    and references.

    Reference is returned as tuple (id, name).

    Yields
    ------
    item : `str` or `tuple`
        Pieces of text and references.
    """
    while True:
        pos = text.find("\x01")
        if pos < 0:
            if text:
                yield text
            break
        else:
            if pos > 0:
                yield text[:pos]
            text = text[pos + 1 :]
            pos = text.find("\x03")
            ref_text = text[:pos]
            text = text[pos + 1 :]
            ref, _, name = ref_text.partition("\x02")
            yield (ref, name)


def img_mime_type(img: Image.Image) -> str | None:
    """Return image MIME type or ``None``.

    Parameters
    ----------
    img: `PIL.Image`
        PIL Image object.

    Returns
    -------
    mime_type : `str`
        MIME string like "image/jpg" or ``None``.
    """
    if img.format:
        ext = "." + img.format
        return mimetypes.types_map.get(ext.lower())
    return None


def img_resize(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Resize image to fit given size.

    Image is resized only if it is larger than `size`, otherwise
    unmodified image is returned.

    Parameters
    ----------
    img : `PIL.Image`
        PIL Image object.
    size : `tuple`
        Final image size (width, height)

    Returns
    -------
    image : `PIL.Image`
        Resized image.
    """
    newsize = resize(img.size, size)
    newsize = (int(newsize[0]), int(newsize[1]))
    if newsize != img.size:
        # means size was reduced
        _log.debug("Resize image to %s", newsize)
        img = img.resize(newsize, Image.Resampling.LANCZOS)

    return img


def img_save(img: Image.Image, file: BinaryIO) -> str | None:
    """Save image into output file.

    This method automatically chooses the best file format for output.

    Parameters
    ----------
    img : `PIL.Image`
        PIL Image object.
    file
        File object to write output to.

    Returns
    -------
    mime_type : `str`
        MIME type of the output image.
    """
    if img.format:
        # save in the original format
        img.save(file, img.format)
        return img_mime_type(img)
    elif img.mode in ("P", "RGBA"):
        # palette or transparency - save it as PNG
        img.save(file, "PNG", optimize=True)
        return mimetypes.types_map.get(".png")
    else:
        # everyhting else is stored as JPEG
        img.save(file, "JPEG", optimize=True)
        return mimetypes.types_map.get(".jpeg")
