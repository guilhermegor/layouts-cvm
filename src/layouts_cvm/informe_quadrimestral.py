"""CVM Informe Quadrimestral (FIP) — submission (envio) writer.

Produces the Informe Quadrimestral V2 XML from a validated
:class:`InformeQuadrimestralDocument`. The schema declares its
fields in XML order and named after their tag, so the serialiser is one recursive walk over
``model_fields``: a ``None`` is omitted, a nested model is a block, a list repeats its element.
Pure logic plus file I/O at the edges — no network.
"""

from collections.abc import Mapping
from xml.etree import ElementTree as ET  # noqa: S405  # builds XML, never parses untrusted input

from layouts_cvm._internal.config.ports.submission_writer import SubmissionWriter
from layouts_cvm._internal.config.schemas.informe_quadrimestral import InformeQuadrimestralDocument
from layouts_cvm._internal.utils.xml_writer import (
    append_field,
    coerce_document,
    deliver,
    render_xml,
)


_NAMESPACE = "urn:inftrim"


class InformeQuadrimestral(SubmissionWriter[InformeQuadrimestralDocument]):
    """Serialize a validated Informe Quadrimestral V2 document to CVM-compliant XML.

    Concrete :class:`SubmissionWriter` for the Informe Quadrimestral V2 XML standard.

    Methods
    -------
    export(doc, output_path)
            Serialize a validated document to windows-1252 XML.
    """

    def export(
        self,
        doc: InformeQuadrimestralDocument | Mapping[str, object],
        output_path: str | None = None,
    ) -> str | None:
        """Serialize a validated document to a CVM-compliant XML string or file.

        The text is encoded and checked for well-formedness **before** the destination is
        opened, so a failure never truncates an existing file.

        Parameters
        ----------
        doc : InformeQuadrimestralDocument or Mapping
                Validated document model, or plain data to validate into one.
        output_path : Optional[str]
                Destination file. When given the file is written in windows-1252 and ``None`` is
                returned; otherwise the XML string is returned, by default None.

        Returns
        -------
        Optional[str]
                The XML text when ``output_path`` is None, else None.

        Raises
        ------
        ValueError
                If the document holds text windows-1252 cannot encode or XML cannot carry (only
                possible when validation was bypassed, e.g. ``model_construct``).
        """
        document = coerce_document(InformeQuadrimestralDocument, doc)
        root = ET.Element("DOC_ARQ", {"xmlns": _NAMESPACE})
        append_field(root, "cab_inform", document.header)
        informs = ET.SubElement(root, "LISTA_INFORM")
        for inform in document.informs:
            append_field(informs, "inform", inform)
        xml_str, payload = render_xml(root)
        return deliver(xml_str, payload, output_path)
