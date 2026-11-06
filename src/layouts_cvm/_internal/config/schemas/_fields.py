"""Shared field helpers for CVM XML-standard schemas.

Direction-neutral building blocks reused by every ``_internal/config/schemas/<standard>.py``
model: a decimal-scale truncation factory (ROUND_DOWN, never growing a value in
magnitude past the scale a standard permits) and the Brazilian CPF/CNPJ check-digit validators.

This is a private ``_``-prefixed module — it ships in the wheel but is not part of the
public API. Each standard imports these to declare its own ``Annotated`` field types
and validators, so the truncation/validation logic lives in exactly one place.
"""

from collections.abc import Callable
from datetime import datetime
from decimal import ROUND_DOWN, Context, Decimal, InvalidOperation
import re

from layouts_cvm._internal.utils.br_identifiers import (
    is_valid_cnpj,
    is_valid_cpf,
    unmask_cnpj,
    unmask_cpf,
)
from layouts_cvm._internal.utils.typing import type_checker
from layouts_cvm._internal.utils.xml_fields import require


DecimalInput = Decimal | str | int | float | None

_PERSON_DOC_RULES = {
    "PF": ("CPF", is_valid_cpf, unmask_cpf),
    "PJ": ("CNPJ", is_valid_cnpj, unmask_cnpj),
}


_TRUNCATION_CONTEXT = Context(prec=28)

_COMPETENCE_RE = re.compile(r"(0[1-9]|1[0-2])/(?!0000)[0-9]{4}")
_DATE_BR_SHAPE_RE = re.compile(r"[0-9]{2}/[0-9]{2}/[0-9]{4}")


@type_checker
def _quantize(value: DecimalInput, quantum: Decimal) -> Decimal:
    """Truncate one non-null value to ``quantum`` (ROUND_DOWN); a truncated zero is unsigned.

    Parameters
    ----------
    value : DecimalInput
        Raw value from XML parsing, CSV reload, or direct construction.
    quantum : Decimal
        The scale to truncate to.

    Returns
    -------
    Decimal
        The truncated value.

    Raises
    ------
    ValueError
        If the value cannot be interpreted as a decimal number.
    """
    try:
        as_decimal = value if isinstance(value, Decimal) else Decimal(str(value))
        truncated = as_decimal.quantize(quantum, rounding=ROUND_DOWN, context=_TRUNCATION_CONTEXT)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid decimal value: {value!r}") from exc
    return truncated.copy_abs() if truncated.is_zero() else truncated


@type_checker
def truncate_to_scale(decimal_places: int) -> Callable[[DecimalInput], Decimal | None]:
    """Build a before-validator that truncates a value to ``decimal_places`` (ROUND_DOWN).

    Truncation (never rounding) is used so a value never grows in magnitude past
    the scale the CVM standard permits; any excess precision is discarded toward zero.

    Parameters
    ----------
    decimal_places : int
            Number of decimal places mandated by the CVM standard for the field.

    Returns
    -------
    Callable[[DecimalInput], Optional[Decimal]]
            A validator callable returning the truncated ``Decimal`` (or ``None``).

    Raises
    ------
    ValueError
            Raised by the returned validator when a value cannot be interpreted as a
            decimal number.
    """
    quantum = Decimal(1).scaleb(-decimal_places)

    def _truncate(value: DecimalInput) -> Decimal | None:
        """Truncate a single incoming value to the bound scale.

        Parameters
        ----------
        value : DecimalInput
                Raw value from XML parsing, CSV reload, or direct construction.

        Returns
        -------
        Optional[Decimal]
                Truncated value, or ``None`` when the input is ``None``.

        Raises
        ------
        ValueError
                If the value cannot be interpreted as a decimal number.
        """
        return None if value is None else _quantize(value, quantum)

    return _truncate


@type_checker
def validated_cnpj(value: str) -> str:
    """Normalise and check-digit-validate a CNPJ, returning its bare 14-char form.

    Parameters
    ----------
    value : str
            A CNPJ in any shape (masked, padded, or bare).

    Returns
    -------
    str
            The unmasked (bare) CNPJ.

    Raises
    ------
    ValueError
            If the value is not a valid CNPJ (failing check digits).
    """
    require(is_valid_cnpj(value), f"invalid CNPJ: {value!r}")
    return unmask_cnpj(value)


@type_checker
def validate_person_doc(tp_pessoa: str, value: str) -> str:
    """Validate a document as CPF (PF) or CNPJ (PJ) and return its bare form.

    Parameters
    ----------
    tp_pessoa : str
            ``"PF"`` (natural person → CPF) or ``"PJ"`` (legal entity → CNPJ).
    value : str
            The document in any shape.

    Returns
    -------
    str
            The unmasked (bare) document.

    Raises
    ------
    ValueError
            If the document is not valid for the given person type.
    """
    kind = "PF" if tp_pessoa == "PF" else "PJ"
    name, is_valid, unmask = _PERSON_DOC_RULES[kind]
    require(is_valid(value), f"invalid {name} for {kind}: {value!r}")
    return unmask(value)


@type_checker
def validated_competence(value: str) -> str:
    """Check a competence follows ``MM/AAAA`` and return it unchanged.

    Parameters
    ----------
    value : str
            The competence, e.g. ``"06/2026"``.

    Returns
    -------
    str
            The validated value.

    Raises
    ------
    ValueError
            If the value is not ``MM/AAAA`` (month 01-12, four-digit year not ``0000``).
    """
    if not _COMPETENCE_RE.fullmatch(value):
        raise ValueError(f"expected MM/AAAA, got {value!r}")
    return value


@type_checker
def validated_br_date(value: str) -> str:
    """Check a date is written ``DD/MM/AAAA`` and exists on the calendar; return it unchanged.

    The regex pins the shape (ASCII digits, zero-padded), which ``strptime`` alone does not;
    ``strptime`` then rejects a day that does not exist, such as ``31/02/2026``.

    Parameters
    ----------
    value : str
            The date text, e.g. ``"15/06/2026"``.

    Returns
    -------
    str
            The validated value.

    Raises
    ------
    ValueError
            If the value does not follow ``DD/MM/AAAA`` or names a day that does not exist.
    """
    if not _DATE_BR_SHAPE_RE.fullmatch(value):
        raise ValueError(f"expected DD/MM/AAAA, got {value!r}")
    datetime.strptime(value, "%d/%m/%Y")  # noqa: DTZ007  (calendar check only)
    return value
