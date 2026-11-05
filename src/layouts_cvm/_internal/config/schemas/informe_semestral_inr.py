"""Pydantic models for the Semiannual Non-Resident Investor Report — Part I.

Direction-neutral schema for ``PadraoXMLInfoSemestralINRParte1.asp``
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoSemestralINRParte1.asp;
namespace ``urn:infmensal``, ``COD_DOC=69``, ``VERSAO=1.0``).

Part I has the monthly INR blocks minus ``APLICACOES``, but it is a frozen layout version of its
own: every model is declared here and none inherits from
:mod:`layouts_cvm._internal.config.schemas.inr_mensal`, so a change to the live monthly layout
cannot move Part I's models. The field validators (``utils/inr_mensal_fields.py``) are shared on
purpose: a change there reaches both layouts, so version it before changing a rule for one.
``APLICACOES`` is not a field, so no input can make the writer emit it.

**Field order is the XML order**, as in the monthly schema. Part II (``COD_DOC=70``, the
applications) is **not** modelled here.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    model_validator,
)

from layouts_cvm._internal.utils.inr_mensal_fields import (
    check_br_date,
    check_cvm_code,
    check_month_year,
    check_participant_code,
    whole_amount,
)


_MAX_DIGITS_VALUE = 10**18 - 1
_MAX_PARTICIPANTS = 1000

_AmountField = Annotated[
    int, BeforeValidator(whole_amount), Field(strict=True, ge=0, le=_MAX_DIGITS_VALUE)
]
_SignedAmountField = Annotated[
    int,
    BeforeValidator(whole_amount),
    Field(strict=True, ge=-_MAX_DIGITS_VALUE, le=_MAX_DIGITS_VALUE),
]
_CompetenceField = Annotated[str, AfterValidator(check_month_year)]
_DateField = Annotated[str, AfterValidator(check_br_date)]
_CvmCodeField = Annotated[str, AfterValidator(check_cvm_code)]
_ParticipantCodeField = Annotated[str, AfterValidator(check_participant_code)]


class _Block(BaseModel):
    """Base of every block: closed (no unknown fields) and immutable."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class InformeSemestralInrHeader(_Block):
    """CAB_INFORM — Part I header; ``COD_DOC`` is pinned to ``69``."""

    cod_doc: Literal[69] = 69
    versao: Literal["1.0"] = "1.0"
    cd_cvm: _CvmCodeField
    dt_compt: _CompetenceField
    dt_gerac_arq: _DateField


class EntradaSaida(_Block):
    """ENTRADA_SAIDA — resources in and out during the period (reais)."""

    vl_entr: _AmountField
    vl_saida: _AmountField


class TransfRecursos(_Block):
    """TRANSF_RECURSOS — transfers between investment modalities (reais)."""

    vl_invest_carteira_haver_nres: _AmountField
    vl_haver_nres_invest_carteira: _AmountField
    vl_invest_carteira_adr: _AmountField
    vl_adr_invest_carteira: _AmountField
    vl_invest_carteira_estrang_direta: _AmountField
    vl_estrang_direta_invest_carteira: _AmountField


class RecursosRecebMesmoInvest(_Block):
    """RECURSOS_RECEB_MESMO_INVEST — one resource received from the same investor."""

    cd_partic_origem: _ParticipantCodeField
    vl_recebido: _AmountField


class RecursosEnvMesmoInvest(_Block):
    """RECURSOS_ENV_MESMO_INVEST — one resource sent to the same investor."""

    cd_partic_dest: _ParticipantCodeField
    vl_enviado: _AmountField


class RecursosRecebOutroInvest(_Block):
    """RECURSOS_RECEB_OUTRO_INVEST — one resource received from a different investor."""

    cd_partic_origem: _ParticipantCodeField
    vl_recebido: _AmountField


class RecursosEnvOutroInvest(_Block):
    """RECURSOS_ENV_OUTRO_INVEST — one resource sent to a different investor."""

    cd_partic_dest: _ParticipantCodeField
    vl_enviado: _AmountField


class RecursosMesmoInvest(_Block):
    """RECURSOS_MESMO_INVEST — optional container; omit it when there is nothing to report."""

    recursos_receb_mesmo_invest: list[RecursosRecebMesmoInvest] = Field(default_factory=list)
    recursos_env_mesmo_invest: list[RecursosEnvMesmoInvest] = Field(default_factory=list)

    @model_validator(mode="after")
    def _not_empty(self) -> RecursosMesmoInvest:
        """Refuse an empty container: the page says to omit it instead."""
        if not (self.recursos_receb_mesmo_invest or self.recursos_env_mesmo_invest):
            raise ValueError("omit RECURSOS_MESMO_INVEST when there is no data to report")
        return self


class RecursosOutroInvest(_Block):
    """RECURSOS_OUTRO_INVEST — optional container; omit it when there is nothing to report."""

    recursos_receb_outro_invest: list[RecursosRecebOutroInvest] = Field(default_factory=list)
    recursos_env_outro_invest: list[RecursosEnvOutroInvest] = Field(default_factory=list)

    @model_validator(mode="after")
    def _not_empty(self) -> RecursosOutroInvest:
        """Refuse an empty container: the page says to omit it instead."""
        if not (self.recursos_receb_outro_invest or self.recursos_env_outro_invest):
            raise ValueError("omit RECURSOS_OUTRO_INVEST when there is no data to report")
        return self


class MovRecursos(_Block):
    """MOV_RECURSOS — resource movement during the period."""

    transf_recursos: TransfRecursos
    recursos_mesmo_invest: RecursosMesmoInvest | None = None
    recursos_outro_invest: RecursosOutroInvest | None = None


class InformeSemestralInrParticipante(_Block):
    """PARTICIPANTE — Part I participant; ``APLICACOES`` belongs to Part II, so is absent."""

    cod_partic: _ParticipantCodeField
    entrada_saida: EntradaSaida
    mov_recursos: MovRecursos
    patrim_liq: _SignedAmountField


class InformeSemestralInrDocument(_Block):
    """DOC_ARQ — a complete Part I file: header plus 1 to 1000 participants."""

    header: InformeSemestralInrHeader
    participantes: Annotated[
        list[InformeSemestralInrParticipante],
        Field(min_length=1, max_length=_MAX_PARTICIPANTS),
    ]

    @model_validator(mode="after")
    def _unique_participants(self) -> InformeSemestralInrDocument:
        """Reject the same participant code listed twice."""
        codes = [p.cod_partic for p in self.participantes]
        if len(set(codes)) != len(codes):
            raise ValueError("each participant code may appear only once per file")
        return self

    @model_validator(mode="after")
    def _codes_belong_to_the_representative(self) -> InformeSemestralInrDocument:
        """Require every participant's AAAAA (representative) to equal the header ``CD_CVM``."""
        prefix = self.header.cd_cvm
        stray = [p.cod_partic for p in self.participantes if p.cod_partic.split(".")[0] != prefix]
        if stray:
            raise ValueError(f"participant code prefix must equal header CD_CVM: {stray[0]}")
        return self
