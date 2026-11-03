"""Pydantic models for the CVM CDA XML standard — V3.

V3 is described by the CVM page
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLCDANetV3.aspx; namespace
``urn:cda``, ``COD_DOC=3``, ``VERSAO=3.0``). Measured against the V4 page
(``PadraoXMLCDANetV4.aspx``) and the V4 schema in
:mod:`layouts_cvm._internal.config.schemas.cda`, the
tables (A, B, C, D, E, F, G, H), the block x application-type table, the decimal scales and
the tag order are identical. Only these differ:

* ``VERSAO`` is ``3.0`` (``COD_DOC`` stays ``3``).
* A file holds at most **50** funds (V4: 1000).
* ``COTAS`` is identified **only** by ``CNPJ_FDO``; ``COD_SUBCLASSE`` does not exist.
* ``DEP_PRAZO_TIT_IF`` has no ``DESC_ATIV_VINC``.
* ``INV_EXT`` has no ``INV_COLETIVO`` nor ``GEST_INV_COLETIVO``, and its ``APLIC`` has no
  ``ATIVO_EXT``.

Every other block is shared, so the V3 models extend the V4 ones rather than copying them.
A field that V3 lacks stays on the model (a subclass cannot drop it) but is rejected when set,
so the writer never emits its tag.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, ValidationInfo, field_validator

from layouts_cvm._internal.config.schemas.cda import (
    CdaAplic,
    CdaCotas,
    CdaDepPrazoTitIf,
    CdaDocument,
    CdaHeader,
    CdaInform,
    CdaInvExt,
)
from layouts_cvm._internal.utils.typing import type_checker


_MAX_INFORMS = 50


@type_checker
def _reject_field(name: str, value: object) -> object:
    """Refuse a field the V3 standard does not define.

    Parameters
    ----------
    name : str
        The schema field name, for the message.
    value : object
        The value given; it must be absent.

    Returns
    -------
    object
        The same (absent) value.

    Raises
    ------
    ValueError
        If a value was given.
    """
    if value is not None:
        raise ValueError(f"{name} does not exist in CDA V3")
    return value


class CdaV3Header(CdaHeader):
    """CAB_INFORM — V3 header; ``VERSAO`` is pinned to ``3.0`` and ``COD_DOC`` to ``3``."""

    versao: Literal["3.0"] = "3.0"  # type: ignore[assignment]


class CdaV3Aplic(CdaAplic):
    """APLIC — V3 application; ``ATIVO_EXT`` does not exist."""

    @field_validator("ativo_ext")
    @classmethod
    def _reject_ativo_ext(cls, v: object, info: ValidationInfo) -> object:
        """Reject ``ATIVO_EXT``.

        Parameters
        ----------
        v : object
            The value given.
        info : ValidationInfo
            Pydantic context, for the field name.

        Returns
        -------
        object
            ``None``.
        """
        return _reject_field(str(info.field_name), v)


class CdaV3Cotas(CdaCotas):
    """COTAS — V3 fund shares, keyed by ``CNPJ_FDO`` only (no ``COD_SUBCLASSE``)."""

    cnpj_fdo: str

    @field_validator("cod_subclasse")
    @classmethod
    def _reject_subclasse(cls, v: object, info: ValidationInfo) -> object:
        """Reject ``COD_SUBCLASSE``.

        Parameters
        ----------
        v : object
            The value given.
        info : ValidationInfo
            Pydantic context, for the field name.

        Returns
        -------
        object
            ``None``.
        """
        return _reject_field(str(info.field_name), v)


class CdaV3DepPrazoTitIf(CdaDepPrazoTitIf):
    """DEP_PRAZO_TIT_IF — V3 block; ``DESC_ATIV_VINC`` does not exist."""

    @field_validator("desc_ativ_vinc")
    @classmethod
    def _reject_desc_ativ_vinc(cls, v: object, info: ValidationInfo) -> object:
        """Reject ``DESC_ATIV_VINC``.

        Parameters
        ----------
        v : object
            The value given.
        info : ValidationInfo
            Pydantic context, for the field name.

        Returns
        -------
        object
            ``None``.
        """
        return _reject_field(str(info.field_name), v)


class CdaV3InvExt(CdaInvExt):
    """INV_EXT — V3 block; no ``INV_COLETIVO``, ``GEST_INV_COLETIVO`` or ``ATIVO_EXT``."""

    inv_coletivo: Literal["S", "N"] | None = None  # type: ignore[assignment]
    gest_inv_coletivo: Literal["S", "N"] | None = None  # type: ignore[assignment]
    aplic: CdaV3Aplic

    @field_validator("inv_coletivo", "gest_inv_coletivo")
    @classmethod
    def _reject_collective(cls, v: object, info: ValidationInfo) -> object:
        """Reject the collective-vehicle flags.

        Parameters
        ----------
        v : object
            The value given.
        info : ValidationInfo
            Pydantic context, for the field name.

        Returns
        -------
        object
            ``None``.
        """
        return _reject_field(str(info.field_name), v)


class CdaV3Inform(CdaInform):
    """INFORM — V3 fund block, with the V3 variants of the blocks that changed."""

    cotas: list[CdaV3Cotas] = Field(default_factory=list)  # type: ignore[assignment]
    dep_prazo_tit_if: list[CdaV3DepPrazoTitIf] = Field(  # type: ignore[assignment]
        default_factory=list
    )
    inv_ext: list[CdaV3InvExt] = Field(default_factory=list)  # type: ignore[assignment]


class CdaV3Document(CdaDocument):
    """DOC_ARQ — complete V3 file (at most 50 funds, one competence)."""

    header: CdaV3Header
    informs: list[CdaV3Inform] = Field(max_length=_MAX_INFORMS)  # type: ignore[assignment]
