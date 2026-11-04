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


SinteticoDocument = (
    InformeSinteticoFcceDocument
    | InformeSinteticoFitvmDocument
    | InformeSinteticoFicDocument
    | InformeSinteticoOutrosDocument
)

_DOCUMENTS_BY_COD_DOC = {
    5: InformeSinteticoFcceDocument,
    7: InformeSinteticoFitvmDocument,
    8: InformeSinteticoFicDocument,
    9: InformeSinteticoOutrosDocument,
}


@type_checker
def _resolve_document(doc: SinteticoDocument | Mapping[str, object]) -> SinteticoDocument:
    """Return ``doc`` as a validated variant document, picking the variant from ``COD_DOC``.

    Parameters
    ----------
    doc : SinteticoDocument or Mapping
            A built model (passes through), or plain data whose ``header.cod_doc`` is 5, 7, 8
            or 9.

    Returns
    -------
    SinteticoDocument
            The validated document.

    Raises
    ------
    ValueError
            If a mapping carries no ``header.cod_doc`` of 5, 7, 8 or 9.
    """
    if not isinstance(doc, Mapping):
        return doc
    header = doc.get("header")
    cod_doc = header.get("cod_doc") if isinstance(header, Mapping) else None
    if cod_doc not in _DOCUMENTS_BY_COD_DOC:
        raise ValueError(
            f"header.cod_doc must be one of {sorted(_DOCUMENTS_BY_COD_DOC)}, got {cod_doc!r}"
        )
    return coerce_document(_DOCUMENTS_BY_COD_DOC[cod_doc], doc)


class InformeSintetico(SubmissionWriter[SinteticoDocument]):
    """Serialize a validated Informe Sintético document (any of the four variants) to XML.

    Methods
    -------
    export(doc, output_path)
            Serialize a validated document to windows-1252 XML.
    """

    def export(
        self, doc: SinteticoDocument | Mapping[str, object], output_path: str | None = None
    ) -> str | None:
        """Serialize a validated Informe Sintético document to CVM-compliant XML.

        Parameters
        ----------
        doc : SinteticoDocument or Mapping
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
