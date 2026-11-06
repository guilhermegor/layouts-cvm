"""Pydantic models for the CVM CDA XML — V4.

Direction-neutral schema mirroring the submission XML described at
https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLCDANetV4.aspx
(namespace ``urn:cda``, ``COD_DOC=3``, ``VERSAO=4.0``). Field names, scales and
cardinalities come from that page.

Scales stated by the page: ``VL_PL`` 21 integer + 2 decimal digits; ``VL_*_NEGOC`` and
``MERC_POS_FIM`` 15 + 2; ``QTDE_*`` 15 + 6; ``TIT_POS_FIX_PR_INDEX``, ``TIT_POS_FIX_CUPOM``
and ``TIT_PRE_FIX_TAXA_CONTR`` 3 + 6. Excess decimals are truncated (``ROUND_DOWN``).

Business rules enforced from the page: which application types (``COD_TP_APLIC``) each
repetition block accepts, the required/optional/forbidden matrix of Table A, the
application-type x asset-type relation of Table B, and the conditional blocks
(post-fixed index, risk classification).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import re
from typing import Annotated, ClassVar, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    Field,
    field_validator,
    model_validator,
)

from layouts_cvm._internal.config.schemas._fields import (
    truncate_to_scale,
    validate_person_doc,
    validated_br_date_shape,
    validated_cnpj,
    validated_competence,
)
from layouts_cvm._internal.utils.typing import type_checker


_SWAP_RE = re.compile(r"SWP[A-Z0-9]{3}")
_XML_ILLEGAL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_LINE_BREAK_RE = re.compile(r"[\t\n\r]")

_MAX_INT_15 = Decimal(10) ** 15
_MAX_INT_21 = Decimal(10) ** 21
_MAX_INT_3 = Decimal(10) ** 3


@type_checker
def _reject_float(value: object) -> object:
    """Refuse a binary ``float``: it would launder an already-lossy value into a ``Decimal``.

    Parameters
    ----------
    value : object
            Raw input.

    Returns
    -------
    object
            The same value.

    Raises
    ------
    ValueError
            If ``value`` is a ``float``.
    """
    if isinstance(value, float):
        raise ValueError("pass a str, int or Decimal, never a float")
    return value


@type_checker
def _require_nonblank(value: str) -> None:
    """Refuse empty or whitespace-only text.

    Parameters
    ----------
    value : str
        Candidate text.

    Raises
    ------
    ValueError
        If blank.
    """
    if not value.strip():
        raise ValueError("text must not be empty or blank")


@type_checker
def _require_single_line(value: str) -> None:
    """Refuse a tab or line break.

    Parameters
    ----------
    value : str
        Candidate text.

    Raises
    ------
    ValueError
        If a tab or line break is present.
    """
    if _LINE_BREAK_RE.search(value):
        raise ValueError("text must not hold a tab or line break")


@type_checker
def _require_windows_1252(value: str) -> None:
    """Refuse a character the file's declared encoding cannot carry.

    Parameters
    ----------
    value : str
        Candidate text.

    Raises
    ------
    ValueError
        If not encodable in windows-1252.
    """
    try:
        value.encode("windows-1252")
    except UnicodeEncodeError as exc:
        raise ValueError(
            f"character {value[exc.start]!r} is not encodable in windows-1252"
        ) from exc


@type_checker
def _require_xml_legal(value: str) -> None:
    """Refuse a control character XML 1.0 forbids.

    Parameters
    ----------
    value : str
        Candidate text.

    Raises
    ------
    ValueError
        If a forbidden control character is present.
    """
    if _XML_ILLEGAL_RE.search(value):
        raise ValueError("text holds a control character XML forbids")


@type_checker
def _check_text(value: str) -> str:
    """Require text the file can carry: non-blank, single-line, windows-1252, legal XML characters.

    Parameters
    ----------
    value : str
            Candidate text.

    Returns
    -------
    str
            The same value.

    Raises
    ------
    ValueError
            If empty, not encodable in windows-1252 (the file's declared encoding), or holding a
            character XML 1.0 forbids.
    """
    _require_nonblank(value)
    _require_single_line(value)
    _require_windows_1252(value)
    _require_xml_legal(value)
    return value


Text = Annotated[str, AfterValidator(_check_text)]
Money = Annotated[
    Decimal,
    BeforeValidator(truncate_to_scale(2)),
    BeforeValidator(_reject_float),
    Field(ge=0, lt=_MAX_INT_15),
]
SignedMoney = Annotated[
    Decimal,
    BeforeValidator(truncate_to_scale(2)),
    BeforeValidator(_reject_float),
    Field(gt=-_MAX_INT_15, lt=_MAX_INT_15),
]
Quantity = Annotated[
    Decimal,
    BeforeValidator(truncate_to_scale(6)),
    BeforeValidator(_reject_float),
    Field(gt=-_MAX_INT_15, lt=_MAX_INT_15),
]
TradedQuantity = Annotated[
    Decimal,
    BeforeValidator(truncate_to_scale(6)),
    BeforeValidator(_reject_float),
    Field(ge=0, lt=_MAX_INT_15),
]
PatrimonyValue = Annotated[
    Decimal,
    BeforeValidator(truncate_to_scale(2)),
    BeforeValidator(_reject_float),
    Field(gt=-_MAX_INT_21, lt=_MAX_INT_21),
]
Rate = Annotated[
    Decimal,
    BeforeValidator(truncate_to_scale(6)),
    BeforeValidator(_reject_float),
    Field(ge=0, lt=_MAX_INT_3),
]
ForeignValue = Annotated[Decimal, BeforeValidator(_reject_float), Field(allow_inf_nan=False)]

INDEXERS = frozenset(
    {
        "ANB",
        "CDS",
        "DI1",
        "DOL",
        "I50",
        "IAP",
        "IBX",
        "IEE",
        "IGD",
        "IGM",
        "IGP",
        "IMA",
        "IMA-B",
        "IMA-B5",
        "IMA-B5+",
        "IMA-C",
        "IMA-C5",
        "IMA-C5+",
        "IMA-S",
        "IND",
        "INP",
        "IPC",
        "IRF",
        "ITE",
        "JPY",
        "OUT",
        "OZ1",
        "PIB",
        "PRE",
        "REU",
        "SB1",
        "SB2",
        "SEL",
        "TBF",
        "TJL",
        "TR",
    }
)

_TABLE_A: dict[int, tuple[str, str, str, str]] = {
    37: ("S", "S", "S", "S"),
    39: ("S", "OP", "OP", "S"),
    40: ("S", "OP", "OP", "S"),
    42: ("S", "N", "OP", "S"),
    43: ("S", "OP", "N", "S"),
    48: ("S", "OP", "OP", "S"),
    74: ("S", "OP", "OP", "S"),
    75: ("NA", "S", "S", "S"),
    94: ("NA", "N", "N", "N"),
    96: ("NA", "N", "N", "N"),
    97: ("NA", "N", "N", "N"),
    102: ("NA", "OP", "OP", "S"),
    103: ("NA", "OP", "OP", "S"),
    143: ("S", "N", "N", "S"),
    146: ("S", "N", "N", "S"),
    147: ("S", "N", "N", "S"),
    151: ("S", "OP", "OP", "S"),
    152: ("S", "OP", "OP", "S"),
    183: ("NA", "N", "N", "N"),
    184: ("NA", "N", "N", "N"),
    187: ("NA", "OP", "OP", "S"),
    189: ("S", "OP", "OP", "S"),
    191: ("NA", "N", "N", "N"),
    192: ("NA", "N", "N", "N"),
    193: ("S", "OP", "OP", "S"),
    195: ("S", "OP", "OP", "S"),
    196: ("S", "OP", "OP", "S"),
    197: ("S", "OP", "OP", "S"),
    198: ("S", "OP", "OP", "S"),
    199: ("S", "OP", "OP", "S"),
    200: ("NA", "N", "N", "N"),
}

_FUTURES = frozenset({9, 46, *range(52, 75)})
_LOAN = frozenset({1, 2, 6, 7, 11, 12, 13, 14, 21, 23, 24, 28, 29, 30, 40, 43, 44, 45, 47})
_LOAN |= frozenset({48, 49, 81})
_TABLE_B: dict[int, frozenset[int]] = {
    37: frozenset({1, 2, 13}),
    39: frozenset({3, 4, 91, 92}),
    40: frozenset({3, 4, 91, 92}),
    42: frozenset({1, 2, 13, 999}),
    43: frozenset({1, 2, 11, 13, 999}),
    48: frozenset({21, 23, 25, 46, 999}),
    74: frozenset({50, 51, 76, 77, 78, 84, 85, 86, 92, 999}),
    75: frozenset({28, 29, 30, 87}),
    94: frozenset({999}),
    96: frozenset({89, 999}),
    97: frozenset({999}),
    102: _FUTURES,
    103: _FUTURES,
    143: _LOAN,
    146: _LOAN | {88},
    147: frozenset({6, 7, 18, 28, 29, 30, 50, 51, 84, 85, 86, 90, 999}),
    151: frozenset({11, 12}),
    152: frozenset({14, 15, 17, 18, 19, 21, 23, 24, 90}),
    183: frozenset({26}),
    184: frozenset({26}),
    187: frozenset({999}),
    189: frozenset(
        {1, 2, 3, 4, 6, 7, 9, 11, 12, 13, 14, 15, 17, 18, 19, 20, 21, 23, 26, 27}
        | {46, 82, 83, 90, 91, 92, 999}
    ),
    191: frozenset({1, 2, 13, 999}),
    192: frozenset({1, 2, 13, 999}),
    193: frozenset({6, 7, 79, 80}),
    195: frozenset({31, 32, 33, 34, 35, 36, 37}),
    196: frozenset({15, 38, 39, 75}),
    197: frozenset({40, 41, 42, 43, 44, 45}),
    198: frozenset({47, 48, 49, 81, 88}),
    199: frozenset({11, 12, 13, 14, 15, 17, 18, 19, 21, 23, 24, 90}),
    200: frozenset({3, 4, 91, 92, 999}),
}

_CODIF_UNCODED = frozenset({37, 39, 40, 42, 43, 102, 103, 143, 146, 151, 152, 198})
BLOCK_APLIC_TYPES: dict[str, frozenset[int]] = {
    "TIT_PUB": frozenset({75, 147}),
    "COTAS": frozenset({197}),
    "SWAP": frozenset({183, 184}),
    "DEMAIS_CODIF": _CODIF_UNCODED | {193},
    "DEP_PRAZO_TIT_IF": frozenset({74}),
    "TIT_AGRO_CRED_PRIV": frozenset({193, 195, 196}),
    "INV_EXT": frozenset({189}),
    "DEMAIS_N_CODIF": frozenset({48, 75, 94, 96, 97, 147, 187, 191, 192, 199, 200})
    | _CODIF_UNCODED,
}


@type_checker
def _require_br_format(value: str) -> None:
    """Refuse text that does not follow DD/MM/AAAA.

    Parameters
    ----------
    value : str
        Candidate date.

    Raises
    ------
    ValueError
        If the format is wrong.
    """
    validated_br_date_shape(value)


@type_checker
def _require_real_date(value: str) -> None:
    """Refuse a well-formed date that is not on the calendar.

    Parameters
    ----------
    value : str
        Candidate date.

    Raises
    ------
    ValueError
        If the date does not exist.
    """
    try:
        datetime.strptime(value, "%d/%m/%Y")  # noqa: DTZ007  (calendar check only)
    except ValueError as exc:
        raise ValueError(f"{value} is not a real calendar date.") from exc


@type_checker
def _check_br_date(value: str) -> str:
    """Require a real calendar date in the DD/MM/AAAA format.

    Parameters
    ----------
    value : str
            Candidate date.

    Returns
    -------
    str
            The same value.

    Raises
    ------
    ValueError
            If the format is wrong or the date does not exist.
    """
    _require_br_format(value)
    _require_real_date(value)
    return value


BrDate = Annotated[str, AfterValidator(_check_br_date)]


class CdaHeader(BaseModel):
    """CAB_INFORM — document header (COD_DOC fixed at 3, VERSAO at 4.0)."""

    cod_doc: Literal[3] = 3
    versao: Literal["4.0"] = "4.0"
    dt_compt: str
    dt_gerac_arq: BrDate

    @field_validator("dt_compt")
    @classmethod
    def _check_compt(cls, v: str) -> str:
        """Require MM/AAAA.

        Parameters
        ----------
        v : str
                Competence.

        Returns
        -------
        str
                Validated value.

        Raises
        ------
        ValueError
                If the format is not MM/AAAA.
        """
        return validated_competence(v)


@type_checker
def _require_not_empty(model: BaseModel) -> None:
    """Refuse a block with every field unset.

    Parameters
    ----------
    model : BaseModel
        The NEGOC model.

    Raises
    ------
    ValueError
        If no field is set.
    """
    if all(getattr(model, name) is None for name in type(model).model_fields):
        raise ValueError("negoc must carry at least one field; omit the block instead")


@type_checker
def _require_together(model: BaseModel, name_a: str, name_b: str) -> None:
    """Require two fields to be both set or both unset.

    Parameters
    ----------
    model : BaseModel
        The model holding the pair.
    name_a : str
        First field name.
    name_b : str
        Second field name.

    Raises
    ------
    ValueError
        If only one of the pair is set.
    """
    if (getattr(model, name_a) is None) != (getattr(model, name_b) is None):
        raise ValueError(f"{name_a} and {name_b} must be filled together")


class CdaNegoc(BaseModel):
    """NEGOC — month's trades. Quantity and value of a side must come together."""

    tp_negoc: Literal[1, 2] | None = None
    qtde_vendas_negoc: TradedQuantity | None = None
    vl_vendas_negoc: Money | None = None
    qtde_aquis_negoc: TradedQuantity | None = None
    vl_aquis_negoc: Money | None = None

    @model_validator(mode="after")
    def _pairs(self) -> CdaNegoc:
        """Require quantity and value to be filled together for sales and acquisitions.

        Returns
        -------
        CdaNegoc
                The model.

        Raises
        ------
        ValueError
                If only one of the pair is filled, or the block is empty.
        """
        _require_not_empty(self)
        _require_together(self, "qtde_vendas_negoc", "vl_vendas_negoc")
        _require_together(self, "qtde_aquis_negoc", "vl_aquis_negoc")
        return self


class CdaPosFim(BaseModel):
    """POS_FIM — final position."""

    qtde_pos_fim: Quantity | None = None
    merc_pos_fim: SignedMoney


class CdaAtivoExt(BaseModel):
    """ATIVO_EXT — foreign asset detail (INV_EXT only)."""

    desc_at_ext: Annotated[Text, Field(max_length=50)]
    qtde_at_ext: int
    valor_at_ext: ForeignValue


@type_checker
def _empr_required(code: int, value: object) -> None:
    """Require ``empr_ligada`` (Table A flag ``S``).

    Parameters
    ----------
    code : int
        Application type, for the message.
    value : object
        The ``empr_ligada`` value.

    Raises
    ------
    ValueError
        If omitted.
    """
    if value is None:
        raise ValueError(f"empr_ligada is required for COD_TP_APLIC {code}")


@type_checker
def _empr_forbidden(code: int, value: object) -> None:
    """Forbid ``empr_ligada`` (Table A flag ``NA``).

    Parameters
    ----------
    code : int
        Application type, for the message.
    value : object
        The ``empr_ligada`` value.

    Raises
    ------
    ValueError
        If filled.
    """
    if value is not None:
        raise ValueError(f"empr_ligada is not applicable for COD_TP_APLIC {code}")


@type_checker
def _empr_optional(code: int, value: object) -> None:
    """Accept any ``empr_ligada`` (flags ``N`` and ``OP``).

    Parameters
    ----------
    code : int
        Unused.
    value : object
        Unused.
    """


@type_checker
def _flag_required(code: int, what: str, filled: bool) -> None:
    """Require a column (Table A flag ``S``).

    Parameters
    ----------
    code : int
        Application type, for the message.
    what : str
        Column name, for the message.
    filled : bool
        Whether the quantity is present.

    Raises
    ------
    ValueError
        If omitted.
    """
    if not filled:
        raise ValueError(f"{what} is required for COD_TP_APLIC {code}")


@type_checker
def _flag_forbidden(code: int, what: str, filled: bool) -> None:
    """Forbid a column (Table A flag ``N``).

    Parameters
    ----------
    code : int
        Application type, for the message.
    what : str
        Column name, for the message.
    filled : bool
        Whether the quantity is present.

    Raises
    ------
    ValueError
        If filled.
    """
    if filled:
        raise ValueError(f"{what} must not be filled for COD_TP_APLIC {code}")


@type_checker
def _flag_optional(code: int, what: str, filled: bool) -> None:
    """Accept any quantity (flag ``OP``).

    Parameters
    ----------
    code : int
        Unused.
    what : str
        Unused.
    filled : bool
        Unused.
    """


_EMPR_CHECKS = {
    "S": _empr_required,
    "NA": _empr_forbidden,
    "N": _empr_optional,
    "OP": _empr_optional,
}
_FLAG_CHECKS = {
    "S": _flag_required,
    "N": _flag_forbidden,
    "OP": _flag_optional,
    "NA": _flag_optional,
}


class CdaAplic(BaseModel):
    """APLIC — application: negotiation and final position, per Table A.

    ``cod_tp_aplic`` is omitted from the XML for the COTAS, DEP_PRAZO_TIT_IF and INV_EXT
    blocks (the page has no such tag there); the block then implies 197, 74 and 189.
    """

    cod_tp_aplic: int | None = None
    empr_ligada: Literal["S", "N"] | None = None
    qtde_dias_confid: int | None = Field(default=None, ge=0, le=90)
    negoc: CdaNegoc | None = None
    pos_fim: CdaPosFim
    ativo_ext: CdaAtivoExt | None = None

    def check_table_a(self, code: int) -> None:
        """Apply the Table A required/optional/forbidden matrix for ``code``.

        Parameters
        ----------
        code : int
                Effective application type.

        Raises
        ------
        ValueError
                If a field is filled/omitted against the matrix.
        """
        empr, vendas, aquis, qtd = _TABLE_A[code]
        _EMPR_CHECKS[empr](code, self.empr_ligada)
        neg = self.negoc
        self._rule(code, "vendas", vendas, neg.qtde_vendas_negoc if neg else None)
        self._rule(code, "aquisicoes", aquis, neg.qtde_aquis_negoc if neg else None)
        self._rule(code, "posicao final", qtd, self.pos_fim.qtde_pos_fim)

    @staticmethod
    def _rule(code: int, what: str, flag: str, qty: Decimal | None) -> None:
        """Check one Table A column.

        Parameters
        ----------
        code : int
                Application type, for the message.
        what : str
                Column name, for the message.
        flag : str
                ``S``, ``OP`` or ``N``.
        qty : Optional[Decimal]
                Quantity (``None`` when omitted).

        Raises
        ------
        ValueError
                On a violation.
        """
        _FLAG_CHECKS[flag](code, what, qty is not None)


@type_checker
def _code_implicit(block: str, aplic: CdaAplic, implicit: int) -> int:
    """Take the block's implied type, refusing an explicit tag.

    Parameters
    ----------
    block : str
        Block tag.
    aplic : CdaAplic
        The application.
    implicit : int
        Application type implied by the block.

    Returns
    -------
    int
        The result.

    Raises
    ------
    ValueError
        If the application carries a ``cod_tp_aplic`` the block forbids.
    """
    if aplic.cod_tp_aplic is not None:
        raise ValueError(f"{block} has no COD_TP_APLIC tag")
    return implicit


@type_checker
def _code_explicit(block: str, aplic: CdaAplic, implicit: int | None) -> int:
    """Take the application's own type, requiring it.

    Parameters
    ----------
    block : str
        Block tag.
    aplic : CdaAplic
        The application.
    implicit : Optional[int]
        Application type implied by the block.

    Returns
    -------
    int
        The result.

    Raises
    ------
    ValueError
        If ``cod_tp_aplic`` is omitted.
    """
    if aplic.cod_tp_aplic is None:
        raise ValueError(f"cod_tp_aplic is required in {block}")
    return aplic.cod_tp_aplic


@type_checker
def _resolve_code(block: str, aplic: CdaAplic, implicit: int | None) -> int:
    """Resolve the effective application type of an APLIC.

    Parameters
    ----------
    block : str
        Block tag.
    aplic : CdaAplic
        The application.
    implicit : Optional[int]
        Application type implied by the block.

    Returns
    -------
    int
        The result.
    """
    if implicit is not None:
        return _code_implicit(block, aplic, implicit)
    return _code_explicit(block, aplic, implicit)


@type_checker
def _require_allowed_type(block: str, code: int) -> None:
    """Require the type to be accepted by the block.

    Parameters
    ----------
    block : str
        Block tag.
    code : int
        Effective application type.

    Raises
    ------
    ValueError
        If the block does not accept the type.
    """
    if code not in BLOCK_APLIC_TYPES[block]:
        raise ValueError(f"COD_TP_APLIC {code} is not allowed in {block}")


@type_checker
def _require_ativo_ext_scope(block: str, aplic: CdaAplic) -> None:
    """Allow ``ativo_ext`` only inside INV_EXT.

    Parameters
    ----------
    block : str
        Block tag.
    aplic : CdaAplic
        The application.

    Raises
    ------
    ValueError
        If ``ativo_ext`` is set elsewhere.
    """
    if aplic.ativo_ext is not None and block != "INV_EXT":
        raise ValueError(f"ativo_ext is only valid in INV_EXT, not {block}")


@type_checker
def _require_table_b(code: int, tp_ativ: int | None) -> None:
    """Apply the Table B application-type x asset-type relation.

    Parameters
    ----------
    code : int
        Effective application type.
    tp_ativ : Optional[int]
        Asset type of the enclosing block, when it has one.

    Raises
    ------
    ValueError
        If the asset type is not valid for the application type.
    """
    if tp_ativ is not None and tp_ativ not in _TABLE_B[code]:
        raise ValueError(f"COD_TP_ATIV {tp_ativ} is not valid for COD_TP_APLIC {code}")


@type_checker
def _check_aplic(block: str, aplic: CdaAplic, implicit: int | None, tp_ativ: int | None) -> None:
    """Validate an APLIC against its block (types, Table A, Table B).

    Parameters
    ----------
    block : str
            Block tag.
    aplic : CdaAplic
            The application.
    implicit : Optional[int]
            Application type implied by the block when the tag is absent.
    tp_ativ : Optional[int]
            Asset type of the enclosing block, when it has one.

    Raises
    ------
    ValueError
            On any rule violation.
    """
    code = _resolve_code(block, aplic, implicit)
    _require_allowed_type(block, code)
    _require_ativo_ext_scope(block, aplic)
    aplic.check_table_a(code)
    _require_table_b(code, tp_ativ)


class CdaSwapPosFim(BaseModel):
    """POS_FIM of a SWAP: only the market value (the page nests it in POS_FIM)."""

    merc_pos_fim: SignedMoney


class CdaSwapAplic(BaseModel):
    """APLIC of a SWAP: only the market value of the final position."""

    cod_tp_aplic: Literal[183, 184]
    qtde_dias_confid: int | None = Field(default=None, ge=0, le=90)
    pos_fim: CdaSwapPosFim


class CdaEmitter(BaseModel):
    """EMIS of TIT_AGRO_CRED_PRIV / DEMAIS_N_CODIF — PF/PJ issuer."""

    tp_pf_pj_emis: Literal["PF", "PJ"]
    nr_pf_pj_emis: str
    nm_emis: Annotated[Text, Field(max_length=150)]

    @model_validator(mode="after")
    def _doc(self) -> CdaEmitter:
        """Validate and normalise the document against the person type.

        Returns
        -------
        CdaEmitter
                The model.
        """
        self.nr_pf_pj_emis = validate_person_doc(self.tp_pf_pj_emis, self.nr_pf_pj_emis)
        return self


class CdaBankEmitter(BaseModel):
    """EMIS of DEP_PRAZO_TIT_IF — CNPJ issuer."""

    cnpj_emis: str
    nm_emis: Annotated[Text, Field(max_length=150)]

    @field_validator("cnpj_emis")
    @classmethod
    def _cnpj(cls, v: str) -> str:
        """Validate the CNPJ.

        Parameters
        ----------
        v : str
                CNPJ in any shape.

        Returns
        -------
        str
                Bare CNPJ.
        """
        return validated_cnpj(v)


class CdaPosFixIndex(BaseModel):
    """TIT_POS_FIX_INDEX — indexer of a post-fixed security."""

    tit_pos_fix_cod_index: str
    tit_pos_fix_pr_index: Rate
    tit_pos_fix_cupom: Rate

    @field_validator("tit_pos_fix_cod_index")
    @classmethod
    def _index(cls, v: str) -> str:
        """Require a Table D code.

        Parameters
        ----------
        v : str
                Indexer code.

        Returns
        -------
        str
                Validated code.

        Raises
        ------
        ValueError
                If not in Table D.
        """
        if v not in INDEXERS:
            raise ValueError(f"indexer {v!r} is not in Table D")
        return v


class CdaRiskRating(BaseModel):
    """CLASSIF_RISCO — issuer risk rating."""

    ag_classif_risco: Annotated[Text, Field(max_length=200)]
    dt_classif_risco: BrDate
    grau_classif_risco: Annotated[Text, Field(max_length=6)]


@type_checker
def _check_post_fixed(index: object, taxa: object) -> None:
    """Post-fixed needs the index block and no pre-fixed rate.

    Parameters
    ----------
    index : object
        The TIT_POS_FIX_INDEX block (or ``None``).
    taxa : object
        TIT_PRE_FIX_TAXA_CONTR (or ``None``).

    Raises
    ------
    ValueError
        On inconsistency.
    """
    if index is None or taxa is not None:
        raise ValueError("post-fixed security needs tit_pos_fix_index and no pre-fixed rate")


@type_checker
def _check_pre_fixed(index: object, taxa: object) -> None:
    """Pre-fixed needs the contracted rate and no index block.

    Parameters
    ----------
    index : object
        The TIT_POS_FIX_INDEX block (or ``None``).
    taxa : object
        TIT_PRE_FIX_TAXA_CONTR (or ``None``).

    Raises
    ------
    ValueError
        On inconsistency.
    """
    if index is not None or taxa is None:
        raise ValueError("pre-fixed security needs tit_pre_fix_taxa_contr and no index block")


_FIXING_CHECKS = {True: _check_post_fixed, False: _check_pre_fixed}


@type_checker
def _check_fixing(pos: bool, index: object, taxa: object) -> None:
    """Post-fixed needs the index block; pre-fixed needs the contracted rate.

    Parameters
    ----------
    pos : bool
            ST_TIT_POS_FIX is ``S``.
    index : object
            The TIT_POS_FIX_INDEX block (or ``None``).
    taxa : object
            TIT_PRE_FIX_TAXA_CONTR (or ``None``).

    Raises
    ------
    ValueError
            On inconsistency.
    """
    _FIXING_CHECKS[pos](index, taxa)


@type_checker
def _check_rating(flag: str, rating: object) -> None:
    """CLASSIF_RISCO is present exactly when ST_CLASSIF_RISCO is ``S``.

    Parameters
    ----------
    flag : str
            ``S`` or ``N``.
    rating : object
            The rating block (or ``None``).

    Raises
    ------
    ValueError
            On inconsistency.
    """
    if (flag == "S") != (rating is not None):
        raise ValueError("classif_risco must be present if and only if st_classif_risco is 'S'")


class CdaTitPub(BaseModel):
    """TIT_PUB — SELIC public security (types 75, 147)."""

    cod_selic: Text
    dt_venc: BrDate
    aplic: CdaAplic

    @model_validator(mode="after")
    def _rules(self) -> CdaTitPub:
        """Apply block rules.

        Returns
        -------
        CdaTitPub
                The model.
        """
        _check_aplic("TIT_PUB", self.aplic, None, None)
        return self


@type_checker
def _require_one_identifier(cnpj_fdo: str | None, cod_subclasse: str | None) -> None:
    """Require exactly one of the class CNPJ and the subclass code.

    Parameters
    ----------
    cnpj_fdo : Optional[str]
        CNPJ of the class.
    cod_subclasse : Optional[str]
        Subclass code.

    Raises
    ------
    ValueError
        If both or neither is set.
    """
    if (cnpj_fdo is None) == (cod_subclasse is None):
        raise ValueError("provide exactly one of cnpj_fdo or cod_subclasse")


@type_checker
def _normalise_cnpj(cnpj_fdo: str | None) -> str | None:
    """Validate a CNPJ when present.

    Parameters
    ----------
    cnpj_fdo : Optional[str]
        CNPJ in any shape, or ``None``.

    Returns
    -------
    str | None
        The result.
    """
    return None if cnpj_fdo is None else validated_cnpj(cnpj_fdo)


class CdaCotas(BaseModel):
    """COTAS — fund shares (type 197); CNPJ of the class xor subclass code."""

    cnpj_fdo: str | None = None
    cod_subclasse: Text | None = None
    aplic: CdaAplic

    @model_validator(mode="after")
    def _rules(self) -> CdaCotas:
        """Require exactly one identifier and apply block rules.

        Returns
        -------
        CdaCotas
                The model.

        Raises
        ------
        ValueError
                If both or neither identifier is set.
        """
        _require_one_identifier(self.cnpj_fdo, self.cod_subclasse)
        self.cnpj_fdo = _normalise_cnpj(self.cnpj_fdo)
        _check_aplic("COTAS", self.aplic, 197, None)
        return self


class CdaSwap(BaseModel):
    """SWAP — swap differential (types 183, 184)."""

    cod_swap: str
    aplic: CdaSwapAplic

    @field_validator("cod_swap")
    @classmethod
    def _swap(cls, v: str) -> str:
        """Require ``SWP`` + 3 characters.

        Parameters
        ----------
        v : str
                Swap code.

        Returns
        -------
        str
                Validated code.

        Raises
        ------
        ValueError
                If malformed.
        """
        if not _SWAP_RE.fullmatch(v):
            raise ValueError("cod_swap must be 'SWP' followed by a 3-character Table E code")
        return v


class CdaDemaisCodif(BaseModel):
    """DEMAIS_CODIF — other coded assets."""

    cod_ativ: Text
    cod_tp_ativ: int
    dt_ini_vigen: BrDate
    aplic: CdaAplic

    @model_validator(mode="after")
    def _rules(self) -> CdaDemaisCodif:
        """Apply block rules.

        Returns
        -------
        CdaDemaisCodif
                The model.
        """
        _check_aplic("DEMAIS_CODIF", self.aplic, None, self.cod_tp_ativ)
        return self


class CdaDepPrazoTitIf(BaseModel):
    """DEP_PRAZO_TIT_IF — time deposits and other financial-institution paper (74)."""

    cod_tp_ativ: int
    desc_ativ_vinc: Text | None = None
    emis: CdaBankEmitter
    dt_venc: BrDate
    st_tit_pos_fix: Literal["S", "N"]
    tit_pos_fix_index: CdaPosFixIndex | None = None
    tit_pre_fix_taxa_contr: Rate | None = None
    st_classif_risco: Literal["S", "N"]
    classif_risco: CdaRiskRating | None = None
    aplic: CdaAplic

    @model_validator(mode="after")
    def _rules(self) -> CdaDepPrazoTitIf:
        """Apply block rules.

        Returns
        -------
        CdaDepPrazoTitIf
                The model.
        """
        _check_fixing(
            self.st_tit_pos_fix == "S", self.tit_pos_fix_index, self.tit_pre_fix_taxa_contr
        )
        _check_rating(self.st_classif_risco, self.classif_risco)
        _check_aplic("DEP_PRAZO_TIT_IF", self.aplic, 74, self.cod_tp_ativ)
        return self


class CdaTitAgroCredPriv(BaseModel):
    """TIT_AGRO_CRED_PRIV — agribusiness and private-credit paper (193, 195, 196)."""

    cod_tp_ativ: int
    emis: CdaEmitter
    dt_venc: BrDate
    st_tit_pos_fix: Literal["S", "N"]
    tit_pos_fix_index: CdaPosFixIndex | None = None
    tit_pre_fix_taxa_contr: Rate | None = None
    st_tit_reg_cetip: Literal["S", "N"]
    st_tit_garant_seguro: Literal["S", "N"]
    cnpj_instit_financ: str | None = None
    aplic: CdaAplic

    @model_validator(mode="after")
    def _rules(self) -> CdaTitAgroCredPriv:
        """Apply block rules.

        Returns
        -------
        CdaTitAgroCredPriv
                The model.
        """
        _check_fixing(
            self.st_tit_pos_fix == "S", self.tit_pos_fix_index, self.tit_pre_fix_taxa_contr
        )
        if self.cnpj_instit_financ is not None:
            self.cnpj_instit_financ = validated_cnpj(self.cnpj_instit_financ)
        _check_aplic("TIT_AGRO_CRED_PRIV", self.aplic, None, self.cod_tp_ativ)
        return self


class CdaInvExt(BaseModel):
    """INV_EXT — foreign investment (189)."""

    cod_tp_ativ: int
    inv_coletivo: Literal["S", "N"]
    gest_inv_coletivo: Literal["S", "N"]
    nm_emis: Annotated[Text, Field(max_length=150)]
    dt_venc: BrDate | None = None
    cod_pais: int
    cod_bv_merc: Text
    cod_ativo_bv_merc: Text
    st_classif_risco: Literal["S", "N"]
    classif_risco: CdaRiskRating | None = None
    aplic: CdaAplic

    @model_validator(mode="after")
    def _rules(self) -> CdaInvExt:
        """Apply block rules.

        Returns
        -------
        CdaInvExt
                The model.
        """
        _check_rating(self.st_classif_risco, self.classif_risco)
        _check_aplic("INV_EXT", self.aplic, 189, self.cod_tp_ativ)
        return self


class CdaDemaisNCodif(BaseModel):
    """DEMAIS_N_CODIF — other, uncoded assets."""

    cod_tp_ativ: int
    desc: Annotated[Text, Field(max_length=1000)]
    emis: CdaEmitter
    aplic: CdaAplic

    @model_validator(mode="after")
    def _rules(self) -> CdaDemaisNCodif:
        """Apply block rules.

        Returns
        -------
        CdaDemaisNCodif
                The model.
        """
        _check_aplic("DEMAIS_N_CODIF", self.aplic, None, self.cod_tp_ativ)
        return self


class CdaInform(BaseModel):
    """INFORM — one fund/class. Block lists are emitted in the page's mandated order."""

    BLOCK_ORDER: ClassVar[tuple[str, ...]] = (
        "tit_pub",
        "cotas",
        "swap",
        "demais_codif",
        "dep_prazo_tit_if",
        "tit_agro_cred_priv",
        "inv_ext",
        "demais_n_codif",
    )

    cnpj_fdo: str
    vl_pl: PatrimonyValue
    tit_pub: list[CdaTitPub] = Field(default_factory=list)
    cotas: list[CdaCotas] = Field(default_factory=list)
    swap: list[CdaSwap] = Field(default_factory=list)
    demais_codif: list[CdaDemaisCodif] = Field(default_factory=list)
    dep_prazo_tit_if: list[CdaDepPrazoTitIf] = Field(default_factory=list)
    tit_agro_cred_priv: list[CdaTitAgroCredPriv] = Field(default_factory=list)
    inv_ext: list[CdaInvExt] = Field(default_factory=list)
    demais_n_codif: list[CdaDemaisNCodif] = Field(default_factory=list)

    @field_validator("cnpj_fdo")
    @classmethod
    def _cnpj(cls, v: str) -> str:
        """Validate the CNPJ.

        Parameters
        ----------
        v : str
                CNPJ in any shape.

        Returns
        -------
        str
                Bare CNPJ.
        """
        return validated_cnpj(v)


class CdaDocument(BaseModel):
    """DOC_ARQ — complete CDA file (at most 1000 funds, one competence)."""

    header: CdaHeader
    informs: list[CdaInform] = Field(max_length=1000)
