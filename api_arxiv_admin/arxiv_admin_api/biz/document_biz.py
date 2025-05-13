from arxiv.db.models import Document, PaperOwner
from flask import session
from sqlalchemy.orm import Session
from sqlalchemy import and_


def document_summary(session: Session, user_id: str) -> dict:
    """
    Summary of user's current state of papers.
    """

    # Shared filter: exclude rejected, pending, replace
    valid_paper_id_filter = and_(
        ~Document.paper_id.like('rejected/%'),
        ~Document.paper_id.like('pending/%'),
        ~Document.paper_id.like('replace/%')
    )

    # Base query for documents owned or submitted by user
    base_document_filter = and_(
        Document.submitter_id == user_id,
        valid_paper_id_filter
    )

    submit_count = session.query(Document).filter(base_document_filter).count()

    owned_filter = and_(
        PaperOwner.user_id == user_id,
        valid_paper_id_filter
    )

    owns_count = (
        session.query(PaperOwner)
        .join(Document, PaperOwner.document_id == Document.document_id)
        .filter(owned_filter)
        .count()
    )

    authored_filter = and_(
        PaperOwner.user_id == user_id,
        PaperOwner.flag_author == 1,
        valid_paper_id_filter
    )

    author_count = (
        session.query(PaperOwner)
        .join(Document, PaperOwner.document_id == Document.document_id)
        .filter(authored_filter)
        .count()
    )

    return {
        "submitted_count": submit_count,
        "owns_count": owns_count,
        "authored_count": author_count,
    }