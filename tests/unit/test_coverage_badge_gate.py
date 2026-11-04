"""Unit tests for the coverage-badge guards (``bin/check_coverage_badge.py``, issue #44).

The structural guard must fire on each of its two cases (a tracked ``coverage.svg``, a README
badge off the Pages URL) and stay quiet on the healthy layout; the content guard must reject
``n/a`` and a missing file but accept what ``genbadge`` really emits.
"""

import importlib.util
import os
from pathlib import Path
import re
import shutil
import subprocess
from types import ModuleType

import pytest


_STR_GIT = shutil.which("git") or "git"

_STR_SVG_REAL = '<svg><text x="1">coverage</text><text x="2">87%</text></svg>'
_STR_SVG_NA = '<svg><title>coverage: n/a</title><text x="2">n/a</text></svg>'
_STR_MSG_NO_README = "README.md is missing or not a regular file: cannot check its badge."


def _load_gate() -> ModuleType:
    """Import ``bin/check_coverage_badge.py`` as a module.

    Returns
    -------
    ModuleType
        The loaded gate module.
    """
    path_gate = Path(__file__).resolve().parents[2] / "bin" / "check_coverage_badge.py"
    cls_spec = importlib.util.spec_from_file_location("_check_coverage_badge", path_gate)
    assert cls_spec is not None
    assert cls_spec.loader is not None
    cls_module = importlib.util.module_from_spec(cls_spec)
    cls_spec.loader.exec_module(cls_module)
    return cls_module


@pytest.fixture(autouse=True)
def _clean_git_env(monkeypatch: pytest.MonkeyPatch) -> None:  # complexity-ok: one loop over GIT_*
    """Scrub every ``GIT_`` variable so the gate and fixtures run hermetically.

    The scrub also drops ``GIT_CONFIG_GLOBAL`` and ``GIT_CONFIG_NOSYSTEM``, which would let git
    fall back to the developer's own config, so both are pinned to "no config" afterwards.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest's environment patcher.
    """
    for str_key in [str_key for str_key in os.environ if str_key.startswith("GIT_")]:
        monkeypatch.delenv(str_key)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")


@pytest.fixture
def gate() -> ModuleType:
    """Provide the loaded gate module.

    Returns
    -------
    ModuleType
        The loaded gate module.
    """
    return _load_gate()


def _repo(path_root: Path, str_badge_url: str) -> Path:
    """Build a git repo whose README carries the given coverage badge URL.

    Parameters
    ----------
    path_root : pathlib.Path
        Directory to initialise.
    str_badge_url : str
        URL placed in the README ``![Test Coverage](...)`` badge.

    Returns
    -------
    pathlib.Path
        The repository root.
    """
    subprocess.run([_STR_GIT, "init", "-q"], cwd=path_root, check=True)  # noqa: S603
    (path_root / "README.md").write_text(f"![Test Coverage]({str_badge_url})\n", encoding="utf-8")
    return path_root


def _track(path_root: Path, str_name: str) -> None:
    """Create ``str_name`` and add it to the git index.

    Parameters
    ----------
    path_root : pathlib.Path
        Repository root.
    str_name : str
        File to create and stage.
    """
    (path_root / str_name).write_text(_STR_SVG_NA, encoding="utf-8")
    subprocess.run([_STR_GIT, "add", str_name], cwd=path_root, check=True)  # noqa: S603


def test_structural_healthy_layout_has_no_findings(gate: ModuleType, tmp_path: Path) -> None:
    """The Pages URL and no tracked ``coverage.svg`` is the passing case."""
    path_root = _repo(tmp_path, gate.URL_BADGE)
    assert gate.structural_findings(path_root) == []


def test_structural_tracked_badge_is_flagged(gate: ModuleType, tmp_path: Path) -> None:
    """A staged ``coverage.svg`` is reported, which is what blocks the commit."""
    path_root = _repo(tmp_path, gate.URL_BADGE)
    _track(path_root, "coverage.svg")
    assert any(
        "coverage.svg is tracked" in str_msg for str_msg in gate.structural_findings(path_root)
    )


def test_structural_nested_tracked_badge_is_flagged(gate: ModuleType, tmp_path: Path) -> None:
    """The glob catches a ``coverage.svg`` below the root, not just beside the README."""
    path_root = _repo(tmp_path, gate.URL_BADGE)
    (path_root / "docs").mkdir()
    _track(path_root, "docs/coverage.svg")
    assert gate.tracked_badge_files(path_root) == ["docs/coverage.svg"]


@pytest.mark.parametrize(
    "str_url",
    [
        "https://raw.githubusercontent.com/guilhermegor/layouts-cvm/main/coverage.svg",
        "./coverage.svg",
    ],
)
def test_structural_badge_off_pages_url_is_flagged(
    gate: ModuleType, tmp_path: Path, str_url: str
) -> None:
    """Any README badge URL other than the Pages one is reported."""
    path_root = _repo(tmp_path, str_url)
    assert any(
        "expected the Pages URL" in str_msg for str_msg in gate.structural_findings(path_root)
    )


def test_structural_missing_badge_is_flagged(gate: ModuleType, tmp_path: Path) -> None:
    """A README with no coverage badge fails, rather than passing vacuously."""
    path_root = _repo(tmp_path, gate.URL_BADGE)
    (path_root / "README.md").write_text("# no badge here\n", encoding="utf-8")
    assert len(gate.structural_findings(path_root)) == 1


def test_svg_percentage_is_accepted(gate: ModuleType, tmp_path: Path) -> None:
    """A badge whose value text is a percentage may be published."""
    path_svg = tmp_path / "coverage.svg"
    path_svg.write_text(_STR_SVG_REAL, encoding="utf-8")
    assert gate.svg_findings(path_svg) == []


def test_svg_na_is_rejected(gate: ModuleType, tmp_path: Path) -> None:
    """The ``n/a`` badge a broken coverage run produces must not be published."""
    path_svg = tmp_path / "coverage.svg"
    path_svg.write_text(_STR_SVG_NA, encoding="utf-8")
    assert len(gate.svg_findings(path_svg)) == 1


def test_svg_missing_file_is_rejected(gate: ModuleType, tmp_path: Path) -> None:
    """No badge at all is a failure, not a pass."""
    assert len(gate.svg_findings(tmp_path / "absent.svg")) == 1


def test_main_svg_mode_exits_nonzero_on_na(gate: ModuleType, tmp_path: Path) -> None:
    """``--svg`` turns the content finding into a non-zero exit for the publish job."""
    path_svg = tmp_path / "coverage.svg"
    path_svg.write_text(_STR_SVG_NA, encoding="utf-8")
    assert gate.main(["--svg", str(path_svg)]) == 1


def test_structural_missing_readme_is_a_finding_not_a_traceback(
    gate: ModuleType, tmp_path: Path
) -> None:
    """A repo without ``README.md`` reports a README-not-found finding instead of raising."""
    subprocess.run([_STR_GIT, "init", "-q"], cwd=tmp_path, check=True)  # noqa: S603
    assert gate.structural_findings(tmp_path) == [_STR_MSG_NO_README]


def test_readme_badge_url_missing_file_is_none(gate: ModuleType, tmp_path: Path) -> None:
    """A missing README yields ``None`` rather than raising."""
    assert gate.readme_badge_url(tmp_path / "README.md") is None


def test_structural_readme_directory_is_a_finding(gate: ModuleType, tmp_path: Path) -> None:
    """A directory named ``README.md`` is reported, not read."""
    subprocess.run([_STR_GIT, "init", "-q"], cwd=tmp_path, check=True)  # noqa: S603
    (tmp_path / "README.md").mkdir()
    assert gate.structural_findings(tmp_path) == [_STR_MSG_NO_README]


def test_main_exits_nonzero_without_readme(
    gate: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The structural mode fails the run, naming the missing README, when it is absent."""
    subprocess.run([_STR_GIT, "init", "-q"], cwd=tmp_path, check=True)  # noqa: S603
    monkeypatch.chdir(tmp_path)
    int_code = gate.main([])
    assert (int_code, capsys.readouterr().err) == (
        1,
        f"check_coverage_badge: {_STR_MSG_NO_README}\n",
    )


def _concurrency_group(str_workflow: str) -> str:
    """Read the one ``group:`` a workflow file declares.

    Parameters
    ----------
    str_workflow : str
        File name under ``.github/workflows``.

    Returns
    -------
    str
        The concurrency group name.
    """
    path_file = Path(__file__).resolve().parents[2] / ".github" / "workflows" / str_workflow
    (str_group,) = re.findall(r"^\s+group:\s*(\S+)\s*$", path_file.read_text("utf-8"), re.M)
    return str_group


def test_badge_and_docs_deploy_use_separate_concurrency_groups() -> None:
    """A badge run must not share a group with ``deploy_docs``.

    GitHub keeps one pending run per group and cancels the older one, so a docs deploy
    queued behind a badge publish was displaced by the next badge run (issue #63).
    """
    assert _concurrency_group("coverage-badge.yaml") != _concurrency_group("release-pypi.yaml")
