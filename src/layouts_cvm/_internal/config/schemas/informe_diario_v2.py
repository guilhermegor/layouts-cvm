"""Pydantic models for the CVM Daily Report (Informe Diário) XML standard — V2.

V2 (valid 2012-07-01 to 2015-09-30, ICVM 409/512) is described by the CVM page
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoDiarioNet739.asp).
Measured against the V4 schema in
:mod:`layouts_cvm._internal.config.schemas.informe_diario` the page differs in:

* ``VERSAO`` is ``2.0`` (``COD_DOC`` stays ``1``, namespace ``urn:infdiario``).
* The fund is identified **only** by ``CNPJ_FDO``; ``COD_SUBCLASSE`` does not exist.
* ``DATA_PROX_PL`` does not exist: an ``INFORM`` goes from ``CNPJ_FDO`` straight to ``VL_TOTAL``.
* The funds sit inside a ``LISTA_INFORM`` block under ``DOC_ARQ`` (the writer emits it).

The header, the decimal scales (2 places; ``VL_QUOTA`` up to 12; ``PR_COTST`` up to 4) and the
``COTST_SIGNIF`` block are identical, so they are imported from the V4 module rather than copied.
``NOME_FUNDO``, ``RESG_NAO_PROCES`` and ``LIQ_DIA_DISPON`` appear in the page's tag description
but only inside HTML comments and not in its sample file: they are not part of V2.

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


class InformeDiarioV2Header(InformeDiarioHeader, BaseModel):
    """CAB_INFORM — V2 header; ``VERSAO`` is pinned to ``2.0`` and ``COD_DOC`` to ``1``."""

    versao: Literal["2.0"] = "2.0"
    cod_doc: Literal[1] = 1


class InformeDiarioV2Inform(BaseModel):
    """INFORM — one fund's daily movement, keyed by ``CNPJ_FDO`` only.

    Closed (``extra="forbid"``): a V3/V4-only field such as ``DATA_PROX_PL`` or
    ``COD_SUBCLASSE`` is rejected instead of being silently dropped from the XML.
    """

    model_config = ConfigDict(extra="forbid")

    cnpj_fdo: str
    vl_total: TwoDecimalField
    vl_quota: QuotaValueField
    patrim_liq: TwoDecimalField
    captc_dia: TwoDecimalField
    resg_dia: TwoDecimalField
    vl_total_sai: TwoDecimalField
    vl_total_atv: TwoDecimalField
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


class InformeDiarioV2Document(BaseModel):
    """DOC_ARQ — complete V2 document (up to 100 funds, one competence)."""

    header: InformeDiarioV2Header
    informs: list[InformeDiarioV2Inform] = Field(max_length=100)
