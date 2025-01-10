from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import insert, select
from flask import url_for
import pytest

from arxiv_db.models import OwnershipRequests, OwnershipRequestsAudit, Documents
from arxiv_db.models.associative_tables import t_arXiv_ownership_requests_papers, \
    t_arXiv_paper_owners

@pytest.fixture(scope='session')
def fake_ownerships(db):
     with Session(db) as session:
         oreq = OwnershipRequests(
             request_id=1,
             user_id=246231,
             workflow_status='pending')
         session.add(oreq)
         raudit = OwnershipRequestsAudit(
             request_id=1,
             session_id=0,
             remote_addr='127.0.0.1',
             tracking_cookie='127.0.0.1.1999999999999',
             date=datetime.now(),
             )
         session.add(raudit)

         doc = Documents(document_id = 1111, paper_id='2010.01111', title="bogus title",
                         submitter_email="bob@cornell.edu", authors="Smith, Bob",
                         submitter_id=246231, primary_subject_class='cs.IR')
         session.add(doc)

         stmt = insert(t_arXiv_ownership_requests_papers).values(request_id=1, document_id=1111)
         session.execute(stmt)

         oreq = OwnershipRequests(
             request_id=2,
             user_id=246231,
             workflow_status='rejected')
         session.add(oreq)
         raudit = OwnershipRequestsAudit(
             request_id=2,
             session_id=0,
             remote_addr='127.0.0.1',
             tracking_cookie='127.0.0.1.1999999999999',
             date=datetime.now(),
             )
         session.add(raudit)

         doc = Documents(document_id = 2222 , paper_id='2010.02222', title="bogus title",
                         submitter_email="bob@cornell.edu", authors="Smith, Bob",
                         submitter_id=246231, primary_subject_class='cs.IR')
         session.add(doc)

         stmt = insert(t_arXiv_ownership_requests_papers).values(request_id=1, document_id=2222)
         session.execute(stmt)

         oreq = OwnershipRequests(
             request_id=3,
             user_id=246231,
             workflow_status='accepted')
         session.add(oreq)
         raudit = OwnershipRequestsAudit(
             request_id=3,
             session_id=0,
             remote_addr='127.0.0.1',
             tracking_cookie='127.0.0.1.1999999999999',
             date=datetime.now(),
             )
         session.add(raudit)

         doc = Documents(document_id = 3333, paper_id='2010.03333', title="bogus title",
                         submitter_email="bob@cornell.edu", authors="Smith, Bob",
                         submitter_id=246231, primary_subject_class='cs.IR')
         session.add(doc)

         stmt = insert(t_arXiv_ownership_requests_papers).values(request_id=1, document_id=3333)
         session.execute(stmt)

         stmt = insert(t_arXiv_paper_owners).values(document_id=3333, user_id=246231, valid=1)
         # need: user/nick/etc request audit, documents, owned_papers,
         session.commit()
         return [1,2,3]

def test_get_reports(admin_client, fake_ownerships):
    resp = admin_client.get(url_for('ownership.pending'))
    assert resp.status_code == 200

    resp = admin_client.get(url_for('ownership.rejected'))
    assert resp.status_code == 200

    resp = admin_client.get(url_for('ownership.accepted'))
    assert resp.status_code == 200

def test_get_detailed_report(admin_client, fake_ownerships):
    resp = admin_client.get(url_for('ownership.display', ownership_id = fake_ownerships[0]))
    assert resp.status_code == 200

    resp = admin_client.get(url_for('ownership.display', ownership_id = fake_ownerships[1]))
    assert resp.status_code == 200

    resp = admin_client.get(url_for('ownership.display', ownership_id = fake_ownerships[2]))
    assert resp.status_code == 200

    resp = admin_client.get(url_for('ownership.display', ownership_id = 0))
    assert resp.status_code == 404

def test_edits(admin_client, fake_ownerships, db):
    with Session(db) as session:
        oreq = session.execute(select(OwnershipRequests).where(OwnershipRequests.user_id==246231,OwnershipRequests.workflow_status=='pending')).scalar()
        request_id = oreq.request_id
        assert oreq
        resp = admin_client.post(url_for('ownership.display', ownership_id=oreq.request_id),
                            data = dict(request_id=request_id,
                                        make_owner='make owner',
                                        approve_1111=1,
                                        is_author=1)
                            )
        assert resp.status_code == 200
        session.expire(oreq)
        assert oreq and oreq.workflow_status == 'accepted'

        resp = admin_client.post(url_for('ownership.display', ownership_id=oreq.request_id),
                            data = dict(request_id=request_id,
                                        revisit='revisit',
                                        approve_1111=1,
                                        is_author=1)
                            )
        assert resp.status_code == 200
        session.expire(oreq)
        assert oreq and oreq.workflow_status == 'pending'

        resp = admin_client.post(url_for('ownership.display', ownership_id=oreq.request_id),
                            data = dict(request_id=request_id,
                                        reject='reject',
                                        approve_1111=1,
                                        is_author=1)
                            )
        assert resp.status_code == 200
        session.expire(oreq)
        assert oreq and oreq.workflow_status == 'rejected'


        resp = admin_client.post(url_for('ownership.display', ownership_id=oreq.request_id),
                            data = dict(request_id=request_id,
                                        no_action='no defined submit actions for form')
                            )
        assert resp.status_code == 400

        resp = admin_client.post(url_for('ownership.display', ownership_id=0),
                                 data = dict(request_id=request_id,
                                             make_owner='1')
                                 )
        assert resp.status_code == 404
