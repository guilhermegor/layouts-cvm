"""CVM Informe Diário V3 — submission (envio) writer.

Produces CVM-compliant Daily Report XML (V3, ``VERSAO`` 3.0) from validated schema
models. The V3 and V4 layouts share the tag order and decimal scales, so this writer
delegates to the V4 writer's public ``export`` instead of copying its builder.
"""

from collections.abc import Mapping

from layouts_cvm._internal.config.ports.submission_writer import SubmissionWriter
from layouts_cvm._internal.config.schemas.informe_diario_v3 import InformeDiarioV3Document
from layouts_cvm._internal.utils.xml_writer import coerce_document
from layouts_cvm.informe_diario import InformeDiario


class InformeDiarioV3(SubmissionWriter[InformeDiarioV3Document]):
    """Serialize a validated Informe Diário V3 document to CVM-compliant XML.

    Methods
    -------
    export(doc, output_path)
            Serialize a validated V3 document to a CVM-compliant XML string.
    """

    def export(
        self,
        doc: InformeDiarioV3Document | Mapping[str, object],
        output_path: str | None = None,
    ) -> str | None:
        """Serialize a validated InformeDiarioV3Document to CVM-compliant XML.

        Parameters
        ----------
        doc : InformeDiarioV3Document or Mapping
                Validated document model, or plain data to validate into one.
        output_path : Optional[str]
                Destination file path, written atomically as windows-1252. If given, None
                is returned; otherwise the XML string is returned, by default None.

        Returns
        -------
        Optional[str]
                XML string when output_path is None, else None.
        """
        document = coerce_document(InformeDiarioV3Document, doc)
        return InformeDiario().export(document, output_path, versao="3.0")
