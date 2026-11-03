"""Unit tests for the Perfil Mensal V3 submission writer.

Pin the tag order and decimal scales to PadraoXMLPerfilV3.asp and cover the V3-only rules
(VERSAO 3.0, DISTR_PATRIM mandatory with all 16 percentages).
"""

from pathlib import Path
import re

from pydantic import ValidationError
import pytest

from layouts_cvm import (
    ClientCount,
    NominalRiskBlock,
    NominalRiskFactor,
    OtcOperation,
    PerfilMensal,
    PerfilMensalDocument,
    PerfilMensalV3,
    PerfilMensalV3Document,
    PerfilMensalV3Header,
    PerfilMensalV3PatrimonyDistribution,
    PerfilMensalV3Row,
    PerformanceFeeDetails,
    PrimitiveRiskFactor,
    PrivateCreditIssuer,
    VarOutros,
    VarPercValCota,
)


VALID_CNPJ = "11222333000181"
PAGE_TAGS = [
    "DOC_ARQ",
    "CAB_INFORM",
    "COD_DOC",
    "DT_COMPT",
    "DT_GERAC_ARQ",
    "VERSAO",
    "PERFIL_MENSAL",
    "ROW_PERFIL",
    "CNPJ_FDO",
    "NR_CLIENT",
    "NR_PF_PRIV_BANK",
    "NR_PF_VARJ",
    "NR_PJ_N_FINANC_PRIV_BANK",
    "NR_PJ_N_FINANC_VARJ",
    "NR_BNC_COMERC",
    "NR_PJ_CORR_DIST",
    "NR_PJ_OUTR_FINANC",
    "NR_INV_N_RES",
    "NR_ENT_AB_PREV_COMPL",
    "NR_ENT_FC_PREV_COMPL",
    "NR_REG_PREV_SERV_PUB",
    "NR_SOC_SEG_RESEG",
    "NR_SOC_CAPTLZ_ARRENDM_MERC",
    "NR_FDOS_CLUB_INV",
    "NR_COTST_DISTR_FDO",
    "NR_OUTROS_N_RELAC",
    "DISTR_PATRIM",
    "PR_PF_PRIV_BANK",
    "PR_PF_VARJ",
    "PR_PJ_N_FINANC_PRIV_BANK",
    "PR_PJ_N_FINANC_VARJ",
    "PR_BNC_COMERC",
    "PR_PJ_CORR_DIST",
    "PR_PJ_OUTR_FINANC",
    "PR_INV_N_RES",
    "PR_ENT_AB_PREV_COMPL",
    "PR_ENT_FC_PREV_COMPL",
    "PR_REG_PREV_SERV_PUB",
    "PR_SOC_SEG_RESEG",
    "PR_SOC_CAPTLZ_ARRENDM_MERC",
    "PR_FDOS_CLUB_INV",
    "PR_COTST_DISTR_FDO",
    "PR_OUTROS_N_RELAC",
    "RESM_TEOR_VT_PROFRD",
    "JUST_SUM_VT_PROFRD",
    "VAR_PERC_PL",
    "MOD_VAR_UTILIZ",
    "PRAZ_MED_CART_TIT",
    "RES_DELIB",
    "TOTAL_RECURS_EXTER",
    "TOTAL_RECURS_BR",
    "VARIACAO_PERC_VAL_COTA",
    "VAL_PERCENT",
    "LISTA_FATOR_PRIMIT_RISCO",
    "FATOR_PRIMIT_RISCO",
    "NOME_FATOR_PRIMIT_RISCO",
    "CEN_UTIL",
    "VAR_DIAR_PERC_COTA_FDO_PIOR_CEN_ESTRESS",
    "VAR_DIAR_PERC_PATRIM_FDO_VAR_N_TAXA_ANUAL",
    "VAR_DIAR_PERC_PATRIM_FDO_VAR_N_TAXA_CAMBIO",
    "VAR_PATRIM_FDO_N_PRECO_ACOES",
    "VARIACAO_DIAR_PERC_PATRIM_FDO_VAR_N_OUTROS",
    "FATOR_RISCO_OUTROS",
    "VAL_PERCENT_OUTROS",
    "VALOR_NOC_TOT_CONTRAT_DERIV_MANT_FDO",
    "VAL_COLATERAL",
    "LISTA_FATOR_RISCO_NOC",
    "FATOR_RISCO_NOC",
    "NOME_FATOR_NOC",
    "VAL_FATOR_RISCO_NOC_LONG",
    "VAL_FATOR_RISCO_NOC_SHORT",
    "LISTA_OPER_CURS_MERC_BALCAO",
    "OPER_CURS_MERC_BALCAO",
    "TP_PESSOA",
    "NR_PF_PJ_COMITENTE",
    "PARTE_RELACIONADA",
    "VALOR_PARTE",
    "TOT_ATIVOS_P_RELAC",
    "LISTA_EMISSORES_TIT_CRED_PRIV",
    "EMISSORES_TIT_CRED_PRIV",
    "TP_PESSOA_EMISSOR",
    "NR_PF_PJ_EMISSOR",
    "PARTE_RELACIONADA",
    "VALOR_PARTE",
    "TOT_ATIVOS_CRED_PRIV",
    "VED_REGUL_COBR_TAXA_PERFORM",
    "RESP_VED_REGUL_COBR_TAXA_PERFORM",
    "DATA_COTA_FUNDO",
    "VAL_COTA_FUNDO",
    "MONTANTE_DISTRIB",
    "INF_COMPL_PERFIL",
]
PATRIM_FIELDS = list(PerfilMensalV3PatrimonyDistribution.model_fields)


def _clients() -> ClientCount:
    return ClientCount(**dict.fromkeys(ClientCount.model_fields, 1))


def _patrimony(**overrides: object) -> dict[str, object]:
    return {**dict.fromkeys(PATRIM_FIELDS, "6.25"), **overrides}


def _row(**overrides: object) -> PerfilMensalV3Row:
    fields: dict[str, object] = {
        "cnpj_fdo": VALID_CNPJ,
        "nr_client": _clients(),
        "distr_patrim": PerfilMensalV3PatrimonyDistribution(**_patrimony()),
        "total_recurs_exter": "1.999",
        "total_recurs_br": "2",
        "tot_ativos_p_relac": "3.99",
        "tot_ativos_cred_priv": "4",
    }
    fields.update(overrides)
    return PerfilMensalV3Row(**fields)


def _full_row() -> PerfilMensalV3Row:
    return _row(
        resm_teor_vt_profrd="a",
        just_sum_vt_profrd="b",
        var_perc_pl="1.23456",
        mod_var_utiliz="1",
        praz_med_cart_tit="2.34567",
        res_delib="c",
        variacao_perc_val_cota=VarPercValCota(
            val_percent="1.239",
            lista_fator_primit_risco=[
                PrimitiveRiskFactor(nome_fator_primit_risco="IBOVESPA", cen_util="s")
            ],
        ),
        var_diar_perc_cota_fdo_pior_cen_estress="1.239",
        var_diar_perc_patrim_fdo_var_n_taxa_anual="1.23456",
        var_diar_perc_patrim_fdo_var_n_taxa_cambio="1.23456",
        var_patrim_fdo_n_preco_acoes="1.23456",
        variacao_diar_perc_patrim_fdo_var_n_outros=VarOutros(
            fator_risco_outros="x", val_percent_outros="1.23456"
        ),
        valor_noc_tot_contrat_deriv_mant_fdo=NominalRiskBlock(
            val_colateral="1.239",
            lista_fator_risco_noc=[
                NominalRiskFactor(
                    nome_fator_noc="DOLAR", val_fator_risco_noc_long=1, val_fator_risco_noc_short=2
                )
            ],
        ),
        lista_oper_curs_merc_balcao=[
            OtcOperation(
                tp_pessoa="PJ",
                nr_pf_pj_comitente=VALID_CNPJ,
                parte_relacionada="S",
                valor_parte="1.99",
            )
        ],
        lista_emissores_tit_cred_priv=[
            PrivateCreditIssuer(
                tp_pessoa_emissor="PJ",
                nr_pf_pj_emissor=VALID_CNPJ,
                parte_relacionada="N",
                valor_parte="2.99",
            )
        ],
        ved_regul_cobr_taxa_perform="S",
        resp_ved_regul_cobr_taxa_perform=PerformanceFeeDetails(
            data_cota_fundo="15/01/2025", val_cota_fundo="1.1234599"
        ),
        montante_distrib="5.999",
        inf_compl_perfil="d",
    )


def _doc(row: PerfilMensalV3Row | None = None) -> PerfilMensalV3Document:
    header = PerfilMensalV3Header(dt_compt="01/2025", dt_gerac_arq="15/01/2025")
    return PerfilMensalV3Document(header=header, rows=[row or _row()])


def _xml(row: PerfilMensalV3Row | None = None) -> str:
    xml = PerfilMensalV3().export(_doc(row))
    assert xml is not None
    return xml


def test_full_document_tag_sequence_matches_page_sample() -> None:
    """Emit every tag of a fully populated row in the page sample's order."""
    assert re.findall(r"<([A-Z_0-9]+)[ >]", _xml(_full_row())) == PAGE_TAGS


@pytest.mark.parametrize(
    "tag",
    ["<VERSAO>3.0</VERSAO>", "<COD_DOC>40</COD_DOC>", '<DOC_ARQ xmlns="urn:perf">'],
)
def test_header_stamps_v3_version_doc_code_and_namespace(tag: str) -> None:
    """Stamp VERSAO 3.0, COD_DOC 40 and the urn:perf namespace."""
    assert tag in _xml()


@pytest.mark.parametrize(
    "tag",
    [
        "<TOTAL_RECURS_EXTER>1,99</TOTAL_RECURS_EXTER>",
        "<VAR_PERC_PL>1,2345</VAR_PERC_PL>",
        "<PRAZ_MED_CART_TIT>2,3456</PRAZ_MED_CART_TIT>",
        "<VAL_PERCENT>1,23</VAL_PERCENT>",
        "<VAR_DIAR_PERC_COTA_FDO_PIOR_CEN_ESTRESS>1,23</VAR_DIAR_PERC_COTA_FDO_PIOR_CEN_ESTRESS>",
        "<VAR_PATRIM_FDO_N_PRECO_ACOES>1,2345</VAR_PATRIM_FDO_N_PRECO_ACOES>",
        "<VAL_COLATERAL>1,23</VAL_COLATERAL>",
        "<VALOR_PARTE>1,9</VALOR_PARTE>",
        "<TOT_ATIVOS_P_RELAC>3,9</TOT_ATIVOS_P_RELAC>",
        "<PR_PF_VARJ>6,2</PR_PF_VARJ>",
        "<VAL_COTA_FUNDO>1,12345</VAL_COTA_FUNDO>",
        "<MONTANTE_DISTRIB>5,99</MONTANTE_DISTRIB>",
    ],
)
def test_decimal_scales_follow_page_and_truncate(tag: str) -> None:
    """Truncate to the page's scale (1, 2, 4 or 5 places) and use a decimal comma."""
    assert tag in _xml(_full_row())


@pytest.mark.parametrize("field", PATRIM_FIELDS)
def test_distr_patrim_rejects_a_missing_percentage(field: str) -> None:
    """Reject a DISTR_PATRIM that leaves any of the 16 percentages out."""
    with pytest.raises(ValidationError):
        PerfilMensalV3PatrimonyDistribution(**_patrimony(**{field: None}))


def test_distr_patrim_is_required_on_the_row() -> None:
    """Reject a row without DISTR_PATRIM, which V4 allows but V3 does not."""
    with pytest.raises(ValidationError):
        _row(distr_patrim=None)


def test_distr_patrim_has_the_16_page_percentages() -> None:
    """Carry the 16 PR_* tags the page lists, no more."""
    assert len(PATRIM_FIELDS) == 16


def test_distr_patrim_rejects_percentage_above_100() -> None:
    """Reject a percentage above the page's 100 ceiling."""
    with pytest.raises(ValidationError):
        PerfilMensalV3PatrimonyDistribution(**_patrimony(pr_pf_varj="100.1"))


def test_header_rejects_other_versao() -> None:
    """Reject a header claiming another VERSAO."""
    with pytest.raises(ValidationError):
        PerfilMensalV3Header(dt_compt="01/2025", dt_gerac_arq="15/01/2025", versao="4.0")


def test_header_rejects_other_cod_doc() -> None:
    """Reject a header claiming another COD_DOC."""
    with pytest.raises(ValidationError):
        PerfilMensalV3Header(dt_compt="01/2025", dt_gerac_arq="15/01/2025", cod_doc=1)


def test_header_rejects_malformed_competence() -> None:
    """Reject a DT_COMPT that is not MM/AAAA."""
    with pytest.raises(ValidationError):
        PerfilMensalV3Header(dt_compt="2025-01", dt_gerac_arq="15/01/2025")


def test_invalid_cnpj_check_digit_is_rejected() -> None:
    """Reject a fund CNPJ whose check digits are wrong."""
    with pytest.raises(ValidationError):
        _row(cnpj_fdo="11222333000182")


def test_negative_client_count_is_rejected() -> None:
    """Reject a negative client count: the page says integer, mandatory."""
    with pytest.raises(ValidationError):
        ClientCount(**{**dict.fromkeys(ClientCount.model_fields, 1), "nr_pf_varj": -1})


def test_more_than_three_otc_counterparties_rejected() -> None:
    """Reject a fourth OPER_CURS_MERC_BALCAO: the page repeats the block up to 3 times."""
    otc = OtcOperation(
        tp_pessoa="PJ", nr_pf_pj_comitente=VALID_CNPJ, parte_relacionada="S", valor_parte="1"
    )
    with pytest.raises(ValidationError):
        _row(lista_oper_curs_merc_balcao=[otc] * 4)


def test_more_than_five_primitive_risk_factors_rejected() -> None:
    """Reject a sixth FATOR_PRIMIT_RISCO: the page repeats the block up to 5 times."""
    factor = PrimitiveRiskFactor(nome_fator_primit_risco="DOLAR", cen_util="s")
    with pytest.raises(ValidationError):
        VarPercValCota(val_percent="1", lista_fator_primit_risco=[factor] * 6)


def test_unknown_risk_factor_name_rejected() -> None:
    """Reject a factor name outside the page's five."""
    with pytest.raises(ValidationError):
        PrimitiveRiskFactor(nome_fator_primit_risco="EURO", cen_util="s")


def test_oversized_vote_summary_rejected() -> None:
    """Reject a vote summary over the page's 4,000 characters."""
    with pytest.raises(ValidationError):
        _row(resm_teor_vt_profrd="x" * 4001)


def test_oversized_complementary_info_rejected() -> None:
    """Reject complementary information over the page's 500 characters."""
    with pytest.raises(ValidationError):
        _row(inf_compl_perfil="x" * 501)


def test_export_to_file_returns_none(tmp_path: Path) -> None:
    """Return None when an output path is given."""
    assert PerfilMensalV3().export(_doc(), output_path=str(tmp_path / "perfil.xml")) is None


def test_export_writes_windows_1252_file(tmp_path: Path) -> None:
    """Write the file as windows-1252."""
    out = tmp_path / "perfil.xml"
    PerfilMensalV3().export(_doc(), output_path=str(out))
    assert (
        out.read_bytes()
        .decode("windows-1252")
        .startswith('<?xml version="1.0" encoding="windows-1252"?>')
    )


def test_export_pins_versao_even_if_header_is_mutated() -> None:
    """Emit VERSAO 3.0 even when the header was mutated to 4.0 after validation."""
    doc = _doc()
    doc.header.versao = "4.0"  # type: ignore[assignment]
    assert "<VERSAO>3.0</VERSAO>" in str(PerfilMensalV3().export(doc))


def test_v3_writer_rejects_a_v4_document() -> None:
    """Refuse a V4 document: the V3 writer is its own port adapter, not a V4 subclass."""
    v4_doc = PerfilMensalDocument.model_validate(_doc().model_dump())
    with pytest.raises(TypeError):
        PerfilMensalV3().export(v4_doc)


def test_v4_writer_stamps_its_own_versao_on_a_v3_document() -> None:
    """Pin that the V4 writer emits VERSAO 4.0 for a V3 model (V3 fields are a V4 subset)."""
    assert "<VERSAO>4.0</VERSAO>" in str(PerfilMensal().export(_doc()))
