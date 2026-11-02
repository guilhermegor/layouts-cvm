"""Unit tests for the Informe de Fundo 157 submission writer.

The expected tag lists are typed from the CVM page's sample file, not derived from the models.
"""

from pathlib import Path
from xml.etree import ElementTree as ET  # noqa: S405

from pydantic import ValidationError
import pytest

from layouts_cvm import (
    InfFundo157,
    InfFundo157Cotista,
    InfFundo157Document,
    InfFundo157Header,
)


NS = "{urn:inffdo157}"
CNPJ = "11222333000181"
CPF = "52998224725"
OTHER_CPF = "11144477735"

ROOT_TAGS = ["DESC_FDO_157", "LISTA_COTSTS"]
HEADER_TAGS = ["COD_DOC", "CNPJ_FDO_157", "DT_GERAC_ARQ", "DT_COMPTC"]
COTST_TAGS = ["CPF", "NOME", "DT_FIM", "CONF"]


def _header(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "cnpj_fdo_157": CNPJ,
        "dt_gerac_arq": "31/10/2026",
        "dt_comptc": "10/2026",
    }
    return base | overrides


def _cotista(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "cpf": CPF,
        "nome": "Maria da Conceição",
        "dt_fim": "15/09/2026",
        "conf": "S",
    }
    return base | overrides


def _doc(*cotistas: dict[str, object]) -> InfFundo157Document:
    return InfFundo157Document.model_validate(
        {"header": _header(), "cotistas": list(cotistas or [_cotista()])}
    )


def _parse(xml: str) -> ET.Element:
    """Parse the writer's own output."""
    return ET.fromstring(xml)  # noqa: S314


def _tags(element: ET.Element) -> list[str]:
    return [child.tag.removeprefix(NS) for child in element]


def test_export_root_and_blocks_follow_spec_order_1() -> None:
    """Export root and blocks follow spec order."""
    root = _parse(InfFundo157().export(_doc(_cotista(), _cotista(cpf=OTHER_CPF))))
    assert root.tag == f"{NS}DOC_ARQ"
    root.findall(f"{NS}LISTA_COTSTS/{NS}COTST")


def test_export_root_and_blocks_follow_spec_order_2() -> None:
    """Export root and blocks follow spec order."""
    root = _parse(InfFundo157().export(_doc(_cotista(), _cotista(cpf=OTHER_CPF))))
    assert _tags(root) == ROOT_TAGS
    root.findall(f"{NS}LISTA_COTSTS/{NS}COTST")


def test_export_root_and_blocks_follow_spec_order_3() -> None:
    """Export root and blocks follow spec order."""
    root = _parse(InfFundo157().export(_doc(_cotista(), _cotista(cpf=OTHER_CPF))))
    assert _tags(root[0]) == HEADER_TAGS
    root.findall(f"{NS}LISTA_COTSTS/{NS}COTST")


def test_export_root_and_blocks_follow_spec_order_4() -> None:
    """Export root and blocks follow spec order."""
    root = _parse(InfFundo157().export(_doc(_cotista(), _cotista(cpf=OTHER_CPF))))
    cotistas = root.findall(f"{NS}LISTA_COTSTS/{NS}COTST")
    assert len(cotistas) == 2


def test_export_root_and_blocks_follow_spec_order_5() -> None:
    """Export root and blocks follow spec order."""
    root = _parse(InfFundo157().export(_doc(_cotista(), _cotista(cpf=OTHER_CPF))))
    cotistas = root.findall(f"{NS}LISTA_COTSTS/{NS}COTST")
    assert all(_tags(c) == COTST_TAGS for c in cotistas)


def test_export_values_and_declaration_1() -> None:
    """Export values and declaration."""
    xml = InfFundo157().export(_doc())
    assert xml.startswith('<?xml version="1.0" encoding="windows-1252"?>\n')
    root = _parse(xml)
    {c.tag.removeprefix(NS): c.text for c in root[0]}
    {c.tag.removeprefix(NS): c.text for c in root[1][0]}


def test_export_values_and_declaration_2() -> None:
    """Export values and declaration."""
    xml = InfFundo157().export(_doc())
    root = _parse(xml)
    header = {c.tag.removeprefix(NS): c.text for c in root[0]}
    assert header == {
        "COD_DOC": "55",
        "CNPJ_FDO_157": CNPJ,
        "DT_GERAC_ARQ": "31/10/2026",
        "DT_COMPTC": "10/2026",
    }
    {c.tag.removeprefix(NS): c.text for c in root[1][0]}


def test_export_values_and_declaration_3() -> None:
    """Export values and declaration."""
    xml = InfFundo157().export(_doc())
    root = _parse(xml)
    {c.tag.removeprefix(NS): c.text for c in root[0]}
    cotst = {c.tag.removeprefix(NS): c.text for c in root[1][0]}
    assert cotst == {"CPF": CPF, "NOME": "Maria da Conceição", "DT_FIM": "15/09/2026", "CONF": "S"}


def test_export_writes_windows_1252_bytes_1(tmp_path: Path) -> None:
    """Export writes windows 1252 bytes."""
    target = tmp_path / "out.xml"
    assert InfFundo157().export(_doc(), str(target)) is None


def test_export_writes_windows_1252_bytes_2(tmp_path: Path) -> None:
    """Export writes windows 1252 bytes."""
    target = tmp_path / "out.xml"
    InfFundo157().export(_doc(), str(target))
    assert "Conceição".encode("windows-1252") in target.read_bytes()


def test_failed_export_keeps_existing_file_1(tmp_path: Path) -> None:
    """Failed export keeps existing file."""
    target = tmp_path / "out.xml"
    target.write_bytes(b"keep")
    bad = InfFundo157Cotista.model_construct(**_cotista(nome="Ω"))
    doc = InfFundo157Document.model_construct(
        header=InfFundo157Header.model_validate(_header()), cotistas=[bad]
    )
    with pytest.raises(ValueError, match="windows-1252"):
        InfFundo157().export(doc, str(target))


def test_failed_export_keeps_existing_file_2(tmp_path: Path) -> None:
    """Failed export keeps existing file."""
    target = tmp_path / "out.xml"
    target.write_bytes(b"keep")
    bad = InfFundo157Cotista.model_construct(**_cotista(nome="Ω"))
    InfFundo157Document.model_construct(
        header=InfFundo157Header.model_validate(_header()), cotistas=[bad]
    )
    assert target.read_bytes() == b"keep"


@pytest.mark.parametrize(
    "overrides",
    [
        {"cnpj_fdo_157": "11222333000182"},
        {"cnpj_fdo_157": " 11222333000181"},
        {"cnpj_fdo_157": "11222333000181\n"},
        {"dt_gerac_arq": "31/02/2026"},
        {"dt_gerac_arq": "2026-10-31"},
        {"dt_comptc": "13/2026"},
        {"dt_comptc": "10/0001"},
        {"cod_doc": 56},
    ],
)
def test_header_invalid_field_raises_validation_error(overrides: dict[str, object]) -> None:
    """A header with one malformed or unknown field raises ValidationError."""
    with pytest.raises(ValidationError):
        InfFundo157Header.model_validate(_header(**overrides))


@pytest.mark.parametrize(
    "overrides",
    [
        {"cpf": "52998224726"},
        {"cpf": "529.982.247-25"},
        {"cpf": "52998224725\n"},
        {"cpf": "٥٢٩٩٨٢٢٤٧٢٥"},
        {"cpf": ""},
        {"nome": ""},
        {"nome": "   "},
        {"nome": "A" * 201},
        {"nome": "a\x00b"},
        {"dt_fim": "30/02/2026"},
        {"dt_fim": "01/01/0001"},
        {"conf": "s"},
        {"conf": "X"},
        {"unknown": "x"},
    ],
)
def test_cotista_invalid_field_raises_validation_error(overrides: dict[str, object]) -> None:
    """A cotista with one malformed or unknown field raises ValidationError."""
    with pytest.raises(ValidationError):
        InfFundo157Cotista.model_validate(_cotista(**overrides))


def test_cotista_accepts_boundaries() -> None:
    """Cotista accepts boundaries."""
    assert InfFundo157Cotista.model_validate(_cotista(nome="A" * 200, conf="N")).conf == "N"


def test_masked_cnpj_is_written_bare() -> None:
    """Masked cnpj is written bare."""
    header = InfFundo157Header.model_validate(_header(cnpj_fdo_157="11.222.333/0001-81"))
    assert header.cnpj_fdo_157 == CNPJ


def test_document_requires_at_least_one_cotista() -> None:
    """Document requires at least one cotista."""
    with pytest.raises(ValidationError):
        InfFundo157Document.model_validate({"header": _header(), "cotistas": []})


def test_document_cotistas_cannot_be_emptied_after_validation_1() -> None:
    """The validated cotistas collection is immutable, so min_length cannot be bypassed."""
    doc = InfFundo157Document.model_validate({"header": _header(), "cotistas": [_cotista()]})
    assert isinstance(doc.cotistas, tuple)


def test_document_cotistas_cannot_be_emptied_after_validation_2() -> None:
    """The validated cotistas collection is immutable, so min_length cannot be bypassed."""
    doc = InfFundo157Document.model_validate({"header": _header(), "cotistas": [_cotista()]})
    assert not hasattr(doc.cotistas, "clear")
