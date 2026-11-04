# Informe Semestral INR Part I writer (#14)

Source of truth: CVM `PadraoXMLInfoSemestralINRParte1.asp`, diffed against the monthly INR schema.

- [x] Part I models extend the monthly INR ones; `APLICACOES` is rejected when set.
- [x] `InformeSemestralInr.export` delegates to `InrMensal().export` with `COD_DOC` 69.
- [x] Registries: both `__init__.py`, `mkdocs.yml`, README table, docs page.
- [x] Unit tests pin tag order, `COD_DOC`, and the 0, 1000 and 1001 participant bounds.
- [ ] Part II (`COD_DOC` 70, `PadraoXMLInfoSemestralINRParte2.aspx`) is not implemented; the page is unreadable.
- [ ] Cross-part consistency (same investors and competence in both files) is not checked.
