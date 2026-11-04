# Work ledger — fix/57-ledger-gate-fail-open

- [x] resolve the base from origin/<default> when there is no local main or origin/HEAD
- [x] fail loudly (exit 1, message on stderr) when no base resolves
- [x] tests: origin-only checkout, unresolvable base
- [ ] other bin/ gates using default_branch()/merge-base (pr_gate.py), and upstream BlueprintX fix — follow-up
