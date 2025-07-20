from pydantic import BaseModel


class ReactAdminUpdateResult(BaseModel):
    id: str | int
    data: dict = {}
