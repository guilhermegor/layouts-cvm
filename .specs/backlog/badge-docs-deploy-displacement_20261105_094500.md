# Badge run displacing a queued docs deploy (#63)

`coverage-badge.yaml` and the `deploy_docs` job in `release-pypi.yaml` shared one
concurrency group, so a newer badge run could displace a docs deploy that was queued.

- [x] `coverage-badge.yaml` uses its own group, `gh-pages-badge`; `deploy_docs` keeps
  `gh-pages-publish`.
- [x] The badge `git push` retries a non-fast-forward rejection, up to 5 attempts, then fails.
- [x] A test pins the two separate groups, and it fails on the old shared group.
- [x] The review follow-ups in `tests/unit/test_coverage_badge_gate.py` are pinned.
- [ ] The retry loop is proven by a real concurrent badge and release run.
