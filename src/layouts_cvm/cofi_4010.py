"""CVM COFI 4010 (Balancete) — submission (envio) writer.

Produces the fixed-width ``.cvm`` file of the PadraoCOFI page: 71-position records, one header
per fund followed by its account records, and a single footer counting every record written.
"""

from collections.abc import Mapping

from layouts_cvm._internal.config.ports.submission_writer import SubmissionWriter
from layouts_cvm._internal.config.schemas.cofi_4010 import Cofi4010Document
from layouts_cvm._internal.utils.atomic_write import atomic_write_bytes
from layouts_cvm._internal.utils.cofi_4010_records import ENCODING, LINE_END, build_records
from layouts_cvm._internal.utils.xml_writer import coerce_document


class Cofi4010(SubmissionWriter[Cofi4010Document]):
    """Serialize a validated COFI 4010 document to the fixed-width ``.cvm`` format.

    Methods
    -------
    export(doc, output_path)
            Serialize the document to ASCII fixed-width records.
    """

    def export(
        self, doc: Cofi4010Document | Mapping[str, object], output_path: str | None = None
    ) -> str | None:
        """Serialize a validated Cofi4010Document to a fixed-width string or file.

        Parameters
        ----------
        doc : Cofi4010Document or Mapping
                Validated document model, or plain data to validate into one.
        output_path : Optional[str]
                Destination file path, written atomically as ASCII. If given, None is
                returned; otherwise the text is returned, by default None.

        Returns
        -------
        Optional[str]
                File text when output_path is None, else None.
        """
        cls_document = coerce_document(Cofi4010Document, doc)
        str_text = "".join(f"{str_rec}{LINE_END}" for str_rec in build_records(cls_document))
        if output_path is None:
            return str_text
        atomic_write_bytes(output_path, str_text.encode(ENCODING))
        return None
