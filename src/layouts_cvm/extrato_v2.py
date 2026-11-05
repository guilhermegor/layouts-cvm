"""CVM Extrato V2 (fund statement) — submission (envio) writer.

Produces the Extrato V2 XML from a validated :class:`ExtratoV2Document`. The schema declares its
fields in XML order and named after their tag, so the serialiser is one recursive walk over
``model_fields``: a ``None`` is omitted, a nested model is a block, a list repeats its element.
Pure logic plus file I/O at the edges — no network.
"""

from collections.abc import Mapping
from xml.etree import ElementTree as ET  # noqa: S405  # builds XML, never parses untrusted input

from layouts_cvm._internal.config.ports.submission_writer import SubmissionWriter
from layouts_cvm._internal.config.schemas.extrato_v2 import ExtratoV2Document
from layouts_cvm._internal.utils.xml_fields import require
from layouts_cvm._internal.utils.xml_writer import (
    append_field,
    coerce_document,
    deliver,
    render_xml,
)


_NAMESPACE = "urn:extr"
_MAX_BYTES = 1_000_000


class ExtratoV2(SubmissionWriter[ExtratoV2Document]):
    """Serialize a validated Extrato V2 document to CVM-compliant XML.

    Concrete :class:`SubmissionWriter` for the Extrato (fund statement) V2 XML
    standard.

    Methods
    -------
    export(doc, output_path)
            Serialize a validated document to windows-1252 XML.
    """

    def export(
        self, doc: ExtratoV2Document | Mapping[str, object], output_path: str | None = None
    ) -> str | None:
        """Serialize a validated ExtratoV2Document to a CVM-compliant XML string or file.

        The text is encoded and checked for well-formedness and size **before** the destination
        is opened, so a failure never truncates an existing file.

        Parameters
        ----------
        doc : ExtratoV2Document or Mapping
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
                possible when validation was bypassed, e.g. ``model_construct``), or the encoded
                file exceeds the page's 1 MB limit.
        """
        document = coerce_document(ExtratoV2Document, doc)
        root = ET.Element("DOC_ARQ", {"xmlns": _NAMESPACE})
        append_field(root, "cab_inform", document.header)
        funds = ET.SubElement(root, "EXTRATO_FUNDO")
        for row in document.rows:
            append_field(funds, "row_extrato", row)
        xml_str, payload = render_xml(root)
        require(
            len(payload) <= _MAX_BYTES,
            lambda: f"file is {len(payload)} bytes; the page allows at most 1 MB",
        )
        return deliver(xml_str, payload, output_path)
