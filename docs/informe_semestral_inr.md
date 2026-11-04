# **Informe Semestral de Investidor não Residente — Parte I**

Envio (→ CVM) da **Parte I** do Informe Semestral INR
([`PadraoXMLInfoSemestralINRParte1.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoSemestralINRParte1.asp)).

> **Veja também:** [Informe Mensal INR](inr_mensal.md), de que a Parte I copia a estrutura (modelos próprios, congelados) ·
> [Referência da API](api/index.md) · [Uso](usage.md).

!!! warning "A Parte II NÃO está implementada"
    O Informe Semestral é composto por **dois arquivos enviados conjuntamente** (Parte I,
    `COD_DOC` 69; Parte II, `COD_DOC` 70), com os mesmos investidores nos dois. Esta biblioteca
    implementa **somente a Parte I**. A Parte II
    ([`PadraoXMLInfoSemestralINRParte2.aspx`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoSemestralINRParte2.aspx),
    as aplicações, no layout `urn:cda`) não tem writer. **Um arquivo da Parte I, sozinho, não
    forma um envio completo e não deve ser tratado como aceitável pela CVM.**

---

## Descrição

Monte um `InformeSemestralInrDocument` (um `InformeSemestralInrHeader` + de 1 a 1000
`InformeSemestralInrParticipante`, todos da mesma competência) e serialize com
`InformeSemestralInr().export(...)`. O XML usa o namespace `urn:infmensal`, `COD_DOC=69` e
`VERSAO=1.0`, gravado em `windows-1252`.

A Parte I tem a mesma estrutura do Informe Mensal INR, sem o bloco `APLICACOES`: os blocos
(`ENTRADA_SAIDA`, `MOV_RECURSOS`, `TRANSF_RECURSOS`, `RECURSOS_*_INVEST`) e as regras são os
descritos em [Informe Mensal INR](inr_mensal.md). `aplicacoes` é recusado nesta parte.

## Não são verificados

- **A Parte II** (ver aviso acima) e a consistência entre as duas partes (mesmos investidores,
  mesma competência).
- Que a competência (`DT_COMPT`) seja de fim de semestre: não confirmado na página da Parte I, nada é imposto além do formato `MM/AAAA`.
- O dígito verificador de `COD_PARTIC` (a página não publica o algoritmo); só se checa que é um
  dígito.
- Nenhuma checagem da CVM foi executada; o teste de sintaxe da própria CVM
  (`FormTestaArquivo`) não foi usado.
- A página pede "vírgula para casas decimais" mas descreve os valores como inteiros: adotou-se
  **inteiro**. Esta decisão não foi confirmada com a CVM.
- O mínimo de **1** participante por arquivo é herdado do Informe Mensal: a página da Parte I
  só declara o máximo (1000 tags `PARTICIPANTE`), não um mínimo.
- A premissa de que o `AAAAA` de cada participante iguala `CD_CVM` vem do Informe Mensal e não
  foi lida de forma explícita na página da Parte I.

---

## Exemplo

```python
from layouts_cvm import InformeSemestralInr

doc = dict(
    header=dict(cd_cvm="12345", dt_compt="06/2025", dt_gerac_arq="15/07/2025"),
    participantes=[
        dict(
            cod_partic="12345.123456.654321.1-9",
            entrada_saida=dict(vl_entr=10, vl_saida=20),
            mov_recursos=dict(
                transf_recursos=dict(
                    vl_invest_carteira_haver_nres=0,
                    vl_haver_nres_invest_carteira=0,
                    vl_invest_carteira_adr=0,
                    vl_adr_invest_carteira=0,
                    vl_invest_carteira_estrang_direta=0,
                    vl_estrang_direta_invest_carteira=0,
                )
            ),
            patrim_liq=500,
        )
    ],
)

InformeSemestralInr().export(doc, output_path="informe_semestral_inr_parte1_202506.xml")
```
