# Ship py.typed and stable package metadata before 1.0.0 (#94)

Consumers' type checkers ignore a package without the PEP 561 marker, and the PyPI classifiers
must match the Python versions CI actually tests.

- [x] `src/layouts_cvm/py.typed` ships in the built wheel, pinned by a unit test.
- [x] One `Programming Language :: Python :: 3.X` classifier per version in the `tests.yaml` matrix, pinned by a unit test that parses the YAML.
- [x] `Development Status :: 5 - Production/Stable` replaces `3 - Alpha`.
- [x] README Python badge and prerequisites line say 3.11-3.14.
- [x] The published wheel METADATA, not pyproject.toml, is what the classifier test reads; classifiers are static in `[project]` so Poetry stops adding a 3.15 classifier from `python = ">=3.11,<4.0"`.
