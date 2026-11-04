"""CVM COFI 4016 (Balanço) — fixed-width submission writer.

Produces the 71-column ``.cvm`` text file of ``PadraoCOFI.aspx`` from a validated
:class:`Cofi4016Document`: per fund a header record and its account records, then one footer
record carrying the total record count.
"""

from collections.abc import Mapping
from decimal import Decimal
from itertools import chain

from layouts_cvm._internal.config.ports.submission_writer import SubmissionWriter
from layouts_cvm._internal.config.schemas.cofi_4016 import (
    Cofi4016Account,
    Cofi4016Document,
    Cofi4016Fund,
)
from layouts_cvm._internal.utils.atomic_write import atomic_write_bytes
from layouts_cvm._internal.utils.typing import type_checker
from layouts_cvm._internal.utils.xml_writer import coerce_document


_ENCODING = "ascii"
_LINE_END = "\r\n"
_DOCUMENT_CODE = "4016"
_RECORD_WIDTH = 71
_VALUE_WIDTH = 18
_CENTS = Decimal(100)
_MAX_RECORDS = 999_999


@type_checker
def _pad(str_text: str) -> str:
    """Right-pad a record with blanks to the fixed 71-column width.

    Parameters
    ----------
    str_text : str
        The record content so far.

    Returns
    -------
    str
        The 71-character record.
    """
    return str_text.ljust(_RECORD_WIDTH)


@type_checker
def _render_value(decimal_value: Decimal) -> str:
    """Render one value column: 18 digits of absolute cents, then its sign character.

    Parameters
    ----------
    decimal_value : Decimal
        The signed value, two decimal places.

    Returns
    -------
    str
        19 characters: zero-filled magnitude plus ``+`` or ``-``.
    """
    str_digits = str(int(abs(decimal_value) * _CENTS)).zfill(_VALUE_WIDTH)
    return str_digits + ("-" if decimal_value < 0 else "+")


@type_checker
def _render_header(cls_fund: Cofi4016Fund, str_competence: str) -> str:
    """Render the control (header) record of one fund.

    Parameters
    ----------
    cls_fund : Cofi4016Fund
        The fund being written.
    str_competence : str
        The competence as ``MM/AAAA``.

    Returns
    -------
    str
        The 71-character record.
    """
    str_mmyyyy = str_competence.replace("/", "")
    return _pad(f"#C1{_DOCUMENT_CODE}{cls_fund.cnpj_fundo}{' ' * 8}{str_mmyyyy}")


@type_checker
def _render_account(cls_account: Cofi4016Account) -> str:
    """Render one account record.

    Parameters
    ----------
    cls_account : Cofi4016Account
        The account and its three value columns.

    Returns
    -------
    str
        The 71-character record.
    """
    str_values = "".join(
        _render_value(decimal_value)
        for decimal_value in (cls_account.total, cls_account.ate_90_dias, cls_account.apos_90_dias)
    )
    return _pad(f"{cls_account.conta}{' ' * 4}{str_values}")


@type_checker
def _render_footer(int_records: int) -> str:
    """Render the control (footer) record.

    Parameters
    ----------
    int_records : int
        Records written in the file, footer included.

    Returns
    -------
    str
        The 71-character record.
    """
    return _pad(f"@1{int_records:06d}")


@type_checker
def _render_fund(cls_fund: Cofi4016Fund, str_competence: str) -> list[str]:
    """Render one fund: its header record followed by its account records.

    Parameters
    ----------
    cls_fund : Cofi4016Fund
        The fund being written.
    str_competence : str
        The competence as ``MM/AAAA``.

    Returns
    -------
    list[str]
        The fund's records in file order.
    """
    return [
        _render_header(cls_fund, str_competence),
        *(_render_account(cls_acc) for cls_acc in cls_fund.contas),
    ]


@type_checker
def _render_records(cls_document: Cofi4016Document) -> list[str]:
    """Render every record of the file, footer last.

    Parameters
    ----------
    cls_document : Cofi4016Document
        The validated document.

    Returns
    -------
    list[str]
        The records in file order.

    Raises
    ------
    ValueError
        If the record count does not fit the 6-digit footer field.
    """
    list_records = list(
        chain.from_iterable(
            _render_fund(cls_fund, cls_document.dt_compt) for cls_fund in cls_document.fundos
        )
    )
    if len(list_records) + 1 > _MAX_RECORDS:
        raise ValueError(f"a COFI file holds at most {_MAX_RECORDS} records")
    list_records.append(_render_footer(len(list_records) + 1))
    return list_records


class Cofi4016(SubmissionWriter[Cofi4016Document]):
    """Serialize a validated COFI 4016 document to the fixed-width ``.cvm`` text.

    Methods
    -------
    export(doc, output_path)
        Serialize a document to ASCII fixed-width records, CRLF-terminated.
    """

    def export(
        self, doc: Cofi4016Document | Mapping[str, object], output_path: str | None = None
    ) -> str | None:
        """Serialize a COFI 4016 document to text, or write it to a file.

        Parameters
        ----------
        doc : Cofi4016Document or Mapping
            Validated document model, or plain data to validate into one.
        output_path : str, optional
            Destination file, written atomically as ASCII. If given, None is returned.

        Returns
        -------
        str or None
            The file text when output_path is None, else None.
        """
        cls_document = coerce_document(Cofi4016Document, doc)
        str_text = "".join(str_rec + _LINE_END for str_rec in _render_records(cls_document))
        if output_path is None:
            return str_text
        atomic_write_bytes(output_path, str_text.encode(_ENCODING))
        return None
