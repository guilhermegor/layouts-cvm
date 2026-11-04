"""Unit tests for the Informe Semestral INR Part II submission writer.

Expectations come from the CVM page PadraoXMLInfoSemestralINRParte2.aspx (tag names and order,
comma decimals and scales, cardinalities, Tables A, B, D, G and H), not from the writer. The
expected child lists are the page's XML template, extracted from the fetched page.
"""
# ruff: noqa: S314  (parses the writer's own output, not untrusted input)

import copy
from pathlib import Path
from xml.etree import ElementTree as ET  # noqa: S405

from pydantic import ValidationError
import pytest

from layouts_cvm import InformeSemestralInrParte2
from layouts_cvm._internal.config.schemas.informe_semestral_inr_parte2 import (
    InformeSemestralInrParte2Document,
)


VALID_CNPJ = "11222333000181"
ZERO_PADDED_CNPJ = "00000000000191"
VALID_CPF = "52998224725"
PARTIC = "12345.123456.654321.1-9"
NS = {"c": "urn:cda"}
POS_QTY = ["QTDE_POS_FIM", "MERC_POS_FIM"]
POS_NOCION = ["QTDE_POS_FIM", "MERC_POS_FIM", "NOCION_POS_FIM"]
RATING = ["AG_CLASSIF_RISCO", "DT_CLASSIF_RISCO", "GRAU_CLASSIF_RISCO"]
POS_FIX = ["TIT_POS_FIX_COD_INDEX", "TIT_POS_FIX_PR_INDEX", "TIT_POS_FIX_CUPOM"]
LISTA_ATIV_ORDER = [
    "TIT_PUB",
    "COTAS",
    "SWAP",
    "NOCION_SWAP",
    "DEMAIS_CODIF",
    "DEP_PRAZO_TIT_IF",
    "TIT_AGRO_CRED_PRIV",
    "INV_EXT",
    "DEMAIS_N_CODIF",
]
ORDER_BY_PATH = [
    ("c:CAB_INFORM", ["COD_DOC", "VERSAO", "DT_COMPT", "DT_GERAC_ARQ"]),
    (".//c:INFORM", ["COD_PARTIC", "LISTA_ATIV"]),
    (".//c:LISTA_ATIV", LISTA_ATIV_ORDER),
    (".//c:TIT_PUB", ["COD_SELIC", "DT_VENC", "APLIC"]),
    (".//c:TIT_PUB/c:APLIC", ["COD_TP_APLIC", "POS_FIM"]),
    (".//c:TIT_PUB/c:APLIC/c:POS_FIM", POS_QTY),
    (".//c:COTAS", ["CNPJ_FDO", "APLIC"]),
    (".//c:COTAS/c:APLIC", ["POS_FIM"]),
    (".//c:COTAS/c:APLIC/c:POS_FIM", POS_QTY),
    (".//c:SWAP", ["COD_SWAP", "APLIC"]),
    (".//c:SWAP/c:APLIC", ["COD_TP_APLIC", "POS_FIM"]),
    (".//c:SWAP/c:APLIC/c:POS_FIM", ["MERC_POS_FIM"]),
    (".//c:DEMAIS_CODIF", ["COD_ATIV", "COD_TP_ATIV", "DT_INI_VIGEN", "APLIC"]),
    (".//c:DEMAIS_CODIF/c:APLIC", ["COD_TP_APLIC", "POS_FIM"]),
    (".//c:DEMAIS_CODIF/c:APLIC/c:POS_FIM", POS_NOCION),
    (
        ".//c:DEP_PRAZO_TIT_IF",
        [
            "COD_TP_ATIV",
            "EMIS",
            "DT_VENC",
            "ST_TIT_POS_FIX",
            "TIT_POS_FIX_INDEX",
            "ST_CLASSIF_RISCO",
            "CLASSIF_RISCO",
            "APLIC",
        ],
    ),
    (".//c:DEP_PRAZO_TIT_IF/c:EMIS", ["CNPJ_EMIS", "NM_EMIS"]),
    (".//c:DEP_PRAZO_TIT_IF/c:TIT_POS_FIX_INDEX", POS_FIX),
    (".//c:DEP_PRAZO_TIT_IF/c:CLASSIF_RISCO", RATING),
    (".//c:DEP_PRAZO_TIT_IF/c:APLIC", ["POS_FIM"]),
    (".//c:DEP_PRAZO_TIT_IF/c:APLIC/c:POS_FIM", POS_QTY),
    (
        ".//c:TIT_AGRO_CRED_PRIV",
        [
            "COD_TP_ATIV",
            "EMIS",
            "DT_VENC",
            "ST_TIT_POS_FIX",
            "TIT_PRE_FIX_TAXA_CONTR",
            "ST_TIT_REG_CETIP",
            "ST_TIT_GARANT_SEGURO",
            "CNPJ_INSTIT_FINANC",
            "APLIC",
        ],
    ),
    (".//c:TIT_AGRO_CRED_PRIV/c:EMIS", ["TP_PF_PJ_EMIS", "NR_PF_PJ_EMIS", "NM_EMIS"]),
    (".//c:TIT_AGRO_CRED_PRIV/c:APLIC", ["COD_TP_APLIC", "POS_FIM"]),
    (
        ".//c:INV_EXT",
        [
            "COD_TP_ATIV",
            "INV_COLETIVO",
            "GEST_INV_COLETIVO",
            "NM_EMIS",
            "DT_VENC",
            "COD_PAIS",
            "COD_BV_MERC",
            "COD_ATIVO_BV_MERC",
            "ST_CLASSIF_RISCO",
            "CLASSIF_RISCO",
            "APLIC",
        ],
    ),
    (".//c:INV_EXT/c:CLASSIF_RISCO", RATING),
    (".//c:INV_EXT/c:APLIC", ["DT_APLIC", "POS_FIM", "ATIVO_EXT"]),
    (".//c:INV_EXT/c:APLIC/c:ATIVO_EXT", ["DESC_AT_EXT", "QTDE_AT_EXT", "VALOR_AT_EXT"]),
    (".//c:DEMAIS_N_CODIF", ["COD_TP_ATIV", "DESC", "EMIS", "APLIC"]),
    (".//c:DEMAIS_N_CODIF/c:EMIS", ["TP_PF_PJ_EMIS", "NR_PF_PJ_EMIS", "NM_EMIS"]),
    (".//c:DEMAIS_N_CODIF/c:APLIC", ["COD_TP_APLIC", "POS_FIM"]),
    (".//c:DEMAIS_N_CODIF/c:APLIC/c:POS_FIM", ["MERC_POS_FIM", "NOCION_POS_FIM"]),
]
TEXT_BY_PATH = [
    (".//c:TIT_PUB//c:QTDE_POS_FIM", "10,000000"),
    (".//c:TIT_PUB//c:MERC_POS_FIM", "1000,50"),
    (".//c:SWAP//c:MERC_POS_FIM", "5,00"),
    (".//c:NOCION_SWAP", "100,00"),
    (".//c:DEMAIS_CODIF//c:NOCION_POS_FIM", "3,00"),
    (".//c:DEP_PRAZO_TIT_IF//c:TIT_POS_FIX_PR_INDEX", "102,000000"),
    (".//c:DEP_PRAZO_TIT_IF//c:TIT_POS_FIX_CUPOM", "3,000000"),
    (".//c:TIT_AGRO_CRED_PRIV/c:TIT_PRE_FIX_TAXA_CONTR", "15,000000"),
    (".//c:INV_EXT//c:VALOR_AT_EXT", "1,5"),
    (".//c:INV_EXT//c:QTDE_AT_EXT", "3"),
    (".//c:COTAS/c:CNPJ_FDO", "191"),
    (".//c:TIT_AGRO_CRED_PRIV/c:CNPJ_INSTIT_FINANC", VALID_CNPJ),
    (".//c:TIT_AGRO_CRED_PRIV//c:NR_PF_PJ_EMIS", VALID_CPF),
]


def _pos(qtde: str = "1", merc: str = "2") -> dict:
    """Build a POS_FIM mapping with quantity and market value."""
    return {"qtde_pos_fim": qtde, "merc_pos_fim": merc}


def _rating() -> dict:
    """Build a CLASSIF_RISCO mapping."""
    return {
        "ag_classif_risco": "Agency",
        "dt_classif_risco": "01/03/2026",
        "grau_classif_risco": "AAA",
    }


def _pos_fix_index() -> dict:
    """Build a TIT_POS_FIX_INDEX mapping."""
    return {
        "tit_pos_fix_cod_index": "DI1",
        "tit_pos_fix_pr_index": "102",
        "tit_pos_fix_cupom": "3",
    }


def _tit_pub() -> dict:
    """Build a TIT_PUB mapping."""
    return {
        "cod_selic": "100000",
        "dt_venc": "01/01/2030",
        "aplic": {"cod_tp_aplic": 75, "pos_fim": _pos("10", "1000.5")},
    }


def _swap() -> dict:
    """Build a SWAP mapping."""
    return {
        "cod_swap": "SWPSAB",
        "aplic": {"cod_tp_aplic": 183, "pos_fim": {"merc_pos_fim": "5"}},
    }


def _demais_codif() -> dict:
    """Build a DEMAIS_CODIF mapping (options, so the notional is required)."""
    return {
        "cod_ativ": "X1",
        "cod_tp_ativ": 3,
        "dt_ini_vigen": "01/01/2026",
        "aplic": {"cod_tp_aplic": 39, "pos_fim": {**_pos(), "nocion_pos_fim": "3"}},
    }


def _dep_prazo() -> dict:
    """Build a post-fixed, rated DEP_PRAZO_TIT_IF mapping."""
    return {
        "cod_tp_ativ": 51,
        "emis": {"cnpj_emis": VALID_CNPJ, "nm_emis": "Banco"},
        "dt_venc": "01/01/2030",
        "st_tit_pos_fix": "S",
        "tit_pos_fix_index": _pos_fix_index(),
        "st_classif_risco": "S",
        "classif_risco": _rating(),
        "aplic": {"pos_fim": _pos()},
    }


def _agro() -> dict:
    """Build a pre-fixed TIT_AGRO_CRED_PRIV mapping."""
    return {
        "cod_tp_ativ": 6,
        "emis": {"tp_pf_pj_emis": "PF", "nr_pf_pj_emis": VALID_CPF, "nm_emis": "Ana"},
        "dt_venc": "01/01/2030",
        "st_tit_pos_fix": "N",
        "tit_pre_fix_taxa_contr": "15",
        "st_tit_reg_cetip": "S",
        "st_tit_garant_seguro": "N",
        "cnpj_instit_financ": VALID_CNPJ,
        "aplic": {"cod_tp_aplic": 193, "pos_fim": _pos()},
    }


def _inv_ext() -> dict:
    """Build a rated INV_EXT mapping."""
    return {
        "cod_tp_ativ": 1,
        "inv_coletivo": "N",
        "gest_inv_coletivo": "N",
        "nm_emis": "Acme",
        "dt_venc": "01/01/2031",
        "cod_pais": 28,
        "cod_bv_merc": "A11",
        "cod_ativo_bv_merc": "ACME",
        "st_classif_risco": "S",
        "classif_risco": _rating(),
        "aplic": {
            "dt_aplic": "01/02/2026",
            "pos_fim": _pos(),
            "ativo_ext": {"desc_at_ext": "d", "qtde_at_ext": 3, "valor_at_ext": "1.5"},
        },
    }


def _n_codif() -> dict:
    """Build a DEMAIS_N_CODIF mapping (type 191: no quantity, notional required)."""
    return {
        "cod_tp_ativ": 999,
        "desc": "Outros",
        "emis": {"tp_pf_pj_emis": "PJ", "nr_pf_pj_emis": VALID_CNPJ, "nm_emis": "Acme"},
        "aplic": {
            "cod_tp_aplic": 191,
            "pos_fim": {"merc_pos_fim": "2", "nocion_pos_fim": "3"},
        },
    }


def _full_lista_ativ() -> dict:
    """Build a LISTA_ATIV mapping holding one of every block."""
    return {
        "tit_pub": [_tit_pub()],
        "cotas": [{"cnpj_fdo": ZERO_PADDED_CNPJ, "aplic": {"pos_fim": _pos()}}],
        "swap": [_swap()],
        "nocion_swap": "100",
        "demais_codif": [_demais_codif()],
        "dep_prazo_tit_if": [_dep_prazo()],
        "tit_agro_cred_priv": [_agro()],
        "inv_ext": [_inv_ext()],
        "demais_n_codif": [_n_codif()],
    }


def _doc(lista_ativ: dict, n_informs: int = 1) -> dict:
    """Build a document mapping repeating ``lista_ativ`` in ``n_informs`` participants."""
    inform = {"cod_partic": PARTIC, "lista_ativ": lista_ativ}
    return {
        "cab_inform": {"dt_compt": "06/2026", "dt_gerac_arq": "05/07/2026"},
        "lista_inform": {"inform": [copy.deepcopy(inform) for _ in range(n_informs)]},
    }


def _lista(doc: dict) -> dict:
    """Return the first participant's LISTA_ATIV of ``doc``."""
    return doc["lista_inform"]["inform"][0]["lista_ativ"]


def _block(doc: dict, name: str) -> dict:
    """Return the first block called ``name`` of the first participant."""
    return _lista(doc)[name][0]


def _parse(doc: dict) -> ET.Element:
    """Export ``doc`` and parse the XML back."""
    return ET.fromstring(InformeSemestralInrParte2().export(doc).split("\n", 1)[1])


def _names(node: ET.Element) -> list[str]:
    """List the local tag names of a node's children."""
    return [child.tag.split("}")[1] for child in node]


@pytest.fixture(scope="module")  # fixture-scope-ok: immutable text, rebuilt per test otherwise
def xml() -> str:
    """Render a document holding every block once."""
    return InformeSemestralInrParte2().export(_doc(_full_lista_ativ()))


@pytest.fixture
def root(xml: str) -> ET.Element:
    """Parse the shared document once."""
    return ET.fromstring(xml.split("\n", 1)[1])


def test_export_starts_with_windows_1252_declaration(xml: str) -> None:
    """Declare windows-1252, as the page's template does."""
    assert xml.startswith('<?xml version="1.0" encoding="windows-1252"?>')


def test_export_root_is_doc_arq_in_urn_cda_namespace(root: ET.Element) -> None:
    """Use the urn:cda namespace the page declares on DOC_ARQ."""
    assert root.tag == "{urn:cda}DOC_ARQ"


def test_header_stamps_part_ii_values(root: ET.Element) -> None:
    """Stamp COD_DOC 70, VERSAO 1.0 and both dates."""
    head = root.find("c:CAB_INFORM", NS)
    assert [e.text for e in head] == ["70", "1.0", "06/2026", "05/07/2026"]


@pytest.mark.parametrize(("path", "expected"), ORDER_BY_PATH)
def test_children_follow_page_order(root: ET.Element, path: str, expected: list[str]) -> None:
    """Emit each element's children in the order of the page's XML template."""
    assert _names(root.find(path, NS)) == expected


@pytest.mark.parametrize(("path", "expected"), TEXT_BY_PATH)
def test_leaf_text_follows_page_scale(root: ET.Element, path: str, expected: str) -> None:
    """Write the page's scale with a comma separator and no zero filler on identifiers."""
    assert root.find(path, NS).text == expected


def test_export_truncates_excess_decimals_never_rounds() -> None:
    """Drop excess decimals toward zero instead of rounding up."""
    tit_pub = _tit_pub()
    tit_pub["aplic"]["pos_fim"] = _pos("1.9999999", "2.999")
    pos = _parse(_doc({"tit_pub": [tit_pub]})).find(".//c:TIT_PUB//c:POS_FIM", NS)
    assert [n.text for n in pos] == ["1,999999", "2,99"]


def test_export_repeats_blocks_grouped_in_page_order() -> None:
    """Repeat a block and keep NOCION_SWAP right after the SWAP blocks."""
    lista = {
        "demais_n_codif": [_n_codif(), _n_codif()],
        "swap": [_swap()],
        "nocion_swap": "1",
        "tit_pub": [_tit_pub(), _tit_pub()],
    }
    names = _names(_parse(_doc(lista)).find(".//c:LISTA_ATIV", NS))
    assert names == [
        "TIT_PUB",
        "TIT_PUB",
        "SWAP",
        "NOCION_SWAP",
        "DEMAIS_N_CODIF",
        "DEMAIS_N_CODIF",
    ]


def test_export_mapping_and_model_give_identical_bytes() -> None:
    """Serialize a mapping and its validated model to the same text."""
    model = InformeSemestralInrParte2Document.model_validate(_doc(_full_lista_ativ()))
    assert InformeSemestralInrParte2().export(model) == InformeSemestralInrParte2().export(
        _doc(_full_lista_ativ())
    )


def test_export_to_path_returns_none(tmp_path: Path) -> None:
    """Return None once the file is written."""
    path = tmp_path / "parte2.xml"
    assert InformeSemestralInrParte2().export(_doc(_full_lista_ativ()), str(path)) is None


def test_export_to_path_writes_windows_1252(tmp_path: Path) -> None:
    """Encode accented text as windows-1252 bytes."""
    lista = {"demais_n_codif": [{**_n_codif(), "desc": "Ação"}]}
    path = tmp_path / "parte2.xml"
    InformeSemestralInrParte2().export(_doc(lista), str(path))
    assert "Ação".encode("windows-1252") in path.read_bytes()


def test_document_accepts_1000_informs() -> None:
    """Accept the page's maximum of 1000 INFORM per file."""
    assert len(_parse(_doc({}, 1000)).findall(".//c:INFORM", NS)) == 1000


@pytest.mark.parametrize("count", [0, 1001])
def test_document_rejects_informs_out_of_bounds(count: int) -> None:
    """Reject an empty file and one above 1000 INFORM."""
    with pytest.raises(ValidationError):
        InformeSemestralInrParte2().export(_doc({}, count))


REJECTED = {
    "wrong_cod_doc": lambda d: d["cab_inform"].update(cod_doc=69),
    "wrong_versao": lambda d: d["cab_inform"].update(versao="2.0"),
    "bad_competence": lambda d: d["cab_inform"].update(dt_compt="13/2026"),
    "bad_generation_date": lambda d: d["cab_inform"].update(dt_gerac_arq="31/02/2026"),
    "bad_participant": lambda d: d["lista_inform"]["inform"][0].update(cod_partic="1.2.3"),
    "type_not_in_block": lambda d: _block(d, "tit_pub")["aplic"].update(cod_tp_aplic=197),
    "table_b_mismatch": lambda d: _block(d, "demais_codif").update(cod_tp_ativ=1),
    "missing_quantity": lambda d: _block(d, "tit_pub")["aplic"]["pos_fim"].pop("qtde_pos_fim"),
    "quantity_forbidden": lambda d: _block(d, "demais_n_codif")["aplic"]["pos_fim"].update(
        qtde_pos_fim="1"
    ),
    "notional_missing": lambda d: _block(d, "demais_codif")["aplic"]["pos_fim"].pop(
        "nocion_pos_fim"
    ),
    "notional_forbidden": lambda d: _block(d, "demais_codif")["aplic"].update(cod_tp_aplic=37),
    "swap_without_notional": lambda d: _lista(d).pop("nocion_swap"),
    "notional_without_swap": lambda d: _lista(d).update(swap=[]),
    "swap_type": lambda d: _block(d, "swap")["aplic"].update(cod_tp_aplic=75),
    "swap_code": lambda d: _block(d, "swap").update(cod_swap="SAB"),
    "swap_code_non_ascii": lambda d: _block(d, "swap").update(cod_swap="SWPÁÉÍ"),
    "market_integer_digits": lambda d: _block(d, "tit_pub")["aplic"]["pos_fim"].update(
        merc_pos_fim="1" * 16
    ),
    "quantity_integer_digits": lambda d: _block(d, "tit_pub")["aplic"]["pos_fim"].update(
        qtde_pos_fim="1" * 16
    ),
    "bad_cnpj": lambda d: _block(d, "cotas").update(cnpj_fdo="11222333000182"),
    "bad_cpf": lambda d: _block(d, "tit_agro_cred_priv")["emis"].update(
        nr_pf_pj_emis="11111111111"
    ),
    "pos_fixed_without_index": lambda d: _block(d, "dep_prazo_tit_if").pop("tit_pos_fix_index"),
    "pre_fixed_without_rate": lambda d: _block(d, "tit_agro_cred_priv").pop(
        "tit_pre_fix_taxa_contr"
    ),
    "pre_fixed_with_index": lambda d: _block(d, "tit_agro_cred_priv").update(
        tit_pos_fix_index=_pos_fix_index()
    ),
    "indexer_not_in_table_d": lambda d: _block(d, "dep_prazo_tit_if")["tit_pos_fix_index"].update(
        tit_pos_fix_cod_index="XXX"
    ),
    "rating_flag_without_block": lambda d: _block(d, "dep_prazo_tit_if").pop("classif_risco"),
    "rating_block_without_flag": lambda d: _block(d, "inv_ext").update(st_classif_risco="N"),
    "country_not_in_table_g": lambda d: _block(d, "inv_ext").update(cod_pais=4),
    "exchange_not_in_table_h": lambda d: _block(d, "inv_ext").update(cod_bv_merc="ZZ"),
    "invalid_yes_no": lambda d: _block(d, "inv_ext").update(inv_coletivo="X"),
    "ext_description_too_long": lambda d: _block(d, "inv_ext")["aplic"]["ativo_ext"].update(
        desc_at_ext="x" * 51
    ),
    "description_too_long": lambda d: _block(d, "demais_n_codif").update(desc="x" * 1001),
    "grade_too_long": lambda d: _block(d, "inv_ext")["classif_risco"].update(
        grau_classif_risco="AAAAAAA"
    ),
    "float_value": lambda d: _block(d, "tit_pub")["aplic"]["pos_fim"].update(merc_pos_fim=1.5),
    "unrepresentable_text": lambda d: _block(d, "demais_n_codif").update(desc="漢字"),
}


@pytest.mark.parametrize("name", sorted(REJECTED))
def test_export_rejects_invalid_input(name: str) -> None:
    """Reject each input that breaks a rule the page states."""
    doc = _doc(_full_lista_ativ())
    REJECTED[name](doc)
    with pytest.raises(ValidationError):
        InformeSemestralInrParte2().export(doc)
