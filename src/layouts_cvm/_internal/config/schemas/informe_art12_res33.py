"""Pydantic models for the CVM Informe Art. 12 Resolução CVM 33 (escriturador) XML standard.

Direction-neutral contract for ``PadraoXMLPrest.asp``
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLPrest.asp). The file is
``DOC_ARQ`` (namespace ``urn:prestserv``) holding ``COD_ARQ`` (always ``29``), the ``DS_INFORM``
header, and a ``LISTA_PREST`` of ``INFORM_PREST`` blocks, each with a ``DS_PREST`` and a
``LISTA_EMISSORES`` of ``EMISSOR`` blocks that repeat ``ATIVO``.

The page states no decimal field. ``DT_COMPT`` is ``MM/AAAA``; every other date is
``DD/MM/AAAA``. The page says the file may carry several providers "desde que sejam de uma mesma
competência", which is structural here: there is one ``DS_INFORM`` per document.

**Field order is the XML order**: the writer walks ``model_fields`` in declaration order.
"""

from __future__ import annotations

from datetime import datetime
import re
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from layouts_cvm._internal.config.schemas._fields import validated_cnpj
from layouts_cvm._internal.utils.typing import type_checker


_DATE_RE = re.compile(r"[0-9]{2}/[0-9]{2}/[0-9]{4}")
_MONTH_RE = re.compile(r"[0-9]{2}/[0-9]{4}")
_DATE_FMT = "%d/%m/%Y"

ProviderType = Literal[41, 42, 52, 65]
AssetType = Literal["A1", "A2", "A3", "A4"]


@type_checker
def _parse_date(value: str) -> datetime:
    """Parse a strict ``DD/MM/AAAA`` text into a datetime.

    Parameters
    ----------
    value : str
            The date text.

    Returns
    -------
    datetime
            The parsed date.

    Raises
    ------
    ValueError
            If the shape is wrong or the date does not exist.
    """
    if not _DATE_RE.fullmatch(value):
        raise ValueError("date must follow DD/MM/AAAA")
    return datetime.strptime(value, _DATE_FMT)  # noqa: DTZ007  (calendar check only)


class DsInform(BaseModel):
    """DS_INFORM — document header: competence month and file generation date."""

    model_config = ConfigDict(extra="forbid")

    dt_compt: str
    dt_gerac_arq: str

    @field_validator("dt_compt")
    @classmethod
    def _check_dt_compt(cls, v: str) -> str:
        """Require a real ``MM/AAAA`` month.

        Parameters
        ----------
        v : str
                Value to validate.

        Returns
        -------
        str
                The unchanged value.

        Raises
        ------
        ValueError
                If the shape is wrong or the month is not 01-12.
        """
        if not _MONTH_RE.fullmatch(v):
            raise ValueError("dt_compt must follow MM/AAAA")
        _parse_date(f"01/{v}")
        return v

    @field_validator("dt_gerac_arq")
    @classmethod
    def _check_dt_gerac_arq(cls, v: str) -> str:
        """Require a real ``DD/MM/AAAA`` date.

        Parameters
        ----------
        v : str
                Value to validate.

        Returns
        -------
        str
                The unchanged value.
        """
        _parse_date(v)
        return v


class Ativo(BaseModel):
    """ATIVO — one escriturated asset type and its contract dates with the provider."""

    model_config = ConfigDict(extra="forbid")

    ativo_escriturado: AssetType
    dt_inicio_contrato: str
    dt_fim_contrato: str | None = None

    @field_validator("dt_inicio_contrato", "dt_fim_contrato")
    @classmethod
    def _check_date(cls, v: str | None) -> str | None:
        """Require a real ``DD/MM/AAAA`` date when one is given.

        Parameters
        ----------
        v : Optional[str]
                Value to validate.

        Returns
        -------
        Optional[str]
                The unchanged value.
        """
        if v is not None:
            _parse_date(v)
        return v

    @model_validator(mode="after")
    def _check_contract_span(self) -> Self:
        """Reject a contract that ends before it starts.

        Returns
        -------
        Self
                The validated model.

        Raises
        ------
        ValueError
                If ``DT_FIM_CONTRATO`` precedes ``DT_INICIO_CONTRATO``.
        """
        if self.dt_fim_contrato and _parse_date(self.dt_fim_contrato) < _parse_date(
            self.dt_inicio_contrato
        ):
            raise ValueError("dt_fim_contrato must not precede dt_inicio_contrato")
        return self


class Emissor(BaseModel):
    """EMISSOR — one issuer client and the asset types escriturated for it."""

    model_config = ConfigDict(extra="forbid")

    cnpj_emissor: str
    ativo: Annotated[list[Ativo], Field(min_length=1)]

    @field_validator("cnpj_emissor")
    @classmethod
    def _check_cnpj(cls, v: str) -> str:
        """Validate and normalise the issuer CNPJ (check-digit aware).

        Parameters
        ----------
        v : str
                The issuer CNPJ in any shape.

        Returns
        -------
        str
                The unmasked (bare) CNPJ.
        """
        return validated_cnpj(v)


class DsPrest(BaseModel):
    """DS_PREST — the service provider (escriturador) identity."""

    model_config = ConfigDict(extra="forbid")

    cnpj_escriturador: str
    cd_tp_prest: ProviderType

    @field_validator("cnpj_escriturador")
    @classmethod
    def _check_cnpj(cls, v: str) -> str:
        """Validate and normalise the provider CNPJ (check-digit aware).

        Parameters
        ----------
        v : str
                The provider CNPJ in any shape.

        Returns
        -------
        str
                The unmasked (bare) CNPJ.
        """
        return validated_cnpj(v)


class Prestador(BaseModel):
    """INFORM_PREST — one provider and its issuer clients (``LISTA_EMISSORES``)."""

    model_config = ConfigDict(extra="forbid")

    ds_prest: DsPrest
    emissores: Annotated[list[Emissor], Field(min_length=1)]


class InformeArt12Res33Document(BaseModel):
    """DOC_ARQ — complete document: ``COD_ARQ`` 29, header and at least one provider."""

    model_config = ConfigDict(extra="forbid")

    cod_arq: Literal[29] = 29
    ds_inform: DsInform
    prestadores: Annotated[list[Prestador], Field(min_length=1)]
