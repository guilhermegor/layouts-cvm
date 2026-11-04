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


def test_find_order_problems_accepts_a_sorted_list_with_leading_names() -> None:
    """Leading names are exempt; the rest must be sorted."""
    assert _DICT_GATE["find_order_problems"]("x", ["main", "a", "b"], ("main",)) == []


def test_find_order_problems_names_the_first_misplaced_key() -> None:
    """An out-of-order list is reported with the key that broke the order."""
    list_problems = _DICT_GATE["find_order_problems"]("x", ["a", "c", "b"])

    assert "first misplaced: 'c'" in list_problems[0]


def test_read_nav_modules_reads_stems_until_the_section_ends(tmp_path: Path) -> None:
    """Only the ``Layouts`` entries are read, in file order."""
    path_yml = tmp_path / "mkdocs.yml"
    path_yml.write_text(
        'nav:\n  - Layouts:\n      - "B": b.md\n      - "A": a.md\n  - API:\n      - X: x.md\n',
        encoding="utf-8",
    )

    assert _DICT_GATE["read_nav_modules"](path_yml) == ["b", "a"]
