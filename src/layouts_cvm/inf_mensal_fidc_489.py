"""CVM Informe Mensal FIDC — ICVM 489 submission (envio) writer (until 2019-11-01).

Produces the ``urn:fidc`` XML of ``PadraoXMLMensalFIDC489.asp`` from a validated
:class:`InfMensalFidc489Document`. The element order is the schema's field order and every tag
is the field name (or alias), exactly as for the ICVM 576 layout, so this writer reuses that
writer's block walk and only swaps the document model it validates. Pure logic plus file I/O
at the edges — no network.
"""

from collections.abc import Mapping

from layouts_cvm._internal.config.schemas.inf_mensal_fidc_489 import InfMensalFidc489Document
from layouts_cvm._internal.utils.atomic_write import atomic_write_bytes
from layouts_cvm._internal.utils.xml_writer import coerce_document
from layouts_cvm.inf_mensal_fidc import InfMensalFidc


class InfMensalFidc489(InfMensalFidc):
    """Serialize a validated Informe Mensal FIDC (ICVM 489) document to CVM-compliant XML.

    Methods
    -------
    export(doc, output_path)
            Serialize a validated document to a CVM-compliant XML string or file.
    """

    def export(
        self,
        doc: InfMensalFidc489Document | Mapping[str, object],  # type: ignore[override]
        output_path: str | None = None,
    ) -> str | None:
        """Serialize a validated InfMensalFidc489Document to a CVM-compliant XML string.

        Produces UTF-8 text internally; when output_path is given the file is
        written atomically with windows-1252 encoding as required by CVM.

        Parameters
        ----------
        doc : InfMensalFidc489Document or Mapping
                Validated document model, or plain data to validate into one.
        output_path : Optional[str]
                Destination file path. If provided, the file is written and None is
                returned; otherwise the XML string is returned, by default None.

        Returns
        -------
        Optional[str]
                XML string when output_path is None, else None.
        """
        document = coerce_document(InfMensalFidc489Document, doc)
        lines = ['<?xml version="1.0" encoding="windows-1252"?>', '<DOC_ARQ xmlns="urn:fidc">']
        lines.extend(self._block_lines(document, 1))
        lines.append("</DOC_ARQ>")
        xml_str = "\n".join(lines)
        if output_path is not None:
            atomic_write_bytes(output_path, xml_str.encode("windows-1252"))
            return None
        return xml_str
