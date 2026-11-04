# Informe Semestral INR Part I writer (#14)

Source of truth: CVM `PadraoXMLInfoSemestralINRParte1.asp`, diffed against the monthly INR schema.

- [x] Part I models are a frozen copy (none inherits the live monthly ones, PRINCIPLES 1); `APLICACOES` is not a field, so extra=forbid rejects it.
- [x] `InformeSemestralInr.export` builds on the shared `xml_writer` helpers with `COD_DOC` 69.
- [x] Registries: both `__init__.py`, `mkdocs.yml`, README table, docs page.
- [x] Unit tests pin the top-level participant tag order, `COD_DOC`, and the 0, 1000 and 1001 participant bounds (header order and optional blocks are not pinned).
- [ ] Part II (`COD_DOC` 70, `PadraoXMLInfoSemestralINRParte2.aspx`) is not implemented here (PR #88). The page is served as windows-1252 and reads fine with that encoding.
- [ ] Cross-part consistency (same investors and competence in both files) is not checked.
