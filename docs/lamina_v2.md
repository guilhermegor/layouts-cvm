# **Lâmina de Fundos — V2**

Envio (→ CVM) do padrão **Lâmina de Fundos V2**, vigente a partir de 01/10/2015 (ICVM 555)
([`PadraoXMLLaminaV2.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLLaminaV2.asp)).

> **Veja também:** [Lâmina de Fundos (V3)](lamina.md) · [Referência da API](api/index.md)

## Descrição

Monte um `LaminaV2Document` (`LaminaV2Header` + de 1 a 70 `LaminaV2Inform`, todos da mesma
competência) e serialize com `LaminaV2().export(doc, output_path=None)`. Namespace
`urn:lamina`, `COD_DOC=24`, `VERSAO=2.0`, `windows-1252`. Com `output_path` o arquivo é
gravado de forma atômica e o retorno é `None`.

## Diferenças medidas contra o V3

A página foi comparada ao schema V3. Há três diferenças:

- `VERSAO` é `2.0` (`COD_DOC` continua `24`).
- O fundo é identificado **somente** por `CNPJ_FUNDO`, obrigatório; `COD_SUBCLASSE` não existe
  (rejeitado).
- Cada linha de `TAB_RENT_MENSAL` usa os nomes da tabela de retorno por ano: `MES`, `RENT_LIQ`,
  `VAR_IND_REF`, `RENT_PERC_IND_REF`, `COMENTARIOS`. No V3 as três colunas de valor se chamam
  `RENT_MENS`, `VAR_MENS_IND_REF` e `RENT_MENS_PERC_IND_REF`.

Ordem das tags, escalas, tamanhos de texto e cardinalidades são os do V3, por isso os modelos
estendem os do V3 e o writer delega ao `Lamina` por composição, sem copiar a lógica de serialização.

## Decisões

- A página não declara escala decimal. Seguem-se as do V3: valores monetários com 2 casas e
  percentuais com 4, truncados (nunca arredondados); `float` é recusado.
- A página é inconsistente quanto ao namespace: o exemplo traz `urn:lamina` e a lista de tags
  traz `urn:infdiario`. O writer emite `urn:lamina`, como no V3.
- O mês da tabela mensal aparece como `MES` no exemplo e `MES_RENT` na lista de tags. O writer
  emite `MES`, igual ao V3.
- `RECLAMACOES` tem no máximo 50 caracteres, como na página.
