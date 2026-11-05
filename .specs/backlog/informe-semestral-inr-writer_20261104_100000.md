# Informe Semestral INR Part I writer (#14)

Source of truth: CVM `PadraoXMLInfoSemestralINRParte1.asp`, diffed against the monthly INR schema.

- [x] Part I models are a frozen copy (none inherits the live monthly ones, PRINCIPLES 1); `APLICACOES` is not a field, so extra=forbid rejects it.
- [x] `InformeSemestralInr.export` builds on the shared `xml_writer` helpers with `COD_DOC` 69.
- [x] Registries: both `__init__.py`, `mkdocs.yml`, README table, docs page.
- [x] Unit tests pin the top-level participant tag order, `COD_DOC`, and the 0, 1000 and 1001 participant bounds and the child order of the header, MOV_RECURSOS and RECURSOS_*_INVEST blocks.
- [x] Part II (`COD_DOC` 70) is written by `InformeSemestralInrParte2` (#88); this PR covers Part I only.
- [ ] Cross-part consistency (same investors and competence in both files) is not checked.
