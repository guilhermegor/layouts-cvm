"""Unit tests for the Lâmina V1 submission writer.

The expected tag lists are typed from the CVM page's sample file (PadraoXMLLamina.asp), not
derived from the models, so a field declared out of order or under the wrong name fails here.
The V1-only rules are pinned too: VERSAO 1.0, a mandatory CNPJ_FUNDO, CONC_EMISSOR, and the
absence of the tags V3 added later.
"""

from pathlib import Path
from xml.etree import ElementTree as ET  # noqa: S405

from pydantic import ValidationError
import pytest

from layouts_cvm._internal.config.schemas.lamina_v1 import LaminaV1Document
from layouts_cvm.lamina_v1 import LaminaV1


NS = "{urn:lamina}"
VALID_CNPJ = "11222333000181"

INFORM_TAGS = [
    "CNPJ_FUNDO",
    "NOME_FANTASIA",
    "END_ELETR",
    "DESC_PUB_ALVO",
    "RESTR_INV",
    "DESC_OBJET",
    "DESC_POL_INV",
    "ATIVO_EXT",
    "CRED_PRIV",
    "ALAV",
    "CONC_EMISSOR",
    "PERDAS_SIGN",
    "PL_NEGAT",
    "INV_INICIAL",
    "INV_ADIC",
    "RESG_MIN",
    "HOR_APL_RESG",
    "VALOR_PERM",
    "CARENCIA",
    "CONVERSAO",
    "PRAZO_PAGAM",
    "INFOR_TX_ADM",
    "INFOR_TX_ENTR",
    "INFOR_TX_SAIDA",
    "TX_DESEMPENHO",
    "INFOR_DESPESAS",
    "LISTA_COMP_CARTEIRA",
    "CLASSIF_RISCO",
    "INFOR_TAB_RENT_ANUAL",
    "LISTA_TAB_RENT_ANUAL",
    "LISTA_TAB_RENT_MENSAL",
    "FORM_CALC_RENT",
    "TAB_VAR_DESEMP",
    "INFORM_EXEMPLO_COMP",
    "TAB_SIMUL_DESPESAS",
    "TEL_SAC",
    "RECLAMACOES",
]
MONTHLY_ROW_TAGS = [
    "MES",
    "RENT_MENS",
    "VAR_MENS_IND_REF",
    "RENT_MENS_PERC_IND_REF",
    "COMENTARIOS",
]
V3_ONLY_TAGS = {
    "COD_SUBCLASSE",
    "UTILIZ_DERIV_APENAS_PROTECAO_CART",
    "PERC_MAX",
    "OBS_HOR_APL_RESG",
    "TP_PRAZO_DIAS",
    "DS_FORMA_REMUN_DISTR",
    "PRINC_DISTR_OFERTA",
    "PRINC_CONFLITO_INTERES",
    "INFO_ADIC",
}


def _inform(**overrides: object) -> dict[str, object]:
    """Build the mandatory fields of one INFORM; keyword overrides replace or add fields."""
    base: dict[str, object] = {
        "cnpj_fundo": VALID_CNPJ,
        "nome_fantasia": "Fundo Alfa",
        "end_eletr": "www.alfa.com.br",
        "desc_pub_alvo": "Investidores em geral",
        "restr_inv": "Nenhuma",
        "desc_objet": "Superar o CDI",
        "desc_pol_inv": "Titulos publicos",
        "ativo_ext": "10",
        "cred_priv": "20",
        "alav": "200",
        "conc_emissor": "30",
        "perdas_sign": "N",
        "pl_negat": "N",
        "inv_inicial": "100",
        "inv_adic": "50",
        "resg_min": "10",
        "hor_apl_resg": "14:30",
        "valor_perm": "0",
        "conversao": {"abert_fech": "A", "dia_aplic": 1, "abert_fech_c": "F", "dia_resg": 2},
        "prazo_pagam": 3,
        "infor_tx_adm": {"tipo_tx_adm": "F", "tx_adm": "1.5"},
        "tx_desempenho": "20% do que exceder o CDI",
        "classif_risco": 3,
        "tel_sac": "1140041234",
        "reclamacoes": "sac@alfa.com.br",
    }
    base.update(overrides)
    return base


def _full_inform_head() -> dict[str, object]:
    """First half of the fully populated INFORM fields."""
    return {
        "carencia": {"dias_car": 30, "cond_car": "Sem resgate"},
        "infor_tx_entr": {"tx_entr": "0.5", "cond_entr": "Sobre a aplicacao"},
        "infor_tx_saida": {"dias_saida": 10, "tx_saida": "1", "cond_saida": "Antes de 10 dias"},
        "infor_despesas": {
            "despesas": "0.75",
            "inic_periodo": "01/01/2024",
            "fim_periodo": "31/12/2024",
            "end_elet_adm": "www.adm.com.br",
        },
        "lista_comp_carteira": {
            "pl_fundo": "1000000.5",
            "comp_carteira": [{"especie_ativo": "Titulos publicos", "perc_pl": "100"}],
        },
    }


def _full_inform_tail() -> dict[str, object]:
    """Second half of the fully populated INFORM fields."""
    return {
        "infor_tab_rent_anual": {
            "rent_5anos": "45.1234",
            "ind_refer": "CDI",
            "rent_ind_ref": "40",
            "anos_abaixo": 1,
            "inic_funcio": "15/03/2021",
            "antes_inic2": {"ano": [2019, 2020]},
        },
        "lista_tab_rent_anual": {
            "tab_rent_anual": [{"ano_rent": 2023, "rent_liq": "-1.5", "var_ind_ref": "13"}]
        },
        "lista_tab_rent_mensal": {
            "tab_rent_mensal": [
                {
                    "mes": 1,
                    "rent_mens": "0.8",
                    "var_mens_ind_ref": "0.9",
                    "rent_mens_perc_ind_ref": "88.8888",
                    "comentarios": "Janeiro",
                },
                {"mes": 12, "rent_mens": "-0.1"},
            ]
        },
        "form_calc_rent": "Cota liquida de despesas",
        "tab_var_desemp": {"var_desemp": "5", "formula_rentab": "Indice mais spread"},
        "inform_exemplo_comp": {
            "ano_ant": 2023,
            "ano_emiss": 2024,
            "valor_resg": "1000",
            "impostos": "15.55",
            "valor_despesas": "12.3",
        },
        "tab_simul_despesas": {
            "desp_prev3": "30",
            "desp_prev5": "50",
            "retor_brut3": "-4.5",
            "retor_brut5": "60",
        },
    }


def _full_inform() -> dict[str, object]:
    """Build an INFORM with every optional block and field filled."""
    return _inform(**_full_inform_head(), **_full_inform_tail())


def _doc(*informs: dict[str, object], **header: object) -> LaminaV1Document:
    """Build a V1 document around the given INFORM dicts."""
    head = {"dt_compt": "01/2025", "dt_gerac_arq": "15/01/2025", **header}
    return LaminaV1Document.model_validate({"header": head, "informs": list(informs)})


def _root(doc: LaminaV1Document) -> ET.Element:
    """Export a document and parse the XML back."""
    return ET.fromstring(LaminaV1().export(doc).split("\n", 1)[1])  # type: ignore[union-attr]  # noqa: S314


def _pairs(element: ET.Element) -> list[tuple[str, str | None]]:
    """Return (tag, text) for each child, with the namespace stripped."""
    return [(child.tag.removeprefix(NS), child.text) for child in element]


def _first_inform(doc: LaminaV1Document) -> ET.Element:
    """Return the first INFORM element of an exported document."""
    return _root(doc).find(f"{NS}LISTA_INFORM/{NS}INFORM")  # type: ignore[return-value]


REJECTED_INFORMS = {
    "subclass code does not exist in V1": {"cod_subclasse": "SUB1"},
    "v3 only tag perc_max": {"perc_max": "100"},
    "v3 only tag tp_prazo_dias": {"tp_prazo_dias": "1"},
    "v3 only tag info_adic": {"info_adic": "x"},
    "cnpj with wrong check digits": {"cnpj_fundo": "11222333000182"},
    "v2 monthly column names": {
        "lista_tab_rent_mensal": {"tab_rent_mensal": [{"mes": 1, "rent_liq": "1"}]}
    },
    "thirteen monthly rows": {
        "lista_tab_rent_mensal": {"tab_rent_mensal": [{"mes": 1, "rent_mens": "1"}] * 13}
    },
    "repeated month": {
        "lista_tab_rent_mensal": {
            "tab_rent_mensal": [{"mes": 1, "rent_mens": "1"}, {"mes": 1, "rent_mens": "2"}]
        }
    },
    "month out of range": {
        "lista_tab_rent_mensal": {"tab_rent_mensal": [{"mes": 13, "rent_mens": "1"}]}
    },
    "monthly index column without ind_refer": {
        "lista_tab_rent_mensal": {
            "tab_rent_mensal": [{"mes": 1, "rent_mens": "1", "var_mens_ind_ref": "1"}]
        }
    },
    "annual index column without ind_refer": {
        "lista_tab_rent_anual": {
            "tab_rent_anual": [{"ano_rent": 2023, "rent_liq": "1", "var_ind_ref": "1"}]
        }
    },
    "repeated annual year": {
        "lista_tab_rent_anual": {
            "tab_rent_anual": [
                {"ano_rent": 2023, "rent_liq": "1"},
                {"ano_rent": 2023, "rent_liq": "2"},
            ]
        }
    },
    "year both reported and pre-fund": {
        "infor_tab_rent_anual": {"antes_inic2": {"ano": [2023]}},
        "lista_tab_rent_anual": {"tab_rent_anual": [{"ano_rent": 2023, "rent_liq": "1"}]},
    },
    "float for a decimal field": {"ativo_ext": 10.5},
    "percentage over 100": {"conc_emissor": "100.0001"},
    "fixed fee with variable fields": {
        "infor_tx_adm": {"tipo_tx_adm": "F", "tx_adm": "1", "tx_min": "1"}
    },
    "text over the page length": {"nome_fantasia": "x" * 501},
    "reclamacoes over fifty characters": {"reclamacoes": "x" * 51},
    "risk out of scale": {"classif_risco": 6},
    "loss flag not S or N": {"perdas_sign": "X"},
}


@pytest.mark.parametrize("overrides", REJECTED_INFORMS.values(), ids=REJECTED_INFORMS.keys())
def test_inform_rejects_invalid_input(overrides: dict[str, object]) -> None:
    """Refuse each input the page forbids."""
    with pytest.raises(ValidationError):
        _doc(_inform(**overrides))


@pytest.mark.parametrize("missing", ["cnpj_fundo", "conc_emissor", "alav"])
def test_inform_rejects_missing_mandatory_tag(missing: str) -> None:
    """Tags the page does not mark optional are required."""
    base = _inform()
    del base[missing]
    with pytest.raises(ValidationError):
        _doc(base)


def test_export_declares_windows_1252_prolog() -> None:
    """The prolog matches the page's sample."""
    xml = LaminaV1().export(_doc(_inform()))
    assert xml.startswith('<?xml version="1.0" encoding="windows-1252"?>\n')


def test_export_declares_the_lamina_namespace() -> None:
    """The root carries the namespace of the page's sample file."""
    assert '<DOC_ARQ xmlns="urn:lamina">' in LaminaV1().export(_doc(_inform()))


def test_header_block_xml_stamps_code_24_and_version_1() -> None:
    """CAB_INFORM carries 24, 1.0, the competence and the generation date, in that order."""
    header = _root(_doc(_inform())).find(f"{NS}CAB_INFORM")
    assert _pairs(header) == [
        ("COD_DOC", "24"),
        ("VERSAO", "1.0"),
        ("DT_COMPT", "01/2025"),
        ("DT_GERAC_ARQ", "15/01/2025"),
    ]


def test_fully_populated_inform_emits_every_tag_in_sample_order() -> None:
    """Every top-level INFORM tag appears once, in the order of the page's sample file."""
    tags = [tag for tag, _ in _pairs(_first_inform(_doc(_full_inform())))]
    assert tags == INFORM_TAGS


def test_inform_writes_no_v3_only_tag() -> None:
    """No tag introduced after V1 is written."""
    tags = {tag for tag, _ in _pairs(_first_inform(_doc(_full_inform())))}
    assert not V3_ONLY_TAGS & tags


def test_minimal_inform_writes_no_optional_tag() -> None:
    """With only mandatory data no optional tag is written, not even empty."""
    tags = [tag for tag, _ in _pairs(_first_inform(_doc(_inform())))]
    optional = {"CARENCIA", "INFOR_TX_ENTR", "LISTA_TAB_RENT_MENSAL", "TAB_SIMUL_DESPESAS"}
    assert not optional & set(tags)


def test_monthly_row_uses_the_sample_file_column_names() -> None:
    """The monthly row follows the sample file's names (RENT_MENS...), not the tag list's."""
    inform = _first_inform(_doc(_full_inform()))
    row = inform.find(f"{NS}LISTA_TAB_RENT_MENSAL/{NS}TAB_RENT_MENSAL")
    assert [tag for tag, _ in _pairs(row)] == MONTHLY_ROW_TAGS


def test_decimal_scales_follow_the_repository_policy() -> None:
    """Percentages carry four places, money two, in comma notation."""
    pairs = dict(_pairs(_first_inform(_doc(_full_inform()))))
    assert (pairs["ATIVO_EXT"], pairs["CONC_EMISSOR"], pairs["INV_INICIAL"]) == (
        "10,0000",
        "30,0000",
        "100,00",
    )


def test_percent_excess_places_are_truncated_not_rounded() -> None:
    """A fifth decimal place is dropped without rounding."""
    pairs = dict(_pairs(_first_inform(_doc(_inform(conc_emissor="1.99999")))))
    assert pairs["CONC_EMISSOR"] == "1,9999"


def test_money_excess_places_are_truncated_not_rounded() -> None:
    """A third decimal place is dropped without rounding."""
    pairs = dict(_pairs(_first_inform(_doc(_inform(inv_inicial="1.999")))))
    assert pairs["INV_INICIAL"] == "1,99"


def test_cnpj_is_written_bare() -> None:
    """CNPJ_FUNDO carries only the fourteen digits."""
    pairs = dict(_pairs(_first_inform(_doc(_inform()))))
    assert pairs["CNPJ_FUNDO"] == VALID_CNPJ


def test_export_accepts_a_plain_mapping() -> None:
    """A mapping is validated into a document and gives the same text as the model."""
    data = {
        "header": {"dt_compt": "01/2025", "dt_gerac_arq": "15/01/2025"},
        "informs": [_inform()],
    }
    assert LaminaV1().export(data) == LaminaV1().export(_doc(_inform()))


def test_export_to_file_writes_windows_1252(tmp_path: Path) -> None:
    """A path argument writes the file encoded as windows-1252."""
    path_out = tmp_path / "lamina-v1.xml"
    LaminaV1().export(_doc(_inform(nome_fantasia="Fundo Ação")), str(path_out))
    assert "Fundo Ação" in path_out.read_bytes().decode("windows-1252")


def test_export_to_file_returns_none(tmp_path: Path) -> None:
    """Writing to a file returns nothing."""
    assert LaminaV1().export(_doc(_inform()), str(tmp_path / "lamina-v1.xml")) is None


def test_rejects_version_override() -> None:
    """VERSAO is pinned to 1.0."""
    with pytest.raises(ValidationError):
        _doc(_inform(), versao="3.0")


def test_rejects_other_document_code() -> None:
    """COD_DOC is pinned to 24."""
    with pytest.raises(ValidationError):
        _doc(_inform(), cod_doc=25)


def test_rejects_seventy_one_funds() -> None:
    """A file holds at most seventy funds."""
    informs = [_inform(cnpj_fundo=f"{n:08d}000100") for n in range(71)]
    with pytest.raises(ValidationError):
        LaminaV1Document.model_validate(
            {"header": {"dt_compt": "01/2025", "dt_gerac_arq": "15/01/2025"}, "informs": informs}
        )


def test_rejects_the_same_fund_twice() -> None:
    """One CNPJ cannot appear twice in a file."""
    with pytest.raises(ValidationError):
        _doc(_inform(), _inform())
