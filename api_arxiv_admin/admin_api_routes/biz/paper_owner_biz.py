from datetime import datetime
from typing import Tuple, List
from sqlalchemy.orm import Session, aliased
from arxiv.db.models import PaperOwner, PaperPw, Document
from random import randint

def add_paper_owner(
        session: Session, user_id: str, document_id: str, paper_pw: str,
        timestamp: datetime, remote_addr: str, remote_host: str, tracking_cookie: str,
        ) -> Tuple[PaperOwner | None, str]:
    """
    Adds a paper owner to the database.

    Args:
        session (Session): The SQLAlchemy database session.
        user_id (str): The ID of the user who is being assigned ownership.
        document_id (str): The ID of the document being assigned.
        paper_pw (str): The password associated with the paper.
        timestamp (datetime): The timestamp of when the ownership was assigned.
        remote_addr (str): The IP address of the requester.
        remote_host (str): The hostname of the requester.
        tracking_cookie (str): The tracking cookie associated with the request.

    Returns:
        Tuple[Optional[PaperOwner], str]: A tuple containing the created `PaperOwner` object (or None if failed)
        and a status message indicating success or failure.
    """
    pw = aliased(PaperPw)
    document = aliased(Document)
    paper = (
        session.query(pw, document)
        .join(Document, PaperPw.document_id == Document.document_id)
        .filter(Document.document_id == document_id)
        .first()
    )

    if not paper:
        return None, "Paper password recost is not found"

    assert(paper.pw.password_storage == 0)

    if paper.pw.password_enc != paper_pw:
        return None, "Invalid paper password"

    # Register user as owner
    new_owner = PaperOwner(
        user_id=user_id,
        document_id=paper.document.document_id,
        date=timestamp,
        added_by=user_id,
        remote_addr=remote_addr,
        remote_host=remote_host,
        tracking_cookie=tracking_cookie,
        valid=True,
        flag_author=False,
        flag_auto=False,
    )

    session.add(new_owner)
    return new_owner, "Success"


def generate_paper_pw() -> str:
    length = 5
    letters = "abcdefghijklmnopqrstuvwxyz0123456789"
    pw = ""
    n = len(letters)
    rv = randint(0, n ** length )
    for i in range(length):
        pw = pw + letters[rv % n]
        rv = int(rv / n)
    return pw



def update_paper_ownership(session: Session,
                           user_id: str,
                           owning: [int],
                           disowning: [int]
                           ) -> Tuple[List[int], List[int]]:
    """
    Updates paper authorship status for the given user.

    This function updates the `flag_author` status for papers owned by the specified user.
    It modifies the database records by setting `flag_author` to `1` for papers in the
    `owning` list and `0` for papers in the `disowning` list.

    Args:
        session (Session): The SQLAlchemy session used to interact with the database.
        user_id (str): The ID of the user whose paper ownership status is being updated.
        owning (list[int]): A list of document IDs that should be marked as authored (flag_author=1).
        disowning (list[int]): A list of document IDs that should be marked as not authored (flag_author=0).

    Returns:
        Tuple[List[int], List[int]]: A tuple containing two lists:
            - The first list includes document IDs that were successfully marked as authored.
            - The second list includes document IDs that were successfully marked as not authored.

    Notes:
        - The function queries the database for papers belonging to the user before making changes.
        - Updates are performed in memory, and changes are committed to the database at the end.
        - If a document ID is not found in the database, it is ignored.
    """

    # Fetch papers owned by the user
    papers = session.query(PaperOwner).filter(
        PaperOwner.user_id == user_id,
        PaperOwner.document_id.in_(owning + disowning)
    ).all()

    # Modify objects in Python
    owning_as_set = set(owning)
    disowning_as_set = set(disowning)
    result = ([], [])
    for paper in papers:
        if paper.document_id in owning_as_set:
            paper.flag_author = 1
            result[0].append(paper.document_id)
        elif paper.document_id in disowning_as_set:
            paper.flag_author = 0
            result[1].append(paper.document_id)

    # Commit changes
    session.commit()
    return result
