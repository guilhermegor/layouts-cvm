"""Pydantic models for the CVM COFI 4010 fixed-width standard (Balancete).

Described by https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoCOFI.aspx (shared with
COFI 4016). The file holds, per fund, one header record and its account records, then a single
footer. The page does not state the decimal scale of the 18-position values; this schema
assumes ``VALUE_SCALE`` places (truncated, never rounded); the docs record it under "Decisões".
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, Field

from layouts_cvm._internal.config.schemas._fields import truncate_to_scale, validated_cnpj
from layouts_cvm._internal.utils.typing import type_checker
from layouts_cvm._internal.utils.xml_fields import require


VALUE_SCALE = 2
VALUE_DIGITS = 18
ACCOUNT_DIGITS = 10
COMPETENCE_LENGTH = 6
MAX_MONTH = 12


@type_checker
def _check_account(value: str) -> str:
    """Require exactly ``ACCOUNT_DIGITS`` digits (account code plus check digit).

    Parameters
    ----------
    value : str
        Raw account code.

    Returns
    -------
    str
        The same value.
    """
    require(
        len(value) == ACCOUNT_DIGITS and value.isascii() and value.isdigit(),
        f"account must be {ACCOUNT_DIGITS} digits: {value!r}",
    )
    return value


@type_checker
def _check_competence(value: str) -> str:
    """Require a ``MMAAAA`` competence: month 01-12, year not 0000.

    Parameters
    ----------
    value : str
        Raw competence.

    Returns
    -------
    str
        The same value.
    """
    require(
        len(value) == COMPETENCE_LENGTH
        and value.isascii()
        and value.isdigit()
        and 1 <= int(value[:2]) <= MAX_MONTH
        and int(value[2:]) > 0,
        f"competence must be MMAAAA: {value!r}",
    )
    return value


@type_checker
def _require_finite(value: object) -> object:
    """Reject ``Infinity``/``NaN`` before the shared truncation, which would raise bare.

    Parameters
    ----------
    value : object
        Raw value column input.

    Returns
    -------
    object
        The same value.
    """
    try:
        decimal_value = Decimal(str(value))
    except ArithmeticError:
        return value
    require(decimal_value.is_finite(), f"value must be finite: {value!r}")
    return value


Cofi4010AccountField = Annotated[str, AfterValidator(_check_account)]
CompetenceMMAAAA = Annotated[str, AfterValidator(_check_competence)]
CnpjField = Annotated[str, AfterValidator(validated_cnpj)]
ValueField = Annotated[
    Decimal,
    BeforeValidator(truncate_to_scale(VALUE_SCALE)),
    BeforeValidator(_require_finite),
    Field(max_digits=VALUE_DIGITS, decimal_places=VALUE_SCALE),
]


class Cofi4010Block(BaseModel):
    """Base of every COFI 4010 block: closed and immutable."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class Cofi4010Account(Cofi4010Block):
    """One account record: code plus the three signed value columns."""

    conta: Cofi4010AccountField
    total: ValueField
    ate_90_dias: ValueField
    apos_90_dias: ValueField


class Cofi4010Fund(Cofi4010Block):
    """One fund: its header data and account records."""

    cod_doc: Literal["4010"] = "4010"
    cnpj_fundo: CnpjField
    competencia: CompetenceMMAAAA
    contas: list[Cofi4010Account] = Field(min_length=1)


class Cofi4010Document(Cofi4010Block):
    """A COFI 4010 file: one or more funds (the page expects one competence; not checked)."""

    fundos: list[Cofi4010Fund] = Field(min_length=1)
