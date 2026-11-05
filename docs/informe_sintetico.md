# **Informe Sintético**

Envio (→ CVM) do padrão **Informe Sintético**, mensal, com dados agregados da carteira. São
**quatro variantes por tipo de fundo** (não são versões), cada uma com página, `COD_DOC` e blocos
próprios:

| Variante | `COD_DOC` | Fundos | Página |
|----------|-----------|--------|--------|
| FCCE | 5 | FCCE e FCCE-AI | [`PadraoXMLSintFCCE.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLSintFCCE.asp) |
| FITVM | 7 | FITVM, FMP-FGTS CL e FIIM | [`PadraoXMLSintFITVM.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLSintFITVM.asp) |
| FIC-FITVM | 8 | FIC-FITVM | [`PadraoXMLSintFIC.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLSintFIC.asp) |
| Outros | 9 | FICE, FMP-FGTS e FMAI | [`PadraoXMLSintOutros.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLSintOutros.asp) |

> **Veja também:** [Referência da API](api/index.md) · [Uso](usage.md)

---

## Descrição

Um único writer, `InformeSintetico().export(...)`, atende as quatro variantes. Passe um dos
documentos (`InformeSinteticoFcceDocument`, `InformeSinteticoFitvmDocument`,
`InformeSinteticoFicDocument` ou `InformeSinteticoOutrosDocument`) ou dados simples: nesse caso o
`header.cod_doc` (5, 7, 8 ou 9) escolhe a variante, e outro valor é recusado com `ValueError`.

O XML é `DOC_ARQ` > `DESC_ADM` + `INFORME_SINTETICO` > `ROW_INFORME` (um por fundo) >
`CNPJ_FUNDO` + `APLICACOES_POS_FINAL` > `APLICACOES` + `OUTRAS`, em `windows-1252` e **sem
namespace** (as páginas não declaram nenhum). Um arquivo vale para uma única competência e um
único administrador de carteira, com vários fundos.

Cada campo do schema é a tag da página em minúsculas, declarado na ordem do XML. Os blocos de
`APLICACOES` e `OUTRAS` diferem entre as variantes e seguem a ordem de cada página (por exemplo,
`MERC_OPCAO` vem antes de `MERC_A_TERMO` na variante Outros e depois na FITVM).

## Tipagem

- Valores de aplicações e `PATRIM_LIQ`, `QUOTA_EMITIDA_MES`, `QUOTA_RESG_MES`: **inteiros em
  R$ 1000** (a página: "todos os campos devem ser preenchidos com valores inteiros"). `float`,
  `bool` e texto são recusados.
- `NR_TOT_QUOTST_ULT_DIA_MES`: inteiro ≥ 0.
- `VL_QUOTA_ULT_DIA_MES`: `Decimal` marcado "(decimal)" na página, **12 casas** na saída
  (escala decidida aqui, ver abaixo); `float` recusado, casas excedentes **truncadas**, vírgula
  decimal. Deve ser > 0 (como o `VL_QUOTA` do Informe Diário); zero e negativos são recusados, inclusive um valor positivo que o truncamento em 12 casas reduz a zero.
- Inteiros são `int` estrito: `numpy.int64` é recusado, converta com `int()` antes.
- `CNPJ_ADM` e `CNPJ_FUNDO`: CNPJ com dígitos verificadores, gravado sem máscara.
- `DT_COMPT`: `MM/AAAA` real; `DT_GERAC_ARQ`: data real `DD/MM/AAAA`.

## O que foi medido nas páginas

- Estrutura e ordem das tags das quatro páginas, `COD_DOC` 5, 7, 8 e 9, `encoding="windows-1252"`.
- FCCE traz `VL_CONTR_FUTURO_MANTIDO_ABER` em `OUTRAS`; Outros traz
  `VL_CONTR_FUTURO_MANTIDO_ABERTO` (grafia diferente, respeitada); FITVM e FIC-FITVM não têm esse
  campo.
- Vírgula como separador decimal; FCCE: documento mensal com vencimento até o quinto dia útil do
  mês seguinte.

A gravação em disco usa arquivo temporário no mesmo diretório + `os.replace`
(`atomic_write_bytes`).

## Não são verificados

- A página não fixa a escala de `VL_QUOTA_ULT_DIA_MES` ("decimal"): adotadas 12 casas, como no
  `VL_QUOTA` do Informe Diário.
- A página não limita a largura dos inteiros: aceitos até 999.999.999.999 (módulo).
- Valores negativos não são mencionados; como a página não impõe sinal, são aceitos em todos
  os campos de valor inteiros (`PATRIM_LIQ`, `QUOTA_EMITIDA_MES`, `QUOTA_RESG_MES`, as posições
  de `APLICACOES` e `MERC_A_TERMO`, prêmios e margem), recusados só em `NR_TOT_QUOTST_ULT_DIA_MES`.
- `VL_QUOTA_ULT_DIA_MES` aceita até 16 dígitos inteiros e 12 decimais, mais largo que os
  inteiros (12 dígitos), porque a página não fixa a largura de nenhum dos dois.
- Não há limite de fundos por arquivo na página; nenhum é imposto. CNPJ repetido no mesmo
  arquivo não é recusado.
- Não é verificado que `DT_COMPT` é anterior a `DT_GERAC_ARQ`, nem o prazo de envio.
- Não é verificado que o fundo pertence ao administrador do `CNPJ_ADM`, nem que o tipo do
  fundo corresponde à variante escolhida.
- Não é verificada coerência entre campos (por exemplo, soma das aplicações contra o patrimônio
  líquido).
- Os comentários de exemplo das páginas ("SUBSTITUA ESTA FRASE...") não são emitidos.
- Nenhum validador da CVM foi executado.

## Exemplos

```python
from layouts_cvm import InformeSintetico

doc = dict(
    header={
        "cod_doc": 8,
        "cnpj_adm": "11222333000181",
        "dt_compt": "06/2026",
        "dt_gerac_arq": "15/07/2026",
    },
    rows=[
        {
            "cnpj_fundo": "11444777000161",
            "aplicacoes_pos_final": {
                "aplicacoes": {
                    "cotas": 1000,
                    "tit_public": 200,
                    "tit_renda_fixa_emiss_instit_financ": 300,
                    "cota_fdo_invest_financ": 0,
                    "outra_aplic": 0,
                },
                "outras": {
                    "nr_tot_quotst_ult_dia_mes": 12,
                    "vl_quota_ult_dia_mes": "12.5",
                    "patrim_liq": 1500,
                    "quota_emitida_mes": 10,
                    "quota_resg_mes": 5,
                },
            },
        }
    ],
)

print(InformeSintetico().export(doc))
InformeSintetico().export(doc, output_path="informe_sintetico.xml")
```
