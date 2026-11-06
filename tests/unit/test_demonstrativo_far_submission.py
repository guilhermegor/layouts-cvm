"""Unit tests for the FAR submission writer.

Expected tags and order are typed from the CVM page (``PadraoXMLFAR.asp``). ``TABLE_A``
below pins the schema's Table A as a literal copy (it is not imported), so an edit to either
side fails here; it was not re-checked against the live page.
"""

import contextlib
from pathlib import Path
import re
from xml.etree import ElementTree as ET  # noqa: S405

from pydantic import ValidationError
import pytest

from layouts_cvm import DemonstrativoFar
from layouts_cvm._internal.config.schemas.demonstrativo_far import (
    DemonstrativoFarDocument,
    find_missing_codes,
)


CNPJ_ADM = "11222333000181"
CNPJ_A = "11444777000161"
CNPJ_B = "11222333000181"
DESC = {"cnpj_adm": CNPJ_ADM, "dt_compt": "06/2017", "dt_gerac_arq": "15/07/2017"}


def _fund(cnpj: str = CNPJ_A, **over: object) -> dict:
    base = {
        "cnpj_fundo": cnpj,
        "nr_quota_circul_ult_dia_mes": "1000.5",
        "vl_quota_ult_dia_mes": "12.12345678901",
        "nr_total_quotst_ult_dia_mes": 40,
        "doc_mov_mes": {
            "row_mov_por_fundo": [
                {"cd_mov": 53, "vl_entr": 10},
                {"cd_mov": 54, "vl_saida": 4},
            ]
        },
    }
    base.update(over)
    return base


def _doc(*funds: dict) -> dict:
    return {"desc_adm": DESC, "far": {"row_registro_movimento": list(funds) or [_fund()]}}


def _xml(doc: dict) -> ET.Element:
    return ET.fromstring(DemonstrativoFar().export(doc).encode("windows-1252"))  # noqa: S314


def test_declaration_and_no_namespace() -> None:
    """Export starts with the windows-1252 declaration; root has no namespace."""
    text = DemonstrativoFar().export(_doc())
    assert text.startswith('<?xml version="1.0" encoding="windows-1252"?>\n<DOC_ARQ>')


def test_root_children_in_page_order() -> None:
    """Root children are DESC_ADM then FAR."""
    assert [c.tag for c in _xml(_doc())] == ["DESC_ADM", "FAR"]


def test_desc_adm_tags_and_cod_doc() -> None:
    """DESC_ADM tags in page order, COD_DOC is 4."""
    node = _xml(_doc())[0]
    assert [(c.tag, c.text) for c in node] == [
        ("COD_DOC", "4"),
        ("CNPJ_ADM", CNPJ_ADM),
        ("DT_COMPT", "06/2017"),
        ("DT_GERAC_ARQ", "15/07/2017"),
    ]


def test_fund_tags_without_distribution() -> None:
    """Without distribution the three distribution tags are omitted."""
    row = _xml(_doc())[1][0]
    assert [c.tag for c in row] == [
        "CNPJ_FUNDO",
        "NR_QUOTA_CIRCUL_ULT_DIA_MES",
        "VL_QUOTA_ULT_DIA_MES",
        "NR_TOTAL_QUOTST_ULT_DIA_MES",
        "DOC_MOV_MES",
    ]


def test_fund_tags_with_distribution_in_page_order() -> None:
    """With distribution: VL_ULT_DISTR_QUOTA, DT_DISTR, VL_QUOTA_DT_ULT_DISTR."""
    fund = _fund(vl_ult_distr_quota="1", dt_distr="10/06/2017", vl_quota_dt_ult_distr="2")
    assert [c.tag for c in _xml(_doc(fund))[1][0]][4:7] == [
        "VL_ULT_DISTR_QUOTA",
        "DT_DISTR",
        "VL_QUOTA_DT_ULT_DISTR",
    ]


def test_decimals_use_comma_and_ten_places_truncated() -> None:
    """Decimals: comma separator, 10 places, truncated."""
    row = _xml(_doc())[1][0]
    assert [row[1].text, row[2].text] == ["1000,5000000000", "12,1234567890"]


def test_movement_rows() -> None:
    """Movements serialize under DOC_MOV_MES/ROW_MOV_POR_FUNDO, N columns omitted."""
    rows = list(_xml(_doc())[1][0].find("DOC_MOV_MES"))
    assert [[(c.tag, c.text) for c in r] for r in rows] == [
        [("CD_MOV", "53"), ("VL_ENTR", "10")],
        [("CD_MOV", "54"), ("VL_SAIDA", "4")],
    ]


def test_several_funds_repeat_row() -> None:
    """Each fund is one ROW_REGISTRO_MOVIMENTO."""
    assert len(_xml(_doc(_fund(CNPJ_A), _fund(CNPJ_B)))[1]) == 2


def test_mapping_and_model_give_same_bytes() -> None:
    """A mapping and its model serialise identically."""
    d = _doc()
    assert DemonstrativoFar().export(d) == DemonstrativoFar().export(
        DemonstrativoFarDocument.model_validate(d)
    )


def test_output_path_writes_file_and_returns_none(tmp_path: Path) -> None:
    """With output_path the file is written and None returned."""
    path = tmp_path / "far.xml"
    assert (DemonstrativoFar().export(_doc(), str(path)), path.exists()) == (None, True)


TABLE_A = {
    37: "ES", 48: "ES", 53: "E-", 54: "-S", 55: "ES", 56: "E-", 57: "E-", 58: "E-",
    60: "E-", 61: "-S", 62: "-S", 63: "-S", 64: "-S", 65: "-S", 66: "-S", 67: "E-",
    68: "-S", 69: "-S", 70: "ES", 71: "E-", 72: "-S", 73: "-S", 74: "ES", 75: "ES",
    77: "ES", 78: "ES", 144: "E-", 145: "ES", 150: "-S",
}  # fmt: skip


def _movement(code: int, has_in: bool, has_out: bool) -> dict:
    return {
        "cd_mov": code,
        **dict([("vl_entr", 1)][: int(has_in)]),
        **dict([("vl_saida", 1)][: int(has_out)]),
    }


def _accepts(row: dict) -> bool:
    doc = _doc(_fund(doc_mov_mes={"row_mov_por_fundo": [row]}))
    return not _raises_validation(doc)


def _raises_validation(doc: dict) -> bool:
    with contextlib.suppress(ValidationError):
        DemonstrativoFar().export(doc)
        return False
    return True


def test_table_a_has_29_codes() -> None:
    """The pinned table has the 29 codes of Table A."""
    assert len(TABLE_A) == 29


@pytest.mark.parametrize("code", sorted(TABLE_A))
def test_table_a_accepts_only_the_declared_columns(code: int) -> None:
    """Each code accepts exactly its (entrada, saida) pattern and no other."""
    want = (TABLE_A[code][0] == "E", TABLE_A[code][1] == "S")
    got = {(i, o) for i in (False, True) for o in (False, True) if _accepts(_movement(code, i, o))}
    assert got == {want}


@pytest.mark.parametrize("bad", ["-1", "-0.5"])
def test_negative_decimal_is_rejected(bad: str) -> None:
    """Quota counts and values cannot be negative."""
    with pytest.raises(ValidationError):
        DemonstrativoFar().export(_doc(_fund(vl_quota_ult_dia_mes=bad)))


@pytest.mark.parametrize("zero", ["-0", "-0.00000000001"])
def test_negative_zero_is_written_as_plain_zero(zero: str) -> None:
    """A value truncating to negative zero serialises without a minus sign."""
    xml = DemonstrativoFar().export(_doc(_fund(nr_quota_circul_ult_dia_mes=zero)))
    assert "<NR_QUOTA_CIRCUL_ULT_DIA_MES>0,0000000000<" in xml


@pytest.mark.parametrize("bad", ["NaN", "Infinity", "", True])
def test_sentinel_decimals_are_validation_errors(bad: object) -> None:
    """Non-numeric sentinels never reach the XML or raise decimal.InvalidOperation."""
    with pytest.raises(ValidationError):
        DemonstrativoFar().export(_doc(_fund(nr_quota_circul_ult_dia_mes=bad)))


@pytest.mark.parametrize(
    ("field", "ok"),
    [("nr_quota_circul_ult_dia_mes", "9" * 18), ("nr_total_quotst_ult_dia_mes", 999_999_999_999)],
)
def test_value_at_the_limit_is_accepted(field: str, ok: object) -> None:
    """The documented maximum passes."""
    assert DemonstrativoFar().export(_doc(_fund(**{field: ok})))


@pytest.mark.parametrize(
    ("field", "over"),
    [
        ("nr_quota_circul_ult_dia_mes", "1" + "0" * 18),
        ("nr_total_quotst_ult_dia_mes", 1_000_000_000_000),
    ],
)
def test_value_over_the_limit_is_rejected(field: str, over: object) -> None:
    """One more than the maximum is a ValidationError."""
    with pytest.raises(ValidationError):
        DemonstrativoFar().export(_doc(_fund(**{field: over})))


@pytest.mark.parametrize("field", ["nr_total_quotst_ult_dia_mes"])
def test_negative_integer_is_rejected(field: str) -> None:
    """Integer fields refuse negatives like the decimals."""
    with pytest.raises(ValidationError):
        DemonstrativoFar().export(_doc(_fund(**{field: -1})))


@pytest.mark.parametrize("row", [{"cd_mov": 53, "vl_entr": -1}, {"cd_mov": True, "vl_entr": 1}])
def test_negative_flow_and_bool_code_are_rejected(row: dict) -> None:
    """A negative inflow and a bool cd_mov are both refused."""
    assert not _accepts(row)


def test_explicit_none_distribution_is_accepted() -> None:
    """An explicit None on an optional decimal means absent, not an error."""
    assert DemonstrativoFar().export(_doc(_fund(vl_ult_distr_quota=None)))


def test_alphanumeric_cnpj_is_accepted() -> None:
    """The 2026 alphanumeric CNPJ passes the fund CNPJ check."""
    assert DemonstrativoFar().export(_doc(_fund(cnpj_fundo="12ABC34501DE35")))


@pytest.mark.parametrize("bad", ["1" + "0" * 30, "1" + "0" * 19])
def test_oversized_decimal_is_a_validation_error(bad: str) -> None:
    """Too many integer digits raises ValidationError, not decimal.InvalidOperation."""
    with pytest.raises(ValidationError):
        DemonstrativoFar().export(_doc(_fund(nr_quota_circul_ult_dia_mes=bad)))


@pytest.mark.parametrize("bad", ["53", 53.0])
def test_cd_mov_is_strict(bad: object) -> None:
    """cd_mov rejects strings and floats like the other integers."""
    row = {"cd_mov": bad, "vl_entr": 1}
    assert not _accepts(row)


def _bad_movements(*rows: dict) -> dict:
    return _fund(doc_mov_mes={"row_mov_por_fundo": list(rows)})


@pytest.mark.parametrize(
    "doc",
    [
        _doc(_bad_movements({"cd_mov": 999, "vl_entr": 1})),
        _doc(_bad_movements({"cd_mov": 53})),
        _doc(_bad_movements({"cd_mov": 53, "vl_entr": 1, "vl_saida": 1})),
        _doc(_bad_movements({"cd_mov": 54, "vl_entr": 1, "vl_saida": 1})),
        _doc(_bad_movements({"cd_mov": 53, "vl_entr": 1}, {"cd_mov": 53, "vl_entr": 2})),
        _doc(_fund(vl_ult_distr_quota="1")),
        _doc(_fund(CNPJ_A), _fund(CNPJ_A)),
        _doc(_fund(cnpj_fundo="11222333000182")),
        _doc(_fund(nr_quota_circul_ult_dia_mes=1.5)),
        {"desc_adm": {**DESC, "dt_compt": "13/2017"}, "far": _doc()["far"]},
        {"desc_adm": {**DESC, "cod_doc": 5}, "far": _doc()["far"]},
        {"desc_adm": DESC, "far": {"row_registro_movimento": []}},
    ],
)
def test_invalid_documents_are_rejected(doc: dict) -> None:
    """Rule violations raise ValidationError."""
    with pytest.raises(ValidationError):
        DemonstrativoFar().export(doc)


def _all_codes_fund(cnpj: str = CNPJ_A) -> dict:
    list_rows = [
        _movement(code, pair[0] == "E", pair[1] == "S") for code, pair in sorted(TABLE_A.items())
    ]
    return _fund(cnpj, doc_mov_mes={"row_mov_por_fundo": list_rows})


def test_flag_off_accepts_a_fund_with_two_movements() -> None:
    """Without the flag a fund with two movements is accepted."""
    assert DemonstrativoFar().export(_doc())


def test_flag_on_accepts_a_fund_using_every_code() -> None:
    """With the flag a fund using all 29 codes is accepted."""
    assert DemonstrativoFar().export(_doc(_all_codes_fund()), require_all_movements=True)


def test_flag_on_rejects_missing_codes_naming_fund_and_codes() -> None:
    """The message names the CNPJ and the missing codes ascending."""
    list_missing = sorted(set(TABLE_A) - {53, 54})
    with pytest.raises(ValueError, match=f"{CNPJ_A}.*{re.escape(str(list_missing))}"):
        DemonstrativoFar().export(_doc(), require_all_movements=True)


def test_flag_on_reports_every_incomplete_fund() -> None:
    """Two incomplete funds are both named in one error."""
    with pytest.raises(ValueError, match=f"{CNPJ_A}.*{CNPJ_B}"):
        DemonstrativoFar().export(_doc(_fund(CNPJ_A), _fund(CNPJ_B)), require_all_movements=True)


def test_flag_on_rejects_a_built_model() -> None:
    """A built model is checked too, not only a mapping."""
    cls_model = DemonstrativoFarDocument.model_validate(_doc())
    with pytest.raises(ValueError, match="does not use Table A codes"):
        DemonstrativoFar().export(cls_model, require_all_movements=True)


def test_pinned_table_a_has_29_codes() -> None:
    """The independent Table A copy has 29 codes."""
    assert len(TABLE_A) == 29


@pytest.mark.parametrize("int_code", [53, 54])
def test_required_set_equals_table_a(int_code: int) -> None:
    """A fund using one code misses every other code of the pinned TABLE_A."""
    str_pair = TABLE_A[int_code]
    dict_row = _movement(int_code, str_pair[0] == "E", str_pair[1] == "S")
    dict_fund = _fund(doc_mov_mes={"row_mov_por_fundo": [dict_row]})
    cls_registro = DemonstrativoFarDocument.model_validate(
        _doc(dict_fund)
    ).far.row_registro_movimento[0]
    assert set(find_missing_codes(cls_registro)) == set(TABLE_A) - {int_code}
