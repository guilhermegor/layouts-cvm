"""Unit tests for the Informe Anual de Auditor submission writer.

The expected tag order is typed from the CVM page's sample file (PadraoXMLAuditorAnual.asp), not
derived from the models, so a field declared out of order or under the wrong name fails here.
"""

import copy
from decimal import Decimal
from functools import reduce
from operator import getitem
from pathlib import Path
from xml.etree import ElementTree as ET  # noqa: S405

from pydantic import ValidationError
import pytest

from layouts_cvm._internal.config.schemas.informe_anual_auditor import (
    InformeAnualAuditorDocument,
)
from layouts_cvm.informe_anual_auditor import InformeAnualAuditor


NS = "{urn:audtanual}"
CNPJ = "11222333000181"
CPF = "52998224725"

INFORM_TAGS = [
    "DS_INFORM",
    "DS_AUDIT",
    "LISTA_ENDER",
    "LISTA_RESP",
    "LISTA_ENTID_AUDITA",
    "QT_OUTRA_ENTID_AUDITA",
    "FATURA_ANUAL",
    "DS_CRITER_HONOR",
    "RH",
    "LISTA_ENTID_COLIG",
]
ENDER_TAGS = [
    "TP_ENDER",
    "NM_FILIAL",
    "NM_LOGRAD",
    "DS_COMPL",
    "DS_BAIRRO",
    "CD_MUN",
    "NR_CEP",
    "NR_DDD_TEL",
    "NR_TEL",
    "NR_DDD_FAX",
    "NR_FAX",
]


def _addresses() -> list:
    """Build a head-office and a branch address.

    Returns
    -------
    list
        Plain data for ``LISTA_ENDER``.
    """
    return [
        {
            "tp_ender": 1,
            "nm_lograd": "Rua A",
            "ds_compl": "Sala 1",
            "ds_bairro": "Centro",
            "cd_mun": 3550308,
            "nr_cep": "01001000",
            "nr_ddd_tel": "11",
            "nr_tel": "30303030",
            "nr_ddd_fax": "11",
            "nr_fax": "30303031",
        },
        {
            "tp_ender": 2,
            "nm_filial": "Filial RJ",
            "nm_lograd": "Rua B",
            "ds_bairro": "Centro",
            "cd_mun": 3304557,
            "nr_cep": "20010000",
        },
    ]


def _entities() -> dict:
    """Build the audited and affiliated entity blocks.

    Returns
    -------
    dict
        Plain data for ``LISTA_ENTID_AUDITA`` and ``LISTA_ENTID_COLIG``.
    """
    audited = {
        "tp_entid": 95,
        "nr_pj": CNPJ,
        "ds_nome": "Fundo X",
        "dt_contr": "01/02/2025",
        "pr_fatura": "12.345",
    }
    national = {"st_estr": "N", "nr_pj": CNPJ, "ds_nome": "Colig", "ds_setor_ativd": "Gestao"}
    foreign = {"st_estr": "S", "ds_nome": "Foreign", "ds_setor_ativd": "Gestao"}
    return {
        "lista_entid_audita": {"entid_audita": [audited]},
        "lista_entid_colig": {"entid_colig": [national, foreign]},
    }


def _pj_data() -> dict:
    """Build a complete legal-entity auditor payload.

    Returns
    -------
    dict
        Plain data for the document.
    """
    identity = {
        "tp_pf_pj": "PJ",
        "nr_pf_pj": CNPJ,
        "cd_cvm": 123,
        "ds_nome": "Auditores SA",
        "ds_email": "a@b.com",
    }
    return {
        "inform_audit": {
            "ds_inform": {"ano_base": 2025, "dt_gerac_arq": "15/04/2026", "motivo_entreg": 1},
            "ds_audit": identity,
            "lista_ender": {"ender": _addresses()},
            "lista_resp": {"resp": [{"nr_pf": CPF, "ds_nome": "Socio Um", "ds_email": "s@b.com"}]},
            "qt_outra_entid_audita": 4,
            "fatura_anual": {"vl_audit": "1000.50", "pr_audit": "80", "hh_audit": 900},
            "ds_criter_honor": "Por hora trabalhada",
            "rh": {"qt_socios": 3, "qt_func_tecno": 20},
            **_entities(),
        }
    }


def _pf_data() -> dict:
    """Build a natural-person auditor payload (one address, no partners).

    Returns
    -------
    dict
        Plain data for the document.
    """
    data = _pj_data()
    inform = data["inform_audit"]
    inform["ds_audit"].update({"tp_pf_pj": "PF", "nr_pf_pj": CPF})
    inform["lista_ender"]["ender"] = inform["lista_ender"]["ender"][:1]
    del inform["lista_resp"]
    del inform["rh"]["qt_socios"]
    return data


def _root(data: dict) -> ET.Element:
    """Export ``data`` and parse the XML back.

    Parameters
    ----------
    data : dict
        Document payload.

    Returns
    -------
    ET.Element
        The parsed root.
    """
    return ET.fromstring(InformeAnualAuditor().export(data).split("\n", 1)[1])  # noqa: S314


def _tags(element: ET.Element) -> list:
    """List the child tags without namespace.

    Parameters
    ----------
    element : ET.Element
        Parent element.

    Returns
    -------
    list
        Tag names in document order.
    """
    return [child.tag.removeprefix(NS) for child in element]


def test_export_pj_follows_page_tag_order() -> None:
    """Export pj follows page tag order."""
    assert _tags(_root(_pj_data()).find(f"{NS}INFORM_AUDIT")) == INFORM_TAGS


def test_export_root_holds_cod_doc_then_inform_audit() -> None:
    """Export root holds cod doc then inform audit."""
    assert _tags(_root(_pj_data())) == ["COD_DOC", "INFORM_AUDIT"]


def test_export_head_office_address_tag_order() -> None:
    """Export head office address tag order."""
    ender = _root(_pj_data()).find(f"{NS}INFORM_AUDIT/{NS}LISTA_ENDER/{NS}ENDER")
    assert _tags(ender) == [tag for tag in ENDER_TAGS if tag != "NM_FILIAL"]


def test_export_cod_doc_is_23_without_padding() -> None:
    """Export cod doc is 23 without padding."""
    assert _root(_pj_data()).find(f"{NS}COD_DOC").text == "23"


def test_export_decimals_use_comma_separator() -> None:
    """Export decimals use comma separator."""
    root = _root(_pj_data())
    assert root.find(f"{NS}INFORM_AUDIT/{NS}FATURA_ANUAL/{NS}VL_AUDIT").text == "1000,50"


def test_export_percent_truncates_instead_of_rounding() -> None:
    """Export percent truncates instead of rounding."""
    root = _root(_pj_data())
    path_tag = f"{NS}INFORM_AUDIT/{NS}LISTA_ENTID_AUDITA/{NS}ENTID_AUDITA/{NS}PR_FATURA"
    assert root.find(path_tag).text == "12,34"


def test_export_branch_address_tag_order() -> None:
    """Export branch address tag order."""
    ender = _root(_pj_data()).findall(f"{NS}INFORM_AUDIT/{NS}LISTA_ENDER/{NS}ENDER")[1]
    assert _tags(ender) == ["TP_ENDER", "NM_FILIAL", "NM_LOGRAD", "DS_BAIRRO", "CD_MUN", "NR_CEP"]


def test_export_head_office_omits_branch_name() -> None:
    """Export head office omits branch name."""
    enders = _root(_pj_data()).findall(f"{NS}INFORM_AUDIT/{NS}LISTA_ENDER/{NS}ENDER")
    assert [e.find(f"{NS}NM_FILIAL") is None for e in enders] == [True, False]


def test_export_foreign_affiliate_omits_cnpj() -> None:
    """Export foreign affiliate omits cnpj."""
    colig = _root(_pj_data()).findall(f"{NS}INFORM_AUDIT/{NS}LISTA_ENTID_COLIG/{NS}ENTID_COLIG")
    assert _tags(colig[1]) == ["ST_ESTR", "DS_NOME", "DS_SETOR_ATIVD"]


def test_export_pf_omits_responsible_block() -> None:
    """Export pf omits responsible block."""
    inform = _root(_pf_data()).find(f"{NS}INFORM_AUDIT")
    assert "LISTA_RESP" not in _tags(inform)


def test_export_pf_omits_partner_count() -> None:
    """Export pf omits partner count."""
    inform = _root(_pf_data()).find(f"{NS}INFORM_AUDIT")
    assert _tags(inform.find(f"{NS}RH")) == ["QT_FUNC_TECNO"]


def test_export_model_and_mapping_give_same_xml() -> None:
    """Export model and mapping give same xml."""
    model = InformeAnualAuditorDocument.model_validate(_pj_data())
    assert InformeAnualAuditor().export(model) == InformeAnualAuditor().export(_pj_data())


def test_export_writes_windows_1252_file(tmp_path: Path) -> None:
    """Export writes windows 1252 file."""
    data = _pj_data()
    data["inform_audit"]["ds_audit"]["ds_nome"] = "Auditoria Ção"
    path_out = tmp_path / "out.xml"
    InformeAnualAuditor().export(data, str(path_out))
    assert "Auditoria Ção".encode("windows-1252") in path_out.read_bytes()


def test_export_to_file_returns_none(tmp_path: Path) -> None:
    """Export to file returns none."""
    assert InformeAnualAuditor().export(_pj_data(), str(tmp_path / "out.xml")) is None


def _mutate(path: tuple, value: object) -> dict:
    """Return the PJ payload with one nested value replaced.

    Parameters
    ----------
    path : tuple
        Keys/indexes leading to the value.
    value : object
        Replacement.

    Returns
    -------
    dict
        The mutated copy.
    """
    data = copy.deepcopy(_pj_data())
    reduce(getitem, path[:-1], data)[path[-1]] = value
    return data


_INFORM = "inform_audit"
_AUDIT = (_INFORM, "ds_audit")
_ENDER0 = (_INFORM, "lista_ender", "ender", 0)


@pytest.mark.parametrize(
    "data",
    [
        _mutate((*_AUDIT, "nr_pf_pj"), "11222333000182"),
        _mutate((*_AUDIT, "nr_pf_pj"), "11.222.333/0001-81"),
        _mutate((*_AUDIT, "ds_email"), "x" * 51),
        _mutate((_INFORM, "ds_inform", "motivo_entreg"), 4),
        _mutate((_INFORM, "ds_inform", "dt_gerac_arq"), "31/02/2026"),
        _mutate((*_ENDER0, "nm_filial"), "Sede"),
        _mutate((*_ENDER0, "nr_cep"), "01-001"),
        _mutate((*_ENDER0, "ds_compl"), "x" * 19),
        _mutate((_INFORM, "lista_entid_audita", "entid_audita", 0, "tp_entid"), 2),
        _mutate((_INFORM, "lista_entid_colig", "entid_colig", 1, "nr_pj"), CNPJ),
        _mutate((_INFORM, "lista_entid_colig", "entid_colig", 0, "nr_pj"), None),
        _mutate((_INFORM, "fatura_anual", "vl_audit"), 1.5),
        _mutate((_INFORM, "fatura_anual", "pr_audit"), "100.01"),
        _mutate((_INFORM, "ds_criter_honor"), "x" * 501),
        _mutate((_INFORM, "extra"), 1),
    ],
)
def test_document_rejects_invalid_payload(data: dict) -> None:
    """Document rejects invalid payload."""
    with pytest.raises(ValidationError):
        InformeAnualAuditorDocument.model_validate(data)


def test_document_rejects_pf_with_responsible_block() -> None:
    """Document rejects pf with responsible block."""
    data = _pf_data()
    data["inform_audit"]["lista_resp"] = {"resp": []}
    with pytest.raises(ValidationError):
        InformeAnualAuditorDocument.model_validate(data)


def test_document_rejects_pf_with_two_addresses() -> None:
    """Document rejects pf with two addresses."""
    data = _pf_data()
    data["inform_audit"]["lista_ender"]["ender"] = _pj_data()["inform_audit"]["lista_ender"][
        "ender"
    ]
    with pytest.raises(ValidationError):
        InformeAnualAuditorDocument.model_validate(data)


def test_document_keeps_leading_zero_in_cep() -> None:
    """Document keeps leading zero in cep."""
    doc = InformeAnualAuditorDocument.model_validate(_pj_data())
    assert doc.inform_audit.lista_ender.ender[0].nr_cep == "01001000"


def test_document_truncates_percent_never_rounds() -> None:
    """Document truncates percent never rounds."""
    doc = InformeAnualAuditorDocument.model_validate(_pj_data())
    assert doc.inform_audit.lista_entid_audita.entid_audita[0].pr_fatura == Decimal("12.34")


TABLE_B = frozenset(
    {17, 23, 45, 7, 5, 1, 20, 47, 48, 25, 14, 63, 67, 93, 96, 27, 22, 95, 99, 88, 86, 75, 32, 69}
    | {74, 87, 98, 89, 91, 92, 90, 83, 73, 70, 84, 77, 30, 80, 72, 43, 85, 60, 61, 94, 55, 57}
    | {52, 50}
)
NOT_IN_TABLE_B = sorted(set(range(101)) - TABLE_B)
LIST_LIMITS = [
    ("lista_ender", "ENDER", 1000),
    ("lista_entid_audita", "ENTID_AUDITA", 8000),
    ("lista_entid_colig", "ENTID_COLIG", 1000),
]
EMPTY_LISTS = [
    ("lista_resp", "LISTA_RESP", {"resp": []}),
    ("lista_entid_audita", "LISTA_ENTID_AUDITA", {"entid_audita": []}),
    ("lista_entid_colig", "LISTA_ENTID_COLIG", {"entid_colig": []}),
]


def _inform(data: dict) -> ET.Element:
    """Export ``data`` and return its ``INFORM_AUDIT`` block.

    Parameters
    ----------
    data : dict
        Document payload.

    Returns
    -------
    ET.Element
        The ``INFORM_AUDIT`` element.
    """
    return _root(data).find(f"{NS}INFORM_AUDIT")


def _with_items(str_key: str, int_count: int) -> dict:
    """Build the PJ payload with ``int_count`` items in one repeating list.

    Parameters
    ----------
    str_key : str
        The ``LISTA_*`` field to fill.
    int_count : int
        How many blocks the list holds.

    Returns
    -------
    dict
        The payload; an address list keeps its head office first, then branches.
    """
    data = _pj_data()
    inform = data["inform_audit"]
    audited = _entities()["lista_entid_audita"]["entid_audita"][0]
    affiliated = _entities()["lista_entid_colig"]["entid_colig"][0]
    templates = {
        "lista_ender": (_addresses()[0], _addresses()[1]),
        "lista_entid_audita": (audited, audited),
        "lista_entid_colig": (affiliated, affiliated),
    }
    first, rest = templates[str_key]
    items = [copy.deepcopy(first)] + [copy.deepcopy(rest) for _ in range(int_count - 1)]
    inform[str_key] = {next(iter(inform[str_key])): items}
    return data


@pytest.mark.parametrize(("str_key", "str_tag", "dict_empty"), EMPTY_LISTS)
def test_export_empty_list_keeps_its_wrapper(str_key: str, str_tag: str, dict_empty: dict) -> None:
    """Export empty list keeps its wrapper in the page's tag order."""
    data = _mutate((_INFORM, str_key), dict_empty)
    assert _tags(_inform(data)) == INFORM_TAGS


@pytest.mark.parametrize(("str_key", "str_tag", "dict_empty"), EMPTY_LISTS)
def test_export_empty_list_wrapper_holds_no_blocks(
    str_key: str, str_tag: str, dict_empty: dict
) -> None:
    """Export empty list wrapper holds no repeating blocks."""
    data = _mutate((_INFORM, str_key), dict_empty)
    assert list(_inform(data).find(f"{NS}{str_tag}")) == []


@pytest.mark.parametrize("str_key", ["lista_entid_audita", "lista_entid_colig"])
def test_export_omitted_optional_list_still_emits_wrapper(str_key: str) -> None:
    """Export omitted optional list still emits its empty wrapper."""
    data = _pj_data()
    del data["inform_audit"][str_key]
    assert _tags(_inform(data)) == INFORM_TAGS


@pytest.mark.parametrize("int_code", sorted(TABLE_B))
def test_export_table_b_code_is_written_as_is(int_code: int) -> None:
    """Export writes every Table B entity type unchanged."""
    data = _mutate((_INFORM, "lista_entid_audita", "entid_audita", 0, "tp_entid"), int_code)
    tp_entid = _inform(data).find(f"{NS}LISTA_ENTID_AUDITA/{NS}ENTID_AUDITA/{NS}TP_ENTID")
    assert tp_entid.text == str(int_code)


@pytest.mark.parametrize("int_code", NOT_IN_TABLE_B)
def test_document_rejects_code_outside_table_b(int_code: int) -> None:
    """Document rejects every entity type the page's Table B does not list."""
    data = _mutate((_INFORM, "lista_entid_audita", "entid_audita", 0, "tp_entid"), int_code)
    with pytest.raises(ValidationError):
        InformeAnualAuditorDocument.model_validate(data)


@pytest.mark.parametrize(("str_key", "str_tag", "int_limit"), LIST_LIMITS)
def test_export_list_at_upload_limit_keeps_every_block(
    str_key: str, str_tag: str, int_limit: int
) -> None:
    """Export a list at its upload limit (Table A) keeps every block."""
    wrapper = _inform(_with_items(str_key, int_limit)).find(f"{NS}{str_key.upper()}")
    assert len(wrapper.findall(f"{NS}{str_tag}")) == int_limit


@pytest.mark.parametrize(("str_key", "str_tag", "int_limit"), LIST_LIMITS)
def test_document_rejects_list_one_over_upload_limit(
    str_key: str, str_tag: str, int_limit: int
) -> None:
    """Document rejects a list one block over its upload limit (Table A)."""
    with pytest.raises(ValidationError):
        InformeAnualAuditorDocument.model_validate(_with_items(str_key, int_limit + 1))
