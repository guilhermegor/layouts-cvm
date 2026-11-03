"""The README gate's parse paths: the ``__all__`` shape and the import's package."""

import ast
from pathlib import Path
import runpy

import pytest


_DICT_GATE = runpy.run_path(str(Path(__file__).parents[2] / "bin" / "check_readme_layouts.py"))


def test_read_all_names_reads_an_annotated_literal_list() -> None:
    """An annotated top-level ``__all__`` list of literals is read."""
    cls_tree = ast.parse('__all__: list[str] = ["A", "B"]')

    assert _DICT_GATE["read_all_names"](cls_tree) == {"A", "B"}


@pytest.mark.parametrize(
    "str_src",
    ['__all__ = ["A"] + ["B"]', '__all__ = ["A", name]', "x = 1"],
)
def test_read_all_names_rejects_any_other_shape(str_src: str) -> None:
    """A computed, non-literal or missing ``__all__`` fails instead of guessing."""
    with pytest.raises(ValueError, match="__all__"):
        _DICT_GATE["read_all_names"](ast.parse(str_src))


def test_read_top_level_imports_keeps_only_absolute_imports_of_the_package() -> None:
    """Another package and relative imports are not writers."""
    cls_tree = ast.parse(
        "from pkg.a import A\nfrom other.b import B\nfrom .c import C\nfrom pkg.d.e import D\n"
    )

    assert _DICT_GATE["read_top_level_imports"](cls_tree, "pkg") == {"A"}
