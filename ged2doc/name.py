"""Methods for manipulating/formatting names.
"""

import enum


class NameFormat(enum.Flag):
    """Names can be rendered in different formats, this enum defines different
    types of presentations that can also be combined with logical OR (``|``).
    """

    SURNAME_FIRST = 0x1
    """Bit flag for surname-first format (e.g. ``Smith Jane``).
    """
    COMMA = 0x2
    """Bit flag for adding comma in surname-first format (e.g. ``Smith, Jane``).
    """
    MAIDEN = 0x4
    """Bit flag for adding maiden name (e.g. ``Jane Smith (Sawyer)``).
    """
    MAIDEN_ONLY = 0x8
    """Bit flag for using maiden name only (e.g. ``Jane Sawyer``).
    """
    CAPITAL = 0x10
    """Bit flag for rendering surname in capital (e.g. ``Jane SMITH``).
    """


def name_fmt(name, fmt=NameFormat(0)):
    """Format name for output.

    Parameters
    ----------
    name : `ged4py.model.Name`
        Person name.
    fmt : `NameFormat`, optional
        Bitmask combination of `NameFormat` flags.

    Returns
    -------
    name : `str`
        Formatted name representation.
    """
    surname = name.surname
    if fmt & NameFormat.MAIDEN_ONLY:
        surname = name.maiden or name.surname
    elif fmt & NameFormat.MAIDEN:
        surname = name.surname
        if name.maiden:
            if surname:
                surname += ' '
            surname += "(" + name.maiden + ")"
    if fmt & NameFormat.CAPITAL and surname:
        surname = surname.upper()

    if fmt & NameFormat.SURNAME_FIRST:
        if surname and name.given and fmt & NameFormat.COMMA:
            return surname + ', ' + name.given
        if surname and name.given:
            return surname + ' ' + name.given
        else:
            return name.given or surname
    else:
        if surname and name.given:
            return name.given + ' ' + surname
        else:
            return name.given or surname
