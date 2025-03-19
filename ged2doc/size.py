"""Module which defines class for manipulating size values."""

from __future__ import annotations

__all__ = ["Size", "SizeLike"]

from typing import TypeAlias

MM_PER_INCH = 25.4
PT_PER_INCH = 72.0

SizeLike: TypeAlias = str | int | float  # noqa: UP040


class Size:
    """Class for specifying size values.

    Size can be specified as a number with units, supported units are ``pt``
    (points), ``in`` (inches), ``cm`` (centimeters), ``mm`` (millimeters), and
    ``px`` (pixels). If units are not specified then inches are assumed.

    Constructor converts input value to a size. If input value has numeric
    type then it is assumed to be size in inches. If input value is a string
    then it should be a floating number followed by optional suffix (one of
    pt, in, mm, cm, px). Without suffix the number gives size in inches.
    Constructor also accepts other ``Size`` instances as an argument which
    copies the size value (but can be use to specify different ``dpi`` value).

    Class supports most of the regular numeric operators so it can be used
    as a numeric value (in inches) in expressions. Operator XOR (^) is used
    for formatting of the size values with the specified unit type, e.g.::

        size = Size("144pt") / 2
        print(size ^ "mm")  # will produce string "25.4mm"

    Parameters
    ----------
    value : `int`, `float`, `str`, or `Size`
        Input value for size.
    dpi : `float`, optional
        Dots-per-inch for converting pixels into other scale. Default is to use
        class attribute `dpi` value.

    Raises
    ------
    ValueError
        Raised if string does not have correct format.
    TypeError
        Raised if input value has unsupported type.
    """

    dpi = 96.0
    """Class constant used for pixels-to-inches conversion, default
    value is 96., it is used as default DPI for ``Size`` instances that
    do not specify explicit ``dpi`` argument
    """

    def __init__(self, value: Size | SizeLike = 0, dpi: float | int | None = None):
        if isinstance(value, str):
            # convert units to inches
            self.dpi = float(dpi) if dpi is not None else Size.dpi
            if value.endswith("pt"):
                self.value = float(value[:-2]) / PT_PER_INCH
            elif value.endswith("in"):
                self.value = float(value[:-2])
            elif value.endswith("cm"):
                self.value = float(value[:-2]) / (MM_PER_INCH / 10)
            elif value.endswith("mm"):
                self.value = float(value[:-2]) / MM_PER_INCH
            elif value.endswith("px"):
                self.value = float(value[:-2]) / self.dpi
            else:
                # without suffix assume it's inches
                self.value = float(value)
        elif isinstance(value, Size):
            self.value = value.value
            self.dpi = float(dpi) if dpi is not None else value.dpi
        else:
            # expect a number
            try:
                self.dpi = float(dpi) if dpi is not None else Size.dpi
                self.value = float(value)
            except (TypeError, ValueError):
                raise TypeError("incorrect type of the argument: " + str(type(value)))

    @property
    def pt(self) -> float:
        """Size in points (`float`)."""
        return self.value * 72.0

    @property
    def px(self) -> int:
        """Size in pixels, (`int`)."""
        return int(round(self.value * self.dpi))

    @property
    def pxf(self) -> float:
        """Size in (fractional) pixels, (`float`)."""
        return self.value * self.dpi

    @property
    def inches(self) -> float:
        """Size in inches, (`float`)."""
        return self.value

    @property
    def mm(self) -> float:
        """Size in millimeters, (`float`)."""
        return self.value * MM_PER_INCH

    def to_dpi(self, dpi: float | int) -> Size:
        """Return copy of itself with updated DPI value.

        This is a convenience method which does the same as `Size(self, dpi)`.
        """
        return Size(self, dpi)

    def __str__(self) -> str:
        """Return string representation, e.g. "12in"."""
        return str(self.value) + "in"

    def __repr__(self) -> str:
        """Return string representation, e.g. Size("12in")."""
        return f"Size({self.value}in)"

    def __lt__(self, other: object) -> bool:
        """Compare two sizes."""
        if not isinstance(other, Size | SizeLike):
            return NotImplemented
        return self.value < self._coerce(other).value

    def __le__(self, other: object) -> bool:
        """Compare two sizes."""
        if not isinstance(other, Size | SizeLike):
            return NotImplemented
        return self.value <= self._coerce(other).value

    def __eq__(self, other: object) -> bool:
        """Compare two sizes."""
        if not isinstance(other, Size | SizeLike):
            return NotImplemented
        return self.value == self._coerce(other).value

    def __ne__(self, other: object) -> bool:
        """Compare two sizes."""
        if not isinstance(other, Size | SizeLike):
            return NotImplemented
        return self.value != self._coerce(other).value

    def __ge__(self, other: object) -> bool:
        """Compare two sizes."""
        if not isinstance(other, Size | SizeLike):
            return NotImplemented
        return self.value >= self._coerce(other).value

    def __gt__(self, other: object) -> bool:
        """Compare two sizes."""
        if not isinstance(other, Size | SizeLike):
            return NotImplemented
        return self.value > self._coerce(other).value

    def __sub__(self, other: object) -> Size:
        """Subtract size from other size."""
        if not isinstance(other, Size | SizeLike):
            return NotImplemented
        return Size(self.value - self._coerce(other).value, self.dpi)

    def __rsub__(self, other: object) -> Size:
        """Subtract size from other size."""
        if not isinstance(other, Size | SizeLike):
            return NotImplemented
        return self._coerce(other) - self

    def __add__(self, other: object) -> Size:
        """Add two sizes."""
        if not isinstance(other, Size | SizeLike):
            return NotImplemented
        return Size(self.value + self._coerce(other).value, self.dpi)

    def __radd__(self, other: object) -> Size:
        """Add size and something: x + size."""
        if not isinstance(other, Size | SizeLike):
            return NotImplemented
        return self._coerce(other) + self

    def __mul__(self, other: object) -> Size:
        """Multiply size by a factor."""
        if not isinstance(other, int | float):
            return NotImplemented
        return Size(self.value * other, self.dpi)

    def __rmul__(self, other: object) -> Size:
        """Multiply size by a factor: other * size."""
        if not isinstance(other, int | float):
            return NotImplemented
        return Size(self.value * other, self.dpi)

    def __div__(self, other: object) -> Size:
        """Divide size by a factor."""
        if not isinstance(other, int | float):
            return NotImplemented
        return Size(self.value / other, self.dpi)

    def __truediv__(self, other: object) -> Size:
        """Divide size by a factor."""
        if not isinstance(other, int | float):
            return NotImplemented
        return Size(self.value / other, self.dpi)

    def __floordiv__(self, other: object) -> Size:
        """Divide size by a factor."""
        if not isinstance(other, int | float):
            return NotImplemented
        return Size(self.value // other, self.dpi)

    def __xor__(self, units: str) -> str:
        """Size(1.)^"mm"  will return "25.4mm"."""
        if units == "in":
            return f"{self.value:g}in"
        elif units == "pt":
            return f"{self.value * PT_PER_INCH:g}pt"
        elif units == "cm":
            return f"{self.value * MM_PER_INCH / 10:g}cm"
        elif units == "mm":
            return f"{self.value * MM_PER_INCH:g}mm"
        elif units == "px":
            return f"{int(round(self.value * self.dpi)):g}px"
        else:
            return f"{self.value:g}in"

    def _coerce(self, other: Size | SizeLike) -> Size:
        """Coerce other object to Size, use this object dpi if needed."""
        if not isinstance(other, Size):
            other = Size(other, self.dpi)
        return other


class String2Size:
    """Class implementing callable for conversion of strings to `Size`.

    This class defines restrictions on Size units, you can define set of
    accepted/rejected unit types. This could be useful for command line
    parser, e.g. as a `type` argument for ``argparse`` methods.

    Parameters
    ----------
    default_unit : `str`
        Default unit name to use when unit is not given.
    accepted_units : `list` [ `str` ]
        List of acceptable unit names, if string passed to ``__call__`` has
        unit not in this list then ``ValueError`` is raised. If ``None`` or
        empty list is passed to this argument then check is not performed.
    rejected_units : `list` [ `str` ]
        List of rejected unit names, if string passed to ``__call__`` has unit
        on this list then ``ValueError`` is raised. If ``None`` or empty list
        is passed to this argument then check is not performed.
    """

    all_units = ("pt", "in", "cm", "mm", "px")
    """All known unit names.
    """

    def __init__(
        self,
        default_unit: str = "in",
        accepted_units: list[str] | None = None,
        rejected_units: list[str] | None = None,
    ):
        self._default_unit = default_unit
        self._accepted_units = accepted_units
        self._rejected_units = rejected_units

    def __call__(self, value: str) -> Size:
        """Implement operator().

        Parameters
        ----------
        value : `str`
            String value to convert to `Size`.

        Returns
        -------
        size : `Size`
            String value converted to `Size`.

        Raises
        ------
        ValueError
            Raised if string does not have correct format or if unit type is
            not accepted.
        """
        try:
            # if this is a number then add default unit
            float(value)
            value += self._default_unit
        except ValueError:
            pass

        if not any(value.endswith(unit) for unit in self.all_units):
            raise ValueError(f"String {value} does not contain valid unit")

        if self._accepted_units:
            if not any(value.endswith(unit) for unit in self._accepted_units):
                raise ValueError(f"String {value} does not contain acceptable unit")

        if self._rejected_units:
            if any(value.endswith(unit) for unit in self._rejected_units):
                raise ValueError(f"String {value} contains unacceptable unit")

        return Size(value)
