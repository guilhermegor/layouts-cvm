#!/usr/bin/env python3
"""Keep the coverage badge published from ``gh-pages``, never committed (issue #44).

A committed ``coverage.svg`` showed ``n/a`` from the first commit because nothing ever
regenerated it, and regenerating it per PR would make every pair of parallel PRs conflict on the
file. CI on ``main`` now builds the badge and publishes it to the ``gh-pages`` root; the README
points at the Pages URL. Two guards keep that from regressing, and they answer different
questions, so they are two modes of one script:

* **Structural** (default, no arguments): fail when a ``coverage.svg`` is tracked, or when the
  README coverage badge points anywhere but the Pages URL. Runs in pre-commit and CI.
* **Content** (``--svg PATH``): fail when the generated badge text is not a percentage. Runs in
  the publish job right before the push, so a broken coverage run turns the job red instead of
  publishing ``n/a``.

Together they leave ``n/a`` only one way back in: through a red job, never silently.
"""

import argparse
import pathlib
import re
import subprocess
import sys


URL_BADGE = "https://guilhermegor.github.io/layouts-cvm/coverage.svg"

_RE_README_BADGE = re.compile(r"!\[Test Coverage\]\(([^)\s]+)\)")
_RE_SVG_PERCENT = re.compile(r">\s*\d+(?:\.\d+)?%\s*<")


def tracked_badge_files(path_root: pathlib.Path) -> list[str]:
    """List the ``coverage.svg`` files git tracks under ``path_root``.

    Parameters
    ----------
    path_root : pathlib.Path
        Repository root, used as the git working directory.

    Returns
    -------
    list of str
        Tracked paths named ``coverage.svg``, at any depth (index entries included).
    """
    cls_result = subprocess.run(  # noqa: S603
        ["git", "ls-files", "-z", "--", ":(glob)**/coverage.svg"],  # noqa: S607
        cwd=path_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return [str_path for str_path in cls_result.stdout.split("\0") if str_path]


def readme_badge_url(path_readme: pathlib.Path) -> str | None:
    """Return the URL of the README's ``![Test Coverage](...)`` badge.

    Parameters
    ----------
    path_readme : pathlib.Path
        The README to read.

    Returns
    -------
    str or None
        The badge URL, or ``None`` when the README is missing or has no coverage badge.
    """
    if not path_readme.is_file():
        return None
    cls_match = _RE_README_BADGE.search(path_readme.read_text(encoding="utf-8"))
    return cls_match.group(1) if cls_match else None


def structural_findings(path_root: pathlib.Path) -> list[str]:
    """Collect every way the repo can stop publishing its coverage badge from Pages.

    Parameters
    ----------
    path_root : pathlib.Path
        Repository root holding ``README.md``.

    Returns
    -------
    list of str
        One message per violation; empty when the structure holds.
    """
    list_findings = [
        f"{str_path} is tracked: CI publishes the badge to gh-pages, so delete it "
        "(it is gitignored)."
        for str_path in tracked_badge_files(path_root)
    ]
    str_url = readme_badge_url(path_root / "README.md")
    if str_url != URL_BADGE:
        list_findings.append(
            f"README coverage badge is {str_url!r}, expected the Pages URL {URL_BADGE!r}."
        )
    return list_findings


def svg_findings(path_svg: pathlib.Path) -> list[str]:
    """Check that a generated badge carries a percentage rather than ``n/a``.

    Parameters
    ----------
    path_svg : pathlib.Path
        The badge ``genbadge`` wrote.

    Returns
    -------
    list of str
        One message when the text is not a percentage; empty otherwise.
    """
    if not path_svg.is_file():
        return [f"{path_svg} does not exist: the coverage run produced no badge."]
    if _RE_SVG_PERCENT.search(path_svg.read_text(encoding="utf-8")):
        return []
    return [f"{path_svg} carries no percentage (n/a?): refusing to publish it."]


def main(list_argv: list[str] | None = None) -> int:
    """Run the structural guard, or the content guard when ``--svg`` is given.

    Parameters
    ----------
    list_argv : list of str, optional
        Command-line arguments; ``sys.argv[1:]`` when omitted.

    Returns
    -------
    int
        ``0`` when the guard holds, ``1`` otherwise.
    """
    cls_parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    cls_parser.add_argument("--svg", type=pathlib.Path, help="check this generated badge's text")
    cls_args = cls_parser.parse_args(list_argv)
    list_findings = (
        svg_findings(cls_args.svg) if cls_args.svg else structural_findings(pathlib.Path.cwd())
    )
    for str_finding in list_findings:
        print(f"check_coverage_badge: {str_finding}", file=sys.stderr)
    return 1 if list_findings else 0


if __name__ == "__main__":
    sys.exit(main())
