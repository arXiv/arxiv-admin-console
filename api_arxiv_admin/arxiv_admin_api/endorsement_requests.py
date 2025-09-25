"""arXiv endorsement routes."""
import re
from datetime import timedelta, datetime, date, UTC
from sqlite3 import IntegrityError
from typing import Optional, List

from arxiv.auth.user_claims import ArxivUserClaims
from arxiv_bizlogic.fastapi_helpers import get_authn, get_authn_user, ApiToken, get_authn_or_none
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, Request

from sqlalchemy import case, and_  # select, update, func, Select, distinct, exists, and_, or_
from sqlalchemy.orm import Session #, joinedload
import sqlite3
import gzip
import io
from google.cloud import storage
from urllib.parse import urlparse
from pathlib import Path

from pydantic import BaseModel
from arxiv.base import logging
from arxiv.db.models import EndorsementRequest, Demographic, TapirNickname, TapirUser

from . import get_db, datetime_to_epoch, VERY_OLDE, is_any_user, get_current_user #  is_admin_user,
from .biz.endorsement_code import endorsement_code
from .biz.endorser_list import list_endorsement_candidates, EndorsementCandidates, EndorsementCandidate

# Cache for SQLite connections to avoid repeated deserialization
_db_cache = {}

def _get_cache_key(request: Request) -> str:
    """Generate cache key based on storage URL."""
    scheme, location, path = _parse_storage_url(request)
    return f"{scheme}://{location}/{path}" if scheme == 'gs' else f"file://{path}"

def _invalidate_db_cache():
    """Clear the database cache."""
    global _db_cache
    for conn in _db_cache.values():
        if conn:
            conn.close()
    _db_cache.clear()

def _get_cached_db_connection(request: Request) -> sqlite3.Connection:
    """Get cached database connection or create new one."""
    cache_key = _get_cache_key(request)

    if cache_key not in _db_cache:
        _db_cache[cache_key] = _read_cached_data(request)

    return _db_cache[cache_key]

def _create_endorsement_db() -> sqlite3.Connection:
    """
    Create an in-memory SQLite database for endorsement candidates.

    Returns connection to in-memory database with tables created.
    """
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
        CREATE TABLE endorsement_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL UNIQUE,
            timestamp TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE endorsement_candidates (
            id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            document_count INTEGER NOT NULL,
            latest TEXT NOT NULL,
            FOREIGN KEY (category_id) REFERENCES endorsement_categories (id),
            PRIMARY KEY (id, category_id)
        )
    ''')

    conn.commit()
    return conn


def _populate_endorsement_db(conn: sqlite3.Connection, data: List[EndorsementCandidates]) -> None:
    """
    Populate SQLite database with endorsement candidates data.
    """
    cursor = conn.cursor()

    for category_data in data:
        # Insert category
        cursor.execute('''
            INSERT OR REPLACE INTO endorsement_categories (category, timestamp)
            VALUES (?, ?)
        ''', (category_data.category, category_data.timestamp.isoformat()))

        category_id = cursor.lastrowid

        # Insert candidates for this category
        for candidate in category_data.candidates:
            cursor.execute('''
                INSERT OR REPLACE INTO endorsement_candidates
                (id, category_id, document_count, latest)
                VALUES (?, ?, ?, ?)
            ''', (candidate.id, category_id, candidate.document_count, candidate.latest.isoformat()))

    conn.commit()


def _serialize_db_to_gzip(conn: sqlite3.Connection) -> bytes:
    """
    Serialize SQLite database to gzipped bytes using in-memory serialization.
    """
    # Serialize the database to bytes directly from memory
    db_bytes = conn.serialize()

    # Compress with gzip
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode='wb') as gz_file:
        gz_file.write(db_bytes)

    return buffer.getvalue()


def _deserialize_gzip_to_db(gzip_data: bytes) -> sqlite3.Connection:
    """
    Deserialize gzipped SQLite database bytes back to in-memory connection.
    """
    # Decompress gzip data to get raw SQLite database bytes
    with gzip.GzipFile(fileobj=io.BytesIO(gzip_data), mode='rb') as gz_file:
        db_bytes = gz_file.read()

    # Create in-memory connection and deserialize the database
    conn = sqlite3.connect(':memory:')
    conn.deserialize(db_bytes)

    return conn


def _query_category_from_db(conn: sqlite3.Connection, category: str) -> Optional[List[EndorsementCandidate]]:
    """
    Query specific category candidates from SQLite database.
    """
    cursor = conn.cursor()

    cursor.execute('''
        SELECT c.id, c.document_count, c.latest
        FROM endorsement_candidates c
        JOIN endorsement_categories cat ON c.category_id = cat.id
        WHERE cat.category = ?
    ''', (category,))

    rows = cursor.fetchall()
    if not rows:
        return None

    return [
        EndorsementCandidate(
            id=row[0],
            category=category,
            document_count=row[1],
            latest=datetime.fromisoformat(row[2])
        )
        for row in rows
    ]


def _query_users_from_db(conn: sqlite3.Connection, category: str, user_ids: Optional[List[int]] = None) -> List[EndorsementCandidate]:
    """
    Query specific users from database, optionally filtered by user IDs.
    """
    cursor = conn.cursor()

    if user_ids:
        # Query specific user IDs in the category
        placeholders = ','.join('?' * len(user_ids))
        cursor.execute(f'''
            SELECT c.id, c.document_count, c.latest
            FROM endorsement_candidates c
            JOIN endorsement_categories cat ON c.category_id = cat.id
            WHERE cat.category = ? AND c.id IN ({placeholders})
        ''', [category] + user_ids)
    else:
        # Query all users in the category
        cursor.execute('''
            SELECT c.id, c.document_count, c.latest
            FROM endorsement_candidates c
            JOIN endorsement_categories cat ON c.category_id = cat.id
            WHERE cat.category = ?
        ''', (category,))

    rows = cursor.fetchall()
    return [
        EndorsementCandidate(
            id=row[0],
            category=category,
            document_count=row[1],
            latest=datetime.fromisoformat(row[2])
        )
        for row in rows
    ]


def _query_all_categories_from_db(conn: sqlite3.Connection) -> List[EndorsementCandidates]:
    """
    Query all categories and candidates from SQLite database.
    """
    cursor = conn.cursor()

    # Get all categories
    cursor.execute('SELECT id, category, timestamp FROM endorsement_categories')
    categories = cursor.fetchall()

    result = []
    for cat_id, category, timestamp in categories:
        # Get candidates for this category
        cursor.execute('''
            SELECT id, document_count, latest
            FROM endorsement_candidates
            WHERE category_id = ?
        ''', (cat_id,))

        candidates = [
            EndorsementCandidate(
                id=row[0],
                category=category,
                document_count=row[1],
                latest=datetime.fromisoformat(row[2])
            )
            for row in cursor.fetchall()
        ]

        result.append(EndorsementCandidates(
            timestamp=datetime.fromisoformat(timestamp),
            category=category,
            candidates=candidates
        ))

    return result


def _parse_storage_url(request: Request) -> tuple[str, str, str]:
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
# from .categories import CategoryModel
from .dao.endorsement_request_model import EndorsementRequestRequestModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/endorsement_requests", dependencies=[Depends(is_any_user)])
endorsers_router = APIRouter(prefix="/endorsers")


class EndorsementRequestModel(BaseModel):
    class Config:
        from_attributes = True

    id: Optional[int] = None
    endorsee_id: Optional[int] = None
    archive: Optional[str] = None
    subject_class: Optional[str] = None
    secret: Optional[str] = None
    flag_valid: Optional[bool] = None
    issued_when: Optional[datetime] = None
    point_value: int = 0

    flag_open: Optional[bool] = None
    flag_suspect: Optional[bool] = None
    endorsee_username: Optional[str] = None

    @staticmethod
    def base_select(db: Session):

        return db.query(
            EndorsementRequest.request_id.label("id"),
            EndorsementRequest.endorsee_id,
            EndorsementRequest.archive,
            EndorsementRequest.subject_class,
            EndorsementRequest.secret,
            EndorsementRequest.flag_valid,
            case(
                (EndorsementRequest.point_value == 0, True),
                else_=False
            ).label("flag_open"),
            EndorsementRequest.issued_when,
            EndorsementRequest.point_value,
            Demographic.flag_suspect.label("flag_suspect"),
            TapirNickname.nickname.label("endorsee_username")
            # Endorsee ID (single value)
            #TapirUser.user_id.label("endorsee"),
            # Endorsement ID (single value)
            #Endorsement.endorsement_id.label("endorsement"),
            # Audit ID (single value)
            #EndorsementRequestsAudit.session_id.label("audit")
        ).outerjoin(
            Demographic, Demographic.user_id == EndorsementRequest.endorsee_id
        ).outerjoin(
            TapirNickname, TapirNickname.user_id == EndorsementRequest.endorsee_id,
        )
    pass


@router.get('/')
async def list_endorsement_requests(
        response: Response,
        _sort: Optional[str] = Query("id", description="sort by"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: Optional[int] = Query(0, alias="_start"),
        _end: Optional[int] = Query(100, alias="_end"),
        id: Optional[List[int]] = Query(None, description="List of endorsement request IDs to filter by"),
        preset: Optional[str] = Query(None),
        start_date: Optional[date] = Query(None, description="Start date for filtering"),
        end_date: Optional[date] = Query(None, description="End date for filtering"),
        flag_valid: Optional[bool] = Query(None),
        positive: Optional[bool] = Query(None, description="positive point value"),
        suspected: Optional[bool] = Query(None, description="Suspected user"),
        secret_code: Optional[str] = Query(None, description="Endorsement request secret"),
        endorsee_id: Optional[str] = Query(None, description="Endorsement request endorsee ID"),
        endorsee_first_name: Optional[str] = Query(None, description="Endorsement request endorsee first_name"),
        endorsee_last_name: Optional[str] = Query(None, description="Endorsement request endorsee last_name"),
        endorsee_email: Optional[str] = Query(None, description="Endorsement request endorsee email"),
        endorsee_username: Optional[str] = Query(None, description="Endorsee username"),
        category: Optional[str] = Query(None, description="Endorsement category"),
        current_id: Optional[int] = Query(None, description="Current ID - index position - for navigation"),
        current_user: ArxivUserClaims = Depends(get_authn_user),
        session: Session = Depends(get_db),

    ) -> List[EndorsementRequestModel]:

    query = EndorsementRequestModel.base_select(session)

    order_columns = []

    if id is not None:
        query = query.filter(EndorsementRequest.request_id.in_(id))
        _start = 0
        _end = len(id)
        if not current_user.is_admin:
            query = query.filter(EndorsementRequest.endorsee_id == current_user.user_id)
        pass
    else:
        t0 = datetime.now()

        if preset is not None:
            matched = re.search(r"last_(\d+)_day", preset)
            if matched:
                t_begin = datetime_to_epoch(None, t0 - timedelta(days=int(matched.group(1))))
                t_end = datetime_to_epoch(None, t0)
                query = query.filter(EndorsementRequest.issued_when.between(t_begin, t_end))
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Invalid preset format")
        else:
            if start_date or end_date:
                t_begin = datetime_to_epoch(start_date, VERY_OLDE)
                t_end = datetime_to_epoch(end_date, date.today(), hour=23, minute=59, second=59)
                query = query.filter(EndorsementRequest.issued_when.between(t_begin, t_end))

        if secret_code is not None:
            query = query.filter(EndorsementRequest.secret == secret_code)

        if not (current_user.is_admin or current_user.is_mod):
            query = query.filter(EndorsementRequest.endorsee_id == current_user.user_id)

        if flag_valid is not None:
            query = query.filter(EndorsementRequest.flag_valid == flag_valid)

        if positive is not None:
            if positive:
                query = query.filter(EndorsementRequest.point_value > 0)
            else:
                query = query.filter(EndorsementRequest.point_value <= 0)

        if suspected is not None:
            query = query.filter(Demographic.flag_suspect == suspected)

        if endorsee_id is not None:
            query = query.filter(EndorsementRequest.endorsee_id == endorsee_id)

        if endorsee_first_name is not None or endorsee_last_name is not None or endorsee_email is not None:
            query = query.join(TapirUser, EndorsementRequest.endorsee_id == TapirUser.user_id)
            if endorsee_first_name is not None:
                query = query.filter(TapirUser.first_name.contains(endorsee_first_name))
            if endorsee_last_name is not None:
                query = query.filter(TapirUser.last_name.contains(endorsee_last_name))
            if endorsee_email is not None:
                query = query.filter(TapirUser.email.startswith(endorsee_email))

        if endorsee_username is not None:
            query = query.filter(TapirNickname.nickname.contains(endorsee_username))

        if category is not None:
            if "." in category:
                elems = category.split(".")
                archive = elems[0]
                subject_class = elems[1]
                query = query.filter(and_(EndorsementRequest.archive.startswith(archive),
                                          EndorsementRequest.subject_class.startswith(subject_class)))
            else:
                query = query.filter(EndorsementRequest.archive.startswith(category))
                pass
            pass

        if current_id is not None:
            # This is used to navigate
            _order = "ASC"
            _sort = "request_id"
            prev_req = (
                session.query(EndorsementRequest)
                .filter(EndorsementRequest.request_id < current_id)
                .order_by(EndorsementRequest.request_id.desc())
                .first()
            )

            next_req = (
                session.query(EndorsementRequest)
                .filter(EndorsementRequest.request_id > current_id)
                .order_by(EndorsementRequest.request_id.asc())
                .first()
            )
            prev_req_id = current_id
            next_req_id = current_id
            if prev_req:
                prev_req_id = prev_req.request_id
            if next_req:
                next_req_id = next_req.request_id
            query = query.filter(EndorsementRequest.request_id.between(prev_req_id, next_req_id))

        if _sort:
            keys = _sort.split(",")
            for key in keys:
                if key in ["id", "endorsementRequest_id"]:
                    key = "request_id"
                try:
                    order_column = getattr(EndorsementRequest, key)
                    order_columns.append(order_column)
                except AttributeError:
                    logger.error(f"Invalid sort key {key}")
                    # raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                    #                     detail="Invalid start or end index")


    for column in order_columns:
        if _order == "DESC":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    if _start is None:
        _start = 0

    if _end is None:
        _end = 100
    result = [EndorsementRequestModel.model_validate(item) for item in query.offset(_start).limit(_end - _start).all()]
    return result


@router.get('/{id:int}')
async def get_endorsement_request(id: int,
                                  current_user: ArxivUserClaims = Depends(get_authn_user),
                                  db: Session = Depends(get_db)) -> EndorsementRequestModel:
    item: EndorsementRequest = EndorsementRequestModel.base_select(db).filter(EndorsementRequest.request_id == id).one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Endorsement request with id {id} not found")

    if current_user.user_id != item.endorsee_id and (not (current_user.is_admin or current_user.is_mod)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to perform this action")
    return EndorsementRequestModel.model_validate(item)


@router.put('/{id:int}',
            dependencies=[Depends(is_any_user)],
            description='''
            Update an endorsement request.
            - flag_valid: set to 1 to activate the request, 0 to deactivate it.
            - flag_open: set to 1 to open the request, 0 to close it.
            - archive: set to the archive name to change the archive.
            - subject_class: set to the subject class to change the subject class.
            - endorsee_id: set to the endorsee ID to change the endorsee.
            - endorsee_username: set to the endorsee username to change the endorsee.'''
            )
async def update_endorsement_request(
        id: int,
        body: EndorsementRequestModel,
        current_user: ArxivUserClaims = Depends(get_authn_user),
        session: Session = Depends(get_db)) -> EndorsementRequestModel:

    item: EndorsementRequest | None = session.query(EndorsementRequest).filter(EndorsementRequest.request_id == id).one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Endorsement request with id {id} not found")

    if current_user.user_id != item.endorsee_id and (not (current_user.is_admin or current_user.is_mod)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to perform this action")

    #
    if body.flag_open is not None:
        if body.flag_open == False and item.point_value == 0:
            item.point_value = 10
        if body.flag_open == True and item.point_value == 10:
            item.point_value = 0

    if body.flag_valid is not None:
        item.flag_valid = body.flag_valid

    if current_user.is_admin:
        if body.archive is not None:
            item.archive = body.archive
            if body.subject_class is not None:
                item.subject_class = body.subject_class
            else:
                item.subject_class = ""
    # session.add(item)
    session.commit()
    session.refresh(item)  # Refresh the instance with the updated data
    updated = EndorsementRequestModel.base_select(session).filter(EndorsementRequest.request_id == id).one_or_none()
    return EndorsementRequestModel.model_validate(updated)


@router.post('/')
async def create_endorsement_request(
        respones: Response,
        body: EndorsementRequestRequestModel,
        current_user: ArxivUserClaims = Depends(get_authn_user),
        session: Session = Depends(get_db)) -> EndorsementRequestModel:
    endorsee_id = body.endorsee_id
    if endorsee_id is None:
        endorsee_id = current_user.user_id

    if endorsee_id != current_user.user_id and (not current_user.is_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to create endorsement for other users.")

    timestamp = datetime_to_epoch(None, datetime.now(UTC))
    er: EndorsementRequest
    for _ in range(10):
        code = endorsement_code()
        er = EndorsementRequest(
            endorsee_id=endorsee_id,
            archive=body.archive,
            subject_class=body.subject_class,
            secret=code,
            flag_valid=1,
            issued_when=timestamp,
            point_value=0)
        try:
            session.add(er)
            session.commit()
            session.refresh(er)
        except IntegrityError:
            pass
        except Exception as exc:
            logger.error(f"Creating Endorsement request failed", exc_info=exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unknown database opesation error " + str(exc)) from exc
        if er is not None:
            break
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Code creation failed")

    respones.status_code = status.HTTP_201_CREATED
    erm = EndorsementRequestModel.base_select(session).filter(EndorsementRequest.request_id == er.request_id).one_or_none()
    if erm is None:
        msg = f"Endorsement request {er.request_id} is created but not accessible"
        logger.warning(msg)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=msg)
    logger.info(f"Endorsement request {er.request_id} is created successfully.")
    return EndorsementRequestModel.model_validate(erm)


@router.delete('/{id:int}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_endorsement_request(
        id: int,
        current_user: ArxivUserClaims = Depends(get_authn_user),
        session: Session = Depends(get_db)) -> Response:
    if not current_user.is_admin:
        return Response(status_code=status.HTTP_403_FORBIDDEN)
    item: EndorsementRequest | None = session.query(EndorsementRequest).filter(EndorsementRequest.request_id == id).one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="User not found")

    session.delete(item)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get('/code')
async def get_endorsement_request_by_secret(
        secret: str = Query(None, description="Find an endorsement request by code"),
        current_user: ArxivUserClaims = Depends(get_authn_user),
        db: Session = Depends(get_db)
) -> EndorsementRequestModel:
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in first")
    item: EndorsementRequest = EndorsementRequestModel.base_select(db).filter(EndorsementRequest.secret == secret).one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Endorsement request with code {secret} not found")
    return EndorsementRequestModel.model_validate(item)


@endorsers_router.get('/eligible')
async def list_eligible_endorsers(
        response: Response,
        authn: ArxivUserClaims | ApiToken = Depends(get_authn),
        start_time: Optional[datetime] = Query(None, description="Paper count start time"),
        end_time: Optional[datetime] = Query(None, description="Paper count end time"),
        session: Session = Depends(get_db)
) -> List[EndorsementCandidates]:
    if isinstance(authn, ArxivUserClaims) and not authn.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to perform this action")
    data =  list_endorsement_candidates(session, start_date=start_time, end_date=end_time)
    response.headers['X-Total-Count'] = str(len(data))
    return data


@endorsers_router.post('/precomputed')
async def upload_cached_eligible_endorsers(
    request: Request,
    authn: ArxivUserClaims | ApiToken = Depends(get_authn),
    start_time: Optional[datetime] = Query(None, description="Paper count start time"),
    end_time: Optional[datetime] = Query(None, description="Paper count end time"),
    session: Session = Depends(get_db)
) -> dict:
    """
    Generate and upload fresh endorsement candidates to GCP bucket.

    Computes endorsement candidates in real-time and uploads to cloud storage
    for faster future access via the precomputed endpoint.
    """
    if isinstance(authn, ArxivUserClaims) and not authn.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to perform this action")

    # Generate fresh endorsement candidates
    logger.info("Generating fresh endorsement candidates for cache upload")
    data = list_endorsement_candidates(session, start_date=start_time, end_date=end_time)

    # Parse storage info from configuration
    scheme, location, path = _parse_storage_url(request)

    # Create in-memory SQLite database and populate with data
    conn = _create_endorsement_db()
    _populate_endorsement_db(conn, data)

    # Serialize database to gzipped bytes
    gzip_data = _serialize_db_to_gzip(conn)
    conn.close()

    try:
        if scheme == 'gs':
            logger.info(f"Uploading endorsement candidates to gs://{location}/{path}")

            # Initialize GCS client and upload data
            client = storage.Client()
            bucket = client.bucket(location)
            blob = bucket.blob(path)

            blob.upload_from_bytes(
                gzip_data,
                content_type='application/gzip'
            )

            logger.info(f"Successfully uploaded {len(data)} endorsement categories to GCS")

            # Invalidate old cache and register new cache
            _invalidate_db_cache()
            cache_key = _get_cache_key(request)
            _db_cache[cache_key] = conn

            return {
                "message": "Endorsement candidates uploaded successfully",
                "storage_type": "gcs",
                "bucket": location,
                "object": path,
                "categories_count": len(data),
                "upload_timestamp": datetime.now(UTC).isoformat()
            }

        elif scheme == 'file':
            logger.info(f"Uploading endorsement candidates to file://{path}")

            # Create directory if it doesn't exist
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write gzipped database to file
            file_path.write_bytes(gzip_data)

            logger.info(f"Successfully uploaded {len(data)} endorsement categories to file")

            # Invalidate old cache and register new cache
            _invalidate_db_cache()
            cache_key = _get_cache_key(request)
            _db_cache[cache_key] = conn

            return {
                "message": "Endorsement candidates uploaded successfully",
                "storage_type": "file",
                "file_path": path,
                "categories_count": len(data),
                "upload_timestamp": datetime.now(UTC).isoformat()
            }

    except storage.exceptions.Forbidden:
        logger.error(f"Access denied to GCS bucket {location}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to endorsement data storage"
        )
    except PermissionError as e:
        logger.error(f"Permission denied for file operation: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied for file storage"
        )
    except OSError as e:
        logger.error(f"File system error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File system error during upload"
        )
    except Exception as e:
        logger.error(f"Unexpected error uploading to {scheme} storage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload endorsement data to storage"
        )


def _read_cached_data(request: Request) -> sqlite3.Connection:
    """
    Helper function to read cached endorsement data from storage.

    Returns SQLite connection from either GCS or local file storage.
    """
    # Parse storage info from configuration
    scheme, location, path = _parse_storage_url(request)

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

        # Deserialize gzipped data to SQLite database
        conn = _deserialize_gzip_to_db(gzip_data)
        logger.debug(f"Successfully fetched cached endorsement candidates from {scheme} storage")
        return conn

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


@endorsers_router.get('/precomputed')
async def get_cached_eligible_endorsers(
        request: Request,
        response: Response,
        authn: ArxivUserClaims | ApiToken = Depends(get_authn),
) -> List[EndorsementCandidates]:
    """
    Fetch cached endorsement candidates from GCP bucket object.

    Returns precomputed endorsement candidates list from cloud storage,
    providing faster response than real-time computation.
    """
    if isinstance(authn, ArxivUserClaims) and not authn.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to perform this action")

    conn = _get_cached_db_connection(request)

    # Query all categories from database
    data = _query_all_categories_from_db(conn)
    response.headers['X-Total-Count'] = str(len(data))

    return data


@endorsers_router.get('/precomputed/category/{category:str}')
async def get_cached_eligible_endorsers_for_the_category(
        category: str,
        request: Request,
        response: Response,
        _sort: Optional[str] = Query("id", description="sort by"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: Optional[int] = Query(0, alias="_start"),
        _end: Optional[int] = Query(100, alias="_end"),
        authn: ArxivUserClaims | ApiToken = Depends(get_authn),
) -> List[EndorsementCandidate]:
    """
    Fetch cached endorsement candidates for a specific category.

    Returns precomputed endorsement candidates for the specified category
    from cloud storage, providing faster response than real-time computation.
    """
    if isinstance(authn, ArxivUserClaims) and not authn.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to perform this action")

    conn = _get_cached_db_connection(request)

    # Query specific category from database
    candidates = _query_category_from_db(conn, category)
    if candidates is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Endorsement category {category} not found")

    # Apply sorting
    reverse_order = _order.upper() == "DESC"
    if _sort == "id":
        candidates.sort(key=lambda x: x.id, reverse=reverse_order)
    elif _sort == "category":
        candidates.sort(key=lambda x: x.category, reverse=reverse_order)
    elif _sort == "document_count":
        candidates.sort(key=lambda x: x.document_count, reverse=reverse_order)
    elif _sort == "latest":
        candidates.sort(key=lambda x: x.latest, reverse=reverse_order)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid sort parameter: {_sort}")

    response_body = candidates[_start:_end]
    response.headers['X-Total-Count'] = str(len(candidates))
    return response_body


@endorsers_router.get('/precomputed/user')
async def get_cached_endorser_candidates(
        category: str,
        request: Request,
        response: Response,
        id: Optional[List[int]] = Query(None, description="List of user IDs to filter by"),
        _sort: Optional[str] = Query("id", description="sort by"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: Optional[int] = Query(0, alias="_start"),
        _end: Optional[int] = Query(100, alias="_end"),
        authn: ArxivUserClaims | ApiToken = Depends(get_authn),
) -> List[EndorsementCandidate]:
    """
    Fetch cached endorsement candidates for a specific category.

    Returns precomputed endorsement candidates for the specified category
    from cloud storage, providing faster response than real-time computation.
    """
    if isinstance(authn, ArxivUserClaims) and not authn.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to perform this action")

    conn = _get_cached_db_connection(request)

    # Query users from database with optional filtering
    candidates = _query_users_from_db(conn, category, id)
    if not candidates:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No candidates found for category {category}")

    # Apply sorting
    reverse_order = _order.upper() == "DESC"
    if _sort == "id":
        candidates.sort(key=lambda x: x.id, reverse=reverse_order)
    elif _sort == "category":
        candidates.sort(key=lambda x: x.category, reverse=reverse_order)
    elif _sort == "document_count":
        candidates.sort(key=lambda x: x.document_count, reverse=reverse_order)
    elif _sort == "latest":
        candidates.sort(key=lambda x: x.latest, reverse=reverse_order)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid sort parameter: {_sort}")

    response_body = candidates[_start:_end]
    response.headers['X-Total-Count'] = str(len(candidates))
    return response_body


