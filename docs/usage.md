# **Usage**

Examples for installing and using this library.

> **See also:** [API Reference](api/index.md)

---

## Installation

```bash
pip install layouts-cvm
```

Or with Poetry:

```bash
poetry add layouts-cvm
```

---

## Basic usage

Each layout has one writer. It takes a plain dict, validates it against the layout, and
returns the XML text or writes it atomically. The field names, scales and cardinalities
come from the [CVM catalog](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadroesXML.asp), not from this page.

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

xml = InformeDiario().export(dict_payload)
InformeDiario().export(dict_payload, "informe_diario.xml")
```

---

## Running tests

```bash
poe unit_tests         # unit tests only
poe integration_tests  # integration tests only
poe test_cov           # unit tests + coverage report + badge
```

---

## Linting and formatting

```bash
poe lint          # ruff check + ruff format + codespell + pydocstyle
```

---

## Publishing to PyPI

Two GitHub Actions workflows handle releases (present when the repo has a GitHub remote):

- **`release-test-pypi.yaml`** — publish to [Test PyPI](https://test.pypi.org) first.
- **`release-pypi.yaml`** — publish to [PyPI](https://pypi.org) and cut a GitHub release.

Trigger either from the **Actions** tab (`workflow_dispatch`) with the version to release.
Both gate on the new version being greater than the latest already published, build with
Poetry, and publish through OIDC trusted publishing, so no token secrets are needed.

Configure once, on each index (pypi.org and test.pypi.org), a pending publisher:

- PyPI: workflow `release-pypi.yaml`, environment `release-pypi`.
- Test PyPI: workflow `release-test-pypi.yaml`, environment `release-test-pypi`.

After the first `release-pypi.yaml` run creates the `gh-pages` branch, run `poe enable_pages`
once to serve the docs.
