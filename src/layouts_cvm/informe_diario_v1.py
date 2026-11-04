"""CVM Informe Diário V1 — submission (envio) writer.

Produces CVM-compliant Daily Report XML (V1, valid until 2012-07-01, no ``VERSAO`` tag) from a
validated :class:`InformeDiarioV1Document`. The funds sit inside ``LISTA_INFORM`` and an
``INFORM`` has no ``VL_TOTAL_SAI``/``VL_TOTAL_ATV``, so the V4 builder cannot be delegated to;
the shared element serialiser is used instead. Pure logic plus file I/O at the edges.
"""

from collections.abc import Mapping
from xml.etree import ElementTree as ET  # noqa: S405  # builds XML, never parses untrusted input

from layouts_cvm._internal.config.ports.submission_writer import SubmissionWriter
from layouts_cvm._internal.config.schemas.informe_diario_v1 import (
    InformeDiarioV1Document,
    InformeDiarioV1Inform,
    InformeDiarioV1Shareholder,
)
from layouts_cvm._internal.utils.typing import type_checker
from layouts_cvm._internal.utils.xml_writer import (
    append_field,
    coerce_document,
    deliver,
    render_xml,
)


_NAMESPACE = "urn:infdiario"
_INFORM_SCALAR_FIELDS = tuple(
    field for field in InformeDiarioV1Inform.model_fields if field != "lista_cotst_signif"
)


class InformeDiarioV1(SubmissionWriter[InformeDiarioV1Document]):
    """Serialize a validated Informe Diário V1 document to CVM-compliant XML.

    Methods
    -------
    export(doc, output_path)
            Serialize a validated V1 document to a CVM-compliant XML string or file.
    """

    def export(
        self,
        doc: InformeDiarioV1Document | Mapping[str, object],
        output_path: str | None = None,
    ) -> str | None:
        """Serialize a validated InformeDiarioV1Document to CVM-compliant XML.

        Parameters
        ----------
        doc : InformeDiarioV1Document or Mapping
                Validated document model, or plain data to validate into one.
        output_path : Optional[str]
                Destination file path, written atomically as windows-1252. If given, None
                is returned; otherwise the XML string is returned, by default None.

        Returns
        -------
        Optional[str]
                XML string when output_path is None, else None.
        """
        document = coerce_document(InformeDiarioV1Document, doc)
        root = ET.Element("DOC_ARQ", {"xmlns": _NAMESPACE})
        append_field(root, "cab_inform", document.header)
        informs = ET.SubElement(root, "LISTA_INFORM")
        for inform in document.informs:
            _append_inform(informs, inform)
        xml_str, payload = render_xml(root)
        return deliver(xml_str, payload, output_path)


@type_checker
def _append_inform(parent: ET.Element, inform: InformeDiarioV1Inform) -> None:
    """Append one INFORM block, wrapping the shareholders in LISTA_COTST_SIGNIF.

    Parameters
    ----------
    parent : ET.Element
            The LISTA_INFORM element.
    inform : InformeDiarioV1Inform
            Validated fund-informe model.
    """
    node = ET.SubElement(parent, "INFORM")
    for field in _INFORM_SCALAR_FIELDS:
        append_field(node, field, getattr(inform, field))
    _append_shareholders(node, inform.lista_cotst_signif)


@type_checker
def _append_shareholders(
    node: ET.Element, list_cotst: list[InformeDiarioV1Shareholder] | None
) -> None:
    """Append LISTA_COTST_SIGNIF with one COTST_SIGNIF per shareholder, if there are any.

    Parameters
    ----------
    node : ET.Element
            The INFORM element.
    list_cotst : Optional[list[InformeDiarioV1Shareholder]]
            Shareholders holding 20% or more of the net worth; None or empty omits the block.
    """
    if not list_cotst:
        return
    wrapper = ET.SubElement(node, "LISTA_COTST_SIGNIF")
    append_field(wrapper, "cotst_signif", list_cotst)
