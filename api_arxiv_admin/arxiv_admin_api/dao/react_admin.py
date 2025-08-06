from pydantic import BaseModel


class ReactAdminUpdateResult(BaseModel):
    id: str | int
    data: dict = {}


class ReactAdminCreateResult(BaseModel):
    id: str | int
