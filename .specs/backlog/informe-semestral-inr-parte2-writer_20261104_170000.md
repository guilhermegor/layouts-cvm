# Informe Semestral INR Part II writer (#14)

Source of truth: CVM `PadraoXMLInfoSemestralINRParte2.aspx` (served as windows-1252; read it with
that decoding, not UTF-8).

- [x] Models are the standard's own (`urn:cda` layout, `COD_DOC` 70); only CDA field aliases are
  shared, no model or validator is inherited.
- [x] Writer is the shared recursive walk; CPF/CNPJ leading zeros are dropped at the edge.
- [x] Rules: block application types, Table A, Table B, Tables D, G and H, `NOCION_SWAP`, fixing
  and rating conditionals.
- [x] Registries: both `__init__.py`, `mkdocs.yml`, README table, docs page.
- [x] Unit tests pin tag order, scales, bounds and rejections.
- [ ] Cross-part consistency (same participants and competence in Parts I and II) is not checked.
- [ ] `COD_SWAP` is checked for shape only; Table E is not enumerated (its first row has no code).
- [ ] The visible Table A and the commented-out old one disagree on type 200; the visible one is
  followed.
