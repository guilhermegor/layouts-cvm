"""CVM Extrato (fund statement) — submission (envio) writer.

Produces the Extrato V3 XML from a validated :class:`ExtratoDocument`. The schema declares its
fields in XML order and named after their tag, so the serialiser is one recursive walk over
``model_fields``: a ``None`` is omitted, a nested model is a block, a list repeats its element.
Pure logic plus file I/O at the edges — no network.
"""

from xml.etree import ElementTree as ET  # noqa: S405  # builds XML, never parses untrusted input

from layouts_cvm._internal.config.ports.submission_writer import SubmissionWriter
from layouts_cvm._internal.utils.xml_fields import require
from layouts_cvm._internal.utils.xml_writer import append_field, deliver, render_xml
from layouts_cvm.schemas.extrato import ExtratoDocument


_NAMESPACE = "urn:extr"
_MAX_BYTES = 1_000_000


class Extrato(SubmissionWriter[ExtratoDocument]):
    """Serialize a validated Extrato V3 document to CVM-compliant XML.

    Concrete :class:`SubmissionWriter` for the Extrato (fund statement) V3 XML
    standard.

    Methods
    -------
    export(doc, output_path)
            Serialize a validated document to windows-1252 XML.
    """

    def export(self, doc: ExtratoDocument, output_path: str | None = None) -> str | None:
        """Serialize a validated ExtratoDocument to a CVM-compliant XML string or file.

        The text is encoded and checked for well-formedness and size **before** the destination
        is opened, so a failure never truncates an existing file.

        Parameters
        ----------
        doc : ExtratoDocument
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
                possible when validation was bypassed, e.g. ``model_construct``), or the encoded
                file exceeds the page's 1 MB limit.
        """
        root = ET.Element("DOC_ARQ", {"xmlns": _NAMESPACE})
        append_field(root, "cab_inform", doc.header)
        funds = ET.SubElement(root, "EXTRATO_FUNDO")
        for row in doc.rows:
            append_field(funds, "row_extrato", row)
        xml_str, payload = render_xml(root)
        require(
            len(payload) <= _MAX_BYTES,
            lambda: f"file is {len(payload)} bytes; the page allows at most 1 MB",
        )
        return deliver(xml_str, payload, output_path)
