"""CVM CDA V2 (portfolio composition report) — submission (envio) writer.

Produces CVM-compliant CDA V2 XML (namespace ``urn:cda``, ``VERSAO`` 2.0) from validated
schema models. V2 has its own structure (see
:mod:`layouts_cvm._internal.config.schemas.cda_v2`), but its leaves, scales and wrapper blocks
are the V4 writer's, so the tag walk is reused from :mod:`layouts_cvm.cda` and only the
document skeleton is built here.
"""

from collections.abc import Mapping
from xml.etree import ElementTree as ET  # noqa: S405

from layouts_cvm._internal.config.ports.submission_writer import SubmissionWriter
from layouts_cvm._internal.config.schemas.cda_v2 import CdaV2Document, CdaV2Inform
from layouts_cvm._internal.utils.typing import type_checker
from layouts_cvm._internal.utils.xml_writer import coerce_document, deliver_text, fill_children
from layouts_cvm.cda import _build_model, _leaf


@type_checker
def _build_inform(node: ET.Element, inform: CdaV2Inform) -> None:
    """Fill one INFORM element, blocks in the page's mandated order.

    Parameters
    ----------
    node : ET.Element
        The INFORM element.
    inform : CdaV2Inform
        Validated fund model.
    """
    _leaf(node, "CNPJ_FDO", inform.cnpj_fdo)
    _leaf(node, "VL_PL", inform.vl_pl)
    ativ = ET.SubElement(node, "LISTA_ATIV")
    for name, item in [
        (blk, itm) for blk in CdaV2Inform.BLOCK_ORDER for itm in getattr(inform, blk)
    ]:
        _build_model(ET.SubElement(ativ, name.upper()), item)


class CdaV2(SubmissionWriter[CdaV2Document]):
    """Serialize a validated CDA V2 document to CVM-compliant XML.

    Methods
    -------
    export(doc, output_path)
        Serialize a validated V2 document to a CVM-compliant XML string.
    """

    def export(
        self, doc: CdaV2Document | Mapping[str, object], output_path: str | None = None
    ) -> str | None:
        """Serialize a validated CdaV2Document to a CVM-compliant XML string.

        Parameters
        ----------
        doc : CdaV2Document or Mapping
            Validated document model, or plain data to validate into one.
        output_path : Optional[str]
            Destination file path, written atomically as windows-1252. If given, None is
            returned; otherwise the XML string is returned, by default None.

        Returns
        -------
        Optional[str]
            XML string when output_path is None, else None.
        """
        document = coerce_document(CdaV2Document, doc)
        root = ET.Element("DOC_ARQ", {"xmlns": "urn:cda"})
        fill_children(
            ET.SubElement(root, "CAB_INFORM"),
            [
                ("COD_DOC", str(document.header.cod_doc)),
                ("VERSAO", str(document.header.versao)),
                ("DT_COMPT", str(document.header.dt_compt)),
                ("DT_GERAC_ARQ", str(document.header.dt_gerac_arq)),
            ],
        )
        lista = ET.SubElement(root, "LISTA_INFORM")
        for inform in document.informs:
            _build_inform(ET.SubElement(lista, "INFORM"), inform)
        ET.indent(root, space="    ")
        xml_str = '<?xml version="1.0" encoding="windows-1252"?>\n' + ET.tostring(
            root, encoding="unicode"
        )
        return deliver_text(xml_str, output_path)
