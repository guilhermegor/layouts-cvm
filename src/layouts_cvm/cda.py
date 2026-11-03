"""CVM CDA (portfolio composition report) — submission (envio) writer.

Produces CVM-compliant CDA V4 XML (namespace ``urn:cda``) from validated schema models.
Pure logic plus file I/O at the edges — no network.
"""

from collections.abc import Mapping
from decimal import Decimal
from xml.etree import ElementTree as ET  # noqa: S405

from layouts_cvm._internal.config.ports.submission_writer import SubmissionWriter
from layouts_cvm._internal.config.schemas.cda import CdaDocument, CdaInform
from layouts_cvm._internal.utils.typing import type_checker
from layouts_cvm._internal.utils.xml_writer import (
    DocModel,
    coerce_document,
    deliver_text,
    fill_children,
)


_PLACES: dict[str, int] = {
    "VL_PL": 2,
    "VL_VENDAS_NEGOC": 2,
    "VL_AQUIS_NEGOC": 2,
    "MERC_POS_FIM": 2,
    "QTDE_VENDAS_NEGOC": 6,
    "QTDE_AQUIS_NEGOC": 6,
    "QTDE_POS_FIM": 6,
    "TIT_POS_FIX_PR_INDEX": 6,
    "TIT_POS_FIX_CUPOM": 6,
    "TIT_PRE_FIX_TAXA_CONTR": 6,
}
_ID_TAGS = frozenset({"CNPJ_FDO", "CNPJ_EMIS", "CNPJ_INSTIT_FINANC", "NR_PF_PJ_EMIS"})
_WRAPPERS = frozenset(
    {
        "aplic",
        "negoc",
        "pos_fim",
        "ativo_ext",
        "emis",
        "classif_risco",
        "tit_pos_fix_index",
    }
)


@type_checker
def _decimal_text(tag: str, value: Decimal) -> str:
    """Render a decimal with a comma separator at the tag's declared scale.

    Parameters
    ----------
    tag : str
        The XML tag; its scale comes from the page.
    value : Decimal
        The amount; negative zero is written as zero.

    Returns
    -------
    str
        The element text.
    """
    value = abs(value) if value == 0 else value
    places = _PLACES.get(tag)
    return (f"{value:f}" if places is None else f"{value:.{places}f}").replace(".", ",")


@type_checker
def _leaf_text(tag: str, value: object) -> str:
    """Render one leaf value: decimals at scale, identifiers without leading zeros.

    Parameters
    ----------
    tag : str
        The XML tag.
    value : object
        The value to render.

    Returns
    -------
    str
        The element text.
    """
    return (
        _decimal_text(tag, value)
        if isinstance(value, Decimal)
        else str(value).lstrip("0")
        if tag in _ID_TAGS
        else str(value)
    )


@type_checker
def _leaf(node: ET.Element, tag: str, value: object) -> None:
    """Append a text element rendered by :func:`_leaf_text`.

    Parameters
    ----------
    node : ET.Element
        Parent element.
    tag : str
        Tag name.
    value : object
        Value to render.
    """
    ET.SubElement(node, tag).text = _leaf_text(tag, value)


@type_checker
def _emit(node: ET.Element, name: str, value: object) -> None:
    """Emit one set field: a wrapper becomes a block, anything else a leaf.

    Parameters
    ----------
    node : ET.Element
        Parent element.
    name : str
        The schema field name.
    value : object
        The field value.
    """
    _build_model(ET.SubElement(node, name.upper()), value) if name in _WRAPPERS else _leaf(
        node, name.upper(), value
    )


@type_checker
def _build_model(node: ET.Element, model: DocModel) -> None:
    """Emit a model's set fields as children, in declaration order (the spec's order).

    Parameters
    ----------
    node : ET.Element
        Parent element.
    model : DocModel
        Model whose set fields become child elements.
    """
    for name, value in [
        (name, getattr(model, name))
        for name in type(model).model_fields
        if getattr(model, name) is not None
    ]:
        _emit(node, name, value)


@type_checker
def _build_inform(node: ET.Element, inform: CdaInform) -> None:
    """Fill one INFORM element, blocks in the page's mandated order.

    Parameters
    ----------
    node : ET.Element
        The INFORM element.
    inform : CdaInform
        Validated fund model.
    """
    _leaf(node, "CNPJ_FDO", inform.cnpj_fdo)
    _leaf(node, "VL_PL", inform.vl_pl)
    ativ = ET.SubElement(node, "LISTA_ATIV")
    for name, item in [
        (blk, itm) for blk in CdaInform.BLOCK_ORDER for itm in getattr(inform, blk)
    ]:
        _build_model(ET.SubElement(ativ, name.upper()), item)


class Cda(SubmissionWriter[CdaDocument]):
    """Serialize a validated CDA document to CVM-compliant XML.

    Concrete :class:`SubmissionWriter` for the CDA V4 XML standard.

    Methods
    -------
    export(doc, output_path)
        Serialize a validated document to a CVM-compliant XML string.
    """

    def export(
        self, doc: CdaDocument | Mapping[str, object], output_path: str | None = None
    ) -> str | None:
        """Serialize a validated CdaDocument to a CVM-compliant XML string.

        Parameters
        ----------
        doc : CdaDocument or Mapping
            Validated document model, or plain data to validate into one.
        output_path : Optional[str]
            Destination file path (written as windows-1252). If given, None is
            returned; otherwise the XML string is returned, by default None.

        Returns
        -------
        Optional[str]
            XML string when output_path is None, else None.
        """
        document = coerce_document(CdaDocument, doc)
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
