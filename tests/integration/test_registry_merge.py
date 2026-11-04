"""Two branches that each add a writer merge cleanly and still pass the order gate.

Recreates the measurement behind issue 55 on a scratch repo seeded with the real registries.
Each branch registers a different writer next to a different neighbour, the way a writer PR
does; the merge must not conflict and the merged registries must stay in canonical order with
every writer present. No registry stores a count, so no line exists that both branches could
change identically and git could keep one of them silently.
"""

from pathlib import Path
import re
import runpy
import shutil
import subprocess

import pytest


_PATH_ROOT = Path(__file__).parents[2]
_DICT_GATE = runpy.run_path(str(_PATH_ROOT / "bin" / "check_readme_layouts.py"))
_GIT = shutil.which("git") or "git"
_PATH_INIT = Path("src") / "layouts_cvm" / "__init__.py"


def _git(path_repo: Path, *tuple_args: str) -> subprocess.CompletedProcess[str]:
    """Run git in the scratch repo with a fixed identity.

    Parameters
    ----------
    path_repo : pathlib.Path
        The scratch repo.
    *tuple_args : str
        The git arguments.

    Returns
    -------
    subprocess.CompletedProcess of str
        The finished process; the caller reads ``returncode``.
    """
    list_cmd = [_GIT, "-c", "user.name=t", "-c", "user.email=t@t", *tuple_args]
    return subprocess.run(  # noqa: S603 - constant trusted argv
        list_cmd, cwd=path_repo, capture_output=True, text=True, check=False
    )


def _insert_after(path_file: Path, str_marker: str, str_new: str) -> None:
    """Insert a line right after the first line containing the marker.

    Parameters
    ----------
    path_file : pathlib.Path
        The registry file to edit.
    str_marker : str
        A substring identifying the neighbour line.
    str_new : str
        The line to add below it.
    """
    str_text = re.sub(
        rf"^(.*{re.escape(str_marker)}.*)$",
        lambda cls_m: f"{cls_m.group(1)}\n{str_new}",
        path_file.read_text(encoding="utf-8"),
        count=1,
        flags=re.MULTILINE,
    )
    path_file.write_text(str_text, encoding="utf-8")


def _register_writer(path_repo: Path, str_after: str, str_module: str, str_name: str) -> None:
    """Add one writer to the import block, ``__all__``, README table and nav.

    Parameters
    ----------
    path_repo : pathlib.Path
        The scratch repo.
    str_after : str
        The existing writer class the new one sorts directly after.
    str_module : str
        The new writer's submodule name.
    str_name : str
        The new writer's class name.
    """
    _insert_after(
        path_repo / _PATH_INIT,
        f"import {str_after}",
        f"from layouts_cvm.{str_module} import {str_name}",
    )
    _insert_after(path_repo / _PATH_INIT, f'"{str_after}",', f'    "{str_name}",')
    _insert_after(
        path_repo / "README.md",
        f"`{str_after}`",
        f"| {str_name} | `{str_name}` | `{str_name}Document` | spec |",
    )
    _insert_after(
        path_repo / "mkdocs.yml",
        f": {str_module.rsplit('_', 1)[0]}_v3.md",
        f'      - "{str_name}": {str_module}.md',
    )


def _problems(path_repo: Path) -> list[str]:
    """Return every order problem the gate finds in the scratch repo.

    Parameters
    ----------
    path_repo : pathlib.Path
        The scratch repo.

    Returns
    -------
    list of str
        The gate's messages; empty when the registries are in canonical order.
    """
    return _DICT_GATE["find_registry_order_problems"](
        path_repo / _PATH_INIT, "layouts_cvm", path_repo / "README.md", path_repo / "mkdocs.yml"
    )


@pytest.fixture
def path_base(tmp_path: Path) -> Path:
    """Build a scratch repo whose base commit holds the real registries.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest's per-test directory.

    Returns
    -------
    pathlib.Path
        The scratch repo, on ``main``.
    """
    (tmp_path / _PATH_INIT.parent).mkdir(parents=True)
    shutil.copy(_PATH_ROOT / _PATH_INIT, tmp_path / _PATH_INIT)
    shutil.copy(_PATH_ROOT / "README.md", tmp_path)
    shutil.copy(_PATH_ROOT / "mkdocs.yml", tmp_path)
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "base")
    return tmp_path


def test_two_branches_each_adding_a_writer_merge_cleanly(path_base: Path) -> None:
    """Writers added next to different neighbours merge with no conflict and stay sorted."""
    _git(path_base, "checkout", "-q", "-b", "a", "main")
    _register_writer(path_base, "CdaV3", "cda_v4", "CdaV4")
    _git(path_base, "commit", "-q", "-am", "a")
    _git(path_base, "checkout", "-q", "-b", "b", "main")
    _register_writer(path_base, "PerfilMensalV3", "perfil_mensal_v4", "PerfilMensalV4")
    _git(path_base, "commit", "-q", "-am", "b")

    cls_merge = _git(path_base, "merge", "--no-edit", "a")

    str_readme = (path_base / "README.md").read_text(encoding="utf-8")
    assert (cls_merge.returncode, _problems(path_base), "`CdaV4`" in str_readme) == (
        0,
        [],
        True,
    )
