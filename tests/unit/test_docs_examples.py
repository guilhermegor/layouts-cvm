"""Every recipe in docs/examples.md must actually run."""

from pathlib import Path
import re

import pytest


_PATH_EXAMPLES = Path(__file__).parents[2] / "docs" / "examples.md"
_RE_PYTHON_BLOCK = re.compile(r"```python\n(.*?)```", re.DOTALL)
_LIST_BLOCKS = _RE_PYTHON_BLOCK.findall(_PATH_EXAMPLES.read_text(encoding="utf-8"))


def test_examples_page_has_recipes() -> None:
    """The parametrised test below cannot pass vacuously on an empty page."""
    assert _LIST_BLOCKS


@pytest.mark.parametrize("str_code", _LIST_BLOCKS)
def test_recipe_runs(str_code: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A recipe runs clean from a scratch directory, its own asserts included."""
    # one-assert-ok: the recipe carries its own asserts, and any exception fails the test
    monkeypatch.chdir(tmp_path)
    exec(compile(str_code, "docs/examples.md", "exec"), {"__name__": "__main__"})  # noqa: S102
