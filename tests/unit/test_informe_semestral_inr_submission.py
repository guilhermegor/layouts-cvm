"""Unit tests for the Informe Semestral INR Part I submission writer."""

from xml.etree import ElementTree as ET  # noqa: S405

from pydantic import ValidationError
import pytest

from layouts_cvm import InformeSemestralInr


NS = "{urn:infmensal}"
CODE = "12345.123456.654321.1-9"


def _data(**extra: object) -> dict[str, object]:
    """Build plain Part I document data."""
    transf = {
        t: 0
        for t in (
            "vl_invest_carteira_haver_nres",
            "vl_haver_nres_invest_carteira",
            "vl_invest_carteira_adr",
            "vl_adr_invest_carteira",
            "vl_invest_carteira_estrang_direta",
            "vl_estrang_direta_invest_carteira",
        )
    }
    participant: dict[str, object] = {
        "cod_partic": CODE,
        "entrada_saida": {"vl_entr": 10, "vl_saida": 20},
        "mov_recursos": {"transf_recursos": transf},
        "patrim_liq": 500,
    }
    participant.update(extra)
    return {
        "header": {"cd_cvm": "12345", "dt_compt": "06/2025", "dt_gerac_arq": "15/07/2025"},
        "participantes": [participant],
    }


def _root(xml: str) -> ET.Element:
    """Parse the XML text after its declaration."""
    return ET.fromstring(xml.split("\n", 1)[1])  # noqa: S314


def test_export_writes_cod_doc_69() -> None:
    """The header carries COD_DOC 69."""
    root = _root(InformeSemestralInr().export(_data()))
    assert root.find(f"{NS}CAB_INFORM/{NS}COD_DOC").text == "69"


def test_export_uses_the_monthly_namespace() -> None:
    """The root element is DOC_ARQ in urn:infmensal."""
    root = _root(InformeSemestralInr().export(_data()))
    assert root.tag == f"{NS}DOC_ARQ"


def test_export_emits_participant_blocks_without_aplicacoes() -> None:
    """A participant has no APLICACOES element."""
    root = _root(InformeSemestralInr().export(_data()))
    part = root.find(f"{NS}LISTA_PARTICIPANTES/{NS}PARTICIPANTE")
    assert [c.tag.removeprefix(NS) for c in part] == [
        "COD_PARTIC",
        "ENTRADA_SAIDA",
        "MOV_RECURSOS",
        "PATRIM_LIQ",
    ]


def test_aplicacoes_is_rejected() -> None:
    """Part II applications are refused in Part I."""
    bad = _data(aplicacoes=[{"cd_aplic": 1, "vl_mercado_aplic": 5}])
    with pytest.raises(ValidationError, match="APLICACOES"):
        InformeSemestralInr().export(bad)


def test_cod_doc_other_than_69_is_rejected() -> None:
    """Only COD_DOC 69 is accepted."""
    bad = _data()
    bad["header"]["cod_doc"] = 477  # type: ignore[index]
    with pytest.raises(ValidationError):
        InformeSemestralInr().export(bad)


def test_export_to_path_returns_none(tmp_path) -> None:  # noqa: ANN001
    """Writing to a file returns None."""
    assert InformeSemestralInr().export(_data(), str(tmp_path / "out.xml")) is None


def test_export_to_path_writes_windows_1252_declaration(tmp_path) -> None:  # noqa: ANN001
    """The file starts with the windows-1252 declaration."""
    path = tmp_path / "out.xml"
    InformeSemestralInr().export(_data(), str(path))
    assert path.read_bytes().startswith(b'<?xml version="1.0" encoding="windows-1252"?>')


def test_participant_prefix_must_equal_cd_cvm() -> None:
    """A participant of another representative is refused."""
    bad = _data(cod_partic="99999.123456.654321.1-9")
    with pytest.raises(ValidationError, match="CD_CVM"):
        InformeSemestralInr().export(bad)


def _with_participants(count: int) -> dict[str, object]:
    """Build data holding ``count`` participants with distinct codes."""
    data = _data()
    base = data["participantes"][0]  # type: ignore[index]
    data["participantes"] = [
        {**base, "cod_partic": f"12345.123456.{n}.1-9"} for n in range(1, count + 1)
    ]
    return data


def test_zero_participants_is_rejected() -> None:
    """A file needs at least one participant."""
    with pytest.raises(ValidationError, match="at least 1"):
        InformeSemestralInr().export(_with_participants(0))


def test_1001_participants_is_rejected() -> None:
    """The page allows at most 1000 PARTICIPANTE tags per file."""
    with pytest.raises(ValidationError, match="at most 1000"):
        InformeSemestralInr().export(_with_participants(1001))


def test_1000_participants_is_accepted() -> None:
    """The upper bound itself is valid."""
    xml = InformeSemestralInr().export(_with_participants(1000))
    assert xml.count("<PARTICIPANTE>") == 1000
