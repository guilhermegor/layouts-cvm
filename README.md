<!-- readme-archetype: library -->
# layouts-cvm

<p align="center"><img src="https://raw.githubusercontent.com/guilhermegor/layouts-cvm/main/assets/cvm-logo.png" width="200" alt="CVM emblem"></p>

[![Project Status: Active](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![PyPI Version](https://img.shields.io/pypi/v/layouts-cvm)
[![Snyk Vulnerabilities](https://snyk.io/test/github/guilhermegor/layouts-cvm/badge.svg)](https://snyk.io/test/github/guilhermegor/layouts-cvm)
[![Snyk License](https://snyk.io/advisor/python/layouts-cvm/badge.svg)](https://snyk.io/advisor/python/layouts-cvm)
![PyPI Downloads](https://static.pepy.tech/badge/layouts-cvm)
[![PyPI](https://img.shields.io/pypi/v/layouts-cvm.svg)](https://pypi.org/project/layouts-cvm/)
[![Docs](https://img.shields.io/badge/docs-latest-blue.svg)](https://guilhermegor.github.io/layouts-cvm/)
[![Linting](https://img.shields.io/badge/linting-ruff_|_codespell-blue)](https://github.com/astral-sh/ruff)
[![Mypy](https://img.shields.io/badge/type_checked-mypy-blue)](https://mypy-lang.org)
![Test Coverage](https://raw.githubusercontent.com/guilhermegor/layouts-cvm/main/coverage.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Open Issues](https://img.shields.io/github/issues/guilhermegor/layouts-cvm)
![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-darkgreen.svg)

<!-- slug: overview -->
## Overview

Build, validate and serialise the files a fund sends to CVM, in CVM's own file layouts.

<!-- optional section: delete it when the project has no feature list -->
<!-- slug: features -->
## Features

- Pydantic models for 17 CVM XML layouts, validated before anything is serialised.
- One writer per layout (`export(doc, output_path=None)`), producing windows-1252 XML.
- Byte-identical to the original `filings-cvm` writers, pinned by a golden-file test.
- Runtime dependencies: `pydantic` and `beartype`. No network.

| Layout | Writer | Document |
|---|---|---|
| Atualização do Cadastro de Ativos | `CadastroAtivos` | `CadastroAtivosDocument` |
| CDA V4 | `Cda` | `CdaDocument` |
| CDA V3 | `CdaV3` | `CdaV3Document` |
| Extrato das Informações sobre o Fundo V3 | `Extrato` | `ExtratoDocument` |
| Informe de Fundo 157 | `InfFundo157` | `InfFundo157Document` |
| Informe Mensal FIDC (ICVM 576) | `InfMensalFidc` | `InfMensalFidcDocument` |
| Informe Diário V4 | `InformeDiario` | `InformeDiarioDocument` |
| Informe Diário V3 | `InformeDiarioV3` | `InformeDiarioV3Document` |
| Informe de Portabilidade | `InformePortabilidade` | `InformePortabilidadeDocument` |
| Informe Quadrimestral V2 | `InformeQuadrimestral` | `InformeQuadrimestralDocument` |
| Informe Trimestral V1 | `InformeTrimestralV1` | `InformeTrimestralV1Document` |
| Informe Mensal de Investidor Não Residente | `InrMensal` | `InrMensalDocument` |
| Lâmina de Fundos V3 | `Lamina` | `LaminaDocument` |
| Lâmina de Fundos V2 | `LaminaV2` | `LaminaV2Document` |
| Perfil Mensal V4 | `PerfilMensal` | `PerfilMensalDocument` |
| Perfil Mensal (original) | `PerfilMensalOriginal` | `PerfilMensalOriginalDocument` |
| Perfil Mensal V3 | `PerfilMensalV3` | `PerfilMensalV3Document` |

<!-- slug: documentation -->
## Documentation

The documentation site lives at https://guilhermegor.github.io/layouts-cvm/. Serve it locally with `bash bin/poe_exec.sh docs_serve`.

<!-- slug: getting-started -->
## Getting Started

Python 3.10+ is the only prerequisite; `bin/venv.sh` installs [Poetry](https://python-poetry.org/) when it is missing.

<!-- slug: install -->
### Install

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
from layouts_cvm import InformeDiario, InformeDiarioDocument

doc = InformeDiarioDocument.model_validate(dict_payload)
xml = InformeDiario().export(doc)                      # returns the XML text
InformeDiario().export(doc, "informe_diario.xml")      # or writes it, atomically
```

Each layout has its own page under the Layouts section of the documentation.

<!-- slug: project-structure -->
## Project Structure

```text
layouts-cvm/
├── .github/        workflows, CODEOWNERS, PR template
├── .specs/         feature specs and backlog trackers
├── bin/            gate scripts and helpers
├── docs/           published documentation
├── src/            application code
├── tests/
│   ├── unit/
│   └── integration/
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
under `_internal/` is private.

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
