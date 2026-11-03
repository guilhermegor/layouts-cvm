# **Informe Diário — V1**

Envio (→ CVM) do padrão **Informe Diário V1**, vigente até 01/07/2012
([`PadraoXMLInfoDiarioNet.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoDiarioNet.asp)).

> **Veja também:** [Informe Diário (V2)](informe_diario_v2.md) · [Informe Diário (V4)](informe_diario.md) · [Referência da API](api/index.md)

## Descrição

Monte um `InformeDiarioV1Document` (`InformeDiarioV1Header` + até 100 `InformeDiarioV1Inform`)
e serialize com `InformeDiarioV1().export(doc, output_path=None)`. Também aceita um `Mapping`
simples, validado para o modelo. Namespace `urn:infdiario`, `COD_DOC=1`, `windows-1252`. Todos
os informes de um arquivo têm a mesma competência.

## Diferenças medidas contra o V2

- O cabeçalho **não tem `VERSAO`**: só `COD_DOC`, `DT_COMPT`, `DT_GERAC_ARQ`.
- O `INFORM` **não tem `VL_TOTAL_SAI` nem `VL_TOTAL_ATV`**.

Ordem das tags do `INFORM`: `CNPJ_FDO`, `VL_TOTAL`, `VL_QUOTA`, `PATRIM_LIQ`, `CAPTC_DIA`,
`RESG_DIA`, `NR_COTST`, `LISTA_COTST_SIGNIF`.

Escalas (2 casas; `VL_QUOTA` até 12; `PR_COTST` até 4), `LISTA_INFORM` e o bloco
`COTST_SIGNIF` são idênticos ao V2 e importados dele.

## Decisões

- A página não traz número de versão nem período de vigência; o início da vigência (05/04/2004,
  obrigatoriedade do formato) e o fim (01/07/2012) vêm do catálogo da CVM.
- `LISTA_COTST_SIGNIF` é opcional e omitida quando vazia.
- O `INFORM` rejeita campos desconhecidos (`VL_TOTAL_SAI`, `DATA_PROX_PL`, `COD_SUBCLASSE`).
- Excesso de casas decimais é truncado, nunca arredondado; o separador decimal é a vírgula.
- A escrita em arquivo é atômica.
