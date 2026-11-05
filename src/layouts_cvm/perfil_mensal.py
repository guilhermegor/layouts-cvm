"""CVM Perfil Mensal — submission (envio) writer.

Produces CVM-compliant Monthly Profile XML from validated schema models. This is
the *sending* half of the standard; parsing CVM files back into models lives in the
``ingestion`` section. Pure logic plus file I/O at the edges — no network.
"""

from collections.abc import Mapping

from layouts_cvm._base_perfil_mensal import _BasePerfilMensal
from layouts_cvm._internal.config.schemas.perfil_mensal import PerfilMensalDocument
from layouts_cvm._internal.utils.xml_writer import coerce_document


class PerfilMensal(_BasePerfilMensal[PerfilMensalDocument]):
    """Serialize a validated Perfil Mensal document to CVM-compliant XML.

    Concrete :class:`SubmissionWriter` for the Perfil Mensal V4 XML standard.

    Methods
    -------
    export(doc, output_path, versao)
            Serialize a validated document to a CVM-compliant XML string.
    """

    def export(
        self,
        doc: PerfilMensalDocument | Mapping[str, object],
        output_path: str | None = None,
        versao: str = "4.0",
    ) -> str | None:
        """Serialize a validated PerfilMensalDocument to a CVM-compliant XML string.

        Produces UTF-8 text internally; when output_path is given the file is
        written with windows-1252 encoding as required by CVM.

        Parameters
        ----------
        doc : PerfilMensalDocument or Mapping
                Validated document model, or plain data to validate into one.
        output_path : Optional[str]
                Destination file path. If provided, the file is written and None is
                returned; otherwise the XML string is returned, by default None.
        versao : str
                CVM document format version placed in the VERSAO tag, by default "4.0".

        Returns
        -------
        Optional[str]
                XML string when output_path is None, else None.
        """
        document = coerce_document(PerfilMensalDocument, doc)
        return self._emit(self._build_xml_str(document, versao=versao), output_path)
