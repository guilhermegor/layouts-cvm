"""Pydantic models for the CVM Fund Statement (Extrato) XML standard — V2.

Direction-neutral schema for ``PadraoXMLInfExtratoV2.asp``
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfExtratoV2.asp). Diffed against
V3 on 2026-11-03, the sample file carries the same 138 tags in the same order; the two pages differ
in ``VERSAO`` (2.0), in the fund/class wording, and in V3 marking ten row tags "Tag opcional"
where V2 marks none. So V2 reuses every V3 block and only redeclares the header and the row:
those ten tags are required here. Field order is the XML order (a redeclared field keeps its
inherited position).
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from layouts_cvm._internal.config.schemas.extrato import (
    DateField,
    DaysField,
    DistributionCode,
    ExtratoBlock,
    ExtratoRow,
    Money2,
    Percent4,
    Percent6,
    PrazoPagamResg,
    PublicoAlvo,
    TipoValorCota,
    ValorCotaBasePl,
)


_MAX_ROWS = 1000


class ExtratoV2Header(ExtratoBlock):
    """CAB_INFORM — document header."""

    cod_doc: Literal[41] = 41
    versao: Literal["2.0"] = "2.0"
    dt_gerac_arq: DateField


class ExtratoV2Row(ExtratoRow):
    """ROW_EXTRATO — the extract of one fund (V2: no "Tag opcional" row tags)."""

    publico_alvo: PublicoAlvo
    cod_distr_fdo: DistributionCode
    aplicacao_minima_fundo: Money2
    tipo_valor_cota: TipoValorCota
    valor_cota_base_pl: ValorCotaBasePl
    qt_dia_conv_cota: DaysField
    qt_dia_pagam_cota: DaysField
    prazo_pagam_resg: PrazoPagamResg
    taxa_adm: Percent4
    taxa_maxima_custodia: Percent6


class ExtratoV2Document(ExtratoBlock):
    """DOC_ARQ — a whole Extrato V2 file: one header and one row per fund."""

    header: ExtratoV2Header
    rows: Annotated[list[ExtratoV2Row], Field(min_length=1, max_length=_MAX_ROWS)]
