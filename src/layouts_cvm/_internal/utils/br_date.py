r"""The one ``DD/MM/AAAA`` check every date field in the library routes through.

A pure function (no I/O) that pins the shape and then the calendar. It lives in ``utils/`` so
both ``xml_fields`` / ``inr_mensal_fields`` and ``schemas/_fields.py`` can import it without a
cycle (``_fields`` already imports ``xml_fields``).

The shape is checked with ``re.fullmatch`` and ``[0-9]``: a ``$`` anchor accepts a trailing
newline and ``\d`` accepts non-ASCII digits, and ``strptime`` accepts an unpadded day, so none
of them could pin the zero-padded form the standards state.
"""

from datetime import date, datetime
import re

from layouts_cvm._internal.utils.typing import type_checker


_DATE_BR_SHAPE_RE = re.compile(r"[0-9]{2}/[0-9]{2}/[0-9]{4}")


@type_checker
def parse_br_date_strict(value: str) -> date:
    """Parse a zero-padded ``DD/MM/AAAA`` text into a date that exists on the calendar.

    Parameters
    ----------
    value : str
            The date text, e.g. ``"15/06/2026"``.

    Returns
    -------
    date
            The parsed date.

    Raises
    ------
    ValueError
            If the shape is wrong (``expected DD/MM/AAAA, got '<v>'``) or the day does not
            exist (``no such calendar day: '<v>'``).
    """
    _require_shape(value)
    return _parse_calendar_day(value)


@type_checker
def _require_shape(value: str) -> None:
    """Raise ``ValueError`` unless ``value`` is exactly ``DD/MM/AAAA`` in ASCII digits.

    Parameters
    ----------
    value : str
            The candidate text.

    Raises
    ------
    ValueError
            If the shape differs.
    """
    if not _DATE_BR_SHAPE_RE.fullmatch(value):
        raise ValueError(f"expected DD/MM/AAAA, got {value!r}")


@type_checker
def _parse_calendar_day(value: str) -> date:
    """Parse an already well-shaped text, with this module's own message for a missing day.

    ``strptime``'s wording differs between Python versions, so it is not part of the contract.

    Parameters
    ----------
    value : str
            A text already known to be ``DD/MM/AAAA``-shaped.

    Returns
    -------
    date
            The parsed date.

    Raises
    ------
    ValueError
            If the day does not exist, such as ``31/02/2026``.
    """
    try:
        return datetime.strptime(value, "%d/%m/%Y").date()  # noqa: DTZ007
    except ValueError as exc:
        raise ValueError(f"no such calendar day: {value!r}") from exc
