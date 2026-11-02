"""CVM Atualização do Cadastro de Ativos — submission (envio) writer.

Produces CVM-compliant asset-register update XML (``COD_DOC=2``, no namespace) from
validated schema models. Pure logic plus file I/O at the edges — no network.
"""

from xml.etree import ElementTree as ET  # noqa: S405

from layouts_cvm._internal.config.ports.submission_writer import SubmissionWriter
from layouts_cvm._internal.utils.typing import type_checker
from layouts_cvm._internal.utils.xml_writer import deliver_text, fill_children
from layouts_cvm.schemas.cadastro_ativos import (
    CadastroAtivosDocument,
    CadastroAtivosRow,
)


@type_checker
def _row_pairs(row: CadastroAtivosRow) -> list[tuple[str, str]]:
    """List a row's set fields as ``(TAG, text)`` in declaration order (the page's tag order).

    Parameters
    ----------
    row : CadastroAtivosRow
        Validated row.

    Returns
    -------
    list of tuple of (str, str)
        One pair per field that is not ``None``.
    """
    return [
        (name.upper(), str(getattr(row, name)))
        for name in type(row).model_fields
        if getattr(row, name) is not None
    ]


class CadastroAtivos(SubmissionWriter[CadastroAtivosDocument]):
    """Serialize a validated Cadastro de Ativos document to CVM-compliant XML.

    Methods
    -------
    export(doc, output_path)
            Serialize a validated document to a CVM-compliant XML string.
    """

    def export(self, doc: CadastroAtivosDocument, output_path: str | None = None) -> str | None:
        """Serialize a validated CadastroAtivosDocument to a CVM-compliant XML string.

        Parameters
        ----------
        doc : CadastroAtivosDocument
                Fully validated document model.
        output_path : Optional[str]
                Destination file path (written as windows-1252). If given, None is
                returned; otherwise the XML string is returned, by default None.

        Returns
        -------
        Optional[str]
                XML string when output_path is None, else None.
        """
        root = ET.Element("DOC_ARQ")
        fill_children(
            ET.SubElement(root, "DESC_MERC"),
            [
                ("COD_DOC", str(doc.header.cod_doc)),
                ("CNPJ_MERC", str(doc.header.cnpj_merc)),
                ("DT_GERAC_ARQ", str(doc.header.dt_gerac_arq)),
            ],
        )
        ativos = ET.SubElement(root, "ATIVOS")
        for row in doc.rows:
            fill_children(ET.SubElement(ativos, "ROW_ATIVO"), _row_pairs(row))
        ET.indent(root, space="    ")
        xml_str = '<?xml version="1.0" encoding="windows-1252"?>\n' + ET.tostring(
            root, encoding="unicode"
        )
        return deliver_text(xml_str, output_path)
