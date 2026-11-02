"""CVM Informe de Fundo 157 — submission (envio) writer.

Produces the Informe de Fundo 157 XML from a validated :class:`InfFundo157Document`. The schema
declares its fields in XML order and named after their tag, so the serialiser is two flat loops.
Pure logic plus file I/O at the edges — no network.
"""

from xml.etree import ElementTree as ET  # noqa: S405  # builds XML, never parses untrusted input

from pydantic import BaseModel

from layouts_cvm._internal.config.ports.submission_writer import SubmissionWriter
from layouts_cvm._internal.utils.typing import type_checker
from layouts_cvm._internal.utils.xml_writer import deliver, render_xml
from layouts_cvm.schemas.inf_fundo_157 import InfFundo157Document


_NAMESPACE = "urn:inffdo157"


@type_checker
def _block(parent: ET.Element, tag: str, model: BaseModel) -> None:
    """Append ``model`` to ``parent`` as ``<tag>`` with one child per field, in field order.

    Parameters
    ----------
    parent : ET.Element
            The enclosing element.
    tag : str
            The block's XML tag.
    model : BaseModel
            A block whose fields are all scalars named after their lower-cased tag.
    """
    element = ET.SubElement(parent, tag)
    for field in type(model).model_fields:
        ET.SubElement(element, field.upper()).text = str(getattr(model, field))


class InfFundo157(SubmissionWriter[InfFundo157Document]):
    """Serialize a validated Informe de Fundo 157 document to CVM-compliant XML.

    Concrete :class:`SubmissionWriter` for the Informe de Fundo 157 XML standard.

    Methods
    -------
    export(doc, output_path)
            Serialize a validated document to windows-1252 XML.
    """

    def export(self, doc: InfFundo157Document, output_path: str | None = None) -> str | None:
        """Serialize a validated InfFundo157Document to a CVM-compliant XML string or file.

        The text is encoded and checked for well-formedness **before** the destination is
        opened, so a failure never truncates an existing file.

        Parameters
        ----------
        doc : InfFundo157Document
                Fully validated document model.
        output_path : Optional[str]
                Destination file. When given the file is written in windows-1252 and ``None`` is
                returned; otherwise the XML string is returned, by default None.

        Returns
        -------
        Optional[str]
                The XML text when ``output_path`` is None, else None.

        Raises
        ------
        ValueError
                If the document holds text windows-1252 cannot encode or XML cannot carry (only
                possible when validation was bypassed, e.g. ``model_construct``).
        """
        root = ET.Element("DOC_ARQ", {"xmlns": _NAMESPACE})
        _block(root, "DESC_FDO_157", doc.header)
        cotistas = ET.SubElement(root, "LISTA_COTSTS")
        for cotista in doc.cotistas:
            _block(cotistas, "COTST", cotista)
        xml_str, payload = render_xml(root)
        return deliver(xml_str, payload, output_path)
