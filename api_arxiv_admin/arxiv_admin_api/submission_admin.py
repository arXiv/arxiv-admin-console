"""
This is converted from Tapir PHP as a reference.
"""

from fastapi import FastAPI, HTTPException, Depends, Query, Path, Form
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import os
from arxiv.db.models import Submission, SubmissionCategory, AdminLog


# Pydantic Models
class SubmissionStatus(str, Enum):
    WORKING = "0"
    SUBMITTED = "1"
    ON_HOLD = "2"
    NEXT = "4"
    STUCK = "8"
    REMOVED = "9"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class SortBy(str, Enum):
    ID = "id"
    TYPE = "type"
    STATUS = "status"
    CATEGORY = "cat"
    SUBMITTER = "submitter"
    TITLE = "title"
    OK = "ok"
    SUBMIT_TIME = "submit_time"


class SubmissionListResponse(BaseModel):
    submissions: List[Dict[str, Any]]
    total_count: int
    counts: Dict[str, int]
    list_info: Dict[str, Any]


class CommentRequest(BaseModel):
    comment: str = Field(min_length=6, description="Comment must be more than 5 characters")
    notify_mods: bool = False


class HoldRequest(CommentRequest):
    pass


class ReleaseRequest(CommentRequest):
    lock_submission: bool = False


class RemoveRequest(CommentRequest):
    pass


class UnsubmitRequest(CommentRequest):
    hold_on_resubmit: bool = False


class ResubmitRequest(CommentRequest):
    hold_on_resubmit: bool = False


class LockToggleRequest(CommentRequest):
    pass


class ProposalRequest(BaseModel):
    primary_proposals: List[str] = []
    secondary_proposals: List[str] = []
    comment: str = Field(min_length=6)
    put_on_hold: bool = False


# FastAPI App
app = FastAPI(title="ArXiv Admin Queue API", version="1.0.0")


# Dependency for database session
def get_db() -> Session:
    # Replace with your actual database session dependency
    pass


def get_current_user():
    # Replace with your actual authentication dependency
    pass


# Helper Functions
def get_sort_column(sort_by: SortBy) -> str:
    """Map UI sort options to database columns"""
    mapping = {
        SortBy.ID: "submission.submission_id",
        SortBy.TYPE: "submission.type",
        SortBy.STATUS: "submission.status",
        SortBy.CATEGORY: "submission_primary_category.category",
        SortBy.SUBMITTER: "submission.submitter_name",
        SortBy.TITLE: "submission.title",
        SortBy.OK: "submission.is_ok",
        SortBy.SUBMIT_TIME: "submission.submit_time"
    }
    return mapping[sort_by]


def build_base_query(db: Session, status_filter: Dict = None):
    """Build base submission query with joins"""
    query = db.query(Submission).join(SubmissionCategory, isouter=True)

    if status_filter:
        query = query.filter(Submission.status.in_(status_filter.get('status', [])))

    return query


def get_adminq(db: Session, options: Dict) -> Any:
    """Generalized function to get admin queue submissions"""

    # Base query setup
    query = build_base_query(db)

    # Handle different list types
    if 'status' in options:
        if isinstance(options['status'], list):
            query = query.filter(Submission.status.in_(options['status']))
        else:
            query = query.filter(Submission.status == options['status'])

    if 'type' in options:
        if options['type'].get('!='):
            query = query.filter(Submission.type != options['type']['!='])
        elif options['type'].get('='):
            query = query.filter(Submission.type == options['type']['='])

    # Handle special list types
    if options.get('show_ninja'):
        query = build_ninja_query(db, query, options)
    elif options.get('show_covid'):
        query = build_covid_query(db, query, options)
    elif options.get('stuck_list'):
        one_hour_ago = datetime.now() - timedelta(hours=1)
        query = query.filter(Submission.submit_time < one_hour_ago)

    # Sorting
    sort_by = options.get('sort_by', 'id')
    order = options.get('order', 'asc')
    sort_column = get_sort_column(SortBy(sort_by))

    if order == 'desc':
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    return query


def build_ninja_query(db: Session, base_query, options: Dict):
    """Build ninja list specific query logic"""
    # This would implement the complex ninja list logic from lines 411-472
    # For brevity, showing simplified version
    earliest_comment_date = get_last_freeze_time()  # Implement this helper

    ninja_conditions = or_(
        # Flagged users in submitted status
        and_(
            Submission.flag_suspect == 1,
            Submission.status == 1
        ),
        # Held submissions with comments since freeze
        and_(
            Submission.status == 2,
            AdminLog.command == 'Hold',
            AdminLog.created > earliest_comment_date
        ),
        # Add other ninja conditions...
    )

    return base_query.filter(ninja_conditions)


def build_covid_query(db: Session, base_query, options: Dict):
    """Build COVID list specific query logic"""
    covid_conditions = or_(
        Submission.title.ilike('%covid%'),
        Submission.title.ilike('%coronavirus%'),
        Submission.title.ilike('%SARS-CoV-2%'),
        Submission.abstract.ilike('%covid%'),
        Submission.abstract.ilike('%coronavirus%'),
        Submission.abstract.ilike('%SARS-CoV-2%'),
        and_(
            AdminLog.logtext.ilike('%Rimi%'),
            AdminLog.command == 'admin comment'
        )
    )

    return base_query.filter(covid_conditions)


# API Endpoints

@app.get("/admin/queue", response_model=SubmissionListResponse)
async def get_current_submissions(
        sort_by: Optional[SortBy] = Query(SortBy.ID),
        order: Optional[SortOrder] = Query(SortOrder.ASC),
        db: Session = Depends(get_db)
):
    """Get current submitted list (status=1, type!=cross)"""

    options = {
        'status': 1,
        'type': {'!=': 'cross'},
        'sort_by': sort_by.value,
        'order': order.value
    }

    query = get_adminq(db, options)
    submissions = query.all()

    return build_list_response(submissions, "Submitted List", "current")


@app.get("/admin/queue/hold", response_model=SubmissionListResponse)
async def get_hold_list(
        sort_by: Optional[SortBy] = Query(SortBy.ID),
        order: Optional[SortOrder] = Query(SortOrder.ASC),
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """Get submissions on hold (status=2)"""

    options = {
        'status': 2,
        'sort_by': sort_by.value,
        'order': order.value
    }

    query = get_adminq(db, options)
    submissions = query.all()

    return build_list_response(submissions, "Hold List", "hold")


@app.get("/admin/queue/cross", response_model=SubmissionListResponse)
async def get_cross_list(
        sort_by: Optional[SortBy] = Query(SortBy.ID),
        order: Optional[SortOrder] = Query(SortOrder.ASC),
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """Get cross-listed submissions (status=1, type=cross)"""

    options = {
        'status': 1,
        'type': {'=': 'cross'},
        'sort_by': sort_by.value,
        'order': order.value
    }

    query = get_adminq(db, options)
    submissions = query.all()

    return build_list_response(submissions, "Cross List", "cross")


@app.get("/admin/queue/next", response_model=SubmissionListResponse)
async def get_next_list(
        sort_by: Optional[SortBy] = Query(SortBy.ID),
        order: Optional[SortOrder] = Query(SortOrder.ASC),
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """Get submissions scheduled for next announcement (status=4)"""

    options = {
        'status': 4,
        'type': {'!=': 'cross'},
        'sort_by': sort_by.value,
        'order': order.value
    }

    query = get_adminq(db, options)
    submissions = query.all()

    return build_list_response(submissions, "Next List", "next")


@app.get("/admin/queue/working", response_model=SubmissionListResponse)
async def get_working_list(
        sort_by: Optional[SortBy] = Query(SortBy.ID),
        order: Optional[SortOrder] = Query(SortOrder.ASC),
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """Get working submissions (status=0)"""

    options = {
        'status': 0,
        'sort_by': sort_by.value,
        'order': order.value
    }

    query = get_adminq(db, options)
    submissions = query.all()

    return build_list_response(submissions, "Working List", "working")


@app.get("/admin/queue/removed", response_model=SubmissionListResponse)
async def get_removed_list(
        sort_by: Optional[SortBy] = Query(SortBy.ID),
        order: Optional[SortOrder] = Query(SortOrder.ASC),
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """Get removed submissions (status=9)"""

    options = {
        'status': 9,
        'sort_by': sort_by.value,
        'order': order.value
    }

    query = get_adminq(db, options)
    submissions = query.all()

    return build_list_response(submissions, "Removed List", "removed")


@app.get("/admin/queue/ninja", response_model=SubmissionListResponse)
async def get_ninja_list(
        sort_by: Optional[SortBy] = Query(SortBy.ID),
        order: Optional[SortOrder] = Query(SortOrder.ASC),
        go_back: Optional[int] = Query(0, ge=0, le=250),
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """Get ninja list - flagged submissions and holds since freeze"""

    options = {
        'status': 1,
        'sort_by': sort_by.value,
        'order': order.value,
        'show_ninja': True,
        'go_back': go_back
    }

    query = get_adminq(db, options)
    submissions = query.all()

    return build_list_response(submissions, "Ninja List", "ninja")


@app.get("/admin/queue/covid", response_model=SubmissionListResponse)
async def get_covid_list(
        sort_by: Optional[SortBy] = Query(SortBy.ID),
        order: Optional[SortOrder] = Query(SortOrder.ASC),
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """Get COVID-19 related submissions"""

    options = {
        'status': [1, 2, 4],
        'sort_by': sort_by.value,
        'order': order.value,
        'show_covid': True
    }

    query = get_adminq(db, options)
    submissions = query.all()

    return build_list_response(submissions, "COVID-19 List", "covid")


@app.get("/admin/queue/stuck", response_model=SubmissionListResponse)
async def get_stuck_list(
        sort_by: Optional[SortBy] = Query(SortBy.ID),
        order: Optional[SortOrder] = Query(SortOrder.ASC),
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """Get submissions stuck in processing (status=8, >1 hour old)"""

    options = {
        'status': 8,
        'sort_by': sort_by.value,
        'order': order.value,
        'stuck_list': True
    }

    query = get_adminq(db, options)
    submissions = query.all()

    return build_list_response(submissions, "Stuck in Processing List", "stuck")


# Individual Submission Actions

@app.get("/admin/queue/{submission_id}")
async def get_submission_details(
        submission_id: int = Path(...),
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """Get detailed view of a specific submission"""

    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if submission.is_locked:
        return {"message": "This submission is currently locked", "submission": submission}

    return {"submission": submission, "comments": submission.get_comments()}


@app.post("/admin/queue/{submission_id}/hold")
async def set_hold(
        submission_id: int = Path(...),
        request: HoldRequest = ...,
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """Put submission on hold"""

    submission = get_submission_or_404(db, submission_id)
    check_not_locked(submission)

    if submission.status not in [1, 4]:  # submitted or next
        raise HTTPException(status_code=400, detail="Not a valid status for hold")

    old_status = submission.admin_status_str
    submission.set_status('on hold')  # status = 2

    # Log the action
    log_admin_action(
        db, user, submission_id, "admin comment",
        f"Hold: {request.comment}", request.notify_mods
    )
    log_admin_action(
        db, user, submission_id, "Hold",
        f"Status changed from '{old_status}' to '{submission.admin_status_str}'",
        request.notify_mods
    )

    db.commit()
    return {"message": "Submission placed on hold", "status": submission.admin_status_str}


@app.post("/admin/queue/{submission_id}/release")
async def release_from_hold(
        submission_id: int = Path(...),
        request: ReleaseRequest = ...,
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """Release submission from hold"""

    submission = get_submission_or_404(db, submission_id)
    check_not_locked(submission)

    old_status = submission.admin_status_str
    if old_status != 'on hold':
        raise HTTPException(
            status_code=400,
            detail=f"Cannot release a paper that is not on hold (current status is {old_status})"
        )

    if not submission.primary_category:
        raise HTTPException(
            status_code=400,
            detail="Cannot release a paper that has no primary category"
        )

    # Handle auto_hold logic
    release_type = "Release"
    if submission.auto_hold:
        release_type = "Auto Hold Release (Initial email to moderators)"
        # Handle classifier checks, oversize papers, etc.
        handle_auto_hold_release(submission)
        submission.auto_hold = False

    # Do the actual release
    submission.proper_release_from_hold()

    # Handle submission locking if requested
    if request.lock_submission and user.can_lock_submissions and not submission.is_locked:
        submission.is_locked = True
        log_admin_action(db, user, submission_id, "Lock", "Locked submission")

    # Log the actions
    log_admin_action(
        db, user, submission_id, "admin comment",
        f"{release_type}: {request.comment}", request.notify_mods
    )
    log_admin_action(
        db, user, submission_id, release_type,
        f"Status changed from '{old_status}' to '{submission.admin_status_str}'",
        request.notify_mods
    )

    db.commit()
    return {"message": "Submission released from hold", "status": submission.admin_status_str}


@app.post("/admin/queue/{submission_id}/remove")
async def remove_submission(
        submission_id: int = Path(...),
        request: RemoveRequest = ...,
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """Remove submission or unremove if already removed"""

    submission = get_submission_or_404(db, submission_id)
    check_not_locked(submission)

    old_status = submission.admin_status_str

    if submission.status > 19:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot remove a deleted paper (current status is {old_status})"
        )

    # Toggle between removed and hold
    if submission.status == 9:  # removed
        submission.status = 2  # hold
        message = "Status changed to 'hold'"
        action = "Unremove"
    else:
        submission.status = 9  # removed
        message = "Status changed to 'removed'"
        action = "Remove"

    # Log the actions
    log_admin_action(
        db, user, submission_id, "admin comment",
        f"{action}: {request.comment}", request.notify_mods
    )
    log_admin_action(
        db, user, submission_id, "Remove",
        f"Status changed from '{old_status}' to '{submission.admin_status_str}'",
        request.notify_mods
    )

    db.commit()
    return {"message": message, "status": submission.admin_status_str}


@app.post("/admin/queue/{submission_id}/unsubmit")
async def unsubmit_submission(
        submission_id: int = Path(...),
        request: UnsubmitRequest = ...,
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """Change submission status back to working (unsubmit)"""

    submission = get_submission_or_404(db, submission_id)
    check_not_locked(submission)

    old_status = submission.admin_status_str
    valid_statuses = ['submitted', 'next', 'on hold', 'processing(submitting)']

    if old_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot unsubmit a paper that is not submitted (current status is {old_status})"
        )

    # Handle sticky status for resubmission
    sticky_msg = ''
    if request.hold_on_resubmit:
        submission.sticky_status = 2
        sticky_msg = ' and will return to hold if resubmitted'
    else:
        submission.sticky_status = None

    submission.status = 0  # working

    # Log the actions
    log_admin_action(
        db, user, submission_id, "admin comment",
        f"Unsubmit: {request.comment}", request.notify_mods
    )
    log_admin_action(
        db, user, submission_id, "Unsubmit",
        f"Status changed from '{old_status}' to '{submission.admin_status_str}'{sticky_msg}",
        request.notify_mods
    )

    db.commit()

    # Generate email link for admin convenience
    email_link = f"mailto:{submission.submitter_email}?subject=arXiv {submission.sub_id} requires correction&body=\nhttps://arxiv.org/submit/{submission.submission_id}/addfiles"

    return {
        "message": "Submission unsubmitted",
        "status": submission.admin_status_str,
        "email_link": email_link
    }


@app.post("/admin/queue/{submission_id}/resubmit")
async def resubmit_submission(
        submission_id: int = Path(...),
        request: ResubmitRequest = ...,
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """Resubmit a working submission"""

    submission = get_submission_or_404(db, submission_id)
    check_not_locked(submission)

    old_status = submission.admin_status_str
    valid_statuses = ['working', 'processing(submitting)']

    if old_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot resubmit a paper that is not in working status (current status is {old_status})"
        )

    # Determine new status
    if not submission.primary_category or request.hold_on_resubmit:
        submission.sticky_status = None
        submission.set_status('on hold')  # status = 2
    else:
        submission.sticky_status = None
        submission.set_status('submitted')  # status = 1

    # Log the actions
    log_admin_action(
        db, user, submission_id, "admin comment",
        f"Resubmit: {request.comment}", request.notify_mods
    )
    log_admin_action(
        db, user, submission_id, "Resubmit",
        f"Status changed from '{old_status}' to '{submission.admin_status_str}'",
        request.notify_mods
    )

    db.commit()
    return {"message": "Submission resubmitted", "status": submission.admin_status_str}


@app.post("/admin/queue/{submission_id}/toggle_lock")
async def toggle_lock(
        submission_id: int = Path(...),
        request: LockToggleRequest = ...,
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """Toggle submission lock status"""

    if not user.can_lock_submissions:
        raise HTTPException(status_code=403, detail="Not authorized")

    submission = get_submission_or_404(db, submission_id)

    if submission.status > 4:
        raise HTTPException(status_code=400, detail="Not a valid status for lock")

    will_lock = not submission.is_locked
    action = 'Lock' if will_lock else 'Unlock'
    submission.is_locked = will_lock

    # Log the actions
    log_admin_action(
        db, user, submission_id, "admin comment",
        f"{action}: {request.comment}"
    )
    log_admin_action(
        db, user, submission_id, action,
        f"{action}ed submission"
    )

    db.commit()
    return {"message": f"Submission {action.lower()}ed", "is_locked": submission.is_locked}


@app.post("/admin/queue/{submission_id}/comment")
async def add_comment(
        submission_id: int = Path(...),
        request: CommentRequest = ...,
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """Add a comment to submission"""

    submission = get_submission_or_404(db, submission_id)

    log_admin_action(
        db, user, submission_id, "admin comment",
        request.comment, request.notify_mods
    )

    db.commit()
    return {"message": "Comment added"}


@app.get("/admin/queue/{submission_id}/log")
async def get_submission_log(
        submission_id: int = Path(...),
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """Get admin log entries for submission"""

    submission = get_submission_or_404(db, submission_id)

    log_entries = db.query(AdminLog).filter(
        AdminLog.submission_id == submission_id
    ).order_by(AdminLog.created).all()

    return {"log_entries": log_entries}


@app.get("/admin/queue/{submission_id}/00README")
async def download_readme(
        submission_id: int = Path(...),
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """Download 00README.json file for submission"""

    submission = get_submission_or_404(db, submission_id)

    readme_path = f"{submission.files.sub_src_dir}/00README.json"

    if not os.path.exists(readme_path):
        raise HTTPException(status_code=404, detail="00README.json not found")

    timestamp = datetime.now().strftime('%Y%m%d-%H%M')
    filename = f'submission_{submission.id}-{timestamp}.00README.json'

    return FileResponse(
        readme_path,
        media_type='application/json',
        filename=filename
    )


# Helper Functions

def get_submission_or_404(db: Session, submission_id: int):
    """Get submission or raise 404"""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission


def check_not_locked(submission):
    """Check if submission is locked"""
    if submission.is_locked:
        raise HTTPException(status_code=400, detail="This submission is currently locked")


def log_admin_action(db: Session, user, submission_id: int, command: str, logtext: str, notify: bool = False):
    """Log admin action"""
    # Implementation depends on your AdminLog model
    pass


def handle_auto_hold_release(submission):
    """Handle auto hold release logic"""
    # Implementation depends on classifier and auto hold logic
    pass


def build_list_response(submissions: List, list_name: str, list_alias: str) -> SubmissionListResponse:
    """Build standardized list response"""

    # Calculate counts by type
    type_counts = {}
    for submission in submissions:
        submission_type = submission.type
        type_counts[submission_type] = type_counts.get(submission_type, 0) + 1

    ok_count = sum(1 for s in submissions if s.is_ok)

    return SubmissionListResponse(
        submissions=[submission_to_dict(s) for s in submissions],
        total_count=len(submissions),
        counts={
            'new': type_counts.get('new', 0),
            'rep': type_counts.get('rep', 0),
            'jref': type_counts.get('jref', 0),
            'wdr': type_counts.get('wdr', 0),
            'cross': type_counts.get('cross', 0),
            'ok': ok_count
        },
        list_info={
            'name': list_name,
            'alias': list_alias
        }
    )


def submission_to_dict(submission) -> Dict[str, Any]:
    """Convert submission object to dictionary"""
    return {
        'id': submission.id,
        'submission_id': submission.submission_id,
        'type': submission.type,
        'status': submission.status,
        'title': submission.title,
        'submitter_name': submission.submitter_name,
        'submit_time': submission.submit_time.isoformat() if submission.submit_time else None,
        'is_ok': submission.is_ok,
        'primary_category': submission.primary_category,
        'is_locked': submission.is_locked,
        # Add other fields as needed
    }


def get_last_freeze_time():
    """Get the last freeze time for ninja list"""
    # Implementation depends on your freeze time logic
    pass