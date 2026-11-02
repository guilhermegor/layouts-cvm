"""Shared building blocks of the CVM XML submission writers.

Pure functions (plus the one atomic file write at the edge) that turn a validated pydantic
document into the windows-1252 XML the CVM portal expects. A schema declares its fields in XML
order and names them after their tag, so the serialiser is one recursive walk over
``model_fields``: a ``None`` is omitted, a nested model is a block and a list repeats its element.
"""

from decimal import Decimal
from xml.etree import ElementTree as ET  # noqa: S405

from layouts_cvm._internal.utils.typing import type_checker
from pydantic import BaseModel

from layouts_cvm._internal.utils.atomic_write import atomic_write_bytes


ENCODING = "windows-1252"
DECLARATION = f'<?xml version="1.0" encoding="{ENCODING}"?>\n'
INDENT = "    "


@type_checker
def scalar_text(value: Decimal | int | str) -> str:
    """Render one scalar the way the pages require: comma decimal separator, no filler zeros.

    Parameters
    ----------
    value : Decimal | int | str
        The field value, already scaled by the schema.

    Returns
    -------
    str
        The element text.
    """
    return format(value, "f").replace(".", ",") if isinstance(value, Decimal) else str(value)


@type_checker
def append_field(parent: ET.Element, name: str, value: object) -> None:
    """Append one field to ``parent`` as an element, or as repeated elements for a list.

    Parameters
    ----------
    parent : ET.Element
        The enclosing block.
    name : str
        The schema field name; its upper case is the XML tag.
    value : object
        ``None`` (omitted), a nested model, a list of either, or a scalar.
    """
    list_values = value if isinstance(value, list) else [value]
    for item in [item for item in list_values if item is not None]:
        _append_item(parent, name, item)


@type_checker
def _append_item(parent: ET.Element, name: str, item: object) -> None:
    """Append one non-empty value as a ``name.upper()`` element.

    Parameters
    ----------
    parent : ET.Element
        The enclosing block.
    name : str
        The schema field name.
    item : object
        A nested model (becomes a block) or a scalar (becomes the element text).
    """
    element = ET.SubElement(parent, name.upper())
    list_fields = list(type(item).model_fields) if isinstance(item, BaseModel) else []
    element.text = None if isinstance(item, BaseModel) else scalar_text(item)
    for field in list_fields:
        append_field(element, field, getattr(item, field))


@type_checker
def render_xml(root: ET.Element) -> tuple[str, bytes]:
    """Indent ``root`` and encode it, proving the bytes are well-formed XML.

    The text is encoded and re-parsed before any destination is opened, so a failure never
    truncates an existing file.

    Parameters
    ----------
    root : ET.Element
        The document element.

    Returns
    -------
    tuple of (str, bytes)
        The XML text and its windows-1252 payload.

    Raises
    ------
    ValueError
        If the text holds a character windows-1252 cannot encode or XML cannot carry.
    """
    ET.indent(root, space=INDENT)
    xml_str = DECLARATION + ET.tostring(root, encoding="unicode") + "\n"
    try:
        payload = xml_str.encode(ENCODING)
        ET.fromstring(payload)  # noqa: S314  # well-formedness self-check of our own output
    except (UnicodeEncodeError, ET.ParseError) as exc:
        raise ValueError(f"document cannot be serialised as {ENCODING} XML: {exc}") from exc
    return xml_str, payload


@type_checker
def deliver(xml_str: str, payload: bytes, output_path: str | None) -> str | None:
    """Return the XML text, or write the payload atomically and return ``None``.

    Parameters
    ----------
    xml_str : str
        The serialised document.
    payload : bytes
        The same document, windows-1252 encoded.
    output_path : str, optional
        Destination file. When given the payload is written there.

    Returns
    -------
    str or None
        ``xml_str`` when ``output_path`` is ``None``, else ``None``.
    """
    if output_path is None:
        return xml_str
    atomic_write_bytes(output_path, payload)
    return None
