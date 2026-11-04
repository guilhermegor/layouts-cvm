# **Informe Mensal FIDC — ICVM 489**

Envio (→ CVM) do padrão **Informe Mensal FIDC** da ICVM 489, vigente até a data-base 2019-11-01
([`PadraoXMLMensalFIDC489.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLMensalFIDC489.asp)).
O layout vigente (ICVM 576) está em [Informe Mensal FIDC — ICVM 576](inf_mensal_fidc.md).

> **Veja também:** [Uso](usage.md) para instalação e o conceito geral.

---

## Descrição

Monte um `InfMensalFidc489Document` (`cab_inform` + `lista_inform`) e serialize com
`InfMensalFidc489().export(...)`. O arquivo contém **um** informe: um fundo e uma competência
(`DOC_ARQ`, namespace `urn:fidc`, `windows-1252`). Os blocos idênticos aos da ICVM 576 são
reaproveitados do schema dela; só diferem `CAB_INFORM`, `LISTA_INFORM` (totais cruzados), `APLIC_ATIVO` e `OUTRAS_INFORM`.

## Regras aplicadas (todas da página)

- **Decimais:** valores monetários, quantidades e percentuais com **2** casas; quantidade e valor
  de cota (`QT_COTAS`/`VL_COTAS` das séries, `QT_COTAS` dos movimentos, `VL_COTA` das
  amortizações) com até **8**. O excedente é **truncado** (`ROUND_DOWN`). Vírgula decimal.
- **Cabeçalho:** sem prazos de resgate (`PR_ENTRE_*`/`TP_DIAS_*` não existem nesta versão).
- **Somatórios (itens 1 a 31):** os itens 1, 2, 30 e 31 e os totais cruzados são verificados
  aqui; os demais vêm dos blocos reaproveitados do layout ICVM 576. Cada total deve ser igual à soma prescrita; a provisão
  (`VL_PROVIS_REDUC_RECUP`) deve ser não negativa e menor ou igual aos créditos que cobre;
  `VL_SOM_PRAZO_VENC` e `VL_SOM_INAD_VENC` fecham com os créditos existentes; item 31 é a soma
  das `QT_COTISTAS_SUBORD`.
- **Sacados:** de 1 a 25, com CPF/CNPJ válido ou o marcador `99.999.999/9999-99` /
  `999.999.999-99`.
- **Classe sênior** obrigatória em todos os blocos; os `*_SUBORD` são opcionais.
- **Fundo aberto** deve informar ao menos um campo de `LIQUIDEZ`.
- Tags desconhecidas levantam `ValidationError`.

## Não são verificados

- A vigência (até a data-base 2019-11-01): a página do padrão não traz data, então `DT_COMPT`
  só é validado como `MM/AAAA`; escolher este layout em vez do ICVM 576 é decisão de quem envia.
- Os limites mínimo/máximo "Validação para todos os subcampos" (itens de carteira): o trecho
  da página não traz os valores numéricos extraídos aqui.
- A ordem decrescente de cedentes e sacados, e o corte de 10% do patrimônio líquido dos cedentes.
- Que `PR_SOM_LISTA_DEV_SACADOS` seja coerente com o patrimônio líquido.
- O vínculo entre o tipo de fundo (FIDC, FIC-FIDC, FIDC-NP, ...) e os blocos preenchidos.

## Exemplo

```python
from layouts_cvm import InfMensalFidc489

InfMensalFidc489().export(payload, output_path="inf_mensal_fidc_489_201910.xml")
```
