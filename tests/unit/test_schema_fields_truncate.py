"""Unit tests for the shared decimal truncation in ``_internal.config.schemas._fields``."""

from decimal import Decimal

import pytest

from layouts_cvm._internal.config.schemas._fields import truncate_to_scale


@pytest.mark.parametrize("value", ["Infinity", "-Infinity", "1e30", "12345678901234567"])
def test_unrepresentable_value_raises_value_error(value: str) -> None:
    """Raise ValueError, which Pydantic wraps, not a raw decimal.InvalidOperation."""
    with pytest.raises(ValueError, match="invalid decimal value"):
        truncate_to_scale(12)(value)


@pytest.mark.parametrize("value", ["-0.001", "-0.00001", Decimal("-0.009")])
def test_truncated_zero_is_unsigned(value: str | Decimal) -> None:
    """Return 0.00, never -0.00, when truncation takes a small negative value to zero."""
    assert str(truncate_to_scale(2)(value)) == "0.00"
