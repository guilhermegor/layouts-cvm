"""The gate that keeps ``_internal`` names out of a public ``__all__``."""

from pathlib import Path
import runpy
from types import SimpleNamespace

import pytest


_PATH_GATE = Path(__file__).parents[2] / "bin" / "check_public_all_not_internal.py"


def _load_gate(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Run the shipped gate by path, with its sibling ``bin/`` modules importable.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Scopes the ``sys.path`` addition to the test.

    Returns
    -------
    SimpleNamespace
        The gate's module-level names.
    """
    monkeypatch.syspath_prepend(str(_PATH_GATE.parent))
    return SimpleNamespace(**runpy.run_path(str(_PATH_GATE)))


def test_gate_flags_an_internal_name_in_all(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An ``__all__`` that exports a name imported from ``_internal`` is reported."""
    path_init = tmp_path / "__init__.py"
    path_init.write_text(
        "from pkg._internal.config.schemas.x import XDocument\n__all__ = ['XDocument']\n"
    )

    list_problems = _load_gate(monkeypatch).check_package(path_init)

    assert "'XDocument' is exported in __all__" in list_problems[0]


def test_gate_accepts_a_public_only_all(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An ``__all__`` of public names passes."""
    path_init = tmp_path / "__init__.py"
    path_init.write_text("from pkg.writer import Writer\n__all__ = ['Writer']\n")

    assert _load_gate(monkeypatch).check_package(path_init) == []
