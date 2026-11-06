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
* ``DISTR_PATRIM`` is mandatory, with all 16 ``PR_*`` tags (as in V3).

Every model here is **standalone**: ICVM 739 is a closed historical standard while V3/V4
keep changing, so a validator or type added to a live model must not reach it (PRINCIPLES.md
section 1, DRY caveat). The decimal-scale aliases are copied for the same reason; only the
neutral helpers in ``_fields`` are shared.

**Field order is the XML order**: the writer walks the models in declaration order.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, Field, ValidationInfo, field_validator

from layouts_cvm._internal.config.schemas._fields import (
    truncate_to_scale,
    validate_person_doc,
    validated_br_date_shape,
    validated_cnpj,
    validated_competence,
)


OneDecimalField = Annotated[
    Decimal, BeforeValidator(truncate_to_scale(1)), Field(decimal_places=1)
]
TwoDecimalField = Annotated[
    Decimal, BeforeValidator(truncate_to_scale(2)), Field(decimal_places=2)
]
FiveDecimalField = Annotated[
    Decimal, BeforeValidator(truncate_to_scale(5)), Field(decimal_places=5)
]
VarPercentPlField = Annotated[
    Decimal, BeforeValidator(truncate_to_scale(4)), Field(max_digits=14, decimal_places=4)
]
AvgTermField = Annotated[
    Decimal, BeforeValidator(truncate_to_scale(4)), Field(max_digits=8, decimal_places=4)
]
PercentField = Annotated[
    Decimal,
    BeforeValidator(truncate_to_scale(1)),
    Field(ge=Decimal("0"), le=Decimal("100"), max_digits=4, decimal_places=1),
]


class PerfilMensal739Header(BaseModel):
    """CAB_INFORM — ICVM 739 header; ``VERSAO`` is pinned to ``1.0``, ``COD_DOC`` to ``40``."""

    cod_doc: Literal[40] = 40
    dt_compt: str
    dt_gerac_arq: str
    versao: Literal["1.0"] = "1.0"

    @field_validator("dt_compt")
    @classmethod
    def _check_dt_compt(cls, v: str) -> str:
        """Validate dt_compt format.

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
                If value does not follow MM/AAAA format.
        """
        return validated_competence(v)

    @field_validator("dt_gerac_arq")
    @classmethod
    def _check_dt_gerac_arq(cls, v: str) -> str:
        """Validate dt_gerac_arq format.

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
                If value does not follow DD/MM/AAAA format.
        """
        return validated_br_date_shape(v)


class PerfilMensal739ClientCount(BaseModel):
    """NR_CLIENT — count of clients by investor type (all mandatory, non-negative)."""

    nr_pf_priv_bank: int = Field(ge=0)
    nr_pf_varj: int = Field(ge=0)
    nr_pj_n_financ_priv_bank: int = Field(ge=0)
    nr_pj_n_financ_varj: int = Field(ge=0)
    nr_bnc_comerc: int = Field(ge=0)
    nr_pj_corr_dist: int = Field(ge=0)
    nr_pj_outr_financ: int = Field(ge=0)
    nr_inv_n_res: int = Field(ge=0)
    nr_ent_ab_prev_compl: int = Field(ge=0)
    nr_ent_fc_prev_compl: int = Field(ge=0)
    nr_reg_prev_serv_pub: int = Field(ge=0)
    nr_soc_seg_reseg: int = Field(ge=0)
    nr_soc_captlz_arrendm_merc: int = Field(ge=0)
    nr_fdos_club_inv: int = Field(ge=0)
    nr_cotst_distr_fdo: int = Field(ge=0)
    nr_outros_n_relac: int = Field(ge=0)


class PerfilMensal739PatrimonyDistribution(BaseModel):
    """DISTR_PATRIM — patrimony percentage by client type; all 16 tags are mandatory."""

    pr_pf_priv_bank: PercentField
    pr_pf_varj: PercentField
    pr_pj_n_financ_priv_bank: PercentField
    pr_pj_n_financ_varj: PercentField
    pr_bnc_comerc: PercentField
    pr_pj_corr_dist: PercentField
    pr_pj_outr_financ: PercentField
    pr_inv_n_res: PercentField
    pr_ent_ab_prev_compl: PercentField
    pr_ent_fc_prev_compl: PercentField
    pr_reg_prev_serv_pub: PercentField
    pr_soc_seg_reseg: PercentField
    pr_soc_captlz_arrendm_merc: PercentField
    pr_fdos_club_inv: PercentField
    pr_cotst_distr_fdo: PercentField
    pr_outros_n_relac: PercentField


class PerfilMensal739PrimitiveRiskFactor(BaseModel):
    """FATOR_PRIMIT_RISCO — one BM&FBOVESPA primitive risk factor entry."""

    nome_fator_primit_risco: Literal["IBOVESPA", "JUROS-PRE", "CUPOM CAMBIAL", "DOLAR", "OUTROS"]
    cen_util: str = Field(max_length=150)


class PerfilMensal739VarPercValCota(BaseModel):
    """VARIACAO_PERC_VAL_COTA — stress scenario block with primitive risk factors."""

    val_percent: TwoDecimalField
    lista_fator_primit_risco: list[PerfilMensal739PrimitiveRiskFactor] = Field(max_length=5)


class PerfilMensal739VarOutros(BaseModel):
    """VARIACAO_DIAR_PERC_PATRIM_FDO_VAR_N_OUTROS — ``VAL_PERCENT_OUTROS`` has 2 decimals."""

    fator_risco_outros: str = Field(max_length=400)
    val_percent_outros: TwoDecimalField


class PerfilMensal739NominalRiskFactor(BaseModel):
    """FATOR_RISCO_NOC — one notional derivatives risk factor (long and short legs)."""

    nome_fator_noc: Literal["IBOVESPA", "JUROS-PRE", "CUPOM CAMBIAL", "DOLAR", "OUTROS"]
    val_fator_risco_noc_long: int = Field(ge=0)
    val_fator_risco_noc_short: int = Field(ge=0)


class PerfilMensal739NominalRiskBlock(BaseModel):
    """VALOR_NOC_TOT_CONTRAT_DERIV_MANT_FDO — OTC derivatives notional exposure block."""

    val_colateral: TwoDecimalField
    lista_fator_risco_noc: list[PerfilMensal739NominalRiskFactor] = Field(max_length=5)


class PerfilMensal739OtcOperation(BaseModel):
    """OPER_CURS_MERC_BALCAO — one top-3 OTC counterparty without central clearing."""

    tp_pessoa: Literal["PF", "PJ"]
    nr_pf_pj_comitente: str
    parte_relacionada: Literal["S", "N"]
    valor_parte: OneDecimalField

    @field_validator("nr_pf_pj_comitente")
    @classmethod
    def _check_comitente_doc(cls, v: str, info: ValidationInfo) -> str:
        """Validate and normalise the counterparty document against its person type.

        Parameters
        ----------
        v : str
                The counterparty document (CPF or CNPJ) in any shape.
        info : ValidationInfo
                Validation context; ``tp_pessoa`` (declared first) is read from it.

        Returns
        -------
        str
                The document in bare, unmasked form.

        Raises
        ------
        ValueError
                If the document is not a valid CPF (PF) or CNPJ (PJ).
        """
        return validate_person_doc(info.data.get("tp_pessoa", ""), v)


class PerfilMensal739PrivateCreditIssuer(BaseModel):
    """EMISSORES_TIT_CRED_PRIV — one top-3 private credit issuer held by the fund class."""

    tp_pessoa_emissor: Literal["PF", "PJ"]
    nr_pf_pj_emissor: str
    parte_relacionada: Literal["S", "N"]
    valor_parte: OneDecimalField

    @field_validator("nr_pf_pj_emissor")
    @classmethod
    def _check_emissor_doc(cls, v: str, info: ValidationInfo) -> str:
        """Validate and normalise the issuer document against its person type.

        Parameters
        ----------
        v : str
                The issuer document (CPF or CNPJ) in any shape.
        info : ValidationInfo
                Validation context; ``tp_pessoa_emissor`` (declared first) is read from it.

        Returns
        -------
        str
                The document in bare, unmasked form.

        Raises
        ------
        ValueError
                If the document is not a valid CPF (PF) or CNPJ (PJ).
        """
        return validate_person_doc(info.data.get("tp_pessoa_emissor", ""), v)


class PerfilMensal739PerformanceFeeDetails(BaseModel):
    """RESP_VED_REGUL_COBR_TAXA_PERFORM — date and NAV of the last performance fee charge."""

    data_cota_fundo: str
    val_cota_fundo: FiveDecimalField

    @field_validator("data_cota_fundo")
    @classmethod
    def _check_date(cls, v: str) -> str:
        """Validate date format.

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
                If value does not follow DD/MM/AAAA format.
        """
        return validated_br_date_shape(v)


class PerfilMensal739Row(BaseModel):
    """ROW_PERFIL — ICVM 739 fund block.

    The page has no ``MONTANTE_DISTRIB`` / ``INF_COMPL_PERFIL``: they are typed ``None`` so
    a value is rejected instead of silently dropped.
    """

    cnpj_fdo: str
    nr_client: PerfilMensal739ClientCount
    distr_patrim: PerfilMensal739PatrimonyDistribution
    resm_teor_vt_profrd: str | None = Field(default=None, max_length=4000)
    just_sum_vt_profrd: str | None = Field(default=None, max_length=4000)
    var_perc_pl: VarPercentPlField | None = None
    mod_var_utiliz: Literal["1", "2", "3"] | None = None
    praz_med_cart_tit: AvgTermField | None = None
    res_delib: str | None = Field(default=None, max_length=4000)
    total_recurs_exter: TwoDecimalField
    total_recurs_br: TwoDecimalField
    variacao_perc_val_cota: PerfilMensal739VarPercValCota | None = None
    var_diar_perc_cota_fdo_pior_cen_estress: TwoDecimalField | None = None
    var_diar_perc_patrim_fdo_var_n_taxa_anual: TwoDecimalField | None = None
    var_diar_perc_patrim_fdo_var_n_taxa_cambio: TwoDecimalField | None = None
    var_patrim_fdo_n_preco_acoes: TwoDecimalField | None = None
    variacao_diar_perc_patrim_fdo_var_n_outros: PerfilMensal739VarOutros | None = None
    valor_noc_tot_contrat_deriv_mant_fdo: PerfilMensal739NominalRiskBlock | None = None
    lista_oper_curs_merc_balcao: list[PerfilMensal739OtcOperation] | None = Field(
        default=None, max_length=3
    )
    tot_ativos_p_relac: OneDecimalField
    lista_emissores_tit_cred_priv: list[PerfilMensal739PrivateCreditIssuer] | None = Field(
        default=None, max_length=3
    )
    tot_ativos_cred_priv: OneDecimalField
    ved_regul_cobr_taxa_perform: Literal["S", "N"] | None = None
    resp_ved_regul_cobr_taxa_perform: PerfilMensal739PerformanceFeeDetails | None = None
    montante_distrib: None = None
    inf_compl_perfil: None = None

    @field_validator("cnpj_fdo")
    @classmethod
    def _check_cnpj(cls, v: str) -> str:
        """Validate and normalise the fund-class CNPJ (check-digit aware).

        Parameters
        ----------
        v : str
                Value to validate.

        Returns
        -------
        str
                The unmasked (bare) CNPJ.

        Raises
        ------
        ValueError
                If value is not a valid CNPJ.
        """
        return validated_cnpj(v)


class PerfilMensal739Document(BaseModel):
    """DOC_ARQ — complete ICVM 739 document."""

    header: PerfilMensal739Header
    rows: list[PerfilMensal739Row]
