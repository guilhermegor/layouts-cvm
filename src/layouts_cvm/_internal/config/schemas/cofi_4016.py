"""Pydantic models for the CVM COFI 4016 fixed-width document (Balanço).

Layout: https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoCOFI.aspx (71 columns per
record). One file holds the balanços of one or more funds sharing the same competence; each
fund contributes a header record, its account records and nothing else — the single footer
record is written once per file.

The page does not state the decimal scale of the 18-digit value columns, so the models keep
two decimal places (truncated, never rounded) and the writer emits them as integer cents.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
)

from layouts_cvm._internal.config.schemas._fields import validated_cnpj
from layouts_cvm._internal.utils.xml_fields import (
    check_cnpj_shape,
    check_month_year,
    strict_decimal,
)


_VALUE_SCALE = 2
_VALUE_DIGITS = 18

AccountField = Annotated[str, StringConstraints(pattern=r"^[0-9]{10}$")]
CnpjField = Annotated[str, AfterValidator(check_cnpj_shape), AfterValidator(validated_cnpj)]
CompetenceField = Annotated[str, AfterValidator(check_month_year)]
SignedValueField = Annotated[
    Decimal,
    BeforeValidator(strict_decimal(_VALUE_SCALE)),
    Field(max_digits=_VALUE_DIGITS, decimal_places=_VALUE_SCALE),
]


class Cofi4016Block(BaseModel):
    """Base of every COFI 4016 block: closed (no unknown fields) and immutable."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class Cofi4016Account(Cofi4016Block):
    """One account record: the 10-position account and its three value columns."""

    conta: AccountField
    total: SignedValueField = Decimal(0)
    ate_90_dias: SignedValueField = Decimal(0)
    apos_90_dias: SignedValueField = Decimal(0)


class Cofi4016Fund(Cofi4016Block):
    """The balanço of one fund: its CNPJ and account records."""

    cnpj_fundo: CnpjField
    contas: list[Cofi4016Account] = Field(min_length=1)


class Cofi4016Document(Cofi4016Block):
    """A whole COFI 4016 file: one competence and one or more funds."""

    dt_compt: CompetenceField
    fundos: list[Cofi4016Fund] = Field(min_length=1)
