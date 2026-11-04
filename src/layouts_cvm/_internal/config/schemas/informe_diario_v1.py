"""Pydantic models for the CVM Daily Report (Informe Diário) XML standard — V1.

V1 (valid until 2012-07-01) is described by the CVM page
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoDiarioNet.asp).
Measured against the V2 schema in
:mod:`layouts_cvm._internal.config.schemas.informe_diario_v2` the page differs in:

* ``CAB_INFORM`` has **no** ``VERSAO`` tag (only ``COD_DOC`` = 1, ``DT_COMPT``,
  ``DT_GERAC_ARQ``); the page states no version number at all.
* ``INFORM`` has **no** ``VL_TOTAL_SAI`` nor ``VL_TOTAL_ATV``: it ends ``RESG_DIA``,
  ``NR_COTST``, ``LISTA_COTST_SIGNIF``.

Fund identification (``CNPJ_FDO`` only), the ``LISTA_INFORM`` wrapper, the decimal scales
(2 places; ``VL_QUOTA`` up to 12; ``PR_COTST`` up to 4) and the ``COTST_SIGNIF`` block are
identical, so they are imported (from the V4 module) rather than copied.

**Field order is the XML order**: the writer walks ``model_fields`` in declaration order.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from layouts_cvm._internal.config.schemas._fields import validated_cnpj
from layouts_cvm._internal.config.schemas.informe_diario import (
    InformeDiarioHeader,
    QuotaValueField,
    SignificantShareholder,
    TwoDecimalField,
)


class InformeDiarioV1Header(InformeDiarioHeader):
    """CAB_INFORM — V1 header; ``COD_DOC`` is pinned to ``1`` and ``VERSAO`` is never emitted."""

    cod_doc: Literal[1] = 1
    versao: None = None  # type: ignore[assignment]  # V1 has no VERSAO; None is omitted


class InformeDiarioV1Inform(BaseModel):
    """INFORM — one fund's daily movement, keyed by ``CNPJ_FDO`` only.

    Closed (``extra="forbid"``): a V2+ field such as ``VL_TOTAL_SAI`` or ``DATA_PROX_PL`` is
    rejected instead of being silently dropped from the XML.
    """

    model_config = ConfigDict(extra="forbid")

    cnpj_fdo: str
    vl_total: TwoDecimalField
    vl_quota: QuotaValueField
    patrim_liq: TwoDecimalField
    captc_dia: TwoDecimalField
    resg_dia: TwoDecimalField
    nr_cotst: int = Field(ge=0)
    lista_cotst_signif: list[SignificantShareholder] | None = None

    @field_validator("cnpj_fdo")
    @classmethod
    def _check_cnpj(cls, v: str) -> str:
        """Validate and normalise the fund CNPJ (check-digit aware).

        Parameters
        ----------
        v : str
                The fund CNPJ in any shape.

        Returns
        -------
        str
                The unmasked (bare) CNPJ.
        """
        return validated_cnpj(v)


class InformeDiarioV1Document(BaseModel):
    """DOC_ARQ — complete V1 document (up to 100 funds, one competence)."""

    header: InformeDiarioV1Header
    informs: list[InformeDiarioV1Inform] = Field(max_length=100)
