"""Unit tests for the Informe Diário V1 submission writer.

Pin the tag order, the LISTA_INFORM wrapper and the decimal scales to
PadraoXMLInfoDiarioNet.asp, and cover the V1-only rules (no VERSAO, CNPJ_FDO only,
no DATA_PROX_PL).
"""

from pathlib import Path
import re

from pydantic import ValidationError
import pytest

from layouts_cvm._internal.config.schemas.informe_diario_v1 import (
    InformeDiarioV1Document,
    InformeDiarioV1Header,
    InformeDiarioV1Inform,
    InformeDiarioV1Shareholder,
)
from layouts_cvm.informe_diario_v1 import InformeDiarioV1


VALID_CNPJ = "11222333000181"
PAGE_ORDER = [
    "CNPJ_FDO",
    "VL_TOTAL",
    "VL_QUOTA",
    "PATRIM_LIQ",
    "CAPTC_DIA",
    "RESG_DIA",
    "NR_COTST",
    "LISTA_COTST_SIGNIF",
]


def _inform(**overrides: object) -> InformeDiarioV1Inform:
    fields: dict[str, object] = {
        "cnpj_fdo": VALID_CNPJ,
        "vl_total": "1.239",
        "vl_quota": "1.1234567890129",
        "patrim_liq": "2",
        "captc_dia": "3",
        "resg_dia": "4",
        "nr_cotst": 7,
        "lista_cotst_signif": [
            InformeDiarioV1Shareholder(
                tp_pessoa="PJ", cpf_cnpj_cotst=VALID_CNPJ, pr_cotst="20.12345"
            )
        ],
    }
    fields.update(overrides)
    return InformeDiarioV1Inform(**fields)


def _header() -> InformeDiarioV1Header:
    return InformeDiarioV1Header(dt_compt="15/01/2011", dt_gerac_arq="16/01/2011")


def _doc(inform: InformeDiarioV1Inform | None = None) -> InformeDiarioV1Document:
    return InformeDiarioV1Document(header=_header(), informs=[inform or _inform()])


def _xml(inform: InformeDiarioV1Inform | None = None) -> str:
    xml = InformeDiarioV1().export(_doc(inform))
    assert xml is not None
    return xml


def test_header_tags_in_page_order() -> None:
    """Emit COD_DOC, DT_COMPT, DT_GERAC_ARQ (no VERSAO) in the order of the page template."""
    header = _xml().split("<CAB_INFORM>")[1].split("</CAB_INFORM>")[0]

    assert re.findall(r"<([A-Z_]+)>", header) == ["COD_DOC", "DT_COMPT", "DT_GERAC_ARQ"]


def test_header_model_pins_the_full_field_set() -> None:
    """Pin the V1 header fields so a field added to the V4 header cannot leak into V1."""
    list_fields = list(InformeDiarioV1Header.model_fields)

    assert list_fields == ["cod_doc", "dt_compt", "dt_gerac_arq", "versao"]


@pytest.mark.parametrize("tag", ["<COD_DOC>1</COD_DOC>"])
def test_header_stamps_doc_code(tag: str) -> None:
    """Stamp COD_DOC 1 in the header."""
    assert tag in _xml()


@pytest.mark.parametrize(
    "fragment",
    ['<DOC_ARQ xmlns="urn:infdiario">', "<LISTA_INFORM>\n        <INFORM>"],
)
def test_root_declares_namespace_and_wraps_informs_in_lista_inform(fragment: str) -> None:
    """Open with DOC_ARQ in urn:infdiario and nest each INFORM in LISTA_INFORM."""
    assert fragment in _xml()


def test_inform_tag_order_matches_page() -> None:
    """Emit the INFORM children in the order the page template lists them."""
    body = _xml().split("<INFORM>")[1].split("</INFORM>")[0]
    top_level = re.findall(r"^ {12}<([A-Z_]+)>", body, flags=re.M)

    assert top_level == PAGE_ORDER


@pytest.mark.parametrize(
    "tag",
    [
        "<VL_TOTAL>1,23</VL_TOTAL>",
        "<PATRIM_LIQ>2,00</PATRIM_LIQ>",
        "<VL_QUOTA>1,123456789012</VL_QUOTA>",
        "<PR_COTST>20,1234</PR_COTST>",
    ],
)
def test_decimal_scales_follow_page(tag: str) -> None:
    """Truncate to 2 places (money), 12 (quota) and 4 (participation), comma separator."""
    assert tag in _xml()


@pytest.mark.parametrize(
    "tag",
    ["VERSAO", "VL_TOTAL_SAI", "VL_TOTAL_ATV", "DATA_PROX_PL", "COD_SUBCLASSE", "NOME_FUNDO"],
)
def test_tags_absent_from_v1_are_not_emitted(tag: str) -> None:
    """Never emit tags the V1 sample file lacks."""
    assert tag not in _xml()


def test_cotst_signif_block_nests_under_lista() -> None:
    """Nest TP_PESSOA, CPF_CNPJ_COTST, PR_COTST inside COTST_SIGNIF inside the list."""
    block = _xml().split("<COTST_SIGNIF>")[1].split("</COTST_SIGNIF>")[0]

    assert re.findall(r"<([A-Z_]+)>", block) == ["TP_PESSOA", "CPF_CNPJ_COTST", "PR_COTST"]


@pytest.mark.parametrize("list_cotst", [None, []])
def test_lista_cotst_signif_omitted_when_empty(list_cotst: list | None) -> None:
    """Omit the optional shareholder list when no shareholder reaches 20%."""
    assert "LISTA_COTST_SIGNIF" not in _xml(_inform(lista_cotst_signif=list_cotst))


def test_cod_subclasse_is_rejected() -> None:
    """Reject a subclass code because V1 only knows CNPJ_FDO."""
    with pytest.raises(ValidationError):
        _inform(cod_subclasse="X1")


def test_data_prox_pl_is_rejected() -> None:
    """Reject DATA_PROX_PL, which only later versions define."""
    with pytest.raises(ValidationError):
        _inform(data_prox_pl="16/01/2011")


def test_cnpj_is_required() -> None:
    """Reject an informe without CNPJ_FDO."""
    dict_inform = _inform().model_dump()
    del dict_inform["cnpj_fdo"]
    with pytest.raises(ValidationError):
        InformeDiarioV1Inform(**dict_inform)


def test_invalid_cnpj_check_digit_is_rejected() -> None:
    """Reject a CNPJ whose check digits are wrong."""
    with pytest.raises(ValidationError):
        _inform(cnpj_fdo="11222333000182")


def test_negative_cotst_count_is_rejected() -> None:
    """Reject a negative quotaholder count."""
    with pytest.raises(ValidationError):
        _inform(nr_cotst=-1)


@pytest.mark.parametrize("field", ["vl_total_sai", "vl_total_atv"])
def test_v2_only_money_fields_are_rejected(field: str) -> None:
    """Reject VL_TOTAL_SAI / VL_TOTAL_ATV, which the V1 page does not define."""
    with pytest.raises(ValidationError):
        _inform(**{field: "1"})


def test_header_rejects_versao() -> None:
    """Reject a header carrying a VERSAO, which V1 does not define."""
    with pytest.raises(ValidationError):
        InformeDiarioV1Header(dt_compt="15/01/2011", dt_gerac_arq="15/01/2011", versao="2.0")


def test_header_rejects_other_cod_doc() -> None:
    """Reject a header claiming another COD_DOC."""
    with pytest.raises(ValidationError):
        InformeDiarioV1Header(dt_compt="15/01/2011", dt_gerac_arq="15/01/2011", cod_doc=2)


def test_header_rejects_malformed_date() -> None:
    """Reject a competence date that is not DD/MM/AAAA."""
    with pytest.raises(ValidationError):
        InformeDiarioV1Header(dt_compt="2013-01-15", dt_gerac_arq="15/01/2011")


def test_more_than_100_funds_rejected() -> None:
    """Reject a document with more than 100 informes."""
    with pytest.raises(ValidationError):
        InformeDiarioV1Document(header=_header(), informs=[_inform()] * 101)


def test_export_to_file_returns_none(tmp_path: Path) -> None:
    """Return None when an output path is given."""
    assert InformeDiarioV1().export(_doc(), output_path=str(tmp_path / "informe.xml")) is None


def test_export_writes_windows_1252_file(tmp_path: Path) -> None:
    """Write the file as windows-1252, with the page's XML declaration."""
    out = tmp_path / "informe.xml"
    InformeDiarioV1().export(_doc(), output_path=str(out))

    assert (
        out.read_bytes()
        .decode("windows-1252")
        .startswith('<?xml version="1.0" encoding="windows-1252"?>')
    )


def test_export_file_matches_returned_string(tmp_path: Path) -> None:
    """Write exactly the text export returns."""
    out = tmp_path / "informe.xml"
    InformeDiarioV1().export(_doc(), output_path=str(out))

    assert out.read_bytes().decode("windows-1252") == _xml()


def test_writer_rejects_a_non_v1_document() -> None:
    """Refuse an object that is not an InformeDiarioV1Document (runtime type check)."""
    with pytest.raises(TypeError):
        InformeDiarioV1().export("not a document")  # type: ignore[arg-type]


def test_export_plain_data_equals_model_export() -> None:
    """A dict from a valid document's ``model_dump`` exports the same XML as the model."""
    doc = _doc()

    assert InformeDiarioV1().export(doc.model_dump()) == InformeDiarioV1().export(doc)


def test_header_rejects_unknown_field() -> None:
    """Reject a stray header key instead of silently dropping it from the XML."""
    with pytest.raises(ValidationError):
        InformeDiarioV1Header(dt_compt="15/01/2011", dt_gerac_arq="16/01/2011", nome_adm="x")


def test_document_rejects_unknown_field() -> None:
    """Reject a stray top-level key in a plain mapping."""
    dict_doc = _doc().model_dump() | {"foo": 1}
    with pytest.raises(ValidationError):
        InformeDiarioV1().export(dict_doc)


def test_several_informs_stay_inside_one_lista_inform() -> None:
    """Emit one INFORM per fund, in order, inside a single LISTA_INFORM."""
    doc = InformeDiarioV1Document(
        header=_header(), informs=[_inform(), _inform(cnpj_fdo="11444777000161")]
    )
    xml = InformeDiarioV1().export(doc)

    assert re.findall(r"<CNPJ_FDO>(\d+)</CNPJ_FDO>", xml) == [VALID_CNPJ, "11444777000161"]


def test_exactly_100_funds_are_accepted() -> None:
    """Accept the page's maximum of 100 funds in one file."""
    doc = InformeDiarioV1Document(header=_header(), informs=[_inform()] * 100)

    assert len(doc.informs) == 100


def test_shareholder_rejects_unknown_field() -> None:
    """Reject a stray key on a shareholder instead of dropping it from the XML."""
    dict_inform = _inform().model_dump()
    dict_inform["lista_cotst_signif"][0]["foo"] = 1
    with pytest.raises(ValidationError):
        InformeDiarioV1Inform(**dict_inform)


def test_several_informs_share_one_lista_inform_wrapper() -> None:
    """Open LISTA_INFORM exactly once however many funds follow."""
    doc = InformeDiarioV1Document(header=_header(), informs=[_inform(), _inform()])

    assert InformeDiarioV1().export(doc).count("<LISTA_INFORM>") == 1
