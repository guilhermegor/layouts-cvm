# Reject non-existent dates in the Informe Diario schema (#89)

`_DATE_BR_RE` checked only the shape of a date, so a value such as `31/02/2011` passed. PR #62
fixed the same defect for V1 only.

- [x] Both validators share `_validate_date_br`: `fullmatch` on ASCII digits, then `strptime`.
- [x] A failure raises `ValueError`, so Pydantic reports a `ValidationError`.
- [x] Valid dates serialise byte-for-byte unchanged, leap day included.
- [x] The new tests failed on main before the fix.
