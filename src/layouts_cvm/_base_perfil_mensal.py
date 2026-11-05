"""Private shared XML builder for the Perfil Mensal submission writers.

Holds the V4 tag-order builder that ``PerfilMensal`` and ``PerfilMensal739`` both render
through, so neither public writer subclasses the other. Not part of the public API.
"""

from collections.abc import Callable
from decimal import Decimal
from typing import Any
from xml.sax import saxutils  # noqa: S406

from layouts_cvm._internal.config.ports.submission_writer import SubmissionWriter, TDoc
from layouts_cvm._internal.config.schemas.perfil_mensal import (
    ClientCount,
    NominalRiskBlock,
    OtcOperation,
    PatrimonyDistribution,
    PerfilMensalDocument,
    PerfilMensalRow,
    PerformanceFeeDetails,
    PrivateCreditIssuer,
    VarOutros,
    VarPercValCota,
)
from layouts_cvm._internal.utils.atomic_write import atomic_write_bytes


class _BasePerfilMensal(SubmissionWriter[TDoc]):
    """Shared Perfil Mensal XML builder; subclasses supply the typed ``export``.

    Methods
    -------
    export(doc, output_path)
            Abstract; each public writer declares its own document type.
    """

    _STRESS_PLACES = 4

    @staticmethod
    def _emit(xml_str: str, output_path: str | None) -> str | None:
        """Return the XML string, or write it as windows-1252 and return None.

        Parameters
        ----------
        xml_str : str
                Rendered XML.
        output_path : Optional[str]
                Destination file path, or None to return the string.

        Returns
        -------
        Optional[str]
                XML string when output_path is None, else None.
        """
        if output_path is None:
            return xml_str
        atomic_write_bytes(output_path, xml_str.encode("windows-1252"))
        return None

    def _build_xml_str(self, doc: PerfilMensalDocument, versao: str = "4.0") -> str:
        """Build the full CVM XML string from a PerfilMensalDocument.

        Parameters
        ----------
        doc : PerfilMensalDocument
                Validated document model.
        versao : str
                CVM document format version, by default "4.0".

        Returns
        -------
        str
                CVM-compliant XML string (UTF-8 in memory).
        """
        lines: list[str] = []
        lines.append('<?xml version="1.0" encoding="windows-1252"?>')
        lines.append('<DOC_ARQ xmlns="urn:perf">')
        lines.append("    <CAB_INFORM>")
        lines.append(f"        <COD_DOC>{doc.header.cod_doc}</COD_DOC>")
        lines.append(f"        <DT_COMPT>{doc.header.dt_compt}</DT_COMPT>")
        lines.append(f"        <DT_GERAC_ARQ>{doc.header.dt_gerac_arq}</DT_GERAC_ARQ>")
        lines.append(f"        <VERSAO>{versao}</VERSAO>")
        lines.append("    </CAB_INFORM>")
        lines.append("    <PERFIL_MENSAL>")
        for row in doc.rows:
            lines.extend(self._build_row_lines(row))
        lines.append("    </PERFIL_MENSAL>")
        lines.append("</DOC_ARQ>")
        return "\n".join(lines)

    def _build_row_lines(self, row: PerfilMensalRow, ind: str = "        ") -> list[str]:
        """Build the XML lines for one ROW_PERFIL block.

        Parameters
        ----------
        row : PerfilMensalRow
                Validated row model.
        ind : str
                Base indentation string, by default eight spaces.

        Returns
        -------
        list[str]
                Ordered XML lines for this row.
        """
        return (
            [f"{ind}<ROW_PERFIL>", f"{ind}    <CNPJ_FDO>{row.cnpj_fdo}</CNPJ_FDO>"]
            + self._build_nr_client_lines(row.nr_client, ind)
            + self._build_distr_patrim_lines(row.distr_patrim, ind)
            + self._build_risk_scalar_lines(row, ind)
            + self._build_usd_flow_lines(row, ind)
            + self._build_optional_block(
                row.variacao_perc_val_cota, self._build_variacao_vpc_lines, ind
            )
            + self._build_sensitivity_lines(row, ind)
            + self._build_optional_block(
                row.variacao_diar_perc_patrim_fdo_var_n_outros, self._build_var_outros_lines, ind
            )
            + self._build_optional_block(
                row.valor_noc_tot_contrat_deriv_mant_fdo, self._build_nominal_risk_lines, ind
            )
            + self._build_otc_lines(row.lista_oper_curs_merc_balcao, ind)
            + self._build_tag_lines(
                "TOT_ATIVOS_P_RELAC", row.tot_ativos_p_relac, self._dec(1), ind
            )
            + self._build_issuers_lines(row.lista_emissores_tit_cred_priv, ind)
            + self._build_tag_lines(
                "TOT_ATIVOS_CRED_PRIV", row.tot_ativos_cred_priv, self._dec(1), ind
            )
            + self._build_performance_fee_lines(row, ind)
            + self._build_tag_lines("MONTANTE_DISTRIB", row.montante_distrib, self._dec(2), ind)
            + self._build_tag_lines("INF_COMPL_PERFIL", row.inf_compl_perfil, self._esc(500), ind)
            + [f"{ind}</ROW_PERFIL>"]
        )

    @staticmethod
    def _build_optional_block(
        block: object | None, fn_builder: Callable[[Any, str], list[str]], ind: str
    ) -> list[str]:
        """Build a nested block's lines, or nothing when the block is absent.

        Parameters
        ----------
        block : Optional[object]
                Block model, or None if absent.
        fn_builder : Callable[[Any, str], list[str]]
                Builder invoked with the block and the indentation.
        ind : str
                Base indentation string.

        Returns
        -------
        list[str]
                XML lines, empty if block is None.
        """
        return [] if block is None else fn_builder(block, ind)

    @staticmethod
    def _build_tag_lines(
        tag: str, value: object | None, fn_fmt: Callable[[Any], str], ind: str
    ) -> list[str]:
        """Build one ``<TAG>value</TAG>`` line, or nothing when value is None.

        Parameters
        ----------
        tag : str
                XML tag name.
        value : Optional[object]
                Raw value, or None if absent.
        fn_fmt : Callable[[Any], str]
                Formatter turning the value into element text.
        ind : str
                Base indentation string.

        Returns
        -------
        list[str]
                A single XML line, empty if value is None.
        """
        return [] if value is None else [f"{ind}    <{tag}>{fn_fmt(value)}</{tag}>"]

    @staticmethod
    def _dec(places: int) -> Callable[[Decimal], str]:
        """Return a formatter rendering a Decimal with the given places.

        Parameters
        ----------
        places : int
                Number of decimal places.

        Returns
        -------
        Callable[[Decimal], str]
                Formatter using the CVM comma separator.
        """
        return lambda value: _BasePerfilMensal._fmt_decimal(value, places)

    @staticmethod
    def _esc(max_len: int) -> Callable[[str], str]:
        """Return a formatter truncating to max_len then XML-escaping.

        Parameters
        ----------
        max_len : int
                Maximum number of characters kept.

        Returns
        -------
        Callable[[str], str]
                Truncating, escaping formatter.
        """
        return lambda value: saxutils.escape(value[:max_len])

    def _build_nr_client_lines(self, c: ClientCount, ind: str) -> list[str]:
        """Build XML lines for the NR_CLIENT block.

        Parameters
        ----------
        c : ClientCount
                Client count model.
        ind : str
                Base indentation string.

        Returns
        -------
        list[str]
                XML lines for the NR_CLIENT block.
        """
        inner = f"{ind}        "
        pairs = [
            ("NR_PF_PRIV_BANK", c.nr_pf_priv_bank),
            ("NR_PF_VARJ", c.nr_pf_varj),
            ("NR_PJ_N_FINANC_PRIV_BANK", c.nr_pj_n_financ_priv_bank),
            ("NR_PJ_N_FINANC_VARJ", c.nr_pj_n_financ_varj),
            ("NR_BNC_COMERC", c.nr_bnc_comerc),
            ("NR_PJ_CORR_DIST", c.nr_pj_corr_dist),
            ("NR_PJ_OUTR_FINANC", c.nr_pj_outr_financ),
            ("NR_INV_N_RES", c.nr_inv_n_res),
            ("NR_ENT_AB_PREV_COMPL", c.nr_ent_ab_prev_compl),
            ("NR_ENT_FC_PREV_COMPL", c.nr_ent_fc_prev_compl),
            ("NR_REG_PREV_SERV_PUB", c.nr_reg_prev_serv_pub),
            ("NR_SOC_SEG_RESEG", c.nr_soc_seg_reseg),
            ("NR_SOC_CAPTLZ_ARRENDM_MERC", c.nr_soc_captlz_arrendm_merc),
            ("NR_FDOS_CLUB_INV", c.nr_fdos_club_inv),
            ("NR_COTST_DISTR_FDO", c.nr_cotst_distr_fdo),
            ("NR_OUTROS_N_RELAC", c.nr_outros_n_relac),
        ]
        return (
            [f"{ind}    <NR_CLIENT>"]
            + [f"{inner}<{tag}>{val}</{tag}>" for tag, val in pairs]
            + [f"{ind}    </NR_CLIENT>"]
        )

    def _build_distr_patrim_lines(self, dp: PatrimonyDistribution | None, ind: str) -> list[str]:
        """Build XML lines for the optional DISTR_PATRIM block.

        Parameters
        ----------
        dp : Optional[PatrimonyDistribution]
                Patrimony distribution model, or None if absent.
        ind : str
                Base indentation string.

        Returns
        -------
        list[str]
                XML lines, empty if dp is None.
        """
        if dp is None:
            return []
        inner = f"{ind}        "
        pairs = [
            ("PR_PF_PRIV_BANK", dp.pr_pf_priv_bank),
            ("PR_PF_VARJ", dp.pr_pf_varj),
            ("PR_PJ_N_FINANC_PRIV_BANK", dp.pr_pj_n_financ_priv_bank),
            ("PR_PJ_N_FINANC_VARJ", dp.pr_pj_n_financ_varj),
            ("PR_BNC_COMERC", dp.pr_bnc_comerc),
            ("PR_PJ_CORR_DIST", dp.pr_pj_corr_dist),
            ("PR_PJ_OUTR_FINANC", dp.pr_pj_outr_financ),
            ("PR_INV_N_RES", dp.pr_inv_n_res),
            ("PR_ENT_AB_PREV_COMPL", dp.pr_ent_ab_prev_compl),
            ("PR_ENT_FC_PREV_COMPL", dp.pr_ent_fc_prev_compl),
            ("PR_REG_PREV_SERV_PUB", dp.pr_reg_prev_serv_pub),
            ("PR_SOC_SEG_RESEG", dp.pr_soc_seg_reseg),
            ("PR_SOC_CAPTLZ_ARRENDM_MERC", dp.pr_soc_captlz_arrendm_merc),
            ("PR_FDOS_CLUB_INV", dp.pr_fdos_club_inv),
            ("PR_COTST_DISTR_FDO", dp.pr_cotst_distr_fdo),
            ("PR_OUTROS_N_RELAC", dp.pr_outros_n_relac),
        ]
        children = [
            f"{inner}<{tag}>{self._fmt_decimal(val, 1)}</{tag}>"
            for tag, val in pairs
            if val is not None
        ]
        return [f"{ind}    <DISTR_PATRIM>"] + children + [f"{ind}    </DISTR_PATRIM>"]

    def _build_risk_scalar_lines(self, row: PerfilMensalRow, ind: str) -> list[str]:
        """Build XML lines for optional VAR, vote and assembly text fields.

        Parameters
        ----------
        row : PerfilMensalRow
                Validated row model.
        ind : str
                Base indentation string.

        Returns
        -------
        list[str]
                XML lines for text and scalar risk fields.
        """
        esc4000 = self._esc(4000)
        return (
            self._build_tag_lines("RESM_TEOR_VT_PROFRD", row.resm_teor_vt_profrd, esc4000, ind)
            + self._build_tag_lines("JUST_SUM_VT_PROFRD", row.just_sum_vt_profrd, esc4000, ind)
            + self._build_tag_lines("VAR_PERC_PL", row.var_perc_pl, self._dec(4), ind)
            + self._build_tag_lines("MOD_VAR_UTILIZ", row.mod_var_utiliz, str, ind)
            + self._build_tag_lines("PRAZ_MED_CART_TIT", row.praz_med_cart_tit, self._dec(4), ind)
            + self._build_tag_lines("RES_DELIB", row.res_delib, esc4000, ind)
        )

    def _build_usd_flow_lines(self, row: PerfilMensalRow, ind: str) -> list[str]:
        """Build XML lines for the mandatory USD resource flow fields.

        Parameters
        ----------
        row : PerfilMensalRow
                Validated row model.
        ind : str
                Base indentation string.

        Returns
        -------
        list[str]
                XML lines for TOTAL_RECURS_EXTER and TOTAL_RECURS_BR.
        """
        return [
            f"{ind}    <TOTAL_RECURS_EXTER>"
            f"{self._fmt_decimal(row.total_recurs_exter, 2)}"
            f"</TOTAL_RECURS_EXTER>",
            f"{ind}    <TOTAL_RECURS_BR>"
            f"{self._fmt_decimal(row.total_recurs_br, 2)}"
            f"</TOTAL_RECURS_BR>",
        ]

    def _build_variacao_vpc_lines(self, vpc: VarPercValCota, ind: str) -> list[str]:
        """Build XML lines for the VARIACAO_PERC_VAL_COTA block.

        Parameters
        ----------
        vpc : VarPercValCota
                Stress scenario block model.
        ind : str
                Base indentation string.

        Returns
        -------
        list[str]
                XML lines for the stress scenario and primitive risk factor list.
        """
        lines: list[str] = [
            f"{ind}    <VARIACAO_PERC_VAL_COTA>",
            f"{ind}        <VAL_PERCENT>{self._fmt_decimal(vpc.val_percent, 2)}</VAL_PERCENT>",
            f"{ind}        <LISTA_FATOR_PRIMIT_RISCO>",
        ]
        for fpr in vpc.lista_fator_primit_risco:
            lines += [
                f"{ind}            <FATOR_PRIMIT_RISCO>",
                f"{ind}                <NOME_FATOR_PRIMIT_RISCO>"
                f"{saxutils.escape(fpr.nome_fator_primit_risco)}"
                f"</NOME_FATOR_PRIMIT_RISCO>",
                f"{ind}                <CEN_UTIL>{saxutils.escape(fpr.cen_util)}</CEN_UTIL>",
                f"{ind}            </FATOR_PRIMIT_RISCO>",
            ]
        lines += [
            f"{ind}        </LISTA_FATOR_PRIMIT_RISCO>",
            f"{ind}    </VARIACAO_PERC_VAL_COTA>",
        ]
        return lines

    def _build_sensitivity_lines(self, row: PerfilMensalRow, ind: str) -> list[str]:
        """Build XML lines for the optional sensitivity scalar fields.

        Parameters
        ----------
        row : PerfilMensalRow
                Validated row model.
        ind : str
                Base indentation string.

        Returns
        -------
        list[str]
                XML lines for stress-scenario and DV01-style sensitivity fields.
        """
        pairs: list[tuple[str, Decimal | None, int]] = [
            (
                "VAR_DIAR_PERC_COTA_FDO_PIOR_CEN_ESTRESS",
                row.var_diar_perc_cota_fdo_pior_cen_estress,
                2,
            ),
            (
                "VAR_DIAR_PERC_PATRIM_FDO_VAR_N_TAXA_ANUAL",
                row.var_diar_perc_patrim_fdo_var_n_taxa_anual,
                self._STRESS_PLACES,
            ),
            (
                "VAR_DIAR_PERC_PATRIM_FDO_VAR_N_TAXA_CAMBIO",
                row.var_diar_perc_patrim_fdo_var_n_taxa_cambio,
                self._STRESS_PLACES,
            ),
            (
                "VAR_PATRIM_FDO_N_PRECO_ACOES",
                row.var_patrim_fdo_n_preco_acoes,
                self._STRESS_PLACES,
            ),
        ]
        return [
            f"{ind}    <{tag}>{self._fmt_decimal(val, places)}</{tag}>"
            for tag, val, places in pairs
            if val is not None
        ]

    def _build_var_outros_lines(self, vo: VarOutros, ind: str) -> list[str]:
        """Build XML lines for the VARIACAO_DIAR_PERC_PATRIM_FDO_VAR_N_OUTROS block.

        Parameters
        ----------
        vo : VarOutros
                Other risk factor sensitivity model.
        ind : str
                Base indentation string.

        Returns
        -------
        list[str]
                XML lines for the other risk factor block.
        """
        return [
            f"{ind}    <VARIACAO_DIAR_PERC_PATRIM_FDO_VAR_N_OUTROS>",
            f"{ind}        <FATOR_RISCO_OUTROS>"
            f"{saxutils.escape(vo.fator_risco_outros[:400])}"
            f"</FATOR_RISCO_OUTROS>",
            f"{ind}        <VAL_PERCENT_OUTROS>"
            f"{self._fmt_decimal(vo.val_percent_outros, self._STRESS_PLACES)}"
            f"</VAL_PERCENT_OUTROS>",
            f"{ind}    </VARIACAO_DIAR_PERC_PATRIM_FDO_VAR_N_OUTROS>",
        ]

    def _build_nominal_risk_lines(self, nb: NominalRiskBlock, ind: str) -> list[str]:
        """Build XML lines for the VALOR_NOC_TOT_CONTRAT_DERIV_MANT_FDO block.

        Parameters
        ----------
        nb : NominalRiskBlock
                OTC derivatives notional block model.
        ind : str
                Base indentation string.

        Returns
        -------
        list[str]
                XML lines for notional risk factors.
        """
        lines: list[str] = [
            f"{ind}    <VALOR_NOC_TOT_CONTRAT_DERIV_MANT_FDO>",
            f"{ind}        <VAL_COLATERAL>"
            f"{self._fmt_decimal(nb.val_colateral, 2)}"
            f"</VAL_COLATERAL>",
            f"{ind}        <LISTA_FATOR_RISCO_NOC>",
        ]
        for fnoc in nb.lista_fator_risco_noc:
            lines += [
                f"{ind}            <FATOR_RISCO_NOC>",
                f"{ind}                <NOME_FATOR_NOC>"
                f"{saxutils.escape(fnoc.nome_fator_noc)}"
                f"</NOME_FATOR_NOC>",
                f"{ind}                <VAL_FATOR_RISCO_NOC_LONG>"
                f"{fnoc.val_fator_risco_noc_long}"
                f"</VAL_FATOR_RISCO_NOC_LONG>",
                f"{ind}                <VAL_FATOR_RISCO_NOC_SHORT>"
                f"{fnoc.val_fator_risco_noc_short}"
                f"</VAL_FATOR_RISCO_NOC_SHORT>",
                f"{ind}            </FATOR_RISCO_NOC>",
            ]
        lines += [
            f"{ind}        </LISTA_FATOR_RISCO_NOC>",
            f"{ind}    </VALOR_NOC_TOT_CONTRAT_DERIV_MANT_FDO>",
        ]
        return lines

    def _build_otc_lines(self, lista_otc: list | None, ind: str) -> list[str]:
        """Build XML lines for the optional LISTA_OPER_CURS_MERC_BALCAO block.

        Parameters
        ----------
        lista_otc : Optional[list]
                List of OTC counterparties (up to 3), or None if absent.
        ind : str
                Base indentation string.

        Returns
        -------
        list[str]
                XML lines, empty if lista_otc is falsy.
        """
        children = [ln for otc in lista_otc or [] for ln in self._build_otc_item_lines(otc, ind)]
        return self._wrap_list_block("LISTA_OPER_CURS_MERC_BALCAO", children, ind)

    def _build_otc_item_lines(self, otc: OtcOperation, ind: str) -> list[str]:
        """Build XML lines for one OPER_CURS_MERC_BALCAO element.

        Parameters
        ----------
        otc : OtcOperation
                OTC counterparty model.
        ind : str
                Base indentation string.

        Returns
        -------
        list[str]
                XML lines for the counterparty.
        """
        return [
            f"{ind}        <OPER_CURS_MERC_BALCAO>",
            f"{ind}            <TP_PESSOA>{otc.tp_pessoa}</TP_PESSOA>",
            f"{ind}            <NR_PF_PJ_COMITENTE>{otc.nr_pf_pj_comitente}</NR_PF_PJ_COMITENTE>",
            f"{ind}            <PARTE_RELACIONADA>{otc.parte_relacionada}</PARTE_RELACIONADA>",
            f"{ind}            <VALOR_PARTE>{self._fmt_decimal(otc.valor_parte, 1)}</VALOR_PARTE>",
            f"{ind}        </OPER_CURS_MERC_BALCAO>",
        ]

    @staticmethod
    def _wrap_list_block(tag: str, children: list[str], ind: str) -> list[str]:
        """Wrap child lines in a list element, or return nothing when empty.

        Parameters
        ----------
        tag : str
                XML tag name of the list element.
        children : list[str]
                Already-built child lines.
        ind : str
                Base indentation string.

        Returns
        -------
        list[str]
                Opening tag, children and closing tag; empty if no children.
        """
        return [f"{ind}    <{tag}>", *children, f"{ind}    </{tag}>"] if children else []

    def _build_issuers_lines(self, lista_issuers: list | None, ind: str) -> list[str]:
        """Build XML lines for the optional LISTA_EMISSORES_TIT_CRED_PRIV block.

        Parameters
        ----------
        lista_issuers : Optional[list]
                List of private credit issuers (up to 3), or None if absent.
        ind : str
                Base indentation string.

        Returns
        -------
        list[str]
                XML lines, empty if lista_issuers is falsy.
        """
        children = [
            ln for iss in lista_issuers or [] for ln in self._build_issuer_item_lines(iss, ind)
        ]
        return self._wrap_list_block("LISTA_EMISSORES_TIT_CRED_PRIV", children, ind)

    def _build_issuer_item_lines(self, iss: PrivateCreditIssuer, ind: str) -> list[str]:
        """Build XML lines for one EMISSORES_TIT_CRED_PRIV element.

        Parameters
        ----------
        iss : PrivateCreditIssuer
                Private credit issuer model.
        ind : str
                Base indentation string.

        Returns
        -------
        list[str]
                XML lines for the issuer.
        """
        return [
            f"{ind}        <EMISSORES_TIT_CRED_PRIV>",
            f"{ind}            <TP_PESSOA_EMISSOR>{iss.tp_pessoa_emissor}</TP_PESSOA_EMISSOR>",
            f"{ind}            <NR_PF_PJ_EMISSOR>{iss.nr_pf_pj_emissor}</NR_PF_PJ_EMISSOR>",
            f"{ind}            <PARTE_RELACIONADA>{iss.parte_relacionada}</PARTE_RELACIONADA>",
            f"{ind}            <VALOR_PARTE>{self._fmt_decimal(iss.valor_parte, 1)}</VALOR_PARTE>",
            f"{ind}        </EMISSORES_TIT_CRED_PRIV>",
        ]

    def _build_performance_fee_lines(self, row: PerfilMensalRow, ind: str) -> list[str]:
        """Build XML lines for the optional performance-fee blocks.

        Parameters
        ----------
        row : PerfilMensalRow
                Validated row model.
        ind : str
                Base indentation string.

        Returns
        -------
        list[str]
                XML lines for VED_REGUL and RESP_VED_REGUL blocks.
        """
        return self._build_tag_lines(
            "VED_REGUL_COBR_TAXA_PERFORM", row.ved_regul_cobr_taxa_perform, str, ind
        ) + self._build_optional_block(
            row.resp_ved_regul_cobr_taxa_perform, self._build_resp_ved_regul_lines, ind
        )

    def _build_resp_ved_regul_lines(self, pfd: PerformanceFeeDetails, ind: str) -> list[str]:
        """Build XML lines for the RESP_VED_REGUL_COBR_TAXA_PERFORM block.

        Parameters
        ----------
        pfd : PerformanceFeeDetails
                Performance-fee responsible model.
        ind : str
                Base indentation string.

        Returns
        -------
        list[str]
                XML lines for the block.
        """
        return [
            f"{ind}    <RESP_VED_REGUL_COBR_TAXA_PERFORM>",
            f"{ind}        <DATA_COTA_FUNDO>{pfd.data_cota_fundo}</DATA_COTA_FUNDO>",
            f"{ind}        <VAL_COTA_FUNDO>"
            f"{self._fmt_decimal(pfd.val_cota_fundo, 5)}"
            f"</VAL_COTA_FUNDO>",
            f"{ind}    </RESP_VED_REGUL_COBR_TAXA_PERFORM>",
        ]

    @staticmethod
    def _fmt_decimal(value: Decimal, places: int) -> str:
        """Format a Decimal for CVM XML output (comma as decimal separator).

        Parameters
        ----------
        value : Decimal
                Numeric value.
        places : int
                Number of decimal places.

        Returns
        -------
        str
                Formatted string (e.g. '12,3400').
        """
        return f"{value:.{places}f}".replace(".", ",")
