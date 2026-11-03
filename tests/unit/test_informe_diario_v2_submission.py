"""Unit tests for the Informe Diário V2 submission writer.

Pin the tag order, the LISTA_INFORM wrapper and the decimal scales to
PadraoXMLInfoDiarioNet739.asp, and cover the V2-only rules (VERSAO 2.0, CNPJ_FDO only,
no DATA_PROX_PL).
"""

from pathlib import Path
import re

from pydantic import ValidationError
import pytest

from layouts_cvm import InformeDiarioV2
from layouts_cvm._internal.config.schemas.informe_diario import SignificantShareholder
from layouts_cvm._internal.config.schemas.informe_diario_v2 import (
    InformeDiarioV2Document,
    InformeDiarioV2Header,
    InformeDiarioV2Inform,
)


VALID_CNPJ = "11222333000181"
PAGE_ORDER = [
    "CNPJ_FDO",
    "VL_TOTAL",
    "VL_QUOTA",
    "PATRIM_LIQ",
    "CAPTC_DIA",
    "RESG_DIA",
    "VL_TOTAL_SAI",
    "VL_TOTAL_ATV",
    "NR_COTST",
    "LISTA_COTST_SIGNIF",
]


def _inform(**overrides: object) -> InformeDiarioV2Inform:
    fields: dict[str, object] = {
        "cnpj_fdo": VALID_CNPJ,
        "vl_total": "1.239",
        "vl_quota": "1.1234567890129",
        "patrim_liq": "2",
        "captc_dia": "3",
        "resg_dia": "4",
        "vl_total_sai": "5",
        "vl_total_atv": "6",
        "nr_cotst": 7,
        "lista_cotst_signif": [
            SignificantShareholder(tp_pessoa="PJ", cpf_cnpj_cotst=VALID_CNPJ, pr_cotst="20.12345")
        ],
    }
    fields.update(overrides)
    return InformeDiarioV2Inform(**fields)


def _header() -> InformeDiarioV2Header:
    return InformeDiarioV2Header(dt_compt="15/01/2013", dt_gerac_arq="16/01/2013")


def _doc(inform: InformeDiarioV2Inform | None = None) -> InformeDiarioV2Document:
    return InformeDiarioV2Document(header=_header(), informs=[inform or _inform()])


def _xml(inform: InformeDiarioV2Inform | None = None) -> str:
    xml = InformeDiarioV2().export(_doc(inform))
    assert xml is not None
    return xml


def test_header_tags_in_page_order() -> None:
    """Emit COD_DOC, DT_COMPT, DT_GERAC_ARQ, VERSAO in the order of the page template."""
    header = _xml().split("<CAB_INFORM>")[1].split("</CAB_INFORM>")[0]

    assert re.findall(r"<([A-Z_]+)>", header) == ["COD_DOC", "DT_COMPT", "DT_GERAC_ARQ", "VERSAO"]


@pytest.mark.parametrize("tag", ["<VERSAO>2.0</VERSAO>", "<COD_DOC>1</COD_DOC>"])
def test_header_stamps_v2_version_and_doc_code(tag: str) -> None:
    """Stamp VERSAO 2.0 and COD_DOC 1 in the header."""
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


@pytest.mark.parametrize("tag", ["DATA_PROX_PL", "COD_SUBCLASSE", "NOME_FUNDO"])
def test_tags_absent_from_v2_are_not_emitted(tag: str) -> None:
    """Never emit tags the V2 sample file lacks."""
    assert tag not in _xml()


def test_cotst_signif_block_nests_under_lista() -> None:
    """Nest TP_PESSOA, CPF_CNPJ_COTST, PR_COTST inside COTST_SIGNIF inside the list."""
    block = _xml().split("<COTST_SIGNIF>")[1].split("</COTST_SIGNIF>")[0]

    assert re.findall(r"<([A-Z_]+)>", block) == ["TP_PESSOA", "CPF_CNPJ_COTST", "PR_COTST"]


def test_lista_cotst_signif_omitted_when_empty() -> None:
    """Omit the optional shareholder list when no shareholder reaches 20%."""
    assert "LISTA_COTST_SIGNIF" not in _xml(_inform(lista_cotst_signif=None))


def test_cod_subclasse_is_rejected() -> None:
    """Reject a subclass code because V2 only knows CNPJ_FDO."""
    with pytest.raises(ValidationError):
        _inform(cod_subclasse="X1")


def test_data_prox_pl_is_rejected() -> None:
    """Reject DATA_PROX_PL, which only later versions define."""
    with pytest.raises(ValidationError):
        _inform(data_prox_pl="16/01/2013")


def test_cnpj_is_required() -> None:
    """Reject an informe without CNPJ_FDO."""
    with pytest.raises(ValidationError):
        _inform(cnpj_fdo=None)


def test_invalid_cnpj_check_digit_is_rejected() -> None:
    """Reject a CNPJ whose check digits are wrong."""
    with pytest.raises(ValidationError):
        _inform(cnpj_fdo="11222333000182")


def test_negative_cotst_count_is_rejected() -> None:
    """Reject a negative quotaholder count."""
    with pytest.raises(ValidationError):
        _inform(nr_cotst=-1)


def test_header_rejects_other_versao() -> None:
    """Reject a header claiming another VERSAO."""
    with pytest.raises(ValidationError):
        InformeDiarioV2Header(dt_compt="15/01/2013", dt_gerac_arq="15/01/2013", versao="3.0")


def test_header_rejects_other_cod_doc() -> None:
    """Reject a header claiming another COD_DOC."""
    with pytest.raises(ValidationError):
        InformeDiarioV2Header(dt_compt="15/01/2013", dt_gerac_arq="15/01/2013", cod_doc=2)


def test_header_rejects_malformed_date() -> None:
    """Reject a competence date that is not DD/MM/AAAA."""
    with pytest.raises(ValidationError):
        InformeDiarioV2Header(dt_compt="2013-01-15", dt_gerac_arq="15/01/2013")


def test_more_than_100_funds_rejected() -> None:
    """Reject a document with more than 100 informes."""
    with pytest.raises(ValidationError):
        InformeDiarioV2Document(header=_header(), informs=[_inform()] * 101)


def test_export_to_file_returns_none(tmp_path: Path) -> None:
    """Return None when an output path is given."""
    assert InformeDiarioV2().export(_doc(), output_path=str(tmp_path / "informe.xml")) is None


def test_export_writes_windows_1252_file(tmp_path: Path) -> None:
    """Write the file as windows-1252, with the page's XML declaration."""
    out = tmp_path / "informe.xml"
    InformeDiarioV2().export(_doc(), output_path=str(out))

    assert (
        out.read_bytes()
        .decode("windows-1252")
        .startswith('<?xml version="1.0" encoding="windows-1252"?>')
    )


def test_export_file_matches_returned_string(tmp_path: Path) -> None:
    """Write exactly the text export returns."""
    out = tmp_path / "informe.xml"
    InformeDiarioV2().export(_doc(), output_path=str(out))

    assert out.read_bytes().decode("windows-1252") == _xml()


def test_writer_rejects_a_non_v2_document() -> None:
    """Refuse an object that is not an InformeDiarioV2Document (runtime type check)."""
    with pytest.raises(TypeError):
        InformeDiarioV2().export("not a document")  # type: ignore[arg-type]
