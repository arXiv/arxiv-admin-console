DOCKER_DIRS := 
ALL_DIRS := 

include test-env
export $(shell sed 's/=.*//' test-env)

ARXIV_BASE_DIR ?= $(HOME)/arxiv/arxiv-base
GID := $(shell id -g)
UID := $(shell id -u)
TEST_DB_DUMP_DIR ?= $(abspath $(CURDIR)/../../tests/data/test-db-dump)

.PHONY: dump 

dump:
	mkdir -p $(CURDIR)/../../tests/data/test-db-dump
	docker run --rm --network host \
		--user $(shell id -u):$(shell id -g) \
		-v $(CURDIR)/../../tests/data/test-db-dump:/dump-data \
		mydumper/mydumper:latest \
		mydumper \
		--host=127.0.0.1 \
		--port=${ARXIV_DB_PORT} \
		--user=root \
		--password=root_password \
		--database=arXiv \
		--dirty \
		--compress \
		--outputdir=/dump-data


#-#
#-# help:
#-#   print help messsages
help:
	@awk '/^#-#/ { print substr($$0, 5)}' Makefile

#-#
#-# bootstrap:
#-#   bootstraps the environment
bootstrap: .bootstrap

.bootstrap: tests/data/sanitized-test-db.sql setup-$(OS) tests/test_mta_client/
	$(call run_in_all_subdirs,bootstrap)
	touch .bootstrap

setup-debian:
setup-arch:
setup-redhat:

#-#
#-# up:
#-#   runs docker compose up with test-env.
temp-test-env:
	cp test-env temp-test-env
	echo "UID=${UID}" >> temp-test-env
	echo "GID=${GID}" >> temp-test-env
	echo "TEST_DB_DUMP_DIR=${TEST_DB_DUMP_DIR}" >> temp-test-env
	cp temp-test-env .env

up: temp-test-env
	docker compose --ansi=none --env-file=temp-test-env up -d

#-#
#-# down:
#-#   runs docker compose down
down:
	docker compose --ansi=none --env-file=temp-test-env down --remove-orphans


#-#
#-# dbo-up:
#-#   runs docker compose up with test-env.
temp-dbo-test-env:
	cp test-env temp-dbo-test-env
	echo "UID=${UID}" >> temp-dbo-test-env
	echo "GID=${GID}" >> temp-dbo-test-env
	echo "TEST_DB_DUMP_DIR=${TEST_DB_DUMP_DIR}" >> temp-dbo-test-env
	cp temp-dbo-test-env .env

dbo-up: temp-dbo-test-env
	docker compose -f docker-compose-db-only.yaml --ansi=none --env-file=temp-dbo-test-env up -d

#-#
#-# dbo-down:
#-#   runs docker compose down
dbo-down:
	docker compose -f docker-compose-db-only.yaml --ansi=none --env-file=temp-dbo-test-env down --remove-orphans


#-#
#-# clean:
#-# 
clean:
	rm -fr mysql mysql-data mysql-data-snapshot

#-#
#-# sh:
#-# 
sh:
	docker compose --env-file=test-env -f ./docker-compose-db-only.yaml up

