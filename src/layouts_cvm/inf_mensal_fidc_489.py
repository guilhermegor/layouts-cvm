"""CVM Informe Mensal FIDC — ICVM 489 submission (envio) writer (until 2019-11-01).

Produces the ``urn:fidc`` XML of ``PadraoXMLMensalFIDC489.asp`` from a validated
:class:`InfMensalFidc489Document`. The element order is the schema's field order and every tag
is the field name (or alias), exactly as for the ICVM 576 layout, so this writer shares the
private ``_BaseFidcWriter`` with ``InfMensalFidc`` and only names the document model it
validates. Pure logic plus file I/O at the edges — no network.
"""

from layouts_cvm._base_fidc_writer import _BaseFidcWriter
from layouts_cvm._internal.config.schemas.inf_mensal_fidc_489 import InfMensalFidc489Document


class InfMensalFidc489(_BaseFidcWriter[InfMensalFidc489Document]):
    """Serialize a validated Informe Mensal FIDC (ICVM 489) document to CVM-compliant XML.

    Methods
    -------
    export(doc, output_path)
            Serialize a validated document to a CVM-compliant XML string or file.
    """
