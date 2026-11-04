"""Pydantic models for the CVM Informe Anual de Auditor XML standard.

Direction-neutral schema for ``PadraoXMLAuditorAnual.asp``
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLAuditorAnual.asp). One file holds
the report of a single auditor for a single base year.

**Field order is the XML order.** The writer walks ``model_fields`` in declaration order and
names each element ``<FIELD_NAME.upper()>``, so every field is the lower-cased tag from the
page's sample file. A repeating element sits inside a ``Lista*`` wrapper block, as in the sample.

The page's training blocks (``LISTA_TREINA`` and Tables C and D) are commented out of the live
HTML, so they are not modelled. What the page leaves unsaid is decided here and stated on
``docs/informe_anual_auditor.md``.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

from layouts_cvm._internal.config.schemas._fields import validate_person_doc, validated_cnpj
from layouts_cvm._internal.utils.xml_fields import (
    check_br_date,
    check_cnpj_shape,
    check_xml_text,
    require,
    strict_decimal,
)


_MAX_ADDRESSES = 1000
_MAX_AUDITED = 8000
_MAX_AFFILIATED = 1000
_MONEY_PLACES = 2
_MONEY_DIGITS = 18
_PERCENT_MAX = Decimal(100)
_INT_MAX = 999_999_999_999
_AUDITED_TYPES = frozenset(
    {1, 5, 7, 14, 17, 20, 22, 23, 25, 27, 30, 32, 43, 45, 47, 48, 50, 52, 55, 57, 60, 61, 63}
    | {67, 69, 70, 72, 73, 74, 75, 77, 80, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95}
    | {96, 98, 99}
)


_XML_TEXT = AfterValidator(check_xml_text)
_Text18 = Annotated[str, StringConstraints(min_length=1, max_length=18), _XML_TEXT]
_Text30 = Annotated[str, StringConstraints(min_length=1, max_length=30), _XML_TEXT]
_Text50 = Annotated[str, StringConstraints(min_length=1, max_length=50), _XML_TEXT]
_Text100 = Annotated[str, StringConstraints(min_length=1, max_length=100), _XML_TEXT]
_Text500 = Annotated[str, StringConstraints(min_length=1, max_length=500), _XML_TEXT]
_TextOpen = Annotated[str, StringConstraints(min_length=1), _XML_TEXT]
_Money = Annotated[
    Decimal,
    BeforeValidator(strict_decimal(_MONEY_PLACES)),
    Field(ge=Decimal(0), max_digits=_MONEY_DIGITS, decimal_places=_MONEY_PLACES),
]
_Percent = Annotated[
    Decimal,
    BeforeValidator(strict_decimal(_MONEY_PLACES)),
    Field(ge=Decimal(0), le=_PERCENT_MAX, max_digits=_MONEY_DIGITS, decimal_places=_MONEY_PLACES),
]
_Count = Annotated[int, Field(strict=True, ge=0, le=_INT_MAX)]
_Code = Annotated[int, Field(strict=True, ge=1, le=_INT_MAX)]
_Year = Annotated[int, Field(strict=True, ge=1900, le=9999)]
_Date = Annotated[str, AfterValidator(check_br_date)]
_Cnpj = Annotated[str, AfterValidator(check_cnpj_shape), AfterValidator(validated_cnpj)]
_Digits = Annotated[str, Field(pattern=r"\A[0-9]+\z")]
_Cpf = Annotated[str, Field(pattern=r"\A[0-9]{11}\z")]


class _Block(BaseModel):
    """Base of every block: closed (no unknown fields) and immutable."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class AuditorHeader(_Block):
    """DS_INFORM — base year, generation date and reason for delivery."""

    ano_base: _Year
    dt_gerac_arq: _Date
    motivo_entreg: Literal[1, 2, 3]


class AuditorIdentity(_Block):
    """DS_AUDIT — who the auditor is."""

    tp_pf_pj: Literal["PF", "PJ"]
    nr_pf_pj: Annotated[str, Field(min_length=1)]
    cd_cvm: _Code
    ds_nome: _Text100
    ds_email: _Text50

    @model_validator(mode="after")
    def _check_document(self) -> AuditorIdentity:
        """Require a valid CPF (PF) or CNPJ (PJ) written without dots, dashes or slashes.

        Returns
        -------
        AuditorIdentity
            The validated block.
        """
        bare = validate_person_doc(self.tp_pf_pj, self.nr_pf_pj)
        require(bare == self.nr_pf_pj, "nr_pf_pj must omit dots, dashes and slashes")
        return self


class AuditorAddress(_Block):
    """ENDER — the head office (1) or a branch (2)."""

    tp_ender: Literal[1, 2]
    nm_filial: _Text100 | None = None
    nm_lograd: _Text30
    ds_compl: _Text18 | None = None
    ds_bairro: _Text30
    cd_mun: _Code
    nr_cep: _Digits
    nr_ddd_tel: _Digits | None = None
    nr_tel: _Digits | None = None
    nr_ddd_fax: _Digits | None = None
    nr_fax: _Digits | None = None

    @model_validator(mode="after")
    def _check_head_office_has_no_branch_name(self) -> AuditorAddress:
        """Require ``nm_filial`` to be omitted for the head office.

        Returns
        -------
        AuditorAddress
            The validated block.
        """
        require(
            self.tp_ender != 1 or self.nm_filial is None,
            "nm_filial must be omitted for the head office (tp_ender 1)",
        )
        return self


class ListaEnder(_Block):
    """LISTA_ENDER — head office plus branches (1 to 1000)."""

    ender: list[AuditorAddress] = Field(min_length=1, max_length=_MAX_ADDRESSES)


class Responsible(_Block):
    """RESP — a partner who represents the auditor firm."""

    nr_pf: Annotated[_Cpf, AfterValidator(lambda str_v: validate_person_doc("PF", str_v))]
    ds_nome: _Text100
    ds_email: _Text50


class ListaResp(_Block):
    """LISTA_RESP — the representative partners (legal-entity auditors only)."""

    resp: list[Responsible] = Field(default_factory=list)


class AuditedEntity(_Block):
    """ENTID_AUDITA — one audited entity."""

    tp_entid: Annotated[int, Field(strict=True)]
    nr_pj: _Cnpj
    ds_nome: _TextOpen
    dt_contr: _Date | None = None
    pr_fatura: _Percent | None = None

    @model_validator(mode="after")
    def _check_entity_type(self) -> AuditedEntity:
        """Require ``tp_entid`` to be a code of the page's Table B.

        Returns
        -------
        AuditedEntity
            The validated block.
        """
        require(self.tp_entid in _AUDITED_TYPES, f"tp_entid {self.tp_entid} is not in Table B")
        return self


class ListaEntidAudita(_Block):
    """LISTA_ENTID_AUDITA — audited entities (0 to 8000)."""

    entid_audita: list[AuditedEntity] = Field(default_factory=list, max_length=_MAX_AUDITED)


class AnnualBilling(_Block):
    """FATURA_ANUAL — audit billing and hours worked."""

    vl_audit: _Money
    pr_audit: _Percent
    hh_audit: _Count


class HumanResources(_Block):
    """RH — partners and permanent technical staff."""

    qt_socios: _Count | None = None
    qt_func_tecno: _Count


class AffiliatedEntity(_Block):
    """ENTID_COLIG — one affiliated entity."""

    st_estr: Literal["S", "N"]
    nr_pj: _Cnpj | None = None
    ds_nome: _Text100
    ds_setor_ativd: _Text30

    @model_validator(mode="after")
    def _check_cnpj_follows_origin(self) -> AffiliatedEntity:
        """Require ``nr_pj`` for a Brazilian entity and omit it for a foreign one.

        Returns
        -------
        AffiliatedEntity
            The validated block.
        """
        require(
            (self.st_estr == "S") == (self.nr_pj is None),
            "nr_pj is required unless the entity is foreign (st_estr S), when it must be omitted",
        )
        return self


class ListaEntidColig(_Block):
    """LISTA_ENTID_COLIG — affiliated entities (0 to 1000)."""

    entid_colig: list[AffiliatedEntity] = Field(default_factory=list, max_length=_MAX_AFFILIATED)


class InformAudit(_Block):
    """INFORM_AUDIT — the whole annual report of one auditor."""

    ds_inform: AuditorHeader
    ds_audit: AuditorIdentity
    lista_ender: ListaEnder
    lista_resp: ListaResp | None = None
    lista_entid_audita: ListaEntidAudita = Field(default_factory=ListaEntidAudita)
    qt_outra_entid_audita: _Count
    fatura_anual: AnnualBilling
    ds_criter_honor: _Text500
    rh: HumanResources
    lista_entid_colig: ListaEntidColig = Field(default_factory=ListaEntidColig)

    @model_validator(mode="after")
    def _check_natural_person_rules(self) -> InformAudit:
        """Apply the page's rules for a natural-person (PF) auditor.

        A PF sends one address, with no branch name, no responsible partners and no partner
        count.

        Returns
        -------
        InformAudit
            The validated block.
        """
        if self.ds_audit.tp_pf_pj == "PF":
            addresses = self.lista_ender.ender
            require(len(addresses) == 1, "a PF auditor sends exactly one address")
            require(addresses[0].nm_filial is None, "nm_filial must be omitted for a PF auditor")
            require(self.lista_resp is None, "lista_resp must be omitted for a PF auditor")
            require(self.rh.qt_socios is None, "qt_socios must be omitted for a PF auditor")
        return self


class InformeAnualAuditorDocument(_Block):
    """DOC_ARQ — a whole file: one auditor, one base year."""

    cod_doc: Literal[23] = 23
    inform_audit: InformAudit
