# **Demonstrativo de Fontes e Aplicações de Recursos (FAR)**

Envio (→ CVM) do padrão **FAR**, informe mensal do fluxo de caixa do fundo, com vencimento até o
dia 15 do mês seguinte ([`PadraoXMLFAR.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLFAR.asp)).

> **Veja também:** [Referência da API](api/index.md) · [Uso](usage.md)

---

## Descrição

Passe os dados como `dict` a `DemonstrativoFar().export(...)`, que os valida. Um arquivo
traz fundos de uma mesma competência e de um mesmo administrador. O XML não tem namespace e usa
`windows-1252`.

| Modelo | Tag XML | Papel |
|--------|---------|-------|
| `DemonstrativoFarDocument` | `DOC_ARQ` | `desc_adm` + `far`. |
| `DemonstrativoFarDescAdm` | `DESC_ADM` | `cod_doc` (4), `cnpj_adm`, `dt_compt` (`MM/AAAA`), `dt_gerac_arq`. |
| `DemonstrativoFarFar` | `FAR` | `row_registro_movimento`: um por fundo, sem CNPJ repetido. |
| `DemonstrativoFarRegistro` | `ROW_REGISTRO_MOVIMENTO` | Quotas, quotistas, distribuição e `doc_mov_mes`. |
| `DemonstrativoFarDocMovMes` | `DOC_MOV_MES` | `row_mov_por_fundo`: as movimentações do fundo. |
| `DemonstrativoFarMovimento` | `ROW_MOV_POR_FUNDO` | `cd_mov`, `vl_entr`, `vl_saida` (R$ 1000). |

Cada campo é a tag da página em minúsculas, na ordem do XML.

## Tipagem

- `nr_quota_circul_ult_dia_mes`, `vl_quota_ult_dia_mes`, `vl_ult_distr_quota` e
  `vl_quota_dt_ult_distr`: `Decimal` com **10 casas**; `float` é recusado, casas excedentes são
  truncadas, vírgula decimal na saída.
- `nr_total_quotst_ult_dia_mes`, `vl_entr`, `vl_saida`: inteiros ≥ 0.
- A distribuição (`vl_ult_distr_quota`, `dt_distr`, `vl_quota_dt_ult_distr`) é preenchida
  nos três campos ou em nenhum, como diz a página.
- `cd_mov`: apenas os códigos da Tabela A; as colunas `S` são obrigatórias e as `N` ficam
  vazias (omitidas). Um código não se repete no mesmo fundo.
- `cnpj_adm` e `cnpj_fundo`: CNPJ com dígitos verificadores, gravado sem máscara.

## Limites aplicados (escolha do projeto, a página não os fixa)

- Até 18 dígitos inteiros nos decimais e 999.999.999.999 nos inteiros.
- Valores negativos são recusados em todos os campos numéricos; um decimal negativo que o truncamento reduz a zero (`-0.00000000001`) vale zero e é gravado sem sinal.

## Não são verificados

- Que **todos** os tipos da Tabela A apareçam em cada fundo: não é verificado por padrão; use `require_all_movements=True` (veja abaixo).
- Que `dt_distr` caia no mês da competência.
- Que os fundos pertençam ao administrador `cnpj_adm`.
- Que `dt_gerac_arq` não seja anterior à competência.
- Limite de fundos por arquivo.
- Nenhum validador da CVM foi executado.

## Exemplo

O exemplo traz um único movimento por fundo para ser curto; a página pede todos os tipos da Tabela A, o que o escritor só verifica com `require_all_movements=True` (veja abaixo).

```python
from layouts_cvm import DemonstrativoFar

doc = {
    "desc_adm": {"cnpj_adm": "11222333000181", "dt_compt": "06/2017", "dt_gerac_arq": "15/07/2017"},
    "far": {
        "row_registro_movimento": [
            {
                "cnpj_fundo": "11444777000161",
                "nr_quota_circul_ult_dia_mes": "1000.5",
                "vl_quota_ult_dia_mes": "12.5",
                "nr_total_quotst_ult_dia_mes": 40,
                "doc_mov_mes": {"row_mov_por_fundo": [{"cd_mov": 53, "vl_entr": 10}]},
            }
        ]
    },
}

print(DemonstrativoFar().export(doc))
```

## Exigir todos os tipos da Tabela A

A página diz que todos os tipos da Tabela A devem ser utilizados. Por padrão o escritor não exige isso. Com `require_all_movements=True` (só por nome), `export` recusa o documento cujo fundo não use todos os códigos em `row_mov_por_fundo`, com um único `ValueError` que traz, para cada fundo incompleto, o CNPJ e os códigos ausentes em ordem crescente. A verificação roda no documento já construído; sem a opção a saída não muda.

```python
DemonstrativoFar().export(doc, require_all_movements=True)
```
```

Com o `doc` do exemplo acima, que só usa o código 53, a saída real é:

```text
ValueError: fund 11444777000161 does not use Table A codes [37, 48, 54, 55, 56, 57, 58, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 77, 78, 144, 145, 150]
