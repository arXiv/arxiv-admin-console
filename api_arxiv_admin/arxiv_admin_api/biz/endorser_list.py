"""arXiv endorser list business logic."""

# I tried a few parallel processing options but it does not work at all.
# 1. Threading is blocked by GIL.
# 2. MP doesn't work as Python ASGI does not allow child processes from daemon processes
# 3. Solution: Use subprocess to spawn independent Python CLI process
from typing import Optional, List, Iterator
from arxiv.base import logging
from arxiv.db.models import Metadata, Document, PaperOwner, EndorsementDomain, Category, Demographic
from sqlalchemy import func, and_, text, Integer, String, DateTime
from sqlalchemy.orm import Session, aliased
from sqlalchemy.sql import select
from pydantic import BaseModel
from datetime import datetime, date, timedelta, timezone
import os
import time
import asyncio
import sys
import tempfile
import gzip
import sqlite3
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class EndorsementCandidateWithMultipleCategories(BaseModel):
    """Model for endorsement candidate data."""
    user_id: int
    abs_categories: str
    document_count: int
    latest: datetime
    class Config:
        from_attributes = True

class EndorsementCandidate(BaseModel):
    """Model for endorsement candidate data."""
    id: int
    category: str
    document_count: int
    latest: datetime
    class Config:
        from_attributes = True

class EndorsementCandidates(BaseModel):
    """Model for endorsement candidate data."""
    timestamp: datetime
    category: str
    candidates: List[EndorsementCandidate]
    class Config:
        from_attributes = True


class EndorsementCandidateCategories(BaseModel):
    """Model for a single user with multiple categories."""
    id: int
    data: List[EndorsementCandidate]
    class Config:
        from_attributes = True


def _process_candidates(
    unprocessed: List[EndorsementCandidateWithMultipleCategories],
    valid_categories: set[str]
) -> dict[str, dict[int, EndorsementCandidate]]:
    """Process endorsement candidates and return category-organized results."""
    endorsement_candidates: dict[str, dict[int, EndorsementCandidate]] = {}

    for entry in unprocessed:
        for cat in entry.abs_categories.split(' '):
            if not cat or cat not in valid_categories:
                continue

            if cat not in endorsement_candidates:
                endorsement_candidates[cat] = {}

            if entry.user_id not in endorsement_candidates[cat]:
                endorsement_candidates[cat][entry.user_id] = EndorsementCandidate(
                    id=entry.user_id,
                    category=cat,
                    document_count=0,
                    latest=entry.latest,
                )

            endorsement_candidates[cat][entry.user_id].document_count += entry.document_count
            if endorsement_candidates[cat][entry.user_id].latest > entry.latest:
                endorsement_candidates[cat][entry.user_id].latest = entry.latest

    return endorsement_candidates


async def _process_candidates_subprocess(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[EndorsementCandidates]:
    """Process endorsement candidates using subprocess CLI."""
    # Create temporary file for output
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
        temp_path = temp_file.name

    try:
        # Build command arguments
        script_path = Path(__file__).parent.parent / 'bin' / 'create_endorsers_db.py'
        cmd = [sys.executable, str(script_path), '--output', temp_path]

        if start_date:
            cmd.extend(['--start-date', start_date.strftime('%Y-%m-%d')])
        if end_date:
            cmd.extend(['--end-date', end_date.strftime('%Y-%m-%d')])

        # Add database URL from environment
        if 'CLASSIC_DB_URI' in os.environ:
            cmd.extend(['--db-url', os.environ['CLASSIC_DB_URI']])

        logger.info(f"Starting subprocess: {' '.join(cmd)}")

        # Run subprocess
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            logger.error(f"Subprocess failed with return code {process.returncode}")
            logger.error(f"stderr: {stderr.decode()}")
            raise RuntimeError(f"Subprocess failed: {stderr.decode()}")

        logger.info(f"Subprocess completed successfully")
        logger.info(f"stdout: {stdout.decode()}")

        # Read results from SQLite file
        return _load_endorsement_candidates_from_file(temp_path)

    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def _process_categories(
    timestamp: datetime,
    endorsement_candidates: dict[str, dict[int, EndorsementCandidate]],
    endorsement_criteria: dict[str, EndorsementDomain]
) -> List[EndorsementCandidates]:
    """Process all categories to filter qualified candidates."""
    endorsement_candidates_result: List[EndorsementCandidates] = []
    per_cat = {}

    for cat, candidates in endorsement_candidates.items():
        criteria = endorsement_criteria.get(cat)

        # Fallback to parent category if specific category criteria not found
        if criteria is None:
            cat_elems = cat.split(".")
            if len(cat_elems) == 2:
                criteria = endorsement_criteria.get(cat_elems[0])

        if criteria is None:
            continue

        # Filter candidates based on paper count threshold
        users: List[EndorsementCandidate] = []
        for user_id, entry in candidates.items():
            if entry.document_count >= criteria.papers_to_endorse:
                users.append(entry)

        if users:  # Only add categories with qualified candidates
            endorsement_candidates_result.append(EndorsementCandidates(
                timestamp=timestamp,
                category=cat,
                candidates=users
            ))

    return endorsement_candidates_result


def _load_endorsement_candidates_from_file(file_path: str) -> List[EndorsementCandidates]:
    """Load endorsement candidates from compressed SQLite file."""
    # Read compressed SQLite data
    with gzip.open(file_path, 'rb') as f:
        db_bytes = f.read()

    # Create in-memory database from bytes
    conn = sqlite3.connect(':memory:')
    conn.deserialize(db_bytes)
    cursor = conn.cursor()

    # Read data from table
    cursor.execute('SELECT timestamp, category, candidates FROM endorsement_candidates')
    rows = cursor.fetchall()
    conn.close()

    # Convert back to model objects
    result = []
    for timestamp_str, category, candidates_json in rows:
        timestamp = datetime.fromisoformat(timestamp_str)
        candidates_data = json.loads(candidates_json)

        candidates = [
            EndorsementCandidate(
                id=candidate['id'],
                category=candidate['category'],
                document_count=candidate['document_count'],
                latest=datetime.fromisoformat(candidate['latest'])
            )
            for candidate in candidates_data
        ]

        result.append(EndorsementCandidates(
            timestamp=timestamp,
            category=category,
            candidates=candidates
        ))

    return result


def _list_endorsement_candidates(
    session: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[EndorsementCandidateWithMultipleCategories]:
    """
    Find endorsement candidates using an optimized single query approach.

    This restructures the original query to be more efficient while avoiding
    the performance issues of multiple round trips.

    Args:
        session: SQLAlchemy session
        start_date: Start date for paper filtering (defaults to 5y ago)
        end_date: End date for paper filtering (defaults to 3mo ago)

    Returns:
        List of EndorsementCandidateWithMultipleCategories objects
    """
    import time
    start_time = time.time()

    if start_date is None:
        # Default to 5 years ago from current UTC timestamp
        start_date = (datetime.now(timezone.utc) - timedelta(days=5*365)).date()
    if end_date is None:
        # Default to 3 months ago from current UTC timestamp
        end_date = (datetime.now(timezone.utc) - timedelta(days=90)).date()

    # Convert dates to Unix timestamps for comparison
    start_timestamp = int(datetime.combine(start_date, datetime.min.time()).timestamp())
    end_timestamp = int(datetime.combine(end_date, datetime.min.time()).timestamp())

    logger.debug(f"Starting optimized single query for date range {start_date} to {end_date}")

    # Get minimum papers threshold
    min_papers_threshold = session.query(func.min(EndorsementDomain.papers_to_endorse)).scalar()
    logger.debug(f"Minimum papers threshold: {min_papers_threshold}")

    # Create a CTE for qualifying users to avoid repeated subquery evaluation
    po_qualifying: PaperOwner = aliased(PaperOwner)
    qualifying_users_cte = (
        session.query(po_qualifying.user_id.label('user_id'))
        .filter(po_qualifying.valid == 1,
                po_qualifying.flag_author == 1)
        .group_by(po_qualifying.user_id)
        .having(func.count(func.distinct(po_qualifying.document_id)) >= min_papers_threshold)
        .cte('qualifying_users')
    )

    # Main query with better structure - start with date filter first
    query = (
        session.query(
            func.count(func.distinct(Document.document_id)).label('document_count'),
            PaperOwner.user_id,
            Metadata.abs_categories,
            func.max(Document.dated).label('latest')
        )
        .select_from(Document)
        .filter(Document.dated.between(start_timestamp, end_timestamp))  # Date filter first (uses index)
        .join(
            PaperOwner,
            and_(
                Document.document_id == PaperOwner.document_id,
                PaperOwner.valid == 1
            )
        )
        .join(
            qualifying_users_cte,
            PaperOwner.user_id == qualifying_users_cte.c.user_id
        )
        .join(
            Metadata,
            and_(
                Document.document_id == Metadata.document_id,
                Metadata.is_current == 1,
                Metadata.is_withdrawn == 0
            )
        )
        .join(
            Demographic,
            and_(
                Demographic.user_id == PaperOwner.user_id,
                Demographic.veto_status == "ok"
            )
        )
        .group_by(PaperOwner.user_id, Metadata.abs_categories)
        .order_by(PaperOwner.user_id, Metadata.abs_categories)
    )

    # Execute query and convert to models
    results = query.all()

    elapsed = time.time() - start_time
    logger.debug(f"Optimized single query completed in {elapsed:.3f} seconds, found {len(results)} results")

    return [
        EndorsementCandidateWithMultipleCategories(
            user_id=row.user_id,
            abs_categories=row.abs_categories,
            document_count=row.document_count,
            latest=datetime.fromtimestamp(row.latest, timezone.utc)
        )
        for row in results
    ]


async def list_endorsement_candidates(
    session: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    use_multiprocessing: Optional[bool] = None
) -> List[EndorsementCandidates]:
    """
    Get endorsement candidates organized by category with threshold filtering.

    This function processes raw endorsement candidate data and organizes it by
    individual arXiv categories, applying category-specific thresholds from
    the endorsement domains configuration.

    Process:
    1. Retrieves raw candidate data using _list_endorsement_candidates()
    2. Splits multi-category papers (e.g., "math.CO cs.DM") into individual categories
    3. Aggregates document counts per user per category
    4. Applies category-specific paper count thresholds from EndorsementDomain
    5. Returns qualified users organized by category

    Args:
        session: SQLAlchemy database session
        start_date: Start date for paper filtering (defaults to 5y ago)
        end_date: End date for paper filtering (defaults to 3mo ago)
        use_multiprocessing: Whether to use multiprocessing (defaults to environment variable USE_MULTIPROCESSING)

    Returns:
        List of EndorsementCandidatesInCategory objects, each containing:
        - category: The arXiv category (e.g., "math.CO", "cs.AI")
        - candidates: List of user_ids who meet the threshold for that category

    Example:
        >>> candidates = list_endorsement_candidates(session)
        >>> for category_data in candidates:
        ...     print(f"{category_data.category}: {len(category_data.candidates)} users")
        math.CO: 45 users
        cs.AI: 123 users
    """
    # Determine which implementation to use
    use_subprocess = os.getenv('USE_SUBPROCESS_WORKERS', 'true').lower() == 'true'

    # Override with use_multiprocessing parameter for backward compatibility
    if use_multiprocessing is not None:
        use_subprocess = use_multiprocessing

    timestamp = datetime.now(timezone.utc)
    start_time = time.time()

    endorsement_criteria = {}
    criteria: EndorsementDomain
    for criteria in session.query(EndorsementDomain).all():
        endorsement_criteria[criteria.endorsement_domain] = criteria

    # Get valid categories
    valid_categories = set()
    for cat in session.query(Category).all():
        if cat.subject_class:
            cat_name = f"{cat.archive}.{cat.subject_class}"
            valid_categories.add(cat_name)
        else:
            valid_categories.add(cat.archive)

    unprocessed: List[EndorsementCandidateWithMultipleCategories] = _list_endorsement_candidates(session, start_date, end_date)

    implementation = "subprocess" if use_subprocess else "simple"
    logger.debug(f"Processing endorsement candidates using {implementation} implementation")

    try:
        if use_subprocess:
            # Use subprocess implementation
            import asyncio

            # Check if we're already in an event loop
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, but need to run our async function
                # Use asyncio.create_task or run in thread pool
                logger.info("Running subprocess in existing event loop")
                result = await _process_candidates_subprocess(start_date, end_date)
            except RuntimeError:
                # No event loop running, create one
                logger.info("Creating new event loop for subprocess")
                result = asyncio.run(_process_candidates_subprocess(start_date, end_date))

            total_time = time.time() - start_time
            logger.info(f"Endorsement processing (subprocess): {total_time:.3f}s total, "
                       f"{len(result)} categories with qualified candidates")
            return result

        else:
            # Use simple implementation
            unprocessed: List[EndorsementCandidateWithMultipleCategories] = _list_endorsement_candidates(session, start_date, end_date)

            process_start = time.time()
            endorsement_candidates_0 = _process_candidates(unprocessed, valid_categories)
            process_time = time.time() - process_start

            filter_start = time.time()
            endorsement_candidates_result = _process_categories(timestamp, endorsement_candidates_0, endorsement_criteria)
            filter_time = time.time() - filter_start

            total_time = time.time() - start_time
            logger.info(f"Endorsement processing (simple): {total_time:.3f}s total "
                       f"(process: {process_time:.3f}s, filter: {filter_time:.3f}s), "
                       f"{len(endorsement_candidates_result)} categories with qualified candidates")
            return endorsement_candidates_result

    except Exception as e:
        if use_subprocess:
            logger.error(f"Subprocess implementation failed: {e}, falling back to simple implementation")
            # Fall back to simple implementation
            unprocessed: List[EndorsementCandidateWithMultipleCategories] = _list_endorsement_candidates(session, start_date, end_date)

            process_start = time.time()
            endorsement_candidates_0 = _process_candidates(unprocessed, valid_categories)
            process_time = time.time() - process_start

            filter_start = time.time()
            endorsement_candidates_result = _process_categories(timestamp, endorsement_candidates_0, endorsement_criteria)
            filter_time = time.time() - filter_start

            total_time = time.time() - start_time
            logger.info(f"Endorsement processing (simple fallback): {total_time:.3f}s total "
                       f"(process: {process_time:.3f}s, filter: {filter_time:.3f}s), "
                       f"{len(endorsement_candidates_result)} categories with qualified candidates")

            return endorsement_candidates_result
        else:
            raise


