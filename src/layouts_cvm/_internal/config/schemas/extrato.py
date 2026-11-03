"""Pydantic models for the CVM Fund Statement (Extrato) XML standard — V3.

Direction-neutral schema for ``PadraoXMLInfExtratoV3.asp``
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfExtratoV3.asp). The
``submission`` section builds these models and serialises them to XML. This is the *envio*
artifact; the open-data CSV the ``ingestion`` readers consume is a different file with its own
``FileContract``.

**Field order is the XML order.** The writer walks ``model_fields`` in declaration order and
names each element ``<FIELD_NAME.upper()>``, so every field is the lower-cased tag from the
page's sample file and sits where the sample puts it. A nested model is a block.

The page contradicts itself (its sample file and its tag list describe two generations of the
form). The sample file is followed for structure; the tag list supplies optionality and the
code tables. Every such choice, and what the page leaves unsaid (decimal scales, text bounds),
is stated on ``docs/submission/extrato.md``.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, ClassVar, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

from layouts_cvm._internal.config.schemas._fields import validated_cnpj
from layouts_cvm._internal.utils.typing import type_checker
from layouts_cvm._internal.utils.xml_fields import (
    check_br_date,
    check_cnpj_shape,
    check_xml_text,
    strict_decimal,
)


_DIGITS = 18
_PERCENT_MAX = Decimal(100)


Percent2 = Annotated[
    Decimal,
    BeforeValidator(strict_decimal(2)),
    Field(ge=Decimal(0), le=_PERCENT_MAX, max_digits=_DIGITS, decimal_places=2),
]
Percent4 = Annotated[
    Decimal,
    BeforeValidator(strict_decimal(4)),
    Field(ge=Decimal(0), le=_PERCENT_MAX, max_digits=_DIGITS, decimal_places=4),
]
Percent6 = Annotated[
    Decimal,
    BeforeValidator(strict_decimal(6)),
    Field(ge=Decimal(0), le=_PERCENT_MAX, max_digits=_DIGITS, decimal_places=6),
]
Money2 = Annotated[
    Decimal,
    BeforeValidator(strict_decimal(2)),
    Field(ge=Decimal(0), max_digits=_DIGITS, decimal_places=2),
]
Ratio4 = Annotated[
    Decimal,
    BeforeValidator(strict_decimal(4)),
    Field(ge=Decimal(0), max_digits=_DIGITS, decimal_places=4),
]

_DAYS_MAX = 9999
DaysField = Annotated[int, Field(strict=True, ge=0, le=_DAYS_MAX)]

DateField = Annotated[str, AfterValidator(check_br_date)]
CnpjField = Annotated[str, AfterValidator(check_cnpj_shape), AfterValidator(validated_cnpj)]

_XML_TEXT = AfterValidator(check_xml_text)
MarketCode = Annotated[int, Field(strict=True, ge=1, le=4)]
AnbimaCode = Annotated[int, Field(strict=True, ge=1, le=68)]
DistributionCode = Annotated[int, Field(strict=True, ge=1, le=3)]
PolicyCode = Annotated[int, Field(strict=True, ge=1, le=4)]
_INDEX_CODES = frozenset({*range(1, 36), 99})
Yn = Literal["S", "N"]

Text200 = Annotated[str, StringConstraints(min_length=1, max_length=200), _XML_TEXT]
InfoText = Annotated[str, StringConstraints(min_length=5, max_length=400), _XML_TEXT]

_QUALIFIED = frozenset({"INVESTIDORES QUALIFICADOS", "INVESTIDORES PROFISSIONAIS"})
_MAX_ROWS = 1000
_FEE_REQUIRED = ("taxa_performance", "tp_taxa_performance", "per_indice_referencia")

_REQUIRED_MSG = "{name} is required when {flag} is {trigger}"
_FORBIDDEN_MSG = "{name} must be omitted unless {flag} is {trigger}"
_GATE_ERRORS = {
    (True, False, True): _REQUIRED_MSG,
    (True, False, False): _REQUIRED_MSG,
    (False, True, True): _FORBIDDEN_MSG,
}


@type_checker
def _check_dependent(
    block: BaseModel, name: str, flag: str, trigger: str, triggered: bool, forbid: bool
) -> None:
    """Raise if one gated dependent is missing when required or present when forbidden.

    Parameters
    ----------
    block : BaseModel
        The block under validation.
    name : str
        The dependent field name.
    flag : str
        The gating field name.
    trigger : str
        The flag value that makes the dependent required.
    triggered : bool
        Whether the flag equals the trigger.
    forbid : bool
        Whether the dependent must be absent when not triggered.

    Raises
    ------
    ValueError
        If the dependent's presence contradicts the gate.
    """
    present = getattr(block, name) is not None
    str_template = _GATE_ERRORS.get((triggered, present, forbid))
    if str_template:
        raise ValueError(
            str_template.format(name=name.upper(), flag=flag.upper(), trigger=trigger)
        )


@type_checker
def _check_gate(
    block: BaseModel, flag: str, trigger: str, dependents: tuple[str, ...], forbid: bool
) -> None:
    """Check every dependent of one gate.

    Parameters
    ----------
    block : BaseModel
        The block under validation.
    flag : str
        The gating field name.
    trigger : str
        The flag value that makes the dependents required.
    dependents : tuple[str, ...]
        The gated field names.
    forbid : bool
        Whether the dependents must be absent when not triggered.
    """
    triggered = getattr(block, flag) == trigger
    for name in dependents:
        _check_dependent(block, name, flag, trigger, triggered, forbid)


@type_checker
def _check_percentage(amount: Decimal) -> None:
    """Reject a percentage fee above 100.

    Parameters
    ----------
    amount : Decimal
        The fee value.

    Raises
    ------
    ValueError
        If the amount exceeds 100.
    """
    if amount > _PERCENT_MAX:
        raise ValueError("a percentage fee must not exceed 100")


@type_checker
def _check_reais(amount: Decimal) -> None:
    """Reject an R$ fee with more than two decimal places.

    Parameters
    ----------
    amount : Decimal
        The fee value.

    Raises
    ------
    ValueError
        If the amount has more than two decimal places.
    """
    if amount != amount.quantize(Decimal("0.01")):
        raise ValueError("an R$ fee takes at most two decimal places")


@type_checker
def _accept_amount(amount: Decimal) -> None:
    """Accept any amount (no rule for an undeclared kind).

    Parameters
    ----------
    amount : Decimal
        The fee value.
    """


_AMOUNT_CHECKS = {"1": _check_percentage, "2": _check_reais}


@type_checker
def _is_min_field(name: str) -> bool:
    """Tell whether a field name is a ``*_min`` bound.

    Parameters
    ----------
    name : str
        The field name.

    Returns
    -------
    bool
        True for a minimum bound.
    """
    return name.endswith("_min")


@type_checker
def _check_pair(block: BaseModel, name: str) -> None:
    """Require one minimum not to exceed its maximum.

    Parameters
    ----------
    block : BaseModel
        The block under validation.
    name : str
        The ``*_min`` field name.

    Raises
    ------
    ValueError
        If the minimum is above its maximum.
    """
    name_max = name[:-4] + "_max"
    if getattr(block, name) > getattr(block, name_max):
        raise ValueError(f"{name.upper()} must not exceed {name_max.upper()}")


@type_checker
def _is_unset(calc: BaseModel, name: str) -> bool:
    """Tell whether a field of the fee block is ``None``.

    Parameters
    ----------
    calc : BaseModel
        The fee block.
    name : str
        The field name.

    Returns
    -------
    bool
        True when unset.
    """
    return getattr(calc, name) is None


@type_checker
def _check_fee_fields_present(calc: BaseModel) -> None:
    """Require the mandatory fee fields.

    Parameters
    ----------
    calc : BaseModel
        The fee block.

    Raises
    ------
    ValueError
        If any mandatory field is missing.
    """
    list_missing = [n.upper() for n in _FEE_REQUIRED if _is_unset(calc, n)]
    if list_missing:
        raise ValueError(f"{', '.join(list_missing)} required for non-qualified investors")


@type_checker
def _check_fee_info_empty(calc: BaseModel) -> None:
    """Require ``INFO_ADICIONAL`` to be empty.

    Parameters
    ----------
    calc : BaseModel
        The fee block.

    Raises
    ------
    ValueError
        If ``INFO_ADICIONAL`` is set.
    """
    if not _is_unset(calc, "info_adicional"):
        raise ValueError("INFO_ADICIONAL must be empty for non-qualified investors")


class ExtratoBlock(BaseModel):
    """Base of every Extrato block: closed (no unknown fields) and immutable.

    A subclass may declare ``_GATES``: ``(flag, trigger, dependents, forbid)`` tuples. The
    dependents are required when ``flag == trigger``, and — with ``forbid`` — must be absent
    otherwise (the page says "preencher somente se ...").
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    _GATES: ClassVar[tuple[tuple[str, str, tuple[str, ...], bool], ...]] = ()

    @model_validator(mode="after")
    def _check_gates(self) -> ExtratoBlock:
        """Enforce the conditional-field rules the page states per answer.

        Returns
        -------
        ExtratoBlock
                The validated block.

        Raises
        ------
        ValueError
                If a dependent field is missing when required, or present when forbidden.
        """
        for tuple_gate in self._GATES:
            _check_gate(self, *tuple_gate)
        return self


class ExtratoHeader(ExtratoBlock):
    """CAB_INFORM — document header."""

    cod_doc: Literal[41] = 41
    versao: Literal["3.0"] = "3.0"
    dt_gerac_arq: DateField


class FormaCondominio(ExtratoBlock):
    """FORMA_CONDOMINIO — open/closed condominium and organised-market trading."""

    _GATES: ClassVar[tuple[tuple[str, str, tuple[str, ...], bool], ...]] = (
        ("tipo_condominio", "FECHADO", ("aberta_neg_mer_organ",), False),
        ("aberta_neg_mer_organ", "S", ("lista_merc_bloqueio",), True),
    )

    tipo_condominio: Literal["FECHADO", "ABERTO"]
    aberta_neg_mer_organ: Yn | None = None
    lista_merc_bloqueio: MarketCode | None = None


class Prazo(ExtratoBlock):
    """PRAZO — fund term."""

    _GATES: ClassVar[tuple[tuple[str, str, tuple[str, ...], bool], ...]] = (
        ("tipo_prazo", "DETERMINADO", ("detalhamento_prazo",), False),
    )

    tipo_prazo: Literal["DETERMINADO", "INDETERMINADO"]
    detalhamento_prazo: Text200 | None = None


class FundoAnbima(ExtratoBlock):
    """FUNDO_ANBIMA — ANBIMA registration and classification."""

    _GATES: ClassVar[tuple[tuple[str, str, tuple[str, ...], bool], ...]] = (
        ("anbima", "S", ("cod_classificacao",), True),
    )

    anbima: Yn
    cod_classificacao: AnbimaCode | None = None


class FundoInvertCotas(ExtratoBlock):
    """FUNDO_INVERT_COTAS — fund of funds."""

    _GATES: ClassVar[tuple[tuple[str, str, tuple[str, ...], bool], ...]] = (
        ("tipo_fundo_invert", "S", ("tipo_fundo",), True),
    )

    tipo_fundo_invert: Yn
    tipo_fundo: Literal["FUNDO DE FUNDOS", "FUNDO-ESPELHO"] | None = None


class ValorCota(ExtratoBlock):
    """VALOR_COTA — quota value update frequency."""

    _GATES: ClassVar[tuple[tuple[str, str, tuple[str, ...], bool], ...]] = (
        ("atualizado_diariamente", "N", ("prazo_atualizacao",), True),
    )

    atualizado_diariamente: Yn
    prazo_atualizacao: Text200 | None = None


class ResgCotas(ExtratoBlock):
    """RESG_COTAS — redemption grace period."""

    _GATES: ClassVar[tuple[tuple[str, str, tuple[str, ...], bool], ...]] = (
        ("carencia_resg_cotas", "S", ("dias_resg_cotas",), True),
    )

    carencia_resg_cotas: Yn
    dias_resg_cotas: DaysField | None = None


class PrazoPagamResg(ExtratoBlock):
    """PRAZO_PAGAM_RESG — redemption payment term."""

    dias_sem_taxa: DaysField
    dias_com_taxa: DaysField
    tipo_de_contagem: Literal["UTEIS", "CORRIDOS"]


class CalcTxPerfm(ExtratoBlock):
    """CALC_TX_PERFM — performance-fee calculation (rules by investor in ``ExtratoRow``)."""

    taxa_performance: Percent4 | None = None
    tp_taxa_performance: Annotated[int, Field(strict=True)] | None = None
    per_indice_referencia: Ratio4 | None = None
    cupom: Ratio4 | None = None
    metodo_calc_taxa: Literal["ATIVO", "PASSIVO", "AJUSTE"] | None = None
    info_adicional: InfoText | None = None

    @model_validator(mode="after")
    def _check_index_code(self) -> CalcTxPerfm:
        """Require the index code to be one of the page's table D codes.

        Returns
        -------
        CalcTxPerfm
                The validated block.

        Raises
        ------
        ValueError
                If ``TP_TAXA_PERFORMANCE`` is not 1-35 or 99.
        """
        if self.tp_taxa_performance is not None and self.tp_taxa_performance not in _INDEX_CODES:
            raise ValueError("TP_TAXA_PERFORMANCE must be a table D code (1-35 or 99)")
        return self


class TxPerfm(ExtratoBlock):
    """TX_PERFM — performance fee."""

    _GATES: ClassVar[tuple[tuple[str, str, tuple[str, ...], bool], ...]] = (
        ("cobra_tx_perfm", "S", ("calc_tx_perfm",), True),
    )

    cobra_tx_perfm: Yn
    calc_tx_perfm: CalcTxPerfm | None = None


class _FixedFee(ExtratoBlock):
    """Shared rules of the entry and exit fee blocks: percentage (4 places) or R$ (2 places)."""

    @staticmethod
    def _check_amount(kind: str | None, amount: Decimal | None) -> None:
        """Bound a fee by its kind: a percentage stays within 100, an R$ amount takes 2 places.

        Parameters
        ----------
        kind : str | None
                ``"1"`` (percentage) or ``"2"`` (R$).
        amount : Decimal | None
                The fee value, already truncated to four places.

        Raises
        ------
        ValueError
                If a percentage fee exceeds 100, or an R$ fee has more than two decimal places.
        """
        if amount is None:
            return
        _AMOUNT_CHECKS.get(kind or "", _accept_amount)(amount)


class TxIngresso(_FixedFee):
    """TX_INGRESSO — entry fee."""

    _GATES: ClassVar[tuple[tuple[str, str, tuple[str, ...], bool], ...]] = (
        ("cobra_tx_ingresso", "S", ("tp_vl_fixo_tx_ingresso", "vl_fixo_tx_ingresso"), True),
    )

    cobra_tx_ingresso: Yn
    tp_vl_fixo_tx_ingresso: Literal["1", "2"] | None = None
    vl_fixo_tx_ingresso: Ratio4 | None = None

    @model_validator(mode="after")
    def _check_value(self) -> TxIngresso:
        """Check the amount against the declared kind.

        Returns
        -------
        TxIngresso
                The validated block.
        """
        self._check_amount(self.tp_vl_fixo_tx_ingresso, self.vl_fixo_tx_ingresso)
        return self


class TxSaida(_FixedFee):
    """TX_SAIDA — exit fee.

    The page's sample reuses the tag ``TP_VL_FIXO_TX_INGRESSO`` for the exit-fee kind; it is
    emitted as written.
    """

    _GATES: ClassVar[tuple[tuple[str, str, tuple[str, ...], bool], ...]] = (
        ("cobra_tx_saida", "S", ("tp_vl_fixo_tx_ingresso", "vl_fixo_tx_saida"), True),
    )

    cobra_tx_saida: Yn
    tp_vl_fixo_tx_ingresso: Literal["1", "2"] | None = None
    vl_fixo_tx_saida: Ratio4 | None = None

    @model_validator(mode="after")
    def _check_value(self) -> TxSaida:
        """Check the amount against the declared kind.

        Returns
        -------
        TxSaida
                The validated block.
        """
        self._check_amount(self.tp_vl_fixo_tx_ingresso, self.vl_fixo_tx_saida)
        return self


class OperDeriv(ExtratoBlock):
    """OPER_DERIV — derivatives operations."""

    _GATES: ClassVar[tuple[tuple[str, str, tuple[str, ...], bool], ...]] = (
        ("realiz_oper_deriv", "S", ("operacoes_derivativos",), True),
    )

    realiz_oper_deriv: Yn
    operacoes_derivativos: Literal["HEDGE", "ESPECULAÇÃO", "ARBITRAGEM"] | None = None


class OperPatrimLiq(ExtratoBlock):
    """OPER_PATRIM_LIQ — operations above the net worth."""

    _GATES: ClassVar[tuple[tuple[str, str, tuple[str, ...], bool], ...]] = (
        ("realiza_oper_patrim_liq", "S", ("qt_oper_patrim_liq",), True),
    )

    realiza_oper_patrim_liq: Yn
    qt_oper_patrim_liq: Ratio4 | Literal["SL"] | None = None


class AtivExter(ExtratoBlock):
    """ATIV_EXTER — foreign assets."""

    _GATES: ClassVar[tuple[tuple[str, str, tuple[str, ...], bool], ...]] = (
        ("invest_exterior", "S", ("pr_max_aplic_ativ_exter",), True),
    )

    invest_exterior: Yn
    pr_max_aplic_ativ_exter: Percent4 | None = None


class FundoAtivos(ExtratoBlock):
    """FUNDO_ATIVOS — private-credit assets."""

    _GATES: ClassVar[tuple[tuple[str, str, tuple[str, ...], bool], ...]] = (
        ("adquira_credito_privado", "S", ("limite_maximo",), True),
    )

    adquira_credito_privado: Yn
    limite_maximo: Percent2 | None = None


class _MinMaxBlock(ExtratoBlock):
    """A block of ``X_MIN``/``X_MAX`` pairs: each minimum may not exceed its maximum."""

    @model_validator(mode="after")
    def _check_pairs(self) -> _MinMaxBlock:
        """Require min <= max for every pair.

        Returns
        -------
        _MinMaxBlock
                The validated block.

        Raises
        ------
        ValueError
                If a minimum is above its maximum.
        """
        for name in filter(_is_min_field, type(self).model_fields):
            _check_pair(self, name)
        return self


class RegulamentoTipoEmissor(_MinMaxBlock):
    """REGULAMENTO_TIPO_EMISSOR — min/max exposure per issuer type (question 28)."""

    instituicoes_financeiras_min: Percent2
    instituicoes_financeiras_max: Percent2
    companhias_abertas_min: Percent2
    companhias_abertas_max: Percent2
    fundos_investimento_min: Percent2
    fundos_investimento_max: Percent2
    uniao_federal_min: Percent2
    uniao_federal_max: Percent2
    administrador_gestor_pessoas_ligadas_min: Percent2
    administrador_gestor_pessoas_ligadas_max: Percent2
    outros_min: Percent2
    outros_max: Percent2


class RegulamentoModalidadeAtivo(_MinMaxBlock):
    """REGULAMENTO_MODALIDADE_ATIVO — min/max exposure per asset modality (question 29)."""

    cotas_fi_555_min: Percent2
    cotas_fi_555_max: Percent2
    cotas_fic_555_min: Percent2
    cotas_fic_555_max: Percent2
    cotas_fi_555_invest_qualificados_min: Percent2
    cotas_fi_555_invest_qualificados_max: Percent2
    cotas_fic_555_invest_qualificados_min: Percent2
    cotas_fic_555_invest_qualificados_max: Percent2
    cotas_fi_555_invest_profissionais_min: Percent2
    cotas_fi_555_invest_profissionais_max: Percent2
    cotas_fic_555_invest_profissionais_min: Percent2
    cotas_fic_555_invest_profissionais_max: Percent2
    cotas_fii_min: Percent2
    cotas_fii_max: Percent2
    cotas_fidc_min: Percent2
    cotas_fidc_max: Percent2
    cotas_ficfidc_min: Percent2
    cotas_ficfidc_max: Percent2
    cotas_fidc_np_min: Percent2
    cotas_fidc_np_max: Percent2
    cotas_ficfidc_np_min: Percent2
    cotas_ficfidc_np_max: Percent2
    cotas_fundos_indice_mercado_etf_min: Percent2
    cotas_fundos_indice_mercado_etf_max: Percent2
    cri_min: Percent2
    cri_max: Percent2
    titulos_publicos_operacoes_min: Percent2
    titulos_publicos_operacoes_max: Percent2
    ouro_min: Percent2
    ouro_max: Percent2
    titulos_emissao_coobrigacao_min: Percent2
    titulos_emissao_coobrigacao_max: Percent2
    valores_mobiliarios_alinea_min: Percent2
    valores_mobiliarios_alinea_max: Percent2
    deposito_acoes_min: Percent2
    deposito_acoes_max: Percent2
    debentures_min: Percent2
    debentures_max: Percent2
    notas_promissorias_min: Percent2
    notas_promissorias_max: Percent2
    operacoes_compromissadas_min: Percent2
    operacoes_compromissadas_max: Percent2
    derivativos_min: Percent2
    derivativos_max: Percent2
    outros_min: Percent2
    outros_max: Percent2
    cotas_fmiee_min: Percent2
    cotas_fmiee_max: Percent2
    cotas_fip_min: Percent2
    cotas_fip_max: Percent2
    cotas_ficfip_min: Percent2
    cotas_ficfip_max: Percent2


class ExtratoRow(ExtratoBlock):
    """ROW_EXTRATO — the extract of one fund quota class."""

    cnpj_fdo: CnpjField
    forma_condominio: FormaCondominio
    prazo: Prazo
    publico_alvo: (
        Literal[
            "PÚBLICO EM GERAL",
            "INVESTIDORES QUALIFICADOS",
            "INVESTIDORES PROFISSIONAIS",
            "PREVIDENCIÁRIO",
        ]
        | None
    ) = None
    fundo_anbima: FundoAnbima
    cod_distr_fdo: DistributionCode | None = None
    cod_polit_invest: PolicyCode
    max_app_cotas_fundo: Percent4
    resultado_atr_carteira: Yn
    fundo_invert_cotas: FundoInvertCotas
    aplicacao_minima_fundo: Money2 | None = None
    valor_cota: ValorCota
    tipo_valor_cota: Literal["DO DIA DA APLICACAO", "DO DIA SEGUINTE AO DA APLICACAO"] | None = (
        None
    )
    valor_cota_base_pl: (
        Literal[
            "DO PRÓPRIO DIA (COTA DE FECHAMENTO)",
            "DO DIA ANTERIOR",
            "ATUALIZADO POR 1 DIA (COTA DE ABERTURA)",
        ]
        | None
    ) = None
    qt_dia_conv_cota: DaysField | None = None
    qt_dia_pagam_cota: DaysField | None = None
    resg_cotas: ResgCotas
    prazo_pagam_resg: PrazoPagamResg | None = None
    taxa_adm: Percent4 | None = None
    taxa_maxima_custodia: Percent6 | None = None
    tx_perfm: TxPerfm
    tx_ingresso: TxIngresso
    tx_saida: TxSaida
    oper_deriv: OperDeriv
    oper_patrim_liq: OperPatrimLiq
    mercado_sem_contraparte_central: Yn
    ativ_exter: AtivExter
    fundo_ativos: FundoAtivos
    regulamento_tipo_emissor: RegulamentoTipoEmissor
    regulamento_modalidade_ativo: RegulamentoModalidadeAtivo

    @model_validator(mode="after")
    def _check_performance_fee(self) -> ExtratoRow:
        """Apply the performance-fee rule that depends on the target investor.

        For a fund not restricted to qualified or professional investors the fee, its index
        code and the index percentage are mandatory and ``INFO_ADICIONAL`` must stay empty;
        a fund for qualified investors may describe the fee as free text instead.

        Returns
        -------
        ExtratoRow
                The validated row.

        Raises
        ------
        ValueError
                If the fee fields do not follow the investor-dependent rule.
        """
        calc = self.tx_perfm.calc_tx_perfm
        if calc is None or self.publico_alvo in _QUALIFIED:
            return self
        _check_fee_fields_present(calc)
        _check_fee_info_empty(calc)
        return self


class ExtratoDocument(ExtratoBlock):
    """DOC_ARQ — a whole Extrato V3 file: one header and one row per fund quota class."""

    header: ExtratoHeader
    rows: Annotated[list[ExtratoRow], Field(min_length=1, max_length=_MAX_ROWS)]
