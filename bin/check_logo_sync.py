"""Fail unless the README logo and the docs logo are one and the same image.

The README points at ``.../main/<path>`` on raw.githubusercontent.com, ``docs/index.md`` at an
``<img src>`` relative to ``docs/``, and ``mkdocs.yml`` at ``theme.logo`` / ``theme.favicon``,
also relative to ``docs/``. All four must resolve to existing, byte-identical files; a missing
file fails. Reading is textual (regex) so the gate needs no YAML dependency; only direct
children of the top-level ``theme:`` block count, so ``theme.icon.logo`` and ``extra.logo``
never match.
"""

import pathlib
import re
import sys


_ROOT = pathlib.Path(__file__).resolve().parents[1]
_RE_README = re.compile(r"raw\.githubusercontent\.com/[^/\s\"']+/[^/\s\"']+/main/([^\s\"')?#]+)")
_RE_INDEX = re.compile(r"<img[^>]*?\ssrc=[\"']([^\"']+)[\"']")
_RE_THEME_BLOCK = re.compile(r"^theme:\n((?:[ \t]+.*\n?|\n)*)", re.MULTILINE)
_RE_THEME = re.compile(r"^  (logo|favicon):\s*[\"']?([^\s\"'#]+)", re.MULTILINE)


def _read_text(path_file: pathlib.Path) -> str:
    """Return the file's text, or an empty string when it does not exist."""
    return path_file.read_text(encoding="utf-8") if path_file.is_file() else ""


def _under(path_base: pathlib.Path, str_rel: str | None) -> pathlib.Path | None:
    """Join ``str_rel`` onto ``path_base``, keeping an absent reference as ``None``."""
    return path_base / str_rel if str_rel else None


def resolve_logos(path_root: pathlib.Path) -> dict[str, pathlib.Path | None]:
    """Map each logo reference to the local file it points at.

    Parameters
    ----------
    path_root : pathlib.Path
        Repository root.

    Returns
    -------
    dict of str to pathlib.Path or None
        Reference label to resolved path; ``None`` when the reference itself is absent.
    """
    cls_readme = _RE_README.search(_read_text(path_root / "README.md"))
    cls_index = _RE_INDEX.search(_read_text(path_root / "docs" / "index.md"))
    cls_theme = _RE_THEME_BLOCK.search(_read_text(path_root / "mkdocs.yml"))
    dict_theme = dict(_RE_THEME.findall(cls_theme.group(1) if cls_theme else ""))
    path_docs = path_root / "docs"
    return {
        "README.md": _under(path_root, cls_readme and cls_readme.group(1)),
        "docs/index.md": _under(path_docs, cls_index and cls_index.group(1)),
        "mkdocs.yml theme.logo": _under(path_docs, dict_theme.get("logo")),
        "mkdocs.yml theme.favicon": _under(path_docs, dict_theme.get("favicon")),
    }


def check_logos(path_root: pathlib.Path) -> list[str]:
    """Return one message per missing logo file, or one if the files differ.

    Parameters
    ----------
    path_root : pathlib.Path
        Repository root.

    Returns
    -------
    list of str
        Human-readable problems; empty when every logo exists and all are identical.
    """
    list_problems = []
    dict_bytes: dict[str, bytes] = {}
    for str_label, path_ref in resolve_logos(path_root).items():
        if path_ref is None or not path_ref.is_file():
            list_problems.append(f"{str_label}: logo file missing ({path_ref or 'no reference'})")
        else:
            dict_bytes[str_label] = path_ref.read_bytes()
    dict_groups: dict[bytes, list[str]] = {}
    for str_label, bytes_content in sorted(dict_bytes.items()):
        dict_groups.setdefault(bytes_content, []).append(str_label)
    if len(dict_groups) > 1:
        list_problems.append(
            "logo files differ, they must be byte-identical: "
            + " | ".join(", ".join(list_labels) for list_labels in dict_groups.values())
        )
    return list_problems


def main() -> int:
    """Run the gate on this repository.

    Returns
    -------
    int
        ``0`` when the logos are in sync, ``1`` otherwise.
    """
    list_problems = check_logos(_ROOT)
    for str_problem in list_problems:
        print(str_problem)
    return 1 if list_problems else 0


if __name__ == "__main__":
    sys.exit(main())
