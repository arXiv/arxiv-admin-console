"""arXiv paper display routes."""
from typing import Optional, Callable
from sqlalchemy.orm import Session
from arxiv.db.models import Base, Metadata, Document, Submission
from .submission_categories_biz import update_submissions_categories

TransformFn = Callable[[Session, "Base", str, "Base", str | None], bool]

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
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"{src.__class__} {column} {value!r} != {dest.__class__} {dest_column} {dest_value!r}")
    return False


def md_to_sub_cats(session: Session, src: Base, column: str, dest: Base, dest_column: str | None = None) -> bool:
    _dest_column = dest_column if dest_column is not None else column
    value = getattr(src, column)
    cats = value.split(" ")
    assert isinstance(dest, Submission)
    return update_submissions_categories(session, cats, dest)


metadata_xfer_map: dict[str, dict[str, dict[str, tuple[TransformFn, str | None]]]] = {
    "abs_categories": {
        "document": {"transform": (md_to_sub_cats, None)},
    },
    "authors": {
        "document": {"transform": (xfer_column_value, None)},
        "metadata": {"transform": (xfer_column_value, None)},
    },
    "document_id": {
        "document": {"transform": (verify_column_values, None)},
        "metadata": {"transform": (verify_column_values, None)},
    },
    "paper_id": {
        "document": {"transform": (verify_column_values, None)},
        "metadata": {"transform": (verify_column_values, None)},
    },
    "submitter_email": {
        "document": {"transform": (xfer_column_value, None)},
        "metadata": {"transform": (xfer_column_value, None)},
    },
    "submitter_id": {
        "document": {"transform": (xfer_column_value, None)},
        "metadata": {"transform": (xfer_column_value, None)},
    },
    "title": {
        "document": {"transform": (xfer_column_value, None)},
        "metadata": {"transform": (xfer_column_value, None)},
    },
}


def propagate_metadata_to_document(session: Session, md: Metadata, column_name: str, doc: Document) -> bool:

    specs: Optional[dict[str, dict[str, tuple[TransformFn, str | None]]]] = metadata_xfer_map.get(column_name)
    if specs is None:
        return False

    doc_spec: Optional[dict[str, tuple[TransformFn, str | None]]] = specs.get("document")
    if doc_spec is None:
        return False

    transform, dest_column = doc_spec.get("transform", (None, None))
    if transform is not None:
        return transform(session, md, column_name, doc, dest_column)
    return False
