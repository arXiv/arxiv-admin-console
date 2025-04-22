from pydantic import BaseModel

class DocInCategoryModel(BaseModel):
    document_id: str
    archive: str
    subject_class: str
    is_primary: bool

    class Config:
        from_attributes = True
