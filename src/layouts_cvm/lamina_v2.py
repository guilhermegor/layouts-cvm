"""CVM Lâmina de Fundos V2 — submission (envio) writer.

Produces the Lâmina V2 XML (``VERSAO`` 2.0) from a validated :class:`LaminaV2Document`. V2 and
V3 share the prolog, namespace and tag walk, and the V2 schema extends the V3 one, so this
writer delegates to the V3 writer's public ``export`` instead of copying its builder.
"""

from layouts_cvm._internal.config.ports.submission_writer import SubmissionWriter
from layouts_cvm.lamina import Lamina
from layouts_cvm.schemas.lamina_v2 import LaminaV2Document


class LaminaV2(SubmissionWriter[LaminaV2Document]):
    """Serialize a validated Lâmina V2 document to CVM-compliant XML.

    Methods
    -------
    export(doc, output_path)
            Serialize a validated V2 document to windows-1252 XML.
    """

    def export(self, doc: LaminaV2Document, output_path: str | None = None) -> str | None:
        """Serialize a validated LaminaV2Document to a CVM-compliant XML string or file.

        Parameters
        ----------
        doc : LaminaV2Document
                Fully validated V2 document model.
        output_path : Optional[str]
                Destination file path, written atomically as windows-1252. If given, None
                is returned; otherwise the XML string is returned, by default None.

        Returns
        -------
        Optional[str]
                XML string when output_path is None, else None.
        """
        return Lamina().export(doc, output_path)
