# One MM/AAAA competence check across every schema (#98)

- [x] Route every MM/AAAA competence field through `validated_competence` (cda, perfil_mensal, perfil_mensal_739, informe_art12_res33, informe_portabilidade).
- [x] Reject year `0000` in the one shared grammar.
- [x] Share the DD/MM/AAAA shape check as `validated_br_date`.
- [x] Tests: every affected schema rejects `13/2026`, `00/2026`, `01/0000` and accepts `01/2026`, `12/2026`.
- [ ] PR merged.
