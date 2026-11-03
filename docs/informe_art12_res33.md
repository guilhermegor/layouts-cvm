# **Informe Art. 12 Res. CVM 33 (Escriturador)**

Envio (→ CVM) do informe mensal dos escrituradores de valores mobiliários, conforme o art. 12 da
Resolução CVM 33
([`PadraoXMLPrest.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLPrest.asp)).

> **Veja também:** [Referência da API](api/index.md)

## Descrição

Passe um dicionário a `InformeArt12Res33().export(doc, output_path=None)`. O writer valida os
dados, emite `windows-1252` e o namespace `urn:prestserv`, com `COD_ARQ` fixo em `29`. O arquivo
tem uma única competência (`DT_COMPT`, `MM/AAAA`); os demais campos de data são `DD/MM/AAAA`.

```python
from layouts_cvm import InformeArt12Res33

doc = {
    "ds_inform": {"dt_compt": "01/2021", "dt_gerac_arq": "05/02/2021"},
    "prestadores": [
        {
            "ds_prest": {"cnpj_escriturador": "11222333000181", "cd_tp_prest": 41},
            "emissores": [
                {
                    "cnpj_emissor": "11444777000161",
                    "ativo": [
                        {
                            "ativo_escriturado": "A1",
                            "dt_inicio_contrato": "01/02/2020",
                            "dt_fim_contrato": "15/01/2021",
                        }
                    ],
                }
            ],
        }
    ],
}
xml = InformeArt12Res33().export(doc)
```

Ordem das tags: `COD_ARQ`, `DS_INFORM` (`DT_COMPT`, `DT_GERAC_ARQ`), `LISTA_PREST` >
`INFORM_PREST` > `DS_PREST` (`CNPJ_ESCRITURADOR`, `CD_TP_PREST`) + `LISTA_EMISSORES` > `EMISSOR`
(`CNPJ_EMISSOR`, `ATIVO` repetido: `ATIVO_ESCRITURADO`, `DT_INICIO_CONTRATO`,
`DT_FIM_CONTRATO`).

## Decisões

- A página abre `<LISTA_PREST>` mas fecha `</LISTA_APREST>`: é erro de digitação; emitimos
  `LISTA_PREST`.
- "Fillers de zeros à esquerda não devem ser utilizados" convive com os formatos `MM/AAAA` e
  `DD/MM/AAAA`: esses campos mantêm o zero do formato; `COD_ARQ` e `CD_TP_PREST` são inteiros.
- `CD_TP_PREST` aceita 41, 42, 52 e 65 (Tabela A), embora 42/52/65 tenham migrado para 41 em
  01/07/2014. `ATIVO_ESCRITURADO` aceita A1 (ações), A2 (debêntures), A3 (cotas de fundos) e A4 (outros),
  conforme a Tabela B.
- `DT_FIM_CONTRATO` é opcional (só quando o contrato foi encerrado no mês anterior) e não pode
  anteceder `DT_INICIO_CONTRATO` (inferência; a página não diz).
- Pelo menos um prestador, um emissor por prestador e um ativo por emissor (a página não diz).
- A página não declara campos decimais. CNPJs são validados (dígitos verificadores) e emitidos
  sem máscara. Campos desconhecidos são rejeitados. A escrita em arquivo é atômica.
