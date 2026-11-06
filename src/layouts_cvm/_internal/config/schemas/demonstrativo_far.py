"""Pydantic models for the CVM Demonstrativo de Fontes e Aplicações de Recursos (FAR) standard.

Direction-neutral schema for ``PadraoXMLFAR.asp``
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLFAR.asp). The page's sample has
no namespace: ``DOC_ARQ`` > ``DESC_ADM`` (the administrator) + ``FAR`` > repeated
``ROW_REGISTRO_MOVIMENTO`` (one fund), each closing with ``DOC_MOV_MES`` > repeated
``ROW_MOV_POR_FUNDO`` (one cash-flow movement).

**Field order is the XML order.** The writer walks ``model_fields`` in declaration order and
names each element ``<FIELD_NAME.upper()>``, so every field is the lower-cased tag of the page.

Scales come from the page: quota count, quota value and distribution values are decimals with
10 places; every other number is an integer. Excess decimal places are truncated toward zero,
never rounded. What the page leaves unsaid is listed on ``docs/demonstrativo_far.md``.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from types import MappingProxyType
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from layouts_cvm._internal.config.schemas._fields import validated_cnpj
from layouts_cvm._internal.utils.typing import type_checker
from layouts_cvm._internal.utils.xml_fields import (
    check_br_date,
    check_cnpj_shape,
    check_month_year,
    require,
    strict_decimal,
)


_PLACES = 10
_INTEGER_DIGITS = 18
_INT_MAX = 999_999_999_999

_TABLE_A: Mapping[int, tuple[bool, bool]] = MappingProxyType(
    {
        37: (True, True),
        48: (True, True),
        53: (True, False),
        54: (False, True),
        55: (True, True),
        56: (True, False),
        57: (True, False),
        58: (True, False),
        60: (True, False),
        61: (False, True),
        62: (False, True),
        63: (False, True),
        64: (False, True),
        65: (False, True),
        66: (False, True),
        67: (True, False),
        68: (False, True),
        69: (False, True),
        70: (True, True),
        71: (True, False),
        72: (False, True),
        73: (False, True),
        74: (True, True),
        75: (True, True),
        77: (True, True),
        78: (True, True),
        144: (True, False),
        145: (True, True),
        150: (False, True),
    }
)

_Decimal10 = Annotated[
    Decimal,
    BeforeValidator(strict_decimal(_PLACES)),
    Field(ge=0, max_digits=_INTEGER_DIGITS + _PLACES, decimal_places=_PLACES),
]
_Count = Annotated[int, Field(strict=True, ge=0, le=_INT_MAX)]
_Competence = Annotated[str, AfterValidator(check_month_year)]
_Date = Annotated[str, AfterValidator(check_br_date)]
_Cnpj = Annotated[str, AfterValidator(check_cnpj_shape), AfterValidator(validated_cnpj)]


class _Block(BaseModel):
    """Base of every block: closed (no unknown fields) and immutable."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class DemonstrativoFarDescAdm(_Block):
    """DESC_ADM — the fund administrator and the file's competence."""

    cod_doc: Literal[4] = 4
    cnpj_adm: _Cnpj
    dt_compt: _Competence
    dt_gerac_arq: _Date


class DemonstrativoFarMovimento(_Block):
    """ROW_MOV_POR_FUNDO — one movement code with its inflow and outflow, in R$ 1000."""

    cd_mov: Annotated[int, Field(strict=True)]
    vl_entr: _Count | None = None
    vl_saida: _Count | None = None

    @model_validator(mode="after")
    def _check_table_a(self) -> DemonstrativoFarMovimento:
        """Apply Table A: the code must exist, ``S`` columns filled, ``N`` columns empty.

        Returns
        -------
        DemonstrativoFarMovimento
                The validated movement.

        Raises
        ------
        ValueError
                If the code is not in Table A or a column breaks its ``S``/``N`` rule.
        """
        rules = _TABLE_A.get(self.cd_mov)
        require(rules is not None, f"cd_mov {self.cd_mov} is not in Table A")
        filled = (self.vl_entr is not None, self.vl_saida is not None)
        require(
            filled == rules,
            f"cd_mov {self.cd_mov}: (vl_entr, vl_saida) filled must be {rules}",
        )
        return self


class DemonstrativoFarDocMovMes(_Block):
    """DOC_MOV_MES — the movements of one fund."""

    row_mov_por_fundo: list[DemonstrativoFarMovimento] = Field(min_length=1)

    @model_validator(mode="after")
    def _check_unique_codes(self) -> DemonstrativoFarDocMovMes:
        """Reject a movement code repeated within one fund.

        Returns
        -------
        DemonstrativoFarDocMovMes
                The validated block.

        Raises
        ------
        ValueError
                If a ``cd_mov`` repeats.
        """
        codes = [m.cd_mov for m in self.row_mov_por_fundo]
        if len(set(codes)) != len(codes):
            raise ValueError("a cd_mov appears twice for the same fund")
        return self


class DemonstrativoFarRegistro(_Block):
    """ROW_REGISTRO_MOVIMENTO — the FAR of one fund."""

    cnpj_fundo: _Cnpj
    nr_quota_circul_ult_dia_mes: _Decimal10
    vl_quota_ult_dia_mes: _Decimal10
    nr_total_quotst_ult_dia_mes: _Count
    vl_ult_distr_quota: _Decimal10 | None = None
    dt_distr: _Date | None = None
    vl_quota_dt_ult_distr: _Decimal10 | None = None
    doc_mov_mes: DemonstrativoFarDocMovMes

    @model_validator(mode="after")
    def _check_distribution_trio(self) -> DemonstrativoFarRegistro:
        """Require the three distribution fields together or not at all.

        Returns
        -------
        DemonstrativoFarRegistro
                The validated block.

        Raises
        ------
        ValueError
                If only some of the distribution fields are filled.
        """
        trio = (self.vl_ult_distr_quota, self.dt_distr, self.vl_quota_dt_ult_distr)
        if len({v is None for v in trio}) > 1:
            raise ValueError("vl_ult_distr_quota, dt_distr and vl_quota_dt_ult_distr go together")
        return self


class DemonstrativoFarFar(_Block):
    """FAR — the funds of the file."""

    row_registro_movimento: list[DemonstrativoFarRegistro] = Field(min_length=1)

    @model_validator(mode="after")
    def _check_unique_funds(self) -> DemonstrativoFarFar:
        """Reject the same fund twice in one file.

        Returns
        -------
        DemonstrativoFarFar
                The validated block.

        Raises
        ------
        ValueError
                If a CNPJ repeats.
        """
        cnpjs = [r.cnpj_fundo for r in self.row_registro_movimento]
        if len(set(cnpjs)) != len(cnpjs):
            raise ValueError("a fund appears twice in the file")
        return self


class DemonstrativoFarDocument(_Block):
    """DOC_ARQ — a whole file: one administrator, one competence, one or more funds."""

    desc_adm: DemonstrativoFarDescAdm
    far: DemonstrativoFarFar


@type_checker
def find_missing_codes(registro: DemonstrativoFarRegistro) -> list[int]:
    """List the Table A codes a fund does not use, in ascending order.

    Parameters
    ----------
    registro : DemonstrativoFarRegistro
        The fund whose movements are checked.

    Returns
    -------
    list[int]
        Table A codes absent from ``row_mov_por_fundo``, ascending.
    """
    set_used = {m.cd_mov for m in registro.doc_mov_mes.row_mov_por_fundo}
    return sorted(set(_TABLE_A) - set_used)


@type_checker
def check_fund_uses_all_codes(registro: DemonstrativoFarRegistro) -> None:
    """Refuse a fund that leaves a Table A code unused.

    Parameters
    ----------
    registro : DemonstrativoFarRegistro
        The fund to check.

    Raises
    ------
    ValueError
        Naming the fund's CNPJ and the missing codes, ascending.
    """
    list_missing = find_missing_codes(registro)
    if list_missing:
        raise ValueError(f"fund {registro.cnpj_fundo} does not use Table A codes {list_missing}")


@type_checker
def check_all_funds_use_all_codes(document: DemonstrativoFarDocument) -> None:
    """Refuse a document in which any fund leaves a Table A code unused.

    Parameters
    ----------
    document : DemonstrativoFarDocument
        The built document to check.
    """
    for registro in document.far.row_registro_movimento:
        check_fund_uses_all_codes(registro)
