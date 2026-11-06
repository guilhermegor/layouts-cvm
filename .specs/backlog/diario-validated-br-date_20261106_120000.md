# informe_diario dates through validated_br_date (#103)

- [x] Replace the private `_DATE_BR_RE` and inline `strptime` in `informe_diario.py` and `informe_diario_v1.py`.
- [x] Test that each schema refuses `31/02/2026`, `1/06/2026` and `15/06/2026\n` and accepts `15/06/2026`.
- [x] Note for the 1.0.0 release notes (#95): the date error text is now `expected DD/MM/AAAA, got '<v>'` or `no such calendar day: '<v>'`.

Completed — kept as a record. Closes #103.
