# Perfil Mensal private base (#83)

Deferred from the review of the ICVM 739 writer (#72): `PerfilMensal739` subclassed
`PerfilMensal` and hid a narrower `export` behind `# type: ignore[override]`.

- [x] `_BasePerfilMensal` in `_base_perfil_mensal.py` holds the shared XML builder; not in `__all__`.
- [x] `PerfilMensal` and `PerfilMensal739` both extend it, each with its own typed `export`.
- [x] The `# type: ignore[override]` is removed.
- [x] Rendered XML of V4, V3 and 739 is byte-identical, pinned by the submission tests.
- [x] No docs page names the class hierarchy, so `docs/` is unchanged.
