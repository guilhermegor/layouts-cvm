"""Unit tests for the Informe Diário submission writer.

Cover the money/validation paths: XML structure, comma-decimal formatting,
ROUND_DOWN truncation, check-digit CNPJ rejection, the CNPJ_FDO xor
COD_SUBCLASSE rule, and the significant-shareholder block.
"""

from pathlib import Path

from pydantic import ValidationError
import pytest

from layouts_cvm import InformeDiario
from layouts_cvm._internal.config.schemas.informe_diario import (
    InformeDiarioDocument,
    InformeDiarioHeader,
    InformeDiarioInform,
    SignificantShareholder,
)


VALID_CNPJ = "11222333000181"


def _minimal_inform(vl_quota: str = "0", **overrides: object) -> InformeDiarioInform:
    """Build a minimal valid INFORM exercising only the mandatory fields."""
    fields: dict[str, object] = {
        "cnpj_fdo": VALID_CNPJ,
        "data_prox_pl": "16/01/2025",
        "vl_total": "0",
        "vl_quota": vl_quota,
        "patrim_liq": "0",
        "captc_dia": "0",
        "resg_dia": "0",
        "vl_total_sai": "0",
        "vl_total_atv": "0",
        "nr_cotst": 0,
    }
    fields.update(overrides)
    return InformeDiarioInform(**fields)


def _document(inform: InformeDiarioInform) -> InformeDiarioDocument:
    """Wrap an informe in a document with a valid header."""
    header = InformeDiarioHeader(dt_compt="15/01/2025", dt_gerac_arq="15/01/2025")
    return InformeDiarioDocument(header=header, informs=[inform])


def test_export_minimal_document_renders_expected_structure_1() -> None:
    """Emit the CVM document envelope, the INFORM block, and the fund CNPJ."""
    xml = InformeDiario().export(_document(_minimal_inform()))
    assert xml is not None


def test_export_minimal_document_renders_expected_structure_2() -> None:
    """Emit the CVM document envelope, the INFORM block, and the fund CNPJ."""
    xml = InformeDiario().export(_document(_minimal_inform()))
    assert 'xmlns="urn:infdiario"' in xml


def test_export_minimal_document_renders_expected_structure_3() -> None:
    """Emit the CVM document envelope, the INFORM block, and the fund CNPJ."""
    xml = InformeDiario().export(_document(_minimal_inform()))
    assert "<CAB_INFORM>" in xml


def test_export_minimal_document_renders_expected_structure_4() -> None:
    """Emit the CVM document envelope, the INFORM block, and the fund CNPJ."""
    xml = InformeDiario().export(_document(_minimal_inform()))
    assert "<COD_DOC>1</COD_DOC>" in xml


def test_export_minimal_document_renders_expected_structure_5() -> None:
    """Emit the CVM document envelope, the INFORM block, and the fund CNPJ."""
    xml = InformeDiario().export(_document(_minimal_inform()))
    assert "<INFORM>" in xml


def test_export_minimal_document_renders_expected_structure_6() -> None:
    """Emit the CVM document envelope, the INFORM block, and the fund CNPJ."""
    xml = InformeDiario().export(_document(_minimal_inform()))
    assert f"<CNPJ_FDO>{VALID_CNPJ}</CNPJ_FDO>" in xml


def test_export_minimal_document_renders_expected_structure_7() -> None:
    """Emit the CVM document envelope, the INFORM block, and the fund CNPJ."""
    xml = InformeDiario().export(_document(_minimal_inform()))
    assert "<PATRIM_LIQ>0,00</PATRIM_LIQ>" in xml


def test_export_quota_renders_twelve_decimals_1() -> None:
    """VL_QUOTA renders with the standard's up-to-12-place scale, comma-separated."""
    xml = InformeDiario().export(_document(_minimal_inform(vl_quota="1.5")))
    assert xml is not None


def test_export_quota_renders_twelve_decimals_2() -> None:
    """VL_QUOTA renders with the standard's up-to-12-place scale, comma-separated."""
    xml = InformeDiario().export(_document(_minimal_inform(vl_quota="1.5")))
    assert "<VL_QUOTA>1,500000000000</VL_QUOTA>" in xml


def test_export_truncates_excess_precision_round_down_1() -> None:
    """A value with excess precision is truncated toward zero, never rounded up."""
    xml = InformeDiario().export(_document(_minimal_inform(vl_total="10.999")))
    assert xml is not None


def test_export_truncates_excess_precision_round_down_2() -> None:
    """A value with excess precision is truncated toward zero, never rounded up."""
    xml = InformeDiario().export(_document(_minimal_inform(vl_total="10.999")))
    assert "<VL_TOTAL>10,99</VL_TOTAL>" in xml


def test_export_truncates_excess_precision_round_down_3() -> None:
    """A value with excess precision is truncated toward zero, never rounded up."""
    xml = InformeDiario().export(_document(_minimal_inform(vl_total="10.999")))
    assert "11,00" not in xml


def test_invalid_cnpj_is_rejected() -> None:
    """A CNPJ that fails the check digits raises a validation error."""
    with pytest.raises(ValidationError):
        _minimal_inform(cnpj_fdo="12345678000100")


def test_both_fund_identifiers_is_rejected() -> None:
    """Providing both CNPJ_FDO and COD_SUBCLASSE violates the xor rule."""
    with pytest.raises(ValidationError):
        _minimal_inform(cod_subclasse="SUB123")


def test_neither_fund_identifier_is_rejected() -> None:
    """Providing neither CNPJ_FDO nor COD_SUBCLASSE violates the xor rule."""
    with pytest.raises(ValidationError):
        _minimal_inform(cnpj_fdo=None)


def test_subclasse_informe_renders_cod_subclasse_1() -> None:
    """A subclass informe carries COD_SUBCLASSE and omits CNPJ_FDO."""
    inform = _minimal_inform(cnpj_fdo=None, cod_subclasse="SUB123")
    xml = InformeDiario().export(_document(inform))
    assert xml is not None


def test_subclasse_informe_renders_cod_subclasse_2() -> None:
    """A subclass informe carries COD_SUBCLASSE and omits CNPJ_FDO."""
    inform = _minimal_inform(cnpj_fdo=None, cod_subclasse="SUB123")
    xml = InformeDiario().export(_document(inform))
    assert "<COD_SUBCLASSE>SUB123</COD_SUBCLASSE>" in xml


def test_subclasse_informe_renders_cod_subclasse_3() -> None:
    """A subclass informe carries COD_SUBCLASSE and omits CNPJ_FDO."""
    inform = _minimal_inform(cnpj_fdo=None, cod_subclasse="SUB123")
    xml = InformeDiario().export(_document(inform))
    assert "<CNPJ_FDO>" not in xml


def test_significant_shareholder_block_renders_1() -> None:
    """A significant shareholder renders inside LISTA_COTST_SIGNIF with 4-place PR_COTST."""
    cotista = SignificantShareholder(tp_pessoa="PJ", cpf_cnpj_cotst=VALID_CNPJ, pr_cotst="25.5")
    inform = _minimal_inform(nr_cotst=1, lista_cotst_signif=[cotista])
    xml = InformeDiario().export(_document(inform))
    assert xml is not None


def test_significant_shareholder_block_renders_2() -> None:
    """A significant shareholder renders inside LISTA_COTST_SIGNIF with 4-place PR_COTST."""
    cotista = SignificantShareholder(tp_pessoa="PJ", cpf_cnpj_cotst=VALID_CNPJ, pr_cotst="25.5")
    inform = _minimal_inform(nr_cotst=1, lista_cotst_signif=[cotista])
    xml = InformeDiario().export(_document(inform))
    assert "<LISTA_COTST_SIGNIF>" in xml


def test_significant_shareholder_block_renders_3() -> None:
    """A significant shareholder renders inside LISTA_COTST_SIGNIF with 4-place PR_COTST."""
    cotista = SignificantShareholder(tp_pessoa="PJ", cpf_cnpj_cotst=VALID_CNPJ, pr_cotst="25.5")
    inform = _minimal_inform(nr_cotst=1, lista_cotst_signif=[cotista])
    xml = InformeDiario().export(_document(inform))
    assert f"<CPF_CNPJ_COTST>{VALID_CNPJ}</CPF_CNPJ_COTST>" in xml


def test_significant_shareholder_block_renders_4() -> None:
    """A significant shareholder renders inside LISTA_COTST_SIGNIF with 4-place PR_COTST."""
    cotista = SignificantShareholder(tp_pessoa="PJ", cpf_cnpj_cotst=VALID_CNPJ, pr_cotst="25.5")
    inform = _minimal_inform(nr_cotst=1, lista_cotst_signif=[cotista])
    xml = InformeDiario().export(_document(inform))
    assert "<PR_COTST>25,5000</PR_COTST>" in xml


def test_export_writes_file_in_windows_1252_1(tmp_path: Path) -> None:
    """With an output path, export returns None and writes a windows-1252 file.

    Parameters
    ----------
    tmp_path : pathlib.Path
            Pytest-provided throwaway directory for the output file.
    """
    out = tmp_path / "informe_diario.xml"
    result = InformeDiario().export(_document(_minimal_inform()), output_path=str(out))
    assert result is None
    out.read_text(encoding="windows-1252")


def test_export_writes_file_in_windows_1252_2(tmp_path: Path) -> None:
    """With an output path, export returns None and writes a windows-1252 file.

    Parameters
    ----------
    tmp_path : pathlib.Path
            Pytest-provided throwaway directory for the output file.
    """
    out = tmp_path / "informe_diario.xml"
    InformeDiario().export(_document(_minimal_inform()), output_path=str(out))
    content = out.read_text(encoding="windows-1252")
    assert 'xmlns="urn:infdiario"' in content


def test_export_writes_file_in_windows_1252_3(tmp_path: Path) -> None:
    """With an output path, export returns None and writes a windows-1252 file.

    Parameters
    ----------
    tmp_path : pathlib.Path
            Pytest-provided throwaway directory for the output file.
    """
    out = tmp_path / "informe_diario.xml"
    InformeDiario().export(_document(_minimal_inform()), output_path=str(out))
    content = out.read_text(encoding="windows-1252")
    assert f"<CNPJ_FDO>{VALID_CNPJ}</CNPJ_FDO>" in content


def test_export_rejects_wrong_argument_type() -> None:
    """The TypeChecker metaclass rejects a mistyped argument at call time."""
    with pytest.raises(TypeError):
        InformeDiario().export("not a document")


@pytest.mark.parametrize(
    "str_bad_date",
    ["31/02/2011", "01/02/2011\n", "15/01/٢٠١١"],
    ids=["calendar-invalid", "trailing-newline", "arabic-indic-digits"],
)
def test_header_rejects_invalid_date(str_bad_date: str) -> None:
    """Reject a date that is the wrong shape or does not exist on the calendar."""
    with pytest.raises(ValidationError):
        InformeDiarioHeader(dt_compt=str_bad_date, dt_gerac_arq="15/01/2011")


@pytest.mark.parametrize(
    "str_bad_date",
    ["31/02/2011", "01/02/2011\n", "15/01/٢٠١١"],
    ids=["calendar-invalid", "trailing-newline", "arabic-indic-digits"],
)
def test_inform_rejects_invalid_data_prox_pl(str_bad_date: str) -> None:
    """Reject an invalid next-PL date on the INFORM block."""
    with pytest.raises(ValidationError):
        _minimal_inform(data_prox_pl=str_bad_date)


@pytest.mark.parametrize("str_date", ["29/02/2024", "01/03/2024"])
def test_valid_date_serialises_unchanged(str_date: str) -> None:
    """A real date round-trips byte-for-byte into the XML, leap day included."""
    xml = InformeDiario().export(
        InformeDiarioDocument(
            header=InformeDiarioHeader(dt_compt="29/02/2024", dt_gerac_arq="01/03/2024"),
            informs=[_minimal_inform(data_prox_pl="01/03/2024")],
        )
    )
    assert str_date in xml
