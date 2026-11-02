# Make the submission-writer import PR green (issue 20)

- [x] Allowlist `passiv` in `.codespellrc` and drop inline codespell ignores
- [x] Repair broken doc links so `mkdocs build --strict` passes (bar `incidents.md`, from PR 23)
- [x] Decorate schema helper functions with `@type_checker`
- [x] Fix mypy errors in `perfil_mensal`, `cda`, `extrato`, `lamina`
- [x] Take the one-assert fixes for `test_review_threads_gate` and `test_typing` from PR 23
- [ ] Bring the submission test files under the complexity and one-assert caps
- [ ] Merge `main` once PR 23 lands and re-run the hooks
