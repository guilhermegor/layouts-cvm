"""CVM Semiannual Non-Resident Investor Report, Part I — submission (envio) writer.

Part I (``COD_DOC`` 69) shares the monthly INR namespace, tag order and encoding, minus the
applications block. It builds on the shared ``xml_writer`` helpers and its own frozen models,
not on the live :class:`layouts_cvm.inr_mensal.InrMensal`.
**Part II (``COD_DOC`` 70) is not implemented**: a Part I file alone is not the complete
Informe Semestral.
"""

from collections.abc import Mapping
from xml.etree import ElementTree as ET  # noqa: S405  # builds XML, never parses untrusted input

from layouts_cvm._internal.config.ports.submission_writer import SubmissionWriter
from layouts_cvm._internal.config.schemas.informe_semestral_inr import (
    InformeSemestralInrDocument,
)
from layouts_cvm._internal.utils.xml_writer import (
    append_field,
    coerce_document,
    deliver,
    render_xml,
)


_NAMESPACE = "urn:infmensal"


class InformeSemestralInr(SubmissionWriter[InformeSemestralInrDocument]):
    """Serialize a validated Informe Semestral INR Part I document to CVM XML.

    Methods
    -------
    export(doc, output_path)
        Serialize a validated document to windows-1252 XML.
    """

    def export(
        self,
        doc: InformeSemestralInrDocument | Mapping[str, object],
        output_path: str | None = None,
    ) -> str | None:
        """Serialize a validated Part I document to a CVM-compliant XML string or file.

        Parameters
        ----------
        doc : InformeSemestralInrDocument or Mapping
            Validated document model, or plain data to validate into one.
        output_path : Optional[str]
            Destination file, written atomically as windows-1252. If given, None is
            returned; otherwise the XML string is returned, by default None.

        Returns
        -------
        Optional[str]
            The XML text when ``output_path`` is None, else None.
        """
        document = coerce_document(InformeSemestralInrDocument, doc)
        root = ET.Element("DOC_ARQ", {"xmlns": _NAMESPACE})
        append_field(root, "cab_inform", document.header)
        participants = ET.SubElement(root, "LISTA_PARTICIPANTES")
        for participant in document.participantes:
            append_field(participants, "participante", participant)
        xml_str, payload = render_xml(root)
        return deliver(xml_str, payload, output_path)
