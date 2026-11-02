"""CVM Informe Quadrimestral (FIP) — submission (envio) writer.

Produces the Informe Quadrimestral V2 XML from a validated
:class:`InformeQuadrimestralDocument`. The schema declares its
fields in XML order and named after their tag, so the serialiser is one recursive walk over
``model_fields``: a ``None`` is omitted, a nested model is a block, a list repeats its element.
Pure logic plus file I/O at the edges — no network.
"""

from xml.etree import ElementTree as ET  # noqa: S405  # builds XML, never parses untrusted input

from layouts_cvm._internal.config.ports.submission_writer import SubmissionWriter
from layouts_cvm._internal.utils.xml_writer import append_field, deliver, render_xml
from layouts_cvm.schemas.informe_quadrimestral import InformeQuadrimestralDocument


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
        self, doc: InformeQuadrimestralDocument, output_path: str | None = None
    ) -> str | None:
        """Serialize a validated document to a CVM-compliant XML string or file.

        The text is encoded and checked for well-formedness **before** the destination is
        opened, so a failure never truncates an existing file.

        Parameters
        ----------
        doc : InformeQuadrimestralDocument
                Fully validated document model.
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
        root = ET.Element("DOC_ARQ", {"xmlns": _NAMESPACE})
        append_field(root, "cab_inform", doc.header)
        informs = ET.SubElement(root, "LISTA_INFORM")
        for inform in doc.informs:
            append_field(informs, "inform", inform)
        xml_str, payload = render_xml(root)
        return deliver(xml_str, payload, output_path)
