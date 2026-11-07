"""Every Python example in README.md, docs/usage.md and docs/examples.md must actually run."""

from pathlib import Path
import re

import pytest


_PATH_ROOT = Path(__file__).parents[2]
_TUPLE_PAGES = ("README.md", "docs/usage.md", "docs/examples.md")
_RE_PYTHON_BLOCK = re.compile(r"```python\n(.*?)```", re.DOTALL)
_LIST_BLOCKS = [
    (str_page, str_code)
    for str_page in _TUPLE_PAGES
    for str_code in _RE_PYTHON_BLOCK.findall((_PATH_ROOT / str_page).read_text(encoding="utf-8"))
]


@pytest.mark.parametrize("str_page", _TUPLE_PAGES)
def test_page_has_examples(str_page: str) -> None:
    """The parametrised test below cannot pass vacuously on a page with no examples."""
    assert any(str_found == str_page for str_found, _ in _LIST_BLOCKS)


@pytest.mark.parametrize(
    ("str_page", "str_code"),
    _LIST_BLOCKS,
    ids=[f"{str_page}#{int_i}" for int_i, (str_page, _) in enumerate(_LIST_BLOCKS)],
)
def test_example_runs(
    str_page: str, str_code: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An example runs clean from a scratch directory, its own asserts included."""
    # one-assert-ok: the example carries its own asserts, and any exception fails the test
    monkeypatch.chdir(tmp_path)
    exec(compile(str_code, str_page, "exec"), {"__name__": "__main__"})  # noqa: S102
