import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from arxiv.auth.legacy.util import epoch
from arxiv.auth.user_claims import ArxivUserClaims, ArxivUserClaimsModel
from arxiv_bizlogic.fastapi_helpers import datetime_to_epoch
from dotenv import load_dotenv
from dotenv.main import DotEnv
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session as SASession

ADMIN_API_TEST_DIR = Path(__file__).parent

dotenv_filename = 'test-env'
load_dotenv(dotenv_path=ADMIN_API_TEST_DIR.joinpath(dotenv_filename), override=True)

import pytest
import logging

from time import sleep
from typing import IO, Dict, Iterable, Iterator, Mapping, Optional, Tuple, Union, Generator

from fastapi.testclient import TestClient
from arxiv_admin_api.main import create_app
import os
from arxiv_bizlogic.database import DatabaseSession, Database
from tests.restore_mysql import wait_for_mysql
from arxiv.db.models import TapirUser

@pytest.fixture(scope="module")
def test_env() -> Dict[str, Optional[str]]:
    if not ADMIN_API_TEST_DIR.joinpath(dotenv_filename).exists():
        raise FileNotFoundError(dotenv_filename)
    return dotenv_values(ADMIN_API_TEST_DIR.joinpath(dotenv_filename).as_posix())

StrPath = Union[str, "os.PathLike[str]"]

def _walk_to_root(path: str) -> Iterator[str]:
    """
    Yield directories starting from the given directory up to the root
    """
    if not os.path.exists(path):
        raise IOError("Starting path not found")

    if os.path.isfile(path):
        path = os.path.dirname(path)

    last_dir = None
    current_dir = os.path.abspath(path)
    while last_dir != current_dir:
        yield current_dir
        parent_dir = os.path.abspath(os.path.join(current_dir, os.path.pardir))
        last_dir, current_dir = current_dir, parent_dir



def find_dotenv(
    filename: str = ".env",
    raise_error_if_not_found: bool = False,
    usecwd: bool = False,
) -> str:
    """
    Search in increasingly higher folders for the given file

    Returns path to the file if found, or an empty string otherwise
    """

    def _is_interactive():
        """Decide whether this is running in a REPL or IPython notebook"""
        try:
            main = __import__("__main__", None, None, fromlist=["__file__"])
        except ModuleNotFoundError:
            return False
        return not hasattr(main, "__file__")

    def _is_debugger():
        return sys.gettrace() is not None

    if usecwd or _is_interactive() or _is_debugger() or getattr(sys, "frozen", False):
        # Should work without __file__, e.g. in REPL or IPython notebook.
        path = os.getcwd()
    else:
        # will work for .py files
        frame = sys._getframe()
        current_file = __file__

        while frame.f_code.co_filename == current_file or not os.path.exists(
            frame.f_code.co_filename
        ):
            assert frame.f_back is not None
            frame = frame.f_back
        frame_filename = frame.f_code.co_filename
        path = os.path.dirname(os.path.abspath(frame_filename))

    for dirname in _walk_to_root(path):
        check_path = os.path.join(dirname, filename)
        if os.path.isfile(check_path):
            return check_path

    if raise_error_if_not_found:
        raise IOError("File not found")

    return ""
#
#
def dotenv_values(
    dotenv_path: Optional[StrPath] = None,
    stream: Optional[IO[str]] = None,
    verbose: bool = False,
    interpolate: bool = True,
    encoding: Optional[str] = "utf-8",
) -> Dict[str, Optional[str]]:
    """
    Parse a .env file and return its content as a dict.

    The returned dict will have `None` values for keys without values in the .env file.
    For example, `foo=bar` results in `{"foo": "bar"}` whereas `foo` alone results in
    `{"foo": None}`

    Parameters:
        dotenv_path: Absolute or relative path to the .env file.
        stream: `StringIO` object with .env content, used if `dotenv_path` is `None`.
        verbose: Whether to output a warning if the .env file is missing.
        encoding: Encoding to be used to read the file.

    If both `dotenv_path` and `stream` are `None`, `find_dotenv()` is used to find the
    .env file.
    """
    if dotenv_path is None and stream is None:
        dotenv_path = find_dotenv()

    return DotEnv(
        dotenv_path=dotenv_path,
        stream=stream,
        verbose=verbose,
        interpolate=interpolate,
        override=True,
        encoding=encoding,
    ).dict()


# def check_any_rows_in_table(schema: str, table_name: str, db_user: str, db_password: str, db_port: str = "3306", ssl: bool = True) -> bool:
#     try:
#         result = subprocess.run(
#             [
#                 "mysql",
#                 f"-u{db_user}",
#                 f"-p{db_password}",
#                 "-h", "127.0.0.1",
#                 "-P", db_port,
#                 "--ssl-mode=ENABLED" if ssl else "--ssl-mode=DISABLED",
#                 "-N",
#                 "-B",
#                 "-e", f"SELECT COUNT(*) FROM {table_name};",
#                 schema
#             ],
#             capture_output=True,
#             text=True,
#             check=True
#         )
#         count = int(result.stdout.strip())
#         return count > 0
#     except subprocess.CalledProcessError as e:
#         return False
#     except ValueError:
#         return False
#
#
#
# @pytest.fixture(scope="module", autouse=True)
# def docker_compose(test_env):
#     logging.info("Setting up docker-compose")
#     docker_compose_file = ADMIN_API_TEST_DIR.joinpath('docker-compose.yaml')
#     if not docker_compose_file.exists():
#         raise FileNotFoundError(docker_compose_file.as_posix())
#     env_arg = "--env-file=" + dotenv_filename
#     working_dir = ADMIN_API_TEST_DIR.as_posix()
#
#     try:
#         if os.environ.get("RECREATE_DOCKERS", "true") == "true":
#             logging.info("Stopping docker-compose...")
#             subprocess.run(["docker", "compose", env_arg, "-f", docker_compose_file, "down", "--remove-orphans"], check=False, cwd=working_dir)
#             logging.info("Starting docker-compose...")
#             subprocess.run(["docker", "compose", env_arg, "-f", docker_compose_file, "up", "-d"], check=True, cwd=working_dir)
#             pass
#
#         # Loop until at least one row is present
#         for _ in range(100):
#             sleep(1)
#             if check_any_rows_in_table("arXiv", "tapir_users", "arxiv", "arxiv_password", db_port=test_env["ARXIV_DB_PORT"], ssl=False):
#                 break
#         else:
#             assert False, "Failed to load "
#
#         yield None
#     except Exception as e:
#         logging.error(f"bad... {str(e)}")
#
#     finally:
#         logging.info("Leaving the docker-compose as is...")
#
#     try:
#         logging.info("Stopping docker-compose...")
#         if os.environ.get("RECREATE_DOCKERS", "true") == "true":
#             subprocess.run(["docker", "compose", env_arg, "-f", docker_compose_file, "down", "--remove-orphans"], check=False, cwd=working_dir)
#     except Exception:
#         pass
#

@pytest.fixture(scope="module", autouse=True)
def api_client(test_env):
    """Start Admin API App. Since it needs the database running, it needs the arxiv db up"""
    os.environ.update(test_env)
    app = create_app()
    # Admin API_app_port = test_env['ARXIV_OAUTH2_APP_PORT']
    api_url = test_env['ADMIN_API_URL']
    client = TestClient(app, base_url=api_url)

    for _ in range(100):
        response = client.get("/openapi.json")
        if response.status_code == 200:
            logging.info("Admin API status - OK")
            break

        if response.status_code == 404:
            logging.error("Very wrong.")
            raise Exception("Fix the API access first")

        sleep(2)
        logging.info("Admin API status - WAITING")
        pass
    else:
        assert False, "The docker compose did not start?"
    yield client
    client.close()


@pytest.fixture(scope="module", autouse=True)
def api_headers(test_env):
    jwt_secret = test_env['JWT_SECRET']
    now_epoch = datetime_to_epoch(None, datetime.now())

    claims_data = ArxivUserClaimsModel(
        sub = "1129053",  # User ID - 1129053 is cookie monster
        exp = now_epoch + 360000,  # Expiration
        iat = now_epoch,
        roles = ["Administrator", "Public user"],
        email_verified = True,
        email = "developers@arxiv.org",

        acc = "magic-access", # Access token
        idt = "", # ID token

        first_name = "Cookie",
        last_name = "Monster",
        username = "cookie_monster",
        client_ipv4 = "127.0.0.1",
        ts_id = 23276916) # 23276916 tapir_session

    api_token = ArxivUserClaims(claims_data).encode_jwt_token(jwt_secret)

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    return headers



DOCKER_COMPOSE_ARGS = ["docker", "compose", "-f", "./tests/docker-compose-for-test.yaml", "--env-file=./tests/test-env"]


admin_api_root = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

MAX_RETRIES = 3
RETRY_DELAY = 2

@pytest.fixture(scope="module", autouse=True)
def setup_db_fixture(test_env) -> None:
    subprocess.run(DOCKER_COMPOSE_ARGS + ["up", "-d"], cwd=admin_api_root)

    db_host = test_env['ARXIV_DB_HOST']
    db_port = int(test_env['ARXIV_DB_PORT'])
    db_user = "arxiv"
    db_password = "arxiv_password"

    wait_for_mysql(db_host, db_port, db_user, db_password, "arXiv", MAX_RETRIES, RETRY_DELAY)
    db_uri = "mysql+mysqldb://{}:{}@{}:{}/{}?ssl=false&ssl_mode=DISABLED".format(db_user, db_password, db_host, db_port, "arXiv")
    from arxiv.config import Settings
    settings = Settings(
        CLASSIC_DB_URI = db_uri,
        LATEXML_DB_URI = None
    )
    database = Database(settings)
    database.set_to_global()
    from app_logging import setup_logger
    setup_logger()
    logger = logging.getLogger()

    for _ in range(10):
        try:
            with DatabaseSession() as session:
                users = session.query(TapirUser).all()
                if len(users) > 0:
                    break

        except OperationalError:
            logger.warning("No database session")
            pass

        except Exception as exc:
            logger.error("Database session", exc_info=exc)
            pass
        time.sleep(5)
    else:
        logger.error("No database session - cannot continue")
        raise Exception("No database session - cannot continue")


def teardown_db_fixture() -> None:
    """This method runs once after all test methods in the class."""
    subprocess.run(DOCKER_COMPOSE_ARGS + ["down"], cwd=admin_api_root)

@pytest.fixture(scope="module")
def arxiv_db(setup_db_fixture):
    """Fixture to set up and tear down the database."""
    yield
    teardown_db_fixture()


@pytest.fixture(scope="function")
def db_session() -> Generator[SASession, None, None]:
    """
    Fixture to provide a database session.

    This fixture creates a new database session for each test function,
    which ensures test isolation.

    Returns:
        SQLAlchemy Session: A session connected to the test database
    """
    with DatabaseSession() as session:
        yield session
