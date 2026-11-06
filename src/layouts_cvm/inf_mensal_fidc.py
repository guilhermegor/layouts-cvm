"""CVM Informe Mensal FIDC — submission (envio) writer (ICVM 576, from 2019-11-01).

Produces the CVM-compliant ``urn:fidc`` XML from validated schema models. The element
order is the schema's attribute order and each tag is the attribute's name (or alias),
so the writer carries no per-field code: the schema is the single source of the layout.
The rendering lives in the private ``_BaseFidcWriter``, shared with the ICVM 489 writer.
Pure logic plus file I/O at the edges — no network.
"""

from layouts_cvm._base_fidc_writer import _BaseFidcWriter
from layouts_cvm._internal.config.schemas.inf_mensal_fidc import InfMensalFidcDocument


class InfMensalFidc(_BaseFidcWriter[InfMensalFidcDocument]):
    """Serialize a validated Informe Mensal FIDC document to CVM-compliant XML.

    Methods
    -------
    export(doc, output_path)
            Serialize a validated document to a CVM-compliant XML string or file.
    """

    _document_model = InfMensalFidcDocument
