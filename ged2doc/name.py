"""Various methods for manipulating/formatting names.
"""

from __future__ import absolute_import, division, print_function

# Names can be rendered in different formats
FMT_SURNAME_FIRST = 0x1  # Smith Jane
FMT_COMMA = 0x2  # Smith, Jane -- only if surname is first
FMT_MAIDEN = 0x4  # Jane Smith (Sawyer)   -- maiden name
FMT_MAIDEN_ONLY = 0x8  # Jane Sawyer   -- maiden name only
FMT_CAPITAL = 0x10  # Jane SMITH   -- surname is all caps


def name_fmt(name, fmt=0x0):
    """Format name for output.

    :param name: :py:class:`ged4py.model.Name` instance.
    :param int fmt: Bitmask of FMT_* flags.
    :return: Formatted name representation.
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
