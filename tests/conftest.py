"""Special pytest fixture configuration file.

This file automatically provides all fixtures defined in it to all
pytest tests in this directory and sub directories.

See https://docs.pytest.org/en/6.2.x/fixture.html#conftest-py-sharing-fixtures-across-multiple-files

pytest fixtures are used to initialize object for test functions. The
fixtures run for a function are based on the name of the argument to
the test function.

Scope = 'session' means that the fixture will be run onec and reused
for the whole test run session. The default scope is 'function' which
means that the fixture will be re-run for each test function.

"""
import os
import pytest

from pathlib import Path, PurePath
import hashlib
from base64 import b64encode
import pathlib

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from arxiv_db import test_load_db_file, models

from admin_webapp.factory import create_web_app

DB_FILE = "./pytest.db"


SQL_DATA_FILE = './tests/data/data.sql'

DELETE_DB_FILE_ON_EXIT = True


def parse_cookies(cookie_data):
    """This should be moved to a library function in arxiv-auth for reuse in tests."""
    cookies = {}
    for cdata in cookie_data:
        parts = cdata.split('; ')
        data = parts[0]
        key, value = data[:data.index('=')], data[data.index('=') + 1:]
        extra = {
            part[:part.index('=')]: part[part.index('=') + 1:]
            for part in parts[1:] if '=' in part
        }
        cookies[key] = dict(value=value, **extra)
    return cookies


@pytest.fixture(scope='session')
def engine():
    db_file = pathlib.Path(DB_FILE).resolve()
    try:
        print(f"Created db at {db_file}")
        connect_args = {"check_same_thread": False}
        engine = create_engine(f"sqlite:///{db_file}",
                               connect_args=connect_args)
        yield engine
    finally: # cleanup
        if DELETE_DB_FILE_ON_EXIT:
            db_file.unlink(missing_ok=True)
            print(f"Deleted {db_file} at end of test. "
                  "Set DELETE_DB_FILE_ON_EXIT to control.")

@pytest.fixture(scope='session')
def db(engine):
    """Create and load db tables."""
    print("Making tables...")
    from arxiv_db.tables import arxiv_tables
    arxiv_tables.metadata.create_all(bind=engine)
    print("Done making tables.")
    test_load_db_file(engine, SQL_DATA_FILE)
    yield engine

@pytest.fixture(scope='session')
def admin_user(db):
    with Session(db) as session:
        admin_exits = select(models.TapirUsers).where(models.TapirUsers.email == 'testadmin@example.con')
        admin = session.scalar(admin_exits)
        if admin:
            return admin

        salt = b'fdoo'
        password = b'thepassword'
        hashed = hashlib.sha1(salt + b'-' + password).digest()
        encrypted = b64encode(salt + hashed)

        # We have a good old-fashioned user.
        db_user = models.TapirUsersPassword(
            user_id=59999,
            first_name='testadmin',
            last_name='admin',
            suffix_name='',
            email='testadmin@example.com',
            policy_class=2,
            flag_edit_users=1,
            flag_email_verified=1,
            flag_edit_system=0,
            flag_approved=1,
            flag_deleted=0,
            flag_banned=0,
            tracking_cookie='foocookie',
            password_storage=2,
            password_enc=encrypted
        )

        db_nick=models.TapirNicknames(
            user_id = db_user.user_id,
            nickname='foouser',
            user_seq=1,
            flag_valid=1,
            role=0,
            policy=0,
            flag_primary=1
        )
        db_demo = models.Demographics(
            user_id=db_user.user_id,
            country='US',
            affiliation='Cornell U.',
            url='http://example.com/bogus',
            original_subject_classes='cs.OH',
            subject_class = 'OH',
            archive ='cs',
            type=5,
        )


        session.add(db_user)
        session.add(db_nick)
        session.add(db_demo)

        session.commit()
        rd=dict(email=db_user.email, password_cleartext=password)
        return rd

@pytest.fixture(scope='session')
def secret():
    return f'bogus secret set in {__file__}'

@pytest.fixture(scope='session')
def app(db, secret, admin_user):
    """Flask client"""
    app = create_web_app()
    #app.config['CLASSIC_COOKIE_NAME'] = 'foo_tapir_session'
    #app.config['AUTH_SESSION_COOKIE_NAME'] = 'baz_session'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['AUTH_SESSION_COOKIE_SECURE'] = '0'
    app.config['JWT_SECRET'] = "jwt_" + secret
    app.config['CLASSIC_SESSION_HASH'] = "classic_hash_" +secret
    app.config['CLASSIC_DATABASE_URI'] = db.url
    app.config['SQLALCHEMY_DATABASE_URI'] = db.url
    app.config['REDIS_FAKE'] = True
    return app


@pytest.fixture(scope='session')
def admin_client(app, admin_user):
    """A flask app client pre configured to send admin cookies"""
    client = app.test_client()
    resp = client.post('/login', data=dict(username=admin_user['email'],
                                           password=admin_user['password_cleartext']))
    assert resp.status_code == 303

    cookies = parse_cookies(resp.headers.getlist('Set-Cookie'))
    ngcookie_name = app.config['AUTH_SESSION_COOKIE_NAME']
    assert ngcookie_name in cookies
    classic_cookie_name = app.config['CLASSIC_COOKIE_NAME']
    assert classic_cookie_name in cookies
    client.set_cookie('', ngcookie_name, cookies[ngcookie_name]['value'])
    client.set_cookie('', classic_cookie_name, cookies[classic_cookie_name]['value'])
    client.set_cookie('', app.config['CLASSIC_TRACKING_COOKIE'], 'fake_browser_tracking_cookie_value')
    return client
