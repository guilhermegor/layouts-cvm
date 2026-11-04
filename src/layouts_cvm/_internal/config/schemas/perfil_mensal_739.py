"""Pydantic models for the CVM Monthly Profile (Perfil Mensal) XML standard — ICVM 739.

The ICVM 739 version (valid from 2012-07-01, ICVM 409/512) is described by the CVM page
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLPerfil739.asp).
Measured against the V3 page and the V3 schema in
:mod:`layouts_cvm._internal.config.schemas.perfil_mensal_v3`, the XML sample is identical
tag for tag except for these differences:

* ``VERSAO`` is ``1.0`` (``COD_DOC`` stays ``40``, namespace ``urn:perf``).
* ``MONTANTE_DISTRIB`` and ``INF_COMPL_PERFIL`` do not exist on this page.
* ``VAR_DIAR_PERC_PATRIM_FDO_VAR_N_TAXA_ANUAL``, ``..._TAXA_CAMBIO``,
  ``VAR_PATRIM_FDO_N_PRECO_ACOES`` and ``VAL_PERCENT_OUTROS`` carry two decimal places
  (four in V3/V4).

Every other block is shared, so these models extend the V3 ones rather than copying them.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from layouts_cvm._internal.config.schemas.perfil_mensal import (
    DocumentHeader,
    TwoDecimalField,
    VarOutros,
)
from layouts_cvm._internal.config.schemas.perfil_mensal_v3 import (
    PerfilMensalV3Document,
    PerfilMensalV3Row,
)


class PerfilMensal739Header(DocumentHeader, BaseModel):
    """CAB_INFORM — ICVM 739 header; ``VERSAO`` is pinned to ``1.0``, ``COD_DOC`` to ``40``."""

    cod_doc: Literal[40] = 40
    versao: Literal["1.0"] = "1.0"


class PerfilMensal739VarOutros(VarOutros, BaseModel):
    """VARIACAO_DIAR_PERC_PATRIM_FDO_VAR_N_OUTROS — ``VAL_PERCENT_OUTROS`` has 2 decimals."""

    val_percent_outros: TwoDecimalField


class PerfilMensal739Row(PerfilMensalV3Row, BaseModel):
    """ROW_PERFIL — ICVM 739 fund block.

    The page has no ``MONTANTE_DISTRIB`` / ``INF_COMPL_PERFIL``: they are typed ``None`` so
    a value is rejected instead of silently dropped.
    """

    var_diar_perc_patrim_fdo_var_n_taxa_anual: TwoDecimalField | None = None
    var_diar_perc_patrim_fdo_var_n_taxa_cambio: TwoDecimalField | None = None
    var_patrim_fdo_n_preco_acoes: TwoDecimalField | None = None
    variacao_diar_perc_patrim_fdo_var_n_outros: PerfilMensal739VarOutros | None = None
    montante_distrib: None = None
    inf_compl_perfil: None = None


class PerfilMensal739Document(PerfilMensalV3Document, BaseModel):
    """DOC_ARQ — complete ICVM 739 document.

    ``rows`` deliberately narrows the V3 element type, hence the invariance ``type: ignore``.
    """

    header: PerfilMensal739Header  # type: ignore[assignment]
    rows: list[PerfilMensal739Row]  # type: ignore[assignment]
