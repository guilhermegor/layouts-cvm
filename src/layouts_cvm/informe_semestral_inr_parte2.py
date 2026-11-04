"""CVM Semiannual Non-Resident Investor Report, Part II — submission (envio) writer.

Produces the Informe Semestral de INR Part II XML (``COD_DOC`` 70, namespace ``urn:cda``) from a
validated :class:`InformeSemestralInrParte2Document`. The schema declares its fields in XML
order, so the serialiser is the shared recursive walk over ``model_fields``. Part II carries the
applications only: Part I (``COD_DOC`` 69) is a separate file, and the Informe Semestral is
complete only with both.
"""

from collections.abc import Mapping
from xml.etree import ElementTree as ET  # noqa: S405  # builds XML, never parses untrusted input

from layouts_cvm._internal.config.ports.submission_writer import SubmissionWriter
from layouts_cvm._internal.config.schemas.informe_semestral_inr_parte2 import (
    InformeSemestralInrParte2Document,
)
from layouts_cvm._internal.utils.typing import type_checker
from layouts_cvm._internal.utils.xml_writer import (
    append_field,
    coerce_document,
    deliver,
    render_xml,
)


_NAMESPACE = "urn:cda"
_ID_TAGS = frozenset({"CNPJ_FDO", "CNPJ_EMIS", "CNPJ_INSTIT_FINANC", "NR_PF_PJ_EMIS"})


@type_checker
def _omit_leading_zeros(root: ET.Element) -> None:
    """Drop the zero filler of every CPF/CNPJ element, as the page requires.

    Parameters
    ----------
    root : ET.Element
        The document element, modified in place.
    """
    for node in [node for node in root.iter() if node.tag in _ID_TAGS]:
        node.text = (node.text or "").lstrip("0")


class InformeSemestralInrParte2(SubmissionWriter[InformeSemestralInrParte2Document]):
    """Serialize a validated Informe Semestral INR Part II document to CVM-compliant XML.

    Methods
    -------
    export(doc, output_path)
        Serialize a validated document to windows-1252 XML.
    """

    def export(
        self,
        doc: InformeSemestralInrParte2Document | Mapping[str, object],
        output_path: str | None = None,
    ) -> str | None:
        """Serialize a validated Part II document to a CVM-compliant XML string or file.

        Parameters
        ----------
        doc : InformeSemestralInrParte2Document or Mapping
            Validated document model, or plain data to validate into one.
        output_path : Optional[str]
            Destination file, written atomically as windows-1252. If given, None is
            returned; otherwise the XML string is returned, by default None.

        Returns
        -------
        Optional[str]
            XML string when output_path is None, else None.
        """
        document = coerce_document(InformeSemestralInrParte2Document, doc)
        root = ET.Element("DOC_ARQ", {"xmlns": _NAMESPACE})
        for name in type(document).model_fields:
            append_field(root, name, getattr(document, name))
        _omit_leading_zeros(root)
        xml_str, payload = render_xml(root)
        return deliver(xml_str, payload, output_path)
