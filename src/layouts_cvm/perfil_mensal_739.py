"""CVM Perfil Mensal ICVM 739 — submission (envio) writer.

Produces CVM-compliant Monthly Profile XML (``VERSAO`` 1.0) from validated schema models.
The layout shares the V4 tag order; it differs only in the scale of four tags and in the
absence of two, so this writer reuses the V4 builder with the stress scale set to 2.
"""

from collections.abc import Mapping

from layouts_cvm._internal.config.schemas.perfil_mensal_739 import PerfilMensal739Document
from layouts_cvm._internal.utils.xml_writer import coerce_document
from layouts_cvm.perfil_mensal import PerfilMensal


class PerfilMensal739(PerfilMensal):
    """Serialize a validated Perfil Mensal ICVM 739 document to CVM-compliant XML.

    Methods
    -------
    export(doc, output_path)
            Serialize a validated 739 document to a CVM-compliant XML string or file.
    """

    _STRESS_PLACES = 2

    def export(  # type: ignore[override]
        self,
        doc: PerfilMensal739Document | Mapping[str, object],
        output_path: str | None = None,
    ) -> str | None:
        """Serialize a validated PerfilMensal739Document to CVM-compliant XML.

        Parameters
        ----------
        doc : PerfilMensal739Document or Mapping
                Validated document model, or plain data to validate into one.
        output_path : Optional[str]
                Destination file path, written atomically as windows-1252. If given, None
                is returned; otherwise the XML string is returned, by default None.

        Returns
        -------
        Optional[str]
                XML string when output_path is None, else None.
        """
        document = coerce_document(PerfilMensal739Document, doc)
        return super().export(document, output_path, versao="1.0")
