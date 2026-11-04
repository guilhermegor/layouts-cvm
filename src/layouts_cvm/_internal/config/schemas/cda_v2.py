"""Pydantic models for the CVM CDA XML standard — V2.

V2 is described by the CVM page
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLCDANet.aspx; namespace
``urn:cda``, ``COD_DOC=3``, ``VERSAO=2.0``). Measured against the V3 and V4 pages it is a
different structure, not a delta, so it has its own models. What differs:

* Five asset blocks only, in this order: ``TIT_PUB``, ``COTAS``, ``SWAP``, ``DEMAIS_CODIF``,
  ``DEMAIS_N_CODIF``. There is no ``DEP_PRAZO_TIT_IF``, ``TIT_AGRO_CRED_PRIV`` or ``INV_EXT``.
* ``APLIC`` has no ``EMPR_LIGADA``; ``POS_FIM`` has ``CUSTO_CORREC_POS_FIM`` (cost of the final
  position) between ``QTDE_POS_FIM`` and ``MERC_POS_FIM``.
* ``COTAS`` carries ``COD_TP_APLIC`` and is identified only by ``CNPJ_FDO``.
* ``QTDE_DIAS_CONFID`` "deve ser preenchido" (0 to 90) in every ``APLIC``.
* A file holds at most 50 funds or classes; Table A has 32 application types with its own
  Custo column; Table B is the page's list of asset types, and the application type x asset
  type relation is the last column of Table A.

Scales stated by the page: ``VL_PL`` 21 integer + 2 decimal digits; ``VL_*_NEGOC``,
``CUSTO_CORREC_POS_FIM`` and ``MERC_POS_FIM`` 15 + 2; ``QTDE_*`` 15 + 6. Excess decimals are
truncated. The page does not say which application types each block accepts; the models derive
it from the asset type each block stands for (``TIT_PUB`` 8, ``COTAS`` 22, ``SWAP`` 26) and
Table A's related asset types, and accept in ``DEMAIS_CODIF`` the asset types the page lists in
its template comment. Everything else is left unchecked (see ``docs/cda_v2.md``).
"""

from __future__ import annotations

import re
from typing import Annotated, ClassVar, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from layouts_cvm._internal.config.schemas._fields import validated_cnpj
from layouts_cvm._internal.config.schemas.cda import (
    BrDate,
    CdaEmitter,
    CdaHeader,
    CdaNegoc,
    PatrimonyValue,
    Quantity,
    SignedMoney,
    Text,
)
from layouts_cvm._internal.utils.typing import type_checker


_MAX_INFORMS = 50
_SWAP_RE = re.compile(r"SWP[A-Z0-9]{3}")

_TABLE_A: dict[int, tuple[str, str, str, str, str, str, str]] = {
    37: ("OP", "OP", "OP", "OP", "S", "S", "S"),
    39: ("OP", "OP", "OP", "OP", "S", "S", "S"),
    40: ("OP", "OP", "OP", "OP", "S", "S", "S"),
    42: ("N", "N", "OP", "OP", "S", "S", "S"),
    43: ("OP", "OP", "N", "N", "S", "S", "S"),
    44: ("OP", "OP", "OP", "OP", "S", "S", "S"),
    45: ("OP", "OP", "OP", "OP", "S", "S", "S"),
    48: ("OP", "OP", "OP", "OP", "S", "S", "S"),
    74: ("OP", "OP", "OP", "OP", "S", "S", "S"),
    75: ("OP", "OP", "OP", "OP", "S", "S", "S"),
    91: ("N", "N", "N", "N", "S", "S", "S"),
    92: ("OP", "OP", "OP", "OP", "S", "S", "S"),
    93: ("OP", "OP", "OP", "OP", "S", "S", "S"),
    94: ("N", "N", "N", "N", "N", "N", "S"),
    96: ("N", "N", "N", "N", "N", "N", "S"),
    97: ("N", "N", "N", "N", "N", "N", "S"),
    102: ("OP", "OP", "OP", "OP", "S", "N", "S"),
    103: ("OP", "OP", "OP", "OP", "S", "N", "S"),
    143: ("N", "N", "N", "N", "S", "S", "S"),
    146: ("N", "N", "N", "N", "S", "S", "S"),
    147: ("N", "N", "N", "N", "N", "S", "S"),
    148: ("OP", "OP", "OP", "OP", "S", "S", "S"),
    151: ("OP", "OP", "OP", "OP", "S", "S", "S"),
    152: ("OP", "OP", "OP", "OP", "S", "S", "S"),
    153: ("OP", "OP", "OP", "OP", "S", "S", "S"),
    183: ("N", "N", "N", "N", "N", "OP", "S"),
    184: ("N", "N", "N", "N", "N", "OP", "S"),
    185: ("OP", "OP", "OP", "OP", "S", "S", "S"),
    186: ("N", "N", "N", "N", "S", "N", "S"),
    187: ("OP", "OP", "OP", "OP", "S", "S", "S"),
    189: ("OP", "OP", "OP", "OP", "S", "S", "S"),
    190: ("OP", "OP", "OP", "OP", "S", "S", "S"),
}
_TABLE_A_COLUMNS = (
    "qtde_vendas_negoc",
    "vl_vendas_negoc",
    "qtde_aquis_negoc",
    "vl_aquis_negoc",
    "qtde_pos_fim",
    "custo_correc_pos_fim",
    "merc_pos_fim",
)
_RELATED_ASSETS: dict[int, frozenset[int]] = {
    37: frozenset({1, 2, 13}),
    39: frozenset({3, 4}),
    40: frozenset({3, 4}),
    42: frozenset({5}),
    43: frozenset({5}),
    44: frozenset({7}),
    45: frozenset({6}),
    48: frozenset({10, 21, 23, 25, 999}),
    74: frozenset({10}),
    75: frozenset({8}),
    91: frozenset({1, 2, 6, 7}),
    92: frozenset({22}),
    93: frozenset({22}),
    94: frozenset({999}),
    96: frozenset({999}),
    97: frozenset({999}),
    102: frozenset({9}),
    103: frozenset({9}),
    143: frozenset({1, 2}),
    146: frozenset({1, 2}),
    147: frozenset({8, 10}),
    148: frozenset({6, 7, 8}),
    151: frozenset({11, 12, 16}),
    152: frozenset({14, 15, 17, 18, 19, 24}),
    153: frozenset({20}),
    183: frozenset({26}),
    184: frozenset({26}),
    185: frozenset({10}),
    186: frozenset({1, 2, 13}),
    187: frozenset({999}),
    189: frozenset({10, 27}),
    190: frozenset({22}),
}
_ASSET_TYPES = frozenset({*range(1, 28), 999})
_CODIF_ASSET_TYPES = frozenset({*range(1, 8), 9, *range(10, 22), 23, 24, 25, 27}) - {8, 22, 26}
_TIT_PUB_ASSET = 8
_COTAS_ASSET = 22
_SWAP_ASSET = 26


@type_checker
def _require_filled(code: int, name: str, value: object) -> None:
    """Require a column (Table A flag ``S``).

    Parameters
    ----------
    code : int
        Application type, for the message.
    name : str
        Field name, for the message.
    value : object
        The field value.

    Raises
    ------
    ValueError
        If omitted.
    """
    if value is None:
        raise ValueError(f"{name} is required for COD_TP_APLIC {code}")


@type_checker
def _require_empty(code: int, name: str, value: object) -> None:
    """Forbid a column (Table A flag ``N``).

    Parameters
    ----------
    code : int
        Application type, for the message.
    name : str
        Field name, for the message.
    value : object
        The field value.

    Raises
    ------
    ValueError
        If filled.
    """
    if value is not None:
        raise ValueError(f"{name} must not be filled for COD_TP_APLIC {code}")


@type_checker
def _allow_any(code: int, name: str, value: object) -> None:
    """Accept any value (flag ``OP``).

    Parameters
    ----------
    code : int
        Unused.
    name : str
        Unused.
    value : object
        Unused.
    """


_FLAG_CHECKS = {"S": _require_filled, "N": _require_empty, "OP": _allow_any}


class CdaV2Header(CdaHeader):
    """CAB_INFORM — V2 header; ``VERSAO`` is pinned to ``2.0`` and ``COD_DOC`` to ``3``."""

    versao: Literal["2.0"] = "2.0"  # type: ignore[assignment]


class CdaV2PosFim(BaseModel):
    """POS_FIM — final position: quantity, cost and market value (page order)."""

    qtde_pos_fim: Quantity | None = None
    custo_correc_pos_fim: SignedMoney | None = None
    merc_pos_fim: SignedMoney


class CdaV2SwapNegoc(BaseModel):
    """NEGOC of a SWAP — the page gives it only ``TP_NEGOC``."""

    tp_negoc: Literal[1, 2]


class CdaV2SwapPosFim(BaseModel):
    """POS_FIM of a SWAP — cost (optional, Table A ``OP``) and market value."""

    custo_correc_pos_fim: SignedMoney | None = None
    merc_pos_fim: SignedMoney


class CdaV2Aplic(BaseModel):
    """APLIC — application, checked against Table A for its ``COD_TP_APLIC``."""

    cod_tp_aplic: int
    qtde_dias_confid: int = Field(ge=0, le=90)
    negoc: CdaNegoc | None = None
    pos_fim: CdaV2PosFim

    def column_values(self) -> tuple[object, ...]:
        """List the Table A columns of this application, in the table's order.

        Returns
        -------
        tuple[object, ...]
            Vendas Quant./R$, Aquisições Quant./R$, Posição Final Quant./Custo/Mercado
            (``None`` when omitted).
        """
        negoc = self.negoc
        return (
            negoc.qtde_vendas_negoc if negoc else None,
            negoc.vl_vendas_negoc if negoc else None,
            negoc.qtde_aquis_negoc if negoc else None,
            negoc.vl_aquis_negoc if negoc else None,
            self.pos_fim.qtde_pos_fim,
            self.pos_fim.custo_correc_pos_fim,
            self.pos_fim.merc_pos_fim,
        )


class CdaV2SwapAplic(BaseModel):
    """APLIC of a SWAP — types 183 and 184 only."""

    cod_tp_aplic: Literal[183, 184]
    qtde_dias_confid: int = Field(ge=0, le=90)
    negoc: CdaV2SwapNegoc | None = None
    pos_fim: CdaV2SwapPosFim


@type_checker
def _check_aplic(aplic: CdaV2Aplic, tp_ativ: int) -> None:
    """Validate an APLIC against Table A and the application x asset type relation.

    Parameters
    ----------
    aplic : CdaV2Aplic
        The application.
    tp_ativ : int
        Asset type of the enclosing block.

    Raises
    ------
    ValueError
        If the application type is unknown, does not relate to the asset type, or a column
        breaks its Table A flag.
    """
    code = aplic.cod_tp_aplic
    if code not in _TABLE_A:
        raise ValueError(f"COD_TP_APLIC {code} is not in Table A")
    if tp_ativ not in _RELATED_ASSETS[code]:
        raise ValueError(f"COD_TP_ATIV {tp_ativ} is not valid for COD_TP_APLIC {code}")
    for flag, name, value in zip(
        _TABLE_A[code], _TABLE_A_COLUMNS, aplic.column_values(), strict=True
    ):
        _FLAG_CHECKS[flag](code, name, value)


class CdaV2TitPub(BaseModel):
    """TIT_PUB — SELIC public security (asset type 8)."""

    cod_selic: Text
    dt_venc: BrDate
    aplic: CdaV2Aplic

    @model_validator(mode="after")
    def _rules(self) -> CdaV2TitPub:
        """Apply Table A for the public-security asset type.

        Returns
        -------
        CdaV2TitPub
            The model.
        """
        _check_aplic(self.aplic, _TIT_PUB_ASSET)
        return self


class CdaV2Cotas(BaseModel):
    """COTAS — shares of an invested fund (asset type 22), by ``CNPJ_FDO``."""

    cnpj_fdo: str
    aplic: CdaV2Aplic

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

    @model_validator(mode="after")
    def _rules(self) -> CdaV2Cotas:
        """Apply Table A for the fund-share asset type.

        Returns
        -------
        CdaV2Cotas
            The model.
        """
        _check_aplic(self.aplic, _COTAS_ASSET)
        return self


class CdaV2Swap(BaseModel):
    """SWAP — swap differential (types 183 and 184, asset type 26)."""

    cod_swap: str
    aplic: CdaV2SwapAplic

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
            raise ValueError("cod_swap must be 'SWP' followed by a 3-character Table D code")
        return v


class CdaV2DemaisCodif(BaseModel):
    """DEMAIS_CODIF — other coded assets."""

    cod_ativ: Text
    cod_tp_ativ: int
    dt_ini_vigen: BrDate
    aplic: CdaV2Aplic

    @model_validator(mode="after")
    def _rules(self) -> CdaV2DemaisCodif:
        """Require a listed asset type and apply Table A.

        Returns
        -------
        CdaV2DemaisCodif
            The model.

        Raises
        ------
        ValueError
            If the asset type is not one the page lists for this block.
        """
        if self.cod_tp_ativ not in _CODIF_ASSET_TYPES:
            raise ValueError(f"COD_TP_ATIV {self.cod_tp_ativ} is not allowed in DEMAIS_CODIF")
        _check_aplic(self.aplic, self.cod_tp_ativ)
        return self


class CdaV2DemaisNCodif(BaseModel):
    """DEMAIS_N_CODIF — assets with no registry code."""

    cod_tp_ativ: int
    desc: Annotated[Text, Field(max_length=1000)]
    emis: CdaEmitter
    aplic: CdaV2Aplic

    @model_validator(mode="after")
    def _rules(self) -> CdaV2DemaisNCodif:
        """Require a Table B asset type and apply Table A.

        Returns
        -------
        CdaV2DemaisNCodif
            The model.

        Raises
        ------
        ValueError
            If the asset type is not in Table B.
        """
        if self.cod_tp_ativ not in _ASSET_TYPES:
            raise ValueError(f"COD_TP_ATIV {self.cod_tp_ativ} is not in Table B")
        _check_aplic(self.aplic, self.cod_tp_ativ)
        return self


class CdaV2Inform(BaseModel):
    """INFORM — one fund or class. Block lists are emitted in the page's mandated order."""

    BLOCK_ORDER: ClassVar[tuple[str, ...]] = (
        "tit_pub",
        "cotas",
        "swap",
        "demais_codif",
        "demais_n_codif",
    )

    cnpj_fdo: str
    vl_pl: PatrimonyValue
    tit_pub: list[CdaV2TitPub] = Field(default_factory=list)
    cotas: list[CdaV2Cotas] = Field(default_factory=list)
    swap: list[CdaV2Swap] = Field(default_factory=list)
    demais_codif: list[CdaV2DemaisCodif] = Field(default_factory=list)
    demais_n_codif: list[CdaV2DemaisNCodif] = Field(default_factory=list)

    @field_validator("cnpj_fdo")
    @classmethod
    def _cnpj(cls, v: str) -> str:
        """Validate the fund's CNPJ.

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


class CdaV2Document(BaseModel):
    """DOC_ARQ — complete V2 file (at most 50 funds or classes, one competence)."""

    header: CdaV2Header
    informs: list[CdaV2Inform] = Field(max_length=_MAX_INFORMS)
