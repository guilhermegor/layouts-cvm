"""CVM Informe Anual de Auditor — submission (envio) writer.

Produces the Informe Anual de Auditor XML (``COD_DOC`` 23, namespace ``urn:audtanual``) from a
validated :class:`InformeAnualAuditorDocument`. The schema declares its fields in XML order, so
the serialiser is the shared recursive walk over ``model_fields``.
"""

from collections.abc import Mapping
from xml.etree import ElementTree as ET  # noqa: S405  # builds XML, never parses untrusted input

from layouts_cvm._internal.config.ports.submission_writer import SubmissionWriter
from layouts_cvm._internal.config.schemas.informe_anual_auditor import (
    InformeAnualAuditorDocument,
)
from layouts_cvm._internal.utils.xml_writer import (
    append_field,
    coerce_document,
    deliver,
    render_xml,
)


_NAMESPACE = "urn:audtanual"


class InformeAnualAuditor(SubmissionWriter[InformeAnualAuditorDocument]):
    """Serialize a validated Informe Anual de Auditor document to CVM-compliant XML.

    Methods
    -------
    export(doc, output_path)
            Serialize a validated document to windows-1252 XML.
    """

    def export(
        self,
        doc: InformeAnualAuditorDocument | Mapping[str, object],
        output_path: str | None = None,
    ) -> str | None:
        """Serialize a validated document to a CVM-compliant XML string or file.

        Parameters
        ----------
        doc : InformeAnualAuditorDocument or Mapping
                Validated document model, or plain data to validate into one.
        output_path : Optional[str]
                Destination file, written atomically as windows-1252. If given, None is
                returned; otherwise the XML string is returned, by default None.

        Returns
        -------
        Optional[str]
                XML string when output_path is None, else None.
        """
        document = coerce_document(InformeAnualAuditorDocument, doc)
        root = ET.Element("DOC_ARQ", {"xmlns": _NAMESPACE})
        for name in type(document).model_fields:
            append_field(root, name, getattr(document, name))
        xml_str, payload = render_xml(root)
        return deliver(xml_str, payload, output_path)
