"""Unit tests for the shared schema field helpers."""

from pydantic import ValidationError
import pytest

from layouts_cvm._internal.config.schemas._fields import (
    validated_br_date,
    validated_competence,
)
from layouts_cvm._internal.config.schemas.cda import CdaHeader
from layouts_cvm._internal.config.schemas.inf_mensal_fidc import InfMensalFidcHeader
from layouts_cvm._internal.config.schemas.inf_mensal_fidc_489 import InfMensalFidc489Header
from layouts_cvm._internal.config.schemas.informe_art12_res33 import DsInform
from layouts_cvm._internal.config.schemas.informe_diario import (
    InformeDiarioHeader,
    InformeDiarioInform,
)
from layouts_cvm._internal.config.schemas.informe_diario_v1 import InformeDiarioV1Header
from layouts_cvm._internal.config.schemas.informe_portabilidade import (
    PortabilidadeHeader,
    PortabilidadeInform,
)
from layouts_cvm._internal.config.schemas.perfil_mensal import DocumentHeader
from layouts_cvm._internal.config.schemas.perfil_mensal_739 import PerfilMensal739Header


LIST_COMPETENCE_FIELDS_NO_MODEL_CHECK = [
    (CdaHeader, "dt_compt"),
    (DocumentHeader, "dt_compt"),
    (PerfilMensal739Header, "dt_compt"),
    (DsInform, "dt_compt"),
    (PortabilidadeHeader, "dt_compt"),
    (PortabilidadeInform, "dt_event"),
]
LIST_COMPETENCE_FIELDS_ALL = [
    *LIST_COMPETENCE_FIELDS_NO_MODEL_CHECK,
    (InfMensalFidcHeader, "dt_compt"),
    (InfMensalFidc489Header, "dt_compt"),
]


@pytest.mark.parametrize("str_value", ["01/2026", "12/1999"])
def test_validated_competence_valid_value_returns_it_unchanged(str_value: str) -> None:
    """A valid MM/AAAA competence is returned as given.

    Parameters
    ----------
    str_value : str
        A valid competence.
    """
    assert validated_competence(str_value) == str_value


@pytest.mark.parametrize(
    "str_value",
    [
        "13/2026",
        "00/2026",
        "2026/06",
        "6/2026",
        "06-2026",
        "",
        "06/2026\n",
        "06/\u0662\u0660\u0662\u0666",
    ],
)
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


@pytest.mark.parametrize(("cls_model", "str_field"), LIST_COMPETENCE_FIELDS_ALL)
@pytest.mark.parametrize("str_value", ["13/2026", "00/2026", "01/0000"])
def test_competence_field_rejects_invalid_value_with_the_shared_message(
    cls_model: type, str_field: str, str_value: str
) -> None:
    """Every MM/AAAA field refuses a bad month or year ``0000`` with one message.

    Parameters
    ----------
    cls_model : type
        A model that owns a competence field.
    str_field : str
        The competence field name.
    str_value : str
        An invalid competence.
    """
    with pytest.raises(ValidationError, match=rf"{str_field}\n  Value error, expected MM/AAAA"):
        cls_model.__pydantic_validator__.validate_assignment(
            cls_model.model_construct(), str_field, str_value
        )


@pytest.mark.parametrize(("cls_model", "str_field"), LIST_COMPETENCE_FIELDS_NO_MODEL_CHECK)
@pytest.mark.parametrize("str_value", ["01/2026", "12/2026"])
def test_competence_field_accepts_valid_value(
    cls_model: type, str_field: str, str_value: str
) -> None:
    """Every MM/AAAA field accepts the first and last month of a year.

    Parameters
    ----------
    cls_model : type
        A model that owns a competence field.
    str_field : str
        The competence field name.
    str_value : str
        A valid competence.
    """
    cls_result = cls_model.__pydantic_validator__.validate_assignment(
        cls_model.model_construct(), str_field, str_value
    )
    assert getattr(cls_result, str_field) == str_value


@pytest.mark.parametrize("str_value", ["15/06/2026", "29/02/2024"])
def test_validated_br_date_valid_shape_returns_it_unchanged(str_value: str) -> None:
    """A DD/MM/AAAA date that exists on the calendar is returned as given.

    Parameters
    ----------
    str_value : str
        A well-shaped, existing date.
    """
    assert validated_br_date(str_value) == str_value


@pytest.mark.parametrize(
    "str_value", ["2026-06-15", "1/06/2026", "15/06/26", "15/06/2026\n", "١٥/06/2026"]
)
def test_validated_br_date_invalid_shape_names_the_format(str_value: str) -> None:
    """A wrong shape, a trailing newline or non-ASCII digits raise the shared message.

    Parameters
    ----------
    str_value : str
        A badly shaped date.
    """
    with pytest.raises(ValueError, match="expected DD/MM/AAAA"):
        validated_br_date(str_value)


@pytest.mark.parametrize("str_value", ["31/02/2026", "29/02/2025", "15/13/2026"])
def test_validated_br_date_nonexistent_day_raises(str_value: str) -> None:
    """A well-shaped date naming a day that does not exist is refused.

    Parameters
    ----------
    str_value : str
        A DD/MM/AAAA text with no matching calendar day.
    """
    with pytest.raises(ValueError, match="no such calendar day"):
        validated_br_date(str_value)


LIST_DIARIO_DATE_FIELDS = [
    (InformeDiarioHeader, "dt_compt"),
    (InformeDiarioHeader, "dt_gerac_arq"),
    (InformeDiarioInform, "data_prox_pl"),
    (InformeDiarioV1Header, "dt_compt"),
    (InformeDiarioV1Header, "dt_gerac_arq"),
]


@pytest.mark.parametrize(("cls_model", "str_field"), LIST_DIARIO_DATE_FIELDS)
@pytest.mark.parametrize("str_value", ["1/06/2026", "15/06/2026\n", "\u0661\u0665/06/2026"])
def test_informe_diario_date_invalid_shape_uses_the_shared_message(
    cls_model: type, str_field: str, str_value: str
) -> None:
    """Each informe diario date field refuses a wrong shape with the shared message.

    Parameters
    ----------
    cls_model : type
        The informe diario model under test.
    str_field : str
        The date field name.
    str_value : str
        A badly shaped date.
    """
    with pytest.raises(ValidationError, match="expected DD/MM/AAAA"):
        cls_model.__pydantic_validator__.validate_assignment(
            cls_model.model_construct(), str_field, str_value
        )


@pytest.mark.parametrize(("cls_model", "str_field"), LIST_DIARIO_DATE_FIELDS)
def test_informe_diario_date_nonexistent_day_uses_the_shared_message(
    cls_model: type, str_field: str
) -> None:
    """Each informe diario date field refuses a day missing from the calendar.

    Parameters
    ----------
    cls_model : type
        The informe diario model under test.
    str_field : str
        The date field name.
    """
    with pytest.raises(ValidationError, match="no such calendar day"):
        cls_model.__pydantic_validator__.validate_assignment(
            cls_model.model_construct(), str_field, "31/02/2026"
        )


LIST_DIARIO_HEADER_DATE_FIELDS = [
    (cls_model, str_field)
    for cls_model, str_field in LIST_DIARIO_DATE_FIELDS
    if cls_model is not InformeDiarioInform
]


def test_informe_diario_data_prox_pl_accepts_a_real_day() -> None:
    """``data_prox_pl`` accepts an existing day on an inform that names its subclass."""
    cls_result = InformeDiarioInform.__pydantic_validator__.validate_assignment(
        InformeDiarioInform.model_construct(cod_subclasse="SUB1"), "data_prox_pl", "15/06/2026"
    )
    assert cls_result.data_prox_pl == "15/06/2026"


@pytest.mark.parametrize(("cls_model", "str_field"), LIST_DIARIO_HEADER_DATE_FIELDS)
def test_informe_diario_date_accepts_a_real_day(cls_model: type, str_field: str) -> None:
    """Each informe diario date field accepts an existing DD/MM/AAAA day.

    Parameters
    ----------
    cls_model : type
        The informe diario model under test.
    str_field : str
        The date field name.
    """
    cls_result = cls_model.__pydantic_validator__.validate_assignment(
        cls_model.model_construct(), str_field, "15/06/2026"
    )
    assert getattr(cls_result, str_field) == "15/06/2026"
