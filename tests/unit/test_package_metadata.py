"""Guard the packaging metadata a consumer's type checker and PyPI page rely on."""

from pathlib import Path
import shutil
import subprocess
import zipfile

import pytest
import yaml


PATH_ROOT = Path(__file__).resolve().parents[2]
STR_PY_PREFIX = "Programming Language :: Python :: "
STR_CLASSIFIER_LINE = "Classifier: "


@pytest.fixture(scope="module")  # fixture-scope-ok: one poetry build shared by read-only asserts
def path_wheel(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build the wheel once for the module.

    Parameters
    ----------
    tmp_path_factory : pytest.TempPathFactory
        Factory for the build output directory.

    Returns
    -------
    pathlib.Path
        The built wheel.
    """
    path_out = tmp_path_factory.mktemp("wheel")
    str_poetry = shutil.which("poetry")
    assert str_poetry is not None, "poetry is not on PATH"
    cls_build = subprocess.run(  # noqa: S603
        [str_poetry, "build", "-f", "wheel", "--output", str(path_out)],
        cwd=PATH_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert cls_build.returncode == 0, f"poetry build failed:\n{cls_build.stderr}"
    list_wheels = list(path_out.glob("*.whl"))
    assert len(list_wheels) == 1, f"expected one wheel in {path_out}, found {list_wheels}"
    return list_wheels[0]


@pytest.fixture
def list_classifiers(path_wheel: Path) -> list[str]:
    """Read the classifiers PyPI will publish, from the wheel's METADATA.

    Parameters
    ----------
    path_wheel : pathlib.Path
        The built wheel.

    Returns
    -------
    list[str]
        The published trove classifiers.
    """
    with zipfile.ZipFile(path_wheel) as cls_zip:
        str_member = next(
            str_name for str_name in cls_zip.namelist() if str_name.endswith(".dist-info/METADATA")
        )
        str_metadata = cls_zip.read(str_member).decode("utf-8")
    return [
        str_line.removeprefix(STR_CLASSIFIER_LINE)
        for str_line in str_metadata.splitlines()
        if str_line.startswith(STR_CLASSIFIER_LINE)
    ]


def test_classifiers_python_versions_equal_tests_matrix(list_classifiers: list[str]) -> None:
    """Every CI-tested Python version is a published classifier, and no other is.

    Parameters
    ----------
    list_classifiers : list[str]
        The published trove classifiers.
    """
    dict_workflow = yaml.safe_load(
        (PATH_ROOT / ".github/workflows/tests.yaml").read_text(encoding="utf-8")
    )
    set_matrix = set(dict_workflow["jobs"]["test"]["strategy"]["matrix"]["python-version"])
    set_classified = {
        str_cls.removeprefix(STR_PY_PREFIX)
        for str_cls in list_classifiers
        if str_cls.startswith(STR_PY_PREFIX + "3.")
    }
    assert set_classified == set_matrix


def test_classifiers_development_status_is_stable(list_classifiers: list[str]) -> None:
    """The package advertises itself as production/stable.

    Parameters
    ----------
    list_classifiers : list[str]
        The published trove classifiers.
    """
    list_status = [str_cls for str_cls in list_classifiers if str_cls.startswith("Development")]
    assert list_status == ["Development Status :: 5 - Production/Stable"]


def test_wheel_ships_py_typed_marker(path_wheel: Path) -> None:
    """The PEP 561 marker is inside the built wheel.

    Parameters
    ----------
    path_wheel : pathlib.Path
        The built wheel.
    """
    with zipfile.ZipFile(path_wheel) as cls_zip:
        list_names = cls_zip.namelist()
    assert "layouts_cvm/py.typed" in list_names
