"""Unit tests for the shared schema field helpers."""

from pydantic import ValidationError
import pytest

from layouts_cvm._internal.config.schemas._fields import validated_competence
from layouts_cvm._internal.config.schemas.inf_mensal_fidc import InfMensalFidcHeader
from layouts_cvm._internal.config.schemas.inf_mensal_fidc_489 import InfMensalFidc489Header


@pytest.mark.parametrize("str_value", ["01/2026", "12/1999"])
def test_validated_competence_valid_value_returns_it_unchanged(str_value: str) -> None:
    """A valid MM/AAAA competence is returned as given.

    Parameters
    ----------
    str_value : str
        A valid competence.
    """
    assert validated_competence(str_value) == str_value


@pytest.mark.parametrize("str_value", ["13/2026", "00/2026", "2026/06", "6/2026", "06-2026", ""])
def test_validated_competence_invalid_value_names_the_format(str_value: str) -> None:
    """An invalid month or wrong shape raises with the MM/AAAA message.

    Parameters
    ----------
    str_value : str
        An invalid competence.
    """
    with pytest.raises(ValueError, match="expected MM/AAAA"):
        validated_competence(str_value)


@pytest.mark.parametrize("cls_header", [InfMensalFidcHeader, InfMensalFidc489Header])
def test_fidc_header_model_validate_rejects_an_impossible_month(cls_header: type) -> None:
    """Validating a FIDC header with month 13 fails on ``dt_compt`` with the MM/AAAA message.

    Parameters
    ----------
    cls_header : type
        A FIDC header model.
    """
    with pytest.raises(ValidationError, match=r"dt_compt\n  Value error, expected MM/AAAA"):
        cls_header.model_validate({"dt_compt": "13/2026"})
