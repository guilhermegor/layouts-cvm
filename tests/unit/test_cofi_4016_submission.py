"""Unit tests for the COFI 4016 fixed-width writer.

Expected records are typed from the column table of PadraoCOFI.aspx, not derived from the code.
"""

from decimal import Decimal
from pathlib import Path

from pydantic import ValidationError
import pytest

from layouts_cvm import Cofi4016


CNPJ = "11222333000181"
OTHER_CNPJ = "11444777000161"


def _doc(list_funds: list[dict] | None = None) -> dict:
    """Build a one-fund document."""
    return {
        "dt_compt": "03/2026",
        "fundos": list_funds
        or [
            {
                "cnpj_fundo": CNPJ,
                "contas": [
                    {
                        "conta": "0010000007",
                        "total": "1234.56",
                        "ate_90_dias": Decimal("-0.99"),
                    }
                ],
            }
        ],
    }


def _lines(dict_doc: dict) -> list[str]:
    """Export and split into records."""
    return (Cofi4016().export(dict_doc) or "").split("\r\n")[:-1]


def test_export_records_have_71_columns() -> None:
    """Every record is 71 columns wide."""
    assert {len(str_line) for str_line in _lines(_doc())} == {71}


def test_export_header_matches_page_layout() -> None:
    """The header follows the page column table."""
    assert _lines(_doc())[0] == "#C14016" + CNPJ + " " * 8 + "032026" + " " * 36


def test_export_account_matches_page_layout() -> None:
    """The account record follows the page column table."""
    str_expected = (
        "0010000007" + " " * 4 + "000000000000123456+" + "000000000000000099-" + "0" * 18 + "+"
    )
    assert _lines(_doc())[1] == str_expected


def test_export_footer_counts_all_records() -> None:
    """The footer counts every record, itself included."""
    assert _lines(_doc())[-1] == "@1000003" + " " * 63


def test_export_multiple_funds_writes_one_footer() -> None:
    """Two funds yield two headers and one footer."""
    list_funds = [
        {"cnpj_fundo": c, "contas": [{"conta": "0010000007"}]} for c in (CNPJ, OTHER_CNPJ)
    ]
    list_lines = _lines(_doc(list_funds))
    assert [s[:2] for s in list_lines] == ["#C", "00", "#C", "00", "@1"]


def test_export_truncates_excess_scale() -> None:
    """Digits beyond two decimals are truncated, not rounded."""
    str_line = _lines(
        _doc([{"cnpj_fundo": CNPJ, "contas": [{"conta": "0010000007", "total": "1.999"}]}])
    )[1]
    assert str_line[14:33] == "000000000000000199+"


def test_export_writes_file(tmp_path: Path) -> None:
    """The file holds exactly the returned text."""
    str_path = str(tmp_path / "balanco.cvm")
    Cofi4016().export(_doc(), str_path)
    assert (tmp_path / "balanco.cvm").read_bytes() == (Cofi4016().export(_doc()) or "").encode()


@pytest.mark.parametrize(
    "dict_patch",
    [
        {"dt_compt": "13/2026"},
        {"dt_compt": "3/2026"},
        {"fundos": []},
        {"fundos": [{"cnpj_fundo": "11111111111111", "contas": [{"conta": "0010000007"}]}]},
        {"fundos": [{"cnpj_fundo": CNPJ, "contas": [{"conta": "10000007"}]}]},
        {"fundos": [{"cnpj_fundo": CNPJ, "contas": [{"conta": "0010000007", "total": 1.5}]}]},
        {"fundos": [{"cnpj_fundo": CNPJ, "contas": [{"conta": "0010000007", "total": "NaN"}]}]},
        {
            "fundos": [
                {"cnpj_fundo": CNPJ, "contas": [{"conta": "0010000007", "total": "Infinity"}]}
            ]
        },
    ],
)
def test_export_invalid_document_is_rejected(dict_patch: dict) -> None:
    """Each invalid document fails validation."""
    with pytest.raises(ValidationError):
        Cofi4016().export({**_doc(), **dict_patch})


def test_export_negative_value_truncating_to_zero_is_positive() -> None:
    """A magnitude below one cent renders as zero with a plus sign."""
    str_line = _lines(
        _doc([{"cnpj_fundo": CNPJ, "contas": [{"conta": "0010000007", "total": "-0.001"}]}])
    )[1]
    assert str_line[14:33] == "0" * 18 + "+"


def test_export_alphanumeric_cnpj_in_header() -> None:
    """A 2026 alphanumeric CNPJ keeps its 14 columns in the header."""
    str_cnpj = "12ABC34501DE35"
    str_header = _lines(_doc([{"cnpj_fundo": str_cnpj, "contas": [{"conta": "0010000007"}]}]))[0]
    assert str_header == "#C14016" + str_cnpj + " " * 8 + "032026" + " " * 36


def test_export_over_record_limit_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """More records than the 6-digit footer holds raises."""
    monkeypatch.setattr("layouts_cvm.cofi_4016._MAX_RECORDS", 2)
    with pytest.raises(ValueError, match="at most"):
        Cofi4016().export(_doc())


def test_pad_rejects_overflow() -> None:
    """Content wider than 71 columns is never silently emitted."""
    from layouts_cvm.cofi_4016 import _pad

    with pytest.raises(ValueError, match="at most"):
        _pad("x" * 72)
