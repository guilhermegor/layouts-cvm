"""Unit tests for the Lâmina V2 submission writer.

The expected tag lists are typed from the CVM page's sample file
(PadraoXMLLaminaV2.asp), not derived from the models, so a field declared out of order or
under the wrong name fails here. The V2-only rules are pinned too: VERSAO 2.0, a mandatory
CNPJ_FUNDO with no COD_SUBCLASSE, and the monthly table that reuses the annual column names.
"""

from pathlib import Path
from xml.etree import ElementTree as ET  # noqa: S405

from pydantic import ValidationError
import pytest

from layouts_cvm import Lamina, LaminaV2
from layouts_cvm._internal.config.schemas.lamina_v2 import LaminaV2Document


NS = "{urn:lamina}"
VALID_CNPJ = "11222333000181"
OTHER_CNPJ = "11444777000161"

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
    "UTILIZ_DERIV_APENAS_PROTECAO_CART",
    "PERDAS_SIGN",
    "PL_NEGAT",
    "PERC_MAX",
    "INV_INICIAL",
    "INV_ADIC",
    "RESG_MIN",
    "HOR_APL_RESG",
    "OBS_HOR_APL_RESG",
    "VALOR_PERM",
    "CARENCIA",
    "CONVERSAO",
    "TP_PRAZO_DIAS",
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
    "DS_FORMA_REMUN_DISTR",
    "PRINC_DISTR_OFERTA",
    "PRINC_CONFLITO_INTERES",
    "TEL_SAC",
    "RECLAMACOES",
    "INFO_ADIC",
]
MONTHLY_ROW_TAGS = ["MES", "RENT_LIQ", "VAR_IND_REF", "RENT_PERC_IND_REF", "COMENTARIOS"]


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
        "utiliz_deriv_apenas_protecao_cart": "S",
        "perdas_sign": "N",
        "pl_negat": "N",
        "perc_max": "100",
        "inv_inicial": "100",
        "inv_adic": "50",
        "resg_min": "10",
        "hor_apl_resg": "14:30",
        "obs_hor_apl_resg": "Ate as 14h30",
        "valor_perm": "0",
        "conversao": {"abert_fech": "A", "dia_aplic": 1, "abert_fech_c": "F", "dia_resg": 2},
        "tp_prazo_dias": "1",
        "prazo_pagam": 3,
        "infor_tx_adm": {"tipo_tx_adm": "F", "tx_adm": "1.5"},
        "tx_desempenho": "20% do que exceder o CDI",
        "classif_risco": 3,
        "ds_forma_remun_distr": "Parte da taxa de administracao",
        "princ_distr_oferta": "Nao",
        "princ_conflito_interes": "Nenhum",
        "tel_sac": "1140041234",
        "reclamacoes": "sac@alfa.com.br",
        "info_adic": "Nada a declarar",
    }
    base.update(overrides)
    return base


def _full_inform_head() -> dict[str, object]:
    """First half of the fully populated INFORM fields."""
    return {
        "alav": "200",
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
            "tab_rent_anual": [
                {
                    "ano_rent": 2023,
                    "rent_liq": "-1.5",
                    "var_ind_ref": "13",
                    "rent_perc_ind_ref": "-11.5",
                    "comentarios": "Ano dificil",
                },
            ]
        },
        "lista_tab_rent_mensal": {
            "tab_rent_mensal": [
                {
                    "mes": 1,
                    "rent_liq": "0.8",
                    "var_ind_ref": "0.9",
                    "rent_perc_ind_ref": "88.8888",
                    "comentarios": "Janeiro",
                },
                {"mes": 12, "rent_liq": "-0.1"},
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


def _doc(*informs: dict[str, object], **header: object) -> LaminaV2Document:
    """Build a V2 document around the given INFORM dicts."""
    head = {"dt_compt": "01/2025", "dt_gerac_arq": "15/01/2025", **header}
    return LaminaV2Document.model_validate({"header": head, "informs": list(informs)})


def _root(doc: LaminaV2Document) -> ET.Element:
    """Export a document and parse the XML back."""
    return ET.fromstring(LaminaV2().export(doc).split("\n", 1)[1])  # type: ignore[union-attr]  # noqa: S314


def _pairs(element: ET.Element) -> list[tuple[str, str | None]]:
    """Return (tag, text) for each child, with the namespace stripped."""
    return [(child.tag.removeprefix(NS), child.text) for child in element]


def _first_inform(doc: LaminaV2Document) -> ET.Element:
    """Return the first INFORM element of an exported document."""
    return _root(doc).find(f"{NS}LISTA_INFORM/{NS}INFORM")  # type: ignore[return-value]


def _first_monthly_row(doc: LaminaV2Document) -> ET.Element:
    """Return the first TAB_RENT_MENSAL element of the first INFORM."""
    return _first_inform(doc).find(f"{NS}LISTA_TAB_RENT_MENSAL/{NS}TAB_RENT_MENSAL")  # type: ignore[return-value]


REJECTED_INFORMS = {
    "subclass code does not exist in V2": {"cod_subclasse": "SUB1"},
    "cnpj with wrong check digits": {"cnpj_fundo": "11222333000182"},
    "v3 monthly column names": {
        "lista_tab_rent_mensal": {"tab_rent_mensal": [{"mes": 1, "rent_mens": "1"}]}
    },
    "thirteen monthly rows": {
        "lista_tab_rent_mensal": {"tab_rent_mensal": [{"mes": 1, "rent_liq": "1"}] * 13}
    },
    "repeated month": {
        "lista_tab_rent_mensal": {
            "tab_rent_mensal": [{"mes": 1, "rent_liq": "1"}, {"mes": 1, "rent_liq": "2"}]
        }
    },
    "month out of range": {
        "lista_tab_rent_mensal": {"tab_rent_mensal": [{"mes": 13, "rent_liq": "1"}]}
    },
    "monthly index column without ind_refer": {
        "lista_tab_rent_mensal": {
            "tab_rent_mensal": [{"mes": 1, "rent_liq": "1", "var_ind_ref": "1"}]
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
    "unknown field": {"campo_inexistente": "x"},
    "float for a decimal field": {"ativo_ext": 10.5},
    "fixed fee with variable fields": {
        "infor_tx_adm": {"tipo_tx_adm": "F", "tx_adm": "1", "tx_min": "1"}
    },
    "text over the page length": {"nome_fantasia": "x" * 501},
}


@pytest.mark.parametrize("overrides", REJECTED_INFORMS.values(), ids=REJECTED_INFORMS.keys())
def test_inform_rejects_invalid_input(overrides: dict[str, object]) -> None:
    """Refuse each input the page or the inherited V3 rules forbid."""
    with pytest.raises(ValidationError):
        _doc(_inform(**overrides))


def test_export_declares_windows_1252_prolog() -> None:
    """The prolog matches the page's sample."""
    xml = LaminaV2().export(_doc(_inform()))
    assert xml.startswith('<?xml version="1.0" encoding="windows-1252"?>\n')


def test_export_declares_the_lamina_namespace() -> None:
    """The root carries the namespace of the page's sample file."""
    xml = LaminaV2().export(_doc(_inform()))
    assert '<DOC_ARQ xmlns="urn:lamina">' in xml


def test_header_block_xml_stamps_code_24_and_version_2() -> None:
    """CAB_INFORM carries 24, 2.0, the competence and the generation date, in that order."""
    header = _root(_doc(_inform())).find(f"{NS}CAB_INFORM")
    assert _pairs(header) == [
        ("COD_DOC", "24"),
        ("VERSAO", "2.0"),
        ("DT_COMPT", "01/2025"),
        ("DT_GERAC_ARQ", "15/01/2025"),
    ]


def test_fully_populated_inform_emits_every_tag_in_sample_order() -> None:
    """Every top-level INFORM tag appears once, in the order of the page's sample file."""
    tags = [tag for tag, _ in _pairs(_first_inform(_doc(_full_inform())))]
    assert tags == INFORM_TAGS


def test_minimal_inform_writes_no_optional_tag() -> None:
    """With only mandatory data no optional tag is written, not even empty."""
    tags = [tag for tag, _ in _pairs(_first_inform(_doc(_inform())))]
    optional = {"ALAV", "CARENCIA", "INFOR_TX_ENTR", "LISTA_TAB_RENT_MENSAL", "COD_SUBCLASSE"}
    assert not optional & set(tags)


def test_monthly_row_uses_the_annual_column_names() -> None:
    """V2 names the monthly columns RENT_LIQ/VAR_IND_REF/RENT_PERC_IND_REF, not the V3 names."""
    tags = [tag for tag, _ in _pairs(_first_monthly_row(_doc(_full_inform())))]
    assert tags == MONTHLY_ROW_TAGS


def test_monthly_row_values_are_comma_decimals_at_percentage_scale() -> None:
    """Monthly returns keep four decimal places and a comma separator."""
    pairs = dict(_pairs(_first_monthly_row(_doc(_full_inform()))))
    assert pairs["RENT_PERC_IND_REF"] == "88,8888"


def test_percent_scale_is_four_places() -> None:
    """A percentage is written with exactly four decimal places."""
    pairs = dict(_pairs(_first_inform(_doc(_full_inform()))))
    assert pairs["ATIVO_EXT"] == "10,0000"


def test_money_scale_is_two_places() -> None:
    """A money value is written with exactly two decimal places."""
    pairs = dict(_pairs(_first_inform(_doc(_inform(inv_inicial="100")))))
    assert pairs["INV_INICIAL"] == "100,00"


def test_percent_excess_places_are_truncated_not_rounded() -> None:
    """A fifth decimal place is dropped without rounding."""
    pairs = dict(_pairs(_first_inform(_doc(_inform(ativo_ext="1.99999")))))
    assert pairs["ATIVO_EXT"] == "1,9999"


def test_money_excess_places_are_truncated_not_rounded() -> None:
    """A third decimal place is dropped without rounding."""
    pairs = dict(_pairs(_first_inform(_doc(_inform(inv_inicial="1.999")))))
    assert pairs["INV_INICIAL"] == "1,99"


def test_cnpj_is_written_bare() -> None:
    """CNPJ_FUNDO carries only the fourteen digits."""
    pairs = dict(_pairs(_first_inform(_doc(_inform()))))
    assert pairs["CNPJ_FUNDO"] == VALID_CNPJ


def test_writer_matches_the_v3_writer_for_a_v2_document() -> None:
    """The V2 writer delegates to the V3 walk, so both emit identical text for one document."""
    doc = _doc(_inform())
    assert LaminaV2().export(doc) == Lamina().export(doc)


def test_export_to_file_writes_windows_1252(tmp_path: Path) -> None:
    """A path argument writes the encoded file and returns None."""
    path_out = tmp_path / "lamina-v2.xml"
    LaminaV2().export(_doc(_inform(nome_fantasia="Fundo Ação")), str(path_out))
    assert "Fundo Ação" in path_out.read_bytes().decode("windows-1252")


def test_export_to_file_returns_none(tmp_path: Path) -> None:
    """Writing to a file returns nothing."""
    assert LaminaV2().export(_doc(_inform()), str(tmp_path / "lamina-v2.xml")) is None


def test_rejects_missing_cnpj() -> None:
    """CNPJ_FUNDO is mandatory in V2."""
    base = _inform()
    del base["cnpj_fundo"]
    with pytest.raises(ValidationError):
        _doc(base)


def test_accepts_monthly_index_column_with_reference_index() -> None:
    """The same row passes once IND_REFER is declared."""
    row = {"mes": 1, "rent_liq": "1", "var_ind_ref": "1"}
    doc = _doc(
        _inform(
            infor_tab_rent_anual={"ind_refer": "CDI"},
            lista_tab_rent_mensal={"tab_rent_mensal": [row]},
        )
    )
    assert doc.informs[0].lista_tab_rent_mensal.tab_rent_mensal[0].var_ind_ref is not None


def test_rejects_version_override() -> None:
    """VERSAO is pinned to 2.0."""
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
        LaminaV2Document.model_validate(
            {"header": {"dt_compt": "01/2025", "dt_gerac_arq": "15/01/2025"}, "informs": informs}
        )


def test_rejects_the_same_fund_twice() -> None:
    """One CNPJ cannot appear twice in a file."""
    with pytest.raises(ValidationError):
        _doc(_inform(), _inform())


def test_distinct_funds_are_accepted() -> None:
    """Two different CNPJs in one file pass."""
    doc = _doc(_inform(), _inform(cnpj_fundo=OTHER_CNPJ))
    assert len(doc.informs) == 2
