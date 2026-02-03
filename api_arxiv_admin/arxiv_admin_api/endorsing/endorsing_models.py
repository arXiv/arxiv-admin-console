"""SQLAlchemy 2.0 models for endorsement candidates SQLite database."""
from datetime import datetime
from typing import List

from sqlalchemy import String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pydantic import BaseModel, ConfigDict


class EndorsingBase(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass


class EndorsingCategoryModel(EndorsingBase):
    """Model for endorsement categories."""
    __tablename__ = "endorsement_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    # Relationship to candidates
    candidates: Mapped[List["EndorsingCandidateModel"]] = relationship(
        back_populates="category_ref",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"EndorsementCategory(id={self.id}, category={self.category!r})"


class EndorsingCandidateModel(EndorsingBase):
    """Model for endorsement candidates."""
    __tablename__ = "endorsement_candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True) # surrogate key
    user_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("endorsement_categories.id"))
    document_count: Mapped[int] = mapped_column(Integer, nullable=False)
    latest_document_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationship to category
    category_ref: Mapped["EndorsingCategoryModel"] = relationship(back_populates="candidates")

    def __repr__(self) -> str:
        return f"EndorsementCandidateModel(id={self.id}, category_id={self.category_id}, document_count={self.document_count}, latest={self.latest_document_id})"


class EndorsingMetadataModel(EndorsingBase):
    """Model for endorsement candidates."""
    __tablename__ = "metadata"

    key: Mapped[str] = mapped_column(String, primary_key=True) # surrogate key
    value: Mapped[str] = mapped_column(String)

    def __repr__(self) -> str:
        return f"EndorsingMetadataModel(key={self.key}, value={self.value!r})"


class EndorsementCandidate(BaseModel):
    """Model for endorsement candidate data."""
    id: int # surrogate ID
    user_id: int # user id
    category: str
    document_count: int
    latest_document_id: int

    model_config = ConfigDict(from_attributes=True)


class EndorsementCandidates(BaseModel):
    """Model for endorsement candidate data."""
    category: str
    candidates: List[EndorsementCandidate]

    model_config = ConfigDict(from_attributes=True)
