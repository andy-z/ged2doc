"""Various utility methods.
"""

from __future__ import absolute_import, division, print_function

import locale


def resize(size, max_size, reduce_only=True):
    """Resize a box so that it fits into other box and keeps aspect ratio.

    :param tuple size: tuple (width, height) - box to resize.
    :param tuple max_size: tuple (width, height) - box to fit new resized
        box into.
    :param boolean reduce_only: If True (default) and size is smaller than
        max_size then return original box.
    :return: Tuple (width, height) representing resized box.
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


def personImageFile(person):
    """Finds primary person image file name.

    Scans INDI's OBJE records and finds "best" FILE record from those.

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

    :param person: :py:class:`ged4py.model.Individual` instance
    :return: String with file name or None.
    """

    first = None
    for obje in person.sub_tags('OBJE'):

        # assume by default it is some image format
        objform = obje.sub_tag("FORM")
        objform = objform.value if objform else 'jpg'

        primary = obje.sub_tag("_PRIM")
        primary = primary.value == 'Y' if primary is not None else False

        files = obje.sub_tags("FILE")
        for file in files:
            form = file.sub_tag("FORM")
            form = form.value if form is not None else objform

            if form.lower() in ('jpg', 'gif', 'tif', 'bmp'):
                if primary:
                    return file.value
                elif not first:
                    first = file.value

    return first


def languages():
    """Returns list of supported languages.

    This should correspond to the existing translations
    """
    return ['en', 'ru']


def system_lang():
    """Try to guess system language.
    """
    loclang, _ = locale.getdefaultlocale()
    for lang in languages():
        if loclang.startswith(lang):
            return lang
    return "en"


def embed_ref(xref_id, name):
    """Returns encoded person reference.

    Encoded reference consists of ASCII character SOH (\001) followed by
    reference ID, STX (\002), person name, and ETX (\003)
    """
    return "\001" + "person." + xref_id + "\002" + name + "\003"


def split_refs(text):
    """Split text with embedded references into a sequence of text
    and references.

    Reference is returned as tuple (id, name).

    :returns: iterator over pieces of text and references.
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
            text = text[pos + 1:]
            pos = text.find("\x03")
            ref_text = text[:pos]
            text = text[pos + 1:]
            ref, _, name = ref_text.partition("\x02")
            yield (ref, name)
