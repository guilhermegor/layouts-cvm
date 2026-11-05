"""Unit tests for the Extrato V2 submission writer (tags typed from PadraoXMLInfExtratoV2.asp)."""

from pathlib import Path
from xml.etree import ElementTree as ET  # noqa: S405  # parses our own output in tests

from pydantic import ValidationError
import pytest

from layouts_cvm import ExtratoV2
from layouts_cvm._internal.config.schemas.extrato_v2 import (
    ExtratoV2Document,
    ExtratoV2Header,
    ExtratoV2Row,
)


_NS = "{urn:extr}"
_CNPJ = "11222333000181"

HEADER_TAGS = ["COD_DOC", "VERSAO", "DT_GERAC_ARQ"]
ROW_TAGS = [
    "CNPJ_FDO",
    "FORMA_CONDOMINIO",
    "PRAZO",
    "PUBLICO_ALVO",
    "FUNDO_ANBIMA",
    "COD_DISTR_FDO",
    "COD_POLIT_INVEST",
    "MAX_APP_COTAS_FUNDO",
    "RESULTADO_ATR_CARTEIRA",
    "FUNDO_INVERT_COTAS",
    "APLICACAO_MINIMA_FUNDO",
    "VALOR_COTA",
    "TIPO_VALOR_COTA",
    "VALOR_COTA_BASE_PL",
    "QT_DIA_CONV_COTA",
    "QT_DIA_PAGAM_COTA",
    "RESG_COTAS",
    "PRAZO_PAGAM_RESG",
    "TAXA_ADM",
    "TAXA_MAXIMA_CUSTODIA",
    "TX_PERFM",
    "TX_INGRESSO",
    "TX_SAIDA",
    "OPER_DERIV",
    "OPER_PATRIM_LIQ",
    "MERCADO_SEM_CONTRAPARTE_CENTRAL",
    "ATIV_EXTER",
    "FUNDO_ATIVOS",
    "REGULAMENTO_TIPO_EMISSOR",
    "REGULAMENTO_MODALIDADE_ATIVO",
]
TIPO_EMISSOR_BASES = [
    "INSTITUICOES_FINANCEIRAS",
    "COMPANHIAS_ABERTAS",
    "FUNDOS_INVESTIMENTO",
    "UNIAO_FEDERAL",
    "ADMINISTRADOR_GESTOR_PESSOAS_LIGADAS",
    "OUTROS",
]
MODALIDADE_BASES = [
    "COTAS_FI_555",
    "COTAS_FIC_555",
    "COTAS_FI_555_INVEST_QUALIFICADOS",
    "COTAS_FIC_555_INVEST_QUALIFICADOS",
    "COTAS_FI_555_INVEST_PROFISSIONAIS",
    "COTAS_FIC_555_INVEST_PROFISSIONAIS",
    "COTAS_FII",
    "COTAS_FIDC",
    "COTAS_FICFIDC",
    "COTAS_FIDC_NP",
    "COTAS_FICFIDC_NP",
    "COTAS_FUNDOS_INDICE_MERCADO_ETF",
    "CRI",
    "TITULOS_PUBLICOS_OPERACOES",
    "OURO",
    "TITULOS_EMISSAO_COOBRIGACAO",
    "VALORES_MOBILIARIOS_ALINEA",
    "DEPOSITO_ACOES",
    "DEBENTURES",
    "NOTAS_PROMISSORIAS",
    "OPERACOES_COMPROMISSADAS",
    "DERIVATIVOS",
    "OUTROS",
    "COTAS_FMIEE",
    "COTAS_FIP",
    "COTAS_FICFIP",
]


V2_REQUIRED: dict[str, object] = {
    "publico_alvo": "PÚBLICO EM GERAL",
    "cod_distr_fdo": 2,
    "aplicacao_minima_fundo": "100.50",
    "tipo_valor_cota": "DO DIA DA APLICACAO",
    "valor_cota_base_pl": "DO DIA ANTERIOR",
    "qt_dia_conv_cota": 1,
    "qt_dia_pagam_cota": 2,
    "prazo_pagam_resg": {"dias_sem_taxa": 1, "dias_com_taxa": 2, "tipo_de_contagem": "UTEIS"},
    "taxa_adm": "2.5",
    "taxa_maxima_custodia": "0.123456",
}


def _pairs(bases: list[str], low: str = "1.00", high: str = "50.00") -> dict[str, str]:
    return {
        f"{base.lower()}_{suffix}": value
        for base in bases
        for suffix, value in (("min", low), ("max", high))
    }


def _row(**over: object) -> dict[str, object]:
    row: dict[str, object] = {
        "cnpj_fdo": _CNPJ,
        **V2_REQUIRED,
        "forma_condominio": {"tipo_condominio": "ABERTO"},
        "prazo": {"tipo_prazo": "INDETERMINADO"},
        "fundo_anbima": {"anbima": "N"},
        "cod_polit_invest": 1,
        "max_app_cotas_fundo": "10.5",
        "resultado_atr_carteira": "S",
        "fundo_invert_cotas": {"tipo_fundo_invert": "N"},
        "valor_cota": {"atualizado_diariamente": "S"},
        "resg_cotas": {"carencia_resg_cotas": "N"},
        "tx_perfm": {"cobra_tx_perfm": "N"},
        "tx_ingresso": {"cobra_tx_ingresso": "N"},
        "tx_saida": {"cobra_tx_saida": "N"},
        "oper_deriv": {"realiz_oper_deriv": "N"},
        "oper_patrim_liq": {"realiza_oper_patrim_liq": "N"},
        "mercado_sem_contraparte_central": "N",
        "ativ_exter": {"invest_exterior": "N"},
        "fundo_ativos": {"adquira_credito_privado": "N"},
        "regulamento_tipo_emissor": _pairs(TIPO_EMISSOR_BASES),
        "regulamento_modalidade_ativo": _pairs(MODALIDADE_BASES),
    }
    row.update(over)
    return row


def _doc(**over: object) -> ExtratoV2Document:
    return ExtratoV2Document(
        header=ExtratoV2Header(dt_gerac_arq="31/10/2026"),
        rows=[ExtratoV2Row(**_row(**over))],
    )


def _tags(el: ET.Element) -> list[str]:
    return [c.tag.removeprefix(_NS) for c in el]


def _export(doc: ExtratoV2Document) -> ET.Element:
    xml = ExtratoV2().export(doc)
    assert xml is not None
    return ET.fromstring(xml.encode("windows-1252"))  # noqa: S314


def test_header_is_cod_doc_41_versao_2_0() -> None:
    """The header carries COD_DOC 41, VERSAO 2.0 and the generation date."""
    root = _export(_doc())
    assert [c.text for c in root[0]] == ["41", "2.0", "31/10/2026"]


def test_envelope_tags_follow_the_sample_order() -> None:
    """The root holds CAB_INFORM then EXTRATO_FUNDO, tags in the sample order."""
    root = _export(_doc())
    assert [_tags(root), _tags(root[0])] == [["CAB_INFORM", "EXTRATO_FUNDO"], HEADER_TAGS]


def test_row_tags_follow_the_sample_order() -> None:
    """Every row tag is emitted, in the sample order (none is optional in V2)."""
    root = _export(_doc())
    assert _tags(root[1][0]) == ROW_TAGS


def test_regulation_tags_emit_min_max_pairs() -> None:
    """Both regulation blocks emit one MIN/MAX pair per base, in the sample order."""
    row = _export(_doc())[1][0]
    got = [
        _tags(row.find(f"{_NS}REGULAMENTO_TIPO_EMISSOR")),
        _tags(row.find(f"{_NS}REGULAMENTO_MODALIDADE_ATIVO")),
    ]
    want = [
        [f"{b}_{s}" for b in bases for s in ("MIN", "MAX")]
        for bases in (TIPO_EMISSOR_BASES, MODALIDADE_BASES)
    ]
    assert got == want


@pytest.mark.parametrize(
    ("tag", "text"),
    [
        ("APLICACAO_MINIMA_FUNDO", "100,50"),
        ("TAXA_ADM", "2,5000"),
        ("TAXA_MAXIMA_CUSTODIA", "0,123456"),
        ("MAX_APP_COTAS_FUNDO", "10,5000"),
        ("INSTITUICOES_FINANCEIRAS_MIN", "1,00"),
    ],
)
def test_decimals_use_comma_and_the_page_scale(tag: str, text: str) -> None:
    """Decimals are comma-separated at the scale the page (or the repo policy) fixes."""
    row = _export(_doc())[1][0]
    assert next(e.text for e in row.iter() if e.tag == f"{_NS}{tag}") == text


def test_decimal_input_is_truncated_not_rounded() -> None:
    """A custody fee beyond 6 places is truncated toward zero."""
    row = _export(_doc(taxa_maxima_custodia="0.1234569"))[1][0]
    assert row.find(f"{_NS}TAXA_MAXIMA_CUSTODIA").text == "0,123456"


@pytest.mark.parametrize("name", list(V2_REQUIRED))
def test_row_rejects_a_missing_v2_required_tag(name: str) -> None:
    """The ten tags V3 marks optional are required in V2."""
    row = _row()
    del row[name]
    with pytest.raises(ValidationError):
        ExtratoV2Row(**row)


@pytest.mark.parametrize(
    "bad",
    [
        {"taxa_adm": 2.5},
        {"taxa_adm": "100.01"},
        {"taxa_maxima_custodia": "0.1234567x"},
        {"aplicacao_minima_fundo": float("nan")},
        {"cnpj_fdo": "11222333000182"},
        {"cod_polit_invest": 5},
        {"publico_alvo": "OUTRO"},
        {"unknown_tag": 1},
    ],
)
def test_row_rejects_invalid_input(bad: dict[str, object]) -> None:
    """Floats, out-of-range, bad CNPJ, bad codes and unknown fields are refused."""
    with pytest.raises(ValidationError):
        ExtratoV2Row(**_row(**bad))


def test_regulation_minimum_above_maximum_is_rejected() -> None:
    """A MIN above its MAX is refused."""
    with pytest.raises(ValidationError):
        ExtratoV2Row(**_row(regulamento_tipo_emissor=_pairs(TIPO_EMISSOR_BASES, "60", "50")))


def test_header_rejects_other_versao() -> None:
    """VERSAO is fixed at 2.0."""
    with pytest.raises(ValidationError):
        ExtratoV2Header(dt_gerac_arq="31/10/2026", versao="3.0")


def test_header_rejects_an_impossible_date() -> None:
    """DT_GERAC_ARQ must be a real DD/MM/AAAA date."""
    with pytest.raises(ValidationError):
        ExtratoV2Header(dt_gerac_arq="31/02/2026")


def test_document_requires_at_least_one_row() -> None:
    """An empty file is refused."""
    with pytest.raises(ValidationError):
        ExtratoV2Document(header=ExtratoV2Header(dt_gerac_arq="31/10/2026"), rows=[])


def test_export_accepts_a_plain_mapping() -> None:
    """A mapping is validated into a document."""
    xml = ExtratoV2().export({"header": {"dt_gerac_arq": "31/10/2026"}, "rows": [_row()]})
    assert (xml or "").count("<VERSAO>2.0</VERSAO>") == 1


def test_export_writes_windows_1252_and_returns_none(tmp_path: Path) -> None:
    """With output_path the file is windows-1252 and nothing is returned."""
    path = tmp_path / "extrato.xml"
    returned = ExtratoV2().export(_doc(publico_alvo="PREVIDENCIÁRIO"), str(path))
    assert (returned, "PREVIDENCIÁRIO".encode("windows-1252") in path.read_bytes()) == (None, True)


def _oversize_doc() -> ExtratoV2Document:
    row = ExtratoV2Row(**_row())
    return ExtratoV2Document.model_construct(
        header=ExtratoV2Header(dt_gerac_arq="01/01/2026"), rows=[row] * 1000
    )


def _unencodable_doc() -> ExtratoV2Document:
    header = ExtratoV2Header.model_construct(cod_doc=41, versao="2.0", dt_gerac_arq="日本")
    return ExtratoV2Document.model_construct(header=header, rows=[])


def test_oversize_file_is_refused(tmp_path: Path) -> None:
    """A file past 1 MB raises."""
    with pytest.raises(ValueError, match="1 MB"):
        ExtratoV2().export(_oversize_doc(), str(tmp_path / "e.xml"))


def test_oversize_fixture_has_margin_over_the_limit() -> None:
    """The oversize fixture stays well above 1 MB, so the limit test cannot pass by accident."""
    xml = ExtratoV2().export(_doc())
    assert len((xml or "").encode("windows-1252")) * 1000 > 1_200_000


def test_oversize_file_leaves_the_target_alone(tmp_path: Path) -> None:
    """A refused oversize file does not truncate an existing one."""
    target = tmp_path / "e.xml"
    target.write_bytes(b"keep")
    with pytest.raises(ValueError, match="1 MB"):
        ExtratoV2().export(_oversize_doc(), str(target))
    assert target.read_bytes() == b"keep"  # one-assert-ok: pytest.raises is the failure path


def test_document_rejects_more_than_1000_rows() -> None:
    """The page caps a file at 1000 rows."""
    row = ExtratoV2Row(**_row())
    with pytest.raises(ValidationError):
        ExtratoV2Document(header=ExtratoV2Header(dt_gerac_arq="01/01/2026"), rows=[row] * 1001)


def test_unencodable_text_leaves_the_target_alone(tmp_path: Path) -> None:
    """A failed export does not truncate an existing file."""
    target = tmp_path / "e.xml"
    target.write_bytes(b"keep")
    with pytest.raises(ValueError, match="windows-1252"):
        ExtratoV2().export(_unencodable_doc(), str(target))
    assert target.read_bytes() == b"keep"  # one-assert-ok: pytest.raises is the failure path
