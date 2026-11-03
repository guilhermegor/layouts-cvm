"""CVM Informe Diário V2 — submission (envio) writer.

Produces CVM-compliant Daily Report XML (V2, ``VERSAO`` 2.0) from a validated
:class:`InformeDiarioV2Document`. Unlike V3/V4 the page wraps the funds in ``LISTA_INFORM`` and
has no ``DATA_PROX_PL``, so the V4 builder cannot be delegated to; the shared element serialiser
is used instead. Pure logic plus file I/O at the edges — no network.
"""

from collections.abc import Mapping
from xml.etree import ElementTree as ET  # noqa: S405  # builds XML, never parses untrusted input

from layouts_cvm._internal.config.ports.submission_writer import SubmissionWriter
from layouts_cvm._internal.config.schemas.informe_diario import SignificantShareholder
from layouts_cvm._internal.config.schemas.informe_diario_v2 import (
    InformeDiarioV2Document,
    InformeDiarioV2Inform,
)
from layouts_cvm._internal.utils.typing import type_checker
from layouts_cvm._internal.utils.xml_writer import (
    append_field,
    coerce_document,
    deliver,
    render_xml,
)


_NAMESPACE = "urn:infdiario"
_LIST_SCALAR_FIELDS = tuple(
    field for field in InformeDiarioV2Inform.model_fields if field != "lista_cotst_signif"
)


class InformeDiarioV2(SubmissionWriter[InformeDiarioV2Document]):
    """Serialize a validated Informe Diário V2 document to CVM-compliant XML.

    Methods
    -------
    export(doc, output_path)
            Serialize a validated V2 document to a CVM-compliant XML string or file.
    """

    def export(
        self,
        doc: InformeDiarioV2Document | Mapping[str, object],
        output_path: str | None = None,
    ) -> str | None:
        """Serialize a validated InformeDiarioV2Document to CVM-compliant XML.

        Parameters
        ----------
        doc : InformeDiarioV2Document or Mapping
                Validated document model, or plain data to validate into one.
        output_path : Optional[str]
                Destination file path, written atomically as windows-1252. If given, None
                is returned; otherwise the XML string is returned, by default None.

        Returns
        -------
        Optional[str]
                XML string when output_path is None, else None.
        """
        document = coerce_document(InformeDiarioV2Document, doc)
        root = ET.Element("DOC_ARQ", {"xmlns": _NAMESPACE})
        append_field(root, "cab_inform", document.header)
        informs = ET.SubElement(root, "LISTA_INFORM")
        for inform in document.informs:
            self._append_inform(informs, inform)
        xml_str, payload = render_xml(root)
        return deliver(xml_str, payload, output_path)

    @staticmethod
    def _append_inform(parent: ET.Element, inform: InformeDiarioV2Inform) -> None:
        """Append one INFORM block, wrapping the shareholders in LISTA_COTST_SIGNIF.

        Parameters
        ----------
        parent : ET.Element
                The LISTA_INFORM element.
        inform : InformeDiarioV2Inform
                Validated fund-informe model.
        """
        node = ET.SubElement(parent, "INFORM")
        for field in _LIST_SCALAR_FIELDS:
            append_field(node, field, getattr(inform, field))
        _append_shareholders(node, inform.lista_cotst_signif)


@type_checker
def _append_shareholders(
    node: ET.Element, list_cotst: list[SignificantShareholder] | None
) -> None:
    """Append LISTA_COTST_SIGNIF with one COTST_SIGNIF per shareholder, if there are any.

    Parameters
    ----------
    node : ET.Element
            The INFORM element.
    list_cotst : Optional[list[SignificantShareholder]]
            Shareholders holding 20% or more of the net worth; None or empty omits the block.
    """
    if not list_cotst:
        return
    wrapper = ET.SubElement(node, "LISTA_COTST_SIGNIF")
    append_field(wrapper, "cotst_signif", list_cotst)
