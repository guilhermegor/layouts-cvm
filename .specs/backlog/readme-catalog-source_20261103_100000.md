# README: CVM catalog as source of truth (#38)

Source of truth: CVM `PadroesXML.asp`.

- [x] Source-of-truth callout in README Overview and `docs/index.md`.
- [x] Spec column in the README layout table (URLs taken from each `docs/<layout>.md`).
- [x] Coverage line (18 implemented, rest tracked as open writer issues).
- [x] Validation guarantees (ROUND_DOWN truncation, CNPJ/CPF check digits) and submission-only direction.
- [x] `pip install layouts-cvm` under Install (0.1.2 is on PyPI).
- [x] Runnable Usage example (dict payload, shape from #47); `docs/usage.md` template placeholders replaced.
- [x] Real Project Structure tree (shows `_internal/config/schemas/`, valid once #47 lands).
- [x] Gate `bin/check_readme_layouts.py`, in pre-commit and `tests.yaml`, with tests for a missing and a stale row.
- [ ] Merge `origin/main` after #47 lands and resolve the README conflict.
