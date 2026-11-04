"""Pydantic models for the Semiannual Non-Resident Investor Report — Part II.

Direction-neutral schema for ``PadraoXMLInfoSemestralINRParte2.aspx``
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoSemestralINRParte2.aspx;
namespace ``urn:cda``, ``COD_DOC=70``, ``VERSAO=1.0``). Part II lists the applications of each
participant. Its layout is the CDA one (same blocks, same ``APLIC``/``POS_FIM`` nesting), but it
is a different standard with a different audience, so it owns its models: only the field
*vocabulary* (type aliases in :mod:`layouts_cvm._internal.config.schemas.cda`) is shared, never
a model or a validator.

**Field order is the XML order.** The writer walks ``model_fields`` in declaration order and
names each element ``<FIELD_NAME.upper()>``; a list repeats its element and a nested model is a
block. The eight asset blocks of ``LISTA_ATIV`` are lists declared in the page's mandated order.

Scales stated by the page: ``MERC_POS_FIM``, ``NOCION_POS_FIM`` and ``NOCION_SWAP`` 15 integer +
2 decimal digits; ``QTDE_POS_FIM`` 15 + 6; ``TIT_POS_FIX_PR_INDEX``, ``TIT_POS_FIX_CUPOM`` and
``TIT_PRE_FIX_TAXA_CONTR`` 3 + 6. Excess decimals are truncated (``ROUND_DOWN``).

Rules enforced from the page: the application types each block accepts (the
*Blocos x Tipos de Aplicações* table), Table A (quantity and notional required or forbidden per
application type), Table B (application type x asset type), the Table D indexers, the Table G
countries, the Table H exchanges, and the conditional blocks (post-fixed index, risk rating).
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, Field, field_validator, model_validator

from layouts_cvm._internal.config.schemas._fields import validate_person_doc, validated_cnpj
from layouts_cvm._internal.config.schemas.cda import (
    BrDate,
    ForeignValue,
    Quantity,
    Rate,
    SignedMoney,
    Text,
)
from layouts_cvm._internal.utils.inr_mensal_fields import (
    check_month_year,
    check_participant_code,
)
from layouts_cvm._internal.utils.typing import type_checker


_MAX_INFORMS = 1000
_SWAP_PREFIX = "SWP"
_SWAP_CODE_LEN = 6

YesNo = Literal["S", "N"]
MonthYear = Annotated[str, AfterValidator(check_month_year)]
ParticipantCode = Annotated[str, AfterValidator(check_participant_code)]

_INDEXERS = frozenset(
    {"ANB", "CDS", "DI1", "DOL", "I50", "IAP", "IBX", "IEE", "IGD", "IGM", "IGP", "IMA"}
    | {"IMA-B", "IMA-B5", "IMA-B5+", "IMA-C", "IMA-C5", "IMA-C5+", "IMA-S", "IND", "INP"}
    | {"IPC", "IRF", "ITE", "JPY", "OUT", "OZ1", "PIB", "PRE", "REU", "SB1", "SB2", "SEL"}
    | {"TBF", "TJL", "TR"}
)
_COUNTRIES = frozenset(
    {1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24}
    | {25, 26, 27, 28, 29, 30, 31, 32, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46}
    | {47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67}
    | {68, 69, 70, 71, 72, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89}
    | {90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108}
    | {109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 121, 123, 125, 126, 127, 128}
    | {129, 130, 131, 132, 133, 134, 137, 138, 139, 140, 141, 142, 160, 161, 162, 163, 164}
    | {165, 166, 167, 168, 169, 170, 171, 172, 173, 175, 176, 177, 178, 179, 180, 181, 182}
    | {183, 184, 186, 187, 188, 189, 190, 191, 193, 195, 196, 197, 198, 199, 200, 201, 202}
    | {203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219}
    | {221, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 237, 239, 240, 241}
    | {243, 244, 245, 246, 247, 248, 249, 251, 254, 255, 256, 257, 258, 259, 260, 263, 264}
    | {265, 266, 267, 268, 270, 271}
)
_EXCHANGES = frozenset(
    {"99", "A1", "A10", "A11", "A12", "A13", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9"}
    | {"C1", "C10", "C11", "C12", "C13", "C14", "C15", "C16", "C17", "C18", "C2", "C3", "C4"}
    | {"C5", "C6", "C7", "C8", "C9", "E1", "E10", "E11", "E12", "E13", "E14", "E15", "E16"}
    | {"E17", "E18", "E19", "E2", "E20", "E21", "E22", "E3", "E4", "E5", "E6", "E7", "E8", "E9"}
)

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
    189: frozenset({1, 2, 3, 4, 6, 7, 9, 11, 12, 13, 14, 15, 17, 18, 19, 20, 21, 23, 26, 27})
    | {46, 82, 83, 90, 91, 92, 999},
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

_NO_QUANTITY = frozenset({94, 96, 97, 183, 184, 191, 192})
_NOTIONAL = frozenset({39, 40, 42, 43, 102, 103, 183, 184, 191, 192})
_CODIF_TYPES = frozenset({37, 39, 40, 42, 43, 102, 103, 143, 146, 151, 152, 198})
_BLOCK_TYPES: dict[str, frozenset[int]] = {
    "TIT_PUB": frozenset({75, 147}),
    "COTAS": frozenset({197}),
    "SWAP": frozenset({183, 184}),
    "DEMAIS_CODIF": _CODIF_TYPES | {193},
    "DEP_PRAZO_TIT_IF": frozenset({74}),
    "TIT_AGRO_CRED_PRIV": frozenset({193, 195, 196}),
    "INV_EXT": frozenset({189}),
    "DEMAIS_N_CODIF": frozenset({48, 75, 94, 96, 97, 147, 187, 191, 192, 199, 200}) | _CODIF_TYPES,
}
_DEP_TYPE = 74
_EXT_TYPE = 189


@type_checker
def _require_block_type(block: str, code: int) -> None:
    """Require the block to accept the application type.

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
    if code not in _BLOCK_TYPES[block]:
        raise ValueError(f"COD_TP_APLIC {code} is not allowed in {block}")


@type_checker
def _require_table_b(code: int, tp_ativ: int | None) -> None:
    """Apply Table B: the asset type must relate to the application type.

    Parameters
    ----------
    code : int
        Effective application type.
    tp_ativ : int or None
        Asset type of the enclosing block, ``None`` where the block carries none.

    Raises
    ------
    ValueError
        If Table B does not relate the asset type to the application type.
    """
    if tp_ativ is not None and tp_ativ not in _TABLE_B[code]:
        raise ValueError(f"COD_TP_ATIV {tp_ativ} is not valid for COD_TP_APLIC {code}")


@type_checker
def _check_type(block: str, code: int, tp_ativ: int | None) -> None:
    """Require the application type to fit the block and, when given, the asset type.

    Parameters
    ----------
    block : str
        Block tag.
    code : int
        Effective application type.
    tp_ativ : int or None
        Asset type of the enclosing block, ``None`` where the block carries none.
    """
    _require_block_type(block, code)
    _require_table_b(code, tp_ativ)


_FLAG_VERDICTS = {True: "is required for", False: "must not be filled for"}


@type_checker
def _check_flag(code: int, name: str, value: object, required: bool) -> None:
    """Apply one Table A cell: ``S`` (required) or ``N`` (forbidden).

    Parameters
    ----------
    code : int
        Effective application type.
    name : str
        Tag name, for the message.
    value : object
        The field value (``None`` when omitted).
    required : bool
        Whether Table A marks the cell ``S``.

    Raises
    ------
    ValueError
        If the field is filled where forbidden, or omitted where required.
    """
    if required == (value is None):
        raise ValueError(f"{name} {_FLAG_VERDICTS[required]} COD_TP_APLIC {code}")


@type_checker
def _check_table_a(code: int, qtde: object, nocion: object) -> None:
    """Apply Table A: quantity and notional are required (``S``) or forbidden (``N``).

    Parameters
    ----------
    code : int
        Effective application type.
    qtde : object
        ``QTDE_POS_FIM`` (``None`` when omitted).
    nocion : object
        ``NOCION_POS_FIM`` (``None`` when omitted).
    """
    _check_flag(code, "QTDE_POS_FIM", qtde, code not in _NO_QUANTITY)
    _check_flag(code, "NOCION_POS_FIM", nocion, code in _NOTIONAL)


@type_checker
def _check_post_fixed(index: object, taxa: object) -> None:
    """Post-fixed needs the index block and no contracted rate.

    Parameters
    ----------
    index : object
        The ``TIT_POS_FIX_INDEX`` block, or ``None``.
    taxa : object
        ``TIT_PRE_FIX_TAXA_CONTR``, or ``None``.

    Raises
    ------
    ValueError
        If the index is missing or a rate is present.
    """
    if index is None or taxa is not None:
        raise ValueError("post-fixed security needs tit_pos_fix_index and no pre-fixed rate")


@type_checker
def _check_pre_fixed(index: object, taxa: object) -> None:
    """Pre-fixed needs the contracted rate and no index block.

    Parameters
    ----------
    index : object
        The ``TIT_POS_FIX_INDEX`` block, or ``None``.
    taxa : object
        ``TIT_PRE_FIX_TAXA_CONTR``, or ``None``.

    Raises
    ------
    ValueError
        If the rate is missing or an index is present.
    """
    if index is not None or taxa is None:
        raise ValueError("pre-fixed security needs tit_pre_fix_taxa_contr and no index block")


_FIXING_CHECKS = {"S": _check_post_fixed, "N": _check_pre_fixed}


@type_checker
def _check_fixing(st_pos_fix: str, index: object, taxa: object) -> None:
    """Post-fixed needs the index block; pre-fixed needs the contracted rate.

    Parameters
    ----------
    st_pos_fix : str
        ``ST_TIT_POS_FIX`` (``S`` or ``N``).
    index : object
        The ``TIT_POS_FIX_INDEX`` block, or ``None``.
    taxa : object
        ``TIT_PRE_FIX_TAXA_CONTR``, or ``None``.
    """
    _FIXING_CHECKS[st_pos_fix](index, taxa)


@type_checker
def _check_rating(st_classif_risco: str, rating: object) -> None:
    """Require ``CLASSIF_RISCO`` exactly when ``ST_CLASSIF_RISCO`` is ``S``.

    Parameters
    ----------
    st_classif_risco : str
        ``S`` or ``N``.
    rating : object
        The ``CLASSIF_RISCO`` block, or ``None``.

    Raises
    ------
    ValueError
        If the block and the flag disagree.
    """
    if (st_classif_risco == "S") != (rating is not None):
        raise ValueError("classif_risco must be present if and only if st_classif_risco is 'S'")


class InformeSemestralInrParte2Header(BaseModel):
    """CAB_INFORM — document header (``COD_DOC`` fixed at 70, ``VERSAO`` at 1.0)."""

    cod_doc: Literal[70] = 70
    versao: Literal["1.0"] = "1.0"
    dt_compt: MonthYear
    dt_gerac_arq: BrDate


class InrParte2PosFim(BaseModel):
    """POS_FIM with quantity and market value — blocks whose Table A row forbids a notional."""

    qtde_pos_fim: Quantity
    merc_pos_fim: SignedMoney


class InrParte2SwapPosFim(BaseModel):
    """POS_FIM of a SWAP — only the market value."""

    merc_pos_fim: SignedMoney


class InrParte2NocionalPosFim(BaseModel):
    """POS_FIM of DEMAIS_CODIF and DEMAIS_N_CODIF — quantity and notional follow Table A."""

    qtde_pos_fim: Quantity | None = None
    merc_pos_fim: SignedMoney
    nocion_pos_fim: SignedMoney | None = None


class InrParte2Aplic(BaseModel):
    """APLIC of TIT_PUB and TIT_AGRO_CRED_PRIV — explicit type, quantity and market value."""

    cod_tp_aplic: int
    pos_fim: InrParte2PosFim


class InrParte2ImplicitAplic(BaseModel):
    """APLIC of COTAS and DEP_PRAZO_TIT_IF — the block implies the type (197 and 74)."""

    pos_fim: InrParte2PosFim


class InrParte2SwapAplic(BaseModel):
    """APLIC of a SWAP — types 183 and 184, market value only."""

    cod_tp_aplic: Literal[183, 184]
    pos_fim: InrParte2SwapPosFim


class InrParte2CodifAplic(BaseModel):
    """APLIC of DEMAIS_CODIF and DEMAIS_N_CODIF — explicit type, Table A decides the fields."""

    cod_tp_aplic: int
    pos_fim: InrParte2NocionalPosFim

    @model_validator(mode="after")
    def _table_a(self) -> InrParte2CodifAplic:
        """Apply Table A to the final position.

        Returns
        -------
        InrParte2CodifAplic
            The model.
        """
        _check_table_a(self.cod_tp_aplic, self.pos_fim.qtde_pos_fim, self.pos_fim.nocion_pos_fim)
        return self


class InrParte2AtivoExt(BaseModel):
    """ATIVO_EXT — detail of a foreign asset."""

    desc_at_ext: Annotated[Text, Field(max_length=50)]
    qtde_at_ext: int = Field(ge=0)
    valor_at_ext: ForeignValue


class InrParte2ExtAplic(BaseModel):
    """APLIC of INV_EXT — application date, final position and optional foreign-asset detail."""

    dt_aplic: BrDate
    pos_fim: InrParte2PosFim
    ativo_ext: InrParte2AtivoExt | None = None


class InrParte2BankEmis(BaseModel):
    """EMIS of DEP_PRAZO_TIT_IF — CNPJ issuer."""

    cnpj_emis: str
    nm_emis: Annotated[Text, Field(max_length=150)]

    @field_validator("cnpj_emis")
    @classmethod
    def _cnpj(cls, v: str) -> str:
        """Validate the issuer's CNPJ.

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


class InrParte2PersonEmis(BaseModel):
    """EMIS of TIT_AGRO_CRED_PRIV and DEMAIS_N_CODIF — PF or PJ issuer."""

    tp_pf_pj_emis: Literal["PF", "PJ"]
    nr_pf_pj_emis: str
    nm_emis: Annotated[Text, Field(max_length=150)]

    @model_validator(mode="after")
    def _document(self) -> InrParte2PersonEmis:
        """Validate the CPF or CNPJ against the person type and store its bare form.

        Returns
        -------
        InrParte2PersonEmis
            The model.
        """
        self.nr_pf_pj_emis = validate_person_doc(self.tp_pf_pj_emis, self.nr_pf_pj_emis)
        return self


class InrParte2PosFixIndex(BaseModel):
    """TIT_POS_FIX_INDEX — indexer of a post-fixed security (Table D)."""

    tit_pos_fix_cod_index: str
    tit_pos_fix_pr_index: Rate
    tit_pos_fix_cupom: Rate

    @field_validator("tit_pos_fix_cod_index")
    @classmethod
    def _indexer(cls, v: str) -> str:
        """Require a Table D code.

        Parameters
        ----------
        v : str
            Indexer code.

        Returns
        -------
        str
            The same code.

        Raises
        ------
        ValueError
            If it is not in Table D.
        """
        if v not in _INDEXERS:
            raise ValueError(f"indexer {v!r} is not in Table D")
        return v


class InrParte2ClassifRisco(BaseModel):
    """CLASSIF_RISCO — the issuer's risk rating."""

    ag_classif_risco: Annotated[Text, Field(max_length=200)]
    dt_classif_risco: BrDate
    grau_classif_risco: Annotated[Text, Field(max_length=6)]


class InrParte2TitPub(BaseModel):
    """TIT_PUB — SELIC public security (types 75 and 147)."""

    cod_selic: Text
    dt_venc: BrDate
    aplic: InrParte2Aplic

    @model_validator(mode="after")
    def _rules(self) -> InrParte2TitPub:
        """Apply the block's application types.

        Returns
        -------
        InrParte2TitPub
            The model.
        """
        _check_type("TIT_PUB", self.aplic.cod_tp_aplic, None)
        return self


class InrParte2Cotas(BaseModel):
    """COTAS — shares of an invested fund (type 197, implied by the block)."""

    cnpj_fdo: str
    aplic: InrParte2ImplicitAplic

    @field_validator("cnpj_fdo")
    @classmethod
    def _cnpj(cls, v: str) -> str:
        """Validate the invested fund's CNPJ.

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


class InrParte2Swap(BaseModel):
    """SWAP — swap differential (types 183 and 184)."""

    cod_swap: str
    aplic: InrParte2SwapAplic

    @field_validator("cod_swap")
    @classmethod
    def _swap(cls, v: str) -> str:
        """Require ``SWP`` followed by a 3-character Table E code.

        Parameters
        ----------
        v : str
            Swap code.

        Returns
        -------
        str
            The same code.

        Raises
        ------
        ValueError
            If it is not ``SWP`` plus three ASCII letters or digits.
        """
        body = v[len(_SWAP_PREFIX) :]
        if (
            len(v) != _SWAP_CODE_LEN
            or not v.startswith(_SWAP_PREFIX)
            or not (body.isascii() and body.isalnum())
        ):
            raise ValueError("cod_swap must be 'SWP' followed by a 3-character Table E code")
        return v


class InrParte2DemaisCodif(BaseModel):
    """DEMAIS_CODIF — other assets found in the CVM asset registry."""

    cod_ativ: Text
    cod_tp_ativ: int
    dt_ini_vigen: BrDate
    aplic: InrParte2CodifAplic

    @model_validator(mode="after")
    def _rules(self) -> InrParte2DemaisCodif:
        """Apply the block's types and Table B.

        Returns
        -------
        InrParte2DemaisCodif
            The model.
        """
        _check_type("DEMAIS_CODIF", self.aplic.cod_tp_aplic, self.cod_tp_ativ)
        return self


class InrParte2DepPrazoTitIf(BaseModel):
    """DEP_PRAZO_TIT_IF — term deposits and other bank securities (type 74, implied)."""

    cod_tp_ativ: int
    emis: InrParte2BankEmis
    dt_venc: BrDate
    st_tit_pos_fix: YesNo
    tit_pos_fix_index: InrParte2PosFixIndex | None = None
    tit_pre_fix_taxa_contr: Rate | None = None
    st_classif_risco: YesNo
    classif_risco: InrParte2ClassifRisco | None = None
    aplic: InrParte2ImplicitAplic

    @model_validator(mode="after")
    def _rules(self) -> InrParte2DepPrazoTitIf:
        """Apply Table B and the fixing and rating conditionals.

        Returns
        -------
        InrParte2DepPrazoTitIf
            The model.
        """
        _check_type("DEP_PRAZO_TIT_IF", _DEP_TYPE, self.cod_tp_ativ)
        _check_fixing(self.st_tit_pos_fix, self.tit_pos_fix_index, self.tit_pre_fix_taxa_contr)
        _check_rating(self.st_classif_risco, self.classif_risco)
        return self


class InrParte2TitAgroCredPriv(BaseModel):
    """TIT_AGRO_CRED_PRIV — agribusiness and private credit securities."""

    cod_tp_ativ: int
    emis: InrParte2PersonEmis
    dt_venc: BrDate
    st_tit_pos_fix: YesNo
    tit_pos_fix_index: InrParte2PosFixIndex | None = None
    tit_pre_fix_taxa_contr: Rate | None = None
    st_tit_reg_cetip: YesNo
    st_tit_garant_seguro: YesNo
    cnpj_instit_financ: str | None = None
    aplic: InrParte2Aplic

    @field_validator("cnpj_instit_financ")
    @classmethod
    def _cnpj(cls, v: str | None) -> str | None:
        """Validate the co-obligor's CNPJ when given.

        Parameters
        ----------
        v : str or None
            CNPJ in any shape, or ``None``.

        Returns
        -------
        str or None
            Bare CNPJ, or ``None``.
        """
        return None if v is None else validated_cnpj(v)

    @model_validator(mode="after")
    def _rules(self) -> InrParte2TitAgroCredPriv:
        """Apply the block's types, Table B and the fixing conditional.

        Returns
        -------
        InrParte2TitAgroCredPriv
            The model.
        """
        _check_type("TIT_AGRO_CRED_PRIV", self.aplic.cod_tp_aplic, self.cod_tp_ativ)
        _check_fixing(self.st_tit_pos_fix, self.tit_pos_fix_index, self.tit_pre_fix_taxa_contr)
        return self


class InrParte2InvExt(BaseModel):
    """INV_EXT — investment abroad (type 189, implied)."""

    cod_tp_ativ: int
    inv_coletivo: YesNo
    gest_inv_coletivo: YesNo
    nm_emis: Annotated[Text, Field(max_length=150)]
    dt_venc: BrDate | None = None
    cod_pais: int
    cod_bv_merc: str
    cod_ativo_bv_merc: Text
    st_classif_risco: YesNo
    classif_risco: InrParte2ClassifRisco | None = None
    aplic: InrParte2ExtAplic

    @field_validator("cod_pais")
    @classmethod
    def _country(cls, v: int) -> int:
        """Require a Table G country.

        Parameters
        ----------
        v : int
            Country code.

        Returns
        -------
        int
            The same code.

        Raises
        ------
        ValueError
            If it is not in Table G.
        """
        if v not in _COUNTRIES:
            raise ValueError(f"country {v} is not in Table G")
        return v

    @field_validator("cod_bv_merc")
    @classmethod
    def _exchange(cls, v: str) -> str:
        """Require a Table H exchange or over-the-counter market.

        Parameters
        ----------
        v : str
            Exchange code.

        Returns
        -------
        str
            The same code.

        Raises
        ------
        ValueError
            If it is not in Table H.
        """
        if v not in _EXCHANGES:
            raise ValueError(f"exchange {v!r} is not in Table H")
        return v

    @model_validator(mode="after")
    def _rules(self) -> InrParte2InvExt:
        """Apply Table B and the rating conditional.

        Returns
        -------
        InrParte2InvExt
            The model.
        """
        _check_type("INV_EXT", _EXT_TYPE, self.cod_tp_ativ)
        _check_rating(self.st_classif_risco, self.classif_risco)
        return self


class InrParte2DemaisNCodif(BaseModel):
    """DEMAIS_N_CODIF — assets absent from the CVM asset registry."""

    cod_tp_ativ: int
    desc: Annotated[Text, Field(max_length=1000)]
    emis: InrParte2PersonEmis
    aplic: InrParte2CodifAplic

    @model_validator(mode="after")
    def _rules(self) -> InrParte2DemaisNCodif:
        """Apply the block's types and Table B.

        Returns
        -------
        InrParte2DemaisNCodif
            The model.
        """
        _check_type("DEMAIS_N_CODIF", self.aplic.cod_tp_aplic, self.cod_tp_ativ)
        return self


class InrParte2ListaAtiv(BaseModel):
    """LISTA_ATIV — the asset blocks, each repeatable, in the page's mandated order.

    ``NOCION_SWAP`` follows the SWAP blocks and is present exactly when a SWAP is.
    """

    tit_pub: list[InrParte2TitPub] = Field(default_factory=list)
    cotas: list[InrParte2Cotas] = Field(default_factory=list)
    swap: list[InrParte2Swap] = Field(default_factory=list)
    nocion_swap: SignedMoney | None = None
    demais_codif: list[InrParte2DemaisCodif] = Field(default_factory=list)
    dep_prazo_tit_if: list[InrParte2DepPrazoTitIf] = Field(default_factory=list)
    tit_agro_cred_priv: list[InrParte2TitAgroCredPriv] = Field(default_factory=list)
    inv_ext: list[InrParte2InvExt] = Field(default_factory=list)
    demais_n_codif: list[InrParte2DemaisNCodif] = Field(default_factory=list)

    @model_validator(mode="after")
    def _notional_swap(self) -> InrParte2ListaAtiv:
        """Require the swap notional exactly when the participant holds a swap.

        Returns
        -------
        InrParte2ListaAtiv
            The model.

        Raises
        ------
        ValueError
            If a swap lacks its notional or a notional has no swap.
        """
        if bool(self.swap) != (self.nocion_swap is not None):
            raise ValueError("nocion_swap must be present if and only if a swap is reported")
        return self


class InrParte2Inform(BaseModel):
    """INFORM — one participant and its applications."""

    cod_partic: ParticipantCode
    lista_ativ: InrParte2ListaAtiv


class InrParte2ListaInform(BaseModel):
    """LISTA_INFORM — 1 to 1000 participants."""

    inform: list[InrParte2Inform] = Field(min_length=1, max_length=_MAX_INFORMS)


class InformeSemestralInrParte2Document(BaseModel):
    """DOC_ARQ — a complete Part II file: header plus 1 to 1000 participants."""

    cab_inform: InformeSemestralInrParte2Header
    lista_inform: InrParte2ListaInform
