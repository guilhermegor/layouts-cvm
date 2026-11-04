"""Pydantic models for the CVM Informe Sintético XML standard — four fund-type variants.

Direction-neutral schema for the four ``PadraoXMLSint*.asp`` pages, e.g.
https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLSintFITVM.asp
The variants are not versions: each fund type has its own page, ``COD_DOC`` and block
layout, so each has its own models.

| Variant  | Page                     | ``COD_DOC`` | Funds                     |
|----------|--------------------------|-------------|---------------------------|
| ``Fcce`` | ``PadraoXMLSintFCCE``    | 5           | FCCE and FCCE-AI          |
| ``Fitvm``| ``PadraoXMLSintFITVM``   | 7           | FITVM, FMP-FGTS CL, FIIM  |
| ``Fic``  | ``PadraoXMLSintFIC``     | 8           | FIC-FITVM                 |
| ``Outros``| ``PadraoXMLSintOutros`` | 9           | FICE, FMP-FGTS, FMAI      |

**Field order is the XML order.** The writer walks ``model_fields`` in declaration order and names
each element ``<FIELD_NAME.upper()>``, so every field is the lower-cased tag from the page's
sample file (including its spelling quirks, e.g. ``VL_CONTR_FUTURO_MANTIDO_ABER`` on the FCCE page
against ``..._ABERTO`` on the Outros page).

The pages state the scales: every value is an integer in R$ 1000, except
``VL_QUOTA_ULT_DIA_MES``, marked "(decimal)" with no number of places. What the pages leave
unsaid is decided here and stated on ``docs/informe_sintetico.md``.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, Field

from layouts_cvm._internal.config.schemas._fields import validated_cnpj
from layouts_cvm._internal.utils.xml_fields import (
    check_br_date,
    check_cnpj_shape,
    check_month_year,
    strict_decimal,
)


_QUOTA_VALUE_PLACES = 12
_INTEGER_DIGITS = 18
_INT_MAX = 999_999_999_999

_Amount = Annotated[int, Field(strict=True, ge=-_INT_MAX, le=_INT_MAX)]
_Count = Annotated[int, Field(strict=True, ge=0, le=_INT_MAX)]
_QuotaValue = Annotated[
    Decimal,
    BeforeValidator(strict_decimal(_QUOTA_VALUE_PLACES)),
    Field(max_digits=_INTEGER_DIGITS + _QUOTA_VALUE_PLACES, decimal_places=_QUOTA_VALUE_PLACES),
]
_Competence = Annotated[str, AfterValidator(check_month_year)]
_Date = Annotated[str, AfterValidator(check_br_date)]
_Cnpj = Annotated[str, AfterValidator(check_cnpj_shape), AfterValidator(validated_cnpj)]


class _Block(BaseModel):
    """Base of every block: closed (no unknown fields) and immutable."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class _Header(_Block):
    """DESC_ADM — document header; each variant narrows ``cod_doc`` to its own code."""

    cod_doc: int
    cnpj_adm: _Cnpj
    dt_compt: _Competence
    dt_gerac_arq: _Date


class InformeSinteticoFcceHeader(_Header):
    """DESC_ADM of the FCCE variant."""

    cod_doc: Literal[5] = 5


class InformeSinteticoFitvmHeader(_Header):
    """DESC_ADM of the FITVM variant."""

    cod_doc: Literal[7] = 7


class InformeSinteticoFicHeader(_Header):
    """DESC_ADM of the FIC-FITVM variant."""

    cod_doc: Literal[8] = 8


class InformeSinteticoOutrosHeader(_Header):
    """DESC_ADM of the Outros variant."""

    cod_doc: Literal[9] = 9


class FitvmOutras(_Block):
    """OUTRAS of the FITVM variant."""

    nr_tot_quotst_ult_dia_mes: _Count
    vl_quota_ult_dia_mes: _QuotaValue
    patrim_liq: _Amount
    quota_emitida_mes: _Amount
    quota_resg_mes: _Amount


class FicOutras(_Block):
    """OUTRAS of the FIC-FITVM variant (its own page, so its own copy)."""

    nr_tot_quotst_ult_dia_mes: _Count
    vl_quota_ult_dia_mes: _QuotaValue
    patrim_liq: _Amount
    quota_emitida_mes: _Amount
    quota_resg_mes: _Amount


class FcceAplicacoes(_Block):
    """APLICACOES of the FCCE variant."""

    acoes: _Amount
    quota_fdo_renda_fixa: _Amount
    tit_divida_public_fed: _Amount
    outro_vl_mobili_emiss_cia_aber: _Amount
    outra_aplic: _Amount


class FcceOutras(_Block):
    """OUTRAS of the FCCE variant: the open futures value comes first."""

    vl_contr_futuro_mantido_aber: _Amount
    nr_tot_quotst_ult_dia_mes: _Count
    vl_quota_ult_dia_mes: _QuotaValue
    patrim_liq: _Amount
    quota_emitida_mes: _Amount
    quota_resg_mes: _Amount


class FitvmMercATermo(_Block):
    """MERC_A_TERMO — forward-market positions."""

    pos_comprd: _Amount
    pos_vend: _Amount


class FitvmContrFuturo(_Block):
    """CONTR_FUTURO — futures."""

    tot_margem_requerida: _Amount


class FitvmMercOpcao(_Block):
    """MERC_OPCAO — options premiums."""

    premio_pago: _Amount
    premio_receb: _Amount


class FitvmDebt(_Block):
    """DEBT — debentures."""

    simples: _Amount
    conversiveis: _Amount


class FitvmAplicacoes(_Block):
    """APLICACOES of the FITVM variant."""

    acao: _Amount
    merc_a_termo: FitvmMercATermo
    contr_futuro: FitvmContrFuturo
    merc_opcao: FitvmMercOpcao
    debt: FitvmDebt
    certf_recibo_depos_outro_vl_mobili: _Amount
    tit_public: _Amount
    tit_renda_fixa_emiss_instit_financ: _Amount
    cota_fdo_invest_financ: _Amount
    outra_aplic: _Amount


class FicAplicacoes(_Block):
    """APLICACOES of the FIC-FITVM variant."""

    cotas: _Amount
    tit_public: _Amount
    tit_renda_fixa_emiss_instit_financ: _Amount
    cota_fdo_invest_financ: _Amount
    outra_aplic: _Amount


class OutrosMercOpcao(_Block):
    """MERC_OPCAO — options premiums."""

    premio_pago: _Amount
    premio_receb: _Amount


class OutrosMercATermo(_Block):
    """MERC_A_TERMO — forward-market positions."""

    pos_comprd: _Amount
    pos_vend: _Amount


class OutrosAplicacoes(_Block):
    """APLICACOES of the Outros variant."""

    acao: _Amount
    merc_opcao: OutrosMercOpcao
    merc_a_termo: OutrosMercATermo
    conversiveis: _Amount
    simples: _Amount
    tit_public: _Amount
    moeda_privat: _Amount
    outra_aplic: _Amount


class OutrosOutras(_Block):
    """OUTRAS of the Outros variant: the open futures value comes first."""

    vl_contr_futuro_mantido_aberto: _Amount
    nr_tot_quotst_ult_dia_mes: _Count
    vl_quota_ult_dia_mes: _QuotaValue
    patrim_liq: _Amount
    quota_emitida_mes: _Amount
    quota_resg_mes: _Amount


class FcceAplicacoesPosFinal(_Block):
    """APLICACOES_POS_FINAL of the FCCE variant."""

    aplicacoes: FcceAplicacoes
    outras: FcceOutras


class FitvmAplicacoesPosFinal(_Block):
    """APLICACOES_POS_FINAL of the FITVM variant."""

    aplicacoes: FitvmAplicacoes
    outras: FitvmOutras


class FicAplicacoesPosFinal(_Block):
    """APLICACOES_POS_FINAL of the FIC-FITVM variant."""

    aplicacoes: FicAplicacoes
    outras: FicOutras


class OutrosAplicacoesPosFinal(_Block):
    """APLICACOES_POS_FINAL of the Outros variant."""

    aplicacoes: OutrosAplicacoes
    outras: OutrosOutras


class _Row(_Block):
    """ROW_INFORME — one fund's final-position report."""

    cnpj_fundo: _Cnpj


class InformeSinteticoFcceRow(_Row):
    """ROW_INFORME of the FCCE variant."""

    aplicacoes_pos_final: FcceAplicacoesPosFinal


class InformeSinteticoFitvmRow(_Row):
    """ROW_INFORME of the FITVM variant."""

    aplicacoes_pos_final: FitvmAplicacoesPosFinal


class InformeSinteticoFicRow(_Row):
    """ROW_INFORME of the FIC-FITVM variant."""

    aplicacoes_pos_final: FicAplicacoesPosFinal


class InformeSinteticoOutrosRow(_Row):
    """ROW_INFORME of the Outros variant."""

    aplicacoes_pos_final: OutrosAplicacoesPosFinal


class InformeSinteticoFcceDocument(_Block):
    """DOC_ARQ of the FCCE variant: one competence, one administrator, any number of funds."""

    header: InformeSinteticoFcceHeader
    rows: tuple[InformeSinteticoFcceRow, ...] = Field(min_length=1)


class InformeSinteticoFitvmDocument(_Block):
    """DOC_ARQ of the FITVM variant."""

    header: InformeSinteticoFitvmHeader
    rows: tuple[InformeSinteticoFitvmRow, ...] = Field(min_length=1)


class InformeSinteticoFicDocument(_Block):
    """DOC_ARQ of the FIC-FITVM variant."""

    header: InformeSinteticoFicHeader
    rows: tuple[InformeSinteticoFicRow, ...] = Field(min_length=1)


class InformeSinteticoOutrosDocument(_Block):
    """DOC_ARQ of the Outros variant."""

    header: InformeSinteticoOutrosHeader
    rows: tuple[InformeSinteticoOutrosRow, ...] = Field(min_length=1)
