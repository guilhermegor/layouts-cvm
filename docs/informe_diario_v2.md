# **Informe Diário — V2**

Envio (→ CVM) do padrão **Informe Diário V2**, vigente de 01/07/2012 a 30/09/2015
([`PadraoXMLInfoDiarioNet739.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoDiarioNet739.asp)).

> **Veja também:** [Informe Diário (V4)](informe_diario.md) · [Informe Diário (V3)](informe_diario_v3.md) · [Referência da API](api/index.md)

## Descrição

Monte um `InformeDiarioV2Document` (`InformeDiarioV2Header` + até 100 `InformeDiarioV2Inform`)
e serialize com `InformeDiarioV2().export(doc, output_path=None)`. Namespace `urn:infdiario`,
`COD_DOC=1`, `VERSAO=2.0`, `windows-1252`. Todos os informes de um arquivo têm a mesma
competência.

## Diferenças medidas contra o V4/V3

A página foi comparada ao schema V4. O V2 difere em:

- `VERSAO` é `2.0`.
- O fundo é identificado **somente** por `CNPJ_FDO`; `COD_SUBCLASSE` não existe.
- `DATA_PROX_PL` não existe: o `INFORM` vai de `CNPJ_FDO` direto a `VL_TOTAL`.
- Os fundos ficam dentro de `LISTA_INFORM` (os writers V3/V4 não emitem esse bloco).

Cabeçalho, escalas (2 casas; `VL_QUOTA` até 12; `PR_COTST` até 4) e o bloco `COTST_SIGNIF` são
idênticos ao V4 e importados dele. Como o `INFORM` não é um subconjunto do V4, o writer não
delega ao writer V4: usa o serializador de elementos compartilhado (`xml_writer`).

Ordem das tags do `INFORM`: `CNPJ_FDO`, `VL_TOTAL`, `VL_QUOTA`, `PATRIM_LIQ`, `CAPTC_DIA`,
`RESG_DIA`, `VL_TOTAL_SAI`, `VL_TOTAL_ATV`, `NR_COTST`, `LISTA_COTST_SIGNIF`.

## Decisões

- `NOME_FUNDO`, `RESG_NAO_PROCES` e `LIQ_DIA_DISPON` aparecem na descrição das tags, mas
  cercados por `-->` e ausentes do modelo XML: não são emitidos.
- `LISTA_COTST_SIGNIF` é opcional (a página só pede os cotistas com 20% ou mais quando a CVM
  solicita) e é omitida quando vazia; a página não diz se um bloco vazio é válido.
- O `INFORM` rejeita campos desconhecidos (`DATA_PROX_PL`, `COD_SUBCLASSE`), em vez de
  descartá-los em silêncio.
- Excesso de casas decimais é truncado, nunca arredondado; o separador decimal é a vírgula.
- A escrita em arquivo é atômica.
