List Characteristics:

  Status Code:

  - Status = 4 (from both implementations)
  - In current enum: SubmissionStatus.NEXT = "4"
  - In status list: SubmissionStatusModel(id=4, name="Next", group="current")

  Purpose:

  - Submissions scheduled for next announcement: These are papers that have been processed and approved, but are waiting for the next daily announcement
  cycle
  - Not cross-listed: The filter excludes type='cross' submissions (cross-listed papers have their own queue)

  Workflow Position:

  The typical submission workflow is:
  1. Working (status=0) → Author preparing
  2. Submitted (status=1) → Submitted for review
  3. On Hold (status=2) → Admin review needed
  4. Next (status=4) → Approved, waiting for announcement
  5. Processing (status=5-8) → Being published
  6. Published (status=7) → Live on arXiv

  Current Implementation Access:

  In the current submissions.py, the Next List can be accessed using:
  GET /submissions?submission_status=NEXT
  or
  GET /submissions?submission_status=4

  However, to match the old system exactly, you'd also need to exclude cross-listed submissions:
  GET /submissions?submission_status=NEXT&type=new,rep,jref,wdr
  (excluding "cross" type)

  Summary:

  The Next List is the queue of submissions that have been approved by administrators and are scheduled for the next daily announcement. They're essentially
   "ready to publish" but waiting for the announcement cycle. This is different from:

  - Hold List (status=2): Needs admin review
  - Submitted List (status=1): Recently submitted, under review
  - Next List (status=4): Approved, waiting to be announced

  It represents the final stage before papers go live on arXiv.

> What is "Cross List"?

● Looking at the old implementation in submission_admin.py, the "Cross List" is a specific administrative queue for cross-listed submissions.

  Cross List Definition:

  From submission_admin.py lines 250-269:

  @app.get("/admin/queue/cross", response_model=SubmissionListResponse)
  async def get_cross_list(...):
      """Get cross-listed submissions (status=1, type=cross)"""

      options = {
          'status': 1,           # Status = 1 (Submitted)
          'type': {'=': 'cross'}, # Type must be 'cross'
          'sort_by': sort_by.value,
          'order': order.value
      }

  Cross List Characteristics:

  Criteria:

  - Status = 1 (Submitted)
  - Type = 'cross' (Cross-listed submission type)

  What is Cross-Listing?

  Cross-listing in arXiv means a paper is listed in multiple subject categories. For example:
  - A machine learning paper about physics might be cross-listed in both cs.ML (Computer Science - Machine Learning) and physics.comp-ph (Physics -
  Computational Physics)
  - The paper has a primary category where it "lives"
  - And secondary categories where it's also listed for discoverability

  Cross List vs Regular Submissions:

  Regular Submission Flow:
  1. Submitted (status=1) → Review → Next (status=4) → Published

  Cross-Listed Submission Flow:
  1. Submitted (status=1, type='cross') → Special cross-list review → Next → Published

  Why Separate Queue?

  Cross-listed submissions need different administrative handling:
  1. Category validation: Ensure the cross-listing is appropriate
  2. Moderation: Different moderators for different subject areas
  3. Announcement coordination: Cross-listed papers appear in multiple daily announcements

  Current Implementation Access:

  In the current submissions.py, the Cross List can be accessed using:
  GET /submissions?submission_status=SUBMITTED&type=cross
  or
  GET /submissions?submission_status=1&type=cross

  Relationship to Other Lists:

  Regular Submitted List (from old implementation):

  options = {
      'status': 1,
      'type': {'!=': 'cross'},  # Excludes cross-listed
  }

  Cross List:

  options = {
      'status': 1,
      'type': {'=': 'cross'},   # Only cross-listed
  }

  So the "Submitted" queue is split into:
  - Regular submissions: status=1, type≠'cross'
  - Cross-listed submissions: status=1, type='cross'

  Summary:

  The Cross List is a specialized administrative queue for cross-listed submissions that:
  - Are in submitted status (status=1)
  - Have submission type = 'cross'
  - Need special handling because they appear in multiple subject categories
  - Require coordination across different subject area moderators
  - Have different announcement and publication workflows

  This separation allows administrators to handle cross-listed papers with the special attention they require for multi-category coordination.
