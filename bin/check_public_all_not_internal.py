"""Fail when a package's ``__all__`` exports a name that is defined under ``_internal/``.

``_internal`` ships in the wheel so imports resolve after ``pip install``, but the leading
underscore marks it off-limits. A name imported from it and listed in ``__all__`` turns a
private model into public API by accident, and every consumer then couples to it.

Reading is done with ``ast`` — never by importing — so the gate has no side effects. Only
public ``__init__.py`` files (not inside ``_internal`` itself) that declare ``__all__`` are
checked, and discovery matching zero such files is a failure: a gate that scanned nothing
also found nothing wrong.
"""

import ast
import pathlib
import sys

from check_all_exports import declared_all


_SRC = pathlib.Path("src")
_INTERNAL = "_internal"


def internal_imports(path_init: pathlib.Path) -> dict[str, str]:
    """Map each name an ``__init__`` imports from an ``_internal`` module to that module.

    Parameters
    ----------
    path_init : pathlib.Path
        The ``__init__.py`` to read.

    Returns
    -------
    dict of str to str
        Bound name to the ``_internal`` module it came from.
    """
    dict_found: dict[str, str] = {}
    for cls_node in ast.walk(ast.parse(path_init.read_text(encoding="utf-8"))):
        if not isinstance(cls_node, ast.ImportFrom):
            continue
        str_module = cls_node.module or ""
        if _INTERNAL not in str_module.split("."):
            continue
        for cls_alias in cls_node.names:
            dict_found[cls_alias.asname or cls_alias.name] = str_module
    return dict_found


def check_package(path_init: pathlib.Path) -> list[str]:
    """Return one message per exported name that comes from ``_internal``.

    Parameters
    ----------
    path_init : pathlib.Path
        The package's ``__init__.py``.

    Returns
    -------
    list of str
        Human-readable problems; empty when ``__all__`` is clean.
    """
    list_exported = declared_all(path_init) or []
    dict_internal = internal_imports(path_init)
    return [
        f"{path_init}: '{str_name}' is exported in __all__ "
        f"but defined in {dict_internal[str_name]}"
        for str_name in sorted(set(list_exported) & dict_internal.keys())
    ]


def main() -> int:
    """Run the gate over every ``__init__.py`` under ``src/`` that declares ``__all__``.

    Returns
    -------
    int
        ``0`` when no ``__all__`` exports an ``_internal`` name, ``1`` otherwise.
    """
    list_inits = [
        path_init
        for path_init in sorted(_SRC.rglob("__init__.py"))
        if _INTERNAL not in path_init.parts and declared_all(path_init) is not None
    ]
    if not list_inits:
        print("check_public_all_not_internal: no package declares __all__ — checked NOTHING.")
        return 1
    list_problems = [msg for path_init in list_inits for msg in check_package(path_init)]
    for str_problem in list_problems:
        print(str_problem)
    return 1 if list_problems else 0


if __name__ == "__main__":
    sys.exit(main())
