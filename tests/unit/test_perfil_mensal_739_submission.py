"""Unit tests for the Perfil Mensal ICVM 739 submission writer.

Pin the tag order and decimal scales to PadraoXMLPerfil739.asp and cover the 739-only rules
(VERSAO 1.0, no MONTANTE_DISTRIB / INF_COMPL_PERFIL, 2-decimal stress tags).
"""

from pathlib import Path
import re
from types import ModuleType

from pydantic import ValidationError
import pytest

from layouts_cvm import PerfilMensal739
from layouts_cvm._internal.config.schemas import (
    perfil_mensal as v4,
    perfil_mensal_739 as m739,
    perfil_mensal_v3 as v3,
)
from layouts_cvm._internal.config.schemas.perfil_mensal_739 import (
    PerfilMensal739ClientCount,
    PerfilMensal739Document,
    PerfilMensal739Header,
    PerfilMensal739NominalRiskBlock,
    PerfilMensal739NominalRiskFactor,
    PerfilMensal739OtcOperation,
    PerfilMensal739PatrimonyDistribution,
    PerfilMensal739PerformanceFeeDetails,
    PerfilMensal739PrimitiveRiskFactor,
    PerfilMensal739PrivateCreditIssuer,
    PerfilMensal739Row,
    PerfilMensal739VarOutros,
    PerfilMensal739VarPercValCota,
)
from layouts_cvm._internal.config.schemas.perfil_mensal_v3 import PerfilMensalV3Document


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
]
PATRIM_FIELDS = list(PerfilMensal739PatrimonyDistribution.model_fields)


def _clients() -> PerfilMensal739ClientCount:
    return PerfilMensal739ClientCount(**dict.fromkeys(PerfilMensal739ClientCount.model_fields, 1))


def _patrimony(**overrides: object) -> dict[str, object]:
    return {**dict.fromkeys(PATRIM_FIELDS, "6.25"), **overrides}


def _row(**overrides: object) -> PerfilMensal739Row:
    fields: dict[str, object] = {
        "cnpj_fdo": VALID_CNPJ,
        "nr_client": _clients(),
        "distr_patrim": PerfilMensal739PatrimonyDistribution(**_patrimony()),
        "total_recurs_exter": "1.999",
        "total_recurs_br": "2",
        "tot_ativos_p_relac": "3.99",
        "tot_ativos_cred_priv": "4",
    }
    fields.update(overrides)
    return PerfilMensal739Row(**fields)


def _full_row() -> PerfilMensal739Row:
    return _row(
        resm_teor_vt_profrd="a",
        just_sum_vt_profrd="b",
        var_perc_pl="1.23456",
        mod_var_utiliz="1",
        praz_med_cart_tit="2.34567",
        res_delib="c",
        variacao_perc_val_cota=PerfilMensal739VarPercValCota(
            val_percent="1.239",
            lista_fator_primit_risco=[
                PerfilMensal739PrimitiveRiskFactor(
                    nome_fator_primit_risco="IBOVESPA", cen_util="s"
                )
            ],
        ),
        var_diar_perc_cota_fdo_pior_cen_estress="1.239",
        var_diar_perc_patrim_fdo_var_n_taxa_anual="1.239",
        var_diar_perc_patrim_fdo_var_n_taxa_cambio="1.239",
        var_patrim_fdo_n_preco_acoes="1.239",
        variacao_diar_perc_patrim_fdo_var_n_outros=PerfilMensal739VarOutros(
            fator_risco_outros="x", val_percent_outros="1.239"
        ),
        valor_noc_tot_contrat_deriv_mant_fdo=PerfilMensal739NominalRiskBlock(
            val_colateral="1.239",
            lista_fator_risco_noc=[
                PerfilMensal739NominalRiskFactor(
                    nome_fator_noc="DOLAR", val_fator_risco_noc_long=1, val_fator_risco_noc_short=2
                )
            ],
        ),
        lista_oper_curs_merc_balcao=[
            PerfilMensal739OtcOperation(
                tp_pessoa="PJ",
                nr_pf_pj_comitente=VALID_CNPJ,
                parte_relacionada="S",
                valor_parte="1.99",
            )
        ],
        lista_emissores_tit_cred_priv=[
            PerfilMensal739PrivateCreditIssuer(
                tp_pessoa_emissor="PJ",
                nr_pf_pj_emissor=VALID_CNPJ,
                parte_relacionada="N",
                valor_parte="2.99",
            )
        ],
        ved_regul_cobr_taxa_perform="S",
        resp_ved_regul_cobr_taxa_perform=PerfilMensal739PerformanceFeeDetails(
            data_cota_fundo="15/01/2025", val_cota_fundo="1.1234599"
        ),
    )


def _doc(row: PerfilMensal739Row | None = None) -> PerfilMensal739Document:
    header = PerfilMensal739Header(dt_compt="01/2025", dt_gerac_arq="15/01/2025")
    return PerfilMensal739Document(header=header, rows=[row or _row()])


def _xml(row: PerfilMensal739Row | None = None) -> str:
    xml = PerfilMensal739().export(_doc(row))
    assert xml is not None
    return xml


def test_full_document_tag_sequence_matches_page_sample() -> None:
    """Emit every tag of a fully populated row in the page sample's order."""
    assert re.findall(r"<([A-Z_0-9]+)[ >]", _xml(_full_row())) == PAGE_TAGS


@pytest.mark.parametrize(
    "tag",
    ["<VERSAO>1.0</VERSAO>", "<COD_DOC>40</COD_DOC>", '<DOC_ARQ xmlns="urn:perf">'],
)
def test_header_stamps_739_version_doc_code_and_namespace(tag: str) -> None:
    """Stamp VERSAO 1.0, COD_DOC 40 and the urn:perf namespace."""
    assert tag in _xml()


@pytest.mark.parametrize(
    "tag",
    [
        "<TOTAL_RECURS_EXTER>1,99</TOTAL_RECURS_EXTER>",
        "<VAR_PERC_PL>1,2345</VAR_PERC_PL>",
        "<PRAZ_MED_CART_TIT>2,3456</PRAZ_MED_CART_TIT>",
        "<VAL_PERCENT>1,23</VAL_PERCENT>",
        "<VAR_DIAR_PERC_COTA_FDO_PIOR_CEN_ESTRESS>1,23</VAR_DIAR_PERC_COTA_FDO_PIOR_CEN_ESTRESS>",
        "<VAR_DIAR_PERC_PATRIM_FDO_VAR_N_TAXA_ANUAL>1,23</VAR_DIAR_PERC_PATRIM_FDO_VAR_N_TAXA_ANUAL>",
        "<VAR_DIAR_PERC_PATRIM_FDO_VAR_N_TAXA_CAMBIO>1,23</VAR_DIAR_PERC_PATRIM_FDO_VAR_N_TAXA_CAMBIO>",
        "<VAR_PATRIM_FDO_N_PRECO_ACOES>1,23</VAR_PATRIM_FDO_N_PRECO_ACOES>",
        "<VAL_PERCENT_OUTROS>1,23</VAL_PERCENT_OUTROS>",
        "<VAL_COLATERAL>1,23</VAL_COLATERAL>",
        "<VALOR_PARTE>1,9</VALOR_PARTE>",
        "<TOT_ATIVOS_P_RELAC>3,9</TOT_ATIVOS_P_RELAC>",
        "<PR_PF_VARJ>6,2</PR_PF_VARJ>",
        "<VAL_COTA_FUNDO>1,12345</VAL_COTA_FUNDO>",
        "<TOTAL_RECURS_BR>2,00</TOTAL_RECURS_BR>",
        "<TOT_ATIVOS_CRED_PRIV>4,0</TOT_ATIVOS_CRED_PRIV>",
        "<VALOR_PARTE>2,9</VALOR_PARTE>",
    ],
)
def test_decimal_scales_follow_page_and_truncate(tag: str) -> None:
    """Truncate to the page's scale (1, 2, 4 or 5 places) and use a decimal comma."""
    assert tag in _xml(_full_row())


@pytest.mark.parametrize("field", ["montante_distrib", "inf_compl_perfil"])
def test_row_rejects_tags_the_739_page_does_not_have(field: str) -> None:
    """Reject a V3/V4-only tag instead of silently dropping it."""
    with pytest.raises(ValidationError):
        _row(**{field: "1"})


def test_distr_patrim_rejects_a_missing_percentage() -> None:
    """Reject a DISTR_PATRIM that omits a percentage (the page marks it mandatory)."""
    with pytest.raises(ValidationError):
        PerfilMensal739PatrimonyDistribution(
            **{k: v for k, v in _patrimony().items() if k != "pr_pf_varj"}
        )


def test_header_rejects_other_versao() -> None:
    """Reject a header claiming another VERSAO."""
    with pytest.raises(ValidationError):
        PerfilMensal739Header(dt_compt="01/2025", dt_gerac_arq="15/01/2025", versao="3.0")


def test_header_rejects_malformed_competence() -> None:
    """Reject a DT_COMPT that is not MM/AAAA."""
    with pytest.raises(ValidationError):
        PerfilMensal739Header(dt_compt="2025-01", dt_gerac_arq="15/01/2025")


def test_invalid_cnpj_check_digit_is_rejected() -> None:
    """Reject a fund CNPJ whose check digits are wrong."""
    with pytest.raises(ValidationError):
        _row(cnpj_fdo="11222333000182")


def test_more_than_three_otc_counterparties_rejected() -> None:
    """Reject a fourth OPER_CURS_MERC_BALCAO: the page repeats the block up to 3 times."""
    otc = PerfilMensal739OtcOperation(
        tp_pessoa="PJ", nr_pf_pj_comitente=VALID_CNPJ, parte_relacionada="S", valor_parte="1"
    )
    with pytest.raises(ValidationError):
        _row(lista_oper_curs_merc_balcao=[otc] * 4)


def test_export_to_file_returns_none(tmp_path: Path) -> None:
    """Return None when an output path is given."""
    assert PerfilMensal739().export(_doc(), output_path=str(tmp_path / "perfil.xml")) is None


def test_export_writes_windows_1252_file(tmp_path: Path) -> None:
    """Write the file as windows-1252: an accented value is one byte, not UTF-8's two."""
    out = tmp_path / "perfil.xml"
    PerfilMensal739().export(_doc(_row(res_delib="ação")), output_path=str(out))
    assert b"<RES_DELIB>a\xe7\xe3o</RES_DELIB>" in out.read_bytes()


def test_739_writer_rejects_a_v3_document() -> None:
    """Refuse a V3 document model: its scales and VERSAO differ from 739."""
    cls_v3 = PerfilMensalV3Document.model_construct(header=_doc().header, rows=_doc().rows)
    with pytest.raises(TypeError):
        PerfilMensal739().export(cls_v3, None)  # type: ignore[arg-type]


def test_negative_stress_value_truncates_toward_zero() -> None:
    """Truncate a negative stress value toward zero at two places, never down."""
    row = _row(
        variacao_diar_perc_patrim_fdo_var_n_outros=PerfilMensal739VarOutros(
            fator_risco_outros="x", val_percent_outros="-1.239"
        )
    )
    assert "<VAL_PERCENT_OUTROS>-1,23</VAL_PERCENT_OUTROS>" in _xml(row)


def test_export_plain_data_equals_model_export() -> None:
    """A dict from a valid document's ``model_dump`` exports the same XML as the model."""
    doc = _doc()

    assert PerfilMensal739().export(doc.model_dump()) == PerfilMensal739().export(doc)


def _own_classes(mod: ModuleType) -> list[type]:
    return [
        obj
        for obj in vars(mod).values()
        if isinstance(obj, type) and obj.__module__ == mod.__name__
    ]


@pytest.mark.parametrize("cls_model", _own_classes(m739))
def test_739_models_do_not_subclass_live_models(cls_model: type) -> None:
    """Keep 739 standalone so a validator or type added to a V3/V4 model cannot reach it."""
    set_live = set(_own_classes(v4)) | set(_own_classes(v3))

    assert not set_live & set(cls_model.__mro__)


def test_issuer_list_over_three_is_rejected() -> None:
    """Reject a fourth EMISSORES_TIT_CRED_PRIV: the page repeats the block up to 3 times."""
    item = PerfilMensal739PrivateCreditIssuer(
        tp_pessoa_emissor="PJ", nr_pf_pj_emissor=VALID_CNPJ, parte_relacionada="N", valor_parte="1"
    )
    with pytest.raises(ValidationError):
        _row(lista_emissores_tit_cred_priv=[item] * 4)


def test_primitive_risk_factor_list_over_five_is_rejected() -> None:
    """Reject a sixth FATOR_PRIMIT_RISCO: the page repeats the block up to 5 times."""
    item = PerfilMensal739PrimitiveRiskFactor(nome_fator_primit_risco="DOLAR", cen_util="s")
    with pytest.raises(ValidationError):
        PerfilMensal739VarPercValCota(val_percent="1", lista_fator_primit_risco=[item] * 6)


def test_nominal_risk_factor_list_over_five_is_rejected() -> None:
    """Reject a sixth FATOR_RISCO_NOC: the page repeats the block up to 5 times."""
    item = PerfilMensal739NominalRiskFactor(
        nome_fator_noc="DOLAR", val_fator_risco_noc_long=1, val_fator_risco_noc_short=2
    )
    with pytest.raises(ValidationError):
        PerfilMensal739NominalRiskBlock(val_colateral="1", lista_fator_risco_noc=[item] * 6)


def test_739_writer_rejects_a_v3_versao_given_as_plain_data() -> None:
    """Reject the ``model_dump`` of a real V3 document: its VERSAO 3.0 is not a 739 one."""
    doc_v3 = PerfilMensalV3Document(
        header={"dt_compt": "01/2025", "dt_gerac_arq": "15/01/2025"},
        rows=[
            _row().model_dump(exclude={"montante_distrib", "inf_compl_perfil"}),
        ],
    )
    with pytest.raises(ValidationError):
        PerfilMensal739().export(doc_v3.model_dump())


_V4_TO_739 = {
    "PerfilMensalRow": "PerfilMensal739Row",
    "DocumentHeader": "PerfilMensal739Header",
    "ClientCount": "PerfilMensal739ClientCount",
    "PatrimonyDistribution": "PerfilMensal739PatrimonyDistribution",
    "PrimitiveRiskFactor": "PerfilMensal739PrimitiveRiskFactor",
    "VarPercValCota": "PerfilMensal739VarPercValCota",
    "VarOutros": "PerfilMensal739VarOutros",
    "NominalRiskFactor": "PerfilMensal739NominalRiskFactor",
    "NominalRiskBlock": "PerfilMensal739NominalRiskBlock",
    "OtcOperation": "PerfilMensal739OtcOperation",
    "PrivateCreditIssuer": "PerfilMensal739PrivateCreditIssuer",
    "PerformanceFeeDetails": "PerfilMensal739PerformanceFeeDetails",
}


@pytest.mark.parametrize("name_v4", _V4_TO_739)
def test_739_model_fields_match_v4_so_the_writer_mapping_cannot_drift(name_v4: str) -> None:
    """Fail when a V4 model gains or loses a field its 739 counterpart does not mirror.

    The writer validates the 739 document into the V4 shape before building, so a new V4
    field would be emitted into 739 files unless the models are revisited. This pins field
    names only, not constraints.
    """
    cls_v4 = getattr(v4, name_v4)
    cls_739 = getattr(m739, _V4_TO_739[name_v4])

    assert set(cls_v4.model_fields) == set(cls_739.model_fields)
