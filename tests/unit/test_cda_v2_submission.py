"""Unit tests for the CDA V2 submission writer.

Expectations come from the CVM page PadraoXMLCDANet.aspx (tag names and order, comma
decimals, cardinalities, Table A), not from the writer. The expected child lists are the page's
XML template, extracted from the fetched page.
"""
# ruff: noqa: S314  (parses the writer's own output, not untrusted input)

from pathlib import Path
from xml.etree import ElementTree as ET  # noqa: S405

from pydantic import ValidationError
import pytest

from layouts_cvm import CdaV2
from layouts_cvm._internal.config.schemas.cda import CdaEmitter, CdaNegoc
from layouts_cvm._internal.config.schemas.cda_v2 import (
    CdaV2Aplic,
    CdaV2Cotas,
    CdaV2DemaisCodif,
    CdaV2DemaisNCodif,
    CdaV2Document,
    CdaV2Header,
    CdaV2Inform,
    CdaV2PosFim,
    CdaV2Swap,
    CdaV2SwapAplic,
    CdaV2SwapNegoc,
    CdaV2SwapPosFim,
    CdaV2TitPub,
)


VALID_CNPJ = "11222333000181"
NS = {"c": "urn:cda"}
APLIC_CHILDREN = ["COD_TP_APLIC", "QTDE_DIAS_CONFID", "NEGOC", "POS_FIM"]
NEGOC_CHILDREN = [
    "TP_NEGOC",
    "QTDE_VENDAS_NEGOC",
    "VL_VENDAS_NEGOC",
    "QTDE_AQUIS_NEGOC",
    "VL_AQUIS_NEGOC",
]
POS_FIM_CHILDREN = ["QTDE_POS_FIM", "CUSTO_CORREC_POS_FIM", "MERC_POS_FIM"]
ORDER_BY_PATH = [
    ("c:CAB_INFORM", ["COD_DOC", "VERSAO", "DT_COMPT", "DT_GERAC_ARQ"]),
    (".//c:INFORM", ["CNPJ_FDO", "VL_PL", "LISTA_ATIV"]),
    (
        ".//c:LISTA_ATIV",
        ["TIT_PUB", "COTAS", "SWAP", "DEMAIS_CODIF", "DEMAIS_N_CODIF"],
    ),
    (".//c:TIT_PUB", ["COD_SELIC", "DT_VENC", "APLIC"]),
    (".//c:TIT_PUB/c:APLIC", APLIC_CHILDREN),
    (".//c:TIT_PUB/c:APLIC/c:NEGOC", NEGOC_CHILDREN),
    (".//c:TIT_PUB/c:APLIC/c:POS_FIM", POS_FIM_CHILDREN),
    (".//c:COTAS", ["CNPJ_FDO", "APLIC"]),
    (".//c:COTAS/c:APLIC", APLIC_CHILDREN),
    (".//c:SWAP", ["COD_SWAP", "APLIC"]),
    (".//c:SWAP/c:APLIC", APLIC_CHILDREN),
    (".//c:SWAP/c:APLIC/c:NEGOC", ["TP_NEGOC"]),
    (".//c:SWAP/c:APLIC/c:POS_FIM", ["CUSTO_CORREC_POS_FIM", "MERC_POS_FIM"]),
    (".//c:DEMAIS_CODIF", ["COD_ATIV", "COD_TP_ATIV", "DT_INI_VIGEN", "APLIC"]),
    (".//c:DEMAIS_CODIF/c:APLIC", APLIC_CHILDREN),
    (".//c:DEMAIS_N_CODIF", ["COD_TP_ATIV", "DESC", "EMIS", "APLIC"]),
    (".//c:DEMAIS_N_CODIF/c:EMIS", ["TP_PF_PJ_EMIS", "NR_PF_PJ_EMIS", "NM_EMIS"]),
    (".//c:DEMAIS_N_CODIF/c:APLIC", ["COD_TP_APLIC", "QTDE_DIAS_CONFID", "POS_FIM"]),
]
SCALE_BY_TAG = [
    (".//c:VL_PL", "1000000,12"),
    (".//c:TIT_PUB//c:QTDE_VENDAS_NEGOC", "1,000000"),
    (".//c:TIT_PUB//c:VL_VENDAS_NEGOC", "10,00"),
    (".//c:TIT_PUB//c:QTDE_AQUIS_NEGOC", "2,500000"),
    (".//c:TIT_PUB//c:VL_AQUIS_NEGOC", "20,99"),
    (".//c:TIT_PUB//c:QTDE_POS_FIM", "100,123456"),
    (".//c:TIT_PUB//c:CUSTO_CORREC_POS_FIM", "99,99"),
    (".//c:TIT_PUB//c:MERC_POS_FIM", "1234,50"),
]
NOT_IN_V2 = [
    "EMPR_LIGADA",
    "DEP_PRAZO_TIT_IF",
    "TIT_AGRO_CRED_PRIV",
    "INV_EXT",
    "COD_SUBCLASSE",
    "ATIVO_EXT",
]


def _names(node: ET.Element) -> list[str]:
    """Return the local tag names of a node's direct children."""
    return [child.tag.split("}")[1] for child in node]


def _pos_fim(**overrides: object) -> CdaV2PosFim:
    """Build a final position whose quantity, cost and value need truncation."""
    fields: dict[str, object] = {
        "qtde_pos_fim": "100.1234567",
        "custo_correc_pos_fim": "99.999",
        "merc_pos_fim": "1234.5",
    }
    fields.update(overrides)
    return CdaV2PosFim(**fields)


def _negoc() -> CdaNegoc:
    """Trades whose values need truncation."""
    return CdaNegoc(
        tp_negoc=1,
        qtde_vendas_negoc="1",
        vl_vendas_negoc="10",
        qtde_aquis_negoc="2.5",
        vl_aquis_negoc="20.999",
    )


def _aplic(code: int = 37, **overrides: object) -> CdaV2Aplic:
    """Build an application with every Table A column filled."""
    fields: dict[str, object] = {
        "cod_tp_aplic": code,
        "qtde_dias_confid": 0,
        "negoc": _negoc(),
        "pos_fim": _pos_fim(),
    }
    fields.update(overrides)
    return CdaV2Aplic(**fields)


def _inform() -> CdaV2Inform:
    """Build a fund holding one asset of every block."""
    return CdaV2Inform(
        cnpj_fdo=VALID_CNPJ,
        vl_pl="1000000.129",
        tit_pub=[CdaV2TitPub(cod_selic="100000", dt_venc="01/01/2030", aplic=_aplic(75))],
        cotas=[CdaV2Cotas(cnpj_fdo=VALID_CNPJ, aplic=_aplic(92))],
        swap=[
            CdaV2Swap(
                cod_swap="SWPSAB",
                aplic=CdaV2SwapAplic(
                    cod_tp_aplic=183,
                    qtde_dias_confid=0,
                    negoc=CdaV2SwapNegoc(tp_negoc=1),
                    pos_fim=CdaV2SwapPosFim(custo_correc_pos_fim="1", merc_pos_fim="2"),
                ),
            )
        ],
        demais_codif=[
            CdaV2DemaisCodif(
                cod_ativ="ABC",
                cod_tp_ativ=1,
                dt_ini_vigen="01/01/2020",
                aplic=_aplic(37),
            )
        ],
        demais_n_codif=[
            CdaV2DemaisNCodif(
                cod_tp_ativ=999,
                desc="Caixa",
                emis=CdaEmitter(tp_pf_pj_emis="PJ", nr_pf_pj_emis=VALID_CNPJ, nm_emis="Banco"),
                aplic=CdaV2Aplic(
                    cod_tp_aplic=94,
                    qtde_dias_confid=0,
                    pos_fim=CdaV2PosFim(merc_pos_fim="5"),
                ),
            )
        ],
    )


def _doc(*informs: CdaV2Inform) -> CdaV2Document:
    """Build a document of the given funds (one full fund by default)."""
    return CdaV2Document(
        header=CdaV2Header(dt_compt="03/2024", dt_gerac_arq="05/04/2024"),
        informs=list(informs) or [_inform()],
    )


@pytest.fixture(scope="module")  # fixture-scope-ok: immutable text, rebuilt per test otherwise
def xml() -> str:
    """Render the shared document once."""
    return CdaV2().export(_doc())


@pytest.fixture(scope="module")  # fixture-scope-ok: immutable text, rebuilt per test otherwise
def root(xml: str) -> ET.Element:
    """Parse the shared document once."""
    return ET.fromstring(xml.split("\n", 1)[1])


def test_export_starts_with_windows_1252_declaration(xml: str) -> None:
    """Declare windows-1252, as the page's template does."""
    assert xml.startswith('<?xml version="1.0" encoding="windows-1252"?>')


def test_export_root_is_doc_arq_in_urn_cda_namespace(root: ET.Element) -> None:
    """Use the urn:cda namespace the page declares on DOC_ARQ."""
    assert root.tag == "{urn:cda}DOC_ARQ"


def test_header_stamps_v2_values(root: ET.Element) -> None:
    """Stamp COD_DOC 3, VERSAO 2.0 and both dates."""
    head = root.find("c:CAB_INFORM", NS)
    assert [e.text for e in head] == ["3", "2.0", "03/2024", "05/04/2024"]


@pytest.mark.parametrize(("path", "expected"), ORDER_BY_PATH)
def test_children_follow_page_order(root: ET.Element, path: str, expected: list[str]) -> None:
    """Emit each element's children in the order of the page's XML template."""
    assert _names(root.find(path, NS)) == expected


@pytest.mark.parametrize(("path", "expected"), SCALE_BY_TAG)
def test_decimal_scales_follow_page(root: ET.Element, path: str, expected: str) -> None:
    """Truncate to the page's scale (2 for money, 6 for quantity), comma separator."""
    assert root.find(path, NS).text == expected


@pytest.mark.parametrize("tag", NOT_IN_V2)
def test_tags_absent_from_v2_are_never_emitted(xml: str, tag: str) -> None:
    """Never emit a tag the V2 page does not define."""
    assert f"<{tag}>" not in xml


def test_export_to_file_returns_none(tmp_path: Path) -> None:
    """Return None when an output path is given."""
    assert CdaV2().export(_doc(), str(tmp_path / "cda.xml")) is None


def test_export_file_equals_returned_string(tmp_path: Path, xml: str) -> None:
    """The file holds exactly the XML the string form returns, as windows-1252."""
    out = tmp_path / "cda.xml"
    CdaV2().export(_doc(), str(out))
    assert out.read_bytes().decode("windows-1252") == xml


def test_export_accepts_a_mapping(xml: str) -> None:
    """A mapping validates into the same document and serialises identically."""
    assert CdaV2().export(_doc().model_dump(), None) == xml


def test_header_rejects_other_versions() -> None:
    """VERSAO must be 2.0."""
    with pytest.raises(ValidationError):
        CdaV2Header(versao="3.0", dt_compt="03/2024", dt_gerac_arq="05/04/2024")


def test_document_rejects_more_than_50_informs() -> None:
    """The page allows at most 50 funds or classes."""
    with pytest.raises(ValidationError):
        _doc(*[CdaV2Inform(cnpj_fdo=VALID_CNPJ, vl_pl="1")] * 51)


def test_aplic_requires_qtde_dias_confid() -> None:
    """QTDE_DIAS_CONFID must be filled."""
    with pytest.raises(ValidationError):
        CdaV2Aplic(cod_tp_aplic=37, pos_fim=_pos_fim(), negoc=_negoc())


def test_aplic_rejects_more_than_90_confidential_days() -> None:
    """The page caps QTDE_DIAS_CONFID at 90."""
    with pytest.raises(ValidationError):
        _aplic(qtde_dias_confid=91)


def test_table_a_rejects_a_forbidden_column() -> None:
    """Type 94 forbids the final-position quantity."""
    with pytest.raises(ValidationError):
        CdaV2DemaisNCodif(
            cod_tp_ativ=999,
            desc="Caixa",
            emis=CdaEmitter(tp_pf_pj_emis="PJ", nr_pf_pj_emis=VALID_CNPJ, nm_emis="B"),
            aplic=CdaV2Aplic(
                cod_tp_aplic=94,
                qtde_dias_confid=0,
                pos_fim=CdaV2PosFim(qtde_pos_fim="1", merc_pos_fim="5"),
            ),
        )


def test_table_a_requires_a_mandatory_column() -> None:
    """Type 37 requires the cost of the final position."""
    with pytest.raises(ValidationError):
        CdaV2DemaisCodif(
            cod_ativ="A",
            cod_tp_ativ=1,
            dt_ini_vigen="01/01/2020",
            aplic=_aplic(37, pos_fim=_pos_fim(custo_correc_pos_fim=None)),
        )


def test_table_a_rejects_an_unknown_application_type() -> None:
    """Application type 197 exists in V3/V4 but not in the V2 Table A."""
    with pytest.raises(ValidationError):
        CdaV2Cotas(cnpj_fdo=VALID_CNPJ, aplic=_aplic(197))


def test_asset_type_must_relate_to_application_type() -> None:
    """Application 37 (Ações) relates only to asset types 1, 2 and 13."""
    with pytest.raises(ValidationError):
        CdaV2DemaisCodif(cod_ativ="A", cod_tp_ativ=3, dt_ini_vigen="01/01/2020", aplic=_aplic(37))


def test_demais_codif_rejects_an_asset_type_outside_the_page_list() -> None:
    """The page lists asset types 1-7, 9-21, 23-25 and 27 for DEMAIS_CODIF."""
    with pytest.raises(ValidationError):
        CdaV2DemaisCodif(cod_ativ="A", cod_tp_ativ=8, dt_ini_vigen="01/01/2020", aplic=_aplic(75))


def test_money_rejects_a_float() -> None:
    """A binary float is refused, never laundered into a Decimal."""
    with pytest.raises(ValidationError):
        CdaV2PosFim(merc_pos_fim=1.5)


def test_swap_code_must_be_swp_plus_three_characters() -> None:
    """COD_SWAP is 'SWP' plus the 3-character Table D code."""
    with pytest.raises(ValidationError):
        CdaV2Swap(
            cod_swap="SAB",
            aplic=CdaV2SwapAplic(
                cod_tp_aplic=183, qtde_dias_confid=0, pos_fim=CdaV2SwapPosFim(merc_pos_fim="1")
            ),
        )


def test_v2_writer_rejects_a_v3_document() -> None:
    """Refuse a document of another version."""
    with pytest.raises(TypeError):
        CdaV2().export(object())
