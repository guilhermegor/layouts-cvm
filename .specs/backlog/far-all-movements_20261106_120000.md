# FAR opt-in check: every Table A movement code is used (#101)

Source of truth: CVM `PadraoXMLFAR.asp`; origin #99.

- [x] Keyword-only `require_all_movements` flag on `DemonstrativoFar.export`, default off.
- [x] Check runs on the built document, after `coerce_document`, not in a validator.
- [x] Required set derived from `_TABLE_A`, never restated.
- [x] `ValueError` names the fund CNPJ and the missing codes, ascending.
- [x] Tests: flag off, flag on with all 29 codes, rejection message, required set equals `_TABLE_A`.
- [x] Docs: `docs/demonstrativo_far.md` updated.
