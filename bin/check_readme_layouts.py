"""Fail when the README layout table and the package's writers disagree.

The writers are derived from ``src/layouts_cvm/__init__.py``, never listed twice: a name is a
writer when it is in ``__all__`` AND imported from a top-level submodule of the package
(``from layouts_cvm.cda import Cda``). That excludes ``__version__``, ``main`` and every
schema/model name, so the gate neither depends on nor breaks when the schemas move.

The README side is the first backticked cell of each row of the layout table.
"""

import argparse
import ast
from pathlib import Path
import re
import sys


_SET_NOT_WRITERS = frozenset({"__version__", "main"})
_STR_TABLE_HEADER = "| Layout | Writer |"
_RE_ROW = re.compile(r"^\|[^|]*\|\s*`(\w+)`\s*\|")


def read_writers(path_init: Path) -> set[str]:
    """Return the writer names the package exports.

    Parameters
    ----------
    path_init : pathlib.Path
        The package ``__init__.py``.

    Returns
    -------
    set of str
        Names in ``__all__`` imported from a top-level submodule, minus ``main``.
    """
    cls_tree = ast.parse(path_init.read_text(encoding="utf-8"))
    set_all: set[str] = set()
    set_top: set[str] = set()
    for cls_node in cls_tree.body:
        if isinstance(cls_node, ast.ImportFrom) and cls_node.module:
            list_parts = cls_node.module.split(".")
            if len(list_parts) == 2 and list_parts[1] != "main":  # noqa: PLR2004
                set_top.update(cls_alias.name for cls_alias in cls_node.names)
        elif isinstance(cls_node, ast.Assign) and any(
            isinstance(cls_t, ast.Name) and cls_t.id == "__all__" for cls_t in cls_node.targets
        ):
            set_all = {
                cls_e.value
                for cls_e in ast.walk(cls_node.value)
                if isinstance(cls_e, ast.Constant) and isinstance(cls_e.value, str)
            }
    return (set_all & set_top) - _SET_NOT_WRITERS


def read_readme_writers(path_readme: Path) -> set[str]:
    """Return the writer names listed in the README layout table.

    Parameters
    ----------
    path_readme : pathlib.Path
        The README to read.

    Returns
    -------
    set of str
        The backticked name in the second column of each row of the layout table (the one
        headed ``| Layout | Writer |``); other tables are ignored.
    """
    set_names: set[str] = set()
    bool_in_table = False
    for str_line in path_readme.read_text(encoding="utf-8").splitlines():
        if str_line.startswith(_STR_TABLE_HEADER):
            bool_in_table = True
            continue
        if bool_in_table and not str_line.startswith("|"):
            break
        cls_match = _RE_ROW.match(str_line) if bool_in_table else None
        if cls_match:
            set_names.add(cls_match.group(1))
    return set_names


def main() -> int:
    """Compare the two sets and report every difference.

    Returns
    -------
    int
        ``0`` when they agree, ``1`` otherwise (including when no writer is found at all).
    """
    cls_parser = argparse.ArgumentParser(description=__doc__)
    cls_parser.add_argument("--init", type=Path, default=Path("src/layouts_cvm/__init__.py"))
    cls_parser.add_argument("--readme", type=Path, default=Path("README.md"))
    cls_args = cls_parser.parse_args()
    set_writers = read_writers(cls_args.init)
    set_rows = read_readme_writers(cls_args.readme)
    if not set_writers:
        print("check_readme_layouts: found ZERO writers in __all__; refusing to pass.")
        return 1
    list_problems = [
        f"{cls_args.readme}: writer '{str_name}' is exported but has no table row"
        for str_name in sorted(set_writers - set_rows)
    ] + [
        f"{cls_args.readme}: table row '{str_name}' is not an exported writer"
        for str_name in sorted(set_rows - set_writers)
    ]
    for str_problem in list_problems:
        print(f"❌ {str_problem}", file=sys.stderr)
    if list_problems:
        return 1
    print(f"README layout table matches {len(set_writers)} exported writer(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
