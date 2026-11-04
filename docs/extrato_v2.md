# **Extrato das Informações sobre o Fundo — V2**

Envio (→ CVM) do padrão **Extrato das Informações sobre o Fundo V2**
([`PadraoXMLInfExtratoV2.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfExtratoV2.asp)).

> **Veja também:** [Referência da API](api/index.md) para cada símbolo público · [Uso](usage.md)
> para instalação e o conceito geral.

---

## Descrição

Monte um `ExtratoV2Document` (um `ExtratoV2Header` + de 1 a 1000 `ExtratoV2Row`, uma por fundo) e serialize com `ExtratoV2().export(...)`. O arquivo não pode passar de **1 MB**.

| Modelo | Tag XML | Papel |
|--------|---------|-------|
| `ExtratoV2Document` | `DOC_ARQ` / `EXTRATO_FUNDO` | Documento: `header` + `rows`. |
| `ExtratoV2Header` | `CAB_INFORM` | `COD_DOC` = 41 e `VERSAO` = 2.0 (fixos), `DT_GERAC_ARQ` `DD/MM/AAAA`. |
| `ExtratoV2Row` | `ROW_EXTRATO` | O extrato de um fundo. |

Os blocos internos (`FormaCondominio`, `Prazo`, `FundoAnbima`, `FundoInvertCotas`, `ValorCota`,
`ResgCotas`, `PrazoPagamResg`, `TxPerfm`/`CalcTxPerfm`, `TxIngresso`, `TxSaida`, `OperDeriv`,
`OperPatrimLiq`, `AtivExter`, `FundoAtivos`, `RegulamentoTipoEmissor`,
`RegulamentoModalidadeAtivo`) têm como campos o nome da tag em minúsculas, **na ordem do arquivo
de exemplo da CVM**; o serializador omite o que é `None`. Os modelos são imutáveis e recusam campos
desconhecidos. O CNPJ do fundo (`cnpj_fdo`) é validado por dígito verificador e gravado sem máscara.

## Tipagem

### Decimais

A página fixa **2 casas** nos limites mínimo e máximo, na aplicação mínima e no teto de crédito
privado, e **até 6** na taxa máxima de custódia. Nos demais percentuais não informa escala: foram
aplicadas **4 casas** (política do repositório, não número da CVM). Sempre truncamento em direção a
zero; entram `Decimal`, `int` e `str`, e **`float`, `bool`, NaN e infinito são recusados**. A
vírgula é o separador decimal na saída. Percentuais ficam entre 0 e 100.

### Regras por resposta (blocos condicionais)

Cada bloco aplica o que a página diz: `FECHADO` exige `ABERTA_NEG_MER_ORGAN`; mercado organizado `S`
é o único que admite `LISTA_MERC_BLOQUEIO`; `DETERMINADO` exige o detalhamento; ANBIMA `S` exige o
código (1 a 68) e `N` o proíbe; análogo para fundo de fundos, valor da cota, carência, taxas de
performance/ingresso/saída, derivativos, operações acima do PL, ativos no exterior e crédito
privado. Taxa em R$ (`2`) aceita só 2 casas. Em cada par `*_MIN`/`*_MAX` o mínimo não ultrapassa o
máximo. A taxa de performance de público **não qualificado** exige taxa, índice (tabela D: 1 a 35
ou 99) e percentual do índice, e proíbe `INFO_ADICIONAL`.

### Texto e datas <!-- codespell:ignore datas -->

Textos são não vazios, no teto da página (`DETALHAMENTO_PRAZO` 200; `INFO_ADICIONAL` 5 a 400),
sem caracteres de controle e codificáveis em `windows-1252`. Datas são lidas de fato <!-- codespell:ignore Datas,controle,datas -->
(`31/02/2026` é recusada).

## Política de retry

Não se aplica: o writer não faz rede. O texto é codificado e checado como XML bem formado e
dentro de 1 MB **antes** de abrir o destino; uma falha levanta `ValueError` e **não trunca** um
arquivo já existente.

## Diferenças em relação ao V3

Comparada com a página do V3 em 03/11/2026, a página do V2 traz o **mesmo arquivo de exemplo**
(138 tags, mesma ordem); mudam `VERSAO` (2.0) e o texto (fundo no lugar de classe de cotas). O V3
marca dez tags da linha como "Tag opcional"; o V2 não marca nenhuma. Por isso são **obrigatórias**
no V2: `PUBLICO_ALVO`, `COD_DISTR_FDO`, `APLICACAO_MINIMA_FUNDO`, `TIPO_VALOR_COTA`,
`VALOR_COTA_BASE_PL`, `QT_DIA_CONV_COTA`, `QT_DIA_PAGAM_COTA`, `PRAZO_PAGAM_RESG`, `TAXA_ADM` e
`TAXA_MAXIMA_CUSTODIA`. Os blocos internos são os do [V3](extrato.md), reaproveitados.

## Divergências da página (escolhas documentadas)

- O exemplo e a lista de tags descrevem duas gerações do formulário. Seguiu-se o **exemplo** para a
  estrutura; blocos que só existem na lista de tags (`COTA_MERC_SECUND`, `COTISTA_EXCV`,
  `SERV_ATEND_COTISTA`, `LIM_*`, ...) **não** são modelados.
- Namespace: exemplo `urn:extr`, lista `urn:perf`. Usado `urn:extr`. CNPJ: exemplo `CNPJ_FDO`,
  lista `CNPJ_FUNDO`. Usado `CNPJ_FDO`.
- Taxa de saída: o exemplo reutiliza a tag `TP_VL_FIXO_TX_INGRESSO` dentro de `TX_SAIDA`; é
  emitida como está.
- Política de investimento: a tabela C lista 1 a 3, o questionário acrescenta 4 (Enhanced);
  aceito 1 a 4.
- Taxa de performance: o exemplo marca tudo obrigatório; a lista de tags o torna dependente do
  público-alvo. Seguiu-se a lista.
- Valores sem número na página: dias 0 a 9999; `PRAZO_ATUALIZACAO` 1 a 200 caracteres.

## Não são verificados

- Dependência entre o público-alvo e o teto de aplicação em cotas de fundos (ICVM 555).
- Coerência entre os limites mínimo/máximo e o regulamento do fundo (só `MIN <= MAX` é checado).
- Escala dos percentuais que a página não numera (4 casas, política do repositório).
- Existência do CNPJ na CVM (só o dígito verificador) e do fundo no cadastro.
- Nenhuma validação da CVM foi executada contra a saída.

## Exemplos

```python
from layouts_cvm import ExtratoV2

row = {...}  # substitua pelos campos da linha (ver acima)
doc = dict(
    header=dict(dt_gerac_arq="31/10/2026"),
    rows=[row],  # row: um dict com os campos acima, uma linha por fundo
)
xml = ExtratoV2().export(doc)                       # retorna str
ExtratoV2().export(doc, output_path="extrato.xml")  # grava windows-1252, retorna None
```
