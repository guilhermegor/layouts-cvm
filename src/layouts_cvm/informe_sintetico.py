"""CVM Informe Sintético — submission (envio) writer for the four fund-type variants.

Produces the Informe Sintético XML (``COD_DOC`` 5, 7, 8 or 9) from a validated variant document.
The four pages share one shape (``DOC_ARQ`` > ``DESC_ADM`` + ``INFORME_SINTETICO`` >
``ROW_INFORME``) and no namespace; only the blocks inside each row differ, and the schemas carry
that, so one writer serves all four. Pure logic plus file I/O at the edges — no network.
"""

from collections.abc import Mapping
from xml.etree import ElementTree as ET  # noqa: S405  # builds XML, never parses untrusted input

from layouts_cvm._internal.config.ports.submission_writer import SubmissionWriter
from layouts_cvm._internal.config.schemas.informe_sintetico import (
    InformeSinteticoFcceDocument,
    InformeSinteticoFicDocument,
    InformeSinteticoFitvmDocument,
    InformeSinteticoOutrosDocument,
)
from layouts_cvm._internal.utils.typing import type_checker
from layouts_cvm._internal.utils.xml_writer import (
    append_field,
    coerce_document,
    deliver,
    render_xml,
)


_SinteticoDocument = (
    InformeSinteticoFcceDocument
    | InformeSinteticoFitvmDocument
    | InformeSinteticoFicDocument
    | InformeSinteticoOutrosDocument
)

_DOCUMENTS_BY_COD_DOC: dict[tuple[type, object], type] = {
    (int, 5): InformeSinteticoFcceDocument,
    (int, 7): InformeSinteticoFitvmDocument,
    (int, 8): InformeSinteticoFicDocument,
    (int, 9): InformeSinteticoOutrosDocument,
}


@type_checker
def _read_cod_doc(doc: Mapping[str, object]) -> object:
    """Return ``doc["header"]["cod_doc"]``, or ``None`` when the header is missing."""
    header = doc.get("header")
    return header.get("cod_doc") if isinstance(header, Mapping) else None


@type_checker
def _pick_document_class(cod_doc: object) -> type:
    """Return the document class for ``cod_doc``; numeric look-alikes of 5/7/8/9 are refused."""
    cls_document = _DOCUMENTS_BY_COD_DOC.get((type(cod_doc), cod_doc))
    if cls_document is None:
        raise ValueError(f"header.cod_doc must be one of 5, 7, 8 or 9, got {cod_doc!r}")
    return cls_document


@type_checker
def _resolve_document(doc: _SinteticoDocument | Mapping[str, object]) -> _SinteticoDocument:
    """Return ``doc`` as a validated variant document, picking the variant from ``COD_DOC``.

    Parameters
    ----------
    doc : _SinteticoDocument or Mapping
            A built model (passes through), or plain data whose ``header.cod_doc`` is 5, 7, 8
            or 9.

    Returns
    -------
    _SinteticoDocument
            The validated document.

    Raises
    ------
    ValueError
            If a mapping carries no ``header.cod_doc`` of 5, 7, 8 or 9.
    """
    if not isinstance(doc, Mapping):
        return doc
    return coerce_document(_pick_document_class(_read_cod_doc(doc)), doc)


class InformeSintetico(SubmissionWriter[_SinteticoDocument]):
    """Serialize a validated Informe Sintético document (any of the four variants) to XML.

    Methods
    -------
    export(doc, output_path)
            Serialize a validated document to windows-1252 XML.
    """

    def export(
        self, doc: _SinteticoDocument | Mapping[str, object], output_path: str | None = None
    ) -> str | None:
        """Serialize a validated Informe Sintético document to CVM-compliant XML.

        Parameters
        ----------
        doc : _SinteticoDocument or Mapping
                A variant document model, or plain data whose ``header.cod_doc`` (5 FCCE,
                7 FITVM, 8 FIC-FITVM, 9 Outros) selects the variant to validate it into.
        output_path : Optional[str]
                Destination file path, written atomically as windows-1252. If given, None is
                returned; otherwise the XML string is returned, by default None.

        Returns
        -------
        Optional[str]
                XML string when output_path is None, else None.
        """
        document = _resolve_document(doc)
        root = ET.Element("DOC_ARQ")
        append_field(root, "desc_adm", document.header)
        rows = ET.SubElement(root, "INFORME_SINTETICO")
        append_field(rows, "row_informe", list(document.rows))
        xml_str, payload = render_xml(root)
        return deliver(xml_str, payload, output_path)
