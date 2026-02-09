# arxiv-admin-console

# Development

## Prerequisit

Before you start, you need 1password CLI. The config.sh gets a few values from
1P and populates the values in .env.localdb.


## Quick start

    cd ~/arxiv/arxiv-keycloak
    ./config.sh
    make bootstrap
    make docker-image
    make up

    cd ~/arxiv/arxiv-admin-console
    ln -s ../arxiv-keycloak/.env .env
    make bootstrap
    make docker-image
    make up

After that, one should be able to log into

    http://localhost.arxiv.org:5100/admin-console/

with user/pass from 1password entry `localhost.arxiv.org for tapir test`

arxiv-keycloak provides not only the auth backend but it has nginx that
reverse proxies the service and UI.


## .env

./config.sh creates the file, and symlink .env --> .env.localdb.

Once created, you may change the .env as needed but YMMV. Adding is fine but
be careful of removing entries.

This is used for building Docker images as well as running Docker containers.
docker compose takes this env file.

## Running test

    cd api_admin_console
    . venv/bin/activate
    poetry run pytest
    

## Development

Once everything is running, you stop a docker and run your development server.

For example, if you want to work on UI, you can `docker kill admin-ui` and then
run the admin UI dev server. Same goes for admin-api.

If you need the env vars, copy&paste `.env` file.
