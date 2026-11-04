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
    """Another package and nested submodules are not writers (issue 71: ``.c`` now is)."""
    cls_tree = ast.parse(
        "from pkg.a import A\nfrom other.b import B\nfrom .c import C\nfrom pkg.d.e import D\n"
    )

    assert _DICT_GATE["read_top_level_imports"](cls_tree, "pkg") == {"A", "C"}


def test_read_all_names_unions_augmented_assignments() -> None:
    """``__all__ += [...]`` extends the assignment instead of being ignored."""
    cls_tree = ast.parse('__all__ = ["A"]\n__all__ += ["B"]')

    assert _DICT_GATE["read_all_names"](cls_tree) == {"A", "B"}


def test_read_all_names_lets_a_reassignment_replace_the_first() -> None:
    """At runtime the second ``=`` replaces the first, so the gate must not union them."""
    cls_tree = ast.parse('__all__ = ["A"]\n__all__ = ["B"]')

    assert _DICT_GATE["read_all_names"](cls_tree) == {"B"}


def test_read_all_names_reads_a_nested_augmented_assignment() -> None:
    """An ``__all__ +=`` inside ``try`` is read like the imports beside it."""
    cls_tree = ast.parse(
        '__all__ = ["A"]\ntry:\n    __all__ += ["B"]\nexcept ImportError:\n    pass'
    )

    assert _DICT_GATE["read_all_names"](cls_tree) == {"A", "B"}


@pytest.mark.parametrize(
    "str_src",
    ['__all__ = ["A"]\n__all__ += other.__all__', '__all__ = ["A"]\n__all__.extend(["B"])'],
)
def test_read_all_names_rejects_unreadable_mutations(str_src: str) -> None:
    """A non-literal ``+=`` or a method call fails loudly instead of being skipped."""
    with pytest.raises(ValueError, match="__all__"):
        _DICT_GATE["read_all_names"](ast.parse(str_src))


def test_read_top_level_imports_keeps_aliases_relative_and_nested() -> None:
    """The bound alias is recorded; ``from .x`` and ``try``/``if`` imports count."""
    cls_tree = ast.parse(
        "from pkg.a import A as Alias\nfrom .c import C\n"
        "try:\n    from pkg.d import D\nexcept ImportError:\n    pass\n"
        "if True:\n    from .e import E\nfrom .f.g import G\nfrom . import h\n"
    )

    assert _DICT_GATE["read_top_level_imports"](cls_tree, "pkg") == {"Alias", "C", "D", "E"}


def test_read_top_level_imports_skips_private_type_checking_and_function_imports() -> None:
    """``_private`` modules, ``TYPE_CHECKING`` blocks and function bodies are not writers."""
    cls_tree = ast.parse(
        "from ._version import V\nfrom pkg._internal import I\nfrom .ok import Ok\n"
        "if TYPE_CHECKING:\n    from .typed import T\n"
        "def f():\n    from .lazy import L\n"
    )

    assert _DICT_GATE["read_top_level_imports"](cls_tree, "pkg") == {"Ok"}


_STR_INIT = 'from pkg.a import A\n__all__ = ["A"]\n'
_STR_README = "| Layout | Writer |\n|---|---|\n| A | `A` |\n"


def _run_gate(
    path_dir: Path, monkeypatch: pytest.MonkeyPatch, str_init: str, str_readme: str
) -> int:
    """Write a fake package and README under ``path_dir`` and run the gate on them."""
    (path_dir / "__init__.py").write_text(str_init, encoding="utf-8")
    (path_dir / "README.md").write_text(str_readme, encoding="utf-8")
    list_argv = [
        "check_readme_layouts",
        "--init",
        str(path_dir / "__init__.py"),
        "--package",
        "pkg",
        "--readme",
        str(path_dir / "README.md"),
    ]
    monkeypatch.setattr("sys.argv", list_argv)
    return _DICT_GATE["main"]()


def test_main_passes_on_a_matching_project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A table that matches the exports exits 0."""
    assert _run_gate(tmp_path, monkeypatch, _STR_INIT, _STR_README) == 0


def test_main_fails_on_a_row_without_backticks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A stale row with a bare writer name exits 1 with the reason on stderr."""
    int_code = _run_gate(tmp_path, monkeypatch, _STR_INIT, _STR_README + "| Old | Gone |\n")

    assert (int_code, "no backticked writer" in capsys.readouterr().err) == (1, True)


def test_main_fails_on_a_syntax_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """An unparsable ``__init__.py`` exits 1 and is named on stderr."""
    int_code = _run_gate(tmp_path, monkeypatch, "def (:\n", _STR_README)

    assert (int_code, "check_readme_layouts" in capsys.readouterr().err) == (1, True)


def test_main_fails_on_a_missing_readme(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A README that does not exist exits 1 on stderr, after ``__init__.py`` read fine."""
    (tmp_path / "__init__.py").write_text(_STR_INIT, encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        [
            "check_readme_layouts",
            "--init",
            str(tmp_path / "__init__.py"),
            "--package",
            "pkg",
            "--readme",
            str(tmp_path / "absent.md"),
        ],
    )
    int_code = _DICT_GATE["main"]()

    assert (int_code, "absent.md" in capsys.readouterr().err) == (1, True)


def test_main_fails_with_zero_writers_on_stderr(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The zero-writer refusal exits 1 on stderr, not stdout."""
    int_code = _run_gate(tmp_path, monkeypatch, "__all__ = []\n", _STR_README)

    assert (int_code, "ZERO writers" in capsys.readouterr().err) == (1, True)
