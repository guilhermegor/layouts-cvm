# **Uso**

Exemplos de instalação e uso desta biblioteca.

> **Veja também:** [Referência da API](api/index.md)

---

## Instalação

```bash
pip install layouts-cvm
```

Ou com o Poetry:

```bash
poetry add layouts-cvm
```

---

## Uso básico

Cada layout tem um writer. Ele recebe um dict simples, valida-o contra o layout e retorna o
texto XML ou grava o arquivo de forma atômica. Nomes de campos, escalas e cardinalidades vêm do
[catálogo da CVM](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadroesXML.asp), não desta página.

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

## Executando os testes

```bash
poe unit_tests         # apenas testes unitários
poe integration_tests  # apenas testes de integração
poe test_cov           # testes unitários + relatório de cobertura + badge
```

---

## Lint e formatação

```bash
poe lint          # ruff check + ruff format + codespell + pydocstyle
```

---

## Publicando no PyPI

Dois workflows do GitHub Actions cuidam das releases (presentes quando o repositório tem um remote no GitHub):

- **`release-test-pypi.yaml`** — publica primeiro no [Test PyPI](https://test.pypi.org).
- **`release-pypi.yaml`** — publica no [PyPI](https://pypi.org) e cria uma GitHub Release.

Dispare qualquer um deles pela aba **Actions** (`workflow_dispatch`), informando a versão.
Ambos exigem que a nova versão seja maior que a última publicada, fazem o build com o Poetry e
publicam por OIDC trusted publishing, portanto nenhum token secreto é necessário.

Configure uma vez, em cada índice (pypi.org e test.pypi.org), um pending publisher:

- PyPI: workflow `release-pypi.yaml`, ambiente `release-pypi`.
- Test PyPI: workflow `release-test-pypi.yaml`, ambiente `release-test-pypi`.

Depois que a primeira execução de `release-pypi.yaml` criar a branch `gh-pages`, execute
`poe enable_pages` uma vez para servir a documentação.
