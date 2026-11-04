"""Pydantic models for the Semiannual Non-Resident Investor Report — Part I.

Direction-neutral schema for ``PadraoXMLInfoSemestralINRParte1.asp``
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoSemestralINRParte1.asp;
namespace ``urn:infmensal``, ``COD_DOC=69``, ``VERSAO=1.0``).

Part I is the monthly INR layout (:mod:`layouts_cvm._internal.config.schemas.inr_mensal`)
without the ``APLICACOES`` block, so every block is shared and only the header code and the
participant differ. A field Part I lacks stays on the model (a subclass cannot drop it) but is
rejected when set, so the writer never emits its tag.

Part II (``COD_DOC=70``, the applications) is **not** modelled here.
"""

from __future__ import annotations

from typing import Literal

from pydantic import field_validator

from layouts_cvm._internal.config.schemas.inr_mensal import (
    InrMensalDocument,
    InrMensalHeader,
    Participante,
)


class InformeSemestralInrHeader(InrMensalHeader):
    """CAB_INFORM — Part I header; ``COD_DOC`` is pinned to ``69``."""

    cod_doc: Literal[69] = 69  # type: ignore[assignment]


class InformeSemestralInrParticipante(Participante):
    """PARTICIPANTE — Part I participant; ``APLICACOES`` belongs to Part II."""

    @field_validator("aplicacoes")
    @classmethod
    def _reject_aplicacoes(cls, v: list[object]) -> list[object]:
        """Refuse applications: the page lists none in Part I.

        Parameters
        ----------
        v : list[object]
            The applications given.

        Returns
        -------
        list[object]
            The empty list.

        Raises
        ------
        ValueError
            If any application was given.
        """
        if v:
            raise ValueError("APLICACOES does not exist in Informe Semestral INR Part I")
        return v


class InformeSemestralInrDocument(InrMensalDocument):
    """DOC_ARQ — a complete Part I file: header plus 1 to 1000 participants."""

    header: InformeSemestralInrHeader
    participantes: list[InformeSemestralInrParticipante]  # type: ignore[assignment]
