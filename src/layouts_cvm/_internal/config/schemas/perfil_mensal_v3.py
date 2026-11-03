"""Pydantic models for the CVM Monthly Profile (Perfil Mensal) XML standard — V3.

V3 (valid from 2015-10-01, ICVM 409/512) is described by the CVM page
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLPerfilV3.asp).
Measured against the V4 page and the V4 schema in
:mod:`layouts_cvm._internal.config.schemas.perfil_mensal`
the XML sample is identical tag for tag (92 tags, same order, same scales and cardinalities)
and the page differs in exactly two ways:

* ``VERSAO`` is ``3.0`` (``COD_DOC`` stays ``40``, namespace ``urn:perf``).
* ``DISTR_PATRIM`` is mandatory, with all 16 ``PR_*`` tags; V4 makes the block optional and
  requires its tags only when the block is present.

Every other block is shared, so the V3 models extend the V4 ones rather than copying them.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, model_validator

from layouts_cvm._internal.config.schemas.perfil_mensal import (
    DocumentHeader,
    PatrimonyDistribution,
    PerfilMensalDocument,
    PerfilMensalRow,
)


class PerfilMensalV3Header(DocumentHeader, BaseModel):
    """CAB_INFORM — V3 header; ``VERSAO`` is pinned to ``3.0`` and ``COD_DOC`` to ``40``."""

    cod_doc: Literal[40] = 40
    versao: Literal["3.0"] = "3.0"


class PerfilMensalV3PatrimonyDistribution(PatrimonyDistribution, BaseModel):
    """DISTR_PATRIM — V3 block; every ``PR_*`` percentage is mandatory."""

    @model_validator(mode="after")
    def _require_every_percentage(self) -> PerfilMensalV3PatrimonyDistribution:
        """Reject a block that leaves any of the page's 16 percentages out.

        Returns
        -------
        PerfilMensalV3PatrimonyDistribution
                The validated block.

        Raises
        ------
        ValueError
                If any ``PR_*`` tag is missing.
        """
        missing = [name for name in type(self).model_fields if getattr(self, name) is None]
        if missing:
            raise ValueError(f"DISTR_PATRIM is fully mandatory in V3; missing: {missing}")
        return self


class PerfilMensalV3Row(PerfilMensalRow, BaseModel):
    """ROW_PERFIL — V3 fund block; ``DISTR_PATRIM`` is mandatory."""

    distr_patrim: PerfilMensalV3PatrimonyDistribution


class PerfilMensalV3Document(PerfilMensalDocument, BaseModel):
    """DOC_ARQ — complete V3 document.

    ``rows`` deliberately narrows the V4 element type, hence the invariance ``type: ignore``
    below.
    """

    header: PerfilMensalV3Header
    rows: list[PerfilMensalV3Row]  # type: ignore[assignment]
