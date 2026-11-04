"""Shared XML-standard schemas (Pydantic models) for the CVM file standards.

Direction-neutral contracts consumed by both the ``submission`` section (models →
XML) and the future ``ingestion`` section (XML → models). One module per CVM
standard, imported from its own module: there is no aggregator to keep in sync.
Ships in the wheel under ``_internal`` and is not public API: the writers take
plain data and validate it into these models (``coerce_document``).
"""
