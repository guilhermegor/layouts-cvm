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
    with pytest.raises(ValidationError, match="Extra inputs"):
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


def test_participant_cannot_carry_aplicacoes_at_all() -> None:
    """The field does not exist, so no mutation or model_construct can emit the tag."""
    from layouts_cvm._internal.config.schemas.informe_semestral_inr import (
        InformeSemestralInrParticipante,
    )

    assert "aplicacoes" not in InformeSemestralInrParticipante.model_fields


_ORDER_CASES = [
    ("CAB_INFORM", ["COD_DOC", "VERSAO", "CD_CVM", "DT_COMPT", "DT_GERAC_ARQ"]),
    (
        "LISTA_PARTICIPANTES/{ns}PARTICIPANTE/{ns}MOV_RECURSOS",
        ["TRANSF_RECURSOS", "RECURSOS_MESMO_INVEST", "RECURSOS_OUTRO_INVEST"],
    ),
    (
        "LISTA_PARTICIPANTES/{ns}PARTICIPANTE/{ns}ENTRADA_SAIDA",
        ["VL_ENTR", "VL_SAIDA"],
    ),
    (
        "LISTA_PARTICIPANTES/{ns}PARTICIPANTE/{ns}MOV_RECURSOS/{ns}TRANSF_RECURSOS",
        [
            "VL_INVEST_CARTEIRA_HAVER_NRES",
            "VL_HAVER_NRES_INVEST_CARTEIRA",
            "VL_INVEST_CARTEIRA_ADR",
            "VL_ADR_INVEST_CARTEIRA",
            "VL_INVEST_CARTEIRA_ESTRANG_DIRETA",
            "VL_ESTRANG_DIRETA_INVEST_CARTEIRA",
        ],
    ),
    (
        "LISTA_PARTICIPANTES/{ns}PARTICIPANTE",
        ["COD_PARTIC", "ENTRADA_SAIDA", "MOV_RECURSOS", "PATRIM_LIQ"],
    ),
    (
        "LISTA_PARTICIPANTES/{ns}PARTICIPANTE/{ns}MOV_RECURSOS/{ns}RECURSOS_OUTRO_INVEST",
        ["RECURSOS_RECEB_OUTRO_INVEST", "RECURSOS_ENV_OUTRO_INVEST"],
    ),
    (
        "LISTA_PARTICIPANTES/{ns}PARTICIPANTE/{ns}MOV_RECURSOS/{ns}RECURSOS_MESMO_INVEST",
        ["RECURSOS_RECEB_MESMO_INVEST", "RECURSOS_ENV_MESMO_INVEST"],
    ),
]


@pytest.mark.parametrize(("path", "expected"), _ORDER_CASES)
def test_block_tag_order(path: str, expected: list[str]) -> None:
    """Field order is XML order: pin the header, MOV_RECURSOS and an optional block."""
    data = _data()
    data["participantes"][0]["mov_recursos"]["recursos_mesmo_invest"] = {  # type: ignore[index]
        "recursos_receb_mesmo_invest": [{"cd_partic_origem": CODE, "vl_recebido": 1}],
        "recursos_env_mesmo_invest": [{"cd_partic_dest": CODE, "vl_enviado": 2}],
    }
    data["participantes"][0]["mov_recursos"]["recursos_outro_invest"] = {  # type: ignore[index]
        "recursos_receb_outro_invest": [{"cd_partic_origem": CODE, "vl_recebido": 3}],
        "recursos_env_outro_invest": [{"cd_partic_dest": CODE, "vl_enviado": 4}],
    }
    root = _root(InformeSemestralInr().export(data))
    block = root.find(f"{NS}{path.format(ns=NS)}")
    assert [c.tag.removeprefix(NS) for c in block] == expected


def test_duplicate_participant_code_is_rejected() -> None:
    """The same participant code may appear only once per file."""
    data = _data()
    data["participantes"] *= 2  # type: ignore[operator]
    with pytest.raises(ValidationError, match="only once"):
        InformeSemestralInr().export(data)


def test_empty_optional_container_is_rejected() -> None:
    """The page says to omit an empty RECURSOS_MESMO_INVEST, not send it."""
    data = _data()
    data["participantes"][0]["mov_recursos"]["recursos_mesmo_invest"] = {}  # type: ignore[index]
    with pytest.raises(ValidationError, match="omit RECURSOS_MESMO_INVEST"):
        InformeSemestralInr().export(data)


def test_negative_entry_amount_is_rejected() -> None:
    """Unsigned amounts refuse a negative value."""
    data = _data()
    data["participantes"][0]["entrada_saida"]["vl_entr"] = -1  # type: ignore[index]
    with pytest.raises(ValidationError):
        InformeSemestralInr().export(data)


def _part_one_model_names() -> list[str]:
    """Name every model class declared in the Part I schema module."""
    from layouts_cvm._internal.config.schemas import informe_semestral_inr as part_one

    return [
        k
        for k, v in vars(part_one).items()
        if isinstance(v, type) and v.__module__ == part_one.__name__
    ]


@pytest.mark.parametrize("name", _part_one_model_names())
def test_no_part_one_model_inherits_from_the_monthly_module(name: str) -> None:
    """Every model in the Part I schema, nested blocks included, is self-contained."""
    from layouts_cvm._internal.config.schemas import informe_semestral_inr as part_one, inr_mensal

    bases = {b.__module__ for b in getattr(part_one, name).__mro__}
    assert inr_mensal.__name__ not in bases
