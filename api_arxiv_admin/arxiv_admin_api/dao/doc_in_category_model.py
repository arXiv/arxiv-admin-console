from pydantic import BaseModel, ConfigDict

class DocInCategoryModel(BaseModel):
    document_id: str
    archive: str
    subject_class: str
    is_primary: bool

    model_config = ConfigDict(from_attributes=True)
