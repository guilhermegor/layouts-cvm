"""Unit tests for the Informe Mensal FIDC (ICVM 576) submission writer.

Expected tags, order, scales and rules are taken from the CVM page
``PadraoXMLMensalFIDC576.asp``, not from the code under test.
"""

from collections.abc import Callable
from decimal import Decimal
from pathlib import Path
import re
import types
from typing import Any, Literal, Union, get_args, get_origin

from pydantic import BaseModel, ValidationError
import pytest

from layouts_cvm import InfMensalFidc
from layouts_cvm._internal.config.schemas.inf_mensal_fidc import InfMensalFidcDocument


VALID_CNPJ = "11222333000181"
VALID_CPF = "52998224725"

SPEC_LISTA_INFORM_ORDER = [
    "APLIC_ATIVO",
    "CART_SEGMT",
    "PASSIV",
    "PATRLIQ",
    "COMPMT_DICRED_AQUIS",
    "COMPMT_DICRED_SEM_AQUIS",
    "NEGOC_DICRED_MES",
    "INFORM",
    "TAXA_NEGOC_DICRED_MES",
    "OUTRAS_INFORM",
]


def _first_non_none_value(annotation: Any, name: str) -> Any:  # noqa: ANN401
    """Build a value for the first non-None member of a union annotation."""
    return _value_for(next(a for a in get_args(annotation) if a is not type(None)), name)


_VALUE_RULES: list[tuple[Callable[[Any, str], bool], Callable[[Any, str], Any]]] = [
    (lambda a, n: get_origin(a) is list, lambda a, n: [_value_for(get_args(a)[0], n)]),
    (lambda a, n: get_origin(a) is Literal, lambda a, n: get_args(a)[0]),
    (lambda a, n: get_origin(a) in (Union, types.UnionType), _first_non_none_value),
    (
        lambda a, n: isinstance(a, type) and issubclass(a, BaseModel),
        lambda a, n: _zeros(a),
    ),
    (lambda a, n: a is Decimal, lambda a, n: "0"),
    (lambda a, n: a is int, lambda a, n: 0),
    (lambda a, n: n == "dt_compt", lambda a, n: "10/2020"),
    (lambda a, n: True, lambda a, n: VALID_CNPJ),
]


def _value_for(annotation: Any, name: str) -> Any:  # noqa: ANN401
    """Build a zero/neutral value for a required field annotation."""
    build = next(build for test, build in _VALUE_RULES if test(annotation, name))
    return build(annotation, name)


def _zeros(model: type[BaseModel]) -> dict[str, Any]:
    """Build a fully-populated all-zero payload (every mandatory tag "preenchida com zero")."""
    return {
        name: _value_for(info.annotation, name)
        for name, info in model.model_fields.items()
        if info.is_required()
    }


def _keep(data: dict[str, Any]) -> None:
    """Leave the raw payload untouched."""


def _doc(mutate: Callable[[dict[str, Any]], None] = _keep) -> InfMensalFidcDocument:
    """Build a closed-fund document from zeros, optionally mutating the raw payload first."""
    data = _zeros(InfMensalFidcDocument)
    data["cab_inform"]["tp_condominio"] = "FECHADO"
    mutate(data)
    return InfMensalFidcDocument.model_validate(data)


def _xml(doc: InfMensalFidcDocument) -> str:
    """Export to a string."""
    out = InfMensalFidc().export(doc)
    assert out is not None
    return out


def _mutate_decimals(data: dict[str, Any]) -> None:
    """Inject over-scale quota quantities and unit values."""
    outras = data["lista_inform"]["outras_inform"]
    outras["desc_serie_classe"]["desc_serie_classe_senior"][0] = {
        "qt_cotas": "1234.123456789",
        "vl_cotas": "1.5",
    }
    outras["capta_resga_amorti"]["capt_mes"]["classe_senior"][0] = {
        "qt_cotas": "2.123456789",
        "vl_cotas": "10.999",
    }


def _mutate_two_series(data: dict[str, Any]) -> None:
    """Declare two senior series with five quota holders."""
    num = data["lista_inform"]["outras_inform"]["num_cotistas"]
    num.update(qt_total_cotistas=5, qt_total_cotistas_senior=5)
    num["classe_senior"] = [{"vl_classe": 2}, {"vl_classe": 3}]


def _mutate_open_fund(data: dict[str, Any]) -> None:
    """Turn the fund into an open one with redemption terms and liquidity."""
    data["cab_inform"].update(
        tp_condominio="ABERTO",
        pr_entre_resgate=30,
        tp_dias_resgate="2",
        pr_entre_conver=2,
        tp_dias_conver="1",
    )
    data["lista_inform"]["outras_inform"]["liquidez"] = {"vl_ativ_liqdez": "1.00"}


def _mutate_net_equity(data: dict[str, Any]) -> None:
    """Set a non-zero net equity with excess decimals."""
    data["lista_inform"]["patrliq"].update(vl_som_patrliq="100.99", vl_patrim_liq="100.999")


def _set_sacado_document(data: dict[str, Any], str_document: str) -> None:
    """Set the first debtor's document."""
    sac = data["lista_inform"]["inform"]["lista_dev_sacados"]["dev_sacados"][0]
    sac["nr_pf_pj_sacado_deved_1"] = str_document


def _mutate_sacado_placeholder(data: dict[str, Any]) -> None:
    """Use the prescribed placeholder for a debtor without CNPJ."""
    _set_sacado_document(data, "99.999.999/9999-99")


def _mutate_sacado_cpf(data: dict[str, Any]) -> None:
    """Use a valid CPF as the debtor document."""
    _set_sacado_document(data, VALID_CPF)


def _mutate_sacado_invalid(data: dict[str, Any]) -> None:
    """Use an invalid CPF as the debtor document."""
    _set_sacado_document(data, "12345678901")


def _mutate_provision(data: dict[str, Any]) -> None:
    """Make the provision exceed the credits it covers."""
    data["lista_inform"]["aplic_ativo"]["cred_existe"]["vl_provis_reduc_recup"] = "5.00"


def _mutate_holder_total(data: dict[str, Any]) -> None:
    """Make the senior holder total disagree with the series counts."""
    num = data["lista_inform"]["outras_inform"]["num_cotistas"]
    num.update(qt_total_cotistas=3, qt_total_cotistas_senior=3)


def _mutate_no_sacado(data: dict[str, Any]) -> None:
    """Remove every debtor."""
    data["lista_inform"]["inform"]["lista_dev_sacados"]["dev_sacados"] = []


def _mutate_no_senior_series(data: dict[str, Any]) -> None:
    """Remove every senior series from the monthly return."""
    data["lista_inform"]["outras_inform"]["rent_mes"]["rent_classe_senior"] = []


@pytest.fixture
def xml_closed() -> str:
    """Return the minimal closed-fund XML."""
    return _xml(_doc())


def test_export_minimal_document_starts_with_prolog_and_root(xml_closed: str) -> None:
    """The envelope follows the template of the page."""
    assert xml_closed.startswith(
        '<?xml version="1.0" encoding="windows-1252"?>\n<DOC_ARQ xmlns="urn:fidc">'
    )


def test_export_minimal_document_ends_with_root_close(xml_closed: str) -> None:
    """The envelope closes the root element."""
    assert xml_closed.endswith("</DOC_ARQ>")


def test_export_minimal_document_header_tags_follow_spec_order(xml_closed: str) -> None:
    """CAB_INFORM follows the template of the page."""
    header_tags = re.findall("<(\\w+)>", xml_closed.split("</CAB_INFORM>")[0])
    assert header_tags == [
        "CAB_INFORM",
        "DT_COMPT",
        "NR_CNPJ_ADM",
        "NR_CNPJ_FUNDO",
        "TP_CONDOMINIO",
        "FDO_EXCL",
        "COTST_VINCUL",
    ]


def test_export_minimal_document_emits_competence(xml_closed: str) -> None:
    """DT_COMPT is emitted as MM/AAAA."""
    assert "<DT_COMPT>10/2020</DT_COMPT>" in xml_closed


def test_export_closed_fund_omits_redemption_terms(xml_closed: str) -> None:
    """A closed fund carries no PR_ENTRE_RESGATE."""
    assert "PR_ENTRE_RESGATE" not in xml_closed


def test_export_lista_inform_children_follow_template_order(xml_closed: str) -> None:
    """LISTA_INFORM children appear in the page's order, each exactly once."""
    body = xml_closed.split("<LISTA_INFORM>")[1].split("</LISTA_INFORM>")[0]
    top = re.findall(r"^ {8}<(\w+)>", body, flags=re.MULTILINE)
    assert top == SPEC_LISTA_INFORM_ORDER


@pytest.mark.parametrize(
    "fragment", ["<NUM_COTISTAS_DESC></NUM_COTISTAS_DESC>", "<DESEMP></DESEMP>"]
)
def test_export_mandatory_empty_blocks_are_emitted_as_empty_tags(
    xml_closed: str, fragment: str
) -> None:
    """Tabela X items 3 and 7: NUM_COTISTAS_DESC and DESEMP are mandatory but may be empty."""
    assert fragment in xml_closed


def test_export_omits_lista_cedent_when_absent(xml_closed: str) -> None:
    """An absent optional block is not emitted."""
    assert "<LISTA_CEDENT>" not in xml_closed


@pytest.mark.parametrize(
    "fragment",
    [
        "<QT_COTAS>1234,12345678</QT_COTAS>",
        "<VL_COTAS>1,50000000</VL_COTAS>",
        "<QT_COTAS>2,12345678</QT_COTAS>",
        "<VL_COTAS>10,99</VL_COTAS>",
        "<VL_DISPONIB>0,00</VL_DISPONIB>",
    ],
)
def test_export_decimals_use_comma_and_spec_scales(fragment: str) -> None:
    """2 casas for money, up to 8 for quota unit values/quantities; excess is truncated."""
    assert fragment in _xml(_doc(_mutate_decimals))


def test_export_repeats_one_class_per_series() -> None:
    """One CLASSE_SENIOR per series."""
    assert _xml(_doc(_mutate_two_series)).count("<VL_CLASSE>") == 2


@pytest.mark.parametrize(
    "tag",
    [
        "<TAXA_NEGOC_DICRED_MES_AQUIS_DESC_COMPRA>",
        "<TAXA_NEGOC_DICRED_MES_ATIV_RF_JUROS_VENDA>",
    ],
)
def test_export_block_prefixed_tags_keep_their_page_names(tag: str) -> None:
    """Block-prefixed tags keep their page names."""
    assert tag in _xml(_doc(_mutate_two_series))


@pytest.mark.parametrize(
    "fragment",
    [
        "<PR_ENTRE_RESGATE>30</PR_ENTRE_RESGATE>",
        "<TP_DIAS_CONVER>1</TP_DIAS_CONVER>",
        "<VL_ATIV_LIQDEZ>1,00</VL_ATIV_LIQDEZ>",
    ],
)
def test_export_open_fund_emits_redemption_terms_and_liquidity(fragment: str) -> None:
    """Open funds carry the four PR_/TP_ tags and at least one LIQUIDEZ field."""
    assert fragment in _xml(_doc(_mutate_open_fund))


def test_export_open_fund_omits_unfilled_liquidity_fields() -> None:
    """Only the filled LIQUIDEZ field is emitted."""
    assert "VL_ATIV_LIQDEZ_30" not in _xml(_doc(_mutate_open_fund))


def test_export_to_file_returns_none(tmp_path: Path) -> None:
    """With an output path nothing is returned."""
    target = tmp_path / "fidc.xml"
    assert InfMensalFidc().export(_doc(), str(target)) is None


def test_export_to_file_writes_windows_1252(tmp_path: Path) -> None:
    """With an output path the file is written in windows-1252."""
    target = tmp_path / "fidc.xml"
    InfMensalFidc().export(_doc(), str(target))
    assert target.read_bytes().decode("windows-1252").startswith("<?xml")


def test_totals_that_match_the_spec_sums_are_accepted() -> None:
    """Item 16 (net equity) with a non-zero value and the 4,2-scale truncation."""
    assert "<VL_SOM_PATRLIQ>100,99</VL_SOM_PATRLIQ>" in _xml(_doc(_mutate_net_equity))


def test_sacado_with_placeholder_document_is_accepted() -> None:
    """The page prescribes 99.999.999/9999-99 for debtors with no CNPJ."""
    assert "99.999.999/9999-99" in _xml(_doc(_mutate_sacado_placeholder))


def test_invalid_fund_cnpj_is_rejected() -> None:
    """CNPJ with bad check digits fails the page's CPF/CNPJ validity rule."""
    with pytest.raises(ValidationError, match="CNPJ"):
        _doc(lambda d: d["cab_inform"].update(nr_cnpj_fundo="11222333000182"))


@pytest.mark.parametrize("value", ["2020-10", "13/2020", "10/20", "00/2020"])
def test_competence_must_be_mm_aaaa(value: str) -> None:
    """DT_COMPT is MM/AAAA."""
    with pytest.raises(ValidationError, match="MM/AAAA"):
        _doc(lambda d: d["cab_inform"].update(dt_compt=value))


def test_closed_fund_must_not_carry_redemption_terms() -> None:
    """Cabeçalho item 1: the four tags are restricted to open funds."""
    with pytest.raises(ValidationError, match="open funds"):
        _doc(lambda d: d["cab_inform"].update(pr_entre_resgate=30))


def test_open_fund_without_liquidity_is_rejected() -> None:
    """Open fund: 'no item Liquidez, pelo menos um dos campos deve ser preenchido'."""
    with pytest.raises(ValidationError, match="LIQUIDEZ"):
        _doc(lambda d: d["cab_inform"].update(tp_condominio="ABERTO"))


def test_somatorio_that_disagrees_with_its_terms_is_rejected() -> None:
    """Item 16: VL_SOM_PATRLIQ must equal the net equity."""
    with pytest.raises(ValidationError, match="SOMATÓRIO"):
        _doc(lambda d: d["lista_inform"]["patrliq"].update(vl_patrim_liq="10.00"))


def test_provision_above_covered_credits_is_rejected() -> None:
    """The provision must be <= the sum of the credits it covers."""
    with pytest.raises(ValidationError, match="PROVIS"):
        _doc(_mutate_provision)


def test_quota_holder_total_must_match_series_counts() -> None:
    """Tabela X item 4: QT_TOTAL_COTISTAS_SENIOR is the sum of the series' VL_CLASSE."""
    with pytest.raises(ValidationError, match="QT_TOTAL_COTISTAS_SENIOR"):
        _doc(_mutate_holder_total)


def test_sacado_with_invalid_document_is_rejected() -> None:
    """Debtor documents must be valid CPF/CNPJ (or the prescribed placeholders)."""
    with pytest.raises(ValidationError, match="CPF/CNPJ"):
        _doc(_mutate_sacado_invalid)


def test_informe_without_any_sacado_is_rejected() -> None:
    """'Não aceitar o envio sem ter pelo menos a informação de um Sacado/Devedor'."""
    with pytest.raises(ValidationError, match=r"(?s)dev_sacados.*at least 1 item"):
        _doc(_mutate_no_sacado)


def test_informe_without_senior_series_is_rejected() -> None:
    """Tabela X item 5: at least one senior series is mandatory."""
    with pytest.raises(ValidationError, match=r"(?s)rent_classe_senior.*at least 1 item"):
        _doc(_mutate_no_senior_series)


def test_unknown_tag_is_rejected() -> None:
    """Blocks forbid extra fields, so a misspelt tag cannot be silently dropped."""
    with pytest.raises(ValidationError, match=r"(?s)vl_patrim_liquido.*Extra inputs"):
        _doc(lambda d: d["lista_inform"]["patrliq"].update(vl_patrim_liquido="1"))


def test_cpf_sacado_is_accepted() -> None:
    """A valid CPF is a legal debtor document."""
    assert VALID_CPF in _xml(_doc(_mutate_sacado_cpf))


def _break_two_acquisition_sums(data: dict[str, Any]) -> None:
    """Break items 23/24 value and items 25/26 quantity at once."""
    negoc = data["lista_inform"]["negoc_dicred_mes"]
    negoc["aquisicoes"]["qt_dicred_aquis"] = 3
    negoc["aquisicoes"]["vl_dicred_aquis"] = 5
    negoc["negoc_dicred_mes_aquis"]["qt_dicred_aquis"] = 3


def test_items_23_to_29_report_the_first_failing_check_in_field_order() -> None:
    """Items 25/26 quantity is reported before items 23/24 value, as the field loop orders them."""
    with pytest.raises(ValidationError, match=r"NEGOC_DICRED_MES_AQUIS\.QT_DICRED_AQUIS"):
        _doc(_break_two_acquisition_sums)
