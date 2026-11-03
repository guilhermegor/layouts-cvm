"""Pydantic models for the CVM Lâmina de Fundos XML standard — V2.

V2 (from 2015-10-01, ICVM 555) is described by the CVM page
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLLaminaV2.asp).
Measured against the V3 schema in :mod:`layouts_cvm.schemas.lamina` the page differs in
three ways:

* ``VERSAO`` is ``2.0`` (``COD_DOC`` stays ``24``).
* The fund is identified **only** by ``CNPJ_FUNDO``, which is mandatory; ``COD_SUBCLASSE`` does
  not exist in V2.
* A ``TAB_RENT_MENSAL`` row is ``MES``, ``RENT_LIQ``, ``VAR_IND_REF``, ``RENT_PERC_IND_REF``,
  ``COMENTARIOS`` — the same names as the annual row — where V3 renames the three value columns
  ``RENT_MENS``, ``VAR_MENS_IND_REF`` and ``RENT_MENS_PERC_IND_REF``.

Every other block (tag order, decimal scales, text lengths, cardinalities) is the V3 one, so
the V2 models extend the V3 models instead of copying them. A subclass keeps a field's
position when it narrows its type, which is what makes the inherited tag order hold.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator, model_validator

from layouts_cvm._internal.utils.typing import type_checker
from layouts_cvm.schemas.lamina import (
    _MAX_INFORMS,
    _MAX_MONTHLY_ROWS,
    CnpjField,
    LaminaBlock,
    LaminaDocument,
    LaminaHeader,
    LaminaInform,
    MonthField,
    SignedPercentField,
    Text500,
    _annual_index_cells,
    _check_unique_months,
    _check_unique_years,
    _check_year_overlap,
    _has_index_reference,
    _monthly_rows,
)


class LaminaV2Header(LaminaHeader):
    """CAB_INFORM — V2 header; ``VERSAO`` is pinned to ``2.0`` and ``COD_DOC`` stays ``24``."""

    versao: Literal["2.0"] = "2.0"  # type: ignore[assignment]


class LaminaV2TabRentMensal(LaminaBlock):
    """TAB_RENT_MENSAL — one month of return, with the V2 column names."""

    mes: MonthField
    rent_liq: SignedPercentField
    var_ind_ref: SignedPercentField | None = None
    rent_perc_ind_ref: SignedPercentField | None = None
    comentarios: Text500 | None = None


class LaminaV2ListaTabRentMensal(LaminaBlock):
    """LISTA_TAB_RENT_MENSAL — up to the last 12 months of return."""

    tab_rent_mensal: list[LaminaV2TabRentMensal] = Field(
        min_length=1, max_length=_MAX_MONTHLY_ROWS
    )


@type_checker
def _monthly_index_cells_v2(inform: LaminaV2Inform) -> list:
    """List every index cell of the V2 monthly return table.

    Parameters
    ----------
    inform : LaminaV2Inform
        The block being read.

    Returns
    -------
    list
        The ``var_ind_ref`` and ``rent_perc_ind_ref`` cells.
    """
    return [c for r in _monthly_rows(inform) for c in (r.var_ind_ref, r.rent_perc_ind_ref)]


@type_checker
def _check_index_columns_v2(inform: LaminaV2Inform) -> None:
    """Require a reference index when an index column of either table is filled.

    Parameters
    ----------
    inform : LaminaV2Inform
        The block being validated.

    Raises
    ------
    ValueError
        If an index cell is set while ``ind_refer`` is absent.
    """
    cells = _annual_index_cells(inform) + _monthly_index_cells_v2(inform)
    if not _has_index_reference(inform) and any(cell is not None for cell in cells):
        raise ValueError("index columns need infor_tab_rent_anual.ind_refer")


_RETURN_TABLE_CHECKS_V2 = (
    _check_unique_years,
    _check_unique_months,
    _check_year_overlap,
    _check_index_columns_v2,
)


class LaminaV2Inform(LaminaInform):
    """INFORM — V2 fund block, keyed by a mandatory ``CNPJ_FUNDO`` (no ``COD_SUBCLASSE``)."""

    cnpj_fundo: CnpjField
    lista_tab_rent_mensal: LaminaV2ListaTabRentMensal | None = None  # type: ignore[assignment]

    @field_validator("cod_subclasse")
    @classmethod
    def _reject_subclasse(cls, v: str | None) -> str | None:
        """Reject ``COD_SUBCLASSE``, which the V2 standard does not define.

        Parameters
        ----------
        v : Optional[str]
                The subclass code, which must be absent.

        Returns
        -------
        Optional[str]
                ``None``.

        Raises
        ------
        ValueError
                If a subclass code is given.
        """
        if v is not None:
            raise ValueError("cod_subclasse does not exist in Lâmina V2")
        return v

    @model_validator(mode="after")
    def _check_return_tables(self) -> LaminaV2Inform:
        """Check the rows of the annual and V2 monthly return tables against each other.

        Replaces the V3 validator of the same name, whose index check reads the V3 monthly
        column names.

        Returns
        -------
        LaminaV2Inform
                The validated block.

        Raises
        ------
        ValueError
                If a year or month repeats, the year sets overlap, or an index column is filled
                while ``ind_refer`` is absent.
        """
        for fn_check in _RETURN_TABLE_CHECKS_V2:
            fn_check(self)
        return self


class LaminaV2Document(LaminaDocument):
    """DOC_ARQ — a whole V2 Lâmina file: one competence, 1 to 70 funds.

    ``informs`` narrows the V3 element type, hence the invariance ``type: ignore`` below.
    """

    header: LaminaV2Header
    informs: list[LaminaV2Inform] = Field(  # type: ignore[assignment]
        min_length=1, max_length=_MAX_INFORMS
    )
