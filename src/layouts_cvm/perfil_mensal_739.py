"""CVM Perfil Mensal ICVM 739 — submission (envio) writer.

Produces CVM-compliant Monthly Profile XML (``VERSAO`` 1.0) from validated schema models.
The layout has the V4 tag order and differs only in the scale of four tags and in the
absence of two. The V4 builder reads none of the V3-only tags, so this writer subclasses
``PerfilMensal`` and sets the stress scale to 2 instead of duplicating the builder. The 739
models are standalone, but the writer validates the document into the V4 shape the builder
reads, so a stricter V4 rule or new V4 field reaches 739 output; a test pins the field sets
to catch that drift (the shared builder base is #83).
"""

from collections.abc import Mapping

from layouts_cvm._internal.config.schemas.perfil_mensal import PerfilMensalDocument
from layouts_cvm._internal.config.schemas.perfil_mensal_739 import PerfilMensal739Document
from layouts_cvm._internal.utils.atomic_write import atomic_write_bytes
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
        doc_v4 = PerfilMensalDocument.model_validate(document.model_dump())
        xml_str = self._build_xml_str(doc_v4, versao=document.header.versao)
        if output_path is not None:
            atomic_write_bytes(output_path, xml_str.encode("windows-1252"))
            return None
        return xml_str
