# **API Reference**

Public interface for this library.

> **See also:** [Usage](../usage.md) · [Examples](../examples.md)

---

## The public surface

The public API is what `layouts_cvm.__all__` lists: `__version__`, and one writer class per CVM
layout. The [layout pages](../cadastro_ativos.md) document each writer's fields.

```python
from layouts_cvm import InformeDiario, __version__
```

Everything under `layouts_cvm._internal` is private, the document models included. It ships in the
wheel so that imports resolve, and it can change in any release.

### `Writer().export(doc, output_path=None)`

| Argument | Meaning |
|----------|---------|
| `doc` | A mapping with the layout's fields. It is validated before anything is serialised. |
| `output_path` | Where to write the file. When omitted, the text is returned instead. |

It returns the file's text as `str`, or `None` once it has written to `output_path`. XML layouts
are windows-1252; `Cofi4010` and `Cofi4016` write ASCII fixed-width `.cvm` records. `DemonstrativoFar.export`
also takes the keyword-only `require_all_movements`, off by default; when on, an incomplete fund
raises `ValueError`.

An invalid document raises `pydantic.ValidationError`.

---

## The 1.x guarantee

Versions follow [semantic versioning](https://semver.org/) since 1.0.0. Within 1.x:

- A name in `__all__` is not removed or renamed, and `export` keeps its signature.
- A new version of a CVM layout ships as a new writer, and the older writer stays.
- A document a writer accepts is not refused later, unless CVM's own rules require it. That case is
  called out in the release notes.
- The exception types above do not change. The wording of error messages can.

A change that breaks any of these is a 2.0.
