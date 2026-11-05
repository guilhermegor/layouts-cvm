"""CVM Perfil Mensal ICVM 739 — submission (envio) writer.

Produces CVM-compliant Monthly Profile XML (``VERSAO`` 1.0) from validated schema models.
The layout has the V4 tag order and differs only in the scale of four tags and in the
absence of two. The V4 builder reads none of the V3-only tags, so this writer shares the
private ``_BasePerfilMensal`` builder with ``PerfilMensal`` and sets the stress scale to 2
instead of duplicating it. The 739 models are standalone, but the writer validates the
document into the V4 shape the builder reads, so a stricter V4 constraint reaches 739
output; a test pins each model's field names against V4 (not its constraints) to catch
added or removed fields.
"""

from collections.abc import Mapping

from layouts_cvm._base_perfil_mensal import _BasePerfilMensal
from layouts_cvm._internal.config.schemas.perfil_mensal import PerfilMensalDocument
from layouts_cvm._internal.config.schemas.perfil_mensal_739 import PerfilMensal739Document
from layouts_cvm._internal.utils.xml_writer import coerce_document


class PerfilMensal739(_BasePerfilMensal[PerfilMensal739Document]):
    """Serialize a validated Perfil Mensal ICVM 739 document to CVM-compliant XML.

    Methods
    -------
    export(doc, output_path)
            Serialize a validated 739 document to a CVM-compliant XML string or file.
    """

    _STRESS_PLACES = 2

    def export(
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
        doc_v4 = PerfilMensalDocument.model_validate(document.model_dump())
        xml_str = self._build_xml_str(doc_v4, versao=document.header.versao)
        return self._emit(xml_str, output_path)
