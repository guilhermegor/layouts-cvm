"""CVM Perfil Mensal V3 — submission (envio) writer.

Produces CVM-compliant Monthly Profile XML (V3, ``VERSAO`` 3.0) from validated schema
models. The V3 and V4 layouts share the tag order and decimal scales, so this writer
delegates to the V4 writer's public ``export`` instead of copying its builder.
"""

from collections.abc import Mapping

from layouts_cvm._internal.config.ports.submission_writer import SubmissionWriter
from layouts_cvm._internal.config.schemas.perfil_mensal_v3 import PerfilMensalV3Document
from layouts_cvm._internal.utils.xml_writer import coerce_document
from layouts_cvm.perfil_mensal import PerfilMensal


class PerfilMensalV3(SubmissionWriter[PerfilMensalV3Document]):
    """Serialize a validated Perfil Mensal V3 document to CVM-compliant XML.

    Methods
    -------
    export(doc, output_path)
            Serialize a validated V3 document to a CVM-compliant XML string or file.
    """

    def export(
        self,
        doc: PerfilMensalV3Document | Mapping[str, object],
        output_path: str | None = None,
    ) -> str | None:
        """Serialize a validated PerfilMensalV3Document to CVM-compliant XML.

        Parameters
        ----------
        doc : PerfilMensalV3Document or Mapping
                Validated document model, or plain data to validate into one.
        output_path : Optional[str]
                Destination file path, written atomically as windows-1252. If given, None
                is returned; otherwise the XML string is returned, by default None.

        Returns
        -------
        Optional[str]
                XML string when output_path is None, else None.
        """
        document = coerce_document(PerfilMensalV3Document, doc)
        return PerfilMensal().export(document, output_path, versao="3.0")
