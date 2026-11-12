<!-- readme-archetype: library -->
# layouts-cvm

<p align="center"><img src="https://raw.githubusercontent.com/guilhermegor/layouts-cvm/main/assets/cvm-logo.png" width="200" alt="Emblema da CVM"></p>

[![Project Status: Active](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)
[![Snyk Vulnerabilities](https://snyk.io/test/github/guilhermegor/layouts-cvm/badge.svg)](https://snyk.io/test/github/guilhermegor/layouts-cvm)
![PyPI Downloads](https://static.pepy.tech/badge/layouts-cvm)
[![PyPI](https://img.shields.io/pypi/v/layouts-cvm.svg)](https://pypi.org/project/layouts-cvm/)
[![Docs](https://img.shields.io/badge/docs-latest-blue.svg)](https://guilhermegor.github.io/layouts-cvm/)
[![Linting](https://img.shields.io/badge/linting-ruff_|_codespell-blue)](https://github.com/astral-sh/ruff)
[![Mypy](https://img.shields.io/badge/type_checked-mypy-blue)](https://mypy-lang.org)
![Test Coverage](https://guilhermegor.github.io/layouts-cvm/coverage.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Open Issues](https://img.shields.io/github/issues/guilhermegor/layouts-cvm)
![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-darkgreen.svg)

<!-- slug: overview -->
## Visão geral

Monte, valide e serialize os arquivos que um fundo envia à CVM, nos layouts da própria CVM.

> **Fonte da verdade.** Nomes de campos, escalas decimais e cardinalidades vêm do
> [catálogo oficial de padrões XML da CVM](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadroesXML.asp), não desta documentação. Se os dois divergirem,
> vale o catálogo; por favor, abra uma issue.

- **Direção: apenas envio** (montar e depois enviar à CVM). Ler arquivos da CVM está fora do
  escopo hoje.
- **Cobertura:** os layouts da tabela abaixo estão implementados. Os demais são acompanhados em
  [issues de writer](https://github.com/guilhermegor/layouts-cvm/issues?q=is%3Aissue+is%3Aopen+writer),
  abertas: estão planejados, não esquecidos.
- **Decimais são truncados, nunca arredondados** (`ROUND_DOWN`): um valor com mais dígitos que a
  escala do layout perde o excesso, de modo que um número informado nunca cresce em magnitude.
- **Os dígitos verificadores de CNPJ e CPF são validados** antes de qualquer serialização.

<!-- optional section: delete it when the project has no feature list -->
<!-- slug: features -->
## Funcionalidades

- Modelos Pydantic para cada layout XML da CVM listado abaixo, validados antes de qualquer serialização.
- Um writer por layout (`export(doc, output_path=None)`), que produz XML em windows-1252 (a exceção é `Cofi4016`: registros `.cvm` em ASCII de largura fixa).
- Saída idêntica byte a byte à dos writers originais do `opendata-cvm` (antes `filings-cvm`), garantida por um teste de golden file.
- Dependências de execução: `pydantic` e `beartype`. Sem acesso à rede.

| Layout | Writer | Modelo do documento (privado) | Especificação |
|---|---|---|---|
| Atualização do Cadastro de Ativos | `CadastroAtivos` | `CadastroAtivosDocument` | [PadraoXMLAtivos](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLAtivos.asp) |
| CDA V4 | `Cda` | `CdaDocument` | [PadraoXMLCDANetV4](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLCDANetV4.aspx) |
| CDA V2 | `CdaV2` | `CdaV2Document` | [PadraoXMLCDANet](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLCDANet.aspx) |
| CDA V3 | `CdaV3` | `CdaV3Document` | [PadraoXMLCDANetV3](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLCDANetV3.aspx) |
| COFI 4010 (Balancete, largura fixa) | `Cofi4010` | `Cofi4010Document` | [PadraoCOFI](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoCOFI.aspx) |
| COFI 4016 (Balanço, largura fixa) | `Cofi4016` | `Cofi4016Document` | [PadraoCOFI](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoCOFI.aspx) |
| Demonstrativo de Fontes e Aplicações de Recursos (FAR) | `DemonstrativoFar` | `DemonstrativoFarDocument` | [PadraoXMLFAR](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLFAR.asp) |
| Extrato das Informações sobre o Fundo V3 | `Extrato` | `ExtratoDocument` | [PadraoXMLInfExtratoV3](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfExtratoV3.asp) |
| Extrato das Informações sobre o Fundo V2 | `ExtratoV2` | `ExtratoV2Document` | [PadraoXMLInfExtratoV2](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfExtratoV2.asp) |
| Informe de Fundo 157 | `InfFundo157` | `InfFundo157Document` | [PadraoXMLInf157](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInf157.asp) |
| Informe Mensal FIDC (ICVM 576) | `InfMensalFidc` | `InfMensalFidcDocument` | [PadraoXMLMensalFIDC576](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLMensalFIDC576.asp) |
| Informe Mensal FIDC (ICVM 489) | `InfMensalFidc489` | `InfMensalFidc489Document` | [PadraoXMLMensalFIDC489](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLMensalFIDC489.asp) |
| Informe Anual de Auditor | `InformeAnualAuditor` | `InformeAnualAuditorDocument` | [PadraoXMLAuditorAnual](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLAuditorAnual.asp) |
| Informe Art. 12 Res. CVM 33 | `InformeArt12Res33` | `InformeArt12Res33Document` | [PadraoXMLPrest](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLPrest.asp) |
| Informe Diário V4 | `InformeDiario` | `InformeDiarioDocument` | [PadraoXMLInfoDiarioNetV4](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoDiarioNetV4.asp) |
| Informe Diário V1 | `InformeDiarioV1` | `InformeDiarioV1Document` | [PadraoXMLInfoDiarioNet](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoDiarioNet.asp) |
| Informe Diário V2 | `InformeDiarioV2` | `InformeDiarioV2Document` | [PadraoXMLInfoDiarioNet739](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoDiarioNet739.asp) |
| Informe Diário V3 | `InformeDiarioV3` | `InformeDiarioV3Document` | [PadraoXMLInfoDiarioNetV3](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoDiarioNetV3.asp) |
| Informe de Portabilidade | `InformePortabilidade` | `InformePortabilidadeDocument` | [PadraoXMLInfoPortabilidade](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoPortabilidade.asp) |
| Informe Quadrimestral V2 | `InformeQuadrimestral` | `InformeQuadrimestralDocument` | [PadraoXMLInfoTrimV2](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoTrimV2.asp) |
| Informe Semestral de Investidor Não Residente — Parte I | `InformeSemestralInr` | `InformeSemestralInrDocument` | [PadraoXMLInfoSemestralINRParte1](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoSemestralINRParte1.asp) |
| Informe Semestral de Investidor Não Residente — Parte II | `InformeSemestralInrParte2` | `InformeSemestralInrParte2Document` | [PadraoXMLInfoSemestralINRParte2](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoSemestralINRParte2.aspx) |
| Informe Sintético (FCCE, FITVM, FIC-FITVM, Outros) | `InformeSintetico` | `InformeSinteticoFcceDocument`, `InformeSinteticoFitvmDocument`, `InformeSinteticoFicDocument`, `InformeSinteticoOutrosDocument` | [FCCE](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLSintFCCE.asp), [FITVM](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLSintFITVM.asp), [FIC-FITVM](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLSintFIC.asp), [Outros](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLSintOutros.asp) |
| Informe Trimestral V1 | `InformeTrimestralV1` | `InformeTrimestralV1Document` | [PadraoXMLInfoTrim](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoTrim.asp) |
| Informe Mensal de Investidor Não Residente | `InrMensal` | `InrMensalDocument` | [PadraoXMLInfoMensalINR](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoMensalINR.asp) |
| Lâmina de Fundos V3 | `Lamina` | `LaminaDocument` | [PadraoXMLLaminaV3](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLLaminaV3.asp) |
| Lâmina de Fundos V1 | `LaminaV1` | `LaminaV1Document` | [PadraoXMLLamina](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLLamina.asp) |
| Lâmina de Fundos V2 | `LaminaV2` | `LaminaV2Document` | [PadraoXMLLaminaV2](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLLaminaV2.asp) |
| Perfil Mensal V4 | `PerfilMensal` | `PerfilMensalDocument` | [PadraoXMLPerfilV4](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLPerfilV4.asp) |
| Perfil Mensal ICVM 739 | `PerfilMensal739` | `PerfilMensal739Document` | [PadraoXMLPerfil739](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLPerfil739.asp) |
| Perfil Mensal (original) | `PerfilMensalOriginal` | `PerfilMensalOriginalDocument` | [PadraoXMLPerfil](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLPerfil.asp) |
| Perfil Mensal V3 | `PerfilMensalV3` | `PerfilMensalV3Document` | [PadraoXMLPerfilV3](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLPerfilV3.asp) |

<!-- slug: documentation -->
## Documentação

O site da documentação fica em https://guilhermegor.github.io/layouts-cvm/. Para servi-lo localmente, use `bash bin/poe_exec.sh docs_serve`.

<!-- slug: getting-started -->
## Primeiros passos

Python 3.11-3.14 é o único pré-requisito; `bin/venv.sh` instala o [Poetry](https://python-poetry.org/) quando ele não existe.

<!-- slug: install -->
### Instalação

```bash
pip install layouts-cvm
```

Ou a partir do código-fonte:

```bash
git clone https://github.com/guilhermegor/layouts-cvm.git
cd layouts-cvm
bash bin/venv.sh
bash bin/poe_exec.sh init
```

O `poe` fica dentro do virtualenv, então `bin/venv.sh` o cria primeiro; `bin/poe_exec.sh` executa
`poe init` em seguida, sem ativar nada. Com o virtualenv criado, `poetry run poe init` faz o
mesmo.

<!-- slug: usage -->
### Uso

```python
from layouts_cvm import InformeDiario

dict_payload = {
    "header": {"dt_compt": "15/01/2025", "dt_gerac_arq": "15/01/2025"},
    "informs": [
        {
            "cnpj_fdo": "11222333000181",
            "data_prox_pl": "16/01/2025",
            "vl_total": "0",
            "vl_quota": "0",
            "patrim_liq": "0",
            "captc_dia": "0",
            "resg_dia": "0",
            "vl_total_sai": "0",
            "vl_total_atv": "0",
            "nr_cotst": 0,
        }
    ],
}

xml = InformeDiario().export(dict_payload)                  # retorna o texto XML
InformeDiario().export(dict_payload, "informe_diario.xml")  # ou grava o arquivo, de forma atômica
```

O payload é composto de dados simples: o writer o valida contra o modelo de documento do layout
antes de serializar. Os modelos de documento são privados (`layouts_cvm._internal`) e não fazem
parte da API pública; a página de cada layout na documentação lista seus campos.

Cada layout tem sua própria página na seção Layouts da documentação.

<!-- slug: project-structure -->
## Estrutura do projeto

```text
layouts-cvm/
├── .github/        workflows, CODEOWNERS, modelo de PR
├── .specs/         specs de funcionalidades e controles de backlog
├── bin/            scripts de gate e utilitários
├── docs/           documentação publicada
├── src/layouts_cvm/
│   ├── <layout>.py um módulo de writer por layout, exportado em __init__.py
│   └── _internal/  privado: config/schemas/ (os modelos de documento), utils/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── golden/     fixture de paridade byte a byte com os writers originais do opendata-cvm
├── pyproject.toml
└── poe_tasks.toml  pontos de entrada do executor de tarefas
```

<!-- slug: development -->
## Desenvolvimento

Depois do bootstrap descrito em Instalação, qualquer tarefa pode ser executada com o script de
bootstrap: `bash bin/poe_exec.sh <task>`; `bash bin/poe_exec.sh` sem tarefa lista todas.

```bash
bash bin/poe_exec.sh unit_tests
bash bin/poe_exec.sh integration_tests
```

Quando o deploy da documentação da primeira release tiver criado a branch `gh-pages`, execute
`bash bin/poe_exec.sh enable_pages` uma vez: enquanto essa branch não existir, `init` não mexe no Pages.

<!-- slug: public-api -->
## API pública

A superfície pública é o que o `__init__.py` do pacote lista em `__all__`; tudo em `_internal/`
é privado. Essa superfície são os writers: os modelos de documento ficam em
`_internal/config/schemas/`, e um writer recebe dados simples (ou um modelo já montado). O gate
`check-public-all-not-internal` falha se `__all__` exportar um nome definido ali.

<!-- slug: publishing -->
## Publicação

As releases saem dos workflows de release em `.github/workflows/`; a tag do git é a versão.

As versões seguem o versionamento semântico desde a 1.0.0. A garantia da 1.x cobre os nomes em
`layouts_cvm.__all__` e a forma de chamar o `export` de cada writer; tudo em
`layouts_cvm._internal` é privado. O texto completo está em
[docs/api/reference.md](docs/api/reference.md).

O caminho da 0.x até a 1.0.0, e o gate de release que o protege, está em
[docs/releasing-1-0-0.md](docs/releasing-1-0-0.md).

<!-- slug: contributing -->
## Contribuindo

Veja [CONTRIBUTING.md](CONTRIBUTING.md) (em inglês) para as regras de branch, commit e revisão.

<!-- slug: license -->
## Licença

Este projeto é licenciado sob a MIT; veja [LICENSE](LICENSE).

<!-- slug: authors -->
## Autores

- Guilherme Rodrigues — [GitHub](https://github.com/guilhermegor) | [LinkedIn](https://www.linkedin.com/in/guilhermegor/)

<!-- slug: useful-links -->
## Links úteis

- [Repositório no GitHub](https://github.com/guilhermegor/layouts-cvm)
- [Rastreador de issues](https://github.com/guilhermegor/layouts-cvm/issues)
- [Documentação](https://guilhermegor.github.io/layouts-cvm/)

---

<sub>Gerado a partir do template lib-minimal via [BlueprintX](https://github.com/guilhermegor/blueprintx).
Biblioteca comunitária e não oficial, sem afiliação com a Comissão de Valores Mobiliários (CVM) nem endosso dela;
o emblema pertence à CVM e não é coberto pela licença MIT deste projeto.</sub>
