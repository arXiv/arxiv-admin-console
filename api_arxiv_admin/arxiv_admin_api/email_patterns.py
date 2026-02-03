"""Provides integration for the external user interface."""
import sqlalchemy
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import Optional, List
from io import StringIO

from sqlalchemy import select, delete, insert
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from arxiv.base import logging
from arxiv.db.models import t_arXiv_black_email, t_arXiv_white_email, t_arXiv_block_email
# from arxiv.auth.user_claims import ArxivUserClaims

from . import is_admin_user, get_db

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(is_admin_user)], prefix="/email_patterns")


class EmailPatternModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    purpose: str
    pass

pattern_tables = {
    "black": t_arXiv_black_email,
    "block": t_arXiv_block_email,
    "white": t_arXiv_white_email,
}


@router.get('/')
async def list_email_patterns(
        response: Response,
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: int = Query(0, alias="_start"),
        _end: int = Query(100, alias="_end"),
        pattern: Optional[str] = Query(None, description="Email pattern"),
        purpose: Optional[str] = Query("black", description="black, block or white"),
        session: Session = Depends(get_db)
    ) -> List[EmailPatternModel]:

    if _start < 0 or _end < _start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid start or end index")

    if purpose is None:
        purpose = "black"

    table = pattern_tables.get(purpose)
    if table is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid purpose {purpose}. Allowed values: black, block, white")
    order_columns = []
    if _order:
        order_columns.append(table.c.pattern)

    query = select(table.c.pattern.label("id")).select_from(table)
    
    if pattern is not None:
        query = query.where(table.c.pattern.contains(pattern))

    for column in order_columns:
        if _order == "DESC":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    count_query = select(table.c.pattern).select_from(table)
    if pattern is not None:
        count_query = count_query.where(table.c.pattern.contains(pattern))
    
    count = len(session.execute(count_query).fetchall())
    response.headers['X-Total-Count'] = str(count)
    
    result_query = query.offset(_start).limit(_end - _start)
    result = [EmailPatternModel.model_validate({"id": item.id, "purpose": purpose}) for item in session.execute(result_query).fetchall()]
    return result


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_email_pattern(
        response: Response,
        body: EmailPatternModel,
        session: Session = Depends(get_db),
) -> EmailPatternModel:

    table = pattern_tables.get(body.purpose)
    if table is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid purpose {body.purpose}. Allowed values: black, block, white")

    if not body.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Pattern ID is required")

    try:
        # Check if pattern already exists
        existing_query = select(table.c.pattern).where(table.c.pattern == body.id)
        existing = session.execute(existing_query).fetchone()
        
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"Email pattern '{body.id}' already exists in {body.purpose} table")

        # Insert new pattern
        insert_query = insert(table).values(pattern=body.id)
        session.execute(insert_query)
        session.commit()
        
        logger.info(f"Created email pattern '{body.id}' in {body.purpose} table")
        response.status_code = status.HTTP_201_CREATED
        return body
    
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating email pattern: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to create email pattern")


class EmailPatternListModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ids: List[str]


@router.delete('/{purpose:str}', status_code=status.HTTP_204_NO_CONTENT,
              responses={
                  400: {"description": "Invalid purpose"},
                  404: {"description": "No patterns found"},
                  500: {"description": "Failed to delete patterns"}
              })
async def delete_email_patterns(
        response: Response,
        purpose: str,
        ids: List[str] = Query(...),
        session: Session = Depends(get_db)
) -> Response:

    table = pattern_tables.get(purpose)
    if table is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid purpose {purpose}. Allowed values: black, block, white")

    if not ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No pattern IDs provided")

    try:
        delete_query = delete(table).where(table.c.pattern.in_(ids))
        result: sqlalchemy.engine.CursorResult = session.execute(delete_query) # type: ignore
        session.commit()

        logger.info(f"Deleted {result.rowcount} email patterns from {purpose} table")
        
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting email patterns: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to delete email patterns")


class BulkUploadResult(BaseModel):
    processed_count: int
    skipped_count: int
    error_count: int
    operation: str
    purpose: str


@router.post('/import')
async def upload_email_patterns(
        file: UploadFile = File(...),
        purpose: str = Form(...),
        operation: str = Form(...),
        session: Session = Depends(get_db)
) -> BulkUploadResult:

    # Validate purpose
    table = pattern_tables.get(purpose)
    if table is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid purpose {purpose}. Allowed values: black, block, white")

    # Validate operation
    if operation not in ['append', 'replace']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid operation. Allowed values: append, replace")

    # Validate file type
    if not file.content_type or not file.content_type.startswith('text/'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="File must be a text file")

    try:
        # Read file content
        content = await file.read()
        text_content = content.decode('utf-8')
        lines = [line.strip() for line in text_content.splitlines() if line.strip()]

        if not lines:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="File is empty or contains no valid patterns")

        processed_count = 0
        skipped_count = 0
        error_count = 0

        # If replace operation, clear existing patterns first
        if operation == 'replace':
            delete_all_query = delete(table)
            session.execute(delete_all_query)
            logger.info(f"Cleared all existing patterns from {purpose} table for replace operation")

        # Get existing patterns to avoid duplicates (only for append)
        existing_patterns = set()
        if operation == 'append':
            existing_query = select(table.c.pattern)
            existing_result = session.execute(existing_query).fetchall()
            existing_patterns = {row.pattern for row in existing_result}

        # Process each line
        for line in lines:
            pattern = line.strip()
            if not pattern:
                continue

            try:
                # Skip if pattern already exists (append mode only)
                if operation == 'append' and pattern in existing_patterns:
                    skipped_count += 1
                    continue

                # Insert pattern
                insert_query = insert(table).values(pattern=pattern)
                session.execute(insert_query)
                processed_count += 1

                # Add to existing patterns set to avoid duplicates within the same file
                existing_patterns.add(pattern)

            except Exception as e:
                logger.warning(f"Failed to insert pattern '{pattern}': {e}")
                error_count += 1
                continue

        # Commit all changes
        session.commit()
        
        logger.info(f"Bulk upload completed: {processed_count} processed, {skipped_count} skipped, {error_count} errors")
        
        return BulkUploadResult(
            processed_count=processed_count,
            skipped_count=skipped_count,
            error_count=error_count,
            operation=operation,
            purpose=purpose
        )

    except UnicodeDecodeError:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="File encoding is not supported. Please use UTF-8 encoded text file")
    except Exception as e:
        session.rollback()
        logger.error(f"Error during bulk upload: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to process file upload")


@router.get('/export/{purpose:str}')
async def export_email_patterns(
        purpose: str,
        session: Session = Depends(get_db)
) -> StreamingResponse:

    # Validate purpose
    table = pattern_tables.get(purpose)
    if table is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid purpose {purpose}. Allowed values: black, block, white")

    try:
        # Query all patterns for the specified purpose
        query = select(table.c.pattern).order_by(table.c.pattern.asc())
        result = session.execute(query).fetchall()
        
        # Create text content with one pattern per line
        content = StringIO()
        pattern_count = 0
        for row in result:
            content.write(f"{row.pattern}\n")
            pattern_count += 1
        
        content.seek(0)
        
        logger.info(f"Exported {pattern_count} email patterns from {purpose} table")
        
        # Create filename with current date
        from datetime import date
        filename = f"email_patterns_{purpose}_{date.today().isoformat()}.txt"
        
        # Return as streaming response
        return StreamingResponse(
            iter([content.getvalue()]),
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting email patterns: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to export email patterns")

