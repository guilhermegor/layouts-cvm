"""CVM Informe Trimestral V1 (until 2017-06) — submission (envio) writer.

Produces the Informe Trimestral V1 XML from a validated :class:`InformeTrimestralV1Document`.
The document shape (``DOC_ARQ`` > ``CAB_INFORM`` + ``LISTA_INFORM`` > ``INFORM``) and the
namespace, encoding and element serialiser are the V2 writer's, imported rather than copied;
only the schema differs. Pure logic plus file I/O at the edges — no network.
"""

from collections.abc import Mapping
from xml.etree import ElementTree as ET  # noqa: S405  # builds XML, never parses untrusted input

from layouts_cvm._internal.config.ports.submission_writer import SubmissionWriter
from layouts_cvm._internal.config.schemas.informe_trimestral_v1 import (
    InformeTrimestralV1Document,
)
from layouts_cvm._internal.utils.xml_writer import (
    append_field,
    coerce_document,
    deliver,
    render_xml,
)
from layouts_cvm.informe_quadrimestral import _NAMESPACE


class InformeTrimestralV1(SubmissionWriter[InformeTrimestralV1Document]):
    """Serialize a validated Informe Trimestral V1 document to CVM-compliant XML.

    Concrete :class:`SubmissionWriter` for the Informe Trimestral V1 XML standard.

    Methods
    -------
    export(doc, output_path)
            Serialize a validated document to windows-1252 XML.
    """

    def export(
        self,
        doc: InformeTrimestralV1Document | Mapping[str, object],
        output_path: str | None = None,
    ) -> str | None:
        """Serialize a validated document to a CVM-compliant XML string or file.

        Parameters
        ----------
        doc : InformeTrimestralV1Document or Mapping
                Validated document model, or plain data to validate into one.
        output_path : Optional[str]
                Destination file. When given the file is written in windows-1252 and ``None`` is
                returned; otherwise the XML string is returned, by default None.

        Returns
        -------
        Optional[str]
                The XML text when ``output_path`` is None, else None.
        """
        document = coerce_document(InformeTrimestralV1Document, doc)
        root = ET.Element("DOC_ARQ", {"xmlns": _NAMESPACE})
        append_field(root, "cab_inform", document.header)
        informs = ET.SubElement(root, "LISTA_INFORM")
        for inform in document.informs:
            append_field(informs, "inform", inform)
        xml_str, payload = render_xml(root)
        return deliver(xml_str, payload, output_path)
