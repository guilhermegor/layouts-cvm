# **CDA — V2**

Envio (→ CVM) do padrão **CDA V2** (Composição e Diversificação das Aplicações, versão 2.0,
[`PadraoXMLCDANet.aspx`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLCDANet.aspx)).

> **Veja também:** [CDA (V4)](cda.md) · [CDA (V3)](cda_v3.md) · [Referência da API](api/index.md)

## Descrição

Monte um `CdaV2Document` (`CdaV2Header` + até **50** `CdaV2Inform`, todos da mesma competência)
e serialize com `CdaV2().export(doc, output_path=None)`. Namespace `urn:cda`, `COD_DOC=3`,
`VERSAO=2.0`, `windows-1252`. O `export` aceita o modelo ou um `Mapping`.

## Diferenças medidas contra o V3 e o V4

A página V2 foi comparada com as páginas V3 e V4. Não é um delta: a estrutura é outra, então o
V2 tem modelos próprios (`CdaV2*`) e só reaproveita as folhas, as escalas e o percurso de tags do
writer V4.

- Cinco blocos de ativos, nesta ordem: `TIT_PUB`, `COTAS`, `SWAP`, `DEMAIS_CODIF`,
  `DEMAIS_N_CODIF`. Não existem `DEP_PRAZO_TIT_IF`, `TIT_AGRO_CRED_PRIV` nem `INV_EXT`.
- `APLIC` não tem `EMPR_LIGADA`. `POS_FIM` tem `CUSTO_CORREC_POS_FIM` entre `QTDE_POS_FIM` e
  `MERC_POS_FIM`.
- `QTDE_DIAS_CONFID` é obrigatório (0 a 90) em todo `APLIC`.
- `COTAS` tem `COD_TP_APLIC` e é identificado só por `CNPJ_FDO`.
- No `SWAP`, `NEGOC` traz só `TP_NEGOC`.
- A *Tabela A* tem 32 tipos de aplicação (V3/V4: 31, outros códigos), com coluna *Custo*; a
  coluna final lista os tipos de ativo relacionados.

## Escalas

`VL_PL` 21 inteiros + 2 decimais; `VL_VENDAS_NEGOC`, `VL_AQUIS_NEGOC`, `CUSTO_CORREC_POS_FIM` e
`MERC_POS_FIM` 15 + 2; `QTDE_VENDAS_NEGOC`, `QTDE_AQUIS_NEGOC` e `QTDE_POS_FIM` 15 + 6. Excesso
de casas é truncado, nunca arredondado; passe `str`/`Decimal`, nunca `float`.

## Não são verificados

- A página não diz quais tipos de aplicação cada bloco aceita. Os modelos derivam isso do tipo de
  ativo do bloco (`TIT_PUB` = 8, `COTAS` = 22, `SWAP` = 26) e da última coluna da *Tabela A*;
  em `DEMAIS_CODIF` valem os tipos de ativo do comentário do modelo XML da página.
- Em `DEMAIS_N_CODIF` vale qualquer tipo de ativo da *Tabela B*; a página não o restringe.
- Que `COD_SELIC`, `COD_ATIV` e `DT_INI_VIGEN` existam nos cadastros do Selic e da consulta
  pública de ativos.
- A *Tabela D* (códigos de swap) e a *Tabela C* (rentabilidades) não são conferidas: só o formato
  `SWP` + 3 caracteres.
- O tamanho máximo de 1 MB do arquivo.
- Que a data de competência seja a mesma em todos os informes (há uma só, no cabeçalho).
- Chaves desconhecidas em um `Mapping` (por exemplo `empr_ligada`) são ignoradas, como nos demais
  writers; a tag nunca é emitida.
