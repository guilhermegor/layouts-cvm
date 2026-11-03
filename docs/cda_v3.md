# **CDA — V3**

Envio (→ CVM) do padrão **CDA V3** (Composição e Diversificação das Aplicações, versão 3.0,
[`PadraoXMLCDANetV3.aspx`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLCDANetV3.aspx)).

> **Veja também:** [CDA (V4)](cda.md) · [Referência da API](api/index.md)

## Descrição

Monte um `CdaV3Document` (`CdaV3Header` + até **50** `CdaV3Inform`, todos da mesma competência)
e serialize com `CdaV3().export(doc, output_path=None)`. Namespace `urn:cda`, `COD_DOC=3`,
`VERSAO=3.0`, `windows-1252`.

## Diferenças medidas contra o V4

A página V3 foi comparada, tag a tag, com a página V4 e com o schema V4. As tabelas A a H, a
tabela *Blocos x Tipos de Aplicações*, as escalas decimais e a ordem das tags são idênticas.
Só há estas diferenças:

- `VERSAO` é `3.0` (`COD_DOC` continua `3`).
- Até 50 fundos por arquivo (V4: 1000).
- `COTAS` identifica o fundo investido **somente** por `CNPJ_FDO`; `COD_SUBCLASSE` não existe.
- `DEP_PRAZO_TIT_IF` não tem `DESC_ATIV_VINC`.
- `INV_EXT` não tem `INV_COLETIVO` nem `GEST_INV_COLETIVO`, e seu `APLIC` não tem `ATIVO_EXT`.

Os modelos V3 estendem os do V4 (`CdaV3Cotas`, `CdaV3DepPrazoTitIf`, `CdaV3InvExt`,
`CdaV3Aplic`); o writer delega ao writer V4 em vez de copiá-lo. Um campo que o V3 não define
continua existindo no modelo, mas é **rejeitado** quando preenchido, então sua tag nunca é emitida.

## Decisões

- Um fundo com `COD_SUBCLASSE` em `COTAS` deve ser enviado pelo [V4](cda.md).
- Excesso de casas decimais é truncado, nunca arredondado; passe `str`/`Decimal`, nunca `float`.
- Em `TIT_PUB` o `APLIC` do modelo XML lista `EMPR_LIGADA`, mas a *Tabela A* marca o campo como
  *Não Aplicável* para o tipo 75; vale a tabela (o campo é rejeitado), igual ao V4.
