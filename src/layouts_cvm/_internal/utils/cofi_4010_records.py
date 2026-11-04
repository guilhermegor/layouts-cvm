"""Record builders for the COFI 4010 (Balancete) fixed-width file.

Pure functions turning a validated document into 71-position records: one header per fund,
its account records, and a single footer counting every record written.
"""

from decimal import Decimal

from layouts_cvm._internal.config.schemas.cofi_4010 import (
    VALUE_DIGITS,
    VALUE_SCALE,
    Cofi4010Account,
    Cofi4010Document,
    Cofi4010Fund,
)
from layouts_cvm._internal.utils.typing import type_checker


ENCODING = "ascii"
RECORD_LENGTH = 71
LINE_END = "\r\n"
_HEADER_ID = "#C1"
_FOOTER_ID = "@1"
_FILLER_ACCOUNT = 4
_FILLER_HEADER_MID = 8
_FILLER_HEADER_END = 36


@type_checker
def format_value(decimal_value: Decimal) -> str:
    """Render one value column: 18 zero-padded digits of the absolute value, then its sign.

    Parameters
    ----------
    decimal_value : Decimal
        The (already scale-truncated) value.

    Returns
    -------
    str
        19 characters; the sign is ``-`` for a negative value and a blank otherwise.
    """
    int_units = int(abs(decimal_value).scaleb(VALUE_SCALE))
    str_sign = "-" if decimal_value < 0 else " "
    return f"{int_units:0{VALUE_DIGITS}d}{str_sign}"


@type_checker
def build_header(cls_fund: Cofi4010Fund) -> str:
    """Build the control record that opens one fund.

    Parameters
    ----------
    cls_fund : Cofi4010Fund
        The fund being written.

    Returns
    -------
    str
        A 71-character header record.
    """
    return (
        f"{_HEADER_ID}{cls_fund.cod_doc}{cls_fund.cnpj_fundo}{' ' * _FILLER_HEADER_MID}"
        f"{cls_fund.competencia}{' ' * _FILLER_HEADER_END}"
    )


@type_checker
def build_account(cls_account: Cofi4010Account) -> str:
    """Build one account record.

    Parameters
    ----------
    cls_account : Cofi4010Account
        The account with its three value columns.

    Returns
    -------
    str
        A 71-character account record.
    """
    return (
        f"{cls_account.conta}{' ' * _FILLER_ACCOUNT}{format_value(cls_account.total)}"
        f"{format_value(cls_account.ate_90_dias)}{format_value(cls_account.apos_90_dias)}"
    )


@type_checker
def build_footer(int_records: int) -> str:
    """Build the closing control record.

    Parameters
    ----------
    int_records : int
        Total records in the file, footer included.

    Returns
    -------
    str
        A 71-character footer record.
    """
    return f"{_FOOTER_ID}{int_records:06d}".ljust(RECORD_LENGTH)


@type_checker
def build_records(cls_document: Cofi4010Document) -> list[str]:
    """Build every record of the file, footer last.

    Parameters
    ----------
    cls_document : Cofi4010Document
        The validated document.

    Returns
    -------
    list[str]
        Header and account records of each fund, then the footer.
    """
    list_records: list[str] = []
    for cls_fund in cls_document.fundos:
        list_records.append(build_header(cls_fund))
        list_records.extend(build_account(cls_account) for cls_account in cls_fund.contas)
    list_records.append(build_footer(len(list_records) + 1))
    return list_records
