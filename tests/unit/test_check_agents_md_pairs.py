"""The CLAUDE.md / AGENTS.md pairing gate: the passing layout and each failure."""

from pathlib import Path
import runpy
import subprocess
import sys

import pytest


_DICT_GATE = runpy.run_path(str(Path(__file__).parents[2] / "bin" / "check_agents_md_pairs.py"))
_STUB = "@AGENTS.md\n\nEdit AGENTS.md, not this file. Claude-Code-only lines go below this one.\n"


def _check(path_root: Path) -> list[str]:
    """Run the gate's per-file check on ``path_root/sub/CLAUDE.md``."""
    return _DICT_GATE["check_claude_file"](path_root, Path("sub/CLAUDE.md"))


@pytest.fixture
def path_sub(tmp_path: Path) -> Path:
    """Build a ``sub/`` directory holding a valid pair."""
    path_dir = tmp_path / "sub"
    path_dir.mkdir()
    (path_dir / "AGENTS.md").write_text("# Guidance\n")
    (path_dir / "CLAUDE.md").write_text(_STUB)
    return path_dir


def test_valid_stub_passes(path_sub: Path) -> None:
    """A stub beside an AGENTS.md has no problems."""
    assert _check(path_sub.parent) == []


def test_claude_only_lines_below_the_marker_pass(path_sub: Path) -> None:
    """Lines below the marker are free-form."""
    (path_sub / "CLAUDE.md").write_text(_STUB + "Use the /foo slash command.\n")

    assert _check(path_sub.parent) == []


def test_missing_sibling_agents_md_fails(path_sub: Path) -> None:
    """No AGENTS.md beside the CLAUDE.md is reported by name."""
    (path_sub / "AGENTS.md").unlink()

    assert "sub/CLAUDE.md: no sibling AGENTS.md" in _check(path_sub.parent)


def test_wrong_first_line_fails(path_sub: Path) -> None:
    """The first non-blank line must be the AGENTS.md import."""
    (path_sub / "CLAUDE.md").write_text("@README.md\n" + _STUB)
    (path_sub / "README.md").write_text("x")

    assert any("first non-blank line" in str_p for str_p in _check(path_sub.parent))


def test_missing_marker_fails(path_sub: Path) -> None:
    """A file without the marker line fails."""
    (path_sub / "CLAUDE.md").write_text("@AGENTS.md\n")

    assert any("marker" in str_p for str_p in _check(path_sub.parent))


def test_content_above_marker_fails(path_sub: Path) -> None:
    """Prose above the marker is rejected so content cannot drift back."""
    (path_sub / "CLAUDE.md").write_text("@AGENTS.md\nsome rule\n" + _STUB)

    assert any("above the marker" in str_p for str_p in _check(path_sub.parent))


def test_import_of_missing_file_fails(path_sub: Path) -> None:
    """An ``@`` import naming a missing file fails."""
    (path_sub / "CLAUDE.md").write_text("@AGENTS.md\n@PRINCIPLES.md\n\n" + _STUB.split("\n\n")[1])

    assert any("PRINCIPLES.md names a missing file" in str_p for str_p in _check(path_sub.parent))


def test_unreadable_file_fails_closed(path_sub: Path) -> None:
    """A file that cannot be decoded is a failure, not a pass."""
    (path_sub / "CLAUDE.md").write_bytes(b"\xff\xfe\x00bad")

    assert any("unreadable" in str_p for str_p in _check(path_sub.parent))


def test_non_ascii_path_is_listed_unquoted(tmp_path: Path) -> None:
    """``git ls-files -z`` returns accented directories verbatim, not C-quoted."""
    path_dir = tmp_path / "relações"
    path_dir.mkdir()
    (path_dir / "CLAUDE.md").write_text(_STUB, encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "init", "-q"], check=True)  # noqa: S603, S607
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)  # noqa: S603, S607

    assert _DICT_GATE["list_tracked_claude_files"](tmp_path) == [Path("relações/CLAUDE.md")]


def test_home_relative_import_above_marker_resolves(
    path_sub: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """``@~/x.md`` resolves against the home directory, not the file's directory."""
    (tmp_path / "x.md").write_text("x")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    (path_sub / "CLAUDE.md").write_text("@AGENTS.md\n@~/x.md\n" + _STUB.split("\n", 1)[1])

    assert _check(path_sub.parent) == []


def test_main_fails_when_no_claude_file_is_tracked(tmp_path: Path) -> None:
    """A discovery that matches nothing must fail, not pass vacuously."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)  # noqa: S603, S607
    gate = Path(__file__).parents[2] / "bin" / "check_agents_md_pairs.py"
    cls_proc = subprocess.run(  # noqa: S603
        [sys.executable, str(gate), "--root", str(tmp_path)], capture_output=True, check=False
    )
    assert (cls_proc.returncode, b"no tracked CLAUDE.md" in cls_proc.stderr) == (1, True)
