# **Informe Semestral de Investidor Não Residente — Parte II**

Envio (→ CVM) da **Parte II** do Informe Semestral de Investidor Não Residente: as aplicações de
cada participante (`COD_DOC=70`,
[`PadraoXMLInfoSemestralINRParte2.aspx`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoSemestralINRParte2.aspx)).

> **Veja também:** [Informe Mensal de Investidor Não Residente](inr_mensal.md) ·
> [CDA (V4)](cda.md) · [Referência da API](api/index.md)

## Descrição

Monte um `InformeSemestralInrParte2Document` (cabeçalho `CAB_INFORM` + `LISTA_INFORM` com **1
a 1000** `INFORM`, um por participante) e serialize com
`InformeSemestralInrParte2().export(doc, output_path=None)`. Namespace `urn:cda`, `COD_DOC=70`,
`VERSAO=1.0`, `windows-1252`. O `export` aceita o modelo ou um `Mapping` cujas chaves são os nomes
das tags em minúsculas (`cab_inform`, `lista_inform`, `inform`, `lista_ativ`, …).

## Parte I e Parte II

O Informe Semestral tem duas partes, cada uma um arquivo próprio: a **Parte I** (`COD_DOC=69`,
dados dos participantes) e esta **Parte II** (`COD_DOC=70`, aplicações). Elas são enviadas
**juntas**, mas este writer valida só o arquivo da Parte II: a **consistência entre as partes não
é verificada** (por exemplo, que um `COD_PARTIC` da Parte II exista na Parte I do mesmo semestre).

A estrutura é a do CDA (mesmos blocos e mesmo aninhamento `APLIC`/`POS_FIM`), mas é outro padrão:
os modelos são próprios e só o vocabulário de campos (tipos de data, de quantidade e de valor)
é compartilhado com o CDA.

## Blocos de `LISTA_ATIV`

Cada bloco pode se repetir, mas a ordem é a da página:

1. `TIT_PUB` — títulos públicos do Selic (tipos 75, 147)
2. `COTAS` — cotas de fundos (197; o tipo é implícito, a tag `COD_TP_APLIC` não existe no bloco)
3. `SWAP` — diferencial de swap (183, 184), seguido de um único `NOCION_SWAP`
4. `DEMAIS_CODIF` — demais ativos codificados (37, 39, 40, 42, 43, 102, 103, 143, 146, 151, 152,
   193, 198)
5. `DEP_PRAZO_TIT_IF` — depósitos a prazo e outros títulos de IF (74, implícito)
6. `TIT_AGRO_CRED_PRIV` — agronegócio e crédito privado (193, 195, 196)
7. `INV_EXT` — investimento no exterior (189, implícito)
8. `DEMAIS_N_CODIF` — ativos sem código no cadastro (48, 75, 94, 96, 97, 147, 187, 191, 192, 199,
   200 e os tipos de `DEMAIS_CODIF` exceto 193)

## Escalas

`MERC_POS_FIM`, `NOCION_POS_FIM` e `NOCION_SWAP` têm 15 inteiros + 2 decimais; `QTDE_POS_FIM`,
15 + 6; `TIT_POS_FIX_PR_INDEX`, `TIT_POS_FIX_CUPOM` e `TIT_PRE_FIX_TAXA_CONTR`, 3 + 6. Excesso de
casas é truncado, nunca arredondado; passe `str`/`Decimal`, nunca `float`. A vírgula é o
separador decimal e CPF/CNPJ são escritos sem pontuação e sem zeros à esquerda, como a página exige.
`VALOR_AT_EXT` é "numérico (float)" na página, sem escala: o valor é mantido como `Decimal`, sem
truncar.

## Regras verificadas

- Tipos de aplicação aceitos por bloco, *Tabela A* (`QTDE_POS_FIM` e `NOCION_POS_FIM`
  obrigatórios ou proibidos por tipo) e *Tabela B* (tipo de aplicação × tipo de ativo).
- `NOCION_SWAP` presente se, e somente se, houver `SWAP`.
- Pós-fixado (`ST_TIT_POS_FIX=S`) exige `TIT_POS_FIX_INDEX` (indexador da *Tabela D*) e proíbe
  `TIT_PRE_FIX_TAXA_CONTR`; pré-fixado exige a taxa e proíbe o bloco.
- `CLASSIF_RISCO` presente se, e somente se, `ST_CLASSIF_RISCO=S`.
- `COD_PAIS` da *Tabela G* e `COD_BV_MERC` da *Tabela H*.
- `COD_PARTIC` no formato `AAAAA.BBBBBB.CCCCCC.T-DV`; CPF/CNPJ com dígitos verificadores.

## Não são verificados

- A consistência entre a Parte I e a Parte II (acima).
- Que `COD_SELIC`, `COD_ATIV` e `DT_INI_VIGEN` existam nos cadastros do Selic e da consulta
  pública de ativos.
- `COD_SWAP`: só o formato `SWP` + 3 caracteres; a *Tabela E* não é conferida.
- O dígito verificador do `COD_PARTIC` (a página não publica o algoritmo).
- O tamanho máximo de 10 MB do arquivo.
- Que um participante tenha ao menos um ativo: a página não fixa a cardinalidade de `LISTA_ATIV`, que pode vir vazia.
- Que a mesma competência valha para todo o arquivo (há uma só, no cabeçalho).
- Chaves desconhecidas em um `Mapping` (por exemplo `cod_tp_aplic` dentro de `COTAS`, onde a
  página não tem essa tag) são ignoradas, como nos demais writers; a tag nunca é emitida.

## Divergências da página

- A *Tabela A* aparece duas vezes na página: a versão visível (colunas *Quant.*, *Mercado*,
  *Nocional*) e uma versão antiga em comentário HTML (vendas, aquisições, posição final). Elas
  discordam no tipo 200 (*Outras operações passivas e exigibilidades*); vale a versão visível, que
  exige `QTDE_POS_FIM`.
- `TIT_POS_FIX_CUPOM` é descrito como "se houver" e, na mesma frase, "obrigatório para títulos
  pós-fixados"; o writer o exige (use `0` quando não há cupom).
- A *Tabela E* tem uma linha "Outros" sem código de 3 caracteres.
- Não há *Tabela F*: a página vai da E para a G.
