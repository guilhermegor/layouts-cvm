"""The Usage example shown in the README and docs/usage.md must actually run."""

from pathlib import Path
import re

import pytest


_PATH_ROOT = Path(__file__).parents[2]
_RE_PYTHON_BLOCK = re.compile(r"```python\n(.*?)```", re.DOTALL)
_LIST_DOCS = [("README.md", "### Usage"), ("docs/usage.md", "## Basic usage")]


def _read_usage_block(path_doc: Path, str_heading: str) -> str:
    """Return the first Python block after ``str_heading`` in a markdown file."""
    str_text = path_doc.read_text(encoding="utf-8")
    return _RE_PYTHON_BLOCK.search(str_text, str_text.index(str_heading)).group(1)


@pytest.fixture(params=_LIST_DOCS, ids=[str_doc for str_doc, _ in _LIST_DOCS])
def dict_namespace(
    request: pytest.FixtureRequest, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> dict[str, object]:
    """Run the documented snippet in a scratch directory and return its namespace."""
    str_doc, str_heading = request.param
    str_code = _read_usage_block(_PATH_ROOT / str_doc, str_heading)
    monkeypatch.chdir(tmp_path)
    dict_ns: dict[str, object] = {}
    exec(compile(str_code, str_doc, "exec"), dict_ns)  # noqa: S102
    return dict_ns


def test_usage_example_returns_xml_text(dict_namespace: dict[str, object]) -> None:
    """The snippet's ``xml`` is an XML document."""
    assert str(dict_namespace["xml"]).lstrip().startswith("<?xml")


def test_usage_example_writes_the_file(dict_namespace: dict[str, object], tmp_path: Path) -> None:
    """The snippet's second call writes a non-empty ``informe_diario.xml``."""
    assert (tmp_path / "informe_diario.xml").stat().st_size > 0
