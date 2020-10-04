"""Methods for manipulating/formatting names.
"""

# Names can be rendered in different formats
FMT_SURNAME_FIRST = 0x1
"""Bit flag for surname-first format (e.g. ``Smith Jane``).
"""
FMT_COMMA = 0x2
"""Bit flag for adding comma in surname-first format (e.g. ``Smith, Jane``).
"""
FMT_MAIDEN = 0x4
"""Bit flag for adding maiden name (e.g. ``Jane Smith (Sawyer)``).
"""
FMT_MAIDEN_ONLY = 0x8
"""Bit flag for using maiden name only (e.g. ``Jane Sawyer``).
"""
FMT_CAPITAL = 0x10
"""Bit flag for rendering surname in capital (e.g. ``Jane SMITH``).
"""


def name_fmt(name, fmt=0x0):
    """Format name for output.

    Parameters
    ----------
    name : `ged4py.model.Name`
        Person name.
    fmt : `int`
        Bitmask combination of ``FMT_*`` flags.

    Returns
    -------
    name : `str`
        Formatted name representation.
    """
    surname = name.surname
    if fmt & FMT_MAIDEN_ONLY:
        surname = name.maiden or name.surname
    elif fmt & FMT_MAIDEN:
        surname = name.surname
        if name.maiden:
            if surname:
                surname += ' '
            surname += "(" + name.maiden + ")"
    if fmt & FMT_CAPITAL and surname:
        surname = surname.upper()

    if fmt & FMT_SURNAME_FIRST:
        if surname and name.given and fmt & FMT_COMMA:
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
