"""Unit tests for the Informe Mensal FIDC (ICVM 489) submission writer.

Expected tags, order, scales and rules are taken from the CVM page
``PadraoXMLMensalFIDC489.asp``, not from the code under test.
"""

from collections.abc import Callable
from copy import deepcopy
from decimal import Decimal
from functools import partial, reduce
from pathlib import Path
import re
import types
from typing import Any, Literal, Union, get_args, get_origin

from pydantic import BaseModel, ValidationError
import pytest

from layouts_cvm import InfMensalFidc489
from layouts_cvm._internal.config.schemas.inf_mensal_fidc_489 import InfMensalFidc489Document


VALID_CNPJ = "11222333000181"
VALID_CPF = "52998224725"

SPEC_TAGS = """
    DOC_ARQ CAB_INFORM DT_COMPT NR_CNPJ_ADM NR_CNPJ_FUNDO TP_CONDOMINIO FDO_EXCL COTST_VINCUL
    LISTA_INFORM APLIC_ATIVO VL_DISPONIB VL_CARTEIRA CRED_EXISTE VL_SOM_DICRED_AQUIS
    VL_CRED_EXISTE_VENC_ADIMPL VL_CRED_EXISTE_VENC_INAD VL_CRED_TOTAL_VENC_INAD
    VL_CRED_EXISTE_INAD VL_CRED_REFER_DICRED_PERFO VL_CRED_VENC_PEND
    VL_CRED_ORIGEM_EMP_PROC_RECUP VL_DECOR_RECEIT_PUBLIC VL_CRED_ACAO_JUDIC
    VL_CRED_CONST_JUR_FATRISC VL_OUTROS_CRED VL_PROVIS_REDUC_RECUP DICRED VL_DICRED
    VL_DICRED_CEDENT LISTA_CEDENT CEDENT NR_PF_PJ_CEDENT PR_CEDENT VALORES_MOB
    VL_SOM_VALORES_MOB VL_DEBT VL_CRI VL_NP_COMERC VL_LETRA_FINANC VL_COTA_FDO_ICVM409
    VL_OUTRO_DICRED VL_TITPUB_FED VL_CDB VL_APLIC_OPER_COMPSS VL_ATIV_FINANC_RF VL_COTA_FIDC
    VL_COTA_FIDC_NAO_PADRAO VL_CONTR_COMPRA_VENDA_PRESTC_FUTURA MERC_DERIVATIVO
    VL_SOM_MERC_DERIVATIVO VL_MERC_TERMO_POS_COMPRD VL_MERC_OP_POS_TITUL
    VL_MERC_FUT_AJUST_POSIT VL_DIFER_SWAP_RECEB VL_COBERT_PREST VL_DEPOS_MARGEM OUTROS_ATIVOS
    VL_SOM_OUTROS_ATIVOS VL_OUTRO_VL_RECEB_CURPRZ VL_OUTRO_VL_RECEB_LPRAZO VL_SOM_APLIC_ATIVO
    CART_SEGMT VL_SOM_CART_SEGMT VL_IND VL_MERC_IMOBIL SEGMT_COMERC VL_SOM_SEGMT_COMERC
    VL_COMERC VL_COMERC_VARJ VL_ARREND_MERCNT SEGMT_SERV VL_SOM_SEGMT_SERV VL_SERV
    VL_SERV_PUBLIC VL_SERV_EDUC VL_SERV_ENTRETEN VL_AGRONEG SEGMT_FINANC VL_SOM_SEGMT_FINANC
    VL_FINANC_CRED_PESSOA VL_FINANC_CRED_PESSOA_CONSIG VL_FINANC_CRED_CORPOR VL_FINANC_MMARKET
    VL_FINANC_VEICL VL_FINANC_IMOBIL_EMPSRL VL_FINANC_IMOBIL_RESID VL_FINANC_OUTRO
    VL_CART_CRED SEGMT_FACT VL_SOM_SEGMT_FACT VL_FACT_PESSOA VL_FACT_CORPOR SEGMT_SETOR_PUBLIC
    VL_SOM_SEGMT_SETOR_PUBLIC VL_SETOR_PUBLIC_PRECAT VL_SETOR_PUBLIC_CRED_TRIBUT
    VL_SETOR_PUBLIC_ROYA VL_SETOR_PUBLIC_OUTRO VL_ACAO_JUDIC VL_PROPRD_MARCA_PATENT PASSIV
    VL_SOM_PASSIV PASSIV_VALORES VL_SOM_PASSIV_VALORES VL_PGTO_CURPRZ VL_PGTO_LPRAZO
    PASSIV_POSICOES VL_SOM_PASSIV_POSICOES VL_POS_MANT_VEND VL_POS_MANT_LANC
    VL_POS_MANT_AJT_FUT VL_POS_MANT_SWAP_PAGAR PATRLIQ VL_SOM_PATRLIQ VL_PATRIM_LIQ
    VL_PATRIM_LIQ_MEDIO COMPMT_DICRED_AQUIS VL_SOM_PRAZO_VENC VL_PRAZO_VENC_30
    VL_PRAZO_VENC_31_60 VL_PRAZO_VENC_61_90 VL_PRAZO_VENC_91_120 VL_PRAZO_VENC_121_150
    VL_PRAZO_VENC_151_180 VL_PRAZO_VENC_181_360 VL_PRAZO_VENC_361_720 VL_PRAZO_VENC_721_1080
    VL_PRAZO_VENC_1080 VL_SOM_INAD_VENC VL_INAD_VENC_30 VL_INAD_VENC_31_60 VL_INAD_VENC_61_90
    VL_INAD_VENC_91_120 VL_INAD_VENC_121_150 VL_INAD_VENC_151_180 VL_INAD_VENC_181_360
    VL_INAD_VENC_361_720 VL_INAD_VENC_721_1080 VL_INAD_VENC_1080 VL_SOM_PAGO_ANTCP
    VL_PAGO_ANTCP_30 VL_PAGO_ANTCP_31_60 VL_PAGO_ANTCP_61_90 VL_PAGO_ANTCP_91_120
    VL_PAGO_ANTCP_121_150 VL_PAGO_ANTCP_151_180 VL_PAGO_ANTCP_181_360 VL_PAGO_ANTCP_361_720
    VL_PAGO_ANTCP_721_1080 VL_PAGO_ANTCP_1080 COMPMT_DICRED_SEM_AQUIS VL_SOM_PRAZO_VENC
    VL_PRAZO_VENC_30 VL_PRAZO_VENC_31_60 VL_PRAZO_VENC_61_90 VL_PRAZO_VENC_91_120
    VL_PRAZO_VENC_121_150 VL_PRAZO_VENC_151_180 VL_PRAZO_VENC_181_360 VL_PRAZO_VENC_361_720
    VL_PRAZO_VENC_721_1080 VL_PRAZO_VENC_1080 VL_SOM_INAD_VENC VL_INAD_VENC_30
    VL_INAD_VENC_31_60 VL_INAD_VENC_61_90 VL_INAD_VENC_91_120 VL_INAD_VENC_121_150
    VL_INAD_VENC_151_180 VL_INAD_VENC_181_360 VL_INAD_VENC_361_720 VL_INAD_VENC_721_1080
    VL_INAD_VENC_1080 VL_SOM_PAGO_ANTCP VL_PAGO_ANTCP_30 VL_PAGO_ANTCP_31_60
    VL_PAGO_ANTCP_61_90 VL_PAGO_ANTCP_91_120 VL_PAGO_ANTCP_121_150 VL_PAGO_ANTCP_151_180
    VL_PAGO_ANTCP_181_360 VL_PAGO_ANTCP_361_720 VL_PAGO_ANTCP_721_1080 VL_PAGO_ANTCP_1080
    NEGOC_DICRED_MES AQUISICOES QT_DICRED_AQUIS VL_DICRED_AQUIS NEGOC_DICRED_MES_AQUIS
    QT_DICRED_AQUIS VL_DICRED_AQUIS NEGOC_DICRED_MES_SEM_AQUIS QT_DICRED_AQUIS VL_DICRED_AQUIS
    NEGOC_DICRED_MES_VENC_ADIMPL QT_DICRED_AQUIS VL_DICRED_AQUIS NEGOC_DICRED_MES_VENC_INAD
    QT_DICRED_AQUIS VL_DICRED_AQUIS NEGOC_DICRED_MES_INAD QT_DICRED_AQUIS VL_DICRED_AQUIS
    DICRED_MES_ALIEN QT_DICRED_ALIEN VL_DICRED_ALIEN VL_DICRED_ALIEN_CONTAB
    DICRED_MES_ALIEN_CEDENT QT_DICRED_ALIEN VL_DICRED_ALIEN VL_DICRED_ALIEN_CONTAB
    DICRED_MES_ALIEN_PREST QT_DICRED_ALIEN VL_DICRED_ALIEN VL_DICRED_ALIEN_CONTAB
    DICRED_MES_ALIEN_TERCR QT_DICRED_ALIEN VL_DICRED_ALIEN VL_DICRED_ALIEN_CONTAB
    DICRED_MES_ALIEN_SUBST QT_DICRED_ALIEN VL_DICRED_ALIEN VL_DICRED_ALIEN_CONTAB
    DICRED_MES_ALIEN_RECOMP QT_DICRED_ALIEN VL_DICRED_ALIEN VL_DICRED_ALIEN_CONTAB INFORM
    LISTA_DEV_SACADOS DEV_SACADOS NR_PF_PJ_SACADO_DEVED_1 VL_SACADO_DEVED_1 PR_SACADO_DEVED_1
    VL_SOM_LISTA_DEV_SACADOS PR_SOM_LISTA_DEV_SACADOS TAXA_NEGOC_DICRED_MES
    TAXA_NEGOC_DICRED_MES_AQUIS TAXA_NEGOC_DICRED_MES_AQUIS_DESC_COMPRA TX_MIN TX_MEDIO
    TX_MAXIMO TAXA_NEGOC_DICRED_MES_AQUIS_DESC_VENDA TX_MIN TX_MEDIO TX_MAXIMO
    TAXA_NEGOC_DICRED_MES_AQUIS_JUROS_COMPRA TX_MIN TX_MEDIO TX_MAXIMO
    TAXA_NEGOC_DICRED_MES_AQUIS_JUROS_VENDA TX_MIN TX_MEDIO TX_MAXIMO
    TAXA_NEGOC_DICRED_MES_SEM_AQUIS TAXA_NEGOC_DICRED_MES_SEM_AQUIS_DESC_COMPRA TX_MIN
    TX_MEDIO TX_MAXIMO TAXA_NEGOC_DICRED_MES_SEM_AQUIS_DESC_VENDA TX_MIN TX_MEDIO TX_MAXIMO
    TAXA_NEGOC_DICRED_MES_SEM_AQUIS_JUROS_COMPRA TX_MIN TX_MEDIO TX_MAXIMO
    TAXA_NEGOC_DICRED_MES_SEM_AQUIS_JUROS_VENDA TX_MIN TX_MEDIO TX_MAXIMO
    TAXA_NEGOC_DICRED_MES_VALOR_MOBILI TAXA_NEGOC_DICRED_MES_VALOR_MOBILI_DESC_COMPRA TX_MIN
    TX_MEDIO TX_MAXIMO TAXA_NEGOC_DICRED_MES_VALOR_MOBILI_DESC_VENDA TX_MIN TX_MEDIO TX_MAXIMO
    TAXA_NEGOC_DICRED_MES_VALOR_MOBILI_JUROS_COMPRA TX_MIN TX_MEDIO TX_MAXIMO
    TAXA_NEGOC_DICRED_MES_VALOR_MOBILI_JUROS_VENDA TX_MIN TX_MEDIO TX_MAXIMO
    TAXA_NEGOC_DICRED_MES_TITPUB_FED TAXA_NEGOC_DICRED_MES_TITPUB_FED_DESC_COMPRA TX_MIN
    TX_MEDIO TX_MAXIMO TAXA_NEGOC_DICRED_MES_TITPUB_FED_DESC_VENDA TX_MIN TX_MEDIO TX_MAXIMO
    TAXA_NEGOC_DICRED_MES_TITPUB_FED_JUROS_COMPRA TX_MIN TX_MEDIO TX_MAXIMO
    TAXA_NEGOC_DICRED_MES_TITPUB_FED_JUROS_VENDA TX_MIN TX_MEDIO TX_MAXIMO
    TAXA_NEGOC_DICRED_MES_CDB TAXA_NEGOC_DICRED_MES_CDB_DESC_COMPRA TX_MIN TX_MEDIO TX_MAXIMO
    TAXA_NEGOC_DICRED_MES_CDB_DESC_VENDA TX_MIN TX_MEDIO TX_MAXIMO
    TAXA_NEGOC_DICRED_MES_CDB_JUROS_COMPRA TX_MIN TX_MEDIO TX_MAXIMO
    TAXA_NEGOC_DICRED_MES_CDB_JUROS_VENDA TX_MIN TX_MEDIO TX_MAXIMO
    TAXA_NEGOC_DICRED_MES_ATIV_RF TAXA_NEGOC_DICRED_MES_ATIV_RF_DESC_COMPRA TX_MIN TX_MEDIO
    TX_MAXIMO TAXA_NEGOC_DICRED_MES_ATIV_RF_DESC_VENDA TX_MIN TX_MEDIO TX_MAXIMO
    TAXA_NEGOC_DICRED_MES_ATIV_RF_JUROS_COMPRA TX_MIN TX_MEDIO TX_MAXIMO
    TAXA_NEGOC_DICRED_MES_ATIV_RF_JUROS_VENDA TX_MIN TX_MEDIO TX_MAXIMO OUTRAS_INFORM
    NUM_COTISTAS QT_TOTAL_COTISTAS QT_TOTAL_COTISTAS_SENIOR QT_TOTAL_COTISTAS_SUBORD
    QT_COTISTAS_SUBORD DESC_SERIE_CLASSE_SENIOR_SERIE QT_COTAS VL_COTAS
    DESC_SERIE_CLASSE_SUBORD QT_COTAS VL_COTAS RENT_MES PR_APURADA_SENIOR PR_APURADA_SUBORD
    CAPT_MES_SENIOR_SERIE QT_COTAS VL_COTAS CAPT_MES_SUBORD QT_COTAS VL_COTAS
    RESG_MES_SENIOR_SERIE QT_COTAS VL_COTAS RESG_MES_SUBORD QT_COTAS VL_COTAS
    RESG_SOLIC_SENIOR_SERIE QT_COTAS VL_COTAS RESG_SOLIC_SUBORD QT_COTAS VL_COTAS
    AMORT_SENIOR_SERIE VL_COTA VL_TOTAL AMORT_SUBORD VL_COTA VL_TOTAL LIQUIDEZ VL_ATIV_LIQDEZ
    VL_ATIV_LIQDEZ_30 VL_ATIV_LIQDEZ_60 VL_ATIV_LIQDEZ_90 VL_ATIV_LIQDEZ_180
    VL_ATIV_LIQDEZ_360 VL_ATIV_LIQDEZ_MAIS_360 DESEMP_SENIOR DESEMP_ESP DESEMP_REAL
    DESEMP_SUBORD DESEMP_ESP DESEMP_REAL
""".split()  # noqa: SIM905  # the page's 391 tags, kept as pasted

SPEC_OUTRAS_INFORM_ORDER = [
    "NUM_COTISTAS",
    "DESC_SERIE_CLASSE_SENIOR_SERIE",
    "DESC_SERIE_CLASSE_SUBORD",
    "RENT_MES",
    "CAPT_MES_SENIOR_SERIE",
    "CAPT_MES_SUBORD",
    "RESG_MES_SENIOR_SERIE",
    "RESG_MES_SUBORD",
    "RESG_SOLIC_SENIOR_SERIE",
    "RESG_SOLIC_SUBORD",
    "AMORT_SENIOR_SERIE",
    "AMORT_SUBORD",
    "LIQUIDEZ",
    "DESEMP_SENIOR",
    "DESEMP_SUBORD",
]

SPEC_APLIC_ATIVO_ORDER = [
    "VL_DISPONIB",
    "VL_CARTEIRA",
    "CRED_EXISTE",
    "DICRED",
    "LISTA_CEDENT",
    "VALORES_MOB",
    "VL_TITPUB_FED",
    "VL_CDB",
    "VL_APLIC_OPER_COMPSS",
    "VL_ATIV_FINANC_RF",
    "VL_COTA_FIDC",
    "VL_COTA_FIDC_NAO_PADRAO",
    "VL_CONTR_COMPRA_VENDA_PRESTC_FUTURA",
    "MERC_DERIVATIVO",
    "OUTROS_ATIVOS",
    "VL_SOM_APLIC_ATIVO",
]

SPEC_LISTA_INFORM_ORDER = [
    "APLIC_ATIVO",
    "CART_SEGMT",
    "PASSIV",
    "PATRLIQ",
    "COMPMT_DICRED_AQUIS",
    "COMPMT_DICRED_SEM_AQUIS",
    "NEGOC_DICRED_MES",
    "INFORM",
    "TAXA_NEGOC_DICRED_MES",
    "OUTRAS_INFORM",
]


def _first_non_none_value(annotation: Any, name: str) -> Any:  # noqa: ANN401
    """Build a value for the first non-None member of a union annotation."""
    return _value_for(next(a for a in get_args(annotation) if a is not type(None)), name)


_VALUE_RULES: list[tuple[Callable[[Any, str], bool], Callable[[Any, str], Any]]] = [
    (lambda a, n: get_origin(a) is list, lambda a, n: [_value_for(get_args(a)[0], n)]),
    (lambda a, n: get_origin(a) is Literal, lambda a, n: get_args(a)[0]),
    (lambda a, n: get_origin(a) in (Union, types.UnionType), _first_non_none_value),
    (lambda a, n: isinstance(a, type) and issubclass(a, BaseModel), lambda a, n: _zeros(a)),
    (lambda a, n: a is Decimal, lambda a, n: "0"),
    (lambda a, n: a is int, lambda a, n: 0),
    (lambda a, n: n == "dt_compt", lambda a, n: "10/2020"),
    (lambda a, n: True, lambda a, n: VALID_CNPJ),
]


def _value_for(annotation: Any, name: str) -> Any:  # noqa: ANN401
    """Build a zero/neutral value for a required field annotation."""
    build = next(build for test, build in _VALUE_RULES if test(annotation, name))
    return build(annotation, name)


def _zeros(model: type[BaseModel]) -> dict[str, Any]:
    """Build a fully-populated all-zero payload (every mandatory tag "preenchida com zero")."""
    return {
        name: _value_for(info.annotation, name)
        for name, info in model.model_fields.items()
        if info.is_required()
    }


def _keep(data: dict[str, Any]) -> None:
    """Leave the raw payload untouched."""


def _raw() -> dict[str, Any]:
    """Build the all-zero closed-fund payload."""
    data = _zeros(InfMensalFidc489Document)
    data["cab_inform"]["tp_condominio"] = "FECHADO"
    return data


def _doc(mutate: Callable[[dict[str, Any]], None] = _keep) -> InfMensalFidc489Document:
    """Build a closed-fund document from zeros, optionally mutating the raw payload first."""
    data = _raw()
    mutate(data)
    return InfMensalFidc489Document.model_validate(data)


def _xml(doc: InfMensalFidc489Document) -> str:
    """Export to a string."""
    out = InfMensalFidc489().export(doc)
    assert out is not None
    return out


def _full(data: dict[str, Any]) -> None:
    """Fill every optional block, so the output mirrors the page's whole template."""
    outras = data["lista_inform"]["outras_inform"]
    outras["num_cotistas"]["qt_cotistas_subord"] = [0]
    outras["desc_serie_classe_subord"] = [{"qt_cotas": "0", "vl_cotas": "0"}]
    outras["capt_mes_subord"] = {"qt_cotas": "0", "vl_cotas": "0"}
    outras["resg_mes_subord"] = {"qt_cotas": "0", "vl_cotas": "0"}
    outras["resg_solic_subord"] = {"qt_cotas": "0", "vl_cotas": "0"}
    outras["amort_subord"] = {"vl_cota": "0", "vl_total": "0"}
    outras["desemp_subord"] = {"desemp_esp": "0", "desemp_real": "0"}
    outras["liquidez"] = _LIQUIDEZ
    data["lista_inform"]["aplic_ativo"]["lista_cedent"] = {
        "cedent": [{"nr_pf_pj_cedent": VALID_CNPJ, "pr_cedent": "0"}]
    }


_LIQUIDEZ = {
    "vl_ativ_liqdez": "0",
    "vl_ativ_liqdez_30": "0",
    "vl_ativ_liqdez_60": "0",
    "vl_ativ_liqdez_90": "0",
    "vl_ativ_liqdez_180": "0",
    "vl_ativ_liqdez_360": "0",
    "vl_ativ_liqdez_mais_360": "0",
}


def _put(keys: tuple[str, ...], value: object, data: dict[str, Any]) -> None:
    """Set one nested key of the raw payload."""
    reduce(dict.__getitem__, keys[:-1], data)[keys[-1]] = value


def _set(*keys: str, value: object) -> Callable[[dict[str, Any]], None]:
    """Build a mutation that sets one nested key of the raw payload."""
    return partial(_put, keys, value)


def _open_fund_with_liquidity(data: dict[str, Any]) -> None:
    """Turn the fund into an open one that reports one liquidity bucket."""
    data["cab_inform"]["tp_condominio"] = "ABERTO"
    data["lista_inform"]["outras_inform"]["liquidez"] = {"vl_ativ_liqdez": "1.00"}


def _net_equity(data: dict[str, Any]) -> None:
    """Set a non-zero net equity with excess decimals."""
    data["lista_inform"]["patrliq"].update(vl_som_patrliq="100.99", vl_patrim_liq="100.999")


_AA = ("lista_inform", "aplic_ativo")
_OUT = ("lista_inform", "outras_inform")
_SACADOS = ("lista_inform", "inform", "lista_dev_sacados", "dev_sacados")


def _sacado(str_document: str) -> list[dict[str, str]]:
    """Build a one-debtor list with the given document."""
    return [
        {
            "nr_pf_pj_sacado_deved_1": str_document,
            "vl_sacado_deved_1": "0",
            "pr_sacado_deved_1": "0",
        }
    ]


@pytest.fixture
def xml_closed() -> str:
    """Return the minimal closed-fund XML."""
    return _xml(_doc())


def _children(str_xml: str, str_tag: str, int_indent: int) -> list[str]:
    """List the direct child tags of the first ``str_tag`` element at a given indent."""
    inner = str_xml.split(f"{' ' * (int_indent - 4)}<{str_tag}>")[1].split(f"</{str_tag}>")[0]
    return re.findall(rf"^ {{{int_indent}}}<(\w+)>", inner, flags=re.MULTILINE)


def test_export_minimal_document_starts_with_prolog_and_root(xml_closed: str) -> None:
    """The envelope follows the template of the page."""
    assert xml_closed.startswith(
        '<?xml version="1.0" encoding="windows-1252"?>\n<DOC_ARQ xmlns="urn:fidc">'
    )


def test_export_minimal_document_ends_with_root_close(xml_closed: str) -> None:
    """The envelope closes the root element."""
    assert xml_closed.endswith("</DOC_ARQ>")


def test_export_full_document_tag_sequence_equals_page_template() -> None:
    """With every optional block filled, the tags are exactly the page's, in its order."""
    assert ["DOC_ARQ", *re.findall(r"<(\w+)>", _xml(_doc(_full)))] == SPEC_TAGS


def test_export_header_has_the_six_tags_of_the_page(xml_closed: str) -> None:
    """CAB_INFORM has no redemption terms in this version."""
    assert re.findall(r"<(\w+)>", xml_closed.split("</CAB_INFORM>")[0]) == SPEC_TAGS[1:8]


def test_export_lista_inform_children_follow_template_order(xml_closed: str) -> None:
    """LISTA_INFORM children appear in the page's order, each exactly once."""
    assert _children(xml_closed, "LISTA_INFORM", 8) == SPEC_LISTA_INFORM_ORDER


def test_export_aplic_ativo_children_follow_template_order() -> None:
    """APLIC_ATIVO has no VL_PVS_* tags and no cedent list under CRED_EXISTE."""
    assert _children(_xml(_doc(_full)), "APLIC_ATIVO", 12) == SPEC_APLIC_ATIVO_ORDER


def test_export_outras_inform_children_follow_template_order() -> None:
    """OUTRAS_INFORM is the ICVM 489 table, in the page's order."""
    assert _children(_xml(_doc(_full)), "OUTRAS_INFORM", 12) == SPEC_OUTRAS_INFORM_ORDER


def test_export_closed_fund_omits_optional_blocks(xml_closed: str) -> None:
    """Absent optional blocks (cedents, subordinate class, liquidity) are not emitted."""
    assert (
        re.findall(
            r"<(LISTA_CEDENT|[A-Z]+_MES_SUBORD|AMORT_SUBORD|DESEMP_SUBORD|LIQUIDEZ)>", xml_closed
        )
        == []
    )


@pytest.mark.parametrize("tag", ["NUM_COTISTAS_DESC", "GARANTIA", "PR_ENTRE_RESGATE"])
def test_export_omits_tags_that_only_exist_in_icvm_576(xml_closed: str, tag: str) -> None:
    """Blocks added by the later layout are not part of this page."""
    assert tag not in xml_closed


@pytest.mark.parametrize(
    ("mutate", "fragment"),
    [
        (
            _set(
                *_OUT,
                "desc_serie_classe_senior_serie",
                value=[{"qt_cotas": "1234.123456789", "vl_cotas": "1.5"}],
            ),
            "<QT_COTAS>1234,12345678</QT_COTAS>",
        ),
        (
            _set(
                *_OUT,
                "desc_serie_classe_senior_serie",
                value=[{"qt_cotas": "1234.123456789", "vl_cotas": "1.5"}],
            ),
            "<VL_COTAS>1,50000000</VL_COTAS>",
        ),
        (
            _set(
                *_OUT,
                "capt_mes_senior_serie",
                value={"qt_cotas": "2.123456789", "vl_cotas": "10.999"},
            ),
            "<VL_COTAS>10,99</VL_COTAS>",
        ),
        (
            _set(
                *_OUT, "amort_senior_serie", value={"vl_cota": "0.123456789", "vl_total": "7.999"}
            ),
            "<VL_COTA>0,12345678</VL_COTA>",
        ),
        (
            _set(
                *_OUT, "amort_senior_serie", value={"vl_cota": "0.123456789", "vl_total": "7.999"}
            ),
            "<VL_TOTAL>7,99</VL_TOTAL>",
        ),
        (
            _set(*_OUT, "rent_mes", "pr_apurada_senior", value="9.0"),
            "<PR_APURADA_SENIOR>9,00</PR_APURADA_SENIOR>",
        ),
        (_set(*_AA, "vl_disponib", value="0"), "<VL_DISPONIB>0,00</VL_DISPONIB>"),
    ],
)
def test_export_decimals_use_comma_and_spec_scales(
    mutate: Callable[[dict[str, Any]], None], fragment: str
) -> None:
    """2 casas for money/percent, up to 8 for quota quantities and unit values; truncated."""
    assert fragment in _xml(_doc(mutate))


def test_export_repeats_one_block_per_senior_series() -> None:
    """DESC_SERIE_CLASSE_SENIOR_SERIE is separated by class and series."""
    mutate = _set(
        *_OUT,
        "desc_serie_classe_senior_serie",
        value=[{"qt_cotas": "1", "vl_cotas": "1"}, {"qt_cotas": "2", "vl_cotas": "2"}],
    )
    assert _xml(_doc(mutate)).count("<DESC_SERIE_CLASSE_SENIOR_SERIE>") == 2


def test_export_repeats_subordinate_holders_per_item_31() -> None:
    """QT_COTISTAS_SUBORD is the 'Subordinada 1..n' of item 31."""
    num = {
        "qt_total_cotistas": 5,
        "qt_total_cotistas_senior": 0,
        "qt_total_cotistas_subord": 5,
        "qt_cotistas_subord": [2, 3],
    }
    assert _xml(_doc(_set(*_OUT, "num_cotistas", value=num))).count("<QT_COTISTAS_SUBORD>") == 2


def test_export_open_fund_emits_liquidity() -> None:
    """An open fund fills at least one LIQUIDEZ field."""
    assert "<VL_ATIV_LIQDEZ>1,00</VL_ATIV_LIQDEZ>" in _xml(_doc(_open_fund_with_liquidity))


def test_export_mapping_equals_model() -> None:
    """A mapping validates into the same bytes as the model."""
    assert InfMensalFidc489().export(deepcopy(_raw())) == _xml(_doc())


def test_export_to_file_returns_none(tmp_path: Path) -> None:
    """With an output path the writer returns None."""
    assert InfMensalFidc489().export(_doc(), str(tmp_path / "out.xml")) is None


def test_export_to_file_writes_windows_1252(tmp_path: Path) -> None:
    """The file is windows-1252 and byte-identical to the string output."""
    path_out = tmp_path / "out.xml"
    InfMensalFidc489().export(_doc(), str(path_out))
    assert path_out.read_bytes() == _xml(_doc()).encode("windows-1252")


def test_net_equity_is_truncated_to_two_places() -> None:
    """Item 16: a non-zero net equity is truncated, never rounded, to two places."""
    assert _doc(_net_equity).lista_inform.patrliq.vl_patrim_liq == Decimal("100.99")


def test_sacado_with_placeholder_document_is_accepted() -> None:
    """Debtors without CNPJ use the page's placeholder."""
    mutate = _set(*_SACADOS, value=_sacado("99.999.999/9999-99"))
    assert _doc(mutate).lista_inform.inform.lista_dev_sacados.dev_sacados[0].vl_sacado_deved_1 == 0


@pytest.mark.parametrize(
    "mutate",
    [
        _set("cab_inform", "nr_cnpj_fundo", value="11222333000180"),
        _set("cab_inform", "nr_cnpj_adm", value="123"),
        _set("cab_inform", "dt_compt", value="2020/10"),
        _set("cab_inform", "dt_compt", value="13/2020"),
        _set("cab_inform", "tp_condominio", value="MISTO"),
        _set("cab_inform", "fdo_excl", value="TALVEZ"),
        _set("cab_inform", "pr_entre_resgate", value=30),
        _set(*_SACADOS, value=_sacado("12345678901")),
        _set(*_SACADOS, value=[]),
        _set(*_AA, "cred_existe", "vl_provis_reduc_recup", value="5.00"),
        _set(*_AA, "vl_carteira", value="1.00"),
        _set(*_AA, "vl_som_aplic_ativo", value="1.00"),
        _set(*_AA, "valores_mob", "vl_som_valores_mob", value="1.00"),
        _set(*_AA, "vl_pvs_otr_atv", value="1.00"),
        _set("lista_inform", "passiv", "vl_som_passiv", value="1.00"),
        _set("lista_inform", "patrliq", "vl_som_patrliq", value="1.00"),
        _set("lista_inform", "compmt_dicred_aquis", "vl_som_prazo_venc", value="1.00"),
        _set("lista_inform", "negoc_dicred_mes", "aquisicoes", "vl_dicred_aquis", value="1.00"),
        _set(*_OUT, "num_cotistas", "qt_total_cotistas", value=1),
        _set(*_OUT, "num_cotistas", "qt_total_cotistas_subord", value=1),
        _set(*_OUT, "num_cotistas", "qt_total_cotistas_senior", value=-1),
        _set(*_OUT, "desc_serie_classe_senior_serie", value=[]),
        _set(*_OUT, "desemp_senior", value=None),
        _set(*_OUT, "capt_mes_senior_serie", "vl_cotas", value="abc"),
        _set(*_OUT, "garantia", value={"vlr_gnt_vnc_drt_crd": "0", "prc_drt_cred_gnt_vnc": "0"}),
        _set("cab_inform", "tp_condominio", value="ABERTO"),
    ],
)
def test_invalid_input_is_rejected(mutate: Callable[[dict[str, Any]], None]) -> None:
    """Each rule of the page (or tag outside it) makes validation fail."""
    with pytest.raises(ValidationError):
        _doc(mutate)


_MERC = (*_AA, "merc_derivativo")


def _item_1_with_margin(data: dict[str, Any]) -> None:
    """Item 1 as the page lists it: disponibilidades + margin deposits as separate terms."""
    _put((*_AA, "vl_disponib"), "1.00", data)
    _put((*_MERC, "vl_depos_margem"), "2.00", data)
    _put((*_AA, "vl_som_aplic_ativo"), "3.00", data)


def test_item_1_counts_the_margin_deposit_as_its_own_term() -> None:
    """The page's item 1 adds 'Valor de Depositos de Margem' beside the derivatives sum."""
    assert _doc(_item_1_with_margin).lista_inform.aplic_ativo.vl_som_aplic_ativo == Decimal("3")


def _item_1_total_omits_margin(data: dict[str, Any]) -> None:
    """Item 1 with a margin deposit but a total that leaves it out."""
    _item_1_with_margin(data)
    _put((*_AA, "vl_som_aplic_ativo"), "1.00", data)


def test_item_1_without_the_margin_term_is_rejected() -> None:
    """Dropping the margin deposit from the item 1 total no longer balances."""
    with pytest.raises(ValidationError, match="item 1"):
        _doc(_item_1_total_omits_margin)


def test_negative_monthly_return_is_accepted() -> None:
    """A loss month reports a negative RENT_MES; the page sets no lower bound."""
    mutate = _set(*_OUT, "rent_mes", "pr_apurada_senior", value="-1.50")
    assert _doc(mutate).lista_inform.outras_inform.rent_mes.pr_apurada_senior == Decimal("-1.5")


def _default_without_credits(data: dict[str, Any]) -> None:
    """Report a default total no existing credit backs."""
    block = data["lista_inform"]["compmt_dicred_aquis"]
    block.update(vl_som_inad_venc="1.00", vl_inad_venc_30="1.00")


@pytest.mark.parametrize(
    ("mutate", "match"),
    [
        (_default_without_credits, "VL_SOM_INAD_VENC vs portfolio"),
        (_set(*_OUT, "num_cotistas", "qt_total_cotistas", value=1), "item 30"),
        (_set(*_OUT, "num_cotistas", "qt_cotistas_subord", value=[1]), "item 31"),
    ],
)
def test_invalid_input_names_the_rule_that_fired(
    mutate: Callable[[dict[str, Any]], None], match: str
) -> None:
    """The error message names the page rule, not just any validation failure."""
    with pytest.raises(ValidationError, match=match):
        _doc(mutate)


def test_cpf_placeholder_is_accepted() -> None:
    """The page's CPF placeholder is a valid debtor document."""
    mutate = _set(*_SACADOS, value=_sacado("999.999.999-99"))
    assert _doc(mutate).lista_inform.inform.lista_dev_sacados.dev_sacados[0].vl_sacado_deved_1 == 0


def test_fidc_writers_are_siblings_over_the_private_base() -> None:
    """Neither FIDC writer subclasses the other; both subclass the shared base."""
    from layouts_cvm import InfMensalFidc, InfMensalFidc489
    from layouts_cvm._base_fidc_writer import _BaseFidcWriter

    assert (
        issubclass(InfMensalFidc489, InfMensalFidc),
        issubclass(InfMensalFidc, InfMensalFidc489),
        issubclass(InfMensalFidc, _BaseFidcWriter),
        issubclass(InfMensalFidc489, _BaseFidcWriter),
    ) == (False, False, True, True)


def test_fidc_base_subclass_without_a_document_model_fails_at_definition() -> None:
    """A writer that does not parametrize the base fails when the class is defined."""
    from layouts_cvm._base_fidc_writer import _BaseFidcWriter

    with pytest.raises(TypeError, match="must parametrize _BaseFidcWriter with a DocModel"):
        type("_Unparametrized", (_BaseFidcWriter,), {})


def test_fidc_576_writer_rejects_a_489_document() -> None:
    """A built 489 document handed to the ICVM 576 writer raises the TypeError main raised."""
    from layouts_cvm import InfMensalFidc

    with pytest.raises(TypeError, match="expected InfMensalFidcDocument, got InfMensalFidc489"):
        InfMensalFidc().export(_doc())


def test_fidc_writer_subclass_without_generic_inherits_the_document_model() -> None:
    """Subclassing a concrete writer without a generic argument keeps the parent's model."""
    from layouts_cvm import InfMensalFidc
    from layouts_cvm._internal.config.schemas.inf_mensal_fidc import InfMensalFidcDocument

    cls_writer = type("_Custom", (InfMensalFidc,), {})

    assert cls_writer._document_model is InfMensalFidcDocument
