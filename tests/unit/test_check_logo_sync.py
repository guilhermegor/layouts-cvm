"""The gate that keeps the README logo and the docs logo the same image."""

from pathlib import Path
import runpy
from types import SimpleNamespace

import pytest


_PATH_GATE = Path(__file__).parents[2] / "bin" / "check_logo_sync.py"
_README = '<img src="https://raw.githubusercontent.com/o/r/main/assets/cvm-logo.png">'
_INDEX = '# t <img src="assets/cvm-logo.png" alt="x">'
_MKDOCS = "theme:\n  logo: assets/cvm-logo.png\n  favicon: assets/cvm-logo.png\n"


def _load_gate() -> SimpleNamespace:
    """Run the shipped gate by path.

    Returns
    -------
    SimpleNamespace
        The gate's module-level names.
    """
    return SimpleNamespace(**runpy.run_path(str(_PATH_GATE)))


@pytest.fixture
def path_repo(tmp_path: Path) -> Path:
    """Build a repo whose README and docs logos are identical.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest-provided scratch directory.

    Returns
    -------
    pathlib.Path
        The repository root.
    """
    (tmp_path / "assets").mkdir()
    (tmp_path / "docs" / "assets").mkdir(parents=True)
    (tmp_path / "assets" / "cvm-logo.png").write_bytes(b"same")
    (tmp_path / "docs" / "assets" / "cvm-logo.png").write_bytes(b"same")
    (tmp_path / "README.md").write_text(_README)
    (tmp_path / "docs" / "index.md").write_text(_INDEX)
    (tmp_path / "mkdocs.yml").write_text(_MKDOCS)
    return tmp_path


def test_gate_passes_when_logos_are_identical(path_repo: Path) -> None:
    """Identical, existing logos report nothing."""
    assert _load_gate().check_logos(path_repo) == []


def test_gate_flags_a_readme_image_mismatch(path_repo: Path) -> None:
    """A README image that differs from the docs image is reported."""
    (path_repo / "assets" / "cvm-logo.png").write_bytes(b"other")

    assert "README.md" in _load_gate().check_logos(path_repo)[0]


def test_gate_flags_a_docs_image_mismatch(path_repo: Path) -> None:
    """A docs image that differs from the README image is reported."""
    (path_repo / "docs" / "assets" / "cvm-logo.png").write_bytes(b"other")

    assert "mkdocs.yml theme.logo" in _load_gate().check_logos(path_repo)[0]


def test_gate_flags_a_missing_file(path_repo: Path) -> None:
    """A referenced logo that does not exist fails, naming the reference."""
    (path_repo / "docs" / "assets" / "cvm-logo.png").unlink()

    assert "docs/index.md: logo file missing" in _load_gate().check_logos(path_repo)[0]
