"""arXiv endorser list business logic."""
from typing import Optional, List, Iterator
from arxiv.base import logging
from arxiv.db.models import Metadata, Document, PaperOwner, EndorsementDomain, Category
from sqlalchemy import func, and_
from sqlalchemy.orm import Session, aliased
from pydantic import BaseModel
from datetime import datetime, date, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from threading import Lock

logger = logging.getLogger(__name__)

class EndorsementCandidateWithMultipleCategories(BaseModel):
    """Model for endorsement candidate data."""
    user_id: int
    abs_categories: str
    document_count: int
    latest: datetime


class EndorsementCandidate(BaseModel):
    """Model for endorsement candidate data."""
    user_id: int
    category: str
    document_count: int
    lastest: datetime

class EndorsementCandidates(BaseModel):
    """Model for endorsement candidate data."""
    category: str
    candidates: List[EndorsementCandidate]


def _chunk_generator(items: List, chunk_size: int) -> Iterator[List]:
    """Generate chunks of items for parallel processing."""
    for i in range(0, len(items), chunk_size):
        yield items[i:i + chunk_size]


def _process_chunk(
    chunk: List[EndorsementCandidateWithMultipleCategories],
    valid_categories: set[str]
) -> dict[str, dict[int, EndorsementCandidate]]:
    """Process a chunk of endorsement candidates and return category-organized results."""
    local_candidates: dict[str, dict[int, EndorsementCandidate]] = {}

    for entry in chunk:
        for cat in entry.abs_categories.split(' '):
            if not cat or cat not in valid_categories:
                continue

            if cat not in local_candidates:
                local_candidates[cat] = {}

            if entry.user_id not in local_candidates[cat]:
                local_candidates[cat][entry.user_id] = EndorsementCandidate(
                    user_id=entry.user_id,
                    category=cat,
                    document_count=0,
                    lastest=entry.latest,
                )

            local_candidates[cat][entry.user_id].document_count += entry.document_count
            if local_candidates[cat][entry.user_id].lastest > entry.latest:
                local_candidates[cat][entry.user_id].lastest = entry.latest

    return local_candidates


def _merge_candidate_dicts(
    target: dict[str, dict[int, EndorsementCandidate]],
    source: dict[str, dict[int, EndorsementCandidate]],
    lock: Lock
) -> None:
    """Thread-safe merge of candidate dictionaries."""
    with lock:
        for cat, users in source.items():
            if cat not in target:
                target[cat] = {}

            for user_id, candidate in users.items():
                if user_id not in target[cat]:
                    target[cat][user_id] = candidate
                else:
                    # Merge document counts and update latest timestamp
                    target[cat][user_id].document_count += candidate.document_count
                    if target[cat][user_id].lastest > candidate.lastest:
                        target[cat][user_id].lastest = candidate.lastest


def _process_category(
    cat: str,
    candidates: dict[int, EndorsementCandidate],
    endorsement_criteria: dict[str, EndorsementDomain]
) -> Optional[EndorsementCandidates]:
    """Process a single category to filter qualified candidates."""
    users: List[EndorsementCandidate] = []
    criteria = endorsement_criteria.get(cat)

    # Fallback to parent category if specific category criteria not found
    if criteria is None:
        cat_elems = cat.split(".")
        if len(cat_elems) == 2:
            criteria = endorsement_criteria.get(cat_elems[0])

    if criteria is None:
        return None

    # Filter candidates based on paper count threshold
    for user_id, entry in candidates.items():
        if entry.document_count >= criteria.papers_to_endorse:
            users.append(entry)

    return EndorsementCandidates(
        category=cat,
        candidates=users
    )


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
    po_qualifying = aliased(PaperOwner)
    qualifying_users_cte = (
        session.query(po_qualifying.user_id.label('user_id'))
        .filter(po_qualifying.valid == 1)
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


def list_endorsement_candidates(
    session: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
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
    endorsement_criteria = {}
    criteria: EndorsementDomain
    for criteria in session.query(EndorsementDomain).all():
        endorsement_criteria[criteria.endorsement_domain] = criteria

    # Initialize category structure and get valid categories
    endorsement_candidates_0: dict[str, dict[int, EndorsementCandidate]] = {}
    valid_categories = set()

    for cat in session.query(Category).all():
        if cat.subject_class:
            cat_name = f"{cat.archive}.{cat.subject_class}"
            endorsement_candidates_0[cat_name] = {}
            valid_categories.add(cat_name)
        else:
            endorsement_candidates_0[cat.archive] = {}
            valid_categories.add(cat.archive)

    unprocessed: List[EndorsementCandidateWithMultipleCategories] = _list_endorsement_candidates(session, start_date, end_date)

    # Process in parallel chunks for large datasets
    if len(unprocessed) > 10000:  # Use parallel processing for large datasets
        # Determine optimal chunk size and thread pool size
        chunk_size = max(1000, len(unprocessed) // (os.cpu_count() * 4))
        max_workers = os.cpu_count() if os.cpu_count() else 4

        logger.debug(f"Processing {len(unprocessed)} candidates in parallel with {max_workers} workers, chunk size: {chunk_size}")

        merge_lock = Lock()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit chunk processing tasks
            future_to_chunk = {
                executor.submit(_process_chunk, chunk, valid_categories): chunk
                for chunk in _chunk_generator(unprocessed, chunk_size)
            }

            # Collect and merge results as they complete
            for future in as_completed(future_to_chunk):
                try:
                    chunk_result = future.result()
                    _merge_candidate_dicts(endorsement_candidates_0, chunk_result, merge_lock)
                except Exception as e:
                    logger.error(f"Error processing chunk: {e}")
                    raise
    else:
        # Sequential processing for smaller datasets
        logger.debug(f"Processing {len(unprocessed)} candidates sequentially")
        chunk_result = _process_chunk(unprocessed, valid_categories)
        endorsement_candidates_0.update(chunk_result)


    # Process categories in parallel (about 100 categories)
    endorsement_candidates_result: List[EndorsementCandidates] = []
    max_workers = min(os.cpu_count() or 4, len(endorsement_candidates_0))  # Don't over-provision

    logger.debug(f"Processing {len(endorsement_candidates_0)} categories in parallel with {max_workers} workers")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit category processing tasks
        future_to_category = {
            executor.submit(_process_category, cat, candidates, endorsement_criteria): cat
            for cat, candidates in endorsement_candidates_0.items()
        }

        # Collect results as they complete
        for future in as_completed(future_to_category):
            try:
                result = future.result()
                if result is not None:  # Only add valid results
                    endorsement_candidates_result.append(result)
            except Exception as e:
                cat = future_to_category[future]
                logger.error(f"Error processing category {cat}: {e}")
                raise

    return endorsement_candidates_result
