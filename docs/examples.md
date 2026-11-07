# **Examples**

Task-oriented, self-contained snippets for common uses of this library. Each recipe stands
alone — copy it and adjust. `tests/unit/test_docs_examples.py` runs every snippet on this page.

> **See also:** [Usage](usage.md) for the basics · [API Reference](api/index.md) for every public
> symbol.

---

## Recipe: write a submission file

Pass `output_path` to write the file. The writer returns `None`, and the file is windows-1252,
as CVM expects.

```python
from pathlib import Path

from layouts_cvm import InformeDiario

dict_row = {
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
dict_payload = {
    "header": {"dt_compt": "15/01/2025", "dt_gerac_arq": "15/01/2025"},
    "informs": [dict_row],
}

InformeDiario().export(dict_payload, "informe_diario.xml")
assert Path("informe_diario.xml").read_bytes().startswith(b"<?xml")
```

## Recipe: refuse a bad document before it reaches CVM

Validation runs before anything is serialised, so a bad value raises and no file is written.
Here the header names a day that does not exist.

```python
from pathlib import Path

from pydantic import ValidationError

from layouts_cvm import InformeDiario

dict_row = {
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
dict_payload = {
    "header": {"dt_compt": "31/02/2025", "dt_gerac_arq": "15/01/2025"},
    "informs": [dict_row],
}

try:
    InformeDiario().export(dict_payload, "refused.xml")
except ValidationError as exc:
    print(exc.error_count(), "problem(s) in the document")

assert not Path("refused.xml").exists()
```
