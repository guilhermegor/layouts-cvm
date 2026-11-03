"""Pydantic models for the CVM Lâmina de Fundos XML standard — V1.

V1 (ICVM 409 as amended by ICVM 522, 2012) is described by the CVM page
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLLamina.asp). Measured against
the V3 schema in :mod:`layouts_cvm._internal.config.schemas.lamina` the page differs in these
ways:

* ``VERSAO`` is ``1.0`` (``COD_DOC`` stays ``24``).
* The fund is identified **only** by ``CNPJ_FUNDO``, which is mandatory; no ``COD_SUBCLASSE``.
* ``CONC_EMISSOR`` (issuer-concentration limit) exists, between ``ALAV`` and ``PERDAS_SIGN``;
  the page does not mark ``ALAV`` optional, so it is mandatory here too.
* V3 tags that do not exist in V1: ``UTILIZ_DERIV_APENAS_PROTECAO_CART``, ``PERC_MAX``,
  ``OBS_HOR_APL_RESG``, ``TP_PRAZO_DIAS`` (``PRAZO_PAGAM`` is always in business days),
  ``DS_FORMA_REMUN_DISTR``, ``PRINC_DISTR_OFERTA``, ``PRINC_CONFLITO_INTERES`` and
  ``INFO_ADIC``.

Because fields disappear and one appears mid-sequence, V1 cannot extend ``LaminaInform`` (a
subclass cannot drop a field or insert one before an inherited one, and the writer's tag order
is declaration order). It declares its own ``INFORM`` and reuses every shared sub-block,
constrained type and text length from the V3 module. Field order is the XML order, as in V3.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from layouts_cvm._internal.config.schemas.lamina import (
    _MAX_INFORMS,
    _MAX_MONTHLY_ROWS,
    CnpjField,
    LaminaBlock,
    LaminaCarencia,
    LaminaConversao,
    LaminaDespesas,
    LaminaHeader,
    LaminaInformExemploComp,
    LaminaInforTabRentAnual,
    LaminaListaCompCarteira,
    LaminaListaTabRentAnual,
    LaminaTabSimulDespesas,
    LaminaTabVarDesemp,
    LaminaTaxaAdministracao,
    LaminaTaxaEntrada,
    LaminaTaxaSaida,
    MoneyField,
    MonthField,
    PercentField,
    PhoneField,
    RatioField,
    RiskField,
    ShortField,
    SignedPercentField,
    Text50,
    Text100,
    Text500,
    Text1000,
    TimeField,
)
from layouts_cvm._internal.utils.typing import type_checker


class LaminaV1Header(LaminaHeader):
    """CAB_INFORM — V1 header; ``VERSAO`` is pinned to ``1.0`` and ``COD_DOC`` stays ``24``."""

    versao: Literal["1.0"] = "1.0"  # type: ignore[assignment]


class LaminaV1TabRentMensal(LaminaBlock):
    """TAB_RENT_MENSAL — one month of return (sample-file column names, as in V3)."""

    mes: MonthField
    rent_mens: SignedPercentField
    var_mens_ind_ref: SignedPercentField | None = None
    rent_mens_perc_ind_ref: SignedPercentField | None = None
    comentarios: Text500 | None = None


class LaminaV1ListaTabRentMensal(LaminaBlock):
    """LISTA_TAB_RENT_MENSAL — up to the last 12 months of return."""

    tab_rent_mensal: list[LaminaV1TabRentMensal] = Field(
        min_length=1, max_length=_MAX_MONTHLY_ROWS
    )


@type_checker
def _has_duplicates(list_values: list) -> bool:
    """Tell whether a list repeats a value.

    Parameters
    ----------
    list_values : list
        The values to compare.

    Returns
    -------
    bool
        True when at least one value appears twice.
    """
    return len(set(list_values)) != len(list_values)


@type_checker
def _annual_rows(inform: LaminaV1Inform) -> list:
    """List the annual return rows, empty when the table is absent.

    Parameters
    ----------
    inform : LaminaV1Inform
        The block being read.

    Returns
    -------
    list
        The ``tab_rent_anual`` rows.
    """
    table = inform.lista_tab_rent_anual
    return table.tab_rent_anual if table else []


@type_checker
def _monthly_rows(inform: LaminaV1Inform) -> list:
    """List the monthly return rows, empty when the table is absent.

    Parameters
    ----------
    inform : LaminaV1Inform
        The block being read.

    Returns
    -------
    list
        The ``tab_rent_mensal`` rows.
    """
    table = inform.lista_tab_rent_mensal
    return table.tab_rent_mensal if table else []


@type_checker
def _pre_fund_years(inform: LaminaV1Inform) -> set:
    """Collect the years declared as "before the fund existed".

    Parameters
    ----------
    inform : LaminaV1Inform
        The block being read.

    Returns
    -------
    set
        The ``antes_inic2`` years, empty when absent.
    """
    info = inform.infor_tab_rent_anual
    return set(info.antes_inic2.ano) if info and info.antes_inic2 else set()


@type_checker
def _index_cells(inform: LaminaV1Inform) -> list:
    """List every index cell of both return tables.

    Parameters
    ----------
    inform : LaminaV1Inform
        The block being read.

    Returns
    -------
    list
        The annual and monthly index-variation and index-performance cells.
    """
    list_annual = [(r.var_ind_ref, r.rent_perc_ind_ref) for r in _annual_rows(inform)]
    list_monthly = [(r.var_mens_ind_ref, r.rent_mens_perc_ind_ref) for r in _monthly_rows(inform)]
    return [cell for pair in list_annual + list_monthly for cell in pair]


@type_checker
def _has_index_reference(inform: LaminaV1Inform) -> bool:
    """Tell whether ``ind_refer`` is declared.

    Parameters
    ----------
    inform : LaminaV1Inform
        The block being read.

    Returns
    -------
    bool
        True when a reference index is present.
    """
    info = inform.infor_tab_rent_anual
    return info is not None and info.ind_refer is not None


class LaminaV1Inform(LaminaBlock):
    """INFORM — the V1 fact sheet of one fund, keyed by a mandatory ``CNPJ_FUNDO``."""

    cnpj_fundo: CnpjField
    nome_fantasia: Text500
    end_eletr: Text100
    desc_pub_alvo: Text1000
    restr_inv: Text500
    desc_objet: Text1000
    desc_pol_inv: Text1000
    ativo_ext: PercentField
    cred_priv: PercentField
    alav: RatioField
    conc_emissor: PercentField
    perdas_sign: Literal["S", "N"]
    pl_negat: Literal["S", "N"]
    inv_inicial: MoneyField
    inv_adic: MoneyField
    resg_min: MoneyField
    hor_apl_resg: TimeField
    valor_perm: MoneyField
    carencia: LaminaCarencia | None = None
    conversao: LaminaConversao
    prazo_pagam: ShortField
    infor_tx_adm: LaminaTaxaAdministracao
    infor_tx_entr: LaminaTaxaEntrada | None = None
    infor_tx_saida: LaminaTaxaSaida | None = None
    tx_desempenho: Text500
    infor_despesas: LaminaDespesas | None = None
    lista_comp_carteira: LaminaListaCompCarteira | None = None
    classif_risco: RiskField
    infor_tab_rent_anual: LaminaInforTabRentAnual | None = None
    lista_tab_rent_anual: LaminaListaTabRentAnual | None = None
    lista_tab_rent_mensal: LaminaV1ListaTabRentMensal | None = None
    form_calc_rent: Text500 | None = None
    tab_var_desemp: LaminaTabVarDesemp | None = None
    inform_exemplo_comp: LaminaInformExemploComp | None = None
    tab_simul_despesas: LaminaTabSimulDespesas | None = None
    tel_sac: PhoneField
    reclamacoes: Text50

    @model_validator(mode="after")
    def _check_unique_years(self) -> LaminaV1Inform:
        """Reject a repeated year in the annual return table.

        Returns
        -------
        LaminaV1Inform
                The validated block.

        Raises
        ------
        ValueError
                If a year repeats.
        """
        if _has_duplicates([row.ano_rent for row in _annual_rows(self)]):
            raise ValueError("ano_rent must not repeat a year")
        return self

    @model_validator(mode="after")
    def _check_unique_months(self) -> LaminaV1Inform:
        """Reject a repeated month in the monthly return table.

        Returns
        -------
        LaminaV1Inform
                The validated block.

        Raises
        ------
        ValueError
                If a month repeats.
        """
        if _has_duplicates([row.mes for row in _monthly_rows(self)]):
            raise ValueError("mes must not repeat a month")
        return self

    @model_validator(mode="after")
    def _check_year_overlap(self) -> LaminaV1Inform:
        """Reject a year both reported and listed as before the fund existed.

        Returns
        -------
        LaminaV1Inform
                The validated block.

        Raises
        ------
        ValueError
                If ``antes_inic2`` overlaps ``tab_rent_anual``.
        """
        if _pre_fund_years(self) & {row.ano_rent for row in _annual_rows(self)}:
            raise ValueError("a year cannot be both in antes_inic2 and in tab_rent_anual")
        return self

    @model_validator(mode="after")
    def _check_index_columns(self) -> LaminaV1Inform:
        """Require ``ind_refer`` when any index column of either return table is filled.

        Returns
        -------
        LaminaV1Inform
                The validated block.

        Raises
        ------
        ValueError
                If an index cell is set while ``ind_refer`` is absent.
        """
        if not _has_index_reference(self) and any(c is not None for c in _index_cells(self)):
            raise ValueError("index columns need infor_tab_rent_anual.ind_refer")
        return self


class LaminaV1Document(LaminaBlock):
    """DOC_ARQ — a whole V1 Lâmina file: one competence, 1 to 70 funds."""

    header: LaminaV1Header
    informs: list[LaminaV1Inform] = Field(min_length=1, max_length=_MAX_INFORMS)

    @model_validator(mode="after")
    def _check_unique_funds(self) -> LaminaV1Document:
        """Reject the same fund twice in one file.

        Returns
        -------
        LaminaV1Document
                The validated document.

        Raises
        ------
        ValueError
                If a CNPJ repeats.
        """
        if _has_duplicates([inform.cnpj_fundo for inform in self.informs]):
            raise ValueError("a fund appears twice in the file")
        return self
