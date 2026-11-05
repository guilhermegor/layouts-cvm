"""CVM Demonstrativo de Fontes e Aplicações de Recursos (FAR) — submission (envio) writer.

Produces the FAR XML from a validated :class:`DemonstrativoFarDocument`. The page's sample has
no namespace, and every block is a field of the schema named after its tag, so the shared
element serialiser walks the document. Pure logic plus file I/O at the edges — no network.
"""

from collections.abc import Mapping
from xml.etree import ElementTree as ET  # noqa: S405  # builds XML, never parses untrusted input

from layouts_cvm._internal.config.ports.submission_writer import SubmissionWriter
from layouts_cvm._internal.config.schemas.demonstrativo_far import DemonstrativoFarDocument
from layouts_cvm._internal.utils.xml_writer import (
    append_field,
    coerce_document,
    deliver,
    render_xml,
)


class DemonstrativoFar(SubmissionWriter[DemonstrativoFarDocument]):
    """Serialize a validated FAR document to CVM-compliant XML.

    Methods
    -------
    export(doc, output_path)
            Serialize a validated document to windows-1252 XML.
    """

    def export(
        self,
        doc: DemonstrativoFarDocument | Mapping[str, object],
        output_path: str | None = None,
    ) -> str | None:
        """Serialize a validated document to a CVM-compliant XML string or file.

        Parameters
        ----------
        doc : DemonstrativoFarDocument or Mapping
                Validated document model, or plain data to validate into one.
        output_path : Optional[str]
                Destination file, written atomically as windows-1252. If given, None is
                returned; otherwise the XML string is returned, by default None.

        Returns
        -------
        Optional[str]
                XML string when output_path is None, else None.
        """
        document = coerce_document(DemonstrativoFarDocument, doc)
        root = ET.Element("DOC_ARQ")
        for field in type(document).model_fields:
            append_field(root, field, getattr(document, field))
        xml_str, payload = render_xml(root)
        return deliver(xml_str, payload, output_path)
