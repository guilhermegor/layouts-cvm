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
(2 places; ``VL_QUOTA`` up to 12; ``PR_COTST`` up to 4) and the ``COTST_SIGNIF`` block match
V2 today, but every model here is **standalone**: V1 is a closed historical standard and V4
keeps changing, so a validator or type added to a V4 model must not reach V1 (PRINCIPLES.md
section 1, DRY caveat). Only the neutral helpers in ``_fields`` are shared.

**Field order is the XML order**: the writer walks ``model_fields`` in declaration order.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import re
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
)

from layouts_cvm._internal.config.schemas._fields import (
    truncate_to_scale,
    validate_person_doc,
    validated_cnpj,
)


_DATE_BR_RE = re.compile(r"^\d{2}/\d{2}/\d{4}$")

TwoDecimalField = Annotated[
    Decimal, BeforeValidator(truncate_to_scale(2)), Field(decimal_places=2)
]
QuotaValueField = Annotated[
    Decimal, BeforeValidator(truncate_to_scale(12)), Field(decimal_places=12)
]
ParticipationField = Annotated[
    Decimal,
    BeforeValidator(truncate_to_scale(4)),
    Field(ge=Decimal("0"), le=Decimal("100"), decimal_places=4),
]


class InformeDiarioV1Header(BaseModel):
    """CAB_INFORM — V1 header; ``COD_DOC`` is pinned to ``1`` and there is no ``VERSAO``."""

    model_config = ConfigDict(extra="forbid")

    cod_doc: Literal[1] = 1
    dt_compt: str
    dt_gerac_arq: str

    @field_validator("dt_compt", "dt_gerac_arq")
    @classmethod
    def _check_br_date(cls, v: str) -> str:
        """Validate a date field is a real calendar date in DD/MM/AAAA format.

        Parameters
        ----------
        v : str
                Value to validate.

        Returns
        -------
        str
                Validated value.

        Raises
        ------
        ValueError
                If value does not follow DD/MM/AAAA format or is not a real date.
        """
        if not _DATE_BR_RE.fullmatch(v):
            raise ValueError("date must follow DD/MM/AAAA format.")
        datetime.strptime(v, "%d/%m/%Y")  # noqa: DTZ007  # calendar check only, no timezone
        return v


class InformeDiarioV1Shareholder(BaseModel):
    """COTST_SIGNIF — V1 shareholder holding 20% or more; closed to unknown keys."""

    model_config = ConfigDict(extra="forbid")

    tp_pessoa: Literal["PF", "PJ"]
    cpf_cnpj_cotst: str
    pr_cotst: ParticipationField

    @field_validator("cpf_cnpj_cotst")
    @classmethod
    def _check_cotst_doc(cls, v: str, info: ValidationInfo) -> str:
        """Validate and normalise the shareholder document against its person type.

        Parameters
        ----------
        v : str
                The shareholder document (CPF or CNPJ) in any shape.
        info : ValidationInfo
                Validation context; ``tp_pessoa`` (declared first) is read from it.

        Returns
        -------
        str
                The document in bare, unmasked form.
        """
        return validate_person_doc(info.data.get("tp_pessoa", ""), v)


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
    lista_cotst_signif: list[InformeDiarioV1Shareholder] | None = None

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

    model_config = ConfigDict(extra="forbid")

    header: InformeDiarioV1Header
    informs: list[InformeDiarioV1Inform] = Field(max_length=100)
