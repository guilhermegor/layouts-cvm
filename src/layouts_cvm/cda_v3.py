"""CVM CDA V3 (portfolio composition report) — submission (envio) writer.

Produces CVM-compliant CDA V3 XML (namespace ``urn:cda``, ``VERSAO`` 3.0) from validated
schema models. The V3 and V4 layouts share the tag order, the decimal scales and the
document skeleton (see :mod:`layouts_cvm._internal.config.schemas.cda_v3` for the measured delta),
and the header carries the version, so this writer delegates to the V4 writer's public ``export``
instead of copying its builder.
"""

from collections.abc import Mapping

from layouts_cvm._internal.config.ports.submission_writer import SubmissionWriter
from layouts_cvm._internal.config.schemas.cda_v3 import CdaV3Document
from layouts_cvm._internal.utils.xml_writer import coerce_document
from layouts_cvm.cda import Cda


class CdaV3(SubmissionWriter[CdaV3Document]):
    """Serialize a validated CDA V3 document to CVM-compliant XML.

    Methods
    -------
    export(doc, output_path)
        Serialize a validated V3 document to a CVM-compliant XML string.
    """

    def export(
        self, doc: CdaV3Document | Mapping[str, object], output_path: str | None = None
    ) -> str | None:
        """Serialize a validated CdaV3Document to a CVM-compliant XML string.

        Parameters
        ----------
        doc : CdaV3Document or Mapping
            Validated document model, or plain data to validate into one.
        output_path : Optional[str]
            Destination file path, written atomically as windows-1252. If given, None is
            returned; otherwise the XML string is returned, by default None.

        Returns
        -------
        Optional[str]
            XML string when output_path is None, else None.
        """
        document = coerce_document(CdaV3Document, doc)
        return Cda().export(document, output_path)
