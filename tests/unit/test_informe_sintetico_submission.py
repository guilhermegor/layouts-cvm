"""Unit tests for the Informe Sintético submission writer (four fund-type variants).

The expected tag lists are typed from the CVM pages' sample files (``PadraoXMLSintFCCE.asp``,
``PadraoXMLSintFITVM.asp``, ``PadraoXMLSintFIC.asp``, ``PadraoXMLSintOutros.asp``), not derived
from the models, so a field declared out of order fails here. Every test holds one assertion site.
"""

from contextlib import suppress
from copy import deepcopy
from pathlib import Path
from xml.etree import ElementTree as ET  # noqa: S405

from pydantic import ValidationError
import pytest

from layouts_cvm import InformeSintetico
from layouts_cvm._internal.config.schemas.informe_sintetico import (
    InformeSinteticoFcceDocument,
    InformeSinteticoFcceHeader,
    InformeSinteticoFicDocument,
    InformeSinteticoFitvmDocument,
    InformeSinteticoOutrosDocument,
)


DOCUMENTS = {
    5: InformeSinteticoFcceDocument,
    7: InformeSinteticoFitvmDocument,
    8: InformeSinteticoFicDocument,
    9: InformeSinteticoOutrosDocument,
}

ADM_CNPJ = "11222333000181"
FUND_CNPJ = "11444777000161"
OTHER_CNPJ = "11222333000262"

TAGS_OUTRAS_TAIL = [
    "NR_TOT_QUOTST_ULT_DIA_MES",
    "VL_QUOTA_ULT_DIA_MES",
    "PATRIM_LIQ",
    "QUOTA_EMITIDA_MES",
    "QUOTA_RESG_MES",
]

TAGS_APLICACOES = {
    5: [
        "ACOES",
        "QUOTA_FDO_RENDA_FIXA",
        "TIT_DIVIDA_PUBLIC_FED",
        "OUTRO_VL_MOBILI_EMISS_CIA_ABER",
        "OUTRA_APLIC",
    ],
    7: [
        "ACAO",
        "MERC_A_TERMO",
        "CONTR_FUTURO",
        "MERC_OPCAO",
        "DEBT",
        "CERTF_RECIBO_DEPOS_OUTRO_VL_MOBILI",
        "TIT_PUBLIC",
        "TIT_RENDA_FIXA_EMISS_INSTIT_FINANC",
        "COTA_FDO_INVEST_FINANC",
        "OUTRA_APLIC",
    ],
    8: [
        "COTAS",
        "TIT_PUBLIC",
        "TIT_RENDA_FIXA_EMISS_INSTIT_FINANC",
        "COTA_FDO_INVEST_FINANC",
        "OUTRA_APLIC",
    ],
    9: [
        "ACAO",
        "MERC_OPCAO",
        "MERC_A_TERMO",
        "CONVERSIVEIS",
        "SIMPLES",
        "TIT_PUBLIC",
        "MOEDA_PRIVAT",
        "OUTRA_APLIC",
    ],
}
TAGS_OUTRAS = {
    5: ["VL_CONTR_FUTURO_MANTIDO_ABER", *TAGS_OUTRAS_TAIL],
    7: TAGS_OUTRAS_TAIL,
    8: TAGS_OUTRAS_TAIL,
    9: ["VL_CONTR_FUTURO_MANTIDO_ABERTO", *TAGS_OUTRAS_TAIL],
}
CODES = sorted(TAGS_APLICACOES)

_AMOUNTS = {
    5: {
        "acoes": 1,
        "quota_fdo_renda_fixa": 2,
        "tit_divida_public_fed": 3,
        "outro_vl_mobili_emiss_cia_aber": 4,
        "outra_aplic": 5,
    },
    7: {
        "acao": 1,
        "merc_a_termo": {"pos_comprd": 2, "pos_vend": 3},
        "contr_futuro": {"tot_margem_requerida": 4},
        "merc_opcao": {"premio_pago": 5, "premio_receb": 6},
        "debt": {"simples": 7, "conversiveis": 8},
        "certf_recibo_depos_outro_vl_mobili": 9,
        "tit_public": 10,
        "tit_renda_fixa_emiss_instit_financ": 11,
        "cota_fdo_invest_financ": 12,
        "outra_aplic": 13,
    },
    8: {
        "cotas": 1,
        "tit_public": 2,
        "tit_renda_fixa_emiss_instit_financ": 3,
        "cota_fdo_invest_financ": 4,
        "outra_aplic": 5,
    },
    9: {
        "acao": 1,
        "merc_opcao": {"premio_pago": 2, "premio_receb": 3},
        "merc_a_termo": {"pos_comprd": 4, "pos_vend": 5},
        "conversiveis": 6,
        "simples": 7,
        "tit_public": 8,
        "moeda_privat": 9,
        "outra_aplic": 10,
    },
}
_FUTURES_FIELD = {
    5: {"vl_contr_futuro_mantido_aber": 11},
    7: {},
    8: {},
    9: {"vl_contr_futuro_mantido_aberto": 11},
}
_OUTRAS_TAIL = {
    "nr_tot_quotst_ult_dia_mes": 12,
    "vl_quota_ult_dia_mes": "12.5",
    "patrim_liq": 1000,
    "quota_emitida_mes": 7,
    "quota_resg_mes": 3,
}


def _row(cod_doc: int, cnpj: str = FUND_CNPJ, **outras_over: object) -> dict:
    outras = {**_FUTURES_FIELD[cod_doc], **_OUTRAS_TAIL, **outras_over}
    return {
        "cnpj_fundo": cnpj,
        "aplicacoes_pos_final": {"aplicacoes": deepcopy(_AMOUNTS[cod_doc]), "outras": outras},
    }


def _header(cod_doc: int, **over: object) -> dict:
    base = {
        "cod_doc": cod_doc,
        "cnpj_adm": ADM_CNPJ,
        "dt_compt": "06/2026",
        "dt_gerac_arq": "15/07/2026",
    }
    return {**base, **over}


def _data(cod_doc: int, *rows: dict, header: dict | None = None) -> dict:
    return {"header": header or _header(cod_doc), "rows": list(rows) or [_row(cod_doc)]}


def _xml(data: dict) -> ET.Element:
    text = InformeSintetico().export(data)
    return ET.fromstring(text.encode("windows-1252"))  # noqa: S314


def _tags(el: ET.Element) -> list[str]:
    return [c.tag for c in el]


def _body(cod_doc: int) -> ET.Element:
    return _xml(_data(cod_doc))[1][0][1]


def test_export_starts_with_windows_1252_declaration() -> None:
    """Export starts with the windows-1252 declaration."""
    assert (
        InformeSintetico()
        .export(_data(5))
        .startswith('<?xml version="1.0" encoding="windows-1252"?>\n')
    )


@pytest.mark.parametrize("cod_doc", CODES)
def test_root_is_doc_arq_without_a_namespace(cod_doc: int) -> None:
    """Root is a bare DOC_ARQ: the pages declare no namespace."""
    assert _xml(_data(cod_doc)).tag == "DOC_ARQ"


@pytest.mark.parametrize("cod_doc", CODES)
def test_root_children_in_page_order(cod_doc: int) -> None:
    """Root children are DESC_ADM then INFORME_SINTETICO."""
    assert _tags(_xml(_data(cod_doc))) == ["DESC_ADM", "INFORME_SINTETICO"]


@pytest.mark.parametrize("cod_doc", CODES)
def test_header_tags_in_page_order(cod_doc: int) -> None:
    """Header tags in page order."""
    assert _tags(_xml(_data(cod_doc))[0]) == [
        "COD_DOC",
        "CNPJ_ADM",
        "DT_COMPT",
        "DT_GERAC_ARQ",
    ]


@pytest.mark.parametrize("cod_doc", CODES)
def test_header_values(cod_doc: int) -> None:
    """Header carries the variant code, bare CNPJ, competence and generation date."""
    assert [c.text for c in _xml(_data(cod_doc))[0]] == [
        str(cod_doc),
        ADM_CNPJ,
        "06/2026",
        "15/07/2026",
    ]


@pytest.mark.parametrize("cod_doc", CODES)
def test_row_children_in_page_order(cod_doc: int) -> None:
    """A row is CNPJ_FUNDO then APLICACOES_POS_FINAL."""
    assert _tags(_xml(_data(cod_doc))[1][0]) == ["CNPJ_FUNDO", "APLICACOES_POS_FINAL"]


@pytest.mark.parametrize("cod_doc", CODES)
def test_position_blocks_in_page_order(cod_doc: int) -> None:
    """APLICACOES_POS_FINAL is APLICACOES then OUTRAS."""
    assert _tags(_body(cod_doc)) == ["APLICACOES", "OUTRAS"]


@pytest.mark.parametrize("cod_doc", CODES)
def test_aplicacoes_tags_in_page_order(cod_doc: int) -> None:
    """APLICACOES tags follow each variant's own page order."""
    assert _tags(_body(cod_doc)[0]) == TAGS_APLICACOES[cod_doc]


@pytest.mark.parametrize("cod_doc", CODES)
def test_outras_tags_in_page_order(cod_doc: int) -> None:
    """OUTRAS tags follow each variant's own page order."""
    assert _tags(_body(cod_doc)[1]) == TAGS_OUTRAS[cod_doc]


def test_fitvm_nested_blocks_in_page_order() -> None:
    """FITVM nested blocks list their leaves in page order."""
    aplic = _body(7)[0]
    assert [_tags(aplic[i]) for i in (1, 2, 3, 4)] == [
        ["POS_COMPRD", "POS_VEND"],
        ["TOT_MARGEM_REQUERIDA"],
        ["PREMIO_PAGO", "PREMIO_RECEB"],
        ["SIMPLES", "CONVERSIVEIS"],
    ]


def test_outros_nested_blocks_in_page_order() -> None:
    """Outros option block precedes the forward-market block, as on the page."""
    assert [_tags(_body(9)[0][i]) for i in (1, 2)] == [
        ["PREMIO_PAGO", "PREMIO_RECEB"],
        ["POS_COMPRD", "POS_VEND"],
    ]


def test_outras_values_use_integer_amounts_and_decimal_comma_quota() -> None:
    """Amounts are written as integers and the quota value with a decimal comma."""
    assert [c.text for c in _body(8)[1]] == [
        "12",
        "12,500000000000",
        "1000",
        "7",
        "3",
    ]


def test_multiple_funds_are_repeated_rows() -> None:
    """Several funds in one file are repeated ROW_INFORME blocks."""
    data = _data(5, _row(5), _row(5, OTHER_CNPJ))
    assert _tags(_xml(data)[1]) == ["ROW_INFORME", "ROW_INFORME"]


def test_masked_cnpj_is_written_bare() -> None:
    """A masked fund CNPJ is written without the mask."""
    data = _data(5, _row(5, "11.444.777/0001-61"))
    assert _xml(data)[1][0][0].text == FUND_CNPJ


@pytest.mark.parametrize("cod_doc", CODES)
def test_mapping_picks_the_variant_from_cod_doc(cod_doc: int) -> None:
    """Plain data and the model built from it serialise to identical text."""
    data = _data(cod_doc)
    model = DOCUMENTS[cod_doc].model_validate(data)
    assert InformeSintetico().export(data) == InformeSintetico().export(model)


@pytest.mark.parametrize("bad", [None, 6, "5", 0])
def test_unknown_cod_doc_rejected(bad: object) -> None:
    """A mapping whose COD_DOC is not 5, 7, 8 or 9 is refused."""
    with pytest.raises(ValueError, match="cod_doc"):
        InformeSintetico().export(_data(5, header={**_header(5), "cod_doc": bad}))


def test_mapping_without_header_rejected() -> None:
    """A mapping with no header cannot pick a variant."""
    with pytest.raises(ValueError, match="cod_doc"):
        InformeSintetico().export({"rows": []})


def test_cod_doc_must_match_the_variant() -> None:
    """A model for one variant refuses another variant's code."""
    with pytest.raises(ValidationError):
        InformeSinteticoFcceHeader(**_header(7))


@pytest.mark.parametrize(
    ("field", "bad"),
    [
        ("patrim_liq", 1.5),
        ("patrim_liq", "1"),
        ("patrim_liq", True),
        ("patrim_liq", 10**12),
        ("nr_tot_quotst_ult_dia_mes", -1),
        ("nr_tot_quotst_ult_dia_mes", 1.0),
        ("vl_quota_ult_dia_mes", 1.5),
        ("vl_quota_ult_dia_mes", "NaN"),
        ("vl_quota_ult_dia_mes", "Infinity"),
    ],
)
def test_invalid_outras_values_rejected(field: str, bad: object) -> None:
    """Floats, bools, strings for integers, NaN and out-of-range values are refused."""
    with pytest.raises(ValidationError):
        InformeSintetico().export(_data(7, _row(7, **{field: bad})))


def test_quota_value_truncates_beyond_twelve_places() -> None:
    """The quota value truncates, never rounds, beyond twelve places."""
    data = _data(7, _row(7, vl_quota_ult_dia_mes="1.9999999999999"))
    assert _body_text(data, 1) == "1,999999999999"


def _body_text(data: dict, index: int) -> str | None:
    return _xml(data)[1][0][1][1][index].text


def test_negative_amount_allowed() -> None:
    """The net worth may be negative (a fund with a deficit)."""
    assert _body_text(_data(7, _row(7, patrim_liq=-5)), 2) == "-5"


@pytest.mark.parametrize("missing", ["patrim_liq", "quota_resg_mes", "vl_quota_ult_dia_mes"])
def test_every_outras_field_is_required(missing: str) -> None:
    """Every OUTRAS field is required."""
    row = _row(8)
    del row["aplicacoes_pos_final"]["outras"][missing]
    with pytest.raises(ValidationError):
        InformeSintetico().export(_data(8, row))


def test_unknown_field_rejected() -> None:
    """An unknown field is refused."""
    row = _row(8)
    row["aplicacoes_pos_final"]["aplicacoes"]["extra"] = 1
    with pytest.raises(ValidationError):
        InformeSintetico().export(_data(8, row))


@pytest.mark.parametrize("bad", ["11222333000182", " 11444777000161", "11444777000161\n"])
def test_invalid_fund_cnpj_rejected(bad: str) -> None:
    """A fund CNPJ with a bad check digit or stray whitespace is refused."""
    with pytest.raises(ValidationError):
        InformeSintetico().export(_data(5, _row(5, bad)))


@pytest.mark.parametrize("bad", ["01/2026\n", "13/2026", "6/2026", "06/26", "00/2026"])
def test_competence_rejected(bad: str) -> None:
    """A competence that is not a real MM/AAAA is refused."""
    with pytest.raises(ValidationError):
        InformeSintetico().export(_data(5, header=_header(5, dt_compt=bad)))


@pytest.mark.parametrize("bad", ["31/02/2026", "1/1/2026", "x"])
def test_generation_date_must_be_a_real_date(bad: str) -> None:
    """The generation date must be a real calendar date."""
    with pytest.raises(ValidationError):
        InformeSinteticoFcceHeader(**_header(5, dt_gerac_arq=bad))


def test_administrator_cnpj_is_validated() -> None:
    """The administrator CNPJ is check-digit validated."""
    with pytest.raises(ValidationError):
        InformeSinteticoFcceHeader(**_header(5, cnpj_adm="11222333000182"))


def test_document_needs_at_least_one_fund() -> None:
    """A document needs at least one fund."""
    with pytest.raises(ValidationError):
        InformeSintetico().export({"header": _header(5), "rows": []})


def test_export_to_file_returns_none(tmp_path: Path) -> None:
    """Export to a file returns None."""
    assert InformeSintetico().export(_data(5), str(tmp_path / "is.xml")) is None


def test_exported_file_is_windows_1252_xml(tmp_path: Path) -> None:
    """The exported file is windows-1252 XML."""
    out = tmp_path / "is.xml"
    InformeSintetico().export(_data(5), str(out))
    assert out.read_bytes().startswith(b'<?xml version="1.0" encoding="windows-1252"?>')


def test_export_leaves_no_temp_file(tmp_path: Path) -> None:
    """Export leaves no temp file behind."""
    InformeSintetico().export(_data(5), str(tmp_path / "is.xml"))
    assert [p.name for p in tmp_path.iterdir()] == ["is.xml"]


def _unencodable_doc() -> InformeSinteticoFcceDocument:
    doc = InformeSinteticoFcceDocument.model_validate(_data(5))
    object.__setattr__(doc.rows[0], "cnpj_fundo", "中")  # noqa: PLC2801
    return doc


def test_unencodable_text_raises_value_error(tmp_path: Path) -> None:
    """Unencodable text raises a ValueError naming the encoding."""
    with pytest.raises(ValueError, match="windows-1252"):
        InformeSintetico().export(_unencodable_doc(), str(tmp_path / "is.xml"))


def test_unencodable_text_never_wipes_existing_file(tmp_path: Path) -> None:
    """Unencodable text never wipes an existing file."""
    out = tmp_path / "is.xml"
    out.write_bytes(b"keep me")
    with suppress(ValueError):
        InformeSintetico().export(_unencodable_doc(), str(out))
    assert out.read_bytes() == b"keep me"


def test_rows_list_input_is_coerced_to_an_immutable_tuple() -> None:
    """List input is stored as a tuple, so a caller cannot append after validation."""
    assert isinstance(InformeSinteticoFcceDocument.model_validate(_data(5)).rows, tuple)
