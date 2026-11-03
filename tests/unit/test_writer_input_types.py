"""The writers accept a document model or plain data, and reject anything else."""

import gzip
import json
from pathlib import Path

from pydantic import ValidationError
import pytest

import layouts_cvm


_PATH_GOLDEN = Path(__file__).parent.parent / "golden" / "submission_xml.json.gz"
_CASE = json.loads(gzip.decompress(_PATH_GOLDEN.read_bytes()))["cases"][0]


def _writer() -> object:
    """Build the first golden case's writer.

    Returns
    -------
    object
        A writer instance.
    """
    return getattr(layouts_cvm, _CASE["writer"])()


def test_export_wrong_type_raises_type_error() -> None:
    """A value that is neither a model nor a mapping fails the runtime type check."""
    with pytest.raises(TypeError):
        _writer().export(42, None, **_CASE["kwargs"])


def test_export_invalid_mapping_raises_validation_error() -> None:
    """A mapping that does not satisfy the schema is rejected by the writer."""
    with pytest.raises(ValidationError):
        _writer().export({}, None, **_CASE["kwargs"])


def test_export_mapping_and_model_agree() -> None:
    """The mapping path emits the golden string."""
    dict_doc = json.loads(_CASE["doc_json"])

    assert _writer().export(dict_doc, None, **_CASE["kwargs"]) == _CASE["xml"]
