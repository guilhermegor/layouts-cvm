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
    """``__all__ += [...]`` adds to the first assignment instead of being ignored."""
    cls_tree = ast.parse('__all__ = ["A"]\n__all__ += ["B"]')

    assert _DICT_GATE["read_all_names"](cls_tree) == {"A", "B"}


def test_read_top_level_imports_keeps_aliases_relative_and_nested() -> None:
    """The bound alias is recorded; ``from .x`` and ``try``/``if`` imports count."""
    cls_tree = ast.parse(
        "from pkg.a import A as Alias\nfrom .c import C\n"
        "try:\n    from pkg.d import D\nexcept ImportError:\n    pass\n"
        "if True:\n    from .e import E\nfrom .f.g import G\nfrom . import h\n"
    )

    assert _DICT_GATE["read_top_level_imports"](cls_tree, "pkg") == {"Alias", "C", "D", "E"}


_STR_INIT = 'from pkg.a import A\n__all__ = ["A"]\n'
_STR_README = "| Layout | Writer | Document |\n|---|---|---|\n| A | `A` | `ADocument` |\n"


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
    """A stale row with a bare writer name is an error on stderr, not a silent skip."""
    _run_gate(tmp_path, monkeypatch, _STR_INIT, _STR_README + "| Old | Gone | `GoneDocument` |\n")

    assert "no backticked writer" in capsys.readouterr().err


def test_main_exits_one_on_a_syntax_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An unparsable ``__init__.py`` exits 1 instead of raising."""
    assert _run_gate(tmp_path, monkeypatch, "def (:\n", _STR_README) == 1


def test_main_reports_a_syntax_error_on_stderr(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The syntax error is named on stderr."""
    _run_gate(tmp_path, monkeypatch, "def (:\n", _STR_README)

    assert "check_readme_layouts" in capsys.readouterr().err


def test_main_exits_one_on_a_missing_readme(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A missing README exits 1 instead of raising."""
    monkeypatch.setattr(Path, "read_text", _raise_missing)

    assert _run_gate(tmp_path, monkeypatch, _STR_INIT, _STR_README) == 1


def _raise_missing(self: Path, *list_args: object, **dict_kwargs: object) -> str:
    """Stand in for ``Path.read_text`` on a file that does not exist."""
    raise FileNotFoundError(str(self))


def test_main_reports_zero_writers_on_stderr(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The zero-writer refusal goes to stderr, not stdout."""
    _run_gate(tmp_path, monkeypatch, "__all__ = []\n", _STR_README)

    assert "ZERO writers" in capsys.readouterr().err
