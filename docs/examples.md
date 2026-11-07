# **Exemplos**

Trechos autônomos, orientados a tarefas, para usos comuns desta biblioteca. Cada receita se
basta: copie e ajuste. `tests/unit/test_docs_examples.py` executa todos os trechos desta página.

> **Veja também:** [Uso](usage.md) para o básico · [Referência da API](api/index.md) para cada
> símbolo público.

---

## Receita: gravar um arquivo de envio { #recipe-write-a-submission-file }

Passe `output_path` para gravar o arquivo. O writer retorna `None`, e o arquivo sai em
windows-1252, como a CVM espera.

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

## Receita: recusar um documento inválido antes que chegue à CVM { #recipe-refuse-a-bad-document-before-it-reaches-cvm }

A validação roda antes de qualquer serialização, então um valor inválido levanta uma exceção e
nenhum arquivo é gravado. Aqui, o cabeçalho cita um dia que não existe.

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
    print(exc.error_count(), "problema(s) no documento")

assert not Path("refused.xml").exists()
```
