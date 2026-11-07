"""Guard the docs dark-scheme link colours against the WCAG AA contrast floor."""

import colorsys
from pathlib import Path
import re

import pytest


PATH_BRAND_CSS = Path(__file__).resolve().parents[2] / "docs" / "stylesheets" / "brand.css"
FLOAT_MIN_CONTRAST = 4.5
TUPLE_SLATE_BG_RGB = colorsys.hls_to_rgb(232 / 360, 0.14, 0.15)
RE_HEX_DECL = re.compile(r"(--[\w-]+):\s*(#[0-9a-fA-F]{6})")
DICT_MATERIAL_FALLBACK = {
    "--md-typeset-a-color": "--md-primary-fg-color",
    "--md-accent-fg-color": "#526cfe",
}
RE_SLATE_BLOCK = re.compile(r'\[data-md-color-scheme="slate"\]\s*\{([^}]*)\}')


def _channel_to_linear(float_channel: float) -> float:
    """Convert one sRGB channel in [0, 1] to linear light.

    Only the gamma branch is implemented: the linear toe below 0.03928 is never reached
    by the colours under test, and a second branch would break the complexity cap.

    Parameters
    ----------
    float_channel : float
        The sRGB channel value.

    Returns
    -------
    float
        The linearised channel value.
    """
    return ((float_channel + 0.055) / 1.055) ** 2.4


def _luminance(tuple_rgb: tuple[float, float, float]) -> float:
    """Return the WCAG relative luminance of an RGB triple.

    Parameters
    ----------
    tuple_rgb : tuple[float, float, float]
        The sRGB channels, each in [0, 1].

    Returns
    -------
    float
        The relative luminance.
    """
    float_r, float_g, float_b = (_channel_to_linear(float_c) for float_c in tuple_rgb)
    return 0.2126 * float_r + 0.7152 * float_g + 0.0722 * float_b


def _slate_contrast(str_var: str) -> float:
    """Return the contrast of a slate CSS variable against the slate background.

    Parameters
    ----------
    str_var : str
        The custom property name, e.g. ``--md-typeset-a-color``.

    Returns
    -------
    float
        The WCAG contrast ratio.
    """
    str_block = RE_SLATE_BLOCK.search(PATH_BRAND_CSS.read_text(encoding="utf-8")).group(1)
    dict_set = dict(RE_HEX_DECL.findall(str_block))
    str_hex = dict_set.get(str_var) or dict_set.get(
        DICT_MATERIAL_FALLBACK[str_var], DICT_MATERIAL_FALLBACK[str_var]
    )
    str_hex = str_hex.lstrip("#")
    tuple_fg = tuple(int(str_hex[i : i + 2], 16) / 255 for i in (0, 2, 4))
    float_hi, float_lo = sorted(
        (_luminance(tuple_fg), _luminance(TUPLE_SLATE_BG_RGB)), reverse=True
    )
    return (float_hi + 0.05) / (float_lo + 0.05)


@pytest.mark.parametrize("str_var", ["--md-typeset-a-color", "--md-accent-fg-color"])
def test_slate_link_colour_against_background_meets_wcag_aa(str_var: str) -> None:
    """Dark-scheme link and hover colours reach 4.5:1 on the slate background.

    Parameters
    ----------
    str_var : str
        The custom property under test.
    """
    assert _slate_contrast(str_var) >= FLOAT_MIN_CONTRAST
