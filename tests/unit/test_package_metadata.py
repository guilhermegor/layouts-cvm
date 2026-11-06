"""Guard the packaging metadata a consumer's type checker and PyPI page rely on."""

from pathlib import Path
import subprocess
import tomllib
import zipfile

import pytest
import yaml


PATH_ROOT = Path(__file__).resolve().parents[2]
STR_PY_PREFIX = "Programming Language :: Python :: 3."


@pytest.fixture
def list_classifiers() -> list[str]:
    """Read the Poetry classifiers from pyproject.toml.

    Returns
    -------
    list[str]
        The declared trove classifiers.
    """
    dict_pyproject = tomllib.loads((PATH_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return dict_pyproject["tool"]["poetry"]["classifiers"]


@pytest.fixture(scope="module")  # fixture-scope-ok: one poetry build shared by read-only asserts
def list_wheel_names(
    tmp_path_factory: pytest.TempPathFactory,
) -> list[str]:
    """Build the wheel once and list its members.

    Parameters
    ----------
    tmp_path_factory : pytest.TempPathFactory
        Factory for the build output directory.

    Returns
    -------
    list[str]
        Member paths inside the built wheel.
    """
    path_out = tmp_path_factory.mktemp("wheel")
    subprocess.run(  # noqa: S603
        ["poetry", "build", "-f", "wheel", "--output", str(path_out)],  # noqa: S607
        cwd=PATH_ROOT,
        check=True,
        capture_output=True,
    )
    with zipfile.ZipFile(next(path_out.glob("*.whl"))) as cls_zip:
        return cls_zip.namelist()


def test_classifiers_python_versions_equal_tests_matrix(list_classifiers: list[str]) -> None:
    """Every CI-tested Python version is a classifier, and no other is.

    Parameters
    ----------
    list_classifiers : list[str]
        The declared trove classifiers.
    """
    dict_workflow = yaml.safe_load(
        (PATH_ROOT / ".github/workflows/tests.yaml").read_text(encoding="utf-8")
    )
    set_matrix = set(dict_workflow["jobs"]["test"]["strategy"]["matrix"]["python-version"])
    set_classified = {
        str_cls.removeprefix("Programming Language :: Python :: ")
        for str_cls in list_classifiers
        if str_cls.startswith(STR_PY_PREFIX)
    }
    assert set_classified == set_matrix


def test_classifiers_development_status_is_stable(list_classifiers: list[str]) -> None:
    """The package advertises itself as production/stable.

    Parameters
    ----------
    list_classifiers : list[str]
        The declared trove classifiers.
    """
    list_status = [str_cls for str_cls in list_classifiers if str_cls.startswith("Development")]
    assert list_status == ["Development Status :: 5 - Production/Stable"]


def test_wheel_ships_py_typed_marker(list_wheel_names: list[str]) -> None:
    """The PEP 561 marker is inside the built wheel.

    Parameters
    ----------
    list_wheel_names : list[str]
        Member paths inside the built wheel.
    """
    assert "layouts_cvm/py.typed" in list_wheel_names
