# arxiv-admin-console


## Setting Up the Test Environment

The API backend tests live in `api_arxiv_admin/tests/`. They use Docker to run a MySQL test database loaded with sanitized test data, and pytest as the test runner.

### Prerequisites

- Python 3.12 (may be updated yearly!)
- Docker and Docker Compose
- `mysql` client CLI (for some health-check helpers)
- 1password CLI

### 1. Bootstrap the Python environment

From the `api_arxiv_admin/` directory:

```bash
cd ~/arxiv/arxiv-keycloak
./config.sh
make bootstrap
make docker-image
make up

cd api_arxiv_admin
ln -s ../arxiv-keycloak/.env .env
make bootstrap
make docker-image
make up
```

After that, one should be able to log into

    http://localhost.arxiv.org:5100/admin-console/

with user/pass from 1password entry `localhost.arxiv.org for tapir test`

arxiv-keycloak provides not only the auth backend but it has nginx that
reverse proxies the service and UI.

## .env

./config.sh in arxiv-keycloak creates the file. Use it by symlink to make life easier.
You may create your own .env. When you do so, make sure two .env files align.

This is used for building Docker images as well as running Docker containers.
docker compose takes this env file.


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


## Development

Once everything is running, you stop a docker and run your development server.

For example, if you want to work on UI, you can `docker kill admin-ui` and then
run the admin UI dev server. Same goes for admin-api.

If you need the env vars, copy&paste `.env` file.
