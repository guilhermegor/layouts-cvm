# **Informe Anual de Auditor**

Envio (→ CVM) do padrão **Informe Anual de Auditor**
([`PadraoXMLAuditorAnual.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLAuditorAnual.asp)).

> **Veja também:** [Referência da API](api/index.md)

## Descrição

Monte um `InformeAnualAuditorDocument` (um único auditor e um único ano-base) e serialize com
`InformeAnualAuditor().export(doc, output_path=None)`; `doc` também pode ser um mapeamento
simples, validado antes de gravar. Namespace `urn:audtanual`, `COD_DOC=23`, `windows-1252`. Com
`output_path` o arquivo é gravado de forma atômica e o retorno é `None`.

Os blocos repetidos ficam dentro de um bloco `LISTA_*`, como no exemplo da página
(`LISTA_ENDER` > `ENDER`, `LISTA_RESP` > `RESP`, `LISTA_ENTID_AUDITA` > `ENTID_AUDITA`,
`LISTA_ENTID_COLIG` > `ENTID_COLIG`).

## Regras verificadas

- `MOTIVO_ENTREG` é 1, 2 ou 3; `DT_GERAC_ARQ` é uma data real `DD/MM/AAAA`; `ANO_BASE` tem
  quatro dígitos.
- `NR_PF_PJ` é CPF (PF) ou CNPJ (PJ) com dígitos verificadores válidos e **sem** pontos, traços
  ou barras.
- Textos respeitam os máximos da página: nome do auditor 100, e-mail 50, filial 100, logradouro
  30, complemento 18, bairro 30, critérios de honorários 500, coligada 100 e ramo 30.
- Endereços: de 1 a 1.000; `NM_FILIAL` é omitido na sede (`TP_ENDER` 1); `NR_CEP`, `NR_DDD_TEL`, `NR_TEL`,
  `NR_DDD_FAX` e `NR_FAX` são textos de dígitos e mantêm zeros à esquerda.
- Auditor PF: um único endereço, sem `NM_FILIAL`, sem `LISTA_RESP` e sem `QT_SOCIOS`.
- Entidades auditadas: até 8.000; `TP_ENTID` deve constar da Tabela B; `NR_PJ` é CNPJ válido.
- Coligadas: até 1.000; `NR_PJ` é obrigatório, exceto para estrangeira (`ST_ESTR` = `S`), quando
  deve ser omitido.
- `VL_AUDIT`, `PR_AUDIT` e `PR_FATURA` têm 2 casas decimais, truncadas (nunca arredondadas),
  vírgula como separador; percentuais ficam entre 0 e 100. `float` é recusado.

## Decisões e contradições da página

- O bloco de treinamentos (`LISTA_TREINA`, `TREINA`, `TREINA_PESSOA` e as Tabelas C e D) está
  dentro de comentário HTML na página, portanto fora do padrão vigente: **não é modelado**.
- A página não declara limite de tamanho para `DS_NOME` da entidade auditada; não há limite.

## Não são verificados

- Que `DS_EMAIL` contenha um único endereço, ou que seja um e-mail válido.
- Que `CD_MUN` seja um código de município válido (a página remete a uma lista externa) e o
  tamanho de `NR_CEP`, DDD, telefone e fax.
- Que exista exatamente uma sede entre os endereços, e que o nome da filial seja informado nas
  filiais.
- Que `PR_FATURA` só seja informado quando superior a 10%, nem que `DT_CONTR` só seja informado
  na primeira auditoria.
- Que `ANO_BASE` coincida com a data de geração, ou que o prazo (último dia útil de abril) tenha
  sido respeitado.
- O limite de 3 endereços, 10 entidades e 2 coligadas do envio por formulário web (o writer
  segue os limites de upload).
