"""Fail when a tracked ``CLAUDE.md`` is not a stub beside its ``AGENTS.md``.

Agent guidance lives in ``AGENTS.md`` so every agent reads it; ``CLAUDE.md`` only imports it.
For each git-tracked ``CLAUDE.md`` outside ``.claude/`` (the shared copy synced from upstream):

- a sibling ``AGENTS.md`` exists;
- the first non-blank line is ``@AGENTS.md``;
- the ``Edit AGENTS.md, not this file.`` marker line is present;
- every line above the marker is an ``@<path>`` import or blank (content cannot drift back);
- every ``@<path>`` import names an existing file (relative to the ``CLAUDE.md``).

An unreadable file is a failure, never a pass.
"""

import argparse
from pathlib import Path
import subprocess
import sys


STR_IMPORT_FIRST = "@AGENTS.md"
STR_MARKER = "Edit AGENTS.md, not this file."


def list_tracked_claude_files(path_root: Path) -> list[Path]:
    """List tracked ``CLAUDE.md`` files outside ``.claude/``.

    Parameters
    ----------
    path_root : Path
        Repository root.

    Returns
    -------
    list of Path
        Paths relative to ``path_root``, sorted.

    Raises
    ------
    RuntimeError
        When ``git ls-files`` fails, so the gate never passes over a listing it could not make.
    """
    cls_proc = subprocess.run(  # noqa: S603
        ["git", "-C", str(path_root), "ls-files", "-z", "--", "CLAUDE.md", "**/CLAUDE.md"],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
    )
    if cls_proc.returncode != 0:
        raise RuntimeError(f"git ls-files failed: {cls_proc.stderr.strip()}")
    return sorted(
        Path(str_line)
        for str_line in cls_proc.stdout.split("\0")
        if str_line and Path(str_line).parts[0] != ".claude"
    )


def check_imports_above_marker(
    path_rel: Path, path_file: Path, list_above: list[str]
) -> list[str]:
    """Return problems in the lines above the marker (only resolvable ``@`` imports allowed).

    Parameters
    ----------
    path_rel : Path
        The ``CLAUDE.md``, relative to the repository root (for messages).
    path_file : Path
        The ``CLAUDE.md`` on disk; imports resolve against its directory.
    list_above : list of str
        The file's lines before the marker.

    Returns
    -------
    list of str
        One message per offending line.
    """
    list_problems = []
    for str_line in list_above:
        str_stripped = str_line.strip()
        if not str_stripped:
            continue
        if not str_stripped.startswith("@"):
            list_problems.append(f"{path_rel}: content above the marker: '{str_stripped}'")
        elif not (path_file.parent / Path(str_stripped[1:]).expanduser()).is_file():
            list_problems.append(f"{path_rel}: import {str_stripped} names a missing file")
    return list_problems


def check_claude_file(path_root: Path, path_rel: Path) -> list[str]:
    """Return the problems with one ``CLAUDE.md``.

    Parameters
    ----------
    path_root : Path
        Repository root.
    path_rel : Path
        The ``CLAUDE.md``, relative to ``path_root``.

    Returns
    -------
    list of str
        One message per problem, each naming the file; empty when it is a valid stub.
    """
    path_file = path_root / path_rel
    if not (path_file.parent / "AGENTS.md").is_file():
        return [f"{path_rel}: no sibling AGENTS.md"]
    try:
        list_lines = path_file.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as cls_err:
        return [f"{path_rel}: unreadable ({cls_err})"]
    list_problems = []
    list_nonblank = [str_line.strip() for str_line in list_lines if str_line.strip()]
    if not list_nonblank or list_nonblank[0] != STR_IMPORT_FIRST:
        list_problems.append(f"{path_rel}: first non-blank line must be {STR_IMPORT_FIRST}")
    int_marker = next(
        (int_i for int_i, str_line in enumerate(list_lines) if str_line.startswith(STR_MARKER)),
        None,
    )
    if int_marker is None:
        return [*list_problems, f"{path_rel}: missing the '{STR_MARKER}' marker line"]
    return [
        *list_problems,
        *check_imports_above_marker(path_rel, path_file, list_lines[:int_marker]),
    ]


def main() -> int:
    """Check every tracked ``CLAUDE.md`` and report each problem.

    Returns
    -------
    int
        ``0`` when all are valid stubs, ``1`` otherwise.
    """
    cls_parser = argparse.ArgumentParser(description=__doc__)
    cls_parser.add_argument("--root", type=Path, default=Path.cwd())
    cls_args = cls_parser.parse_args()
    try:
        list_files = list_tracked_claude_files(cls_args.root)
    except (RuntimeError, OSError) as cls_err:
        print(f"check_agents_md_pairs: {cls_err}", file=sys.stderr)
        return 1
    list_problems = [
        str_problem
        for path_rel in list_files
        for str_problem in check_claude_file(cls_args.root, path_rel)
    ]
    for str_problem in list_problems:
        print(f"❌ {str_problem}", file=sys.stderr)
    if list_problems:
        return 1
    print(f"{len(list_files)} CLAUDE.md file(s) are stubs beside an AGENTS.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
