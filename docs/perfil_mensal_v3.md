# **Perfil Mensal — V3**

Envio (→ CVM) do padrão **Perfil Mensal V3**, vigente a partir de 01/10/2015
([`PadraoXMLPerfilV3.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLPerfilV3.asp)).

> **Veja também:** [Perfil Mensal (V4)](perfil_mensal.md) · [Perfil Mensal — original](perfil_mensal_original.md) · [Referência da API](api/index.md)

---

## Descrição

Monte um `PerfilMensalV3Document` (um `PerfilMensalV3Header` + uma ou mais `PerfilMensalV3Row`,
uma por fundo) e serialize com `PerfilMensalV3().export(doc, output_path=None)`. Namespace
`urn:perf`, `COD_DOC=40`, `VERSAO=3.0`, `windows-1252`, gravação atômica.

## Diferenças medidas contra o V4

A página foi comparada à página e ao schema V4. A sequência de tags do exemplo XML é idêntica
(92 tags, mesma ordem, mesmas escalas e cardinalidades). Só há duas diferenças:

- `VERSAO` é `3.0`.
- `DISTR_PATRIM` é **obrigatório**, com as 16 tags `PR_*`. No V4 o bloco é opcional e suas tags só
  são exigidas quando ele existe.

Os demais blocos são idênticos, por isso os modelos estendem os do V4 e o writer usa o writer V4 por
composição, não por herança nem por cópia.

| Tag | Regra |
|-----|-------|
| `NR_*` | inteiro ≥ 0, obrigatório (16) |
| `PR_*` | 1 casa decimal, 0 a 100, obrigatório (16) |
| `VAR_PERC_PL` | até 10 inteiras e 4 decimais |
| `PRAZ_MED_CART_TIT` | até 4 inteiras e 4 decimais |
| `TOTAL_RECURS_EXTER`, `TOTAL_RECURS_BR`, `VAL_PERCENT`, `VAL_COLATERAL`, `MONTANTE_DISTRIB` | 2 casas decimais |
| `VAR_DIAR_PERC_PATRIM_FDO_VAR_N_*`, `VAR_PATRIM_FDO_N_PRECO_ACOES`, `VAL_PERCENT_OUTROS` | 4 casas decimais |
| `VALOR_PARTE`, `TOT_ATIVOS_P_RELAC`, `TOT_ATIVOS_CRED_PRIV` | 1 casa decimal |
| `VAL_COTA_FUNDO` | 5 casas decimais |
| `FATOR_PRIMIT_RISCO`, `FATOR_RISCO_NOC` | até 5 ocorrências |
| `OPER_CURS_MERC_BALCAO`, `EMISSORES_TIT_CRED_PRIV` | até 3 ocorrências |

## Decisões

- Decimais com precisão excedente são **truncados em direção a zero**, nunca arredondados. Passe
  valores como `str`/`Decimal`, nunca `float`. Na saída, vírgula como separador decimal.
- `VAR_PERC_PL`, `MOD_VAR_UTILIZ`, `PRAZ_MED_CART_TIT` e as variações de estresse são "obrigatórias,
  opcionais para fundos de cotas" na página; o modelo não distingue o tipo do fundo e as trata como
  opcionais, como o V4.
- A tabela de tags da página cita `CNPJ_FUNDO` e uma tag `PR_ENT_AB_FC_PREV_COMPL` (herança do layout
  original), mas o exemplo XML usa `CNPJ_FDO` e as duas tags de previdência separadas, como o V4; o
  writer segue o exemplo. As tags de `PERC_PL_MAIOR_COTST`, `PRINC_FAT_RISC`, `NR_DIAS_NEGOC` e
  `EMP_CLASSF_RISCO` aparecem na descrição, mas cercadas por `-->` e ausentes do exemplo: não são
  emitidas.
- O CNPJ é validado por dígito verificador e gravado sem máscara.
