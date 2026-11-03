"""CVM Lâmina de Fundos V1 — submission (envio) writer.

Produces the Lâmina V1 XML (``VERSAO`` 1.0) from a validated :class:`LaminaV1Document`. V1 has
a different tag set from V3, so its schema cannot extend the V3 one; the serialiser is the same
recursive walk over ``model_fields`` (see :mod:`layouts_cvm.lamina`), reusing the shared XML
helpers.
"""

from collections.abc import Mapping
from xml.etree import ElementTree as ET  # noqa: S405  # builds XML, never parses untrusted input

from layouts_cvm._internal.config.ports.submission_writer import SubmissionWriter
from layouts_cvm._internal.config.schemas.lamina_v1 import LaminaV1Document
from layouts_cvm._internal.utils.xml_writer import (
    append_field,
    coerce_document,
    deliver,
    render_xml,
)


_NAMESPACE = "urn:lamina"


class LaminaV1(SubmissionWriter[LaminaV1Document]):
    """Serialize a validated Lâmina V1 document to CVM-compliant XML.

    Methods
    -------
    export(doc, output_path)
            Serialize a validated V1 document to windows-1252 XML.
    """

    def export(
        self, doc: LaminaV1Document | Mapping[str, object], output_path: str | None = None
    ) -> str | None:
        """Serialize a validated LaminaV1Document to a CVM-compliant XML string or file.

        Parameters
        ----------
        doc : LaminaV1Document or Mapping
                Validated document model, or plain data to validate into one.
        output_path : Optional[str]
                Destination file path, written atomically as windows-1252. If given, None
                is returned; otherwise the XML string is returned, by default None.

        Returns
        -------
        Optional[str]
                XML string when output_path is None, else None.
        """
        document = coerce_document(LaminaV1Document, doc)
        root = ET.Element("DOC_ARQ", {"xmlns": _NAMESPACE})
        append_field(root, "cab_inform", document.header)
        informs = ET.SubElement(root, "LISTA_INFORM")
        for inform in document.informs:
            append_field(informs, "inform", inform)
        xml_str, payload = render_xml(root)
        return deliver(xml_str, payload, output_path)
