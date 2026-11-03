"""Unit tests for the Informe Art. 12 Res. CVM 33 submission writer.

Pin the tag order, nesting and header to PadraoXMLPrest.asp and cover the rejections.
"""

from pathlib import Path
import re

from pydantic import ValidationError
import pytest

from layouts_cvm import InformeArt12Res33
from layouts_cvm._internal.config.schemas.informe_art12_res33 import (
    Ativo,
    DsInform,
    DsPrest,
    Emissor,
    InformeArt12Res33Document,
    Prestador,
)


CNPJ_A = "11222333000181"
CNPJ_B = "11444777000161"


def _ativo(**overrides: object) -> Ativo:
    fields: dict[str, object] = {
        "ativo_escriturado": "A1",
        "dt_inicio_contrato": "01/02/2020",
        "dt_fim_contrato": "15/01/2021",
    }
    fields.update(overrides)
    return Ativo(**fields)


def _doc(ativo: Ativo | None = None) -> InformeArt12Res33Document:
    return InformeArt12Res33Document(
        ds_inform=DsInform(dt_compt="01/2021", dt_gerac_arq="05/02/2021"),
        prestadores=[
            Prestador(
                ds_prest=DsPrest(cnpj_escriturador=CNPJ_A, cd_tp_prest=41),
                emissores=[Emissor(cnpj_emissor=CNPJ_B, ativo=[ativo or _ativo()])],
            )
        ],
    )


def _xml(ativo: Ativo | None = None) -> str:
    xml = InformeArt12Res33().export(_doc(ativo))
    assert xml is not None
    return xml


def test_full_tag_order_matches_page() -> None:
    """Emit every tag in the order and nesting of the page template."""
    assert re.findall(r"<([A-Z_]+)>", _xml()) == [
        "COD_ARQ",
        "DS_INFORM",
        "DT_COMPT",
        "DT_GERAC_ARQ",
        "LISTA_PREST",
        "INFORM_PREST",
        "DS_PREST",
        "CNPJ_ESCRITURADOR",
        "CD_TP_PREST",
        "LISTA_EMISSORES",
        "EMISSOR",
        "CNPJ_EMISSOR",
        "ATIVO",
        "ATIVO_ESCRITURADO",
        "DT_INICIO_CONTRATO",
        "DT_FIM_CONTRATO",
    ]


@pytest.mark.parametrize(
    "fragment",
    [
        '<DOC_ARQ xmlns="urn:prestserv">',
        "<COD_ARQ>29</COD_ARQ>",
        "<DT_COMPT>01/2021</DT_COMPT>",
        "<DT_GERAC_ARQ>05/02/2021</DT_GERAC_ARQ>",
        "<CD_TP_PREST>41</CD_TP_PREST>",
    ],
)
def test_header_fields(fragment: str) -> None:
    """Stamp the namespace, COD_ARQ 29 and the header dates in the page formats."""
    assert fragment in _xml()


def test_dt_fim_contrato_omitted_when_open() -> None:
    """Omit DT_FIM_CONTRATO for a contract that was not closed."""
    assert "DT_FIM_CONTRATO" not in _xml(_ativo(dt_fim_contrato=None))


def test_ativo_repeats_per_asset() -> None:
    """Repeat ATIVO inside one EMISSOR."""
    doc = _doc()
    doc.prestadores[0].emissores[0].ativo.append(_ativo(ativo_escriturado="A2"))

    assert InformeArt12Res33().export(doc).count("<ATIVO>") == 2  # type: ignore[union-attr]


def test_cnpj_is_stored_unmasked() -> None:
    """Strip CNPJ punctuation before emitting."""
    emissor = Emissor(cnpj_emissor="11.444.777/0001-61", ativo=[_ativo()])

    assert emissor.cnpj_emissor == CNPJ_B


@pytest.mark.parametrize("cls", [Emissor, DsPrest])
def test_invalid_cnpj_rejected(cls: type) -> None:
    """Reject a CNPJ with wrong check digits."""
    kwargs = (
        {"cnpj_emissor": "11222333000182", "ativo": [_ativo()]}
        if cls is Emissor
        else {"cnpj_escriturador": "11222333000182", "cd_tp_prest": 41}
    )
    with pytest.raises(ValidationError):
        cls(**kwargs)


@pytest.mark.parametrize("code", [0, 43, 410])
def test_unknown_provider_type_rejected(code: int) -> None:
    """Reject a provider type outside Tabela A."""
    with pytest.raises(ValidationError):
        DsPrest(cnpj_escriturador=CNPJ_A, cd_tp_prest=code)


def test_unknown_asset_type_rejected() -> None:
    """Reject an asset code outside Tabela B."""
    with pytest.raises(ValidationError):
        _ativo(ativo_escriturado="A5")


@pytest.mark.parametrize("value", ["2021-01", "13/2021", "1/2021", "01/02/2021"])
def test_malformed_competence_rejected(value: str) -> None:
    """Reject a DT_COMPT that is not a real MM/AAAA."""
    with pytest.raises(ValidationError):
        DsInform(dt_compt=value, dt_gerac_arq="05/02/2021")


@pytest.mark.parametrize("value", ["2021-02-05", "31/02/2021", "5/2/2021"])
def test_malformed_generation_date_rejected(value: str) -> None:
    """Reject a DT_GERAC_ARQ that is not a real DD/MM/AAAA."""
    with pytest.raises(ValidationError):
        DsInform(dt_compt="01/2021", dt_gerac_arq=value)


def test_contract_end_before_start_rejected() -> None:
    """Reject a contract ending before it starts."""
    with pytest.raises(ValidationError):
        _ativo(dt_fim_contrato="01/01/2020")


def test_cod_arq_other_than_29_rejected() -> None:
    """Reject a COD_ARQ other than 29."""
    with pytest.raises(ValidationError):
        InformeArt12Res33Document(cod_arq=30, **_doc().model_dump(exclude={"cod_arq"}))


def test_no_provider_rejected() -> None:
    """Require at least one provider."""
    with pytest.raises(ValidationError):
        InformeArt12Res33Document(ds_inform=_doc().ds_inform, prestadores=[])


def test_issuer_without_asset_rejected() -> None:
    """Require at least one asset per issuer."""
    with pytest.raises(ValidationError):
        Emissor(cnpj_emissor=CNPJ_B, ativo=[])


def test_export_to_file_returns_none(tmp_path: Path) -> None:
    """Return None when an output path is given."""
    assert InformeArt12Res33().export(_doc(), output_path=str(tmp_path / "i.xml")) is None


def test_export_file_is_windows_1252_with_page_declaration(tmp_path: Path) -> None:
    """Write the file as windows-1252 with the page's XML declaration."""
    out = tmp_path / "informe.xml"
    InformeArt12Res33().export(_doc(), output_path=str(out))

    assert (
        out.read_bytes()
        .decode("windows-1252")
        .startswith('<?xml version="1.0" encoding="windows-1252"?>')
    )


def test_export_file_matches_returned_string(tmp_path: Path) -> None:
    """Write exactly the text export returns."""
    out = tmp_path / "informe.xml"
    InformeArt12Res33().export(_doc(), output_path=str(out))

    assert out.read_bytes().decode("windows-1252") == _xml()


def test_writer_rejects_a_non_document() -> None:
    """Refuse an object that is not a document (runtime type check)."""
    with pytest.raises(TypeError):
        InformeArt12Res33().export("not a document")  # type: ignore[arg-type]


def test_export_plain_data_equals_model_export() -> None:
    """A dict from a valid document's ``model_dump`` exports the same XML as the model."""
    doc = _doc()

    assert InformeArt12Res33().export(doc.model_dump()) == InformeArt12Res33().export(doc)
