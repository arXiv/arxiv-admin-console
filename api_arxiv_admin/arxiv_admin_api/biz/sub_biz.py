

def create_submission(db_session: Session,
                      user: UserModel,
                      document: DocumentModel,
                      submit_type: str,
                      hostname: str,
                      host_ip: str):
    """
    Create a new submission from a document.

    Parameters:
        user: user object with id, name, email
        document: document object with .id, .paper_id, .current_version
        submit_type: submission type (e.g. 'jref')
        request: request object with .hostname and .client (addr)
        db_session: SQLAlchemy session
        flash: function to flash a message
        redirect: function to issue redirect
        make_sub_cats: function to create submission categories
    Returns:
        Submission object
    """
    metadata = document.current_version(db_session)
    if not metadata:
        return None

    columns = Submission.__table__.columns
    fields = {key: value for key, value in metadata.model_dump().items() if key in columns}

    submission_data = {
        "type": submit_type,
        "submitter_id": user.id,
        "document_id": document.id,
        "doc_paper_id": document.paper_id,
        "remote_host": hostname,
        "remote_addr": host_ip,
        "submitter_name": user.name,
        "submitter_email": user.email,
    }
    fields.update(submission_data)
    submission = Submission(**submission_data)
    db_session.add(submission)
    db_session.commit()

    make_sub_cats(submission)
    return submission


def make_sub_cats(db_session: Session, submission, document) -> None:
    """
    Create submission categories based on document categories.

    This function creates submission category entries for each document category,
    copying the category information and marking them as published.

    Parameters:
        submission: The submission object to associate categories with
        document: The document object containing categories to copy from
    """

    # Get all categories for the document
    categories = db_session.query(DocumentCategory).filter(
        DocumentCategory.document_id == document.id
    ).all()

    # Create submission categories for each document category
    for cat in categories:
        # Create a dictionary of the category data
        cat_data = {
            # Copy all attributes from the document category except document_id
            key: getattr(cat, key) for key in cat.__table__.columns.keys()
            if key != 'document_id'
        }

        # Add submission-specific data
        cat_data.update({
            'submission_id': submission.id,
            'is_published': 1
        })

        # Create and add the new submission category
        sub_cat = SubmissionCategory(**cat_data)
        db_session.add(sub_cat)

    # Commit the changes
    db_session.commit()



def create_jref(session: Session, user_id: int, doc_id: int):

    if user.ext.veto_status == 'no-replace':
        request.session["message"] = "Not authorized"
        return RedirectResponse(url="/user")

    # Create submission of type jref
    submission = await create_submission(user=user, document=document, submit_type='jref')

    submission.type = 'jref'
    await submission.save()

    await admin_log(actor=user.username, action="jref", extra="")

    return RedirectResponse(url=f"/submit/jref/{submission.id}")
