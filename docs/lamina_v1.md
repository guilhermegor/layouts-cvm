# **Lâmina de Fundos — V1**

Envio (→ CVM) do padrão **Lâmina de Fundos V1**, que atende à ICVM 409 com as alterações da
ICVM 522 de 2012
([`PadraoXMLLamina.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLLamina.asp)).

> **Veja também:** [Lâmina de Fundos (V3)](lamina.md) · [Lâmina de Fundos (V2)](lamina_v2.md) ·
> [Referência da API](api/index.md)

## Descrição

Monte um `LaminaV1Document` (cabeçalho + de 1 a 70 fundos, todos da mesma competência) e
serialize com `LaminaV1().export(doc, output_path=None)`; `doc` também pode ser um mapeamento
simples, validado antes de gravar. Namespace `urn:lamina`, `COD_DOC=24`, `VERSAO=1.0`,
`windows-1252`. Com `output_path` o arquivo é gravado de forma atômica e o retorno é `None`.

## Diferenças medidas contra o V3

- `VERSAO` é `1.0` (`COD_DOC` continua `24`).
- O fundo é identificado **somente** por `CNPJ_FUNDO`, obrigatório; não há `COD_SUBCLASSE`.
- Existe `CONC_EMISSOR` (teto de concentração em um só emissor), entre `ALAV` e
  `PERDAS_SIGN`. A página não marca `ALAV` como opcional, então ele é obrigatório.
- Não existem no V1: `UTILIZ_DERIV_APENAS_PROTECAO_CART`, `PERC_MAX`, `OBS_HOR_APL_RESG`,
  `TP_PRAZO_DIAS` (`PRAZO_PAGAM` é sempre em dias úteis), `DS_FORMA_REMUN_DISTR`,
  `PRINC_DISTR_OFERTA`, `PRINC_CONFLITO_INTERES` e `INFO_ADIC`.

Como campos somem e um aparece no meio da sequência, o `INFORM` do V1 não estende o do V3; ele
declara o próprio e reaproveita todos os sub-blocos, tipos e tamanhos de texto do V3.

## Decisões e contradições da página

- A página não declara escala decimal (apenas "float"). Seguem-se as do V3: valores monetários
  com 2 casas e percentuais com 4, truncados (nunca arredondados); `float` é recusado.
- Namespace: o exemplo traz `urn:lamina` e a lista de tags traz `urn:infdiario`. O writer
  emite `urn:lamina`.
- Tabela mensal: o exemplo usa `MES`, `RENT_MENS`, `VAR_MENS_IND_REF`,
  `RENT_MENS_PERC_IND_REF`; a lista de tags usa `MES_RENT`, `RENT_LIQ`, `VAR_IND_REF`,
  `RENT_PERC_IND_REF`. O writer segue o exemplo (igual ao V3).
- `TEL_SAC` é "long, apenas números": só dígitos.
- `RECLAMACOES` tem no máximo 50 caracteres, como na página.
