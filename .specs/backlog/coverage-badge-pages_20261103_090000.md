# Publish the coverage badge from main (#44)

`coverage.svg` was committed once and showed `n/a` forever. CI on `main` now builds it and
pushes it to the `gh-pages` root; the README points at the Pages URL.

- [x] `coverage-badge.yaml`: on push to `main`, generate the badge and commit only `coverage.svg` to the `gh-pages` root (mike's `versions.json` and version folders untouched).
- [x] Content guard in that job: `check_coverage_badge.py --svg` fails the job when the text is not a percentage.
- [x] README badge points at the Pages URL; tracked `coverage.svg` deleted and gitignored.
- [x] `test_cov.sh` and the manual `coverage-badge` hook write to `htmlcov/`, not a tracked file.
- [x] Structural guard `check_coverage_badge.py` in pre-commit and `tests.yaml`, with should-fail tests.
- [x] genbadge is py3.11+ once #45 lands: the publish job runs on one leg (ubuntu, 3.12); `test_cov.sh` (also the manual hook) skips only the badge with a printed warning when genbadge is not importable.
- [x] Review follow-ups (PR #49): gate tests scrub `GIT_*` per test via an autouse fixture; a missing `README.md` gets its own finding.
- [ ] After merge: confirm the Pages URL serves an SVG whose text is a percentage, not `n/a`.
- [ ] `.gitattributes` still carries a `coverage.svg linguist-generated` line; harmless, drop it in a follow-up.
