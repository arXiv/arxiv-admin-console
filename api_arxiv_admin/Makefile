include ../.env
export $(shell sed 's/=.*//' ../.env)

app_tag := ${ADMIN_API_TAG}
app_name := arxiv-admin-api
app_port := ${ADMIN_API_PORT}
dockerport := 8080

ROOT_DIR := $(shell pwd)
ADMINAPI_CPUS := $(shell echo $${ADMINAPI_CPUS:-4})
ADMINAPI_WORKERS := $(shell echo $${ADMINAPI_WORKERS:-8})
ADMINAPI_DOCKER_PLATFORM := $(shell echo $${ADMINAPI_DOCKER_PLATFORM:-linux/amd64})

KEYCLOAK_SERVER_URL := ${shell cat ${HOME}/.arxiv/keycloak-url-dev}
KEYCLOAK_CLIENT_SECRET := $(shell cat ${HOME}/.arxiv/keycloak-secret-dev)
CLASSIC_DB_URI := $(shell cat ${HOME}/.arxiv/arxiv-db-dev)

AAA_TOKEN_REFRESH_URL := $(shell echo $${AAA_TOKEN_REFRESH_URL:-https://dev3.arxiv.org/aaa/refresh})
AAA_LOGIN_REDIRECT_URL := $(shell echo $${AAA_LOGIN_REDIRECT_URL:-https://dev3.arxiv.org/aaa/login})

ADMIN_CONSOLE_URL := $(shell echo $${ADMIN_CONSOLE_URL:-https://dev3.arxiv.org/admin-console})

JWT_SECRET := $(shell cat ${HOME}/.arxiv/jwt-secret)
AUTH_SESSION_COOKIE_NAME := arxiv_oidc_session
CLASSIC_COOKIE_NAME := tapir_session

APP_DOCKER_RUN := docker run --cpus ${ADMINAPI_CPUS} --rm -p ${app_port}:${dockerport} \
-e PORT=${dockerport} -e WORKERS=${ADMINAPI_WORKERS} \
-e ADMIN_API_ROOT_PATH=/admin-api \
-e ADMIN_APP_URL=${ADMIN_CONSOLE_URL} \
-e CLASSIC_DB_URI=${CLASSIC_DB_URI} \
-e AAA_TOKEN_REFRESH_URL=${AAA_TOKEN_REFRESH_URL} \
-e AAA_LOGIN_REDIRECT_URL=${AAA_LOGIN_REDIRECT_URL} \
-e JWT_SECRET=${JWT_SECRET} \
-e AUTH_SESSION_COOKIE_NAME=${AUTH_SESSION_COOKIE_NAME} \
-e CLASSIC_COOKIE_NAME=${CLASSIC_COOKIE_NAME} \
--name ${app_name} --security-opt="no-new-privileges=true"

.PHONY: HELLO docker run stop bootstrap show-env

default: HELLO

HELLO:
	@echo If you are developing and set up Python venv, "make bootstrap".
	@echo To see the README of this Makefile, type "make help"
	@echo Local HTTP port is ${app_port}
	@echo Docker command params is:
	@echo ${APP_DOCKER_RUN}

bootstrap: venv/lib/python3.12/site-packages/fastapi

#-#
#-# Command: help
#-#   show this message
help:
	@awk '/^#-#/ { print substr($$0, 5)}' Makefile

#-#
#-# Command: docker-image
#-#   builds the docker image
docker-image: /usr/bin/docker
	@echo "PLATFORM: ${PLATFORM}"
	@echo "dockerport: ${app_port}"
	@echo "tag: ${app_tag}"
	docker buildx build -f ./Dockerfile \
		--security-opt seccomp=unconfined  \
		--progress=plain \
		--platform=linux/amd64 -t ${app_tag}:latest .

#-#
#-# Command: run
#-#   runs the appliance container with the terminal attached (for test)
run: stop
	${APP_DOCKER_RUN} -it --rm ${app_tag}:latest 

#-#
#-# Command: daemon
#-#   runs the appliance container as a daemon
daemon: stop
	${APP_DOCKER_RUN} -d --rm ${app_tag}:latest 

#-#
#-# Command: stop
#-#   stops the appliance container
stop:
	-docker container kill ${app_name}
	-docker container rm ${app_name}

#-#
#-# Command: sh
#-#   runs a bash shell in the container to look inside of it
sh: stop
	${APP_DOCKER_RUN}  -v ${HOME}/Downloads:/home/worker/Downloads -w /home/worker -it ${app_tag}:latest  /bin/bash


/usr/bin/python3.12:
	sudo apt install -y python3.12

/usr/lib/python3.12/ensurepip/__init__.py:
	sudo apt install -y python3.12-venv

.bootstrap:
	sudo apt install -y libmysqlclient-dev build-essential python3.12-dev
	touch .bootstrap

venv:
	python3.12 -m venv venv

venv/bin/poetry: /usr/bin/python3.12 /usr/lib/python3.12/ensurepip/__init__.py venv
	. venv/bin/activate && pip install --upgrade pip && pip install poetry

venv/lib/python3.12/site-packages/fastapi: venv/bin/poetry
	. venv/bin/activate && poetry install

/usr/bin/docker:
	sh ./install-docker.sh

show-env:
	sed -e 's/^/export /g' .env
