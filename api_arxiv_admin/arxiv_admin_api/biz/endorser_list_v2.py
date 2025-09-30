"""arXiv endorser list business logic - Version 2 with temp table approach."""

# 2025-09-30 Tai
# This is WIP - tried to do all of processing at MySQL and I cannot make it to work.
# arXiv_metadata.abs_categories is evil.
# It may be able to shave off 1-2 minutes if this works but also hard thing is there is no way of
# checking/debugging so only way to see it works is to compare the results, which is painfully slow.

from typing import Optional, List
from arxiv.base import logging
from arxiv.db.models import Metadata, Document, PaperOwner, EndorsementDomain, Category, Demographic
from sqlalchemy import func, and_, text, Integer, String, DateTime
from sqlalchemy.orm import Session
from sqlalchemy.sql import select
from datetime import datetime, date, timedelta, timezone
import time
import asyncio

# Import data types from the main endorser_list module
from .endorser_list import EndorsementCandidate, EndorsementCandidates

logger = logging.getLogger(__name__)



def _create_temp_table(session: Session, start_date: date, end_date: date) -> str:
    """Create temporary table with PaperOwner data joined with metadata, denormalized by category."""

    # Convert dates to Unix timestamps for comparison
    start_timestamp = int(datetime.combine(start_date, datetime.min.time()).timestamp())
    end_timestamp = int(datetime.combine(end_date, datetime.min.time()).timestamp())

    logger.debug(f"Creating temp table for date range {start_date} to {end_date}")
    logger.debug(f"Timestamp range: {start_timestamp} to {end_timestamp}")

    # Create a unique temp table name
    temp_table_name = f"temp_endorser_candidates_{int(time.time())}"

    # Create temporary table with denormalized structure (category instead of abs_categories)
    create_table_sql = f"""
    CREATE TEMPORARY TABLE {temp_table_name} (
        document_id INTEGER,
        user_id INTEGER,
        dated INTEGER,
        category VARCHAR(64),
        INDEX idx_user_id (user_id),
        INDEX idx_category (category),
        INDEX idx_dated (dated),
        INDEX idx_user_category (user_id, category)
    )
    """

    session.execute(text(create_table_sql))
    logger.debug(f"Created temporary table: {temp_table_name}")

    # Use MySQL recursive CTE to split space-separated abs_categories directly in SQL
    # This creates multiple rows for each category in abs_categories
    insert_sql = f"""
    INSERT INTO {temp_table_name} (document_id, user_id, dated, category)
    WITH RECURSIVE category_splitter AS (
        SELECT
            po.document_id,
            po.user_id,
            d.dated,
            TRIM(SUBSTRING_INDEX(m.abs_categories, ' ', 1)) AS category,
            CASE
                WHEN LOCATE(' ', m.abs_categories) > 0
                THEN TRIM(SUBSTRING(m.abs_categories, LOCATE(' ', m.abs_categories) + 1))
                ELSE ''
            END AS remaining_categories,
            1 AS level
        FROM arXiv_paper_owners po
        INNER JOIN arXiv_documents d ON po.document_id = d.document_id
        INNER JOIN arXiv_metadata m ON po.document_id = m.document_id
        WHERE d.dated BETWEEN :start_timestamp AND :end_timestamp
          AND po.flag_author = 1
          AND po.valid = 1
          AND m.is_current = 1
          AND m.is_withdrawn = 0
          AND m.abs_categories IS NOT NULL
          AND m.abs_categories != ''
          AND TRIM(m.abs_categories) != ''

        UNION ALL

        SELECT
            document_id,
            user_id,
            dated,
            TRIM(SUBSTRING_INDEX(remaining_categories, ' ', 1)) AS category,
            CASE
                WHEN LOCATE(' ', remaining_categories) > 0
                THEN TRIM(SUBSTRING(remaining_categories, LOCATE(' ', remaining_categories) + 1))
                ELSE ''
            END AS remaining_categories,
            level + 1
        FROM category_splitter
        WHERE remaining_categories != ''
          AND level < 10  -- Prevent infinite recursion, max 10 categories per paper
    )
    SELECT document_id, user_id, dated, category
    FROM category_splitter
    WHERE category != ''
    """

    start_time = time.time()
    result = session.execute(text(insert_sql), {
        'start_timestamp': start_timestamp,
        'end_timestamp': end_timestamp
    })
    insert_time = time.time() - start_time

    row_count = result.rowcount
    logger.info(f"Inserted {row_count} denormalized rows into temp table in {insert_time:.3f}s using MySQL recursive CTE")

    return temp_table_name



def _query_temp_table_candidates(session: Session, temp_table_name: str) -> List[tuple]:
    """Query the temp table to get endorsement candidates using category-specific thresholds from EndorsementDomain."""

    query_sql = f"""
    SELECT
        t.user_id,
        t.category,
        COUNT(DISTINCT t.document_id) as document_count,
        MAX(t.dated) as latest,
        ed.papers_to_endorse
    FROM {temp_table_name} t
    INNER JOIN arXiv_endorsement_domains ed ON t.category = ed.endorsement_domain
    GROUP BY t.user_id, t.category, ed.papers_to_endorse
    HAVING COUNT(DISTINCT t.document_id) >= ed.papers_to_endorse
    ORDER BY t.user_id, t.category
    """

    start_time = time.time()
    result = session.execute(text(query_sql))
    candidates = result.fetchall()
    query_time = time.time() - start_time

    logger.info(f"Found {len(candidates)} candidate records (user_id, category pairs) with category-specific thresholds in {query_time:.3f}s")
    return candidates


def _cleanup_temp_table(session: Session, temp_table_name: str):
    """Drop the temporary table."""
    try:
        session.execute(text(f"DROP TEMPORARY TABLE {temp_table_name}"))
        logger.debug(f"Dropped temporary table: {temp_table_name}")
    except Exception as e:
        logger.warning(f"Failed to drop temp table {temp_table_name}: {e}")


async def list_endorsement_candidates_v2(
    session: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[EndorsementCandidates]:
    """
    Get endorsement candidates using temp table approach for performance comparison.

    This version implements a different strategy:
    1. Find minimum papers_to_endorse threshold from EndorsementDomain
    2. Create temp table with PaperOwner + Metadata data for date range
    3. Query temp table to get candidates grouped by user_id and abs_categories
    4. Process results into category-specific candidate lists

    Args:
        session: SQLAlchemy database session
        start_date: Start date for paper filtering (defaults to 5y ago)
        end_date: End date for paper filtering (defaults to 3mo ago)

    Returns:
        List of EndorsementCandidates objects organized by category
    """
    total_start_time = time.time()

    if start_date is None:
        start_date = (datetime.now(timezone.utc) - timedelta(days=5*365)).date()
    if end_date is None:
        end_date = (datetime.now(timezone.utc) - timedelta(days=90)).date()

    logger.info(f"Starting endorser list v2 for date range {start_date} to {end_date}")

    timestamp = datetime.now(timezone.utc)

    # Step 1: Create and populate temp table (run in thread pool)
    step_start = time.time()
    temp_table_name = await asyncio.get_event_loop().run_in_executor(
        None, _create_temp_table, session, start_date, end_date
    )
    step_time = time.time() - step_start
    logger.debug(f"Step 1 (create temp table): {step_time:.3f}s")

    try:
        # Step 2: Query temp table for candidates with category-specific thresholds (run in thread pool)
        step_start = time.time()
        raw_candidates = await asyncio.get_event_loop().run_in_executor(
            None, _query_temp_table_candidates, session, temp_table_name
        )
        step_time = time.time() - step_start
        logger.debug(f"Step 2 (query candidates with thresholds): {step_time:.3f}s")

        per_cat = {}
        results = []

        for user_id, cat, doc_count, latest, papers_to_endorse in raw_candidates:
            if doc_count < papers_to_endorse:
                continue
            if cat not in per_cat:
                candidates = EndorsementCandidates(
                    timestamp=timestamp,
                    category=cat,
                    candidates=[]
                )
                per_cat[cat] = candidates
                results.append(candidates)
            else:
                candidates = per_cat[cat]
                pass

            candidates.candidates.append(EndorsementCandidate(
                id=user_id,
                category=cat,
                document_count=doc_count,
                latest=latest
            ))

        total_time = time.time() - total_start_time
        logger.info(f"Endorser list v2 completed in {total_time:.3f}s, found {len(raw_candidates)} raw candidate records")
        return results

    finally:
        # Always cleanup temp table (run in thread pool)
        await asyncio.get_event_loop().run_in_executor(
            None, _cleanup_temp_table, session, temp_table_name
        )