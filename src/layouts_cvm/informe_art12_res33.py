"""CVM Informe Art. 12 Resolução CVM 33 (escriturador) — submission (envio) writer.

Produces CVM-compliant XML (``COD_ARQ`` 29, namespace ``urn:prestserv``) from a validated
:class:`InformeArt12Res33Document`. The page nests ``LISTA_PREST > INFORM_PREST`` and
``LISTA_EMISSORES > EMISSOR``; the wrappers are emitted here and the leaves by the shared
element serialiser. Pure logic plus file I/O at the edges — no network.
"""

from collections.abc import Mapping
from xml.etree import ElementTree as ET  # noqa: S405  # builds XML, never parses untrusted input

from layouts_cvm._internal.config.ports.submission_writer import SubmissionWriter
from layouts_cvm._internal.config.schemas.informe_art12_res33 import (
    InformeArt12Res33Document,
    Prestador,
)
from layouts_cvm._internal.utils.xml_writer import (
    append_field,
    coerce_document,
    deliver,
    render_xml,
)


_NAMESPACE = "urn:prestserv"


class InformeArt12Res33(SubmissionWriter[InformeArt12Res33Document]):
    """Serialize a validated Informe Art. 12 Res. 33 document to CVM-compliant XML.

    Methods
    -------
    export(doc, output_path)
            Serialize a document to a CVM-compliant XML string or file.
    """

    def export(
        self,
        doc: InformeArt12Res33Document | Mapping[str, object],
        output_path: str | None = None,
    ) -> str | None:
        """Serialize a validated InformeArt12Res33Document to CVM-compliant XML.

        Parameters
        ----------
        doc : InformeArt12Res33Document or Mapping
                Validated document model, or plain data to validate into one.
        output_path : Optional[str]
                Destination file path, written atomically as windows-1252. If given, None
                is returned; otherwise the XML string is returned, by default None.

        Returns
        -------
        Optional[str]
                XML string when output_path is None, else None.
        """
        document = coerce_document(InformeArt12Res33Document, doc)
        root = ET.Element("DOC_ARQ", {"xmlns": _NAMESPACE})
        append_field(root, "cod_arq", document.cod_arq)
        append_field(root, "ds_inform", document.ds_inform)
        lista = ET.SubElement(root, "LISTA_PREST")
        for prestador in document.prestadores:
            self._append_prestador(lista, prestador)
        xml_str, payload = render_xml(root)
        return deliver(xml_str, payload, output_path)

    @staticmethod
    def _append_prestador(parent: ET.Element, prestador: Prestador) -> None:
        """Append one INFORM_PREST block with its LISTA_EMISSORES.

        Parameters
        ----------
        parent : ET.Element
                The LISTA_PREST element.
        prestador : Prestador
                Validated provider model.
        """
        node = ET.SubElement(parent, "INFORM_PREST")
        append_field(node, "ds_prest", prestador.ds_prest)
        emissores = ET.SubElement(node, "LISTA_EMISSORES")
        append_field(emissores, "emissor", prestador.emissores)
