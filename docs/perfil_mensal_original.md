# **Perfil Mensal — original**

Envio (→ CVM) do padrão **Perfil Mensal original**
([`PadraoXMLPerfil.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLPerfil.asp)).

> **Veja também:** [Perfil Mensal V4](perfil_mensal.md) · [Referência da API](api/index.md)

---

## Descrição

Monte um `PerfilMensalOriginalDocument` (um `PerfilMensalOriginalHeader` + uma ou mais
`PerfilMensalOriginalRow`, uma por fundo) e serialize com `PerfilMensalOriginal().export(...)`.

O layout original **não é uma derivação do V4** — medido contra as duas páginas da CVM, o exemplo
XML do original tem 53 tags (o do V4, 92) e só 36 nomes de tag em comum. Por isso o writer tem
schema próprio; do V4 reaproveita apenas o tipo `PercentField`.

| Diferença medida | Original | V4 |
|------------------|----------|----|
| Cabeçalho | `COD_DOC`, `DT_COMPT`, `DT_GERAC_ARQ` — **sem `VERSAO`** | acrescenta `VERSAO` |
| `NR_CLIENT` / `DISTR_PATRIM` | 14 tags cada; sufixo `_NAC` em `*_BNC_COMERC_NAC`, `*_PJ_CORR_DIST_NAC`, `*_PJ_OUTR_FINANC_NAC`; previdência numa tag só (`*_ENT_AB_FC_PREV_COMPL`) | 16 tags; previdência aberta/fechada separadas e `*_REG_PREV_SERV_PUB` |
| Corpo da linha | `PERC_PL_MAIOR_COTST` (obrigatório), `PRINC_FAT_RISC`, `DESC_PRINC_ATV_OPER_RISC`, `PR_PRINC_ATV_OPER_RISC`, `NR_DIAS_NEGOC` (`ATIV_50_PERC`, `ATIV_100_PERC`, `APRES_LIQDZ`), `PERC_PL_CONV_CAIXA` | ausentes |
| Corpo do V4 | ausente | recursos no exterior/Brasil, cenários de estresse, derivativos, balcão, crédito privado, taxa de performance, `MONTANTE_DISTRIB`, `INF_COMPL_PERFIL` |

Escalas e cardinalidades, como a página as declara:

| Tag | Regra |
|-----|-------|
| `NR_*` | inteiro ≥ 0, obrigatório (14) |
| `PR_*`, `PERC_PL_MAIOR_COTST`, `PERC_PL_CONV_CAIXA` | 1 casa decimal, 0 a 100 |
| `PR_PRINC_ATV_OPER_RISC` | até 7 inteiras e 1 decimal |
| `VAR_PERC_PL` | até 10 inteiras e 4 decimais |
| `ATIV_50_PERC`, `ATIV_100_PERC`, `PRAZ_MED_CART_TIT` | até 4 inteiras e 4 decimais; `ATIV_50_PERC` e `ATIV_100_PERC` vêm juntas |
| `MOD_VAR_UTILIZ` | `"1"`, `"2"` ou `"3"` |
| `APRES_LIQDZ` | `"S"` ou `"N"` |
| `PRINC_FAT_RISC`, `DESC_PRINC_ATV_OPER_RISC` | texto, até 400 caracteres |
| `RESM_TEOR_VT_PROFRD`, `JUST_SUM_VT_PROFRD`, `RES_DELIB` | texto, até 4.000 caracteres |

- Decimais com precisão excedente são **truncados em direção a zero** (`ROUND_DOWN`), nunca
  arredondados. Passe valores como `str`/`Decimal`, nunca `float`. Na saída, vírgula como
  separador decimal; o arquivo é gravado em `windows-1252`, de forma atômica.
- As tags `PRINC_FAT_RISC`, `DESC_PRINC_ATV_OPER_RISC`, `PR_PRINC_ATV_OPER_RISC`, `VAR_PERC_PL`,
  `MOD_VAR_UTILIZ` e `PRAZ_MED_CART_TIT` são "obrigatórias, opcionais para Fundos de Investimento
  em Cotas" na página; o modelo não distingue o tipo do fundo e as trata como opcionais.
- O CNPJ é validado por dígito verificador e gravado sem máscara; o mesmo fundo não pode aparecer
  duas vezes no arquivo.

> A página descreve a tag do CNPJ como `CNPJ_FUNDO` na tabela de tags, mas o exemplo XML (e o V4)
> usam `CNPJ_FDO`; o writer segue o exemplo.

---

## Exemplos

```python
from layouts_cvm import PerfilMensalOriginal

clientes = dict(
    nr_pf_priv_bank=0,
    nr_pf_varj=0,
    nr_pj_n_financ_priv_bank=0,
    nr_pj_n_financ_varj=0,
    nr_bnc_comerc_nac=0,
    nr_pj_corr_dist_nac=0,
    nr_pj_outr_financ_nac=0,
    nr_inv_n_res=0,
    nr_ent_ab_fc_prev_compl=0,
    nr_soc_seg_reseg=0,
    nr_soc_captlz_arrendm_merc=0,
    nr_fdos_club_inv=0,
    nr_cotst_distr_fdo=0,
    nr_outros_n_relac=0,
)
distribuicao = dict(
    pr_pf_priv_bank="0",
    pr_pf_varj="0",
    pr_pj_n_financ_priv_bank="0",
    pr_pj_n_financ_varj="0",
    pr_bnc_comerc_nac="0",
    pr_pj_corr_dist_nac="0",
    pr_pj_outr_financ_nac="0",
    pr_inv_n_res="0",
    pr_ent_ab_fc_prev_compl="0",
    pr_soc_seg_reseg="0",
    pr_soc_captlz_arrendm_merc="0",
    pr_fdos_club_inv="0",
    pr_cotst_distr_fdo="0",
    pr_outros_n_relac="0",
)
doc = dict(
    header=dict(dt_compt="01/2008", dt_gerac_arq="15/02/2008"),
    rows=[
        dict(
            cnpj_fdo="11222333000181",
            nr_client=clientes,
            distr_patrim=distribuicao,
            perc_pl_maior_cotst="12.3",
        )
    ],
)

xml = PerfilMensalOriginal().export(doc)                       # str
PerfilMensalOriginal().export(doc, output_path="perfil.xml")   # grava em windows-1252
```
