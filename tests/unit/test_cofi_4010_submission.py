"""Unit tests for the COFI 4010 fixed-width writer.

Expected records are typed by hand from the PadraoCOFI page's column positions.
"""

from pathlib import Path

from pydantic import ValidationError
import pytest

from layouts_cvm import Cofi4010


CNPJ = "11222333000181"
OTHER_CNPJ = "11444777000161"
ACCOUNT = {"conta": "1000000001", "total": "1234.56", "ate_90_dias": "-0.5", "apos_90_dias": "0"}


def _fund(cnpj: str = CNPJ, **overrides: object) -> dict[str, object]:
    """Build one valid fund mapping; overrides replace fields."""
    base: dict[str, object] = {"cnpj_fundo": cnpj, "competencia": "062026", "contas": [ACCOUNT]}
    base.update(overrides)
    return base


def _lines(list_funds: list[dict[str, object]]) -> list[str]:
    """Export funds and split the text into records."""
    return Cofi4010().export({"fundos": list_funds}).splitlines()


def test_export_header_matches_page_positions() -> None:
    """The header follows the page positions."""
    assert _lines([_fund()])[0] == f"#C14010{CNPJ}" + " " * 8 + "062026" + " " * 36


def test_export_account_matches_page_positions() -> None:
    """The account follows the page positions."""
    assert _lines([_fund()])[1] == (
        "1000000001" + " " * 4 + "000000000000123456 " + "000000000000000050-" + "0" * 18 + " "
    )


def test_export_footer_counts_every_record_including_controls() -> None:
    """The footer counts every record, controls included."""
    assert _lines([_fund()])[-1] == "@1000003" + " " * 63


def test_export_every_record_has_71_positions() -> None:
    """Every record is 71 positions long."""
    assert {len(str_line) for str_line in _lines([_fund()])} == {71}


def test_export_two_funds_share_one_footer() -> None:
    """Two funds share one footer holding the total count."""
    assert _lines([_fund(), _fund(OTHER_CNPJ)])[-1].startswith("@1000005")


def test_export_writes_ascii_file_to_disk(tmp_path: Path) -> None:
    """The file on disk equals the returned text."""
    path_out = tmp_path / "balancete.cvm"
    Cofi4010().export({"fundos": [_fund()]}, str(path_out))
    assert path_out.read_bytes() == Cofi4010().export({"fundos": [_fund()]}).encode("ascii")


@pytest.mark.parametrize(
    "dict_bad",
    [
        _fund(cnpj="11222333000182"),
        _fund(competencia="132026"),
        _fund(contas=[]),
        _fund(cod_doc="4016"),
        _fund(contas=[{**ACCOUNT, "conta": "123"}]),
    ],
)
def test_export_rejects_invalid_input(dict_bad: dict[str, object]) -> None:
    """Invalid input is rejected by validation."""
    with pytest.raises(ValidationError):
        Cofi4010().export({"fundos": [dict_bad]})
