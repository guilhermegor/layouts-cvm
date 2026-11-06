"""Guard the packaging metadata a consumer's type checker and PyPI page rely on."""

from email.parser import Parser
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib
import zipfile

import pytest
import yaml


PATH_ROOT = Path(__file__).resolve().parents[2]
STR_PY_PREFIX = "Programming Language :: Python :: "
RE_PROJECT_NAME = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?")


pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="poetry is not on the test process PATH on Windows CI; wheel METADATA is "
    "OS-independent and the Linux and macOS jobs build and check it",
)


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
def str_metadata(path_wheel: Path) -> str:
    """Read the wheel's ``*.dist-info/METADATA``, the file PyPI publishes from.

    Parameters
    ----------
    path_wheel : pathlib.Path
        The built wheel.

    Returns
    -------
    str
        The METADATA text.
    """
    with zipfile.ZipFile(path_wheel) as cls_zip:
        list_members = [
            str_name for str_name in cls_zip.namelist() if str_name.endswith(".dist-info/METADATA")
        ]
        assert len(list_members) == 1, (
            f"expected one METADATA in {path_wheel}, found {list_members}"
        )
        return cls_zip.read(list_members[0]).decode("utf-8")


@pytest.fixture
def list_classifiers(str_metadata: str) -> list[str]:
    """Read the classifiers PyPI will publish.

    Parameters
    ----------
    str_metadata : str
        The wheel's METADATA text.

    Returns
    -------
    list[str]
        The published trove classifiers.
    """
    return Parser().parsestr(str_metadata).get_all("Classifier", [])


def _canonical_name(str_requirement: str) -> str:
    """Return the PEP 503 normalised project name at the start of a requirement.

    Parameters
    ----------
    str_requirement : str
        A dependency key or a PEP 508 ``Requires-Dist`` value.

    Returns
    -------
    str
        The lower-cased name with runs of ``-``, ``_`` and ``.`` collapsed to ``-``.
    """
    re_match = RE_PROJECT_NAME.match(str_requirement)
    assert re_match is not None, f"no project name in {str_requirement!r}"
    return re.sub(r"[-_.]+", "-", re_match.group(0)).lower()


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


def test_wheel_requires_every_runtime_dependency(str_metadata: str) -> None:
    """Every runtime dependency in pyproject.toml is a ``Requires-Dist`` of the wheel.

    Parameters
    ----------
    str_metadata : str
        The wheel's METADATA text.
    """
    with (PATH_ROOT / "pyproject.toml").open("rb") as cls_file:
        dict_deps = tomllib.load(cls_file)["tool"]["poetry"]["dependencies"]
    set_required = {
        _canonical_name(str_req)
        for str_req in Parser().parsestr(str_metadata).get_all("Requires-Dist", [])
    }
    assert {_canonical_name(str_dep) for str_dep in dict_deps} - {"python"} <= set_required
