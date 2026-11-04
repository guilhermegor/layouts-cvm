"""Pydantic models for the CVM Informe Mensal FIDC XML standard (ICVM 489, until 2019-11-01).

Private document model of one CVM standard; it ships in the wheel under ``_internal`` but is
not part of the public API (the writer takes plain data and validates it into these models).

The authoritative source is the CVM page
https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLMensalFIDC489.asp
(root ``DOC_ARQ`` in the ``urn:fidc`` namespace, ``windows-1252``; one file = one fund and
one month). Where the page shows the same block as the ICVM 576 page, that block is imported
from :mod:`layouts_cvm._internal.config.schemas.inf_mensal_fidc` rather than copied; the
page was compared tag by tag, and only the blocks below differ:

* ``CAB_INFORM`` has six tags (no redemption terms);
* ``APLIC_ATIVO`` has no cedent list under ``CRED_EXISTE``, no ``VL_PVS_*`` provisions, and
  ``DICRED`` has only ``VL_DICRED`` and ``VL_DICRED_CEDENT``;
* ``OUTRAS_INFORM`` is the older table: ``QT_COTISTAS_SUBORD``, ``*_SENIOR_SERIE`` / ``*_SUBORD``
  blocks, ``RENT_MES`` with ``PR_APURADA_SENIOR`` / ``PR_APURADA_SUBORD``, and no
  ``NUM_COTISTAS_DESC`` or ``GARANTIA``.

Conventions, all from the page: monetary, quantity and percentage fields carry **2** decimal
places, the quota quantities and unit values (``QT_COTAS``/``VL_COTAS`` of the series blocks,
``QT_COTAS`` of the movements, ``VL_COTA`` of the amortisations) carry up to **8**. Excess
precision is truncated toward zero, never rounded. The ``SOMATÓRIO`` tags (items 1-31) must
equal the sum the page prescribes, and the page's "auxílio para validação" rules are enforced.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BeforeValidator, Field, field_validator, model_validator

from layouts_cvm._internal.config.schemas._fields import validated_cnpj
from layouts_cvm._internal.config.schemas.inf_mensal_fidc import (
    _COMPETENCE_RE,
    Amortizacao,
    CartSegmt,
    CompmtDicred,
    CotasMovimento,
    Count,
    CredExiste,
    InformSacados,
    Liquidez,
    ListaCedent,
    MercDerivativo,
    Money,
    NegocDicredMes,
    OutrosAtivos,
    Passiv,
    Patrliq,
    SerieClasse,
    TaxaNegocDicredMes,
    ValoresMob,
    _FidcBlock,
    _require_sum,
)


class InfMensalFidc489Header(_FidcBlock):
    """CAB_INFORM — fund identification (no redemption terms in this version)."""

    dt_compt: str
    nr_cnpj_adm: Annotated[str, BeforeValidator(validated_cnpj)]
    nr_cnpj_fundo: Annotated[str, BeforeValidator(validated_cnpj)]
    tp_condominio: Literal["ABERTO", "FECHADO"]
    fdo_excl: Literal["SIM", "NAO"]
    cotst_vincul: Literal["SIM", "NAO"]

    @field_validator("dt_compt")
    @classmethod
    def _check_competence(cls, v: str) -> str:
        """Validate DT_COMPT follows ``MM/AAAA``.

        Parameters
        ----------
        v : str
                Value to validate.

        Returns
        -------
        str
                The validated value.

        Raises
        ------
        ValueError
                If the value is not ``MM/AAAA``.
        """
        if not _COMPETENCE_RE.match(v):
            raise ValueError(f"expected MM/AAAA, got {v!r}")
        return v


class Dicred489(_FidcBlock):
    """DICRED — rights acquired without substantial transfer of risks and benefits."""

    vl_dicred: Money
    vl_dicred_cedent: Money


class AplicAtivo489(_FidcBlock):
    """APLIC_ATIVO — assets (no provisions, no cedent list under CRED_EXISTE)."""

    vl_disponib: Money
    vl_carteira: Money
    cred_existe: CredExiste
    dicred: Dicred489
    lista_cedent: ListaCedent | None = None
    valores_mob: ValoresMob
    vl_titpub_fed: Money
    vl_cdb: Money
    vl_aplic_oper_compss: Money
    vl_ativ_financ_rf: Money
    vl_cota_fidc: Money
    vl_cota_fidc_nao_padrao: Money
    vl_contr_compra_venda_prestc_futura: Money
    merc_derivativo: MercDerivativo
    outros_ativos: OutrosAtivos
    vl_som_aplic_ativo: Money

    @model_validator(mode="after")
    def _check_items_1_and_2(self) -> AplicAtivo489:
        """Check item 2 (somatório de carteira) and item 1 (somatório de ativos).

        Returns
        -------
        AplicAtivo489
                The validated block.
        """
        _require_sum(
            "VL_CARTEIRA (item 2)",
            self.vl_carteira,
            [
                self.cred_existe.vl_som_dicred_aquis,
                self.dicred.vl_dicred,
                self.valores_mob.vl_som_valores_mob,
                self.vl_titpub_fed,
                self.vl_cdb,
                self.vl_aplic_oper_compss,
                self.vl_ativ_financ_rf,
                self.vl_cota_fidc,
                self.vl_cota_fidc_nao_padrao,
                self.vl_contr_compra_venda_prestc_futura,
            ],
            [],
        )
        _require_sum(
            "VL_SOM_APLIC_ATIVO (item 1)",
            self.vl_som_aplic_ativo,
            [
                self.vl_disponib,
                self.vl_carteira,
                self.merc_derivativo.vl_som_merc_derivativo,
                self.outros_ativos.vl_som_outros_ativos,
                self.merc_derivativo.vl_depos_margem,
            ],
            [],
        )
        return self


class NumCotistas489(_FidcBlock):
    """NUM_COTISTAS — number of quota holders (``QT_COTISTAS_SUBORD`` repeats per item 31)."""

    qt_total_cotistas: Count
    qt_total_cotistas_senior: Count
    qt_total_cotistas_subord: Count
    qt_cotistas_subord: list[Count] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_items_30_and_31(self) -> NumCotistas489:
        """Check item 30 (senior + subordinate) and item 31 (subordinate 1..n).

        Returns
        -------
        NumCotistas489
                The validated block.
        """
        _require_sum(
            "QT_TOTAL_COTISTAS (item 30)",
            Decimal(self.qt_total_cotistas),
            [Decimal(self.qt_total_cotistas_senior), Decimal(self.qt_total_cotistas_subord)],
            [],
        )
        _require_sum(
            "QT_TOTAL_COTISTAS_SUBORD (item 31)",
            Decimal(self.qt_total_cotistas_subord),
            [Decimal(n) for n in self.qt_cotistas_subord],
            [],
        )
        return self


class RentMes489(_FidcBlock):
    """RENT_MES — return in the month, in percent (``9,0``, not ``0,09``)."""

    pr_apurada_senior: Money
    pr_apurada_subord: Money


class DesempClasse489(_FidcBlock):
    """DESEMP_SENIOR / DESEMP_SUBORD — expected vs realised performance, in percent."""

    desemp_esp: Money
    desemp_real: Money


class OutrasInform489(_FidcBlock):
    """OUTRAS_INFORM — other information. Only the senior class is guaranteed by the page.

    The page: "Não aceitar o informe sem o preenchimento do campo (CLASSE SENIOR), pois todos
    os fundos possuem no mínimo cota sênior", so every ``*_SUBORD`` block is optional and every
    ``*_SENIOR_SERIE`` block is required.
    """

    num_cotistas: NumCotistas489
    desc_serie_classe_senior_serie: list[SerieClasse] = Field(min_length=1)
    desc_serie_classe_subord: list[SerieClasse] = Field(default_factory=list)
    rent_mes: RentMes489
    capt_mes_senior_serie: CotasMovimento
    capt_mes_subord: CotasMovimento | None = None
    resg_mes_senior_serie: CotasMovimento
    resg_mes_subord: CotasMovimento | None = None
    resg_solic_senior_serie: CotasMovimento
    resg_solic_subord: CotasMovimento | None = None
    amort_senior_serie: Amortizacao
    amort_subord: Amortizacao | None = None
    liquidez: Liquidez | None = None
    desemp_senior: DesempClasse489
    desemp_subord: DesempClasse489 | None = None


class InfMensalFidc489Inform(_FidcBlock):
    """LISTA_INFORM — the single informe of the file (one fund, one month)."""

    aplic_ativo: AplicAtivo489
    cart_segmt: CartSegmt
    passiv: Passiv
    patrliq: Patrliq
    compmt_dicred_aquis: CompmtDicred
    compmt_dicred_sem_aquis: CompmtDicred
    negoc_dicred_mes: NegocDicredMes
    inform: InformSacados
    taxa_negoc_dicred_mes: TaxaNegocDicredMes
    outras_inform: OutrasInform489

    @model_validator(mode="after")
    def _check_maturity_and_delinquency_cross_totals(self) -> InfMensalFidc489Inform:
        """Check the page's cross-block validation of the maturity and default totals.

        The page states both rules in terms of the "Créditos Existentes" tags only, so
        they bind ``COMPMT_DICRED_AQUIS``; ``COMPMT_DICRED_SEM_AQUIS`` has no stated rule.

        Returns
        -------
        InfMensalFidc489Inform
                The validated block.
        """
        ce = self.aplic_ativo.cred_existe
        block = self.compmt_dicred_aquis
        _require_sum(
            "VL_SOM_PRAZO_VENC vs portfolio",
            block.vl_som_prazo_venc,
            [
                ce.vl_cred_existe_venc_adimpl,
                ce.vl_cred_existe_venc_inad,
                ce.vl_cred_refer_dicred_perfo,
            ],
            [ce.vl_cred_total_venc_inad],
        )
        _require_sum(
            "VL_SOM_INAD_VENC vs portfolio",
            block.vl_som_inad_venc,
            [ce.vl_cred_total_venc_inad, ce.vl_cred_existe_inad, ce.vl_cred_venc_pend],
            [],
        )
        return self


class InfMensalFidc489Document(_FidcBlock):
    """DOC_ARQ — a complete Informe Mensal FIDC (ICVM 489) file."""

    cab_inform: InfMensalFidc489Header
    lista_inform: InfMensalFidc489Inform

    @model_validator(mode="after")
    def _open_fund_reports_liquidity(self) -> InfMensalFidc489Document:
        """Require LIQUIDEZ content for open funds (optional for closed ones).

        Returns
        -------
        InfMensalFidc489Document
                The validated document.

        Raises
        ------
        ValueError
                If the fund is open and no LIQUIDEZ field is filled.
        """
        liquidez = self.lista_inform.outras_inform.liquidez
        filled = liquidez is not None and any(
            getattr(liquidez, f) is not None for f in type(liquidez).model_fields
        )
        if self.cab_inform.tp_condominio == "ABERTO" and not filled:
            raise ValueError("open funds must fill at least one LIQUIDEZ field")
        return self
