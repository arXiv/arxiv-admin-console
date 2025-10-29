
from pydantic import BaseModel

class BasePaperMessage(BaseModel):
    """Good for HTML regen"""
    paper_id: str
    version: int


class PaperMessage(BasePaperMessage):
    """Good for sync-to-gcp"""
    submission_id: int
    document_id: int
    type: str
    src_ext: str = ""
