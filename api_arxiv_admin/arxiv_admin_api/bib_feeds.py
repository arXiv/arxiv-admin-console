"""
Bibliographic feeds REST API

Provides REST API endpoints for bibliographic data harvesting administration
for arXiv. Based on the arXiv Bib Feed and Entry modules.

Original CLI version: Simeon Warner - 2008-08
REST API conversion: 2025
"""

from datetime import datetime
from typing import Optional, List

from arxiv.auth.user_claims import ArxivUserClaims
from arxiv.base import logging
from arxiv.db.models import BibFeed, BibUpdate, Document
from arxiv_bizlogic.fastapi_helpers import get_authn_user
from fastapi import APIRouter, Depends, HTTPException, status as http_status, Body, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from . import get_db, is_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bib_feeds", dependencies=[Depends(is_admin_user)])
bib_feed_updates_router = APIRouter(prefix="/bib_feed_updates", dependencies=[Depends(is_admin_user)])

# Pydantic Models

class BibFeedModel(BaseModel):
    """Bibliographic feed model"""
    bib_id: int = Field(..., description="Feed ID", validation_alias="id", serialization_alias="id")
    name: str = Field(..., description="Feed name")
    priority: int = Field(..., description="Feed priority (lower = higher priority)")
    uri: Optional[str] = Field(None, description="Feed URI")
    identifier: Optional[str] = Field(None, description="Feed identifier")
    version: Optional[str] = Field(None, description="Feed version")
    strip_journal_ref: bool = Field(False, description="Strip journal reference flag")
    concatenate_dupes: Optional[int] = Field(None, description="Concatenate duplicates (numeric value)")
    max_updates: Optional[int] = Field(None, description="Maximum updates")
    email_errors: Optional[str] = Field(None, description="Email for errors")
    prune_ids: Optional[str] = Field(None, description="IDs to prune")
    prune_regex: Optional[str] = Field(None, description="Regex pattern for pruning")
    enabled: Optional[bool] = Field(True, description="Feed enabled flag")

    class Config:
        from_attributes = True
        populate_by_name = True


class BibFeedCreateModel(BaseModel):
    """Model for creating a new bibliographic feed"""
    name: str = Field(..., description="Feed name", min_length=1, max_length=64)
    priority: int = Field(..., description="Feed priority (lower = higher priority)")
    uri: Optional[str] = Field(None, description="Feed URI", max_length=255)
    identifier: Optional[str] = Field(None, description="Feed identifier", max_length=255)
    version: Optional[str] = Field(None, description="Feed version", max_length=255)
    strip_journal_ref: bool = Field(False, description="Strip journal reference flag")
    concatenate_dupes: Optional[int] = Field(None, description="Concatenate duplicates (numeric value)")
    max_updates: Optional[int] = Field(None, description="Maximum updates")
    email_errors: Optional[str] = Field(None, description="Email for errors", max_length=255)
    prune_ids: Optional[str] = Field(None, description="IDs to prune")
    prune_regex: Optional[str] = Field(None, description="Regex pattern for pruning")
    enabled: Optional[bool] = Field(True, description="Feed enabled flag")


class BibFeedUpdateModel(BaseModel):
    """Model for updating a bibliographic feed"""
    name: Optional[str] = Field(None, description="Feed name", min_length=1, max_length=64)
    priority: Optional[int] = Field(None, description="Feed priority (lower = higher priority)")
    uri: Optional[str] = Field(None, description="Feed URI", max_length=255)
    identifier: Optional[str] = Field(None, description="Feed identifier", max_length=255)
    version: Optional[str] = Field(None, description="Feed version", max_length=255)
    strip_journal_ref: Optional[bool] = Field(None, description="Strip journal reference flag")
    concatenate_dupes: Optional[int] = Field(None, description="Concatenate duplicates (numeric value)")
    max_updates: Optional[int] = Field(None, description="Maximum updates")
    email_errors: Optional[str] = Field(None, description="Email for errors", max_length=255)
    prune_ids: Optional[str] = Field(None, description="IDs to prune")
    prune_regex: Optional[str] = Field(None, description="Regex pattern for pruning")
    enabled: Optional[bool] = Field(None, description="Feed enabled flag")


class BibUpdateModel(BaseModel):
    """Bibliographic update model"""
    update_id: int = Field(..., description="Update ID", validation_alias="id", serialization_alias="id")
    document_id: int = Field(..., description="Document ID")
    paper_id: Optional[str] = Field(None, description="Paper ID (e.g., 2401.00001)")
    bib_id: int = Field(..., description="Feed ID")
    feed_name: Optional[str] = Field(None, description="Feed name")
    feed_priority: Optional[int] = Field(None, description="Feed priority")
    updated: datetime = Field(..., description="Update timestamp")
    journal_ref: Optional[str] = Field(None, description="Journal reference")
    doi: Optional[str] = Field(None, description="DOI")

    class Config:
        from_attributes = True
        populate_by_name = True


class BibUpdateCreateModel(BaseModel):
    """Model for creating a bibliographic update entry"""
    document_id: int = Field(..., description="Document ID")
    bib_id: int = Field(..., description="Feed ID")
    journal_ref: Optional[str] = Field(None, description="Journal reference")
    doi: Optional[str] = Field(None, description="DOI")


class ManualOverrideRequest(BaseModel):
    """Model for setting manual override"""
    paper_id: str = Field(..., description="Paper ID (e.g., 2401.00001)")


class DeleteUpdateHistoryRequest(BaseModel):
    """Model for deleting update history"""
    paper_id: str = Field(..., description="Paper ID (e.g., 2401.00001)")
    feed_names: Optional[List[str]] = Field(None, description="Feed names to delete from (if None, delete all)")


# API Endpoints

@router.get("/", response_model=List[BibFeedModel])
async def list_feeds(
    response: Response,
    _sort: Optional[str] = Query("bib_id", description="sort by"),
    _order: Optional[str] = Query("ASC", description="sort order"),
    _start: Optional[int] = Query(0, alias="_start"),
    _end: Optional[int] = Query(100, alias="_end"),
    name: Optional[str] = Query(None, description="Filter by feed name"),
    identifier: Optional[str] = Query(None, description="Filter by feed identifier"),
    uri: Optional[str] = Query(None, description="Filter by URI"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled flag"),
    id: Optional[List[int]] = Query(None, description="Filter by feed id"),
    db: Session = Depends(get_db),
    current_user: ArxivUserClaims = Depends(get_authn_user),
) -> List[BibFeedModel]:
    """
    Get all bibliographic feeds in the database.

    Returns a list of all configured feeds with their priorities and settings.
    """
    query = db.query(BibFeed)

    order_columns = []
    if _sort:
        keys = _sort.split(",")
        for key in keys:
            if key == "id":
                key = "bib_id"
            try:
                order_column = getattr(BibFeed, key)
                order_columns.append(order_column)
            except AttributeError:
                raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST,
                                    detail="Invalid start or end index")

    if id:
        query = query.filter(BibFeed.bib_id.in_(id))
    else:
        if name:
            query = query.filter(BibFeed.name.startswith(name))

        if identifier:
            query = query.filter(BibFeed.identifier.contains(identifier))

        if uri:
            query = query.filter(BibFeed.uri.contains(uri))

        if enabled is not None:
            query = query.filter(BibFeed.enabled == enabled)

        for column in order_columns:
            if _order == "DESC":
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    if not id:
        query = query.offset(_start).limit(_end - _start)
    return [BibFeedModel.model_validate(feed) for feed in query.all()]


@router.post("/", response_model=BibFeedModel, status_code=http_status.HTTP_201_CREATED)
async def create_feed(
    feed_data: BibFeedCreateModel,
    db: Session = Depends(get_db),
    current_user: ArxivUserClaims = Depends(get_authn_user),
) -> BibFeedModel:
    """
    Create a new bibliographic feed.

    Args:
        feed_data: Feed configuration including name and priority

    Returns:
        The created feed
    """
    # Check if feed with same name already exists
    existing = db.query(BibFeed).filter(BibFeed.name == feed_data.name).first()
    if existing:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=f"Feed with name '{feed_data.name}' already exists"
        )

    feed = BibFeed(**feed_data.model_dump())
    db.add(feed)
    db.commit()
    db.refresh(feed)

    logger.info(f"Created feed: {feed.name} (id={feed.bib_id}, priority={feed.priority})")
    return BibFeedModel.model_validate(feed)


@router.get("/{feed_id}", response_model=BibFeedModel)
async def get_feed(
    feed_id: int,
    db: Session = Depends(get_db),
    current_user: ArxivUserClaims = Depends(get_authn_user),
) -> BibFeedModel:
    """
    Get a specific bibliographic feed by ID.

    Args:
        feed_id: The feed ID

    Returns:
        The requested feed
    """
    feed = db.query(BibFeed).filter(BibFeed.bib_id == feed_id).first()
    if not feed:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Feed with id={feed_id} not found"
        )
    return BibFeedModel.model_validate(feed)


@router.put("/{feed_id}", response_model=BibFeedModel)
@router.patch("/{feed_id}", response_model=BibFeedModel)
async def update_feed(
    feed_id: int,
    feed_update: BibFeedUpdateModel,
    db: Session = Depends(get_db),
    current_user: ArxivUserClaims = Depends(get_authn_user),
) -> BibFeedModel:
    """
    Update a bibliographic feed.

    Commonly used to change the priority of a feed.
    Supports both PUT and PATCH methods.

    Args:
        feed_id: The feed ID to update
        feed_update: Fields to update

    Returns:
        The updated feed
    """
    feed = db.query(BibFeed).filter(BibFeed.bib_id == feed_id).first()
    if not feed:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Feed with id={feed_id} not found"
        )

    update_data = feed_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(feed, field, value)

    db.commit()
    db.refresh(feed)

    logger.info(f"Updated feed: {feed.name} (id={feed.bib_id})")
    return BibFeedModel.model_validate(feed)


@router.delete("/{feed_id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_feed(
    feed_id: int,
    db: Session = Depends(get_db),
    current_user: ArxivUserClaims = Depends(get_authn_user),
) -> None:
    """
    Delete a bibliographic feed.

    Args:
        feed_id: The feed ID to delete
    """
    feed = db.query(BibFeed).filter(BibFeed.bib_id == feed_id).first()
    if not feed:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Feed with id={feed_id} not found"
        )

    # Check if there are updates associated with this feed
    update_count = db.query(BibUpdate).filter(BibUpdate.bib_id == feed_id).count()
    if update_count > 0:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=f"Cannot delete feed: {update_count} updates are associated with this feed"
        )

    db.delete(feed)
    db.commit()
    logger.info(f"Deleted feed: {feed.name} (id={feed_id})")


@bib_feed_updates_router.get("/", response_model=List[BibUpdateModel])
async def bib_feed_updates_list_all_updates(
    db: Session = Depends(get_db),
    current_user: ArxivUserClaims = Depends(get_authn_user),
    limit: int = 100,
    offset: int = 0,
) -> List[BibUpdateModel]:
    """
    Get update history for all documents.

    Returns updates ordered by update time and feed priority.

    Args:
        limit: Maximum number of results to return
        offset: Number of results to skip

    Returns:
        List of bibliographic updates
    """
    query = (
        db.query(
            BibUpdate,
            Document.paper_id,
            BibFeed.name.label("feed_name"),
            BibFeed.priority.label("feed_priority")
        )
        .join(BibFeed, BibUpdate.bib_id == BibFeed.bib_id)
        .join(Document, BibUpdate.document_id == Document.document_id)
        .order_by(BibUpdate.updated.desc(), BibFeed.priority)
        .limit(limit)
        .offset(offset)
    )

    def create_update_model(update: BibUpdate, paper_id: str, feed_name: str, feed_priority: int) -> BibUpdateModel:
        result = BibUpdateModel.model_validate(update)
        result.paper_id = paper_id
        result.feed_name = feed_name
        result.feed_priority = feed_priority
        return result

    return [create_update_model(update, paper_id, feed_name, feed_priority)
            for update, paper_id, feed_name, feed_priority in query.all()]


@bib_feed_updates_router.get("/{paper_id}", response_model=List[BibUpdateModel])
async def bib_feed_updates_get_update_history(
    paper_id: str,
    db: Session = Depends(get_db),
    current_user: ArxivUserClaims = Depends(get_authn_user),
) -> List[BibUpdateModel]:
    """
    Get update history for a specific paper.

    Args:
        paper_id: The paper ID (e.g., "2401.00001" or "cs/0001001")

    Returns:
        List of updates for this paper, ordered by update time and feed priority
    """
    # Find the document
    document = db.query(Document).filter(Document.paper_id == paper_id).first()
    if not document:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Document with paper_id={paper_id} not found"
        )

    # Get updates with feed information
    query = (
        db.query(
            BibUpdate,
            BibFeed.name.label("feed_name"),
            BibFeed.priority.label("feed_priority")
        )
        .join(BibFeed, BibUpdate.bib_id == BibFeed.bib_id)
        .filter(BibUpdate.document_id == document.document_id)
        .order_by(BibUpdate.updated.desc(), BibFeed.priority)
    )

    def create_update_model(update: BibUpdate, feed_name: str, feed_priority: int) -> BibUpdateModel:
        result = BibUpdateModel.model_validate(update)
        result.paper_id = paper_id
        result.feed_name = feed_name
        result.feed_priority = feed_priority
        return result

    return [create_update_model(update, feed_name, feed_priority)
            for update, feed_name, feed_priority in query.all()]


@bib_feed_updates_router.delete("/{paper_id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def bib_feed_updates_delete_update_history(
    paper_id: str,
    feed_names: Optional[List[str]] = Body(None, description="Optional list of feed names to delete from"),
    db: Session = Depends(get_db),
    current_user: ArxivUserClaims = Depends(get_authn_user),
) -> None:
    """
    Delete update history for a specific paper.

    If feed_names are provided, only deletes history from those specific feeds.
    Otherwise, deletes all history for the paper.

    Args:
        paper_id: The paper ID (e.g., "2401.00001")
        feed_names: Optional list of feed names to delete from (if None, delete all)
    """
    # Find the document
    document = db.query(Document).filter(Document.paper_id == paper_id).first()
    if not document:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Document with paper_id={paper_id} not found"
        )

    document_id = document.document_id

    if feed_names:
        # Delete from specific feeds
        for feed_name in feed_names:
            feed = db.query(BibFeed).filter(BibFeed.name == feed_name).first()
            if feed and feed.bib_id:
                deleted = (
                    db.query(BibUpdate)
                    .filter(BibUpdate.document_id == document_id, BibUpdate.bib_id == feed.bib_id)
                    .delete()
                )
                logger.info(
                    f"Deleted {deleted} update(s) for {paper_id} ({document_id}) from feed {feed_name} ({feed.bib_id})"
                )
            else:
                logger.warning(f"Skipping unknown feed '{feed_name}'")
    else:
        # Delete all updates for this document
        deleted = db.query(BibUpdate).filter(BibUpdate.document_id == document_id).delete()
        logger.info(f"Deleted {deleted} update(s) for {paper_id} ({document_id})")

    db.commit()


@bib_feed_updates_router.post("/{paper_id}/manual-override", response_model=BibUpdateModel, status_code=http_status.HTTP_201_CREATED)
async def bib_feed_updates_set_manual_override(
    paper_id: str,
    db: Session = Depends(get_db),
    current_user: ArxivUserClaims = Depends(get_authn_user),
) -> BibUpdateModel:
    """
    Set manual override with current metadata values for a paper.

    Creates a BibUpdate entry with feed name 'ManualOverride' using the current
    DOI and journal reference from the document metadata.

    Args:
        paper_id: The paper ID (e.g., "2401.00001")

    Returns:
        The created manual override update entry
    """
    feed_name = "ManualOverride"

    # Find the document
    document = db.query(Document).filter(Document.paper_id == paper_id).first()
    if not document:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Document with paper_id={paper_id} not found"
        )

    document_id = document.document_id

    # Find or create the ManualOverride feed
    feed = db.query(BibFeed).filter(BibFeed.name == feed_name).first()
    if not feed:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Feed with name='{feed_name}' not found. Please create it first."
        )

    bib_id = feed.bib_id

    # Get current metadata (from document metadata table if available)
    # For now, we'll use the arXiv_metadata table or get from the document directly
    # This is a simplified version - in production, you'd use the Entry class
    # to get the current metadata properly
    current_doi = document.doi if hasattr(document, 'doi') else None
    current_journal_ref = document.journal_ref if hasattr(document, 'journal_ref') else None

    logger.info(
        f"Setting manual override [{paper_id}({document_id}),{feed_name}({bib_id}),"
        f"{current_doi},{current_journal_ref}]"
    )

    # Create the update entry
    update = BibUpdate(
        document_id=document_id,
        bib_id=bib_id,
        doi=current_doi,
        journal_ref=current_journal_ref,
    )
    db.add(update)
    db.commit()
    db.refresh(update)

    result = BibUpdateModel.model_validate(update)
    result.paper_id = paper_id
    result.feed_name = feed_name
    result.feed_priority = feed.priority
    return result


@bib_feed_updates_router.post("/bulk", response_model=List[BibUpdateModel], status_code=http_status.HTTP_201_CREATED)
async def bib_feed_updates_create_bulk_updates(
    updates: List[BibUpdateCreateModel],
    session: Session = Depends(get_db),
    current_user: ArxivUserClaims = Depends(get_authn_user),
) -> List[BibUpdateModel]:
    """
    Create multiple bibliographic update entries in bulk.

    This endpoint is useful for batch processing feed data.

    Args:
        updates: List of update entries to create

    Returns:
        List of created update entries
    """
    created_updates = []

    for update_data in updates:
        # Verify feed exists
        feed = session.query(BibFeed).filter(BibFeed.bib_id == update_data.bib_id).first()
        if not feed:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Feed with id={update_data.bib_id} not found"
            )

        # Verify document exists
        document = session.query(Document).filter(Document.document_id == update_data.document_id).first()
        if not document:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Document with id={update_data.document_id} not found"
            )

        # Create update
        update = BibUpdate(**update_data.model_dump())
        session.add(update)
        created_updates.append(update)

    session.commit()

    # Refresh and convert to response models

    def create_result_model(update: BibUpdate) -> BibUpdateModel:
        session.refresh(update)
        feed = session.query(BibFeed).filter(BibFeed.bib_id == update.bib_id).first()
        document = session.query(Document).filter(Document.document_id == update.document_id).first()

        result = BibUpdateModel.model_validate(update)
        result.paper_id = document.paper_id if document else None
        result.feed_name = feed.name if feed else None
        result.feed_priority = feed.priority if feed else None
        return result

    results = [create_result_model(update) for update in created_updates]
    logger.info(f"Created {len(results)} bulk updates")
    return results