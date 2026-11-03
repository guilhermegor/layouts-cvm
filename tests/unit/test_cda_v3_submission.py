"""Unit tests for the CDA V3 submission writer.

Expectations come from the CVM page PadraoXMLCDANetV3.aspx (tag names and order, comma
decimals, cardinalities), not from the writer. The expected child lists below are the page's
XML template, extracted from the fetched page. Only the V3-vs-V4 delta is re-tested here; the
shared rules (Table A/B, block x application-type) are pinned by test_cda_submission.py.
"""
# ruff: noqa: S314  (parses the writer's own output, not untrusted input)

from pathlib import Path
from xml.etree import ElementTree as ET  # noqa: S405

from pydantic import ValidationError
import pytest

from layouts_cvm import CdaV3
from layouts_cvm._internal.config.schemas.cda import (
    CdaAplic,
    CdaAtivoExt,
    CdaBankEmitter,
    CdaDemaisCodif,
    CdaDemaisNCodif,
    CdaDocument,
    CdaEmitter,
    CdaHeader,
    CdaInform,
    CdaNegoc,
    CdaPosFim,
    CdaPosFixIndex,
    CdaRiskRating,
    CdaSwap,
    CdaSwapAplic,
    CdaSwapPosFim,
    CdaTitAgroCredPriv,
    CdaTitPub,
)
from layouts_cvm._internal.config.schemas.cda_v3 import (
    CdaV3Aplic,
    CdaV3Cotas,
    CdaV3DepPrazoTitIf,
    CdaV3Document,
    CdaV3Header,
    CdaV3Inform,
    CdaV3InvExt,
)


VALID_CNPJ = "11222333000181"
NS = {"c": "urn:cda"}
APLIC_CHILDREN = ["COD_TP_APLIC", "EMPR_LIGADA", "QTDE_DIAS_CONFID", "NEGOC", "POS_FIM"]
NEGOC_CHILDREN = [
    "TP_NEGOC",
    "QTDE_VENDAS_NEGOC",
    "VL_VENDAS_NEGOC",
    "QTDE_AQUIS_NEGOC",
    "VL_AQUIS_NEGOC",
]
EMIS_PF_PJ = ["TP_PF_PJ_EMIS", "NR_PF_PJ_EMIS", "NM_EMIS"]
INDEX_CHILDREN = ["TIT_POS_FIX_COD_INDEX", "TIT_POS_FIX_PR_INDEX", "TIT_POS_FIX_CUPOM"]
RATING_CHILDREN = ["AG_CLASSIF_RISCO", "DT_CLASSIF_RISCO", "GRAU_CLASSIF_RISCO"]
EMPR_NO_TP_APLIC = ["EMPR_LIGADA", "QTDE_DIAS_CONFID", "NEGOC", "POS_FIM"]
ORDER_BY_PATH = [
    ("c:CAB_INFORM", ["COD_DOC", "VERSAO", "DT_COMPT", "DT_GERAC_ARQ"]),
    (".//c:INFORM", ["CNPJ_FDO", "VL_PL", "LISTA_ATIV"]),
    (
        ".//c:LISTA_ATIV",
        [
            "TIT_PUB",
            "COTAS",
            "SWAP",
            "DEMAIS_CODIF",
            "DEP_PRAZO_TIT_IF",
            "TIT_AGRO_CRED_PRIV",
            "INV_EXT",
            "DEMAIS_N_CODIF",
        ],
    ),
    (".//c:TIT_PUB", ["COD_SELIC", "DT_VENC", "APLIC"]),
    (".//c:TIT_PUB/c:APLIC", ["COD_TP_APLIC", "QTDE_DIAS_CONFID", "NEGOC", "POS_FIM"]),
    (".//c:TIT_PUB/c:APLIC/c:NEGOC", NEGOC_CHILDREN),
    (".//c:TIT_PUB/c:APLIC/c:POS_FIM", ["QTDE_POS_FIM", "MERC_POS_FIM"]),
    (".//c:COTAS", ["CNPJ_FDO", "APLIC"]),
    (".//c:COTAS/c:APLIC", EMPR_NO_TP_APLIC),
    (".//c:SWAP", ["COD_SWAP", "APLIC"]),
    (".//c:SWAP/c:APLIC", ["COD_TP_APLIC", "QTDE_DIAS_CONFID", "POS_FIM"]),
    (".//c:SWAP/c:APLIC/c:POS_FIM", ["MERC_POS_FIM"]),
    (".//c:DEMAIS_CODIF", ["COD_ATIV", "COD_TP_ATIV", "DT_INI_VIGEN", "APLIC"]),
    (".//c:DEMAIS_CODIF/c:APLIC", APLIC_CHILDREN),
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
    (".//c:DEP_PRAZO_TIT_IF/c:TIT_POS_FIX_INDEX", INDEX_CHILDREN),
    (".//c:DEP_PRAZO_TIT_IF/c:CLASSIF_RISCO", RATING_CHILDREN),
    (".//c:DEP_PRAZO_TIT_IF/c:APLIC", EMPR_NO_TP_APLIC),
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
    (".//c:TIT_AGRO_CRED_PRIV/c:EMIS", EMIS_PF_PJ),
    (".//c:TIT_AGRO_CRED_PRIV/c:APLIC", APLIC_CHILDREN),
    (
        ".//c:INV_EXT",
        [
            "COD_TP_ATIV",
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
    (".//c:INV_EXT/c:CLASSIF_RISCO", RATING_CHILDREN),
    (".//c:INV_EXT/c:APLIC", EMPR_NO_TP_APLIC),
    (".//c:DEMAIS_N_CODIF", ["COD_TP_ATIV", "DESC", "EMIS", "APLIC"]),
    (".//c:DEMAIS_N_CODIF/c:EMIS", EMIS_PF_PJ),
    (".//c:DEMAIS_N_CODIF/c:APLIC", ["COD_TP_APLIC", "POS_FIM"]),
]
SCALE_BY_TAG = [
    (".//c:VL_PL", "1000000,12"),
    (".//c:TIT_PUB//c:QTDE_VENDAS_NEGOC", "1,000000"),
    (".//c:TIT_PUB//c:VL_VENDAS_NEGOC", "10,00"),
    (".//c:TIT_PUB//c:QTDE_AQUIS_NEGOC", "2,500000"),
    (".//c:TIT_PUB//c:VL_AQUIS_NEGOC", "20,99"),
    (".//c:TIT_PUB//c:QTDE_POS_FIM", "100,123456"),
    (".//c:TIT_PUB//c:MERC_POS_FIM", "1234,50"),
    (".//c:TIT_POS_FIX_PR_INDEX", "102,123456"),
    (".//c:TIT_POS_FIX_CUPOM", "3,000000"),
    (".//c:TIT_PRE_FIX_TAXA_CONTR", "15,000000"),
]
V4_ONLY_TAGS = [
    "COD_SUBCLASSE",
    "DESC_ATIV_VINC",
    "INV_COLETIVO",
    "GEST_INV_COLETIVO",
    "ATIVO_EXT",
]


def _names(node: ET.Element) -> list[str]:
    """Return the local tag names of a node's direct children."""
    return [child.tag.split("}")[1] for child in node]


def _pos_fim() -> CdaPosFim:
    """Build a final position whose quantity needs truncation."""
    return CdaPosFim(qtde_pos_fim="100.1234567", merc_pos_fim="1234.5")


def _negoc() -> CdaNegoc:
    """Trades whose values need truncation."""
    return CdaNegoc(
        tp_negoc=1,
        qtde_vendas_negoc="1",
        vl_vendas_negoc="10",
        qtde_aquis_negoc="2.5",
        vl_aquis_negoc="20.999",
    )


def _aplic(**overrides: object) -> CdaAplic:
    """Application of type 37 (Ações): every Table A column is filled."""
    fields: dict[str, object] = {
        "empr_ligada": "N",
        "qtde_dias_confid": 0,
        "negoc": _negoc(),
        "pos_fim": _pos_fim(),
    }
    fields.update(overrides)
    return CdaAplic(**fields)


def _rating() -> CdaRiskRating:
    """Build a risk rating."""
    return CdaRiskRating(
        ag_classif_risco="Agencia", dt_classif_risco="01/02/2024", grau_classif_risco="AAA"
    )


def _emitter() -> CdaEmitter:
    """Build a legal-person issuer."""
    return CdaEmitter(tp_pf_pj_emis="PJ", nr_pf_pj_emis=VALID_CNPJ, nm_emis="Emissor")


def _cotas(**overrides: object) -> CdaV3Cotas:
    """V3 COTAS block (type 197)."""
    fields: dict[str, object] = {"cnpj_fdo": VALID_CNPJ, "aplic": _aplic()}
    fields.update(overrides)
    return CdaV3Cotas(**fields)


def _dep_prazo(**overrides: object) -> CdaV3DepPrazoTitIf:
    """V3 DEP_PRAZO_TIT_IF block (type 74), post-fixed and rated."""
    fields: dict[str, object] = {
        "cod_tp_ativ": 51,
        "emis": CdaBankEmitter(cnpj_emis=VALID_CNPJ, nm_emis="Banco"),
        "dt_venc": "01/01/2030",
        "st_tit_pos_fix": "S",
        "tit_pos_fix_index": CdaPosFixIndex(
            tit_pos_fix_cod_index="DI1",
            tit_pos_fix_pr_index="102.1234567",
            tit_pos_fix_cupom="3",
        ),
        "st_classif_risco": "S",
        "classif_risco": _rating(),
        "aplic": _aplic(),
    }
    fields.update(overrides)
    return CdaV3DepPrazoTitIf(**fields)


def _inv_ext(**overrides: object) -> CdaV3InvExt:
    """V3 INV_EXT block (type 189)."""
    fields: dict[str, object] = {
        "cod_tp_ativ": 1,
        "nm_emis": "Foreign Inc",
        "dt_venc": "01/01/2030",
        "cod_pais": 840,
        "cod_bv_merc": "XNYS",
        "cod_ativo_bv_merc": "AAPL",
        "st_classif_risco": "S",
        "classif_risco": _rating(),
        "aplic": CdaV3Aplic(**_aplic().model_dump()),
    }
    fields.update(overrides)
    return CdaV3InvExt(**fields)


def _agro() -> CdaTitAgroCredPriv:
    """TIT_AGRO_CRED_PRIV block (type 195), pre-fixed."""
    return CdaTitAgroCredPriv(
        cod_tp_ativ=31,
        emis=_emitter(),
        dt_venc="01/01/2030",
        st_tit_pos_fix="N",
        tit_pre_fix_taxa_contr="15",
        st_tit_reg_cetip="S",
        st_tit_garant_seguro="N",
        cnpj_instit_financ=VALID_CNPJ,
        aplic=_aplic(cod_tp_aplic=195),
    )


def _inform() -> CdaV3Inform:
    """Build a fund holding all eight blocks, passed in scrambled order."""
    return CdaV3Inform(
        cnpj_fdo=VALID_CNPJ,
        vl_pl="1000000.129",
        demais_n_codif=[
            CdaDemaisNCodif(
                cod_tp_ativ=999,
                desc="Caixa",
                emis=_emitter(),
                aplic=CdaAplic(cod_tp_aplic=94, pos_fim=CdaPosFim(merc_pos_fim="7")),
            )
        ],
        inv_ext=[_inv_ext()],
        tit_agro_cred_priv=[_agro()],
        dep_prazo_tit_if=[_dep_prazo()],
        demais_codif=[
            CdaDemaisCodif(
                cod_ativ="PETR4",
                cod_tp_ativ=1,
                dt_ini_vigen="01/01/2020",
                aplic=_aplic(cod_tp_aplic=37),
            )
        ],
        swap=[
            CdaSwap(
                cod_swap="SWPSDI",
                aplic=CdaSwapAplic(
                    cod_tp_aplic=183,
                    qtde_dias_confid=0,
                    pos_fim=CdaSwapPosFim(merc_pos_fim="5"),
                ),
            )
        ],
        cotas=[_cotas()],
        tit_pub=[
            CdaTitPub(
                cod_selic="100000",
                dt_venc="01/01/2030",
                aplic=_aplic(cod_tp_aplic=75, empr_ligada=None),
            )
        ],
    )


def _doc(*informs: CdaV3Inform) -> CdaV3Document:
    """V3 document, 03/2024."""
    return CdaV3Document(
        header=CdaV3Header(dt_compt="03/2024", dt_gerac_arq="05/04/2024"),
        informs=list(informs) or [_inform()],
    )


@pytest.fixture(scope="module")  # fixture-scope-ok: immutable text, rebuilt per test otherwise
def xml() -> str:
    """Serialize the full document once and share the immutable text."""
    result = CdaV3().export(_doc())
    assert result is not None
    return result


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


def test_header_stamps_v3_values(root: ET.Element) -> None:
    """Stamp COD_DOC 3, VERSAO 3.0 and both dates."""
    head = root.find("c:CAB_INFORM", NS)
    assert [e.text for e in head] == ["3", "3.0", "03/2024", "05/04/2024"]


@pytest.mark.parametrize(("path", "expected"), ORDER_BY_PATH)
def test_children_follow_page_order(root: ET.Element, path: str, expected: list[str]) -> None:
    """Emit each element's children in the order of the page's XML template."""
    assert _names(root.find(path, NS)) == expected


@pytest.mark.parametrize(("path", "expected"), SCALE_BY_TAG)
def test_decimal_scales_follow_page(root: ET.Element, path: str, expected: str) -> None:
    """Truncate to the page's scale (2 for money, 6 for quantity and rates), comma separator."""
    assert root.find(path, NS).text == expected


@pytest.mark.parametrize("tag", V4_ONLY_TAGS)
def test_v4_only_tags_are_never_emitted(xml: str, tag: str) -> None:
    """Never emit a tag that only the V4 page defines."""
    assert f"<{tag}>" not in xml


def test_export_strips_leading_zeros_from_cnpj() -> None:
    """The page forbids zero fillers on the left of the CNPJ."""
    inform = CdaV3Inform(cnpj_fdo="00.000.000/0001-91", vl_pl="1")
    root = ET.fromstring(CdaV3().export(_doc(inform)).split("\n", 1)[1])
    assert root.find(".//c:CNPJ_FDO", NS).text == "191"


def test_export_to_file_returns_none(tmp_path: Path) -> None:
    """Return None when an output path is given."""
    assert CdaV3().export(_doc(), str(tmp_path / "cda.xml")) is None


def test_export_writes_windows_1252_file(tmp_path: Path) -> None:
    """Write the file as windows-1252."""
    out = tmp_path / "cda.xml"
    CdaV3().export(_doc(), str(out))
    assert out.read_bytes().startswith(b'<?xml version="1.0" encoding="windows-1252"?>')


def test_export_file_equals_returned_string(tmp_path: Path, xml: str) -> None:
    """The file holds exactly the XML the string form returns."""
    out = tmp_path / "cda.xml"
    CdaV3().export(_doc(), str(out))
    assert out.read_bytes().decode("windows-1252") == xml


def test_v3_writer_rejects_a_v4_document() -> None:
    """Refuse a V4 document: the V3 writer is its own port adapter."""
    v4_doc = CdaDocument(
        header=CdaHeader(dt_compt="03/2024", dt_gerac_arq="05/04/2024"),
        informs=[CdaInform(cnpj_fdo=VALID_CNPJ, vl_pl="1")],
    )
    with pytest.raises(TypeError):
        CdaV3().export(v4_doc)


def test_header_rejects_v4_versao() -> None:
    """Reject a header claiming VERSAO 4.0."""
    with pytest.raises(ValidationError):
        CdaV3Header(dt_compt="03/2024", dt_gerac_arq="05/04/2024", versao="4.0")


def test_header_rejects_other_cod_doc() -> None:
    """Reject a header claiming another COD_DOC."""
    with pytest.raises(ValidationError):
        CdaV3Header(dt_compt="03/2024", dt_gerac_arq="05/04/2024", cod_doc=1)


def test_header_rejects_malformed_competence() -> None:
    """Reject a competence not in MM/AAAA."""
    with pytest.raises(ValidationError):
        CdaV3Header(dt_compt="2024-03", dt_gerac_arq="05/04/2024")


def test_document_accepts_exactly_50_funds() -> None:
    """Accept the page's limit of 50 funds per file."""
    assert len(_doc(*[_inform()] * 50).informs) == 50


def test_document_rejects_more_than_50_funds() -> None:
    """Reject the 51st fund: V3 caps the file at 50, not V4's 1000."""
    with pytest.raises(ValidationError):
        _doc(*[_inform()] * 51)


def test_cotas_rejects_cod_subclasse() -> None:
    """Reject COD_SUBCLASSE: V3 identifies the invested fund by CNPJ_FDO alone."""
    with pytest.raises(ValidationError, match="cod_subclasse does not exist"):
        _cotas(cod_subclasse="X1")


def test_cotas_requires_cnpj() -> None:
    """Reject COTAS without CNPJ_FDO."""
    with pytest.raises(ValidationError):
        CdaV3Cotas(aplic=_aplic(negoc=None))


def test_cotas_rejects_invalid_cnpj_check_digit() -> None:
    """Reject a CNPJ whose check digits are wrong."""
    with pytest.raises(ValidationError):
        _cotas(cnpj_fdo="11222333000182")


def test_dep_prazo_rejects_desc_ativ_vinc() -> None:
    """Reject DESC_ATIV_VINC, which V3 does not define."""
    with pytest.raises(ValidationError, match="desc_ativ_vinc does not exist"):
        _dep_prazo(desc_ativ_vinc="CDB vinculado")


@pytest.mark.parametrize("name", ["inv_coletivo", "gest_inv_coletivo"])
def test_inv_ext_rejects_collective_vehicle_flags(name: str) -> None:
    """Reject INV_COLETIVO and GEST_INV_COLETIVO, which V3 does not define."""
    with pytest.raises(ValidationError, match=f"{name} does not exist"):
        _inv_ext(**{name: "S"})


def test_inv_ext_aplic_rejects_ativo_ext() -> None:
    """Reject ATIVO_EXT inside the V3 INV_EXT application."""
    ativo = CdaAtivoExt(desc_at_ext="Ativo", qtde_at_ext=1, valor_at_ext="1")
    with pytest.raises(ValidationError, match="ativo_ext does not exist"):
        CdaV3Aplic(**_aplic().model_dump(exclude={"ativo_ext"}), ativo_ext=ativo)


def test_shared_table_a_rule_still_applies() -> None:
    """Keep the shared Table A matrix: type 94 forbids a final-position quantity."""
    with pytest.raises(ValidationError, match="posicao final"):
        CdaDemaisNCodif(
            cod_tp_ativ=999,
            desc="x",
            emis=_emitter(),
            aplic=CdaAplic(cod_tp_aplic=94, pos_fim=_pos_fim()),
        )


def test_shared_post_fixed_rule_still_applies() -> None:
    """Keep the shared fixing rule: a post-fixed deposit needs its index block."""
    with pytest.raises(ValidationError, match="post-fixed"):
        _dep_prazo(tit_pos_fix_index=None)
