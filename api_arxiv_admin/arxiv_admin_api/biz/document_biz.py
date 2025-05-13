from arxiv.db.models import Document, PaperOwner
from sqlalchemy.orm import Session
from sqlalchemy import and_


def document_summary(session: Session, user_id: str) -> dict:
    """
    Summary of user's current state of papers.
    """

    submitted = session.query(Document).filter(
        and_(
            Document.submitter_id == user_id,
            ~Document.paper_id.like('rejected/%'),
            ~Document.paper_id.like('pending/%'),
            ~Document.paper_id.like('replace/%')))

    submit_count = submitted.count()

    # Get owned papers
    owns_count = (
        submitted.join(PaperOwner, PaperOwner.document_id == Document.document_id)
        .filter(PaperOwner.user_id == user_id)
        .count()
    )

    author_count = (
        submitted.join(PaperOwner, PaperOwner.document_id == Document.document_id)
        .filter(and_(
            PaperOwner.user_id == user_id,
            PaperOwner.flag_author == 1
        ))
        .count()
    )

    return {
        "submitted_count": submit_count,
        "owns_count": owns_count,
        "authored_count": author_count,
    }
