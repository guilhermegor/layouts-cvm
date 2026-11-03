"""The README gate reads only the layout table, never another table's second column."""

from pathlib import Path
import runpy


_PATH_GATE = Path(__file__).parents[2] / "bin" / "check_readme_layouts.py"


def test_read_readme_writers_ignores_other_tables(tmp_path: Path) -> None:
    """A writer named in a different table must not count as a layout row."""
    path_readme = tmp_path / "README.md"
    path_readme.write_text(
        "| Layout | Writer | Spec |\n|---|---|---|\n| A | `Alpha` | x |\n\n"
        "| Other | Name |\n|---|---|\n| B | `Beta` |\n",
        encoding="utf-8",
    )
    dict_gate = runpy.run_path(str(_PATH_GATE))
    assert dict_gate["read_readme_writers"](path_readme) == {"Alpha"}
