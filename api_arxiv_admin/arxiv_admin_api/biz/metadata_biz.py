"""arXiv paper display routes."""
from arxiv.db import Base
from arxiv.base import logging
from arxiv.db.models import Metadata, Document, Submission
from sqlalchemy.orm import Session

from .submission_categories_biz import update_submissions_categories

logger = logging.getLogger(__name__)

def xfer_column_value(_session: Session, src: Base, column: str, dest: Base, dest_column: str | None = None):
    value = getattr(src, column)
    dest_column = dest_column if dest_column is not None else column
    dest_value = getattr(dest, dest_column)
    if dest_value != value:
        setattr(dest, dest_column, value)
        return True
    return False


def verify_column_values(_session: Session, src: Base, column: str, dest: Base, dest_column: str | None = None):
    dest_column = dest_column if dest_column is not None else column
    value = getattr(src, column)
    dest_value = getattr(dest, dest_column)
    if dest_value != value:
        logger.warning(f"{src.__class__} {column} {value!r} != {dest.__class__} {dest_column} {dest_value!r}")
    return False


def md_to_sub_cats(session: Session, src: Base, column: str, dest: Base, dest_column: str | None = None) -> bool:
    _dest_column = dest_column if dest_column is not None else column
    value = getattr(src, column)
    cats = value.split(" ")
    assert isinstance(dest, Submission)
    return update_submissions_categories(session, cats, dest)


metadata_xfer_map = {
    "abs_categories": {
        Document: {"transform": (md_to_sub_cats, None)},
    },
    "authors": {
        Document: {"transform": (xfer_column_value, None)},
        Metadata: {"transform": (xfer_column_value, None)},
    },
    "document_id": {
        Document: {"transform": (verify_column_values, None)},
        Metadata: {"transform": (verify_column_values, None)},
    },
    "paper_id": {
        Document: {"transform": (verify_column_values, None)},
        Metadata: {"transform": (verify_column_values, None)},
    },
    "submitter_email": {
        Document: {"transform": (xfer_column_value, None)},
        Metadata: {"transform": (xfer_column_value, None)},
    },
    "submitter_id": {
        Document: {"transform": (xfer_column_value, None)},
        Metadata: {"transform": (xfer_column_value, None)},
    },
    "title": {
        Document: {"transform": (xfer_column_value, None)},
        Metadata: {"transform": (xfer_column_value, None)},
    },
}


def propagate_metadata_to_document(session: Session, md: Metadata, column_name: str, doc: Document) -> bool:
    specs = metadata_xfer_map.get(column_name)
    if specs is None:
        return False

    doc_spec = specs.get(Document)
    if doc_spec is None:
        return False

    transform, dest_column = doc_spec.get("transform")
    if transform is not None:
        return transform(session, md, column_name, doc, dest_column)
    return False
