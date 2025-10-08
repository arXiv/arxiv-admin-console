"""SQLite database utilities for endorsement candidates caching with concurrent processing."""
import sqlite3
import gzip
import io
import asyncio
from multiprocessing import Queue, Process
from datetime import datetime, date, timedelta, timezone
from typing import List, Optional, Dict, Tuple
from pathlib import Path
from collections import defaultdict

from google.cloud import storage
from urllib.parse import urlparse
from fastapi import HTTPException, status, Request
from sqlalchemy import create_engine, select, Engine, and_, func
from sqlalchemy.orm import Session

from arxiv.base import logging
from arxiv.db.models import Category, Document, Metadata, PaperOwner, Demographic, EndorsementDomain

from .endorsing_models import EndorsingBase, EndorsingCategoryModel, EndorsingCandidateModel, EndorsementCandidates, EndorsementCandidate

logger = logging.getLogger(__name__)

# Cache for SQLAlchemy engines to avoid repeated deserialization
_db_cache = {}


class DocumentRecord:
    """Represents a single document record from the query."""
    __slots__ = ('user_id', 'dated', 'category')

    def __init__(self, user_id: int, dated: datetime, category: str):
        self.user_id = user_id
        self.dated = dated
        self.category = category


class AggregatedCandidate:
    """Holds aggregated data for a user-category pair."""
    __slots__ = ('user_id', 'category', 'count', 'latest')

    def __init__(self, user_id: int, category: str, count: int, latest: datetime):
        self.user_id = user_id
        self.category = category
        self.count = count
        self.latest = latest


def endorsing_db_get_cache(request: Request) -> str:
    """Generate cache key based on storage URL."""
    scheme, location, path = endorsing_db_parse_storage_url(request)
    return f"{scheme}://{location}/{path}" if scheme == 'gs' else f"file://{path}"


def endorsing_db_invalidate_cache():
    """Clear the database cache."""
    global _db_cache
    for engine in _db_cache.values():
        if engine:
            engine.dispose()
    _db_cache.clear()


def endorsing_db_get_cached_db(request: Request) -> Engine:
    """Get cached database engine or create new one."""
    cache_key = endorsing_db_get_cache(request)

    if cache_key not in _db_cache:
        _db_cache[cache_key] = endorsing_db_read_cached_data(request)

    return _db_cache[cache_key]


def endorsing_db_create() -> Engine:
    """
    Create an in-memory SQLite database for endorsement candidates using SQLAlchemy 2.0.

    Returns SQLAlchemy engine with tables created.
    """
    engine = create_engine("sqlite:///:memory:", echo=False)
    EndorsingBase.metadata.create_all(engine)
    return engine


def populate_categories(engine: Engine, categories: List[Category]):
    """
    Populate the endorsing database with category data from arXiv Category model.

    Creates EndorsingCategory entries based on arXiv categories.
    Category format: "archive.subject_class" if subject_class exists, otherwise just "archive".
    """
    with Session(engine) as session:
        for cat in categories:
            # Construct category string
            if cat.subject_class:
                category_str = f"{cat.archive}.{cat.subject_class}"
            else:
                category_str = cat.archive

            # Check if category already exists
            stmt = select(EndorsingCategoryModel).where(EndorsingCategoryModel.category == category_str)
            existing_category = session.scalar(stmt)

            if not existing_category:
                # Create new category
                category_obj = EndorsingCategoryModel(
                    category=category_str
                )
                session.add(category_obj)

        session.commit()


def populate_endorsements(engine: Engine, data: List[EndorsementCandidate]) -> None:
    """
    Populate SQLite database with endorsement candidates data using SQLAlchemy 2.0.
    Uses autocommit mode for direct writes without transaction overhead.
    """
    # Get categories once outside the loop
    with Session(engine) as session:
        categories: Dict[str, EndorsingCategoryModel] = {cat.category: cat for cat in session.query(EndorsingCategoryModel).all()}

    # Use raw connection with autocommit
    # Going through transaction + sqlalchemy overhead slows down by 1+ minutes. This is done in 2 seconds.

    conn = engine.raw_connection()
    try:
        cursor = conn.cursor()

        # Prepare batch of values
        values = []
        for candidate in data:
            if candidate.category not in categories:
                logger.warning(f"Skipping category {candidate.category} because it is not in the database")
                continue

            category: EndorsingCategoryModel = categories[candidate.category]
            values.append((candidate.id, category.id, candidate.document_count, candidate.latest, candidate.timestamp))

        # Insert all at once with executemany
        if values:
            cursor.executemany(
                "INSERT INTO endorsement_candidates (user_id, category_id, document_count, latest, timestamp) VALUES (?, ?, ?, ?, ?)",
                values
            )
            conn.commit()  # Explicit commit
            logger.info(f"Inserted {len(values)} endorsement candidates")
    finally:
        conn.close()


def endorsing_db_serialize_to_gzip(engine: Engine) -> bytes:
    """
    Serialize SQLite database to gzipped bytes using in-memory serialization.
    """
    # Get raw SQLite connection from SQLAlchemy engine
    raw_conn = engine.raw_connection()
    try:
        db_bytes = raw_conn.connection.serialize()
    finally:
        raw_conn.close()

    # Compress with gzip
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode='wb') as gz_file:
        gz_file.write(db_bytes)

    return buffer.getvalue()


def endorsing_db_deserialize_from_gzip(gzip_data: bytes) -> Engine:
    """
    Deserialize gzipped SQLite database bytes back to in-memory SQLAlchemy engine.
    """
    # Decompress gzip data to get raw SQLite database bytes
    with gzip.GzipFile(fileobj=io.BytesIO(gzip_data), mode='rb') as gz_file:
        db_bytes = gz_file.read()

    # Create in-memory connection and deserialize the database
    conn = sqlite3.connect(':memory:')
    conn.deserialize(db_bytes)

    # Create SQLAlchemy engine from the connection
    # We need to use the NullPool to avoid connection pooling issues
    from sqlalchemy.pool import NullPool
    engine = create_engine("sqlite:///:memory:", poolclass=NullPool, creator=lambda: conn, echo=False)

    return engine


def endorsing_db_query_users_in_categories(engine: Engine, category: str | List[str]) -> Optional[List[EndorsementCandidate]]:
    """
    Query specific category candidates from SQLite database using SQLAlchemy 2.0.
    Supports both single category (str) or list of categories (List[str]).
    When multiple categories are provided, returns union of all candidates.
    """
    # Convert single category to list for uniform processing
    categories = [category] if isinstance(category, str) else category

    all_candidates: List[EndorsementCandidate] = []

    with Session(engine) as session:
        results = session.query(
            EndorsingCandidateModel.user_id.label('id'),
            EndorsingCategoryModel.category,
            EndorsingCandidateModel.document_count,
            EndorsingCandidateModel.latest,
            EndorsingCandidateModel.timestamp
        ).join(EndorsingCategoryModel).filter(EndorsingCategoryModel.category.in_(categories)).all()
        return [EndorsementCandidate.model_validate(candidate) for candidate in results]

    return all_candidates if all_candidates else None


def endorsing_db_query_users_in_category(engine: Engine, category: str, user_ids: Optional[List[int]] = None) -> List[EndorsementCandidate]:
    """
    Query specific users from database, optionally filtered by user IDs using SQLAlchemy 2.0.
    """
    with Session(engine) as session:
        # Build base query
        query = session.query(
            EndorsingCandidateModel.user_id.label('id'),
            EndorsingCategoryModel.category,
            EndorsingCandidateModel.document_count,
            EndorsingCandidateModel.latest,
            EndorsingCandidateModel.timestamp
        ).join(EndorsingCategoryModel, EndorsingCandidateModel.category_id == EndorsingCategoryModel.id).filter(EndorsingCategoryModel.category == category)

        # Add user ID filter if provided
        if user_ids:
            query = query.filter(EndorsingCandidateModel.id.in_(user_ids))
        return [EndorsementCandidate.model_validate(candidate) for candidate in query.all()]


def endorsing_db_query_user(engine: Engine, user_id: int) -> List[EndorsementCandidate]:
    """
    Query a single user from database, returning all matching records across all categories using SQLAlchemy 2.0.
    """
    with Session(engine) as session:
        query = session.query(
            EndorsingCandidateModel.user_id.label('id'),
            EndorsingCategoryModel.category,
            EndorsingCandidateModel.document_count,
            EndorsingCandidateModel.latest,
            EndorsingCandidateModel.timestamp
        ).join(EndorsingCategoryModel).filter(EndorsingCategoryModel.id == EndorsingCandidateModel.category_id)
        return [EndorsementCandidate.model_validate(candidate) for candidate in query.all()]


def endorsing_db_query_all_categories(engine: Engine) -> List[EndorsementCandidates]:
    """
    Query all categories and candidates from SQLite database using SQLAlchemy 2.0.
    """
    with Session(engine) as session:
        # Get all categories with their candidates
        stmt = select(EndorsingCategoryModel)
        categories = session.execute(stmt).scalars().all()

    result: List[EndorsementCandidates] = []

    for category_obj in categories:
        candidates = endorsing_db_query_users_in_categories(engine, category_obj.category)

        result.append(EndorsementCandidates(
            category=category_obj.category,
            candidates = candidates if candidates else []
        ))

    return result


def endorsing_db_parse_storage_url(request: Request) -> tuple[str, str, str]:
    """
    Parse storage URL from app configuration and return scheme, location, and path.

    Supports:
    - GCS: gs://bucket-name/path/to/object.json
    - Local file: file:///path/to/file.json

    Returns:
        Tuple of (scheme, location, path) where:
        - For GCS: ('gs', bucket_name, object_name)
        - For file: ('file', '', file_path)
    """
    url = request.app.extra.get('ENDORSER_POOL_OBJECT_URL')
    if not url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ENDORSER_POOL_OBJECT_URL is not configured"
        )

    # Parse URL using urlparse
    parsed_url = urlparse(url)

    if parsed_url.scheme == 'gs':
        bucket_name = parsed_url.netloc
        object_name = parsed_url.path.lstrip('/')  # Remove leading slash from path
        return 'gs', bucket_name, object_name
    elif parsed_url.scheme == 'file':
        file_path = parsed_url.path
        return 'file', '', file_path
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid storage URL format. Expected gs://bucket-name/object-name or file:///path/to/file.json"
        )


def endorsing_db_read_cached_data(request: Request) -> Engine:
    """
    Helper function to read cached endorsement data from storage.

    Returns SQLAlchemy Engine from either GCS or local file storage.
    """
    # Parse storage info from configuration
    scheme, location, path = endorsing_db_parse_storage_url(request)

    try:
        if scheme == 'gs':
            logger.info(f"Fetching cached endorsement candidates from gs://{location}/{path}")

            # Initialize GCS client (uses default credentials from environment)
            client = storage.Client()
            bucket = client.bucket(location)
            blob = bucket.blob(path)

            # Download and parse JSON content
            if not blob.exists():
                logger.error(f"Object {path} not found in bucket {location}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cached endorsement data not found"
                )

            # Download gzipped database bytes
            gzip_data = blob.download_as_bytes()

        elif scheme == 'file':
            logger.info(f"Fetching cached endorsement candidates from file://{path}")

            # Check if file exists
            file_path = Path(path)
            if not file_path.exists():
                logger.error(f"File {path} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cached endorsement data file not found"
                )

            # Read gzipped database bytes
            gzip_data = file_path.read_bytes()
        else:
            raise ValueError(f"Invalid storage scheme: {scheme}")

        # Deserialize gzipped data to SQLAlchemy engine
        engine = endorsing_db_deserialize_from_gzip(gzip_data)
        logger.debug(f"Successfully fetched cached endorsement candidates from {scheme} storage")
        return engine

    except (gzip.BadGzipFile, sqlite3.Error) as e:
        logger.error(f"Invalid database format in cached data: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid database format in cached endorsement data"
        )
    except storage.exceptions.NotFound:
        logger.error(f"Bucket {location} or object {path} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cached endorsement data not found in storage"
        )
    except storage.exceptions.Forbidden:
        logger.error(f"Access denied to bucket {location}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to endorsement data storage"
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching cached data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch cached endorsement data from storage"
        )


def _fetch_documents_batched(
    session: Session,
    start_timestamp: int,
    end_timestamp: int,
    batch_size: int = 10000
):
    """
    Fetch documents and related data in batches using 3-step approach.

    Yields tuples of (user_id, dated, abs_categories) for each document.

    Args:
        session: SQLAlchemy session
        start_timestamp: Start timestamp for filtering
        end_timestamp: End timestamp for filtering
        batch_size: Number of documents to fetch per batch

    Yields:
        Tuple of (user_id, dated, abs_categories)
    """
    offset = 0

    while True:
        # Step 1: Get batch of documents in date range
        doc_batch = (
            session.query(Document.document_id, Document.dated)
            .filter(Document.dated.between(start_timestamp, end_timestamp))
            .limit(batch_size)
            .offset(offset)
            .all()
        )

        if not doc_batch:
            break

        doc_ids = [doc.document_id for doc in doc_batch]
        doc_dated_map = {doc.document_id: doc.dated for doc in doc_batch}

        logger.debug(f"Fetched batch at offset {offset}: {len(doc_ids)} documents")

        # Step 2: Get user_id + document_id for qualifying authors
        user_docs = (
            session.query(
                PaperOwner.user_id,
                PaperOwner.document_id
            )
            .join(
                Demographic,
                Demographic.user_id == PaperOwner.user_id
            )
            .filter(
                PaperOwner.document_id.in_(doc_ids),
                PaperOwner.valid == 1,
                PaperOwner.flag_author == 1,
                Demographic.veto_status == 'ok'
            )
            .all()
        )

        # Build document_id -> list of user_ids mapping
        doc_users_map: Dict[str, List[int]] = defaultdict(list)
        for user_id, doc_id in user_docs:
            doc_users_map[doc_id].append(user_id)

        # Step 3: Get abs_categories for documents
        metadata_batch = (
            session.query(
                Metadata.document_id,
                Metadata.abs_categories
            )
            .filter(
                Metadata.document_id.in_(doc_ids),
                Metadata.is_current == 1,
                Metadata.is_withdrawn == 0
            )
            .all()
        )

        # Step 4: Merge results and yield
        for metadata in metadata_batch:
            doc_id = metadata.document_id
            abs_categories = metadata.abs_categories
            dated = doc_dated_map.get(doc_id)

            if doc_id in doc_users_map and dated is not None:
                for user_id in doc_users_map[doc_id]:
                    yield (user_id, dated, abs_categories)

        offset += batch_size


def _worker_process(input_queue: Queue, output_queue: Queue, valid_categories: set, endorsement_domains: Dict[str, dict]):
    """
    Worker process that aggregates records by (user_id, category) and filters by threshold.

    Args:
        input_queue: Queue receiving DocumentRecord tuples (user_id, dated_timestamp, category)
        output_queue: Queue for sending aggregated results
        valid_categories: Set of valid category names
        endorsement_domains: Dictionary of endorsement domain criteria (serialized)
    """
    # Aggregate by (user_id, category)
    aggregates: Dict[Tuple[int, str], AggregatedCandidate] = {}

    while True:
        item = input_queue.get()

        # Sentinel value to stop processing
        if item is None:
            break

        user_id, dated_timestamp, category = item

        if category not in valid_categories:
            continue

        key = (user_id, category)
        dated = datetime.fromtimestamp(dated_timestamp, tz=timezone.utc)

        if key in aggregates:
            agg = aggregates[key]
            agg.count += 1
            # Keep the earliest date (becomes "latest" in output)
            if dated < agg.latest:
                agg.latest = dated
        else:
            aggregates[key] = AggregatedCandidate(
                user_id=user_id,
                category=category,
                count=1,
                latest=dated
            )

    # Filter by threshold before sending results back
    qualified_results = []
    for agg in aggregates.values():
        # Find criteria for this category
        criteria = endorsement_domains.get(agg.category)
        if criteria is None:
            # Try parent category
            parts = agg.category.split(".")
            if len(parts) == 2:
                criteria = endorsement_domains.get(parts[0])

        if criteria is None:
            continue

        # Only include if meets threshold
        if agg.count >= criteria['papers_to_endorse']:
            qualified_results.append((agg.user_id, agg.category, agg.count, agg.latest))

    output_queue.put(qualified_results)


def _process_concurrently(
    data_generator,
    num_workers: int,
    valid_categories: set,
    endorsement_domains: Dict[str, EndorsementDomain],
    timestamp: datetime
) -> List[EndorsementCandidate]:
    """
    Process pre-fetched data using multiprocessing workers.

    Args:
        data_generator: Generator yielding (user_id, dated, abs_categories) tuples
        num_workers: Number of worker processes
        valid_categories: Set of valid category names
        endorsement_domains: Dictionary of endorsement domain criteria
        timestamp: Timestamp for the endorsement candidates

    Returns:
        List of EndorsementCandidates organized by category
    """
    # Serialize endorsement_domains for multiprocessing (convert to dict)
    endorsement_domains_serialized = {
        domain: {'papers_to_endorse': criteria.papers_to_endorse}
        for domain, criteria in endorsement_domains.items()
    }

    # Create worker queues
    input_queues = [Queue(maxsize=100) for _ in range(num_workers)]
    output_queue = Queue()

    # Start workers
    workers = []
    for i in range(num_workers):
        p = Process(target=_worker_process, args=(input_queues[i], output_queue, valid_categories, endorsement_domains_serialized))
        p.start()
        workers.append(p)

    logger.info("Distributing batched data to workers...")

    # Distribute data from generator to workers
    for user_id, dated, abs_categories in data_generator:
        # Split categories by space
        categories = abs_categories.split()
        for cat in categories:
            if not cat or cat not in valid_categories:
                continue

            # Send to queue based on user_id mod N
            channel_idx = user_id % num_workers
            input_queues[channel_idx].put((user_id, dated, cat))

    # Send sentinel values to stop workers
    for q in input_queues:
        q.put(None)

    # Collect results from all workers
    all_aggregates = []
    for i in range(num_workers):
        worker_results = output_queue.get()
        all_aggregates.extend(worker_results)

    # Wait for all workers to finish
    for p in workers:
        p.join()

    # Convert tuples to EndorsementCandidate objects
    result = []
    for user_id, category, count, latest in all_aggregates:
        result.append(EndorsementCandidate(
            id=user_id,
            category=category,
            document_count=count,
            latest=latest,
            timestamp=timestamp
        ))

    return result


def post_process(all_aggregates, timestamp):
    # Group qualified candidates by category
    candidates_by_category: Dict[str, List[EndorsementCandidate]] = defaultdict(list)

    for user_id, category, count, latest in all_aggregates:
        candidates_by_category[category].append(EndorsementCandidate(
            id=user_id,
            category=category,
            document_count=count,
            latest=latest,
            timestamp=timestamp
        ))

    # Build final result
    return [
        EndorsementCandidates(category=cat, candidates=candidates)
        for cat, candidates in candidates_by_category.items()
    ]


async def endorsing_db_list_endorsement_candidates(
    session: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    num_workers: int = 4,
    batch_size: int = 10000
) -> List[EndorsementCandidate]:
    """
    Query endorsement candidates from MySQL database using batched queries and concurrent processing.

    Uses a 3-step batched approach to avoid slow 4-way joins:
    1. Fetch documents in date range (batches of batch_size)
    2. For each batch, fetch qualifying user_ids from PaperOwner + Demographics
    3. For each batch, fetch abs_categories from Metadata
    4. Merge in-memory and distribute to worker processes for aggregation

    This approach is optimized for read replicas where consistency is not critical.

    Args:
        session: SQLAlchemy session connected to arXiv database
        start_date: Start date for paper filtering (defaults to 5 years ago)
        end_date: End date for paper filtering (defaults to 3 months ago)
        num_workers: Number of worker processes for parallel processing
        batch_size: Number of documents to fetch per batch

    Returns:
        List of EndorsementCandidate (flat list of all qualified candidates)
    """
    import time
    start_time = time.time()
    timestamp = datetime.now(timezone.utc)

    # Set default dates
    if start_date is None:
        start_date = (datetime.now(timezone.utc) - timedelta(days=5*365)).date()
    if end_date is None:
        end_date = (datetime.now(timezone.utc) - timedelta(days=90)).date()

    logger.info(f"Querying endorsement candidates (v2 batched) from {start_date} to {end_date}")

    # Disable SQL echo for this session to reduce log noise
    if hasattr(session, 'bind') and hasattr(session.bind, 'echo'):
        old_echo = session.bind.echo
        session.bind.echo = False
    else:
        old_echo = None

    try:
        # Get endorsement domains
        endorsement_domains = {}
        for domain in session.query(EndorsementDomain).all():
            endorsement_domains[domain.endorsement_domain] = domain

        # Get valid categories
        valid_categories = set()
        for cat in session.query(Category).filter(Category.active == 1).all():
            if cat.subject_class:
                cat_name = f"{cat.archive}.{cat.subject_class}"
            else:
                cat_name = cat.archive
            valid_categories.add(cat_name)

        # Convert dates to timestamps
        start_timestamp = int(datetime.combine(start_date, datetime.min.time()).timestamp())
        end_timestamp = int(datetime.combine(end_date, datetime.min.time()).timestamp())

        # Create data generator
        data_generator = _fetch_documents_batched(
            session,
            start_timestamp,
            end_timestamp,
            batch_size
        )

        # Process with workers - run in thread pool to avoid blocking the event loop
        result = await asyncio.to_thread(
            _process_concurrently,
            data_generator,
            num_workers,
            valid_categories,
            endorsement_domains,
            timestamp
        )

        total_time = time.time() - start_time
        logger.info(f"Endorsement processing: {total_time:.3f}s total, "
                    f"{len(result)} qualified candidates")

        return result

    finally:
        # Restore original echo setting
        if old_echo is not None and hasattr(session, 'bind'):
            session.bind.echo = old_echo
