"""Shared building blocks of the CVM XML submission writers.

Pure functions (plus the one atomic file write at the edge) that turn a validated pydantic
document into the windows-1252 XML the CVM portal expects. A schema declares its fields in XML
order and names them after their tag, so the serialiser is one recursive walk over
``model_fields``: a ``None`` is omitted, a nested model is a block and a list repeats its element.
"""

from collections.abc import Mapping
from decimal import Decimal
from typing import TypeAlias, TypeVar
from xml.etree import ElementTree as ET  # noqa: S405

from pydantic import BaseModel
from pydantic.fields import FieldInfo

from layouts_cvm._internal.utils.atomic_write import atomic_write_bytes
from layouts_cvm._internal.utils.typing import type_checker


ENCODING = "windows-1252"
DECLARATION = f'<?xml version="1.0" encoding="{ENCODING}"?>\n'
INDENT = "    "

DocModel: TypeAlias = BaseModel
FieldMeta: TypeAlias = FieldInfo

TDocument = TypeVar("TDocument", bound=BaseModel)


@type_checker
def coerce_document(
    cls_document: type[TDocument], doc: TDocument | Mapping[str, object]
) -> TDocument:
    """Return ``doc`` as a validated ``cls_document``, validating a mapping on the way in.

    An already-built model passes through untouched (it was validated on construction, and
    re-running its validators could reject a deliberately hand-built one), so a mapping and
    its model serialise to identical bytes.

    Parameters
    ----------
    cls_document : type[TDocument]
        The document model the writer serialises.
    doc : TDocument or Mapping
        A built model, or plain data to validate into one.

    Returns
    -------
    TDocument
        The validated document.

    Raises
    ------
    TypeError
        If ``doc`` is a model of another class.
    """
    _reject_foreign_model(cls_document, doc)
    return doc if isinstance(doc, cls_document) else cls_document.model_validate(doc)


@type_checker
def _reject_foreign_model(cls_document: type[BaseModel], doc: object) -> None:
    """Refuse a built model of the wrong class with a ``TypeError``.

    A writer generic over its document type is only checked against the TypeVar's bound, so
    this restores the error a concretely annotated ``export`` raises for the wrong document.

    Parameters
    ----------
    cls_document : type[BaseModel]
        The document model the writer serialises.
    doc : object
        The value handed to the writer.

    Raises
    ------
    TypeError
        If ``doc`` is a ``BaseModel`` that is not a ``cls_document``.
    """
    if isinstance(doc, BaseModel) and not isinstance(doc, cls_document):
        raise TypeError(f"expected {cls_document.__name__}, got {type(doc).__name__}")


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


@type_checker
def fill_children(node: ET.Element, list_pairs: list[tuple[str, str]]) -> None:
    """Append one text child per ``(tag, text)`` pair, in order.

    Parameters
    ----------
    node : ET.Element
        The parent element.
    list_pairs : list of tuple of (str, str)
        Child tag and text.
    """
    for tag, text in list_pairs:
        ET.SubElement(node, tag).text = text


@type_checker
def deliver_text(xml_str: str, output_path: str | None) -> str | None:
    """Return the XML text, or write it as windows-1252 and return ``None``.

    Unlike :func:`deliver`, nothing is encoded or re-parsed unless a file is written.

    Parameters
    ----------
    xml_str : str
        The serialised document.
    output_path : str, optional
        Destination file.

    Returns
    -------
    str or None
        ``xml_str`` when ``output_path`` is ``None``, else ``None``.
    """
    return (
        deliver(xml_str, xml_str.encode(ENCODING), output_path)
        if output_path is not None
        else xml_str
    )
