"""Fail when the README layout table and the package's writers disagree.

The writers are derived from ``src/layouts_cvm/__init__.py``, never listed twice: a name is a
writer when it is in ``__all__`` AND imported from a top-level submodule of the package
(``from layouts_cvm.cda import Cda`` or ``from .cda import Cda``, aliases and
``try``/``if`` nesting included; ``TYPE_CHECKING`` blocks, function bodies and ``_private``
modules are not). That excludes ``__version__``, ``main`` and every schema/model name, so the
gate neither depends on nor breaks when the schemas move.

The README side is the backticked name in the second column of each row of the layout table.
"""

import argparse
import ast
from collections.abc import Iterator
from pathlib import Path
import re
import sys


_SET_NOT_WRITERS = frozenset({"__version__", "main"})
_STR_TABLE_HEADER = "| Layout | Writer |"
_RE_ROW = re.compile(r"^\|[^|]*\|\s*`(\w+)`\s*\|")
_RE_SEPARATOR = re.compile(r"^\|[\s:|-]+$")
_RE_NAV = re.compile(r"^\s{6}- .*:\s*(\w+)\.md\s*$")


def _runtime_branches(cls_node: ast.stmt) -> list[ast.stmt]:
    """Return the nested statements of ``cls_node`` that can run at import time."""
    if isinstance(cls_node, (ast.Try, ast.TryStar)):
        list_nested = [*cls_node.body]
        for cls_handler in cls_node.handlers:
            list_nested.extend(cls_handler.body)
        return [*list_nested, *cls_node.orelse, *cls_node.finalbody]
    if isinstance(cls_node, ast.With):
        return cls_node.body
    if not isinstance(cls_node, ast.If):
        return []
    str_test = ast.unparse(cls_node.test)
    if str_test.endswith("TYPE_CHECKING"):
        return cls_node.orelse if not str_test.startswith("not ") else cls_node.body
    return [*cls_node.body, *cls_node.orelse]


def _iter_statements(
    list_body: list[ast.stmt], bool_nested: bool = False
) -> Iterator[tuple[ast.stmt, bool]]:
    """Yield ``(statement, is_nested)`` for what runs at import time.

    Descends into ``try``, ``with`` and ``if`` only. The branch a ``TYPE_CHECKING`` test
    never takes at runtime is skipped, and function and class bodies are never entered.
    """
    for cls_node in list_body:
        yield cls_node, bool_nested
        yield from _iter_statements(_runtime_branches(cls_node), True)


def _read_literal_names(cls_value: ast.expr) -> set[str]:
    """Return the string literals of a list/tuple node, or raise ``ValueError``."""
    if isinstance(cls_value, (ast.List, ast.Tuple)) and all(
        isinstance(cls_e, ast.Constant) and isinstance(cls_e.value, str)
        for cls_e in cls_value.elts
    ):
        return {cls_e.value for cls_e in cls_value.elts}
    raise ValueError("__all__ must be a list or tuple of string literals")


def _is_all_name(cls_target: ast.expr) -> bool:
    """Return whether an assignment target is the bare name ``__all__``."""
    return isinstance(cls_target, ast.Name) and cls_target.id == "__all__"


def _replacement_value(cls_node: ast.stmt) -> ast.expr | None:
    """Return the value a statement binds to ``__all__`` with ``=``, or ``None``."""
    if isinstance(cls_node, ast.Assign) and any(_is_all_name(cls_t) for cls_t in cls_node.targets):
        return cls_node.value
    if isinstance(cls_node, ast.AnnAssign) and _is_all_name(cls_node.target):
        return cls_node.value
    return None


def read_all_names(cls_tree: ast.Module) -> set[str]:
    """Return the names in ``__all__``, replayed in source order.

    Parameters
    ----------
    cls_tree : ast.Module
        The parsed package ``__init__.py``.

    Returns
    -------
    set of str
        What ``__all__`` holds once the module has run: ``=`` replaces, ``+=`` extends.

    Raises
    ------
    ValueError
        When ``__all__`` is absent, an assignment is not a list/tuple of string literals, or
        it is mutated by ``.extend``/``.append``, which the gate cannot read.
    """
    set_names: set[str] = set()
    bool_found = False
    for cls_node, bool_nested in _iter_statements(cls_tree.body):
        cls_replaced = _replacement_value(cls_node)
        if cls_replaced is not None and bool_nested:
            raise ValueError("__all__ may only be assigned with = at the top level")
        if cls_replaced is not None:
            set_names, bool_found = _read_literal_names(cls_replaced), True
        elif isinstance(cls_node, ast.AugAssign) and _is_all_name(cls_node.target):
            if not isinstance(cls_node.op, ast.Add):
                raise ValueError("__all__ may only be extended with +=")
            set_names, bool_found = set_names | _read_literal_names(cls_node.value), True
        elif isinstance(cls_node, ast.Expr) and ast.unparse(cls_node).startswith("__all__"):
            raise ValueError("__all__ is mutated by a method call; use = or += with literals")
    if not bool_found:
        raise ValueError("no __all__ assignment found at import time")
    return set_names


def _is_writer_module(cls_node: ast.ImportFrom, str_package: str) -> bool:
    """Return whether an import is from a public top-level submodule of the package."""
    if not cls_node.module:
        return False
    list_parts = cls_node.module.split(".")
    if list_parts[-1].startswith("_"):
        return False
    bool_absolute = cls_node.level == 0 and len(list_parts) == 2 and list_parts[0] == str_package  # noqa: PLR2004
    return bool_absolute or (cls_node.level == 1 and len(list_parts) == 1)


def read_top_level_imports(cls_tree: ast.Module, str_package: str) -> set[str]:
    """Return the names imported from a public top-level submodule of the package.

    Parameters
    ----------
    cls_tree : ast.Module
        The parsed package ``__init__.py``.
    str_package : str
        The package's import name.

    Returns
    -------
    set of str
        The bound name (the ``as`` alias when present) of every ``from <package>.<module>
        import ...`` or ``from .<module> import ...`` at import time (``try``/``if`` bodies
        included, ``TYPE_CHECKING`` and function bodies not). A module whose name starts
        with ``_`` is private and never a writer source.
    """
    set_top: set[str] = set()
    for cls_node, _ in _iter_statements(cls_tree.body):
        if isinstance(cls_node, ast.ImportFrom) and _is_writer_module(cls_node, str_package):
            if any(cls_alias.name == "*" for cls_alias in cls_node.names):
                raise ValueError(f"star import from {cls_node.module}: list the names explicitly")
            set_top.update(cls_alias.asname or cls_alias.name for cls_alias in cls_node.names)
    return set_top


def read_writers(path_init: Path, str_package: str) -> set[str]:
    """Return the writer names the package exports.

    Parameters
    ----------
    path_init : pathlib.Path
        The package ``__init__.py``.
    str_package : str
        The package's import name.

    Returns
    -------
    set of str
        Names in ``__all__`` imported from a top-level submodule, minus ``main``.
    """
    cls_tree = ast.parse(path_init.read_text(encoding="utf-8"))
    return (read_all_names(cls_tree) & read_top_level_imports(cls_tree, str_package)) - (
        _SET_NOT_WRITERS
    )


def read_readme_writers(path_readme: Path) -> list[str]:
    """Return the writer names listed in the README layout table.

    Parameters
    ----------
    path_readme : pathlib.Path
        The README to read.

    Returns
    -------
    list of str
        The backticked name in the second column of each row of the layout table (the one
        headed ``| Layout | Writer |``), in order and repeats kept; other tables are ignored.
        Only the Writer column is checked: the Document and Spec columns are hand-copied.

    Raises
    ------
    ValueError
        When a body row has no backticked name in its second column.
    """
    list_names: list[str] = []
    bool_in_table = False
    for str_line in path_readme.read_text(encoding="utf-8").splitlines():
        if str_line.startswith(_STR_TABLE_HEADER):
            bool_in_table = True
            continue
        if bool_in_table and not str_line.startswith("|"):
            break
        if not bool_in_table or _RE_SEPARATOR.match(str_line):
            continue
        cls_match = _RE_ROW.match(str_line)
        if not cls_match:
            raise ValueError(f"{path_readme}: table row has no backticked writer: {str_line!r}")
        list_names.append(cls_match.group(1))
    return list_names


def read_module_by_name(cls_tree: ast.Module, str_package: str) -> dict[str, str]:
    """Map each name imported from a writer submodule to that submodule, in import order.

    Parameters
    ----------
    cls_tree : ast.Module
        The parsed package ``__init__.py``.
    str_package : str
        The package's import name.

    Returns
    -------
    dict of str to str
        ``{"CdaV3": "cda_v3", ...}``; the submodule name is the one shared sort key.
    """
    dict_modules: dict[str, str] = {}
    for cls_node, _ in _iter_statements(cls_tree.body):
        if isinstance(cls_node, ast.ImportFrom) and _is_writer_module(cls_node, str_package):
            str_module = cls_node.module.split(".")[-1]  # type: ignore[union-attr]
            dict_modules.update(
                {cls_alias.asname or cls_alias.name: str_module for cls_alias in cls_node.names}
            )
    return dict_modules


def read_all_order(cls_tree: ast.Module) -> list[str]:
    """Return the literal ``__all__`` entries in file order, ``+=`` appended.

    Parameters
    ----------
    cls_tree : ast.Module
        The parsed package ``__init__.py``.

    Returns
    -------
    list of str
        The entries; empty when ``__all__`` is not a literal (``read_all_names`` reports that).
    """
    list_order: list[str] = []
    for cls_node, _ in _iter_statements(cls_tree.body):
        cls_replaced = _replacement_value(cls_node)
        cls_value = cls_replaced
        if isinstance(cls_node, ast.AugAssign) and _is_all_name(cls_node.target):
            cls_value = cls_node.value
        if not isinstance(cls_value, (ast.List, ast.Tuple)):
            continue
        list_names = [cls_e.value for cls_e in cls_value.elts if isinstance(cls_e, ast.Constant)]
        list_order = list_names if cls_replaced is not None else [*list_order, *list_names]
    return list_order


def read_nav_modules(path_mkdocs: Path) -> list[str]:
    """Return the page stems under the ``Layouts`` nav section, in order.

    Parameters
    ----------
    path_mkdocs : pathlib.Path
        The ``mkdocs.yml`` to read.

    Returns
    -------
    list of str
        ``cda_v3`` for a ``...: cda_v3.md`` entry; empty when the file or section is absent.
    """
    if not path_mkdocs.is_file():
        return []
    list_stems: list[str] = []
    bool_in = False
    for str_line in path_mkdocs.read_text(encoding="utf-8").splitlines():
        if str_line.strip() == "- Layouts:":
            bool_in = True
            continue
        if not bool_in:
            continue
        cls_match = _RE_NAV.match(str_line)
        if not cls_match:
            break
        list_stems.append(cls_match.group(1))
    return list_stems


def find_order_problems(
    str_label: str, list_keys: list[str], list_leading: tuple[str, ...] = ()
) -> list[str]:
    """Report a list that is not in the canonical (sorted) order.

    Parameters
    ----------
    str_label : str
        Where the list lives, for the message.
    list_keys : list of str
        The sort keys in file order.
    list_leading : tuple of str
        Keys allowed to sit before the sorted run (``__version__``, ``main`` in ``__all__``).

    Returns
    -------
    list of str
        One message naming the first out-of-order key and the sorted order; empty when sorted.
    """
    list_body = [str_k for str_k in list_keys if str_k not in list_leading]
    list_expected = sorted(list_body)
    if list_body == list_expected:
        return []
    str_first = next(
        str_a for str_a, str_b in zip(list_body, list_expected, strict=True) if str_a != str_b
    )
    return [
        f"{str_label}: not in canonical order (first misplaced: '{str_first}'); "
        f"expected {list_expected}"
    ]


def find_registry_order_problems(
    path_init: Path, str_package: str, path_readme: Path, path_mkdocs: Path
) -> list[str]:
    """Check the four registries against the one sort key: the writer's submodule name.

    Parameters
    ----------
    path_init : pathlib.Path
        The package ``__init__.py`` (import block and ``__all__``).
    str_package : str
        The package's import name.
    path_readme : pathlib.Path
        The README with the layout table.
    path_mkdocs : pathlib.Path
        The ``mkdocs.yml`` with the ``Layouts`` nav.

    Returns
    -------
    list of str
        One message per registry that is out of order.
    """
    cls_tree = ast.parse(path_init.read_text(encoding="utf-8"))
    dict_module = read_module_by_name(cls_tree, str_package)
    list_rows = [dict_module.get(str_n, str_n) for str_n in read_readme_writers(path_readme)]
    list_all = [dict_module[str_n] for str_n in read_all_order(cls_tree) if str_n in dict_module]
    return (
        find_order_problems(f"{path_init} imports", list(dict_module.values()))
        + find_order_problems(f"{path_init} __all__", list_all, ("__version__", "main"))
        + find_order_problems(f"{path_readme} layout table", list_rows)
        + find_order_problems(f"{path_mkdocs} Layouts nav", read_nav_modules(path_mkdocs))
    )


def main() -> int:
    """Compare the two sets and report every difference.

    Returns
    -------
    int
        ``0`` when they agree, ``1`` otherwise (including when no writer is found at all).
    """
    cls_parser = argparse.ArgumentParser(description=__doc__)
    cls_parser.add_argument("--init", type=Path, default=Path("src/layouts_cvm/__init__.py"))
    cls_parser.add_argument("--package", default="layouts_cvm")
    cls_parser.add_argument("--readme", type=Path, default=Path("README.md"))
    cls_parser.add_argument("--mkdocs", type=Path, default=Path("mkdocs.yml"))
    cls_args = cls_parser.parse_args()
    try:
        set_writers = read_writers(cls_args.init, cls_args.package)
        list_rows = read_readme_writers(cls_args.readme)
    except (OSError, SyntaxError, ValueError) as cls_err:
        print(f"check_readme_layouts: {cls_err}", file=sys.stderr)
        return 1
    set_rows = set(list_rows)
    if not set_writers:
        print(
            "check_readme_layouts: found ZERO writers in __all__; refusing to pass.",
            file=sys.stderr,
        )
        return 1
    list_problems = (
        [
            f"{cls_args.readme}: writer '{str_name}' is exported but has no table row"
            for str_name in sorted(set_writers - set_rows)
        ]
        + [
            f"{cls_args.readme}: table row '{str_name}' is not an exported writer"
            for str_name in sorted(set_rows - set_writers)
        ]
        + [
            f"{cls_args.readme}: table row '{str_name}' is listed more than once"
            for str_name in sorted({str_n for str_n in list_rows if list_rows.count(str_n) > 1})
        ]
    )
    list_problems += find_registry_order_problems(
        cls_args.init, cls_args.package, cls_args.readme, cls_args.mkdocs
    )
    for str_problem in list_problems:
        print(f"❌ {str_problem}", file=sys.stderr)
    if list_problems:
        return 1
    print(f"README layout table matches {len(set_writers)} exported writer(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
