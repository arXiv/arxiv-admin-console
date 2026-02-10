# arxiv-admin-console


## Setting Up the Test Environment

The API backend tests live in `api_arxiv_admin/tests/`. They use Docker to run a MySQL test database loaded with sanitized test data, and pytest as the test runner.

### Prerequisites

- Python 3.12 (may be updated yearly!)
- Docker and Docker Compose
- `mysql` client CLI (for some health-check helpers)

### 1. Bootstrap the Python environment

From the `api_arxiv_admin/` directory:

```bash
cd api_arxiv_admin
./config.sh
make bootstrap
```

This creates a Python 3.12 venv and installs all dependencies (including dev dependencies) via Poetry.

If you already have the venv, you can update dependencies with:

```bash
cd api_arxiv_admin
source venv/bin/activate
poetry install
```

### 2. Test configurations

There are two test configurations, each with its own docker-compose file:

| Configuration     | Docker Compose File           | Description                                                                                                                             |
|-------------------|-------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------|
| **Full stack**    | `docker-compose.yaml`         | MySQL + Keycloak + nginx + test MTA + legacy auth provider. Used by tests requiring Keycloak authentication (e.g., `test_users_rw.py`). |
| **Database only** | `docker-compose-db-only.yaml` | MySQL only. Faster to start. Used by tests that only need the database (e.g., `test_endorsements_api.py`, `test_ownership.py`).         |
| **sqlite3**       | None                          | sqlite3 database made from copying schema/data from mysql.                                                                              |


Mysql use port **22204** for MySQL (defined as `ARXIV_DB_PORT` in `tests/test-env`).

### 3. Start the test database

When you need a test database, you can use `make up` to start it. It loads the test data.

### 4. Run the tests

From the `api_arxiv_admin/` directory:

```bash
cd api_arxiv_admin
source venv/bin/activate
poetry run pytest tests/
```

Or from the project root:

```bash
make test
```

### 5. SQLite-based tests (no Docker required)

Some tests can run against a bundled SQLite database (`tests/data/arxiv-sqlite-0.db.gz`) instead of MySQL. These use the `test-env-sqlite` environment and the `sqlite_db` / `admin_api_sqlite_client` fixtures. No Docker is needed for these tests.
For the tests that doesn't require UTF-8 data, or interaction with user data, use sqlite3. 

See the fixtures in `./api_arxiv_admin/tests/conftest.py`

### Test environment files

| File | Purpose |
|---|---|
| `tests/test-env` | Environment variables for MySQL-based tests (ports, DB URIs, JWT secrets, etc.) |
| `tests/test-env-sqlite` | Environment variables for SQLite-based tests |

### Key test fixtures (from `conftest.py`)

| Fixture | Scope | Description |
|---|---|---|
| `test_env` | module | Loads `test-env` dotenv file |
| `docker_compose` | module | Starts full docker-compose stack |
| `docker_compose_db_only` | module | Starts database-only docker-compose |
| `admin_api_client` | module | FastAPI TestClient with full stack |
| `admin_api_db_only_client` | module | FastAPI TestClient with DB only |
| `admin_api_admin_user_headers` | module | Auth headers for admin user (Cookie Monster) |
| `reset_test_database` | module | Resets MySQL to snapshot state |
| `database_session` | module | Direct SQLAlchemy database session |
| `sqlite_db` | module | Decompresses and configures the SQLite database from `data/arxiv-sqlite-0.db.gz` |
| `test_env_sqlite` | module | Loads `test-env-sqlite` dotenv file with SQLite DB URI |
| `sqlite_session` | module | Direct SQLAlchemy database session using SQLite |
| `admin_api_sqlite_client` | module | FastAPI TestClient using SQLite (no Docker needed) |

