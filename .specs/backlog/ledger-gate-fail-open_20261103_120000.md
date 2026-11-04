# Work ledger — fix/57-ledger-gate-fail-open

- [x] resolve the base from origin/<default> when there is no local main or origin/HEAD
- [x] fail loudly (exit 1, message on stderr) when no base resolves
- [x] tests: origin-only checkout, unresolvable base
- [ ] upstream BlueprintX fix and a LEDGER_BASE_REF escape hatch for remote-less repos whose trunk is not main/master — follow-up (pr_gate.py was fixed in #76)
