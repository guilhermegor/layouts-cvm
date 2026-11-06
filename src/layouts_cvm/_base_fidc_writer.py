"""Private shared XML builder for the Informe Mensal FIDC submission writers.

Holds the schema-driven block walk and the ``export`` template that ``InfMensalFidc`` (ICVM
576) and ``InfMensalFidc489`` both render through, so neither public writer subclasses the
other. A writer names its document model once, as the base's generic argument. Not part of
the public API.
"""

from collections.abc import Iterator, Mapping
from decimal import Decimal
from typing import ClassVar, get_args
from xml.sax.saxutils import escape

from layouts_cvm._internal.config.ports.submission_writer import SubmissionWriter, TDoc
from layouts_cvm._internal.utils.atomic_write import atomic_write_bytes
from layouts_cvm._internal.utils.typing import type_checker
from layouts_cvm._internal.utils.xml_writer import DocModel, FieldMeta, coerce_document


_INDENT = "    "


@type_checker
def _declared_models(cls: type) -> Iterator[type[DocModel]]:
    """Yield the document models a class names in its own generic bases.

    Parameters
    ----------
    cls : type
            The class whose own ``__orig_bases__`` are read; inherited ones are ignored.

    Returns
    -------
    Iterator[type[DocModel]]
            Every generic argument that is a ``DocModel`` subclass, in base order.
    """
    return (
        arg
        for base in cls.__dict__.get("__orig_bases__", ())
        for arg in get_args(base)
        if isinstance(arg, type) and issubclass(arg, DocModel)
    )


class _BaseFidcWriter(SubmissionWriter[TDoc]):
    """Shared Informe Mensal FIDC XML builder; subclasses set ``_document_model``.

    Methods
    -------
    export(doc, output_path)
            Serialize a validated document to a CVM-compliant XML string or file.
    """

    _document_model: ClassVar[type[DocModel]]

    def __init_subclass__(cls, **kwargs: object) -> None:
        """Derive ``_document_model`` from the subclass's generic argument.

        Parameters
        ----------
        **kwargs : object
                Forwarded to ``type.__init_subclass__``.

        A subclass of a concrete writer that names no generic argument of its own inherits
        its parent's model.

        Raises
        ------
        TypeError
                If neither the subclass nor a parent names a document model.
        """
        super().__init_subclass__(**kwargs)
        type_model = next(_declared_models(cls), getattr(cls, "_document_model", None))
        if type_model is None:
            raise TypeError(f"{cls.__name__} must parametrize _BaseFidcWriter with a DocModel")
        cls._document_model = type_model

    def export(
        self, doc: TDoc | Mapping[str, object], output_path: str | None = None
    ) -> str | None:
        """Serialize a validated document to a CVM-compliant XML string.

        Produces UTF-8 text internally; when output_path is given the file is
        written atomically with windows-1252 encoding as required by CVM.

        Parameters
        ----------
        doc : TDoc or Mapping
                Validated document model, or plain data to validate into one.
        output_path : Optional[str]
                Destination file path. If provided, the file is written and None is
                returned; otherwise the XML string is returned, by default None.

        Returns
        -------
        Optional[str]
                XML string when output_path is None, else None.
        """
        document = coerce_document(self._document_model, doc)
        lines = ['<?xml version="1.0" encoding="windows-1252"?>', '<DOC_ARQ xmlns="urn:fidc">']
        lines.extend(self._block_lines(document, 1))
        lines.append("</DOC_ARQ>")
        xml_str = "\n".join(lines)
        if output_path is not None:
            atomic_write_bytes(output_path, xml_str.encode("windows-1252"))
            return None
        return xml_str

    def _block_lines(self, block: DocModel, depth: int) -> list[str]:
        """Emit the child elements of a block, in schema field order.

        Parameters
        ----------
        block : DocModel
                The block whose fields are emitted.
        depth : int
                Indentation depth of the children.

        Returns
        -------
        list[str]
                XML lines; ``None`` fields are omitted (optional tags).
        """
        return [
            line
            for tag, item, scale in self._items(block)
            for line in self._element_lines(tag, item, scale, depth)
        ]

    def _items(self, block: DocModel) -> list[tuple[str, object, int]]:
        """List ``(tag, item, scale)`` for every set field of a block, lists flattened.

        Parameters
        ----------
        block : DocModel
            The block whose fields are listed.

        Returns
        -------
        list of tuple
            One entry per element to emit, in schema field order.
        """
        return [
            (info.alias or name.upper(), item, self._scale(info))
            for name, info in type(block).model_fields.items()
            if getattr(block, name) is not None
            for item in self._as_list(getattr(block, name))
        ]

    @staticmethod
    def _as_list(value: object) -> list[object]:
        """Wrap a scalar or block in a list; pass a list through.

        Parameters
        ----------
        value : object
            A field value.

        Returns
        -------
        list
            The repetitions of the element.
        """
        return value if isinstance(value, list) else [value]

    def _element_lines(self, tag: str, item: object, scale: int, depth: int) -> list[str]:
        """Emit one element: a nested block or a leaf value.

        Parameters
        ----------
        tag : str
                Element name.
        item : object
                A block (``DocModel``) or a leaf (``Decimal``, ``int``, ``str``).
        scale : int
                Decimal places for a ``Decimal`` leaf.
        depth : int
                Indentation depth of the element.

        Returns
        -------
        list[str]
                XML lines for the element.
        """
        pad = _INDENT * depth
        if isinstance(item, DocModel):
            return self._wrap(tag, self._block_lines(item, depth + 1), pad)
        text = self._fmt_decimal(item, scale) if isinstance(item, Decimal) else escape(str(item))
        return [f"{pad}<{tag}>{text}</{tag}>"]

    @staticmethod
    def _wrap(tag: str, children: list[str], pad: str) -> list[str]:
        """Wrap child lines in their tag; an empty block is written inline.

        Parameters
        ----------
        tag : str
            Element name.
        children : list[str]
            Already indented child lines.
        pad : str
            Indentation of the element.

        Returns
        -------
        list[str]
            XML lines for the element.
        """
        return (
            [f"{pad}<{tag}>", *children, f"{pad}</{tag}>"]
            if children
            else [f"{pad}<{tag}></{tag}>"]
        )

    @staticmethod
    def _scale(info: FieldMeta) -> int:
        """Find the ``decimal_places`` a field was declared with.

        ``Money | None`` keeps its constraints inside the union member (as a nested
        ``FieldMeta``), not on the field, so those are searched too.

        Parameters
        ----------
        info : FieldMeta
                The field's declaration.

        Returns
        -------
        int
                Declared decimal places, or 0 for a non-decimal field.
        """
        metadata = [
            *info.metadata,
            *[
                inner
                for member in get_args(info.annotation)
                for meta in getattr(member, "__metadata__", ())
                for inner in (meta.metadata if isinstance(meta, FieldMeta) else [meta])
            ],
        ]
        return next((m.decimal_places for m in metadata if hasattr(m, "decimal_places")), 0)

    @staticmethod
    def _fmt_decimal(value: Decimal, places: int) -> str:
        """Format a Decimal for CVM XML output (comma as decimal separator).

        Parameters
        ----------
        value : Decimal
                Numeric value.
        places : int
                Number of decimal places.

        Returns
        -------
        str
                Formatted string (e.g. '12,34').
        """
        return f"{value:.{places}f}".replace(".", ",")
