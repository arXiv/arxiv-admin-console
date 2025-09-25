#!/usr/bin/env python3
"""Standalone CLI script to create endorsement candidates SQLite database."""

import argparse
import sys
import os
from datetime import datetime, date, timedelta, timezone
from pathlib import Path

# Add the parent directories to the path so we can import arxiv_admin_api modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from arxiv.base import logging
from arxiv.config import Settings
from arxiv_bizlogic.database import Database
from arxiv_admin_api.biz.endorser_list import _list_endorsement_candidates, _process_candidates, _process_categories
from arxiv.db.models import EndorsementDomain, Category
import sqlite3
import gzip
import json
import time

logger = logging.getLogger(__name__)


def serialize_endorsement_candidates(candidates, output_path):
    """Serialize endorsement candidates to compressed SQLite file."""
    # Create in-memory database
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    # Create table
    cursor.execute('''
        CREATE TABLE endorsement_candidates (
            timestamp TEXT,
            category TEXT,
            candidates TEXT
        )
    ''')

    # Insert data
    for candidate_group in candidates:
        candidates_json = json.dumps([
            {
                'id': candidate.id,
                'category': candidate.category,
                'document_count': candidate.document_count,
                'latest': candidate.latest.isoformat()
            }
            for candidate in candidate_group.candidates
        ])

        cursor.execute(
            'INSERT INTO endorsement_candidates (timestamp, category, candidates) VALUES (?, ?, ?)',
            (candidate_group.timestamp.isoformat(), candidate_group.category, candidates_json)
        )

    conn.commit()

    # Serialize to bytes and compress
    db_bytes = conn.serialize()
    conn.close()

    # Write compressed data to file
    with gzip.open(output_path, 'wb') as f:
        f.write(db_bytes)

    logger.info(f"Successfully wrote {len(candidates)} endorsement categories to {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Create endorsement candidates SQLite database')
    parser.add_argument('--output', required=True, help='Output SQLite file path')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    parser.add_argument('--db-url', help='Database URL (optional, uses environment if not provided)')

    args = parser.parse_args()

    # Parse dates
    start_date = None
    end_date = None

    if args.start_date:
        try:
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date()
        except ValueError:
            logger.error(f"Invalid start date format: {args.start_date}. Use YYYY-MM-DD")
            sys.exit(1)

    if args.end_date:
        try:
            end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date()
        except ValueError:
            logger.error(f"Invalid end date format: {args.end_date}. Use YYYY-MM-DD")
            sys.exit(1)

    # Set database URL if provided
    db_uri = args.db_url or os.environ.get('CLASSIC_DB_URI')
    if not db_uri:
        logger.error("Database URI not provided. Use --db-url or set CLASSIC_DB_URI environment variable")
        sys.exit(1)

    logger.info(f"Starting endorsement candidates generation")
    logger.info(f"Output file: {args.output}")
    logger.info(f"Date range: {start_date or 'default'} to {end_date or 'default'}")

    start_time = time.time()

    try:
        # Initialize database
        settings = Settings(
            CLASSIC_DB_URI=db_uri,
            LATEXML_DB_URI=None
        )
        database = Database(settings)
        database.set_to_global()

        # Get database session
        from arxiv_bizlogic.fastapi_helpers import get_db
        db_session = next(get_db())

        try:
            # Get endorsement criteria
            endorsement_criteria = {}
            for criteria in db_session.query(EndorsementDomain).all():
                endorsement_criteria[criteria.endorsement_domain] = criteria

            # Get valid categories
            valid_categories = set()
            for cat in db_session.query(Category).all():
                if cat.subject_class:
                    cat_name = f"{cat.archive}.{cat.subject_class}"
                    valid_categories.add(cat_name)
                else:
                    valid_categories.add(cat.archive)

            # Get raw endorsement candidates
            logger.info("Fetching endorsement candidates from database...")
            unprocessed = _list_endorsement_candidates(db_session, start_date, end_date)
            logger.info(f"Found {len(unprocessed)} raw endorsement records")

            # Process candidates
            logger.info("Processing endorsement candidates...")
            timestamp = datetime.now(timezone.utc)
            process_start = time.time()
            endorsement_candidates_0 = _process_candidates(unprocessed, valid_categories)
            process_time = time.time() - process_start

            # Filter by criteria
            logger.info("Applying endorsement criteria...")
            filter_start = time.time()
            endorsement_candidates_result = _process_categories(timestamp, endorsement_candidates_0, endorsement_criteria)
            filter_time = time.time() - filter_start

            total_time = time.time() - start_time
            logger.info(f"Processing completed: {total_time:.3f}s total "
                       f"(process: {process_time:.3f}s, filter: {filter_time:.3f}s), "
                       f"{len(endorsement_candidates_result)} categories with qualified candidates")

            # Serialize to file
            logger.info(f"Writing results to {args.output}...")
            serialize_endorsement_candidates(endorsement_candidates_result, args.output)

            logger.info("Endorsement candidates database creation completed successfully")

        finally:
            db_session.close()

    except Exception as e:
        logger.error(f"Failed to create endorsement candidates database: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()