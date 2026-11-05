# **Perfil Mensal — ICVM 739**

Envio (→ CVM) do padrão **Perfil Mensal ICVM 739**, vigente a partir de 01/07/2012
([`PadraoXMLPerfil739.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLPerfil739.asp)).

> **Veja também:** [Perfil Mensal (V4)](perfil_mensal.md) · [Perfil Mensal — V3](perfil_mensal_v3.md) · [Perfil Mensal — original](perfil_mensal_original.md) · [Referência da API](api/index.md)

---

## Descrição

Monte um `PerfilMensal739Document` (um `PerfilMensal739Header` + uma ou mais
`PerfilMensal739Row`, uma por fundo) e serialize com `PerfilMensal739().export(doc, output_path=None)`.
Namespace `urn:perf`, `COD_DOC=40`, `VERSAO=1.0`, `windows-1252`, gravação atômica.

## Diferenças medidas contra o V3

A página foi comparada à página e ao schema V3 (tag a tag, e linha a linha do texto). Diferenças:

- `VERSAO` é `1.0`.
- `MONTANTE_DISTRIB` e `INF_COMPL_PERFIL` **não existem** nesta página. O modelo os declara como
  `None`: informar um valor é rejeitado, nunca descartado em silêncio.
- `VAR_DIAR_PERC_PATRIM_FDO_VAR_N_TAXA_ANUAL`, `VAR_DIAR_PERC_PATRIM_FDO_VAR_N_TAXA_CAMBIO`,
  `VAR_PATRIM_FDO_N_PRECO_ACOES` e `VAL_PERCENT_OUTROS` têm **2 casas decimais** (4 no V3/V4).

A saída ainda passa pela validação do V4 antes da montagem: um teste fixa os nomes dos campos
de cada modelo contra o V4, mas não suas restrições. Os demais blocos são idênticos, mas os modelos são **independentes** (o 739 é um padrão
encerrado e não herda dos modelos vivos do V3/V4); o writer reutiliza a rotina de montagem do V4, trocando só a escala das tags de estresse.

| Tag | Regra |
|-----|-------|
| `NR_*` | inteiro ≥ 0, obrigatório (16) |
| `PR_*` | 1 casa decimal, 0 a 100, obrigatório (16) |
| `VAR_PERC_PL`, `PRAZ_MED_CART_TIT` | 4 casas decimais |
| `TOTAL_RECURS_EXTER`, `TOTAL_RECURS_BR`, `VAL_PERCENT`, `VAL_COLATERAL` | 2 casas decimais |
| `VAR_DIAR_PERC_COTA_FDO_PIOR_CEN_ESTRESS` e as 4 tags de estresse acima | 2 casas decimais |
| `VALOR_PARTE`, `TOT_ATIVOS_P_RELAC`, `TOT_ATIVOS_CRED_PRIV` | 1 casa decimal |
| `VAL_COTA_FUNDO` | 5 casas decimais |
| `FATOR_PRIMIT_RISCO`, `FATOR_RISCO_NOC` | até 5 ocorrências |
| `OPER_CURS_MERC_BALCAO`, `EMISSORES_TIT_CRED_PRIV` | até 3 ocorrências |

Decimais com precisão excedente são **truncados em direção a zero**, nunca arredondados. Passe
valores como `str`/`Decimal`, nunca `float`. Na saída, vírgula como separador decimal. O CNPJ é
validado por dígito verificador e gravado sem máscara.

## Não são verificados

O writer segue o exemplo XML da página; o que a página descreve só em prosa e não está
modelado fica sem validação:

- Que `VAR_PERC_PL`, `MOD_VAR_UTILIZ` e `PRAZ_MED_CART_TIT` sejam obrigatórios ("opcional para
  fundo de cotas"): o modelo não distingue o tipo do fundo e os trata como opcionais.
- Que `RESM_TEOR_VT_PROFRD`, `JUST_SUM_VT_PROFRD` e `RES_DELIB` sejam obrigatórios quando houve
  assembleia no período.
- A tabela de tags da página cita `CNPJ_FUNDO` e `PR_ENT_AB_FC_PREV_COMPL` (herança do layout
  original); o exemplo usa `CNPJ_FDO` e as duas tags de previdência separadas, e o writer segue o
  exemplo.
- Que os fundos do arquivo tenham a mesma competência e o mesmo administrador, e o tamanho máximo de 1 MB.
- Que a soma dos `PR_*` seja 100.

## Não emitidas

As tags `PERC_PL_MAIOR_COTST`, `PRINC_FAT_RISC`, `NR_DIAS_NEGOC` e `EMP_CLASSF_RISCO` constam
da descrição da página, mas estão comentadas (`-->`) e ausentes do exemplo; o writer não as emite.
