<!-- readme-archetype: library -->
# layouts-cvm

<p align="center"><img src="https://raw.githubusercontent.com/guilhermegor/layouts-cvm/main/assets/cvm-logo.png" width="200" alt="CVM emblem"></p>

[![Project Status: Active](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![PyPI Version](https://img.shields.io/pypi/v/layouts-cvm)
[![Snyk Vulnerabilities](https://snyk.io/test/github/guilhermegor/layouts-cvm/badge.svg)](https://snyk.io/test/github/guilhermegor/layouts-cvm)
[![Snyk License](https://snyk.io/advisor/python/layouts-cvm/badge.svg)](https://snyk.io/advisor/python/layouts-cvm)
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
## Overview

Build, validate and serialise the files a fund sends to CVM, in CVM's own file layouts.

> **Source of truth.** Field names, decimal scales and cardinalities come from the official
> [CVM catalog of XML standards](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadroesXML.asp), not from this documentation. When the two disagree,
> the catalog wins; please open an issue.

- **Direction: submission only** (build, then send to CVM). Reading CVM files back is out of
  scope today.
- **Coverage:** the layouts in the table below are implemented. The rest are tracked as open
  [writer issues](https://github.com/guilhermegor/layouts-cvm/issues?q=is%3Aissue+is%3Aopen+writer),
  so they are planned, not forgotten.
- **Decimals are truncated, never rounded** (`ROUND_DOWN`): a value with more digits than the
  layout's scale loses the excess, so a reported figure is never inflated.
- **CNPJ and CPF check digits are validated** before anything is serialised.

<!-- optional section: delete it when the project has no feature list -->
<!-- slug: features -->
## Features

- Pydantic models for every CVM XML layout listed below, validated before anything is serialised.
- One writer per layout (`export(doc, output_path=None)`), producing windows-1252 XML.
- Byte-identical to the original `filings-cvm` writers, pinned by a golden-file test.
- Runtime dependencies: `pydantic` and `beartype`. No network.

| Layout | Writer | Document model (private) | Spec |
|---|---|---|---|
| Atualização do Cadastro de Ativos | `CadastroAtivos` | `CadastroAtivosDocument` | [PadraoXMLAtivos](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLAtivos.asp) |
| CDA V4 | `Cda` | `CdaDocument` | [PadraoXMLCDANetV4](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLCDANetV4.aspx) |
| CDA V3 | `CdaV3` | `CdaV3Document` | [PadraoXMLCDANetV3](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLCDANetV3.aspx) |
| Extrato das Informações sobre o Fundo V3 | `Extrato` | `ExtratoDocument` | [PadraoXMLInfExtratoV3](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfExtratoV3.asp) |
| Extrato das Informações sobre o Fundo V2 | `ExtratoV2` | `ExtratoV2Document` | [PadraoXMLInfExtratoV2](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfExtratoV2.asp) |
| Informe de Fundo 157 | `InfFundo157` | `InfFundo157Document` | [PadraoXMLInf157](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInf157.asp) |
| Informe Mensal FIDC (ICVM 576) | `InfMensalFidc` | `InfMensalFidcDocument` | [PadraoXMLMensalFIDC576](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLMensalFIDC576.asp) |
| Informe Diário V4 | `InformeDiario` | `InformeDiarioDocument` | [PadraoXMLInfoDiarioNetV4](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoDiarioNetV4.asp) |
| Informe Diário V3 | `InformeDiarioV3` | `InformeDiarioV3Document` | [PadraoXMLInfoDiarioNetV3](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoDiarioNetV3.asp) |
| Informe Diário V2 | `InformeDiarioV2` | `InformeDiarioV2Document` | [PadraoXMLInfoDiarioNet739](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoDiarioNet739.asp) |
| Informe de Portabilidade | `InformePortabilidade` | `InformePortabilidadeDocument` | [PadraoXMLInfoPortabilidade](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoPortabilidade.asp) |
| Informe Quadrimestral V2 | `InformeQuadrimestral` | `InformeQuadrimestralDocument` | [PadraoXMLInfoTrimV2](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoTrimV2.asp) |
| Informe Trimestral V1 | `InformeTrimestralV1` | `InformeTrimestralV1Document` | [PadraoXMLInfoTrim](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoTrim.asp) |
| Informe Mensal de Investidor Não Residente | `InrMensal` | `InrMensalDocument` | [PadraoXMLInfoMensalINR](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoMensalINR.asp) |
| Lâmina de Fundos V3 | `Lamina` | `LaminaDocument` | [PadraoXMLLaminaV3](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLLaminaV3.asp) |
| Lâmina de Fundos V1 | `LaminaV1` | `LaminaV1Document` | [PadraoXMLLamina](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLLamina.asp) |
| Lâmina de Fundos V2 | `LaminaV2` | `LaminaV2Document` | [PadraoXMLLaminaV2](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLLaminaV2.asp) |
| Perfil Mensal V4 | `PerfilMensal` | `PerfilMensalDocument` | [PadraoXMLPerfilV4](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLPerfilV4.asp) |
| Perfil Mensal (original) | `PerfilMensalOriginal` | `PerfilMensalOriginalDocument` | [PadraoXMLPerfil](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLPerfil.asp) |
| Perfil Mensal V3 | `PerfilMensalV3` | `PerfilMensalV3Document` | [PadraoXMLPerfilV3](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLPerfilV3.asp) |

<!-- slug: documentation -->
## Documentation

The documentation site lives at https://guilhermegor.github.io/layouts-cvm/. Serve it locally with `bash bin/poe_exec.sh docs_serve`.

<!-- slug: getting-started -->
## Getting Started

Python 3.11+ is the only prerequisite; `bin/venv.sh` installs [Poetry](https://python-poetry.org/) when it is missing.

<!-- slug: install -->
### Install

```bash
pip install layouts-cvm
```

Or from source:

```bash
git clone https://github.com/guilhermegor/layouts-cvm.git
cd layouts-cvm
bash bin/venv.sh
bash bin/poe_exec.sh init
```

`poe` lives inside the virtualenv, so `bin/venv.sh` creates it first; `bin/poe_exec.sh` then
runs `poe init` without activating anything. Once the virtualenv exists, `poetry run poe init`
does the same.

<!-- slug: usage -->
### Usage

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

xml = InformeDiario().export(dict_payload)                  # returns the XML text
InformeDiario().export(dict_payload, "informe_diario.xml")  # or writes it, atomically
```

The payload is plain data: the writer validates it against the layout's document model
before serialising. The document models are private (`layouts_cvm._internal`) and not part of
the public API; each layout's page in the documentation lists its fields.

Each layout has its own page under the Layouts section of the documentation.

<!-- slug: project-structure -->
## Project Structure

```text
layouts-cvm/
├── .github/        workflows, CODEOWNERS, PR template
├── .specs/         feature specs and backlog trackers
├── bin/            gate scripts and helpers
├── docs/           published documentation
├── src/layouts_cvm/
│   ├── <layout>.py one writer module per layout, exported in __init__.py
│   └── _internal/  private: config/schemas/ (the document models), utils/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── golden/     byte-parity fixture against the original filings-cvm writers
├── pyproject.toml
└── poe_tasks.toml  task runner entry points
```

<!-- slug: development -->
## Development

After the bootstrap under Install, any task can be run with the bootstrap script:
`bash bin/poe_exec.sh <task>`, and `bash bin/poe_exec.sh` with no task lists them.

```bash
bash bin/poe_exec.sh unit_tests
bash bin/poe_exec.sh integration_tests
```

Once the first release's docs deploy has created the `gh-pages` branch, run
`bash bin/poe_exec.sh enable_pages` once: until that branch exists, `init` leaves Pages untouched.

<!-- slug: public-api -->
## Public API

The public surface is whatever the package `__init__.py` lists in `__all__`; everything
under `_internal/` is private. That surface is the writers: the document models live in
`_internal/config/schemas/` and a writer takes plain data (or a built model). The
`check-public-all-not-internal` gate fails if `__all__` ever exports a name defined there.

<!-- slug: publishing -->
## Publishing

Releases go out from the release workflows under `.github/workflows/`; the git tag is the
version.

The path from 0.x to 1.0.0, and the release gate that guards it, is in
[docs/releasing-1-0-0.md](docs/releasing-1-0-0.md).

<!-- slug: contributing -->
## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the branch, commit and review rules.

<!-- slug: license -->
## License

This project is licensed under MIT; see [LICENSE](LICENSE).

<!-- slug: authors -->
## Authors

- Guilherme Rodrigues — [GitHub](https://github.com/guilhermegor) | [LinkedIn](https://www.linkedin.com/in/guilhermegor/)

<!-- slug: useful-links -->
## Useful Links

- [GitHub Repository](https://github.com/guilhermegor/layouts-cvm)
- [Issue Tracker](https://github.com/guilhermegor/layouts-cvm/issues)
- [Documentation](https://guilhermegor.github.io/layouts-cvm/)

---

<sub>Generated from the lib-minimal template via [BlueprintX](https://github.com/guilhermegor/blueprintx).
Unofficial, community library. Not affiliated with or endorsed by the Comissão de Valores Mobiliários (CVM);
the emblem is theirs and is not covered by this project's MIT license.</sub>
