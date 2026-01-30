import shlex
import sys, os

from arxiv_bizlogic.fastapi_helpers import datetime_to_epoch

rooddir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(rooddir)

import subprocess
from pathlib import Path
from typing import Dict, Optional, Generator

from arxiv.auth.user_claims import ArxivUserClaims, ArxivUserClaimsModel
from dotenv import dotenv_values, load_dotenv
from arxiv.config import Settings
from arxiv_bizlogic.database import Database, DatabaseSession
from arxiv_bizlogic.user_account_models import AccountIdentifierModel

ADMIN_API_TEST_DIR = Path(__file__).parent

dotenv_filename = 'test-env'
load_dotenv(dotenv_path=ADMIN_API_TEST_DIR.joinpath(dotenv_filename), override=True)

import pytest
import logging

from time import sleep
from datetime import datetime

from fastapi.testclient import TestClient
from arxiv_admin_api.main import create_app
import os


MYSQL_DATA_DIR = ADMIN_API_TEST_DIR / "mysql-data"
MYSQL_SNAPSHOT_DIR = ADMIN_API_TEST_DIR / "mysql-data-snapshot"

DC_YAML = ADMIN_API_TEST_DIR.joinpath('docker-compose.yaml')
DC_DBO_YAML = ADMIN_API_TEST_DIR.joinpath('docker-compose-db-only.yaml')

ADMIN_API_DIR = ADMIN_API_TEST_DIR.parent
ARXIV_ADMIN_CONSOLE_DIR = ADMIN_API_DIR.parent
TEST_DB_DUMP_DIR = ARXIV_ADMIN_CONSOLE_DIR / "tests" / "data" / "test-db-dump"


def ignore_socket_files(directory, files):
    """Ignore socket files when copying directory trees."""
    import stat
    ignored = []
    for f in files:
        path = Path(directory) / f
        try:
            if path.exists() and stat.S_ISSOCK(path.stat().st_mode):
                ignored.append(f)
        except (OSError, IOError):
            # If we can't stat the file, ignore it to be safe
            ignored.append(f)
    return ignored


def reset_database_from_snapshot(db_port: str, container_name: str = "admin-api-arxiv-test-db") -> bool:
    """
    Reset the database to its initial state by restoring from snapshot.
    If snapshot doesn't exist, creates one from current data.
    If snapshot exists, restores the database from it.
    Snapshot is stored in mysql-data-snapshot directory on the local disk.
    """
    import shutil

    try:
        # Stop the container
        logging.info("Stopping container...")
        subprocess.run(
            ["docker", "stop", container_name],
            check=True,
            timeout=30
        )

        if not MYSQL_SNAPSHOT_DIR.exists():
            # Snapshot doesn't exist - create it from current data
            logging.info(f"Creating snapshot: copying {MYSQL_DATA_DIR} to {MYSQL_SNAPSHOT_DIR}...")
            shutil.copytree(MYSQL_DATA_DIR, MYSQL_SNAPSHOT_DIR, ignore=ignore_socket_files)
            logging.info("Snapshot created successfully")
        else:
            # Snapshot exists - restore from it
            logging.info("Restoring database from snapshot...")
            if MYSQL_DATA_DIR.exists():
                shutil.rmtree(MYSQL_DATA_DIR)
            shutil.copytree(MYSQL_SNAPSHOT_DIR, MYSQL_DATA_DIR, ignore=ignore_socket_files)
            logging.info("Database restored from snapshot")

        # Start the container (which will start MySQL)
        logging.info("Starting container...")
        subprocess.run(["docker", "start", container_name], check=True, timeout=30)

        # Wait for MySQL to be ready
        for _ in range(30):
            sleep(1)
            result = subprocess.run(
                ["docker", "exec", container_name, "mysqladmin",
                 "ping", "-h", "127.0.0.1", "-P", db_port, "--silent"],
                capture_output=True,
                check=False
            )
            if result.returncode == 0:
                logging.info("Database reset successfully")
                return True

        logging.error("Database failed to start after reset")
        return False

    except Exception as e:
        logging.error(f"Failed to reset database: {str(e)}")
        return False


def check_any_rows_in_table(schema: str, table_name: str, db_user: str, db_password: str, db_port: str = "3306", ssl: bool = True) -> bool:
    try:
        logging.info(f"Checking table {table_name} in schema {schema} on port {db_port}")
        result = subprocess.run(
            [
                "mysql",
                f"-u{db_user}",
                f"-p{db_password}",
                "-h", "127.0.0.1",
                "-P", db_port,
                "--default-auth=mysql_native_password",
                "-N",
                "-B",
                "-e", f"SELECT COUNT(*) FROM {table_name};",
                schema
            ],
            capture_output=True,
            text=True,
            check=False # Do not raise exception for non-zero exit codes
        )
        if result.returncode != 0:
            logging.error(f"MySQL command failed with exit code {result.returncode}")
            logging.error(f"Stdout: {result.stdout}")
            logging.error(f"Stderr: {result.stderr}")
            return False
        count = int(result.stdout.strip())
        logging.info(f"Table {table_name} has {count} rows.")
        return count > 0
    except subprocess.CalledProcessError as e:
        return False
    except ValueError:
        return False


def generate_request_headers(test_env: dict, user_id: int = 1129053, tapir_session_id: int = 0) -> Dict[str, str]:
    jwt_secret = test_env['JWT_SECRET']
    now_epoch = datetime_to_epoch(None, datetime.now())

    claims_data = ArxivUserClaimsModel(
        sub = str(user_id),
        exp = now_epoch + 360000,  # Expiration
        iat = now_epoch,
        roles = ["Public user"],
        email_verified = True,
        email = "no-reply@example.com",

        acc = "magic-access", # Access token
        idt = "", # ID token
        sid = "kc-session-id",

        first_name = "Test",
        last_name = "User",
        username = "cookie_monster",
        client_ipv4 = "127.0.0.1",
        ts_id = tapir_session_id)

    api_token = ArxivUserClaims(claims_data).encode_jwt_token(jwt_secret)

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    return headers


@pytest.fixture(scope="module")
def test_env() -> Dict[str, Optional[str]]:
    if not ADMIN_API_TEST_DIR.joinpath(dotenv_filename).exists():
        raise FileNotFoundError(dotenv_filename)
    return dotenv_values(ADMIN_API_TEST_DIR.joinpath(dotenv_filename).as_posix())


@pytest.fixture(scope="module")
def docker_compose(test_env):
    logging.info("Setting up docker-compose")
    if not DC_YAML.exists():
        raise FileNotFoundError(DC_YAML.as_posix())
    env_arg = "--env-file=" + dotenv_filename
    working_dir = ADMIN_API_TEST_DIR.as_posix()

    # Set UID/GID for docker-compose to run containers as current user
    docker_env = os.environ.copy()
    docker_env["UID"] = str(os.getuid())
    docker_env["GID"] = str(os.getgid())

    try:
        subprocess.run(["docker", "compose", "--ansi=none", env_arg, "-f", DC_DBO_YAML.as_posix(), "down", "--remove-orphans"],
                       check=False, cwd=working_dir, env=docker_env)
    except Exception as e:
        pass

    try:
        logging.info("Stopping docker-compose...")
        subprocess.run(["docker", "compose", "--ansi=none", env_arg, "-f", DC_YAML.as_posix(), "down", "--remove-orphans"], check=False, cwd=working_dir, env=docker_env)
        logging.info("Starting docker-compose...")
        subprocess.run(["docker", "compose", "--ansi=none", env_arg, "-f", DC_YAML.as_posix(), "up", "-d"], check=True, cwd=working_dir, env=docker_env)
        
        # Loop until at least one row is present
        for _ in range(100):
            sleep(1)
            if check_any_rows_in_table("arXiv", "tapir_users", "arxiv", "arxiv_password", db_port=test_env["ARXIV_DB_PORT"], ssl=False):
                logging.info("Database is ready.")
                break
        else:
            assert False, "Failed to load "

        yield None
    except Exception as e:
        logging.error(f"bad... {str(e)}")

    finally:
        logging.info("Leaving the docker-compose as is...")



@pytest.fixture(scope="module")
def test_mta(test_env, docker_compose):
    return f"http://127.0.0.1:{test_env['MAIL_API_PORT']}"


@pytest.fixture(scope="module")
def admin_api_client(test_env, docker_compose):
    """Start Admin Console App. Since it needs the database running, it needs the arxiv db up"""
    os.environ.update(test_env)
    app = create_app(TESTING=True)
    admin_api_url = test_env['ADMIN_API_URL']
    client = TestClient(app, base_url=admin_api_url)

    for _ in range(100):
        response = client.get("/status/")
        if response.status_code == 200:
            logging.info("Admin-API status - OK")
            sleep(2)
            break
        sleep(2)
        logging.info("Admin-API status - WAITING")
        pass
    else:
        assert False, "The docker compose did not start?"
    yield client
    client.close()


@pytest.fixture(scope="module")
def admin_api_db_only_client(test_env: Dict, docker_compose_db_only) -> Generator[TestClient, None, None]:
    """Start Admin API with database-only setup (faster for isolated tests)"""
    # Make sure there is no keycloak secret
    test_env["KEYCLOAK_ADMIN_SECRET"] = "<NOT-SET>"

    os.environ.update(test_env)
    app = create_app(TESTING=True)
    admin_api_url = test_env['ADMIN_API_URL']
    client = TestClient(app, base_url=admin_api_url)

    for _ in range(100):
        response = client.get("/system/database_status")
        if response.status_code == 200:
            logging.info("AAA status - OK")
            break
        sleep(2)
        logging.info("AAA status - WAITING")
        pass
    else:
        assert False, "The database did not start?"
    yield client
    client.close()


@pytest.fixture(scope="module")
def admin_api_headers(test_env):
    admin_api_token = test_env['ADMIN_API_TOKEN']
    headers = {
        "Authorization": f"Bearer {admin_api_token}",
        "Content-Type": "application/json"
    }
    return headers


@pytest.fixture(scope="module")
def admin_api_admin_user_headers(test_env):
    user_info = ArxivUserClaimsModel(
        sub = "1129053",
        exp = 253402300799,
        iat = 0,
        sid = "23276925",
        ts_id = 23276925,
        roles = ["Administrator", "CanLock", "Approved", "Public user"],
        email_verified = True,
        email = "<EMAIL>",
        first_name = "Cookie",
        last_name = "Monster",
        username = "cmonster",
    )
    claims = ArxivUserClaims(user_info)
    token = claims.encode_jwt_token(secret=test_env['JWT_SECRET'])
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    return headers


@pytest.fixture(scope="module")
def user0001_headers(test_env, admin_api_client, admin_api_headers):
    response1 = admin_api_client.get("/account/identifier/?username=user0001", headers=admin_api_headers)
    first_user: AccountIdentifierModel = AccountIdentifierModel.model_validate(response1.json())

    user_claims = ArxivUserClaims(
        ArxivUserClaimsModel(
            acc="fake-access-token",
            sub = first_user.user_id,
            exp = 253402300799,
            iat = 1743465600,
            sid = "kc-session-1",
            roles = ["Approved", "Public user"],
            email_verified = True,
            email = first_user.email,
            first_name = "Test",
            last_name = "User",
            username = first_user.username,
            ts_id = 1,
        )
    )
    token = user_claims.encode_jwt_token(secret=test_env['JWT_SECRET'])
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    return headers


@pytest.fixture(scope="module")
def docker_compose_db_only(test_env):
    logging.info("Setting up database only")
    if not DC_DBO_YAML.exists():
        raise FileNotFoundError(DC_DBO_YAML.as_posix())
    env_arg = "--env-file=" + dotenv_filename
    working_dir = ADMIN_API_TEST_DIR.as_posix()

    LOADER_CONTAINER_NAME = "admin-api-db-myloader"

    # kill off the other docker-compose instance
    try:
        result = subprocess.run(
            ["docker", "compose", "-f", DC_YAML, "down"],
            capture_output=True,
            text=True,
            check=False
        )
    except Exception as e:
        pass

    # Set UID/GID for docker-compose to run containers as current user
    docker_env = os.environ.copy()
    docker_env["UID"] = str(os.getuid())
    docker_env["GID"] = str(os.getgid())
    docker_env["TEST_DB_DUMP_DIR"] = TEST_DB_DUMP_DIR.as_posix()

    try:
        container_name = "admin-api-arxiv-test-db"
        needs_data_load = False

        # Check if container exists and is running
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", container_name],
            capture_output=True,
            text=True,
            check=False,
            env = docker_env
        )

        # Ensure mysql-data directory exists with proper ownership for bind mount
        if not MYSQL_DATA_DIR.exists():
            logging.info("Creating mysql-data directory...")
            MYSQL_DATA_DIR.mkdir(parents=True, exist_ok=True)

        if result.returncode != 0:
            # Container doesn't exist, start docker-compose
            logging.info("Container doesn't exist, starting docker-compose...")
            args = ["docker", "compose", "--ansi=none", env_arg, "-f", DC_DBO_YAML.as_posix(), "up", "-d"]
            logging.info(shlex.join(args))
            result = subprocess.run(args, cwd=working_dir, env=docker_env, capture_output=True, text=True)
            if result.returncode != 0:
                logging.error(f"docker-compose failed: {result.stderr}")
                raise RuntimeError(f"docker-compose failed: {result.stderr}")
            needs_data_load = True
        elif result.stdout.strip() == "true":
            # Container is running
            logging.info("Container already running")
        else:
            # Container exists but is not running (stopped, created, etc.)
            logging.info("Container exists but is not running, recreating...")
            subprocess.run(["docker", "compose", "--ansi=none", env_arg, "-f", DC_DBO_YAML.as_posix(), "down"],
                           cwd=working_dir, env=docker_env)
            result = subprocess.run(["docker", "compose", "--ansi=none", env_arg, "-f", DC_DBO_YAML.as_posix(), "up", "-d"],
                           cwd=working_dir, env=docker_env, capture_output=True, text=True)
            if result.returncode != 0:
                logging.error(f"docker-compose failed: {result.stderr}")
                raise RuntimeError(f"docker-compose failed: {result.stderr}")
            needs_data_load = True

        # Wait for myloader container to complete (only if we just started docker-compose)
        if needs_data_load:
            logging.info("Waiting for myloader to complete...")
            for _ in range(100):
                result = subprocess.run(
                    ["docker", "inspect", "-f", "{{.State.Status}}", LOADER_CONTAINER_NAME],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if result.returncode == 0 and "exited" in result.stdout:
                    # Check if it exited successfully (exit code 0)
                    exit_code_result = subprocess.run(
                        ["docker", "inspect", "-f", "{{.State.ExitCode}}", LOADER_CONTAINER_NAME],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    if exit_code_result.returncode == 0 and "0" in exit_code_result.stdout:
                        logging.info("Myloader completed successfully")
                        break
                    else:
                        logging.error(f"Myloader failed with exit code: {exit_code_result.stdout.strip()}")
                        assert False, "Myloader failed to load data"
                sleep(1)
            else:
                assert False, "Myloader timed out"
        else:
            logging.info("Skipping myloader wait (container already existed)")

        # Wait for MySQL to be ready
        logging.info("Waiting for MySQL to be ready...")
        for _ in range(30):
            result = subprocess.run(
                ["docker", "exec", container_name, "mysqladmin",
                 "ping", "-h", "127.0.0.1", "-P", test_env["ARXIV_DB_PORT"], "--silent"],
                capture_output=True,
                check=False
            )
            if result.returncode == 0:
                logging.info("MySQL is ready")
                break
            sleep(1)
        else:
            assert False, "MySQL failed to become ready"

        # Check if snapshot exists on local disk
        snapshot_exists = MYSQL_SNAPSHOT_DIR.exists()
        logging.info(f"Snapshot exists: {snapshot_exists}")

        # Create snapshot if it doesn't exist
        if not snapshot_exists:
            import shutil
            logging.info("Creating database snapshot on local disk...")
            try:
                # Flush tables to ensure data consistency
                logging.info("Flushing tables for snapshot...")
                subprocess.run(
                    ["docker", "exec", container_name, "mysql",
                     "-uroot", "-proot_password", "-h", "127.0.0.1",
                     "-P", test_env["ARXIV_DB_PORT"],
                     "-e", "FLUSH TABLES;"],
                    check=True,
                    timeout=30
                )

                # Stop the container to ensure clean snapshot
                logging.info("Stopping container for snapshot...")
                subprocess.run(
                    ["docker", "stop", container_name],
                    check=True,
                    timeout=30
                )
                sleep(1)

                # Copy mysql-data to snapshot directory on local disk
                logging.info(f"Copying {MYSQL_DATA_DIR} to {MYSQL_SNAPSHOT_DIR}...")
                shutil.copytree(MYSQL_DATA_DIR, MYSQL_SNAPSHOT_DIR, ignore=ignore_socket_files)

                # Start the container again
                logging.info("Starting container after snapshot...")
                subprocess.run(
                    ["docker", "start", container_name],
                    check=True,
                    timeout=30
                )

                # Wait for MySQL to be ready again
                for _ in range(30):
                    result = subprocess.run(
                        ["docker", "exec", container_name, "mysqladmin",
                         "ping", "-h", "127.0.0.1", "-P", test_env["ARXIV_DB_PORT"], "--silent"],
                        capture_output=True,
                        check=False
                    )
                    if result.returncode == 0:
                        break
                    sleep(1)

                logging.info("Database snapshot created successfully")

            except Exception as e:
                logging.error(f"Failed to create snapshot: {str(e)}")
                raise

        yield None
    except Exception as e:
        logging.error(f"bad... {str(e)}")
        raise

    finally:
        logging.info("Keeping docker-compose running for subsequent tests...")


@pytest.fixture(scope="module")
def reset_test_database(test_env, docker_compose_db_only):
    """
    Reset the database to its initial snapshot state before each test.
    Use this fixture when you need a clean database state for each test.
    """
    logging.info("Resetting database from snapshot...")
    success = reset_database_from_snapshot(db_port=test_env["ARXIV_DB_PORT"])
    if not success:
        pytest.fail("Failed to reset database from snapshot")
    yield None


@pytest.fixture(scope="function")
def reset_test_database_for_function(test_env, docker_compose_db_only):
    """
    Reset the database to its initial snapshot state before each test.
    Use this fixture when you need a clean database state for each test.
    """
    logging.info("Resetting database from snapshot...")
    success = reset_database_from_snapshot(db_port=test_env["ARXIV_DB_PORT"])
    if not success:
        pytest.fail("Failed to reset database from snapshot")
    yield None


@pytest.fixture(scope="function")
def database_instance(test_env, docker_compose_db_only):
    """
    Set up the database connection for tests that need direct database access.
    This fixture configures the global Database instance and provides DatabaseSession.
    """
    db_uri = "mysql+mysqldb://{}:{}@{}:{}/{}".format(
        "arxiv",
        "arxiv_password",
        "127.0.0.1",
        test_env["ARXIV_DB_PORT"],
        "arXiv"
    )

    settings = Settings(
        CLASSIC_DB_URI=db_uri,
        LATEXML_DB_URI=None
    )
    database = Database(settings)
    database.set_to_global()
    yield DatabaseSession


@pytest.fixture(scope="module")
def database_session(test_env, docker_compose_db_only):
    """
    Set up the database connection for tests that need direct database access.
    This fixture configures the global Database instance and provides DatabaseSession.
    """

    db_uri = "mysql+mysqldb://{}:{}@{}:{}/{}".format(
        "arxiv",
        "arxiv_password",
        "127.0.0.1",
        test_env["ARXIV_DB_PORT"],
        "arXiv"
    )

    settings = Settings(
        CLASSIC_DB_URI=db_uri,
        LATEXML_DB_URI=None
    )
    database = Database(settings)
    database.set_to_global()

    yield DatabaseSession
