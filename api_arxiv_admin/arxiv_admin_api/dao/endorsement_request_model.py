from pydantic import BaseModel
from typing import Optional

class EndorsementRequestRequestModel(BaseModel):
    endorsee_id: Optional[int]
    archive: str
    subject_class: str
    pass

